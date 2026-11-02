
import tkinter as tk
import json
import os

from pathlib import Path
from tkinter import filedialog, messagebox, colorchooser, ttk

from orbit_view import OrbitView
from settings import SettingsManager, SettingsWindow
from project_metadata import ProjectMetadataManager


APP_NAME = "NorthStar Project Dock"
VERSION = "0.7.0"

BG = "#080D19"
SIDEBAR = "#0C1424"
PANEL = "#111D30"
PANEL_LIGHT = "#17263C"
BORDER = "#243650"
TEXT = "#E8F0FC"
MUTED = "#8295B2"
ACCENT = "#65E8D0"
PURPLE = "#A994FF"
DANGER = "#FF7185"
FONT = "Segoe UI"
MONO = "Consolas"


class ProjectDock(tk.Tk):

    def __init__(self):
        super().__init__()

        self.projects = []
        self.selected_project = None
        self.search_var = tk.StringVar()
        self.sort_var = tk.StringVar(value="Recently added")

        self.save_file = Path(__file__).with_name("projects.json")

        self.settings_manager = SettingsManager()
        self.settings = self.settings_manager.load()

        self.metadata_manager = ProjectMetadataManager()

        self.accent = self.settings.get("accent_color", ACCENT)

        self.title(APP_NAME)
        self.geometry("1320x820")
        self.minsize(1050, 680)
        self.configure(bg=BG)

        self.setup_styles()
        self.load_projects()
        self.build_ui()
        self.refresh_orbit()

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    # --------------------------------------------------
    # STYLES
    # --------------------------------------------------

    def setup_styles(self):

        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure(
            "North.TCombobox",
            fieldbackground=PANEL_LIGHT,
            background=PANEL_LIGHT,
            foreground=TEXT,
            arrowcolor=self.accent,
            bordercolor=BORDER,
            lightcolor=BORDER,
            darkcolor=BORDER,
            padding=7
        )

        style.map(
            "North.TCombobox",
            fieldbackground=[("readonly", PANEL_LIGHT)],
            foreground=[("readonly", TEXT)]
        )

    def make_button(
        self,
        parent,
        text,
        command,
        color=PANEL_LIGHT,
        foreground=TEXT,
        hover=None,
        **kwargs
    ):

        button = tk.Button(
            parent,
            text=text,
            command=command,
            bg=color,
            fg=foreground,
            activebackground=hover or BORDER,
            activeforeground=TEXT,
            relief="flat",
            borderwidth=0,
            cursor="hand2",
            font=(FONT, 9, "bold"),
            padx=13,
            pady=9,
            **kwargs
        )

        return button

    def make_label(
        self,
        parent,
        text,
        color=TEXT,
        size=10,
        weight="normal",
        font=FONT,
        **kwargs
    ):

        return tk.Label(
            parent,
            text=text,
            bg=parent.cget("bg"),
            fg=color,
            font=(font, size, weight),
            **kwargs
        )

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
                raise ValueError("Invalid project data format.")

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
            self.save_file.parent.mkdir(parents=True, exist_ok=True)

            temporary = self.save_file.with_suffix(".json.tmp")

            temporary.write_text(
                json.dumps(self.projects, indent=4),
                encoding="utf-8"
            )

            temporary.replace(self.save_file)
            return True

        except OSError as error:

            messagebox.showerror(
                APP_NAME,
                f"Could not save projects:\n{error}"
            )
            return False

    def get_metadata(self, path):
        return self.metadata_manager.get(path)

    # --------------------------------------------------
    # MAIN LAYOUT
    # --------------------------------------------------

    def build_ui(self):

        self.layout = tk.Frame(self, bg=BG)
        self.layout.pack(fill="both", expand=True)

        self.build_sidebar()

        self.workspace = tk.Frame(self.layout, bg=BG)
        self.workspace.pack(
            side="left",
            fill="both",
            expand=True,
            padx=(28, 28),
            pady=24
        )

        self.build_topbar()
        self.build_overview()
        self.build_orbit_section()
        self.build_details_panel()
        self.build_bottom_bar()

    # --------------------------------------------------
    # SIDEBAR
    # --------------------------------------------------

    def build_sidebar(self):

        self.sidebar = tk.Frame(
            self.layout,
            bg=SIDEBAR,
            width=225
        )

        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        brand = tk.Frame(self.sidebar, bg=SIDEBAR)
        brand.pack(fill="x", padx=22, pady=(28, 35))

        tk.Label(
            brand,
            text="✦",
            bg=SIDEBAR,
            fg=self.accent,
            font=(FONT, 25, "bold")
        ).pack(anchor="w")

        tk.Label(
            brand,
            text="NORTHSTAR",
            bg=SIDEBAR,
            fg=TEXT,
            font=(MONO, 15, "bold")
        ).pack(anchor="w", pady=(3, 0))

        tk.Label(
            brand,
            text="PROJECT DOCK",
            bg=SIDEBAR,
            fg=MUTED,
            font=(MONO, 8)
        ).pack(anchor="w", pady=(2, 0))

        self.make_label(
            self.sidebar,
            "WORKSPACE",
            MUTED,
            8,
            "bold",
            MONO
        ).pack(anchor="w", padx=23, pady=(0, 10))

        self.nav_items = {}

        self.add_nav_item("◈", "Dashboard", "dashboard")
        self.add_nav_item("◇", "All Projects", "projects")
        self.add_nav_item("⌘", "Developer Tools", "tools")
        self.add_nav_item("⚙", "Settings", "settings")

        spacer = tk.Frame(self.sidebar, bg=SIDEBAR)
        spacer.pack(fill="both", expand=True)

        separator = tk.Frame(self.sidebar, bg=BORDER, height=1)
        separator.pack(fill="x", padx=18, pady=(0, 15))

        tk.Label(
            self.sidebar,
            text="NORTHSTAR CORE",
            bg=SIDEBAR,
            fg=MUTED,
            font=(MONO, 8, "bold")
        ).pack(anchor="w", padx=22)

        tk.Label(
            self.sidebar,
            text=f"BUILD {VERSION}",
            bg=SIDEBAR,
            fg="#526783",
            font=(MONO, 8)
        ).pack(anchor="w", padx=22, pady=(5, 20))

    def add_nav_item(self, icon, label, key):

        item = tk.Frame(self.sidebar, bg=SIDEBAR, cursor="hand2")
        item.pack(fill="x", padx=12, pady=3)

        indicator = tk.Frame(item, bg=SIDEBAR, width=3)
        indicator.pack(side="left", fill="y")

        content = tk.Frame(item, bg=SIDEBAR)
        content.pack(side="left", fill="x", expand=True, padx=10, pady=11)

        icon_label = tk.Label(
            content,
            text=icon,
            bg=SIDEBAR,
            fg=MUTED,
            font=(FONT, 13)
        )
        icon_label.pack(side="left")

        text_label = tk.Label(
            content,
            text=label,
            bg=SIDEBAR,
            fg=MUTED,
            font=(FONT, 9, "bold")
        )
        text_label.pack(side="left", padx=12)

        self.nav_items[key] = (
            item,
            indicator,
            content,
            icon_label,
            text_label
        )

        def click(event=None):
            if key == "settings":
                self.open_settings()
            elif key == "projects":
                self.search_var.set("")
                self.refresh_orbit()
                self.set_status("SHOWING ALL PROJECTS")
            elif key == "tools":
                messagebox.showinfo(
                    "Developer Tools",
                    "Developer Tools is reserved for a future NorthStar module."
                )
            else:
                self.search_var.set("")
                self.refresh_orbit()
                self.set_status("DASHBOARD READY")

        for widget in (item, content, icon_label, text_label):
            widget.bind("<Button-1>", click)

        for widget in (item, content, icon_label, text_label):
            widget.bind(
                "<Enter>",
                lambda event, frame=item: self.nav_hover(frame, True)
            )
            widget.bind(
                "<Leave>",
                lambda event, frame=item: self.nav_hover(frame, False)
            )

        self.set_active_nav("dashboard")

    def nav_hover(self, item, hovered):

        if item is self.nav_items["dashboard"][0]:
            return

        if hovered:
            item.configure(bg=PANEL)
        else:
            item.configure(bg=SIDEBAR)

        for child in item.winfo_children():
            try:
                child.configure(bg=PANEL if hovered else SIDEBAR)
                for nested in child.winfo_children():
                    nested.configure(bg=PANEL if hovered else SIDEBAR)
            except tk.TclError:
                pass

    def set_active_nav(self, key):

        for name, parts in self.nav_items.items():

            item, indicator, content, icon_label, text_label = parts

            active = name == key

            item.configure(bg=PANEL if active else SIDEBAR)
            indicator.configure(bg=self.accent if active else SIDEBAR)
            content.configure(bg=PANEL if active else SIDEBAR)
            icon_label.configure(
                bg=PANEL if active else SIDEBAR,
                fg=self.accent if active else MUTED
            )
            text_label.configure(
                bg=PANEL if active else SIDEBAR,
                fg=TEXT if active else MUTED
            )

    # --------------------------------------------------
    # TOP BAR
    # --------------------------------------------------

    def build_topbar(self):

        top = tk.Frame(self.workspace, bg=BG)
        top.pack(fill="x")

        left = tk.Frame(top, bg=BG)
        left.pack(side="left")

        tk.Label(
            left,
            text="COMMAND CENTER  /  OVERVIEW",
            bg=BG,
            fg=self.accent,
            font=(MONO, 9, "bold")
        ).pack(anchor="w")

        tk.Label(
            left,
            text="Your projects, in orbit.",
            bg=BG,
            fg=TEXT,
            font=(FONT, 25, "bold")
        ).pack(anchor="w", pady=(5, 0))

        right = tk.Frame(top, bg=BG)
        right.pack(side="right", anchor="e")

        self.make_button(
            right,
            "⚙  Preferences",
            self.open_settings,
            color=PANEL,
            foreground=TEXT
        ).pack(side="right", padx=(8, 0))

        self.make_button(
            right,
            "+  Add Project",
            self.add_project,
            color=self.accent,
            foreground=BG,
            hover="#8CFFE9"
        ).pack(side="right")

        self.set_active_nav("dashboard")

    def build_bottom_bar(self):
        self.bottom_bar = tk.Frame(
            self,
            bg="#10182a",
            height=38,
            highlightthickness=1,
            highlightbackground="#263651"
        )
        self.bottom_bar.pack(side="bottom", fill="x")
        self.bottom_bar.pack_propagate(False)

        self.status_label = tk.Label(
            self.bottom_bar,
            text="●  NORTHSTAR SYSTEM ONLINE",
            bg="#10182a",
            fg="#66e3c4",
            font=("Segoe UI", 9),
            anchor="w",
            padx=16
        )
        self.status_label.pack(side="left", fill="y")

        self.version_label = tk.Label(
            self.bottom_bar,
            text=f"NORTHSTAR PROJECT DOCK  •  v{VERSION}",
            bg="#10182a",
            fg="#8da2c0",
            font=("Segoe UI", 8),
            anchor="e",
            padx=16
        )
        self.version_label.pack(side="right", fill="y")

    # --------------------------------------------------
    # OVERVIEW CARDS
    # --------------------------------------------------

    def build_overview(self):

        row = tk.Frame(self.workspace, bg=BG)
        row.pack(fill="x", pady=(20, 18))

        self.total_value = self.create_stat_card(
            row, "REGISTERED PROJECTS", "0", "Your local workspace"
        )

        self.selected_value = self.create_stat_card(
            row, "ACTIVE SELECTION", "NONE", "No planet selected"
        )

        self.system_value = self.create_stat_card(
            row, "SYSTEM STATUS", "ONLINE", "All systems operational"
        )

    def create_stat_card(self, parent, heading, value, subtitle):

        card = tk.Frame(
            parent,
            bg=PANEL,
            highlightbackground=BORDER,
            highlightthickness=1,
            padx=16,
            pady=13
        )

        card.pack(side="left", fill="both", expand=True, padx=(0, 10))

        tk.Label(
            card,
            text=heading,
            bg=PANEL,
            fg=MUTED,
            font=(MONO, 8, "bold")
        ).pack(anchor="w")

        value_label = tk.Label(
            card,
            text=value,
            bg=PANEL,
            fg=TEXT,
            font=(FONT, 19, "bold")
        )
        value_label.pack(anchor="w", pady=(5, 0))

        tk.Label(
            card,
            text=subtitle,
            bg=PANEL,
            fg=MUTED,
            font=(FONT, 8)
        ).pack(anchor="w", pady=(2, 0))

        return value_label

    # --------------------------------------------------
    # ORBIT SECTION
    # --------------------------------------------------

    def build_orbit_section(self):

        header = tk.Frame(self.workspace, bg=BG)
        header.pack(fill="x", pady=(0, 9))

        tk.Label(
            header,
            text="PROJECT ORBIT",
            bg=BG,
            fg=TEXT,
            font=(MONO, 10, "bold")
        ).pack(side="left")

        self.orbit_status = tk.Label(
            header,
            text="● SYSTEM NOMINAL",
            bg=BG,
            fg=self.accent,
            font=(MONO, 8, "bold")
        )
        self.orbit_status.pack(side="right")

        orbit_shell = tk.Frame(
            self.workspace,
            bg=PANEL,
            highlightbackground=BORDER,
            highlightthickness=1
        )
        orbit_shell.pack(fill="both", expand=True)

        toolbar = tk.Frame(orbit_shell, bg=PANEL)
        toolbar.pack(fill="x", padx=14, pady=12)

        search_frame = tk.Frame(
            toolbar,
            bg=PANEL_LIGHT,
            highlightbackground=BORDER,
            highlightthickness=1
        )
        search_frame.pack(side="left", fill="x", expand=True)

        tk.Label(
            search_frame,
            text="⌕",
            bg=PANEL_LIGHT,
            fg=self.accent,
            font=(FONT, 15)
        ).pack(side="left", padx=(10, 4))

        self.search_entry = tk.Entry(
            search_frame,
            textvariable=self.search_var,
            bg=PANEL_LIGHT,
            fg=TEXT,
            insertbackground=TEXT,
            relief="flat",
            font=(FONT, 9)
        )
        self.search_entry.pack(
            side="left",
            fill="x",
            expand=True,
            ipady=9,
            padx=(0, 10)
        )

        self.search_entry.insert(0, "")

        self.search_var.trace_add(
            "write",
            lambda *_: self.refresh_orbit()
        )

        self.sort_box = ttk.Combobox(
            toolbar,
            textvariable=self.sort_var,
            values=[
                "Recently added",
                "Name: A to Z",
                "Name: Z to A",
                "Project type"
            ],
            state="readonly",
            width=17,
            style="North.TCombobox"
        )
        self.sort_box.pack(side="right", padx=(10, 0))
        self.sort_box.bind(
            "<<ComboboxSelected>>",
            lambda event: self.refresh_orbit()
        )

        self.orbit_view = OrbitView(
            orbit_shell,
            on_select=self.on_project_selected,
            instability_enabled=self.settings["orbital_instability"],
            instability_interval=self.settings["instability_interval"],
            show_labels=self.settings.get("show_labels", True),
            starfield_enabled=self.settings.get("starfield", True),
            reduce_motion=self.settings.get("reduce_motion", False),
            accent_color=self.accent
        )

        self.orbit_view.pack(
            fill="both",
            expand=True,
            padx=8,
            pady=(0, 8)
        )

    def refresh_orbit(self):

        query = self.search_var.get().strip().casefold()
        visible = []

        for path in self.projects:

            metadata = self.get_metadata(path)

            searchable = " ".join([
                metadata.get("display_name", ""),
                metadata.get("project_type", ""),
                metadata.get("description", ""),
                Path(path).name
            ]).casefold()

            if query and query not in searchable:
                continue

            visible.append(path)

        sort_mode = self.sort_var.get()

        if sort_mode == "Name: A to Z":
            visible.sort(
                key=lambda p: self.get_metadata(p)["display_name"].casefold()
            )

        elif sort_mode == "Name: Z to A":
            visible.sort(
                key=lambda p: self.get_metadata(p)["display_name"].casefold(),
                reverse=True
            )

        elif sort_mode == "Project type":
            visible.sort(
                key=lambda p: self.get_metadata(p)["project_type"].casefold()
            )

        metadata_map = {
            path: self.get_metadata(path)
            for path in self.projects
        }

        self.orbit_view.set_project_metadata(metadata_map)
        self.orbit_view.set_projects(visible)

        self.update_project_count()

    # --------------------------------------------------
    # DETAILS PANEL
    # --------------------------------------------------

    def build_details_panel(self):

        self.details_panel = tk.Frame(
            self.workspace,
            bg=PANEL,
            highlightbackground=BORDER,
            highlightthickness=1
        )

        self.details_panel.pack(fill="x", pady=(13, 0))

        top = tk.Frame(self.details_panel, bg=PANEL)
        top.pack(fill="x", padx=16, pady=(13, 8))

        tk.Label(
            top,
            text="PROJECT INTELLIGENCE",
            bg=PANEL,
            fg=self.accent,
            font=(MONO, 8, "bold")
        ).pack(side="left")

        self.detail_color = tk.Label(
            top,
            text="   ",
            bg=PANEL,
            fg=TEXT,
            font=(FONT, 10)
        )
        self.detail_color.pack(side="right")

        body = tk.Frame(self.details_panel, bg=PANEL)
        body.pack(fill="x", padx=16, pady=(0, 12))

        self.detail_icon = tk.Label(
            body,
            text="◇",
            bg=PANEL,
            fg=MUTED,
            font=(FONT, 25, "bold"),
            width=2
        )
        self.detail_icon.pack(side="left", anchor="n", padx=(0, 12))

        info = tk.Frame(body, bg=PANEL)
        info.pack(side="left", fill="both", expand=True)

        self.detail_name = tk.Label(
            info,
            text="No project selected",
            bg=PANEL,
            fg=TEXT,
            font=(FONT, 14, "bold"),
            anchor="w"
        )
        self.detail_name.pack(anchor="w")

        self.detail_path = tk.Label(
            info,
            text="Select a planet to inspect its project.",
            bg=PANEL,
            fg=MUTED,
            font=(MONO, 8),
            anchor="w",
            justify="left",
            wraplength=700
        )
        self.detail_path.pack(anchor="w", pady=(3, 0))

        self.detail_description = tk.Label(
            info,
            text="Your project details will appear here.",
            bg=PANEL,
            fg=MUTED,
            font=(FONT, 9),
            anchor="w",
            justify="left",
            wraplength=700
        )
        self.detail_description.pack(anchor="w", pady=(5, 0))

        self.detail_type = tk.Label(
            info,
            text="TYPE / UNKNOWN",
            bg=PANEL,
            fg=self.accent,
            font=(MONO, 8, "bold"),
            anchor="w"
        )
        self.detail_type.pack(anchor="w", pady=(7, 0))

        actions = tk.Frame(body, bg=PANEL)
        actions.pack(side="right", anchor="e", padx=(10, 0))

        self.edit_button = self.make_button(
            actions,
            "Customize",
            self.open_metadata_editor,
            color="#292543",
            foreground=PURPLE
        )
        self.edit_button.pack(fill="x", pady=2)

        self.open_button = self.make_button(
            actions,
            "Open Folder",
            self.open_project_folder
        )
        self.open_button.pack(fill="x", pady=2)

        self.copy_button = self.make_button(
            actions,
            "Copy Path",
            self.copy_project_path
        )
        self.copy_button.pack(fill="x", pady=2)

        self.remove_button = self.make_button(
            actions,
            "Eject Project",
            self.remove_project,
            color="#38202D",
            foreground=DANGER
        )
        self.remove_button.pack(fill="x", pady=2)

        self.set_action_states(False)

    def set_action_states(self, enabled):

        state = "normal" if enabled else "disabled"

        for button in (
            self.edit_button,
            self.open_button,
            self.copy_button,
            self.remove_button
        ):
            button.configure(state=state)

    def refresh_project_details(self):

        if not self.selected_project:
            return

        metadata = self.get_metadata(self.selected_project)

        color = metadata.get("color", self.accent)
        icon = metadata.get("icon", "◇")

        self.detail_name.configure(
            text=metadata["display_name"]
        )

        self.detail_path.configure(
            text=str(Path(self.selected_project))
        )

        self.detail_description.configure(
            text=metadata.get("description") or "No description provided."
        )

        self.detail_type.configure(
            text=f"TYPE / {metadata.get('project_type', 'Other').upper()}"
        )

        self.detail_icon.configure(
            text=icon,
            fg=color
        )

        self.detail_color.configure(
            text=f"●  {color}",
            fg=color
        )

        self.selected_value.configure(
            text=metadata["display_name"][:17].upper()
        )

    # --------------------------------------------------
    # PROJECT SELECTION
    # --------------------------------------------------

    def on_project_selected(self, path):

        if path not in self.projects:
            return

        self.selected_project = path
        self.set_action_states(True)
        self.refresh_project_details()

        metadata = self.get_metadata(path)

        self.set_status(
            f"SELECTED / {metadata['display_name']}",
            metadata.get("color", self.accent)
        )

    def clear_selection(self):

        self.selected_project = None
        self.set_action_states(False)

        self.detail_name.configure(text="No project selected")
        self.detail_path.configure(text="Select a planet to inspect its project.")
        self.detail_description.configure(
            text="Your project details will appear here."
        )
        self.detail_type.configure(text="TYPE / UNKNOWN")
        self.detail_icon.configure(text="◇", fg=MUTED)
        self.detail_color.configure(text="")

        self.selected_value.configure(text="NONE")

    # --------------------------------------------------
    # METADATA EDITOR
    # --------------------------------------------------

    def open_metadata_editor(self):

        if not self.selected_project:
            return

        path = self.selected_project
        metadata = self.get_metadata(path)

        window = tk.Toplevel(self)
        window.title("Project Configuration")
        window.geometry("520x700")
        window.minsize(480, 650)
        window.configure(bg=BG)
        window.transient(self)
        window.grab_set()

        tk.Label(
            window,
            text="PROJECT CONFIGURATION",
            bg=BG,
            fg=self.accent,
            font=(MONO, 11, "bold")
        ).pack(anchor="w", padx=25, pady=(24, 5))

        tk.Label(
            window,
            text="Give this project its own identity.",
            bg=BG,
            fg=MUTED,
            font=(FONT, 9)
        ).pack(anchor="w", padx=25, pady=(0, 18))

        content = tk.Frame(
            window,
            bg=PANEL,
            highlightbackground=BORDER,
            highlightthickness=1
        )
        content.pack(fill="both", expand=True, padx=25, pady=(0, 16))

        def field_label(text, pady=(15, 5)):
            tk.Label(
                content,
                text=text,
                bg=PANEL,
                fg=self.accent,
                font=(MONO, 8, "bold")
            ).pack(anchor="w", padx=18, pady=pady)

        def styled_entry(variable, font_size=10):
            entry = tk.Entry(
                content,
                textvariable=variable,
                bg=PANEL_LIGHT,
                fg=TEXT,
                insertbackground=TEXT,
                relief="flat",
                font=(FONT, font_size)
            )
            entry.pack(fill="x", padx=18, ipady=8)
            return entry

        name_var = tk.StringVar(value=metadata["display_name"])
        field_label("DISPLAY NAME", (18, 5))
        styled_entry(name_var)

        type_var = tk.StringVar(value=metadata["project_type"])
        field_label("PROJECT TYPE")

        types = [
            "Other", "Unity Game", "Unreal Engine Game",
            "Godot Game", "Minecraft Project",
            "Python Application", "Web Application",
            "Desktop Application", "Game Mod",
            "Library", "Website"
        ]

        type_box = ttk.Combobox(
            content,
            textvariable=type_var,
            values=types,
            style="North.TCombobox"
        )
        type_box.pack(fill="x", padx=18, ipady=3)

        field_label("DESCRIPTION")

        description_box = tk.Text(
            content,
            height=5,
            bg=PANEL_LIGHT,
            fg=TEXT,
            insertbackground=TEXT,
            relief="flat",
            font=(FONT, 9),
            wrap="word",
            padx=9,
            pady=8
        )
        description_box.pack(fill="x", padx=18)
        description_box.insert("1.0", metadata["description"])

        icon_var = tk.StringVar(value=metadata["icon"])
        field_label("PROJECT ICON")
        styled_entry(icon_var, 13)

        field_label("PLANET COLOR")

        color_var = tk.StringVar(value=metadata["color"])

        color_row = tk.Frame(content, bg=PANEL)
        color_row.pack(fill="x", padx=18)

        preview = tk.Label(
            color_row,
            text="       ",
            bg=color_var.get(),
            relief="flat"
        )
        preview.pack(side="left", ipady=7)

        color_text = tk.Label(
            color_row,
            textvariable=color_var,
            bg=PANEL,
            fg=TEXT,
            font=(MONO, 9)
        )
        color_text.pack(side="left", padx=10)

        def choose_color():

            selected = colorchooser.askcolor(
                color=color_var.get(),
                parent=window,
                title="Choose Planet Color"
            )

            if selected and selected[1]:
                color_var.set(selected[1])
                preview.configure(bg=selected[1])

        self.make_button(
            color_row,
            "Choose Color",
            choose_color
        ).pack(side="right")

        buttons = tk.Frame(window, bg=BG)
        buttons.pack(fill="x", padx=25, pady=(0, 22))

        def save():

            display_name = name_var.get().strip()
            project_type = type_var.get().strip() or "Other"
            description = description_box.get("1.0", "end-1c").strip()
            icon = icon_var.get().strip() or "◇"
            color = color_var.get().strip()

            if not display_name:
                messagebox.showwarning(
                    APP_NAME,
                    "Enter a display name.",
                    parent=window
                )
                return

            try:
                self.winfo_rgb(color)
            except tk.TclError:
                messagebox.showwarning(
                    APP_NAME,
                    "Choose a valid color.",
                    parent=window
                )
                return

            updated = {
                "display_name": display_name,
                "project_type": project_type,
                "description": description,
                "icon": icon,
                "color": color
            }

            if not self.metadata_manager.update(path, updated):
                messagebox.showerror(
                    APP_NAME,
                    "Could not save project metadata.",
                    parent=window
                )
                return

            # Update the renderer immediately.
            self.orbit_view.update_project_metadata(
                path,
                self.get_metadata(path)
            )

            self.refresh_project_details()
            self.refresh_orbit()

            self.set_status(
                f"IDENTITY UPDATED / {display_name}",
                color
            )

            window.destroy()

        self.make_button(
            buttons,
            "Cancel",
            window.destroy,
            color=PANEL,
            foreground=MUTED
        ).pack(side="right", padx=(8, 0))

        self.make_button(
            buttons,
            "Save Changes",
            save,
            color=self.accent,
            foreground=BG
        ).pack(side="right")

    # --------------------------------------------------
    # PROJECT ACTIONS
    # --------------------------------------------------

    def add_project(self):

        folder = filedialog.askdirectory(
            title="Select a project folder"
        )

        if not folder:
            return

        path = Path(folder).resolve()

        if not path.is_dir():
            messagebox.showerror(APP_NAME, "That folder does not exist.")
            return

        normalized = str(path).casefold()

        if any(
            str(Path(existing).resolve()).casefold() == normalized
            for existing in self.projects
        ):
            messagebox.showinfo(
                APP_NAME,
                "That project is already registered."
            )
            return

        project_path = str(path)
        self.projects.append(project_path)

        if not self.save_projects():
            self.projects.remove(project_path)
            return

        self.orbit_view.add_project_animated(project_path)
        self.refresh_orbit()

        self.set_status(
            f"CAPTURE INITIATED / {path.name}",
            "#FFBD69"
        )

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
                f"Could not open folder:\n{error}"
            )

    def copy_project_path(self):

        if not self.selected_project:
            return

        self.clipboard_clear()
        self.clipboard_append(self.selected_project)

        self.copy_button.configure(text="Copied!")

        self.after(
            1500,
            lambda: self.copy_button.configure(text="Copy Path")
        )

    def remove_project(self):

        if not self.selected_project:
            return

        path = self.selected_project
        name = self.get_metadata(path)["display_name"]

        confirm = messagebox.askyesno(
            APP_NAME,
            (
                f"Eject '{name}' from Project Dock?\n\n"
                "This removes it from your project list. "
                "The actual folder and files will NOT be deleted."
            )
        )

        if not confirm:
            return

        index = self.projects.index(path)
        self.projects.pop(index)

        if not self.save_projects():
            self.projects.insert(index, path)
            return

        if not self.metadata_manager.remove(path):
            messagebox.showwarning(
                APP_NAME,
                "Project removed, but metadata could not be saved."
            )

        self.orbit_view.remove_project_animated(path)

        self.clear_selection()
        self.refresh_orbit()

        self.set_status(
            f"EJECTING / {name}",
            PURPLE
        )

    # --------------------------------------------------
    # SETTINGS
    # --------------------------------------------------

    def open_settings(self):

        self.set_active_nav("settings")

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
        self.accent = new_settings.get("accent_color", ACCENT)

        self.setup_styles()

        self.orbit_view.set_instability_settings(
            enabled=new_settings["orbital_instability"],
            interval=new_settings["instability_interval"]
        )

        self.orbit_view.set_visual_settings(
            show_labels=new_settings.get("show_labels", True),
            starfield_enabled=new_settings.get("starfield", True),
            reduce_motion=new_settings.get("reduce_motion", False),
            accent_color=self.accent
        )

        self.set_status("PREFERENCES UPDATED", self.accent)
        return True

    # --------------------------------------------------
    # STATUS AND COUNTERS
    # --------------------------------------------------

    def update_project_count(self):

        count = len(self.projects)

        self.total_value.configure(text=str(count))

        visible_count = len(self.orbit_view.planets)
        self.orbit_status.configure(
            text=f"● {visible_count} PLANETS IN VIEW"
        )

    def set_status(self, message, color=None):

        color = color or self.accent

        self.system_value.configure(text=message[:17].upper())
        self.orbit_status.configure(
            text=f"● {message.upper()}",
            fg=color
        )

    def on_close(self):
        self.destroy()


if __name__ == "__main__":

    app = ProjectDock()
    app.mainloop()
