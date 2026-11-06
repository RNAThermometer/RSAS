"""RNAfold structure deck engine (RSAS module, local folding).

RSAS Results workbook(s) -> hairpins of the chosen quality tier(s) (Hairpin Analysis) -> the exact same Name on
Full Sequence -> local ViennaRNA fold (RNAfold -p -d2 --noLP, the webserver's defaults) of that full-length
sequence and/or of the hairpin itself, at one to five temperatures -> the MFE drawing in the webserver's style
(naview layout, nucleotides colored by base-pair probability), drawn locally -> PowerPoint (one slide per fold)
that is re-read and checked.

Adapted from RNAfold Deck 1.3.0, which folded on the RNAfold webserver and captured the drawings with Chrome.
No internet connection or browser is needed any more.

Shared by the RSAS page (panel.py) and the command line (cli.py). Anything that cannot be verified raises
DeckError with a reason a non-programmer can act on.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import threading
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable

from . import local_fold

MAX_TIERS = 7  # RSAS's standard classes are Tier 1 to Tier 7; a custom set-up may name them anything
TIERS = [f"Tier {i}" for i in range(1, MAX_TIERS + 1)]
DEFAULT_TEMP, MAX_TEMPS = "37", 5
# what gets folded: the hairpin's full-length sequence (Full Sequence tab), the hairpin itself, or both
SCOPES = {"fullength": "Full-length", "hairpin": "Hairpin"}
DEFAULT_SCOPES = ("fullength",)
SLIDE_W, SLIDE_H = 12191695, 6858000
ACCENT, INK, MUTED_INK = (0x1F, 0x6F, 0x8B), (0x1F, 0x29, 0x37), (0x5B, 0x67, 0x7A)
CHECKS = ("slide_seq_is_folded_seq", "slide_structure_is_vienna", "slide_mfe_is_vienna",
          "image_is_this_folds_drawing", "fold_seq_is_traced_seq", "fold_temp_is_requested",
          "drawing_seq_is_folded_seq", "drawing_colored", "drawing_is_of_this_fold")
MFE_LINE = re.compile(r"^(Full-length|Hairpin) fold\s+·\s+MFE (-?[0-9]+(?:\.[0-9]+)?) kcal/mol at (\S+) °C$")


class DeckError(Exception):
    """A step refused to continue; the message says why."""


class Cancelled(DeckError):
    """The user pressed Stop."""


def _no_progress(stage: str, done: int, total: int) -> None:
    pass


@dataclass
class Hooks:
    log: Callable[[str], None] = print
    progress: Callable[[str, int, int], None] = _no_progress
    stop: threading.Event = field(default_factory=threading.Event)

    def check(self) -> None:
        if self.stop.is_set():
            raise Cancelled("Stopped. Run again with the same deck name and folder to pick up where it left off.")


def expand(path) -> Path:
    return Path(os.path.expanduser(str(path)))


def sid(name, sep="|") -> str:
    return str(name).split(sep)[0].strip()


def rna(s) -> str:
    return str(s).strip().upper().replace("T", "U")


def safe_name(s) -> str:
    return re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", str(s)).strip().rstrip(".")


def sha256(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def cell(row, i):
    return row[i] if row is not None and i is not None and i < len(row) else None


def parse_temps(text) -> list[str]:
    """'25, 37, 42.5' -> ['25', '37', '42.5']: one to MAX_TEMPS distinct temperatures in C, 0-100.
    Commas, semicolons or plain spaces separate the values, so '25 30 37 42 45' works too."""
    raw = [p for p in re.split(r"[,;\s]+", str(text).strip()) if p]
    if not raw:
        raise DeckError(f"Give at least one temperature in C (for example 37); up to {MAX_TEMPS}.")
    if len(raw) > MAX_TEMPS:
        raise DeckError(f"Up to {MAX_TEMPS} temperatures, not {len(raw)}.")
    temps = []
    for p in raw:
        try:
            value = float(p)
        except ValueError:
            raise DeckError(f"'{p}' is not a temperature in C (use numbers like 25, 37 or 42.5).") from None
        if not 0 <= value <= 100:
            raise DeckError(f"Temperature {p} C is outside 0-100 C.")
        temps.append(f"{value:g}")
    if len(set(temps)) != len(temps):
        raise DeckError(f"The same temperature is listed twice ({', '.join(temps)}).")
    return temps


def parse_tiers(tiers) -> list[str]:
    """'Tier 1', 'Tier 1, Tier 2', '1+3', ['Tier 2', 'Tier 1'] -> the chosen tiers, each once, in tier order.

    Any other label ('High', 'Class A') is a custom HP_Quality_Score_Class that RSAS was set up with: kept exactly
    as typed (it must match the sheet), after the standard tiers, in the order given. Blanks are skipped and at
    most MAX_TIERS classes may be chosen in all."""
    if isinstance(tiers, str):
        tiers = re.split(r"[,;+]", tiers)
    standard, custom = [], []
    for t in tiers:
        t = str(t).strip()
        m = re.fullmatch(r"(?i)(?:tiers?\s*)?(\d+)", t)
        if m:
            if not 1 <= int(m.group(1)) <= MAX_TIERS:
                raise DeckError(f"Tiers are {TIERS[0]} to {TIERS[-1]}, not {t}.")
            standard.append(f"Tier {int(m.group(1))}")
        elif t and t not in custom:
            custom.append(t)
    chosen = [t for t in TIERS if t in standard] + custom
    if not chosen:
        raise DeckError("Choose at least one hairpin tier.")
    if len(chosen) > MAX_TIERS:
        raise DeckError(f"At most {MAX_TIERS} tiers can be chosen, not {len(chosen)}.")
    return chosen


def tier_label(tiers) -> str:
    """'Tier 1' for one tier, 'Tiers 1+3' for several standard tiers, 'Tier 1 + High' once a custom class is in:
    used in file names, the log and the title slide."""
    tiers = parse_tiers(tiers)
    if len(tiers) == 1:
        return tiers[0]
    if all(t in TIERS for t in tiers):
        return "Tiers " + "+".join(t.split()[1] for t in tiers)
    return " + ".join(tiers)


def parse_scopes(scopes) -> list[str]:
    """('fullength', 'hairpin') or 'both' -> the scopes to fold, full-length first, each once."""
    if isinstance(scopes, str):
        scopes = [scopes]
    chosen = []
    for s in scopes:
        s = str(s).strip().lower().replace("-", "").replace(" ", "")
        s = {"full": "fullength", "fulllength": "fullength", "hp": "hairpin"}.get(s, s)
        chosen += list(SCOPES) if s == "both" else [s]
    unknown = [s for s in chosen if s not in SCOPES]
    if unknown:
        raise DeckError(f"Fold must be full-length, hairpin or both, not {', '.join(unknown)}.")
    if not chosen:
        raise DeckError("Choose what to fold: full-length, hairpin or both.")
    return [s for s in SCOPES if s in chosen]


def fold_seq(it) -> str:
    """The sequence an item folds: the full-length sequence, or the hairpin alone."""
    return it["hp_seq"] if it.get("scope", "fullength") == "hairpin" else it["fl_seq"]


# ---------------------------------------------------------------- step 1: trace

def _header(ws):
    return next(ws.iter_rows(min_row=1, max_row=1, values_only=True))


def _open(openpyxl, path):
    try:
        return openpyxl.load_workbook(path, read_only=True)
    except Exception as e:  # noqa: BLE001 - corrupt, locked or not-xlsx all mean the same thing here
        raise DeckError(f"Could not open '{Path(path).name}' as an Excel workbook ({type(e).__name__}: {e}).") from e


def _sheet(wb, name, path):
    if name not in wb.sheetnames:
        raise DeckError(f"'{Path(path).name}' has no '{name}' tab (it has: {', '.join(wb.sheetnames)}). "
                        "Use the Excel file RSAS exports - it has 'Hairpin Analysis' and 'Full Sequence' tabs.")
    return wb[name]


def columns(ws, wanted, optional=()):
    idx = {str(h).strip(): i for i, h in enumerate(_header(ws)) if h is not None}
    missing = [w for w in wanted if w not in idx]
    if missing:
        raise DeckError(f"The '{ws.title}' tab has no {', '.join(missing)} column. Turn it on in RSAS (Output "
                        f"Columns) and export again. Columns found: {', '.join(idx)}")
    return {w: idx.get(w) for w in (*wanted, *optional)}


def _rows(ws, label, hooks, max_col=None):
    total = ws.max_row or 0
    for i, r in enumerate(ws.iter_rows(min_row=2, max_col=max_col, values_only=True), start=2):
        if i % 5000 == 0:
            hooks.check()
            hooks.progress(label, i, total)
        yield i, r
    hooks.progress(label, total, total)


def check_rounds(rounds) -> None:
    if not rounds:
        raise DeckError("Add at least one RSAS Results workbook.")
    names = [str(r.get("name", "")).strip() for r in rounds]
    if not all(names):
        raise DeckError("Every Results workbook needs a round name.")
    if len(set(names)) != len(names):
        raise DeckError(f"Round names must all be different (got: {', '.join(names)}).")
    for r in rounds:
        if not expand(r["results_workbook"]).is_file():
            raise DeckError(f"File not found: {r['results_workbook']}")
    if not any("hp_sheet" in r for r in rounds):
        files = [str(expand(r["results_workbook"]).resolve()) for r in rounds]
        if len(set(files)) != len(files):
            raise DeckError("The same Results workbook was added twice - add each file once, one per round.")


def _select_curated(openpyxl, rounds, sep, hooks):
    wanted = []
    for rnd in rounds:
        path = expand(rnd["hp_workbook"])
        wb = _open(openpyxl, path)
        if rnd["hp_sheet"] not in wb.sheetnames:
            raise DeckError(f"'{path.name}' has no '{rnd['hp_sheet']}' tab.")
        ws = wb[rnd["hp_sheet"]]
        c = columns(ws, ["Name", "Hairpin_Sequence"])
        n = 0
        for _, r in _rows(ws, f"Reading {rnd['hp_sheet']}", hooks):
            if cell(r, c["Name"]):
                n += 1
                wanted.append({"round": rnd["name"], "n": n, "id": sid(r[c["Name"]], sep),
                               "hp_name": str(r[c["Name"]]).strip(), "hp_seq": rna(r[c["Hairpin_Sequence"]])})
        wb.close()
    return wanted


def _select_tier(book, rounds, sep, tiers, hooks, hp_header, hp_raw):
    """Every Hairpin Analysis row whose HP_Quality_Score_Class is one of `tiers`, in sheet order."""
    tiers, wanted = parse_tiers(tiers), []
    for rnd in rounds:
        path = expand(rnd["results_workbook"])
        wb = book(path)
        ws = _sheet(wb, "Hairpin Analysis", path)
        c = columns(ws, ["Name", "Hairpin_Sequence", "HP_Quality_Score_Class"], optional=("Hairpin_Structure",))
        hp_header[rnd["name"]] = _header(ws)
        n, per_tier = 0, dict.fromkeys(tiers, 0)
        for _, r in _rows(ws, f"Selecting {tier_label(tiers)} in {path.name}", hooks):
            tier = str(cell(r, c["HP_Quality_Score_Class"])).strip()
            if cell(r, c["Name"]) and tier in per_tier:
                n += 1
                per_tier[tier] += 1
                key = sid(r[c["Name"]], sep)
                wanted.append({"round": rnd["name"], "n": n, "id": key, "tier": tier,
                               "hp_name": str(r[c["Name"]]).strip(), "hp_seq": rna(r[c["Hairpin_Sequence"]]),
                               "hp_struct": str(cell(r, c["Hairpin_Structure"]) or "").strip()})
                hp_raw[(rnd["name"], key)] = r
        hooks.log(f"  {path.name}: " + ", ".join(f"{k} '{t}'" for t, k in per_tier.items()) + " hairpin(s)")
        if n == 0:
            raise DeckError(f"'{path.name}' has no '{' or '.join(tiers)}' rows in Hairpin Analysis "
                            "(HP_Quality_Score_Class).")
    return wanted


def _write_selection(openpyxl, path, rounds, items, hp_header, hp_raw, full_header, full_raw):
    """The workbook that used to be made by hand: per round, the selected hairpin rows and their full-length rows."""
    wb = openpyxl.Workbook(write_only=True)
    used = set()
    for rnd in rounds:
        base = re.sub(r"[\[\]:*?/\\]", "_", rnd["name"])[:21]
        if base in used:
            raise DeckError(f"Round names are too similar to use as Excel tab names: '{base}'.")
        used.add(base)
        mine = [i for i in items if i["round"] == rnd["name"]]
        ws = wb.create_sheet(f"{base} hp")
        ws.append(list(hp_header[rnd["name"]]))
        for it in mine:
            ws.append(list(hp_raw[(rnd["name"], it["id"])]))
        fname = str(expand(rnd["results_workbook"]))
        ws = wb.create_sheet(f"{base} fullength")
        ws.append(list(full_header[fname]))
        for it in mine:
            ws.append(list(full_raw[(fname, it["full_row"])]))
    tmp = Path(path).with_name(Path(path).stem + ".partial.xlsx")
    wb.save(tmp)
    os.replace(tmp, path)


_TEMP_COL = re.compile(r"^(MFE|Structure)_(-?[0-9]+(?:\.[0-9]+)?)C$")


def _temp_columns(ws) -> dict:
    """{('MFE'|'Structure', '25'): column index} for RSAS's per-temperature columns on a tab."""
    out = {}
    for i, h in enumerate(_header(ws)):
        m = _TEMP_COL.match(str(h).strip()) if h is not None else None
        if m:
            out[(m.group(1), f"{float(m.group(2)):g}")] = i
    return out


def _sheet_values(row, temp_cols) -> dict:
    """{'25': {'mfe': '-12.3', 'structure': '((..))'}} from one RSAS row, for cross-checking the local folds."""
    vals = defaultdict(dict)
    for (kind, t), i in temp_cols.items():
        v = cell(row, i)
        if v not in (None, "", 0, 0.0, "0", "0.0"):
            vals[t]["mfe" if kind == "MFE" else "structure"] = str(v).strip()
    return dict(vals)


def _same_mfe(a, b) -> bool:
    try:
        return abs(float(str(a).strip("()")) - float(b)) < 0.006
    except (TypeError, ValueError):
        return False


def _rsas_trimmed_hairpin(it) -> str:
    """The hairpin as RSAS folds it for its MFE_<T>C columns: Hairpin_Sequence minus the trailing unpaired tail."""
    st = it.get("hp_struct") or ""
    if len(st) != len(it["hp_seq"]) or ")" not in st:
        return ""
    return it["hp_seq"][:st.rfind(")") + 1]


def trace(rounds, mapping_path, hooks, tier="Tier 1", excel_path=None, sep="|", temps=(DEFAULT_TEMP,),
          scopes=DEFAULT_SCOPES) -> dict:
    import openpyxl
    check_rounds(rounds)
    temps, scopes = parse_temps(",".join(temps)), parse_scopes(scopes)
    curated = any("hp_sheet" in r for r in rounds)
    if excel_path and curated:
        raise DeckError("The selection workbook is only written when selecting by tier.")
    hp_header, hp_raw, full_header, full_raw = {}, {}, {}, {}
    books = {}  # each Results file opened once: loading a large export's shared strings is the slow part

    def book(path):
        key = str(expand(path))
        if key not in books:
            books[key] = _open(openpyxl, key)
        return books[key]

    try:
        if curated:
            wanted = _select_curated(openpyxl, rounds, sep, hooks)
        else:
            wanted = _select_tier(book, rounds, sep, tier, hooks, hp_header, hp_raw)

        ids = {w["id"] for w in wanted}
        per_round = defaultdict(list)
        for w in wanted:
            per_round[w["round"]].append(w["id"])
        dups = {r: sorted({i for i in v if v.count(i) > 1}) for r, v in per_round.items() if len(set(v)) != len(v)}
        if dups:
            raise DeckError(f"The same ID appears twice in one round: {dups}")

        hp_hits, full_hits = defaultdict(list), defaultdict(list)
        for fname in dict.fromkeys(str(expand(r["results_workbook"])) for r in rounds):
            wb = book(fname)
            ws = _sheet(wb, "Hairpin Analysis", fname)
            c = columns(ws, ["Name", "Hairpin_Sequence"])
            hp_temp_cols = _temp_columns(ws)
            for i, r in _rows(ws, f"Checking Hairpin Analysis in {Path(fname).name}", hooks):
                if cell(r, c["Name"]) and sid(r[c["Name"]], sep) in ids:
                    hp_hits[sid(r[c["Name"]], sep)].append({"file": fname, "row": i, "name": str(r[c["Name"]]).strip(),
                                                            "seq": rna(r[c["Hairpin_Sequence"]]),
                                                            "sheet": _sheet_values(r, hp_temp_cols)})
            ws = _sheet(wb, "Full Sequence", fname)
            c = columns(ws, ["Name", "Sequence"])
            fl_temp_cols = _temp_columns(ws)
            top = None
            if excel_path:
                full_header[fname] = _header(ws)
            for i, r in _rows(ws, f"Finding full-length sequences in {Path(fname).name}", hooks, top):
                if cell(r, c["Name"]) and sid(r[c["Name"]], sep) in ids:
                    if excel_path:
                        full_raw[(fname, i)] = r
                    full_hits[sid(r[c["Name"]], sep)].append({
                        "file": fname, "row": i, "name": str(r[c["Name"]]).strip(), "seq": rna(r[c["Sequence"]]),
                        "sheet": _sheet_values(r, fl_temp_cols)})

        copies = {}
        for rnd in rounds:
            fc = rnd.get("fullength_copy")
            if fc:
                wb = _open(openpyxl, expand(fc["workbook"]))
                ws = wb[fc["sheet"]]
                c = columns(ws, ["Name", "Sequence"])
                for _, r in _rows(ws, f"Reading {fc['sheet']}", hooks):
                    if cell(r, c["Name"]):
                        copies[(rnd["name"], sid(r[c["Name"]], sep))] = rna(r[c["Sequence"]])
                wb.close()

        expected = {r["name"]: str(expand(r["results_workbook"])) for r in rounds}
        has_copy = {r["name"] for r in rounds if r.get("fullength_copy")}
        fails, items = [], []
        for w in wanted:
            h, f, probs = hp_hits[w["id"]], full_hits[w["id"]], []
            if len(h) != 1:
                probs.append(f"Hairpin Analysis hits {[(Path(x['file']).name, x['row']) for x in h]}")
            if len(f) != 1:
                probs.append(f"Full Sequence hits {[(Path(x['file']).name, x['row']) for x in f]}")
            if len(h) == 1 and len(f) == 1:
                h, f = h[0], f[0]
                if h["file"] != f["file"]:
                    probs.append("hairpin and full-length rows are in different Results files")
                if h["file"] != expected[w["round"]]:
                    probs.append(f"found in {Path(h['file']).name}, expected {Path(expected[w['round']]).name}")
                if h["name"] != w["hp_name"] or f["name"] != w["hp_name"]:
                    probs.append("full Name string differs between the hairpin row and the Full Sequence row")
                if h["seq"] != w["hp_seq"]:
                    probs.append("Results hairpin sequence differs from the selected hairpin sequence")
                if w["hp_seq"] not in f["seq"]:
                    probs.append("hairpin sequence is not inside the full-length sequence")
                if w["round"] in has_copy and copies.get((w["round"], w["id"])) != f["seq"]:
                    probs.append("full-length copy sheet disagrees with Results Full Sequence")
                items.append({**w, "results_file": Path(f["file"]).name, "hp_row": h["row"], "full_row": f["row"],
                              "fl_seq": f["seq"], "sheet_fl": f["sheet"], "sheet_hp": h["sheet"]})
            if probs:
                fails.append(f"{w['round']} {w['id']}: " + "; ".join(probs))

        out = expand(mapping_path)
        if fails:
            out.unlink(missing_ok=True)
            raise DeckError(f"TRACE FAILED for {len(fails)} of {len(wanted)} IDs (nothing was folded):\n" + "\n".join(fails))
        # one fold (and one slide) per hairpin per scope per temperature; a hairpin's slides stay together:
        # its full-length fold at every temperature, then its hairpin fold at every temperature
        folds = [{**it, "scope": s, "temp": t} for it in items for s in scopes for t in temps]
        out.write_text(json.dumps({"rounds": [r["name"] for r in rounds],
                                   "tier": None if curated else tier_label(tier),
                                   "tiers": None if curated else parse_tiers(tier),
                                   "temps": temps, "scopes": scopes, "items": folds}, indent=1), encoding="utf-8")
        how = "hairpin rows from the curated sheets" if curated else f"{tier_label(tier)} rows of Hairpin Analysis"
        hooks.log(f"TRACE PASS: {len(items)} {how}; each Name found exactly once in Full Sequence; hairpin inside full-length")
        counts = {r["name"]: sum(1 for i in items if i["round"] == r["name"]) for r in rounds}
        for name, n in counts.items():
            hooks.log(f"  {name}: {n}")
        if len(folds) != len(items):
            hooks.log(f"  {' + '.join(SCOPES[s].lower() for s in scopes)} at {', '.join(temps)} C: {len(folds)} folds")
        if excel_path:
            _write_selection(openpyxl, expand(excel_path), rounds, items, hp_header, hp_raw, full_header, full_raw)
            hooks.log(f"  selection workbook -> {Path(excel_path).name}")
        return {"selected": len(items), "per_round": counts, "temps": temps, "scopes": scopes}
    finally:
        for wb in books.values():
            wb.close()


# ---------------------------------------------------------------- step 2: fold + capture

def load_mapping(path):
    m = expand(path)
    if not m.exists():
        raise DeckError(f"{m.name} is missing - run the selection step first.")
    data = json.loads(m.read_text(encoding="utf-8"))
    for it in data["items"]:
        it.setdefault("temp", DEFAULT_TEMP)  # mappings from before custom temperatures were always 37 C
        it.setdefault("scope", "fullength")  # ... and from before hairpin folds were always full-length
    return data["rounds"], data["items"]


def item_paths(workdir, it):
    """A full-length fold at the default temperature keeps the original names, so folds from earlier runs
    are still reused; hairpin folds add _hp and custom temperatures add _55C."""
    d = expand(workdir) / safe_name(it["round"])
    temp = it.get("temp", DEFAULT_TEMP)
    # every file starts with the input FASTA's name, taken from its RSAS results workbook
    # (<input>_rna_results.xlsx); a hairpin's files sit together under it
    prefix = results_stem(it.get("results_file", ""))
    stem = ((f"{prefix}_" if prefix else "") + f"{it['n']:03d}_{safe_name(it['id'])}" + ("_hp" if it.get("scope", "fullength") == "hairpin" else "")
            + ("" if temp == DEFAULT_TEMP else f"_{safe_name(temp)}C"))
    return d, d / f"{stem}.json", d / f"{stem}.svg", d / f"{stem}.png"


def results_stem(results_file) -> str:
    """'Rose like pool_rna_results.xlsx' -> 'Rose like pool' (the input FASTA's name RSAS put on its outputs)."""
    stem = Path(str(results_file)).stem if results_file else ""
    return safe_name(re.sub(r"_rna_results(_\d{8}_\d{6})?$", "", stem))


def item_label(it) -> str:
    return f"{it['id']} {SCOPES[it.get('scope', 'fullength')].lower()} {it.get('temp', DEFAULT_TEMP)} C"


def _read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_json(path, data):
    tmp = Path(path).with_suffix(".partial.json")
    tmp.write_text(json.dumps(data, indent=1), encoding="utf-8")
    os.replace(tmp, path)


def png_has_color(path) -> bool:
    """A probability-colored drawing has strongly saturated pixels; a failed render would be black and white."""
    from PIL import Image
    with Image.open(path) as im:
        im = im.convert("RGB")
        im.thumbnail((300, 300))
        raw = im.tobytes()
    px = [raw[i:i + 3] for i in range(0, len(raw), 3)]
    return sum(1 for r, g, b in px if max(r, g, b) - min(r, g, b) > 80) / len(px) > 0.005


def _fold_one(workdir, it, hooks):
    """Fold one item with the local ViennaRNA and draw it; reuse an earlier verified fold of the same sequence,
    temperature and ViennaRNA version."""
    hooks.check()
    d, meta_path, svg_path, png_path = item_paths(workdir, it)
    seq = fold_seq(it)
    if meta_path.exists() and svg_path.exists() and png_path.exists():
        meta = _read_json(meta_path)
        if (meta.get("verified") and meta.get("seq") == seq and meta.get("temp") == it["temp"]
                and meta.get("engine") == local_fold.model_description()
                and meta.get("png_sha256") == sha256(png_path) and meta.get("png_svg_sha256") == sha256(svg_path)):
            return meta, False
    d.mkdir(parents=True, exist_ok=True)
    png_path.unlink(missing_ok=True)  # never keep a picture of an older fold
    res = local_fold.fold(seq, it["temp"])
    local_fold.write_svg(res, svg_path, title=f"{it['id']} {item_label(it)}")
    local_fold.write_png(res, png_path)
    drawn = local_fold.drawn_letters(svg_path.read_text(encoding="utf-8"))
    meta = {"id": it["id"], "round": it["round"], "scope": it.get("scope", "fullength"),
            "engine": res["engine"], "job_url": f"local:{res['engine']}",
            "mfe": res["mfe"], "ensemble_energy": res["ensemble_energy"], "seq": res["seq"],
            "structure": res["structure"], "temp": it["temp"],
            "fold_temp_is_requested": res["temp"] == it["temp"],
            "fold_seq_is_traced_seq": res["seq"] == seq,
            "drawing_seq_is_folded_seq": drawn == seq,
            "png_sha256": sha256(png_path), "png_svg_sha256": sha256(svg_path)}
    meta["verified"] = (meta["fold_temp_is_requested"] and meta["fold_seq_is_traced_seq"]
                        and meta["drawing_seq_is_folded_seq"] and len(res["structure"]) == len(seq))
    _write_json(meta_path, meta)
    if not meta["verified"]:
        raise DeckError(f"The local fold of {item_label(it)} did not verify (sequence, temperature or drawing).")
    return meta, True


def _fold_cached(workdir, it) -> bool:
    _, meta_path, svg_path, png_path = item_paths(workdir, it)
    if not (meta_path.exists() and svg_path.exists() and png_path.exists()):
        return False
    meta = _read_json(meta_path)
    return bool(meta.get("verified") and meta.get("seq") == fold_seq(it) and meta.get("temp") == it["temp"]
                and meta.get("engine") == local_fold.model_description())


def _fold_worker(args):
    """Process-pool entry point (must be top level to pickle)."""
    workdir, it = args
    try:
        return _fold_one(workdir, it, Hooks(log=lambda m: None))
    except DeckError as e:
        return e


def _fold_parallel(workdir, items, workers, hooks):
    """Yield (meta, new) per item in order, folding in worker processes; Stop is honored between results."""
    from concurrent.futures import ProcessPoolExecutor
    with ProcessPoolExecutor(max_workers=workers) as ex:
        futures = [ex.submit(_fold_worker, (str(workdir), it)) for it in items]
        try:
            for fut in futures:
                hooks.check()
                res = fut.result()
                if isinstance(res, Exception):
                    raise res
                yield res
        finally:
            for fut in futures:
                fut.cancel()


def fold(mapping_path, workdir, hooks, dry_run=False, workers=None) -> dict:
    """Fold every item locally with ViennaRNA and draw it (no internet, no browser)."""
    _, items = load_mapping(mapping_path)
    cached = [it for it in items if item_paths(workdir, it)[1].exists()]
    if dry_run:
        hooks.log(f"{len(items)} item(s); {len(cached)} already folded in {expand(workdir).name}")
        return {"folded": 0, "cached": len(cached), "captured": 0}
    total, folded = len(items), 0
    stage = "Folding and drawing (ViennaRNA, local)"
    hooks.log(f"Folding {total} sequence(s) with {local_fold.model_description()} "
              f"({len(cached)} found from an earlier run) ...")
    hooks.progress(stage, 0, total)
    workers = workers or max(1, min(8, (os.cpu_count() or 2) - 1))
    todo = [it for it in items if not _fold_cached(workdir, it)]
    if workers > 1 and len(todo) >= 8:
        hooks.log(f"  using {workers} worker processes for {len(todo)} new fold(s)")
        results = _fold_parallel(workdir, items, workers, hooks)
    else:
        results = (_fold_one(workdir, it, hooks) for it in items)
    for i, (it, (meta, new)) in enumerate(zip(items, results), start=1):
        folded += new
        hooks.progress(stage, i, total)
        hooks.log(f"  {i}/{total} {item_label(it)} {'folded' if new else 'kept'}  MFE {meta['mfe']}")
    hooks.log(f"FOLD PASS: {total} folded locally from the exact traced sequence ({folded} new); every drawing "
              "carries that sequence")
    return {"folded": folded, "cached": total - folded, "captured": folded}



# ---------------------------------------------------------------- step 3: build + verify

SEQ_LINE = 60  # monospace characters per line: sequence and dot-bracket break at the same columns


def _add_para(tf, text, size, bold, space_before=None, mono=False, first=False, color=INK, wrap=None):
    """One paragraph, styled on the run itself so PowerPoint, Keynote and LibreOffice all honor it.
    `wrap` breaks the text into fixed-width lines (read back as one paragraph with \\v between lines)."""
    from pptx.dml.color import RGBColor
    from pptx.util import Pt
    para = tf.paragraphs[0] if first else tf.add_paragraph()
    if space_before:
        para.space_before = Pt(space_before / 100)
    lines = [text[i:i + wrap] for i in range(0, len(text), wrap)] if wrap else [text]
    for i, line in enumerate(lines):
        if i:
            para.add_line_break()
        run = para.add_run()
        run.text = line
        run.font.size, run.font.bold = Pt(size / 100), bold
        run.font.name = "Courier New" if mono else "Calibri"
        run.font.color.rgb = RGBColor(*color)


def unwrapped(para) -> str:
    return para.text.replace("\v", "").strip()


def _add_band(slide, x, y, w, h, color=ACCENT):
    from pptx.dml.color import RGBColor
    from pptx.enum.shapes import MSO_SHAPE
    band = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, w, h)
    band.fill.solid()
    band.fill.fore_color.rgb = RGBColor(*color)
    band.line.fill.background()
    band.shadow.inherit = False
    return band


def _title_slide(prs, title, subtitle):
    from pptx.dml.color import RGBColor
    from pptx.util import Inches, Pt
    slide = prs.slides.add_slide(prs.slide_layouts[0])
    head, sub = slide.shapes.title, slide.placeholders[1]
    # the stock layout is sized for a 4:3 slide; span the widescreen slide so the text sits centered
    head.left, head.top, head.width, head.height = Inches(0.8), Inches(2.3), prs.slide_width - Inches(1.6), Inches(1.4)
    sub.left, sub.top, sub.width, sub.height = Inches(0.8), Inches(3.8), prs.slide_width - Inches(1.6), Inches(1.2)
    head.text = title
    for run in head.text_frame.paragraphs[0].runs:
        run.font.size, run.font.bold, run.font.color.rgb = Pt(44), True, RGBColor(*INK)
    sub.text = subtitle
    for run in sub.text_frame.paragraphs[0].runs:
        run.font.size, run.font.color.rgb = Pt(18), RGBColor(*MUTED_INK)
    _add_band(slide, 0, 0, prs.slide_width, Inches(0.18))
    return slide


def _structure_slide(prs, it, meta, rnd):
    """ID and round on the left, then the fold's numbers and sequences; the RNAfold drawing on the right,
    fitted to the space so a squat hairpin drawing and a tall full-length one both sit in the same frame."""
    from PIL import Image
    from pptx.enum.text import MSO_AUTO_SIZE
    from pptx.util import Emu, Inches
    scope = it.get("scope", "fullength")
    start = it["fl_seq"].find(it["hp_seq"]) + 1
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _add_band(slide, 0, 0, prs.slide_width, Inches(0.18))
    tf = slide.shapes.add_textbox(Inches(0.4), Inches(0.42), Inches(4.3), Inches(6.7)).text_frame
    tf.word_wrap = True
    tf.auto_size = MSO_AUTO_SIZE.SHAPE_TO_FIT_TEXT
    _add_para(tf, it["id"], 2000, True, first=True)
    _add_para(tf, rnd, 1300, False, 300, color=MUTED_INK)
    _add_para(tf, f"{SCOPES[scope]} fold · MFE {meta['mfe']} kcal/mol at {it['temp']} °C", 1300, True, 900,
              color=ACCENT)
    _add_para(tf, f"{SCOPES[scope]} sequence ({len(fold_seq(it))} nt)", 1050, True, 1200, color=MUTED_INK)
    _add_para(tf, fold_seq(it), 800, False, mono=True, wrap=SEQ_LINE)
    _add_para(tf, "MFE structure (dot-bracket, same columns as the sequence)", 1050, True, 800, color=MUTED_INK)
    _add_para(tf, meta["structure"], 800, False, mono=True, wrap=SEQ_LINE)
    _add_para(tf, "Full name", 1050, True, 800, color=MUTED_INK)
    _add_para(tf, it["hp_name"], 800, False, mono=True)
    _add_para(tf, "Hairpin within the full-length sequence", 1050, True, 800, color=MUTED_INK)
    _add_para(tf, f"nt {start}–{start + len(it['hp_seq']) - 1} of {len(it['fl_seq'])}", 900, False)
    _add_para(tf, f"Drawing: {meta.get('engine', 'ViennaRNA, local')}; MFE structure (naview layout), "
                  "nucleotides colored by base-pair probability (blue 0 → red 1)", 800, False, 1400, color=MUTED_INK)
    with Image.open(meta["png"]) as im:
        w, h = im.size
    h_shown = h  # the local drawing has no webserver widgets to crop; the embedded file is the verified PNG
    box_x, box_y, box_w, box_h = Inches(4.9), Inches(0.42), Inches(8.1), Inches(6.7)
    scale = min(box_w / w, box_h / h_shown)
    pw, ph = int(w * scale), int(h_shown * scale)
    slide.shapes.add_picture(meta["png"], Emu(box_x + (box_w - pw) // 2), Emu(box_y + (box_h - ph) // 2),
                             Emu(pw), Emu(ph))
    return slide


def _read_slide(slide):
    """(round, id, scope, temp), paragraphs, pictures from a saved structure slide; None for a title slide."""
    boxes = [s for s in slide.shapes if s.shape_type == 17]
    if not boxes:
        return None
    paras = boxes[0].text_frame.paragraphs
    line = MFE_LINE.match(paras[2].text.strip())
    scope = next((k for k, v in SCOPES.items() if line and v == line.group(1)), "?")
    key = (paras[1].text.strip(), paras[0].text.strip(), scope, line.group(3) if line else "?")
    return key, paras, line.group(2) if line else None, [s for s in slide.shapes if s.shape_type == 13]


def deck_subtitle(items, tier=None) -> str:
    temps = list(dict.fromkeys(i.get("temp", DEFAULT_TEMP) for i in items))
    scopes = [SCOPES[s].lower() for s in SCOPES if any(i.get("scope", "fullength") == s for i in items)]
    ids = len({(i["round"], i["id"]) for i in items})
    return (f"{tier + ' hairpins · ' if tier else ''}{ids} hairpin{'s' if ids != 1 else ''} · "
            f"{' + '.join(scopes)} fold{'s' if len(scopes) > 1 else ''} · {', '.join(temps)} °C · ViennaRNA {local_fold.vienna_version()} (local)")


def deck_is_open(out) -> bool:
    out = expand(out)
    return (out.parent / f"~${out.name}").exists()


def build(mapping_path, workdir, out, hooks, only_round=None, write_report=True) -> dict:
    from pptx import Presentation
    rounds, items = load_mapping(mapping_path)
    if only_round is not None:
        if only_round not in rounds:
            raise DeckError(f"No round named '{only_round}' in {Path(mapping_path).name}.")
        rounds, items = [only_round], [i for i in items if i["round"] == only_round]
    out = expand(out)
    if deck_is_open(out):
        raise DeckError(f"'{out.name}' is open in PowerPoint. Close it (on a Mac, quit PowerPoint with Cmd+Q) "
                        "and run again.")
    metas, fails = {}, []
    for it in items:
        _, meta_path, svg_path, png = item_paths(workdir, it)
        label = f"{it['round']} {item_label(it)}"
        if not (meta_path.exists() and svg_path.exists() and png.exists()):
            fails.append(f"{label}: folding output missing")
            continue
        meta, seq = _read_json(meta_path), fold_seq(it)
        meta["fold_seq_is_traced_seq"] = meta.get("seq") == seq
        meta["fold_temp_is_requested"] = meta.get("temp") == it["temp"]
        meta["drawing_seq_is_folded_seq"] = local_fold.drawn_letters(svg_path.read_text(encoding="utf-8")) == seq
        meta["png"], meta["png_file_sha256"] = str(png), sha256(png)
        meta["png_colored"] = png_has_color(png)
        meta["png_of_drawing"] = (meta.get("png_sha256") == meta["png_file_sha256"]
                                  and meta.get("png_svg_sha256") == sha256(svg_path))
        if not (meta["fold_seq_is_traced_seq"] and meta["fold_temp_is_requested"] and meta["drawing_seq_is_folded_seq"]
                and meta["png_colored"] and meta["png_of_drawing"]
                and len(meta.get("structure", "")) == len(seq)):
            fails.append(f"{label}: folding output failed re-verification")
        metas[(it["round"], it["id"], it["scope"], it["temp"])] = meta
    # two slides may only share a picture when they folded the very same sequence at the same temperature
    # (two IDs can carry the same hairpin); otherwise a shared picture means a mixed-up drawing
    same_png = defaultdict(set)
    for key, m in metas.items():
        same_png[m["png_file_sha256"]].add((m.get("seq"), key[3]))
    if any(len(v) > 1 for v in same_png.values()):
        fails.append("two slides of different sequences share an identical drawing")
    if fails:
        raise DeckError("Inputs failed re-verification, so no deck was written:\n" + "\n".join(fails))

    tier = _read_json(expand(mapping_path)).get("tier")
    prs = Presentation()
    prs.slide_width, prs.slide_height = SLIDE_W, SLIDE_H
    total, done = len(items), 0
    for rnd in rounds:
        mine = [i for i in items if i["round"] == rnd]
        _title_slide(prs, rnd, deck_subtitle(mine, tier))
        for it in mine:
            hooks.check()
            _structure_slide(prs, it, metas[(rnd, it["id"], it["scope"], it["temp"])], rnd)
            done += 1
            hooks.progress("Building slides", done, total)
    tmp = out.with_name(out.stem + ".building.pptx")
    prs.save(tmp)

    by_key = {(i["round"], i["id"], i["scope"], i["temp"]): i for i in items}
    fails, rows, seen, current = [], [], set(), None
    saved = Presentation(tmp)
    for slide in saved.slides:
        read = _read_slide(slide)
        if read is None:
            current = slide.shapes.title.text.strip()
            continue
        key, paras, mfe, pics = read
        it, meta = by_key.get(key), metas.get(key)
        if not it or key[0] != current:
            fails.append(f"slide {key} is not a traced ID under its round title")
            continue
        checks = {
            "slide_seq_is_folded_seq": unwrapped(paras[4]) == fold_seq(it),
            "slide_structure_is_vienna": unwrapped(paras[6]) == meta["structure"],
            "slide_mfe_is_vienna": mfe == meta["mfe"],
            "image_is_this_folds_drawing": len(pics) == 1
            and hashlib.sha256(pics[0].image.blob).hexdigest() == meta["png_file_sha256"],
            "fold_seq_is_traced_seq": meta["fold_seq_is_traced_seq"],
            "fold_temp_is_requested": meta["fold_temp_is_requested"],
            "drawing_seq_is_folded_seq": meta["drawing_seq_is_folded_seq"],
            "drawing_colored": meta["png_colored"],
            "drawing_is_of_this_fold": meta["png_of_drawing"],
        }
        fails += [f"{key[0]} {item_label(it)}: {k} FAILED" for k, ok in checks.items() if not ok]
        seen.add(key)
        # RSAS folds with the same model (noLP, d2), so its sheet values at this temperature should match
        sheet = it.get("sheet_fl" if it["scope"] == "fullength" else "sheet_hp", {}).get(it["temp"], {})
        s_struct, s_mfe = sheet.get("structure"), sheet.get("mfe")
        local_mfe = meta["mfe"]
        if it["scope"] == "hairpin" and s_mfe is not None:
            # RSAS folds the hairpin without its trailing unpaired 3' tail; compare like with like
            trimmed = _rsas_trimmed_hairpin(it)
            if trimmed and trimmed != it["hp_seq"]:
                local_mfe = local_fold.fold(trimmed, it["temp"])["mfe"]
        rows.append({"round": it["round"], "id": it["id"], "tier": it.get("tier"),
                     "fold": SCOPES[it["scope"]].lower(),
                     "temperature_C": it["temp"], "folded_seq": fold_seq(it),
                     "results_file": it["results_file"], "results_full_sequence_row": it["full_row"],
                     "results_hairpin_row": it["hp_row"], "hairpin_seq": it["hp_seq"], "fullength_seq": it["fl_seq"],
                     "fold_engine": meta.get("engine"), "mfe": meta["mfe"],
                     "ensemble_energy": meta.get("ensemble_energy"), "structure": meta["structure"],
                     "rsas_mfe_same_temp": "" if s_mfe is None else s_mfe,
                     "mfe_same_as_rsas": "" if s_mfe is None else _same_mfe(s_mfe, local_mfe),
                     "structure_same_as_rsas": "" if not s_struct else meta["structure"] == s_struct,
                     **checks})
    fails += [f"{k[0]} {item_label(by_key[k])}: no slide" for k in by_key if k not in seen]
    if len(saved.slides) != len(rounds) + len(items):
        fails.append(f"deck has {len(saved.slides)} slides, expected {len(rounds) + len(items)}")
    report = out.with_name(out.stem + " verification.csv") if write_report else None
    if report:
        with report.open("w", newline="", encoding="utf-8") as fh:
            wr = csv.DictWriter(fh, fieldnames=list(rows[0]) if rows else ["round", "id"])
            wr.writeheader()
            wr.writerows(rows)
    if fails:
        raise DeckError(f"BUILD VERIFICATION FAILED ({len(fails)}) - {out.name} was not written; the unchecked file "
                        f"is {tmp.name}:\n" + "\n".join(fails))
    try:
        os.replace(tmp, out)
    except PermissionError as e:
        raise DeckError(f"Could not replace '{out.name}' - close it in PowerPoint and run again.") from e
    compared = [r for r in rows if r["mfe_same_as_rsas"] != ""]
    same = sum(r["mfe_same_as_rsas"] is True for r in compared)
    s_cmp = [r for r in rows if r["structure_same_as_rsas"] != ""]
    s_same = sum(r["structure_same_as_rsas"] is True for r in s_cmp)
    hooks.log(f"BUILD PASS ({out.name}): {len(rows)}/{len(items)} slides - ID under the right round, the traced "
              "sequence on the slide, ViennaRNA folded that exact sequence at the requested temperature, image "
              "drawn from that verified fold")
    if compared:
        hooks.log(f"  MFE identical to the RSAS sheet (same temperature) for {same}/{len(compared)} folds")
    if s_cmp:
        hooks.log(f"  structure identical to the RSAS sheet (same temperature) for {s_same}/{len(s_cmp)} full-length folds")
    return {"slides": len(rows), "report": report, "mfe_matches_rsas": same}


# ---------------------------------------------------------------- whole run (the app's Run button)

def plan_outputs(out_dir, name, tier) -> dict:
    name = safe_name(name)
    if not name:
        raise DeckError("Give the deck a name.")
    if not str(out_dir).strip():
        raise DeckError("Choose an output folder.")
    base = expand(out_dir)
    # Every run gets its own folder named after the deck, so one output folder holds one tidy
    # subfolder per deck. Pointing the app at an existing deck folder reuses it instead of nesting.
    d = base if base.name == name else base / name
    return {"name": name, "dir": d, "deck": d / f"{name}.pptx",
            "excel": d / f"{name} {safe_name(tier_label(tier))} selection.xlsx",
            "mapping": d / f"{name} mapping.json", "work": d / f"{name} structures",
            "report": d / f"{name} verification.csv", "log": d / f"{name} log.txt"}


def round_deck_paths(rounds, plan) -> dict:
    """One extra deck per round, saved next to the combined deck; a single-round run needs none."""
    if len(rounds) < 2:
        return {}
    decks = {r["name"]: plan["dir"] / f"{plan['name']} {safe_name(r['name'])}.pptx" for r in rounds}
    if len(set(decks.values())) != len(decks):
        raise DeckError("Two round names become the same file name - make the round names more different.")
    return decks


def build_decks(rounds, plan, hooks) -> dict:
    """The combined deck (every round, plus the verification CSV), then one verified deck per round."""
    summary = build(plan["mapping"], plan["work"], plan["deck"], hooks)
    decks = round_deck_paths(rounds, plan)
    for name, path in decks.items():
        hooks.check()
        build(plan["mapping"], plan["work"], path, hooks, only_round=name, write_report=False)
    return {**summary, "round_decks": decks}


def preflight(rounds, plan) -> str:
    check_rounds(rounds)
    for r in rounds:
        if expand(r["results_workbook"]).suffix.lower() != ".xlsx":
            raise DeckError(f"'{Path(r['results_workbook']).name}' is not an .xlsx file - export the RSAS results as Excel.")
    try:
        plan["dir"].mkdir(parents=True, exist_ok=True)
        probe = plan["dir"] / ".rnafold-deck-write-test"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
    except OSError as e:
        raise DeckError(f"Cannot save into '{plan['dir']}' ({e}). Choose another output folder.") from e
    for deck in [plan["deck"], *round_deck_paths(rounds, plan).values()]:
        if deck_is_open(deck):
            raise DeckError(f"'{deck.name}' is open in PowerPoint. Close it and run again.")
    return check_vienna()


def check_vienna() -> str:
    """The local folding engine and the drawing library must be importable; returns the engine description."""
    try:
        import matplotlib  # noqa: F401
        import RNA  # noqa: F401
        import pptx  # noqa: F401
    except ImportError as e:
        raise DeckError(f"{e.name} is not installed in this Python. Install it in the rsas environment "
                        "(conda: viennarna, matplotlib, python-pptx) and run again.") from e
    return local_fold.model_description()


class KeepAwake:
    """Hold off idle sleep while a run is going (closing a laptop lid still sleeps).

    Long local runs (thousands of folds) should not be interrupted by idle sleep."""

    ES_CONTINUOUS, ES_SYSTEM_REQUIRED = 0x80000000, 0x00000001

    def __enter__(self):
        self.proc = None
        try:
            if sys.platform == "darwin" and shutil.which("caffeinate"):
                self.proc = subprocess.Popen(["caffeinate", "-i", "-w", str(os.getpid())],
                                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            elif sys.platform == "win32":
                import ctypes
                ctypes.windll.kernel32.SetThreadExecutionState(self.ES_CONTINUOUS | self.ES_SYSTEM_REQUIRED)
        except OSError:
            self.proc = None
        return self

    def __exit__(self, *exc):
        if self.proc is not None and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proc.kill()
        if sys.platform == "win32":
            try:
                import ctypes
                ctypes.windll.kernel32.SetThreadExecutionState(self.ES_CONTINUOUS)
            except OSError:
                pass
        return False


def run_all(rounds, tier, plan, hooks, temps=(DEFAULT_TEMP,), scopes=DEFAULT_SCOPES) -> dict:
    with KeepAwake():
        return _run_all(rounds, tier, plan, hooks, temps, scopes)


def _run_all(rounds, tier, plan, hooks, temps, scopes) -> dict:
    temps, scopes = parse_temps(",".join(temps)), parse_scopes(scopes)
    engine_desc = preflight(rounds, plan)
    started = datetime.now()
    logfile = plan["log"].open("a", encoding="utf-8")

    def log(msg):
        hooks.log(msg)
        logfile.write(f"{datetime.now():%H:%M:%S} {msg}\n")
        logfile.flush()

    h = Hooks(log=log, progress=hooks.progress, stop=hooks.stop)
    try:
        log(f"=== RNAfold Deck run {started:%Y-%m-%d %H:%M} | {tier_label(tier)} | "
            f"{' + '.join(SCOPES[s].lower() for s in scopes)} | {', '.join(temps)} C | "
            f"{engine_desc} | "
            + "; ".join(f"{r['name']} = {Path(r['results_workbook']).name}" for r in rounds))
        h.check()
        log("Step 1 of 3: select hairpins and find their full-length sequences")
        t = trace(rounds, plan["mapping"], h, tier=tier, excel_path=plan["excel"], temps=temps, scopes=scopes)
        h.check()
        log("Step 2 of 3: fold locally with ViennaRNA and draw the structures")
        f = fold(plan["mapping"], plan["work"], h)
        h.check()
        log("Step 3 of 3: build and verify the PowerPoints")
        b = build_decks(rounds, plan, h)
        log(f"=== finished in {max(1, round((datetime.now() - started).total_seconds() / 60))} min -> {plan['deck']}")
        return {**plan, **t, **f, **b}
    except DeckError as e:
        log(f"STOPPED: {e}")
        raise
    except Exception as e:
        log(f"FAILED unexpectedly: {type(e).__name__}: {e}")
        raise
    finally:
        logfile.close()
