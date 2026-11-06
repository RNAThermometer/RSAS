"""RNAfold Deck page for RSAS (also runs as its own window).

Add the Excel file(s) RSAS exported (or the latest RSAS run), name each round, tick the tier(s), what to fold
(full-length, hairpin or both) and the temperatures, press Run. The page selects the hairpins, finds each one's
full-length sequence, folds it locally with ViennaRNA (the RNAfold webserver's model), draws the structure
colored by base-pair probability, and builds a PowerPoint it has checked slide by slide. No internet connection
or browser is needed.

    DeckPanel(master, latest_results=callable)   embed in RSAS (RNAGUI.py, sidebar page "RNAfold Deck")
    python -m RnaThermofinder.deck.panel         standalone window
"""
from __future__ import annotations

import os
import queue
import subprocess
import sys
import threading
import traceback
import re
from datetime import date, datetime
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from . import engine, local_fold

APP = "RNAfold Deck"
MUTED = ("gray35", "gray65")
PLAIN = ("gray10", "gray90")


def open_path(path) -> None:
    path = str(path)
    if sys.platform == "win32":
        os.startfile(path)  # noqa: S606 - opens the user's own output file
    elif sys.platform == "darwin":
        subprocess.run(["open", path], check=False)
    else:
        subprocess.run(["xdg-open", path], check=False)


class RoundRow(ctk.CTkFrame):
    def __init__(self, master, path: str, name: str, on_remove):
        super().__init__(master, fg_color=("gray88", "gray20"))
        self.path = path
        self.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self, text=Path(path).name, anchor="w").grid(row=0, column=0, sticky="ew", padx=(12, 8), pady=8)
        ctk.CTkLabel(self, text="Round name", text_color=MUTED).grid(row=0, column=1, padx=(8, 4))
        self.name = ctk.CTkEntry(self, width=170)
        self.name.insert(0, name)
        self.name.grid(row=0, column=2, padx=4)
        self.remove = ctk.CTkButton(self, text="Remove", width=80, fg_color="transparent", border_width=1,
                                    text_color=PLAIN, command=lambda: on_remove(self))
        self.remove.grid(row=0, column=3, padx=(8, 12))


class DeckPanel(ctk.CTkFrame):
    FOLDS = {"Full-length": ("fullength",), "Hairpin": ("hairpin",), "Full-length + hairpin": ("fullength", "hairpin")}
    FOLD_HINTS = {"Full-length": "the whole sequence the hairpin sits in (Full Sequence tab)",
                  "Hairpin": "the hairpin sequence alone (Hairpin Analysis tab)",
                  "Full-length + hairpin": "both, one slide each, kept together per hairpin"}

    def __init__(self, master, latest_results=None, **kwargs):
        """latest_results: optional callable returning the path of the newest RSAS Excel export (or None)."""
        kwargs.setdefault("fg_color", "transparent")
        super().__init__(master, **kwargs)
        self.latest_results = latest_results
        self.events: queue.Queue = queue.Queue()
        self.stop_flag = threading.Event()
        self.worker: threading.Thread | None = None
        self.rows: list[RoundRow] = []
        self.result: dict | None = None
        bold = ctk.CTkFont(size=15, weight="bold")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(5, weight=1)

        head = ctk.CTkFrame(self, fg_color="transparent")
        head.grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 4))
        ctk.CTkLabel(head, text=APP, font=ctk.CTkFont(size=24, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(head, text="RSAS Results  →  tier hairpins  →  full-length and hairpin structures (ViennaRNA, "
                                "local)  →  verified PowerPoint", text_color=MUTED).pack(anchor="w")

        files = ctk.CTkFrame(self)
        files.grid(row=1, column=0, sticky="ew", padx=20, pady=8)
        files.grid_columnconfigure(0, weight=1)
        bar = ctk.CTkFrame(files, fg_color="transparent")
        bar.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 6))
        ctk.CTkLabel(bar, text="1   RSAS Results workbooks", font=bold).pack(side="left")
        ctk.CTkLabel(bar, text="   one per round, in slide order", text_color=MUTED).pack(side="left")
        self.add_button = ctk.CTkButton(bar, text="Add Results file…", width=150, command=self.add_files)
        self.add_button.pack(side="right")
        self.latest_button = ctk.CTkButton(bar, text="Use latest RSAS results", width=180, command=self.add_latest)
        if latest_results is not None:
            self.latest_button.pack(side="right", padx=(0, 8))
        self.list = ctk.CTkScrollableFrame(files, height=150, fg_color="transparent")
        self.list.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 10))
        self.list.grid_columnconfigure(0, weight=1)
        self.empty = ctk.CTkLabel(self.list, text_color=MUTED,
                                  text="No files yet. Add the Excel file(s) RSAS exported "
                                       "(they have Hairpin Analysis and Full Sequence tabs).")
        self.empty.grid(row=0, column=0, pady=24)

        sets = ctk.CTkFrame(self)
        sets.grid(row=2, column=0, sticky="ew", padx=20, pady=8)
        sets.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(sets, text="2   Settings", font=bold).grid(row=0, column=0, columnspan=3, sticky="w",
                                                                padx=12, pady=(12, 6))
        ctk.CTkLabel(sets, text="Hairpin tier").grid(row=1, column=0, sticky="w", padx=12, pady=6)
        tiers = ctk.CTkFrame(sets, fg_color="transparent")
        tiers.grid(row=1, column=1, columnspan=2, sticky="ew", pady=6)
        self.tiers_frame = tiers
        self.tiers = []  # one tick box per standard tier; tick as many as you want (Tier 1 starts ticked)
        for i, tier in enumerate(engine.TIERS):
            box = ctk.CTkCheckBox(tiers, text=tier, width=90)
            box.pack(side="left", padx=(0, 10 if i < len(engine.TIERS) - 1 else 0))
            self.tiers.append(box)
        self.tiers[0].select()
        # RSAS can be set up with its own class names: the Custom tiers switch swaps the tick boxes for text
        # boxes, one per class (up to MAX_TIERS), typed exactly as they appear in HP_Quality_Score_Class
        self.custom_frame = ctk.CTkFrame(sets, fg_color="transparent")
        self.custom_frame.grid(row=1, column=1, columnspan=2, sticky="ew", pady=6)
        self.custom_tiers = []  # blank boxes are skipped
        for i in range(engine.MAX_TIERS):
            box = ctk.CTkEntry(self.custom_frame, width=88, placeholder_text=f"Tier {i + 1}")
            box.pack(side="left", padx=(0, 6))
            self.custom_tiers.append(box)
        self.custom_switch = ctk.CTkSwitch(sets, text="Custom tiers", command=self.describe_tiers)
        self.custom_switch.grid(row=2, column=0, sticky="w", padx=12, pady=(0, 6))
        self.tiers_hint = ctk.CTkLabel(sets, text="", text_color=MUTED)
        self.tiers_hint.grid(row=2, column=1, columnspan=2, sticky="w", pady=(0, 6))
        self.describe_tiers()
        ctk.CTkLabel(sets, text="Fold").grid(row=3, column=0, sticky="w", padx=12, pady=6)
        folds = ctk.CTkFrame(sets, fg_color="transparent")
        folds.grid(row=3, column=1, columnspan=2, sticky="ew", pady=6)
        self.scope = ctk.CTkSegmentedButton(folds, values=list(self.FOLDS), command=lambda _: self.describe_fold())
        self.scope.set("Full-length + hairpin")
        self.scope.pack(side="left")
        self.scope_hint = ctk.CTkLabel(folds, text="", text_color=MUTED)
        self.scope_hint.pack(side="left", padx=(12, 0))
        self.describe_fold()
        ctk.CTkLabel(sets, text="Temperature").grid(row=4, column=0, sticky="w", padx=12, pady=6)
        temps = ctk.CTkFrame(sets, fg_color="transparent")
        temps.grid(row=4, column=1, columnspan=2, sticky="ew", pady=6)
        self.temps = []  # one box per temperature, Temp 1 to Temp 5; blanks are skipped
        for i in range(engine.MAX_TEMPS):
            ctk.CTkLabel(temps, text=f"Temp {i + 1}", text_color=MUTED).pack(side="left", padx=(12 if i else 0, 4))
            box = ctk.CTkEntry(temps, width=56, placeholder_text="°C")
            box.pack(side="left")
            self.temps.append(box)
        self.temps[0].insert(0, engine.DEFAULT_TEMP)
        self.temps_hint = ctk.CTkLabel(sets, text_color=MUTED, wraplength=700, justify="left",
                                       text=f"°C, fill in as many boxes as you want (blank boxes are ignored; "
                                            f"{engine.DEFAULT_TEMP} is the RNAfold default; RSAS used 25/37/42); "
                                            "one slide per hairpin per fold per temperature")
        self.temps_hint.grid(row=5, column=1, columnspan=2, sticky="w", pady=(0, 6))
        ctk.CTkLabel(sets, text="Deck name").grid(row=6, column=0, sticky="w", padx=12, pady=6)
        self.deck_name = ctk.CTkEntry(sets)
        self._auto_deck_name = f"RNAfold deck {date.today():%Y-%m-%d}"
        self.deck_name.insert(0, self._auto_deck_name)
        self.deck_name.grid(row=6, column=1, sticky="ew", pady=6)
        ctk.CTkLabel(sets, text="Output folder").grid(row=7, column=0, sticky="w", padx=12, pady=(6, 12))
        self.out_dir = ctk.CTkEntry(sets)
        self.out_dir.insert(0, str(Path.home() / "Downloads"))
        self.out_dir.grid(row=7, column=1, sticky="ew", pady=(6, 12))
        self.browse = ctk.CTkButton(sets, text="Browse…", width=90, command=self.pick_folder)
        self.browse.grid(row=7, column=2, padx=12, pady=(6, 12))

        run = ctk.CTkFrame(self)
        run.grid(row=3, column=0, sticky="ew", padx=20, pady=8)
        run.grid_columnconfigure(1, weight=1)
        self.run_button = ctk.CTkButton(run, text="Run", width=120, height=40, font=bold, command=self.start)
        self.run_button.grid(row=0, column=0, padx=12, pady=12)
        prog = ctk.CTkFrame(run, fg_color="transparent")
        prog.grid(row=0, column=1, sticky="ew", pady=12)
        prog.grid_columnconfigure(0, weight=1)
        self.stage = ctk.CTkLabel(prog, text="Ready", anchor="w")
        self.stage.grid(row=0, column=0, sticky="ew")
        self.bar = ctk.CTkProgressBar(prog)
        self.bar.set(0)
        self.bar.grid(row=1, column=0, sticky="ew", pady=(4, 0))
        self.stop_button = ctk.CTkButton(run, text="Stop", width=90, state="disabled", fg_color="transparent",
                                         border_width=1, text_color=PLAIN, command=self.request_stop)
        self.stop_button.grid(row=0, column=2, padx=12)

        outs = ctk.CTkFrame(self, fg_color="transparent")
        outs.grid(row=4, column=0, sticky="ew", padx=20, pady=(4, 0))
        self.open_buttons = {}
        for key, label in (("deck", "Open PowerPoint"), ("excel", "Open tier selection"),
                           ("report", "Open verification"), ("dir", "Open folder")):
            button = ctk.CTkButton(outs, text=label, width=160, state="disabled",
                                   command=lambda k=key: self.open_output(k))
            button.pack(side="left", padx=(0, 8))
            self.open_buttons[key] = button

        self.log_box = ctk.CTkTextbox(self, wrap="word", font=ctk.CTkFont(family="Courier", size=12))
        self.log_box.grid(row=5, column=0, sticky="nsew", padx=20, pady=(8, 16))
        self.write_log("Add the RSAS Results workbook(s), check the settings, then press Run.\n"
                       f"Folds locally with {local_fold.model_description()}; "
                       "no internet connection or browser needed.")
        self.after(100, self.poll)

    # ---- files and settings
    def add_files(self):
        paths = filedialog.askopenfilenames(title="Choose RSAS Results workbook(s)",
                                            filetypes=[("Excel workbook", "*.xlsx"), ("All files", "*.*")])
        for path in paths:
            self.add_path(path)

    def add_latest(self):
        path = self.latest_results() if self.latest_results else None
        if not path or not Path(path).is_file():
            messagebox.showinfo(APP, "No RSAS Excel results yet. Run an analysis on the Analyze page first "
                                     "(it writes Data/Outputs/rna_results.xlsx), or add a file you exported.")
            return
        # the deck goes into that analysis's own folder, next to its results
        self.add_path(str(path))

    def add_path(self, path: str, follow_folder: bool = True):
        if any(r.path == path for r in self.rows):
            return
        if not self.rows and self.deck_name.get().strip() == self._auto_deck_name:
            # every deck file starts with the input FASTA's name: <input>_rna_results.xlsx -> <input>_RNAfold_deck_...
            stem = re.sub(r"_rna_results(_\d{8}_\d{6})?$", "", Path(path).stem) or "RNAfold"
            self._auto_deck_name = f"{stem}_RNAfold_deck_{datetime.now():%Y%m%d_%H%M}"
            self.deck_name.delete(0, "end")
            self.deck_name.insert(0, self._auto_deck_name)
        if follow_folder and not self.rows and self.out_dir.get().strip() == str(Path.home() / "Downloads"):
            self.out_dir.delete(0, "end")  # default: save next to the Results files
            self.out_dir.insert(0, str(Path(path).parent))
        self.empty.grid_remove()
        row = RoundRow(self.list, path, f"R{len(self.rows) + 1}", self.remove_row)
        row.grid(row=len(self.rows) + 1, column=0, sticky="ew", pady=4)
        self.rows.append(row)

    def remove_row(self, row: RoundRow):
        self.rows.remove(row)
        row.destroy()
        for i, r in enumerate(self.rows, start=1):
            r.grid(row=i, column=0, sticky="ew", pady=4)
        if not self.rows:
            self.empty.grid()

    def chosen_temps(self) -> list[str]:
        return engine.parse_temps(",".join(box.get() for box in self.temps))

    def chosen_tiers(self) -> list[str]:
        if self.custom_switch.get():
            return engine.parse_tiers([box.get() for box in self.custom_tiers])
        return engine.parse_tiers([box.cget("text") for box in self.tiers if box.get()])

    def describe_tiers(self):
        """Show the tick boxes or the custom class boxes, whichever the switch says."""
        if self.custom_switch.get():
            self.tiers_frame.grid_remove()
            self.custom_frame.grid()
            hint = ("type each class exactly as RSAS wrote it in HP_Quality_Score_Class, up to "
                    f"{engine.MAX_TIERS} (blank boxes are ignored)")
        else:
            self.custom_frame.grid_remove()
            self.tiers_frame.grid()
            hint = "tick one or several of RSAS's standard classes; switch on Custom tiers if RSAS used other names"
        self.tiers_hint.configure(text=hint)

    def describe_fold(self):
        self.scope_hint.configure(text=self.FOLD_HINTS[self.scope.get()])

    def chosen_scopes(self) -> list[str]:
        return engine.parse_scopes(self.FOLDS[self.scope.get()])

    def pick_folder(self):
        chosen = filedialog.askdirectory(title="Choose where to save the deck",
                                         initialdir=self.out_dir.get() or str(Path.home()))
        if chosen:
            self.out_dir.delete(0, "end")
            self.out_dir.insert(0, chosen)

    # ---- running
    def write_log(self, msg: str):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", msg + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def set_running(self, running: bool):
        state = "disabled" if running else "normal"
        for widget in (self.run_button, self.add_button, self.latest_button, self.browse, self.deck_name, self.out_dir,
                       self.scope, self.custom_switch, *self.tiers, *self.custom_tiers, *self.temps):
            widget.configure(state=state)
        for r in self.rows:
            r.name.configure(state=state)
            r.remove.configure(state=state)
        self.stop_button.configure(state="normal" if running else "disabled")
        if running:
            for button in self.open_buttons.values():
                button.configure(state="disabled")

    def start(self):
        if self.worker and self.worker.is_alive():
            return
        rounds = [{"name": r.name.get().strip(), "results_workbook": r.path} for r in self.rows]
        try:
            tier, temps, scopes = self.chosen_tiers(), self.chosen_temps(), self.chosen_scopes()
            plan = engine.plan_outputs(self.out_dir.get().strip(), self.deck_name.get().strip(), tier)
            engine.preflight(rounds, plan)
        except engine.DeckError as e:
            messagebox.showwarning(APP, str(e))
            return
        self.stop_flag.clear()
        self.result = None
        self.set_running(True)
        self.bar.set(0)
        self.stage.configure(text="Starting…")
        hooks = engine.Hooks(log=lambda m: self.events.put(("log", m)),
                             progress=lambda s, d, t: self.events.put(("progress", s, d, t)), stop=self.stop_flag)
        self.worker = threading.Thread(target=self.work, args=(rounds, tier, temps, scopes, plan, hooks), daemon=True)
        self.worker.start()

    def work(self, rounds, tier, temps, scopes, plan, hooks):
        try:
            self.events.put(("done", engine.run_all(rounds, tier, plan, hooks, temps=temps, scopes=scopes)))
        except engine.Cancelled as e:
            self.events.put(("stopped", str(e)))
        except engine.DeckError as e:
            self.events.put(("error", str(e)))
        except Exception:  # noqa: BLE001 - show anything unexpected instead of failing silently
            self.events.put(("error", "Unexpected problem:\n" + traceback.format_exc()))

    def request_stop(self):
        self.stop_flag.set()
        self.stop_button.configure(state="disabled")
        self.stage.configure(text="Stopping after the current step…")

    def poll(self):
        try:
            while True:
                event = self.events.get_nowait()
                kind = event[0]
                if kind == "log":
                    self.write_log(event[1])
                elif kind == "progress":
                    _, stage, done, total = event
                    self.stage.configure(text=f"{stage}  ({done:,} / {total:,})" if total else stage)
                    self.bar.set(min(done / total, 1.0) if total else 0)
                elif kind == "done":
                    self.result = event[1]
                    self.set_running(False)
                    self.bar.set(1)
                    self.stage.configure(text=f"Done - {self.result['slides']} slides verified")
                    for button in self.open_buttons.values():
                        button.configure(state="normal")
                    extra = len(self.result.get("round_decks", {}))
                    messagebox.showinfo(APP, f"Done. {self.result['slides']} structure slides, every one verified."
                                             + (f"\nPlus one deck per round ({extra} files)." if extra else "")
                                             + f"\n\nSaved in:\n{self.result['dir']}")
                else:
                    self.set_running(False)
                    self.stage.configure(text="Stopped" if kind == "stopped" else "Stopped - see the message")
                    self.write_log(event[1] if kind == "stopped" else "PROBLEM: " + event[1])
                    if kind == "error":
                        messagebox.showerror(APP, event[1][:1500])
        except queue.Empty:
            pass
        self.after(100, self.poll)

    def open_output(self, key: str):
        if self.result and Path(self.result[key]).exists():
            open_path(self.result[key])

    def is_running(self) -> bool:
        return bool(self.worker and self.worker.is_alive())

    def confirm_close(self) -> bool:
        """For the host window's close handler: True when it is fine to close."""
        if self.is_running():
            if not messagebox.askyesno(APP, "An RNAfold Deck run is in progress. Stop it and close?"):
                return False
            self.stop_flag.set()
        return True


class App(ctk.CTk):
    """Standalone window holding the same panel."""

    def __init__(self):
        super().__init__()
        self.title(APP)
        self.geometry("1000x900")
        self.minsize(820, 660)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.panel = DeckPanel(self)
        self.panel.grid(row=0, column=0, sticky="nsew")
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_close(self):
        if self.panel.confirm_close():
            self.destroy()


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    ctk.set_appearance_mode("System")
    app = App()
    if "--selftest" in argv:
        import tempfile

        from openpyxl import Workbook
        from pptx import Presentation
        with tempfile.TemporaryDirectory() as tmp:  # a packaged app must carry pptx's slide template
            Presentation().save(Path(tmp) / "check.pptx")
            Workbook().save(Path(tmp) / "check.xlsx")
        fixture = Path(__file__).resolve().parents[2] / "Data" / "Outputs" / "rna_results.xlsx"
        app.panel.add_path(str(fixture))
        app.panel.add_path(str(fixture) + ".second")
        app.panel.remove_row(app.panel.rows[-1])
        app.panel.set_running(True)
        app.panel.set_running(False)
        ok = len(app.panel.rows) == 1 and app.panel.rows[0].name.get() == "R1"
        ok = ok and app.panel.chosen_temps() == ["37"] and app.panel.temps[0].cget("state") == "normal"
        for box, value in zip(app.panel.temps, ("25", "", "37", "42", "")):  # blank boxes are skipped
            box.delete(0, "end")
            box.insert(0, value)
        ok = ok and app.panel.chosen_temps() == ["25", "37", "42"]
        ok = ok and app.panel.chosen_scopes() == ["fullength", "hairpin"]
        ok = ok and app.panel.chosen_tiers() == ["Tier 1"] and app.panel.tiers[0].cget("state") == "normal"
        app.panel.tiers[2].select()
        ok = ok and app.panel.chosen_tiers() == ["Tier 1", "Tier 3"]
        app.panel.tiers[0].deselect()
        app.panel.tiers[2].deselect()
        try:
            app.panel.chosen_tiers()
            ok = False
        except engine.DeckError:
            app.panel.tiers[0].select()
        app.panel.custom_switch.select()  # custom classes: typed labels, blanks skipped, standard names still recognised
        app.panel.describe_tiers()
        for box, value in zip(app.panel.custom_tiers, ("High", "", "Tier 2", "Medium")):
            box.delete(0, "end")
            box.insert(0, value)
        ok = ok and app.panel.chosen_tiers() == ["Tier 2", "High", "Medium"] and "exactly" in app.panel.tiers_hint.cget("text")
        ok = ok and not app.panel.tiers_frame.winfo_manager() and app.panel.custom_frame.winfo_manager() == "grid"
        app.panel.custom_switch.deselect()
        app.panel.describe_tiers()
        ok = ok and app.panel.chosen_tiers() == ["Tier 1"] and app.panel.tiers_frame.winfo_manager() == "grid"
        app.panel.scope.set("Hairpin")
        app.panel.describe_fold()
        ok = ok and app.panel.chosen_scopes() == ["hairpin"] and "alone" in app.panel.scope_hint.cget("text")
        app.after(1200, app.destroy)
        app.mainloop()
        print("GUI SELFTEST PASS" if ok else "GUI SELFTEST FAILED")
        return 0 if ok else 1
    app.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
