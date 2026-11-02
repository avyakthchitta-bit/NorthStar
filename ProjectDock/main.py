
import tkinter as tk
import json
import os

from tkinter import filedialog, messagebox
from pathlib import Path

from orbit_view import OrbitView
from settings import SettingsManager, SettingsWindow


APP_NAME = "NorthStar Project Dock"
VERSION = "0.5.0"

BG = "#0b1020"
SIDEBAR = "#10182a"
PANEL = "#151f33"
BORDER = "#263651"
TEXT = "#e6edf7"
MUTED = "#8da2c0"
ACCENT = "#66e3c4"
DANGER = "#ff7185"


class ProjectDock(tk.Tk):

    def __init__(self):
        super().__init__()

        self.projects = []
        self.selected_project = None

        self.save_file = Path(__file__).with_name("projects.json")

        # Settings are managed by settings.py
        self.settings_manager = SettingsManager()
        self.settings = self.settings_manager.load()

        self.load_projects()

        self.title(APP_NAME)
        self.geometry("1100x700")
        self.minsize(850, 550)
        self.configure(bg=BG)

        self.build_ui()

    # --------------------------------------------------
    # DATA
    # --------------------------------------------------

    def load_projects(self):

        if not self.save_file.exists():
            return

        try:
            data = json.loads(
                self.save_file.read_text(encoding="utf-8")
            )

            if not isinstance(data, list):
                raise ValueError("Invalid project data")

            seen = set()

            for item in data:

                if not isinstance(item, str):
                    continue

                path = Path(item)

                if not path.is_absolute():
                    continue

                normalized = str(path.resolve()).casefold()

                if normalized not in seen:
                    self.projects.append(str(path.resolve()))
                    seen.add(normalized)

        except (OSError, json.JSONDecodeError, ValueError) as error:

            messagebox.showwarning(
                APP_NAME,
                f"Could not load saved projects:\n{error}"
            )

    def save_projects(self):

        try:
            self.save_file.write_text(
                json.dumps(self.projects, indent=4),
                encoding="utf-8"
            )
            return True

        except OSError as error:

            messagebox.showerror(
                APP_NAME,
                f"Could not save projects:\n{error}"
            )
            return False

    # --------------------------------------------------
    # NAVIGATION
    # --------------------------------------------------

    def add_nav_item(self, parent, text, active=False, command=None):

        color = ACCENT if active else MUTED
        bg = PANEL if active else SIDEBAR

        item = tk.Label(
            parent,
            text=text,
            bg=bg,
            fg=color,
            font=("Consolas", 10),
            anchor="w",
            padx=12,
            pady=10,
            cursor="hand2" if command else ""
        )

        item.pack(fill="x", padx=10, pady=2)

        if command:
            item.bind("<Button-1>", lambda event: command())
            item.bind(
                "<Enter>",
                lambda event: item.config(fg=ACCENT)
            )
            item.bind(
                "<Leave>",
                lambda event: item.config(fg=color)
            )

        return item

    # --------------------------------------------------
    # USER INTERFACE
    # --------------------------------------------------

    def build_ui(self):

        layout = tk.Frame(self, bg=BG)
        layout.pack(fill="both", expand=True)

        # Sidebar
        sidebar = tk.Frame(layout, bg=SIDEBAR, width=220)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Label(
            sidebar,
            text="✦ NORTHSTAR",
            bg=SIDEBAR,
            fg=ACCENT,
            font=("Consolas", 13, "bold")
        ).pack(anchor="w", padx=20, pady=(24, 4))

        tk.Label(
            sidebar,
            text="PROJECT DOCK",
            bg=SIDEBAR,
            fg=MUTED,
            font=("Consolas", 9)
        ).pack(anchor="w", padx=20, pady=(0, 30))

        self.add_nav_item(sidebar, "▦  Dashboard", active=True)
        self.add_nav_item(sidebar, "◇  All Projects")
        self.add_nav_item(sidebar, "⌘  Developer Tools")
        self.add_nav_item(
            sidebar,
            "⚙  Settings",
            command=self.open_settings
        )

        tk.Label(
            sidebar,
            text=f"NORTHSTAR CORE / {VERSION}",
            bg=SIDEBAR,
            fg=MUTED,
            font=("Consolas", 8)
        ).pack(side="bottom", anchor="w", padx=20, pady=20)

        # Main workspace
        workspace = tk.Frame(layout, bg=BG)
        workspace.pack(
            side="left",
            fill="both",
            expand=True,
            padx=32,
            pady=24
        )

        tk.Label(
            workspace,
            text="DEVELOPER HUB  /  OVERVIEW",
            bg=BG,
            fg=ACCENT,
            font=("Consolas", 10, "bold")
        ).pack(anchor="w")

        tk.Label(
            workspace,
            text="Your projects, in orbit.",
            bg=BG,
            fg=TEXT,
            font=("Segoe UI", 25, "bold")
        ).pack(anchor="w", pady=(8, 4))

        tk.Label(
            workspace,
            text="One launch point for everything you're building.",
            bg=BG,
            fg=MUTED,
            font=("Segoe UI", 11)
        ).pack(anchor="w", pady=(0, 18))

        # Welcome panel
        welcome = tk.Frame(
            workspace,
            bg=PANEL,
            highlightbackground=BORDER,
            highlightthickness=1,
            padx=20,
            pady=14
        )
        welcome.pack(fill="x")

        tk.Label(
            welcome,
            text="SYSTEM STATUS",
            bg=PANEL,
            fg=ACCENT,
            font=("Consolas", 9, "bold")
        ).pack(anchor="w")

        self.welcome_status = tk.Label(
            welcome,
            text="SYSTEM READY",
            bg=PANEL,
            fg=TEXT,
            font=("Segoe UI", 15, "bold")
        )
        self.welcome_status.pack(anchor="w", pady=(6, 4))

        tk.Label(
            welcome,
            text=(
                "Add a project to bring its planet into orbit. "
                "Your projects stay on your machine."
            ),
            bg=PANEL,
            fg=MUTED,
            font=("Segoe UI", 10),
            wraplength=600,
            justify="left"
        ).pack(anchor="w")

        # Orbit header
        orbit_header = tk.Frame(workspace, bg=BG)
        orbit_header.pack(fill="x", pady=(18, 6))

        tk.Label(
            orbit_header,
            text="PROJECT ORBIT",
            bg=BG,
            fg=TEXT,
            font=("Consolas", 10, "bold")
        ).pack(side="left")

        self.capture_status = tk.Label(
            orbit_header,
            text="● SYSTEM READY",
            bg=BG,
            fg=MUTED,
            font=("Consolas", 8)
        )
        self.capture_status.pack(side="right")

        self.project_count = tk.Label(
            orbit_header,
            text="0 PROJECTS",
            bg=BG,
            fg=MUTED,
            font=("Consolas", 9)
        )
        self.project_count.pack(side="right", padx=(0, 16))

        # Orbit visualization
        self.orbit_view = OrbitView(
            workspace,
            on_select=self.on_project_selected,
            instability_enabled=self.settings["orbital_instability"],
            instability_interval=self.settings["instability_interval"]
        )

        self.orbit_view.pack(fill="both", expand=True)

        # Project details
        self.build_details_panel(workspace)

        # Controls
        controls = tk.Frame(workspace, bg=BG)
        controls.pack(fill="x", pady=(10, 0))

        tk.Button(
            controls,
            text="+ Add Project",
            command=self.add_project,
            bg=PANEL,
            fg=ACCENT,
            activebackground=BORDER,
            activeforeground=TEXT,
            relief="flat",
            padx=12,
            pady=8,
            cursor="hand2"
        ).pack(side="left")

        self.orbit_view.set_projects(self.projects)
        self.update_project_count()

    # --------------------------------------------------
    # SETTINGS
    # --------------------------------------------------

    def open_settings(self):

        SettingsWindow(
            self,
            self.settings,
            self.apply_settings
        )

    def apply_settings(self, new_settings):

        try:
            self.settings_manager.save(new_settings)

        except OSError as error:

            messagebox.showerror(
                APP_NAME,
                f"Could not save settings:\n{error}"
            )

            return False

        self.settings = new_settings

        self.orbit_view.set_instability_settings(
            enabled=self.settings["orbital_instability"],
            interval=self.settings["instability_interval"]
        )

        return True

    # --------------------------------------------------
    # PROJECT DETAILS
    # --------------------------------------------------

    def build_details_panel(self, parent):

        self.details_panel = tk.Frame(
            parent,
            bg=PANEL,
            highlightbackground=BORDER,
            highlightthickness=1,
            padx=16,
            pady=12
        )
        self.details_panel.pack(fill="x", pady=(10, 0))

        tk.Label(
            self.details_panel,
            text="SELECTED PROJECT",
            bg=PANEL,
            fg=ACCENT,
            font=("Consolas", 9, "bold")
        ).pack(anchor="w")

        self.detail_name = tk.Label(
            self.details_panel,
            text="No project selected",
            bg=PANEL,
            fg=TEXT,
            font=("Segoe UI", 14, "bold")
        )
        self.detail_name.pack(anchor="w", pady=(5, 2))

        self.detail_path = tk.Label(
            self.details_panel,
            text="Click a planet to view project details.",
            bg=PANEL,
            fg=MUTED,
            font=("Consolas", 9),
            anchor="w",
            justify="left",
            wraplength=750
        )
        self.detail_path.pack(anchor="w", fill="x")

        actions = tk.Frame(self.details_panel, bg=PANEL)
        actions.pack(fill="x", pady=(12, 0))

        self.open_button = tk.Button(
            actions,
            text="Open Folder",
            command=self.open_project_folder,
            bg="#20334b",
            fg=TEXT,
            activebackground=BORDER,
            activeforeground=TEXT,
            relief="flat",
            padx=12,
            pady=7,
            cursor="hand2",
            state="disabled"
        )
        self.open_button.pack(side="left", padx=(0, 6))

        self.copy_button = tk.Button(
            actions,
            text="Copy Path",
            command=self.copy_project_path,
            bg="#20334b",
            fg=TEXT,
            activebackground=BORDER,
            activeforeground=TEXT,
            relief="flat",
            padx=12,
            pady=7,
            cursor="hand2",
            state="disabled"
        )
        self.copy_button.pack(side="left", padx=6)

        self.remove_button = tk.Button(
            actions,
            text="Remove Project",
            command=self.remove_project,
            bg="#3a202d",
            fg=DANGER,
            activebackground="#512938",
            activeforeground=TEXT,
            relief="flat",
            padx=12,
            pady=7,
            cursor="hand2",
            state="disabled"
        )
        self.remove_button.pack(side="right")

    # --------------------------------------------------
    # STATUS
    # --------------------------------------------------

    def set_status(self, message, color=ACCENT):

        self.capture_status.config(
            text=f"● {message}",
            fg=color
        )

        self.welcome_status.config(text=message)

    def reset_status(self):
        self.set_status("SYSTEM READY", ACCENT)

    # --------------------------------------------------
    # SELECTION
    # --------------------------------------------------

    def on_project_selected(self, path):

        if path not in self.projects:
            return

        self.selected_project = path
        project_path = Path(path)

        self.detail_name.config(text=project_path.name)
        self.detail_path.config(text=str(project_path))

        self.open_button.config(state="normal")
        self.copy_button.config(state="normal")
        self.remove_button.config(state="normal")

        self.set_status(
            f"CAPTURE COMPLETE / {project_path.name}",
            ACCENT
        )

        self.after(2500, self.reset_status)

    def clear_selection(self):

        self.selected_project = None

        self.detail_name.config(text="No project selected")
        self.detail_path.config(
            text="Click a planet to view project details."
        )

        self.open_button.config(state="disabled")
        self.copy_button.config(state="disabled")
        self.remove_button.config(state="disabled")

    # --------------------------------------------------
    # PROJECT ACTIONS
    # --------------------------------------------------

    def open_project_folder(self):

        if not self.selected_project:
            return

        path = Path(self.selected_project)

        if not path.is_dir():
            messagebox.showerror(
                APP_NAME,
                "This project folder no longer exists."
            )
            return

        try:
            os.startfile(str(path))

        except OSError as error:
            messagebox.showerror(
                APP_NAME,
                f"Could not open project folder:\n{error}"
            )

    def copy_project_path(self):

        if not self.selected_project:
            return

        self.clipboard_clear()
        self.clipboard_append(self.selected_project)
        self.update()

        self.copy_button.config(text="Copied!")

        self.after(
            1500,
            lambda: self.copy_button.config(text="Copy Path")
        )

    def remove_project(self):

        if not self.selected_project:
            return

        path = self.selected_project
        name = Path(path).name

        confirm = messagebox.askyesno(
            APP_NAME,
            (
                f"Remove '{name}' from Project Dock?\n\n"
                "The planet will be ejected from orbit. "
                "The actual project folder and its files "
                "will NOT be deleted."
            )
        )

        if not confirm:
            return

        original_index = self.projects.index(path)
        self.projects.pop(original_index)

        if not self.save_projects():

            self.projects.insert(original_index, path)
            return

        # Keep the planet visible for its ejection animation.
        self.orbit_view.remove_project_animated(path)

        self.clear_selection()
        self.update_project_count()

        self.set_status(
            f"EJECTING / {name}",
            "#b9a0ff"
        )

    # --------------------------------------------------
    # PROJECT COUNT
    # --------------------------------------------------

    def update_project_count(self):

        count = len(self.projects)
        label = "PROJECT" if count == 1 else "PROJECTS"

        self.project_count.config(
            text=f"{count} {label}"
        )

    # --------------------------------------------------
    # ADD PROJECT
    # --------------------------------------------------

    def add_project(self):

        folder = filedialog.askdirectory(
            title="Select a project folder"
        )

        if not folder:
            return

        path = Path(folder).resolve()

        if not path.is_dir():
            messagebox.showerror(
                APP_NAME,
                "The selected folder does not exist."
            )
            return

        normalized = str(path).casefold()

        if any(
            str(Path(existing).resolve()).casefold() == normalized
            for existing in self.projects
        ):
            messagebox.showinfo(
                APP_NAME,
                "That folder is already in your project list."
            )
            return

        project_path = str(path)
        self.projects.append(project_path)

        if not self.save_projects():
            self.projects.pop()
            return

        self.orbit_view.add_project_animated(project_path)
        self.update_project_count()

        self.set_status(
            f"CAPTURE INITIATED / {path.name}",
            "#ffbd69"
        )


if __name__ == "__main__":

    app = ProjectDock()
    app.mainloop()
