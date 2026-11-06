"""Command line for RSAS (no display needed): servers, HPC, Docker.

    python -m RnaThermofinder analyze input.fasta [--out-dir DIR] [--cores N] [--temps 25,37,42]
    python -m RnaThermofinder deck ...          (same as python -m RnaThermofinder.deck run ...)
    python -m RnaThermofinder gui              (the desktop application, same as python main.py)
    python -m RnaThermofinder version

`analyze` runs the same pipeline as the Analyze page, with the settings saved by the GUI
(~/.rsas/csv_output_settings.json: output columns, scoring profiles, hairpin detection, temperatures).
Each run writes a new folder <out-dir>/<input>_<YYYYmmdd_HHMMSS>/ whose files all start with the input's name.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # settings_manager lives at the project root


def _analyze(args) -> int:
    from settings_manager import SettingsManager, default_output_dir, input_stem, new_run_dir

    from RnaThermofinder import __version__
    from RnaThermofinder.core import FastaParse, HairpinAnalysis

    src = Path(args.input).expanduser()
    if not src.is_file():
        print(f"STOP: input file not found: {src}", file=sys.stderr)
        return 1
    sm = SettingsManager("csv_output_settings.json")
    if args.temps:
        sm.set_temperatures([int(float(t)) for t in args.temps.replace(";", ",").split(",") if t.strip()])
    calc = sm.settings.get("calculation_settings", {})
    settings = {"hairpin_detection_method": args.hairpin or calc.get("hairpin_detection_method", "terminal"),
                "num_cpu_cores": args.cores}

    stem = input_stem(src)
    run_dir = new_run_dir(stem, base=Path(args.out_dir).expanduser() if args.out_dir else default_output_dir())
    log_lines: list[str] = []

    def log(msg: str):  # the pipeline prints each message itself; keep a copy for <input>_run_log.txt
        log_lines.append(msg)

    started = datetime.now()
    header = f"RSAS {__version__} | input {src} | results folder {run_dir}"
    log_lines.append(header)
    import contextlib
    import io
    quiet = contextlib.redirect_stdout(io.StringIO()) if args.quiet else contextlib.nullcontext()
    with quiet:
        print(header, flush=True)
        sequences = FastaParse.load_sequences(str(src), convert_to_rna=True, validate_fasta=True)
        results = HairpinAnalysis.calculate_results_final(sequences, run_dir, settings, log, sm, file_prefix=stem)
    (run_dir / f"{stem}_run_log.txt").write_text("\n".join(log_lines) + "\n", encoding="utf-8")
    try:
        import RNA
        vienna = RNA.__version__
    except Exception:  # noqa: BLE001
        vienna = "?"
    info = {"rsas_version": __version__, "viennarna_version": vienna, "input_file": str(src),
            "input_name": stem, "started": started.isoformat(timespec="seconds"),
            "finished": datetime.now().isoformat(timespec="seconds"), "status": "ok", "interface": "cli",
            "sequences": len(sequences), "results": len(results),
            "folding_temperatures": sm.get_temperatures(), "analysis_settings": settings,
            "files": sorted(p.name for p in run_dir.iterdir()) + [f"{stem}_run_info.json"]}
    (run_dir / f"{stem}_run_info.json").write_text(json.dumps(info, indent=1), encoding="utf-8")
    print(run_dir)
    return 0


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if argv and argv[0] == "deck":
        from RnaThermofinder.deck.cli import main as deck_main
        return deck_main(["run", *argv[1:]] if len(argv) > 1 and argv[1].startswith("-") else argv[1:])
    ap = argparse.ArgumentParser(prog="python -m RnaThermofinder", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("analyze", help="run the RSAS analysis on a FASTA/CSV/TSV file")
    a.add_argument("input")
    a.add_argument("--out-dir", help="parent folder for the run folder (default: ~/RSAS)")
    a.add_argument("--cores", type=int, default=1, help="CPU cores (default 1)")
    a.add_argument("--temps", help="folding temperatures in C, e.g. 25,37,42 (saved as the new default)")
    a.add_argument("--hairpin", choices=["terminal", "rbs_based"], help="hairpin detection method")
    a.add_argument("--quiet", action="store_true", help="print only the results folder")
    sub.add_parser("deck", help="RNAfold Deck: python -m RnaThermofinder deck --results X.xlsx --out-dir D --name N")
    sub.add_parser("gui", help="start the desktop application")
    sub.add_parser("version", help="print versions")
    args = ap.parse_args(argv)
    if args.cmd == "analyze":
        return _analyze(args)
    if args.cmd == "gui":
        import main as rsas_main
        rsas_main.main()
        return 0
    if args.cmd == "version":
        from RnaThermofinder import __version__
        try:
            import RNA
            vienna = RNA.__version__
        except ImportError:
            vienna = "NOT INSTALLED"
        print(f"RSAS {__version__} | ViennaRNA {vienna} | Python {sys.version.split()[0]}")
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
