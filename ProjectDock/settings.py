
import tkinter as tk

from pathlib import Path
import json


BG = "#0b1020"
PANEL = "#151f33"
BORDER = "#263651"
TEXT = "#e6edf7"
MUTED = "#8da2c0"
ACCENT = "#66e3c4"


DEFAULT_SETTINGS = {
    "orbital_instability": True,
    "instability_interval": 60
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

            if isinstance(data, dict):

                settings["orbital_instability"] = bool(
                    data.get("orbital_instability", True)
                )

                settings["instability_interval"] = max(
                    15,
                    min(
                        120,
                        int(data.get("instability_interval", 60))
                    )
                )

        except (OSError, json.JSONDecodeError, ValueError, TypeError):
            pass

        return settings

    def save(self, settings):

        self.file_path.write_text(
            json.dumps(settings, indent=4),
            encoding="utf-8"
        )


class SettingsWindow(tk.Toplevel):

    def __init__(self, parent, settings, on_save):

        super().__init__(parent)

        self.settings = settings.copy()
        self.on_save = on_save

        self.title("Project Dock Settings")
        self.geometry("440x370")
        self.resizable(False, False)
        self.configure(bg=BG)

        self.transient(parent)
        self.grab_set()

        self.build_ui()

    def build_ui(self):

        tk.Label(
            self,
            text="SYSTEM SETTINGS",
            bg=BG,
            fg=ACCENT,
            font=("Consolas", 12, "bold")
        ).pack(anchor="w", padx=25, pady=(25, 5))

        tk.Label(
            self,
            text="Configure how your project solar system behaves.",
            bg=BG,
            fg=MUTED,
            font=("Segoe UI", 9)
        ).pack(anchor="w", padx=25, pady=(0, 20))

        section = tk.Frame(
            self,
            bg=PANEL,
            highlightbackground=BORDER,
            highlightthickness=1,
            padx=18,
            pady=16
        )

        section.pack(fill="x", padx=25)

        self.enabled_var = tk.BooleanVar(
            value=self.settings["orbital_instability"]
        )

        tk.Checkbutton(
            section,
            text="Enable orbital instability",
            variable=self.enabled_var,
            bg=PANEL,
            fg=TEXT,
            activebackground=PANEL,
            activeforeground=ACCENT,
            selectcolor=BG,
            font=("Segoe UI", 10, "bold")
        ).pack(anchor="w")

        tk.Label(
            section,
            text=(
                "Occasionally, planets lose stability and drift "
                "out of their assigned orbits."
            ),
            bg=PANEL,
            fg=MUTED,
            font=("Segoe UI", 9),
            wraplength=340,
            justify="left"
        ).pack(anchor="w", pady=(5, 18))

        tk.Label(
            section,
            text="AVERAGE TIME BETWEEN INCIDENTS",
            bg=PANEL,
            fg=ACCENT,
            font=("Consolas", 8, "bold")
        ).pack(anchor="w")

        self.interval_var = tk.IntVar(
            value=self.settings["instability_interval"]
        )

        self.value_label = tk.Label(
            section,
            text=f"{self.interval_var.get()} seconds",
            bg=PANEL,
            fg=TEXT,
            font=("Consolas", 10)
        )

        self.value_label.pack(anchor="w", pady=(5, 0))

        tk.Scale(
            section,
            from_=15,
            to=120,
            resolution=5,
            orient="horizontal",
            variable=self.interval_var,
            command=self.update_interval,
            bg=PANEL,
            fg=TEXT,
            troughcolor=BG,
            highlightthickness=0,
            activebackground=ACCENT,
            showvalue=False
        ).pack(fill="x")

        tk.Label(
            self,
            text="Higher values mean fewer instability events.",
            bg=BG,
            fg=MUTED,
            font=("Segoe UI", 8)
        ).pack(anchor="w", padx=27, pady=(10, 0))

        buttons = tk.Frame(self, bg=BG)
        buttons.pack(side="bottom", fill="x", padx=25, pady=20)

        tk.Button(
            buttons,
            text="Cancel",
            command=self.destroy,
            bg=PANEL,
            fg=MUTED,
            relief="flat",
            padx=15,
            pady=8
        ).pack(side="right", padx=(8, 0))

        tk.Button(
            buttons,
            text="Save Settings",
            command=self.save_settings,
            bg="#203b3b",
            fg=ACCENT,
            relief="flat",
            padx=15,
            pady=8
        ).pack(side="right")

    def update_interval(self, value):

        self.value_label.config(
            text=f"{int(float(value))} seconds"
        )

    def save_settings(self):

        new_settings = {
            "orbital_instability": self.enabled_var.get(),
            "instability_interval": self.interval_var.get()
        }

        if self.on_save(new_settings):
            self.destroy()
