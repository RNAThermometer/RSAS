# RNAfold Deck

Sidebar page **RNAfold Deck**: RSAS Excel results → hairpins of the chosen tier(s) → full-length and/or hairpin
structures at 1–5 temperatures → a PowerPoint with one verified slide per fold.

Integrated in RSAS 4.0 from RNAfold Deck 1.3.0. The webserver fold and the Chrome screenshot were replaced by a local engine,
so **no internet connection or browser is needed**.

## What changed versus RNAfold Deck 1.3.0

| Step | 1.3.0 | RSAS module |
|---|---|---|
| Fold | POST to rna.tbi.univie.ac.at, poll the job page | `RNA.fold_compound` with the webserver's model: `-p -d2 --noLP`, Turner 2004 |
| Drawing | download the webserver SVG, screenshot it in headless Chrome/Edge | naview layout + base-pair-probability colors drawn locally (SVG + 300 dpi PNG, matplotlib) |
| Time | ~15–25 min per 100 hairpins | ~1–1.5 s per fold, mostly drawing |
| Checks | page/drawing sequence and temperature | the same checks on the local fold, plus MFE/structure cross-check against the RSAS sheet |

The local result is the webserver's result: `tests/test_deck_local.py` re-folds five saved webserver jobs and
gets the same MFE, dot-bracket, per-nucleotide colors and naview coordinates.

## Use

1. Run an analysis on **Analyze** (writes `Data/Outputs/rna_results.xlsx`), or export results as Excel.
2. **RNAfold Deck** page → **Use latest RSAS results** (the last analysis, `~/RSAS/<input>_<ts>/<input>_rna_results.xlsx`;
   the deck is then saved inside that analysis folder as `<input>_RNAfold_deck_<ts>/`), or
   **Add Results file…** for exported workbooks, one per round in slide order.
3. Tick tiers, choose Full-length / Hairpin / both, fill Temp 1–5, press **Run**.

Command line (same engine):

```bash
python -m RnaThermofinder.deck run --results "~/RSAS/<input>_<ts>/<input>_rna_results.xlsx" --round-name R1 \
    --tier "Tier 1" --fold both --temp 25 --temp 37 --temp 42 --out-dir ~/Documents --name "RNAfold deck"
```

## Output (`<output folder>/<deck name>/`)

| File | Content |
|---|---|
| `<name>.pptx` | title slide per round, one slide per hairpin × fold × temperature |
| `<name> Tier 1 selection.xlsx` | selected Hairpin Analysis rows and their Full Sequence rows |
| `<name> verification.csv` | per slide: sequence, MFE, ensemble energy, structure, RSAS cross-check, all checks |
| `<name> structures/` | per fold: `<input>_NNN_<id>[_hp][_<T>C]` `.json` (fold data), `.svg` (vector, editable), `.png` (slide image) |
| `<name> log.txt`, `<name> mapping.json` | run log, traced IDs |

`mfe_same_as_rsas` / `structure_same_as_rsas` compare with the RSAS sheet at the same temperature. For
hairpin folds RSAS drops the trailing unpaired 3' tail before folding, so that comparison folds the trimmed
hairpin too; the slide shows the hairpin exactly as in `Hairpin_Sequence`.

## Files

```
RnaThermofinder/deck/
  local_fold.py   ViennaRNA fold, probability colors, naview layout, SVG/PNG drawing
  engine.py       select → trace → fold → build + verify (from RNAfold Deck 1.3.0)
  panel.py        DeckPanel (RSAS page) and standalone window: python -m RnaThermofinder.deck.panel
  cli.py          python -m RnaThermofinder.deck ...
tests/test_deck_local.py, tests/deck_webserver_fixtures/
```
