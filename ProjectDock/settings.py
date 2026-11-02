
import tkinter as tk
import json

from pathlib import Path
from tkinter import colorchooser, messagebox


BG = "#080D19"
PANEL = "#111D30"
PANEL_LIGHT = "#17263C"
BORDER = "#243650"
TEXT = "#E8F0FC"
MUTED = "#8295B2"
ACCENT = "#65E8D0"
FONT = "Segoe UI"
MONO = "Consolas"


DEFAULT_SETTINGS = {
    "orbital_instability": True,
    "instability_interval": 60,
    "accent_color": ACCENT,
    "starfield": True,
    "show_labels": True,
    "reduce_motion": False
}


class SettingsManager:

    def __init__(self, file_path=None):

        self.file_path = (
            Path(file_path)
            if file_path
            else Path(__file__).with_name("settings.json")
        )

    def load(self):

        settings = DEFAULT_SETTINGS.copy()

        if not self.file_path.exists():
            return settings

        try:
            data = json.loads(
                self.file_path.read_text(encoding="utf-8")
            )

            if not isinstance(data, dict):
                return settings

            settings["orbital_instability"] = bool(
                data.get("orbital_instability", settings["orbital_instability"])
            )

            settings["instability_interval"] = max(
                15,
                min(120, int(data.get("instability_interval", 60)))
            )

            settings["starfield"] = bool(
                data.get("starfield", settings["starfield"])
            )

            settings["show_labels"] = bool(
                data.get("show_labels", settings["show_labels"])
            )

            settings["reduce_motion"] = bool(
                data.get("reduce_motion", settings["reduce_motion"])
            )

            color = data.get("accent_color", ACCENT)

            if isinstance(color, str) and len(color) == 7:
                settings["accent_color"] = color

        except (OSError, json.JSONDecodeError, ValueError, TypeError):
            pass

        return settings

    def save(self, settings):

        clean = DEFAULT_SETTINGS.copy()
        clean.update(settings)

        clean["orbital_instability"] = bool(
            clean["orbital_instability"]
        )

        clean["instability_interval"] = max(
            15,
            min(120, int(clean["instability_interval"]))
        )

        for key in ("starfield", "show_labels", "reduce_motion"):
            clean[key] = bool(clean[key])

        color = clean["accent_color"]

        if not isinstance(color, str) or len(color) != 7:
            raise ValueError("Invalid accent color.")

        temporary = self.file_path.with_suffix(".json.tmp")

        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        temporary.write_text(
            json.dumps(clean, indent=4),
            encoding="utf-8"
        )

        temporary.replace(self.file_path)


class SettingsWindow(tk.Toplevel):

    def __init__(self, parent, settings, on_save):

        super().__init__(parent)

        self.settings = DEFAULT_SETTINGS.copy()
        self.settings.update(settings)

        self.on_save = on_save
        self.accent = self.settings["accent_color"]

        self.title("NorthStar Preferences")
        self.geometry("540x690")
        self.minsize(500, 650)
        self.configure(bg=BG)

        self.transient(parent)
        self.grab_set()

        self.build_ui()

    # --------------------------------------------------
    # HELPERS
    # --------------------------------------------------

    def section(self, parent, title, description=None):

        frame = tk.Frame(
            parent,
            bg=PANEL,
            highlightbackground=BORDER,
            highlightthickness=1,
            padx=17,
            pady=14
        )

        frame.pack(fill="x", pady=(0, 12))

        tk.Label(
            frame,
            text=title,
            bg=PANEL,
            fg=self.accent,
            font=(MONO, 9, "bold")
        ).pack(anchor="w")

        if description:
            tk.Label(
                frame,
                text=description,
                bg=PANEL,
                fg=MUTED,
                font=(FONT, 8),
                wraplength=430,
                justify="left"
            ).pack(anchor="w", pady=(4, 10))

        return frame

    def toggle(self, parent, title, description, key):

        row = tk.Frame(parent, bg=PANEL)
        row.pack(fill="x", pady=5)

        variable = tk.BooleanVar(
            value=self.settings[key]
        )

        tk.Checkbutton(
            row,
            text=title,
            variable=variable,
            bg=PANEL,
            fg=TEXT,
            activebackground=PANEL,
            activeforeground=self.accent,
            selectcolor=PANEL_LIGHT,
            font=(FONT, 9, "bold"),
            relief="flat",
            borderwidth=0
        ).pack(anchor="w")

        tk.Label(
            row,
            text=description,
            bg=PANEL,
            fg=MUTED,
            font=(FONT, 8),
            wraplength=430,
            justify="left"
        ).pack(anchor="w", padx=(24, 0))

        return variable

    # --------------------------------------------------
    # UI
    # --------------------------------------------------

    def build_ui(self):

        header = tk.Frame(self, bg=BG)
        header.pack(fill="x", padx=25, pady=(23, 17))

        tk.Label(
            header,
            text="SYSTEM PREFERENCES",
            bg=BG,
            fg=self.accent,
            font=(MONO, 11, "bold")
        ).pack(anchor="w")

        tk.Label(
            header,
            text="Configure the behavior and appearance of Project Dock.",
            bg=BG,
            fg=MUTED,
            font=(FONT, 9)
        ).pack(anchor="w", pady=(5, 0))

        content = tk.Frame(self, bg=BG)
        content.pack(
            fill="both",
            expand=True,
            padx=25
        )

        # Appearance
        appearance = self.section(
            content,
            "01  /  APPEARANCE",
            "Personalize your command center."
        )

        self.starfield_var = self.toggle(
            appearance,
            "Background starfield",
            "Display decorative stars and distant space details.",
            "starfield"
        )

        self.labels_var = self.toggle(
            appearance,
            "Planet labels",
            "Show project names and icons beside their planets.",
            "show_labels"
        )

        self.motion_var = self.toggle(
            appearance,
            "Reduce motion",
            "Reduce decorative movement and disable orbital instability.",
            "reduce_motion"
        )

        color_row = tk.Frame(appearance, bg=PANEL)
        color_row.pack(fill="x", pady=(12, 0))

        tk.Label(
            color_row,
            text="ACCENT COLOR",
            bg=PANEL,
            fg=MUTED,
            font=(MONO, 8, "bold")
        ).pack(side="left")

        self.color_preview = tk.Label(
            color_row,
            text="      ",
            bg=self.accent
        )
        self.color_preview.pack(side="right", padx=(8, 0), ipady=5)

        self.color_value = tk.Label(
            color_row,
            text=self.accent,
            bg=PANEL,
            fg=TEXT,
            font=(MONO, 8)
        )
        self.color_value.pack(side="right")

        tk.Button(
            color_row,
            text="Choose",
            command=self.choose_accent,
            bg=PANEL_LIGHT,
            fg=TEXT,
            activebackground=BORDER,
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=5
        ).pack(side="right", padx=(0, 10))

        # Simulation
        simulation = self.section(
            content,
            "02  /  ORBITAL SIMULATION",
            "Control the behavior of your miniature project system."
        )

        self.instability_var = self.toggle(
            simulation,
            "Enable orbital instability",
            "Occasionally, a planet will drift from its orbit and be recovered.",
            "orbital_instability"
        )

        tk.Label(
            simulation,
            text="AVERAGE TIME BETWEEN INCIDENTS",
            bg=PANEL,
            fg=MUTED,
            font=(MONO, 8, "bold")
        ).pack(anchor="w", pady=(13, 5))

        self.interval_var = tk.IntVar(
            value=self.settings["instability_interval"]
        )

        self.interval_value = tk.Label(
            simulation,
            text=f"{self.interval_var.get()} seconds",
            bg=PANEL,
            fg=TEXT,
            font=(MONO, 10, "bold")
        )
        self.interval_value.pack(anchor="w")

        tk.Scale(
            simulation,
            from_=15,
            to=120,
            resolution=5,
            orient="horizontal",
            variable=self.interval_var,
            command=self.update_interval,
            bg=PANEL,
            fg=TEXT,
            troughcolor=PANEL_LIGHT,
            highlightthickness=0,
            activebackground=self.accent,
            showvalue=False,
            relief="flat"
        ).pack(fill="x", pady=(2, 0))

        tk.Label(
            simulation,
            text="Higher values mean fewer instability events.",
            bg=PANEL,
            fg=MUTED,
            font=(FONT, 8)
        ).pack(anchor="w")

        # Footer
        footer = tk.Frame(self, bg=BG)
        footer.pack(fill="x", padx=25, pady=20)

        tk.Button(
            footer,
            text="Cancel",
            command=self.destroy,
            bg=PANEL,
            fg=MUTED,
            activebackground=BORDER,
            relief="flat",
            cursor="hand2",
            padx=15,
            pady=9
        ).pack(side="right", padx=(8, 0))

        tk.Button(
            footer,
            text="Save Preferences",
            command=self.save_settings,
            bg=self.accent,
            fg=BG,
            activebackground="#8CFFE9",
            relief="flat",
            cursor="hand2",
            font=(FONT, 9, "bold"),
            padx=15,
            pady=9
        ).pack(side="right")

    # --------------------------------------------------
    # INTERACTION
    # --------------------------------------------------

    def choose_accent(self):

        result = colorchooser.askcolor(
            color=self.accent,
            parent=self,
            title="Choose Interface Accent"
        )

        if result and result[1]:

            self.accent = result[1]

            self.color_preview.configure(bg=self.accent)
            self.color_value.configure(text=self.accent)

    def update_interval(self, value):

        self.interval_value.configure(
            text=f"{int(float(value))} seconds"
        )

    def save_settings(self):

        new_settings = {
            "orbital_instability": self.instability_var.get(),
            "instability_interval": self.interval_var.get(),
            "accent_color": self.accent,
            "starfield": self.starfield_var.get(),
            "show_labels": self.labels_var.get(),
            "reduce_motion": self.motion_var.get()
        }

        if new_settings["reduce_motion"]:
            new_settings["orbital_instability"] = False

        if self.on_save(new_settings):
            self.destroy()
