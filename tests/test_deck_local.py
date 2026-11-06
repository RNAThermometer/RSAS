"""The local ViennaRNA fold and drawing reproduce the RNAfold webserver results saved by RNAfold Deck 1.3.0.

    python -m pytest tests/test_deck_local.py      (or: python tests/test_deck_local.py)
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from RnaThermofinder.deck import local_fold  # noqa: E402

FIX = Path(__file__).parent / "deck_webserver_fixtures"
CASES = sorted(p.stem for p in FIX.glob("*.json"))


def _web(stem):
    meta = json.loads((FIX / f"{stem}.json").read_text())
    svg = (FIX / f"{stem}.svg").read_text()
    circles = sorted((int(i), float(x), float(y)) for i, x, y in
                     re.findall(r'<circle id="c(\d+)" cx="([-\d.]+)" cy="([-\d.]+)"', svg))
    probs = re.search(r"PROBS = new Array\(([^)]*)\)", svg).group(1).replace("'", "").split(",")
    return meta, [(x, y) for _, x, y in circles], probs


def test_same_mfe_structure_colors_and_layout():
    assert CASES
    for stem in CASES:
        meta, web_xy, web_colors = _web(stem)
        res = local_fold.fold(meta["seq"], meta.get("temp", "37"))
        assert res["mfe"] == meta["mfe"], stem
        assert res["structure"] == meta["structure"], stem
        assert [local_fold.prob_color(p) for p in res["prob"]] == web_colors, stem
        mine = local_fold.layout(res["structure"])
        dx, dy = web_xy[0][0] - mine[0][0], web_xy[0][1] - mine[0][1]   # same picture, shifted
        assert max(max(abs(a[0] + dx - b[0]), abs(a[1] + dy - b[1])) for a, b in zip(mine, web_xy)) < 1e-3, stem


def test_drawings_written(tmp_path=None):
    import tempfile
    out = Path(tmp_path or tempfile.mkdtemp())
    meta, _, _ = _web(CASES[0])
    res = local_fold.fold(meta["seq"], 37)
    local_fold.write_svg(res, out / "a.svg")
    local_fold.write_png(res, out / "a.png")
    assert local_fold.drawn_letters((out / "a.svg").read_text()) == res["seq"]
    assert (out / "a.png").stat().st_size > 10000


if __name__ == "__main__":
    test_same_mfe_structure_colors_and_layout()
    test_drawings_written()
    print(f"PASS: {len(CASES)} webserver folds reproduced locally (MFE, structure, colors, layout)")


def test_input_stem_and_run_dirs():
    import tempfile
    from settings_manager import input_stem, new_run_dir, remove_if_empty
    assert input_stem("/x/results_Roselike_withgene Teste.fasta") == "results_Roselike_withgene Teste"
    assert input_stem("a/Rose like_v2.fasta.gz") == "Rose like_v2"
    assert input_stem("weird:na*me.fna") == "weird_na_me"
    assert input_stem("") == "rsas"
    base = Path(tempfile.mkdtemp())
    a, b = new_run_dir("pool", base=base), new_run_dir("pool", base=base)
    assert a != b and a.name.startswith("pool_") and b.is_dir()
    remove_if_empty(b)
    assert not b.exists()


def test_deck_files_named_after_input():
    from RnaThermofinder.deck import engine
    assert engine.results_stem("Rose like pool_rna_results.xlsx") == "Rose like pool"
    it = {"round": "R1", "n": 1, "id": "seq1", "scope": "hairpin", "temp": "25",
          "results_file": "Rose like pool_rna_results.xlsx"}
    assert engine.item_paths("/tmp/w", it)[3].name == "Rose like pool_001_seq1_hp_25C.png"
