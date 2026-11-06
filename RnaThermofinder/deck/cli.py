"""Command line for the RSAS RNAfold deck (local ViennaRNA); the RSAS "RNAfold Deck" page runs the same steps.

    python -m RnaThermofinder.deck run --results Data/Outputs/rna_results.xlsx --tier "Tier 1" \
        --fold both --temp 25 --temp 37 --temp 42 --out-dir Data/Outputs --name "RNAfold deck"
"""
from __future__ import annotations

import argparse
import json
import sys

from . import engine


def _rounds(args):
    if bool(args.config) == bool(args.results):
        raise engine.DeckError("give either --config (curated hairpin sheets) or --results (select by tier)")
    if args.config:
        cfg = json.loads(engine.expand(args.config).read_text(encoding="utf-8"))
        return cfg["rounds"], cfg.get("id_separator", "|")
    names = args.round_name or [engine.expand(f).stem for f in args.results]
    if len(names) != len(args.results):
        raise engine.DeckError(f"{len(args.results)} --results but {len(names)} --round-name")
    return [{"name": n, "results_workbook": f} for n, f in zip(names, args.results)], "|"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m RnaThermofinder.deck", description=engine.__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    run = sub.add_parser("run", help="all three steps, like the app's Run button")
    run.add_argument("--results", action="append", required=True, help="RSAS Results workbook; repeat per round")
    run.add_argument("--round-name", action="append", help="label per --results, same order")
    run.add_argument("--tier", action="append", metavar="TIER",
                     help="hairpin tier to select (Tier 1 to Tier 7, or a class name RSAS was set up with, typed "
                          "exactly as it appears in HP_Quality_Score_Class); repeat or give 'Tier 1, Tier 2' for "
                          f"several, up to {engine.MAX_TIERS}; default Tier 1")
    run.add_argument("--temp", action="append", metavar="C",
                     help=f"fold at this temperature (C); repeat for up to {engine.MAX_TEMPS}, default 37")
    run.add_argument("--fold", default="fullength", choices=[*engine.SCOPES, "both"],
                     help="fold the full-length sequence (default), the hairpin alone, or both")
    run.add_argument("--out-dir", required=True)
    run.add_argument("--name", required=True, help="deck name (file names derive from it)")

    t = sub.add_parser("trace", help="select hairpins and find their full-length sequences")
    t.add_argument("--results", action="append")
    t.add_argument("--round-name", action="append")
    t.add_argument("--tier", action="append", metavar="TIER")
    t.add_argument("--temp", action="append", metavar="C")
    t.add_argument("--fold", default="fullength", choices=[*engine.SCOPES, "both"])
    t.add_argument("--excel", help="also write the selected hairpin + full-length rows here")
    t.add_argument("--config", help="curated hairpin sheets instead of --results")
    t.add_argument("--mapping", required=True)

    f = sub.add_parser("fold", help="fold locally with ViennaRNA and draw the structures")
    f.add_argument("--mapping", required=True)
    f.add_argument("--workdir", required=True)
    f.add_argument("--dry-run", action="store_true")

    b = sub.add_parser("build", help="build and verify the PowerPoint")
    b.add_argument("--mapping", required=True)
    b.add_argument("--workdir", required=True)
    b.add_argument("--out", required=True)

    args = ap.parse_args(argv)
    hooks = engine.Hooks(log=print)
    try:
        if args.cmd == "run":
            rounds, _ = _rounds(argparse.Namespace(config=None, results=args.results, round_name=args.round_name))
            tiers = engine.parse_tiers(args.tier or ["Tier 1"])
            plan = engine.plan_outputs(args.out_dir, args.name, tiers)
            result = engine.run_all(rounds, tiers, plan, hooks, temps=args.temp or [engine.DEFAULT_TEMP],
                                    scopes=args.fold)
            print(f"deck -> {result['deck']}\nselection -> {result['excel']}\nreport -> {result['report']}")
            for name, path in result["round_decks"].items():
                print(f"round deck {name} -> {path}")
        elif args.cmd == "trace":
            rounds, sep = _rounds(args)
            engine.trace(rounds, args.mapping, hooks, tier=args.tier or ["Tier 1"], excel_path=args.excel, sep=sep,
                         temps=args.temp or [engine.DEFAULT_TEMP], scopes=args.fold)
        elif args.cmd == "fold":
            engine.fold(args.mapping, args.workdir, hooks, dry_run=args.dry_run)
        elif args.cmd == "build":
            engine.build(args.mapping, args.workdir, args.out, hooks)
    except engine.DeckError as e:
        print(f"STOP: {e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
