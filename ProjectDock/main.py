
import tkinter as tk
import json

from tkinter import filedialog, messagebox
from pathlib import Path

from orbit_view import OrbitView


# NorthStar Project Dock
# Version 0.2.0 — Project Orbit integration

APP_NAME = "NorthStar Project Dock"

# Colors
BG = "#0b1020"
SIDEBAR = "#10182a"
PANEL = "#151f33"
BORDER = "#263651"
TEXT = "#e6edf7"
MUTED = "#8da2c0"
ACCENT = "#66e3c4"


class ProjectDock(tk.Tk):
    def __init__(self):
        super().__init__()

        self.projects = []
        self.save_file = Path(__file__).with_name("projects.json")

        self.load_projects()

        self.title(APP_NAME)
        self.geometry("1100x700")
        self.minsize(850, 550)
        self.configure(bg=BG)

        self.build_ui()

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

        except OSError as error:
            messagebox.showerror(
                APP_NAME,
                f"Could not save projects:\n{error}"
            )

    def add_nav_item(self, parent, text, active=False):
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
            pady=10
        )
        item.pack(fill="x", padx=10, pady=2)

    def build_ui(self):
        # Main application layout
        layout = tk.Frame(self, bg=BG)
        layout.pack(fill="both", expand=True)

        # Sidebar
        sidebar = tk.Frame(
            layout,
            bg=SIDEBAR,
            width=220
        )
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        # Brand
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

        # Navigation
        self.add_nav_item(
            sidebar, "▦  Dashboard", active=True
        )
        self.add_nav_item(sidebar, "◇  All Projects")
        self.add_nav_item(sidebar, "⌘  Developer Tools")
        self.add_nav_item(sidebar, "⚙  Settings")

        # Sidebar footer
        tk.Label(
            sidebar,
            text="NORTHSTAR CORE / 0.2.0",
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

        # Header
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
            text="SYSTEM STATUS  /  READY",
            bg=PANEL,
            fg=ACCENT,
            font=("Consolas", 9, "bold")
        ).pack(anchor="w")

        tk.Label(
            welcome,
            text="Your workspace starts here.",
            bg=PANEL,
            fg=TEXT,
            font=("Segoe UI", 15, "bold")
        ).pack(anchor="w", pady=(6, 4))

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

        # Orbit section header
        orbit_header = tk.Frame(workspace, bg=BG)
        orbit_header.pack(fill="x", pady=(18, 6))

        tk.Label(
            orbit_header,
            text="PROJECT ORBIT",
            bg=BG,
            fg=TEXT,
            font=("Consolas", 10, "bold")
        ).pack(side="left")

        self.project_count = tk.Label(
            orbit_header,
            text="0 PROJECTS",
            bg=BG,
            fg=MUTED,
            font=("Consolas", 9)
        )
        self.project_count.pack(side="right")

        # Orbit visualization
        self.orbit_view = OrbitView(workspace)
        self.orbit_view.pack(fill="both", expand=True)

        # Restore saved projects into the orbit.
        self.orbit_view.set_projects(self.projects)
        self.update_project_count()

        # Project controls
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

    def update_project_count(self):
        count = len(self.projects)
        label = "PROJECT" if count == 1 else "PROJECTS"

        self.project_count.config(
            text=f"{count} {label}"
        )

    def add_project(self):
        folder = filedialog.askdirectory(
            title="Select a project folder"
        )

        if not folder:
            return

        path = Path(folder).resolve()

        # Prevent adding the same folder twice.
        if any(
            Path(existing).resolve() == path
            for existing in self.projects
        ):
            messagebox.showinfo(
                APP_NAME,
                "That folder is already in your project list."
            )
            return

        # Register and save the project.
        self.projects.append(str(path))
        self.save_projects()

        # Refresh the orbit and project count.
        self.orbit_view.set_projects(self.projects)
        self.update_project_count()


if __name__ == "__main__":
    app = ProjectDock()
    app.mainloop()
