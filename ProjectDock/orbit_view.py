
import tkinter as tk
import math
from pathlib import Path


BG = "#0b1020"
TEXT = "#e6edf7"
MUTED = "#8da2c0"
ACCENT = "#66e3c4"

PLANET_COLORS = [
    "#66aaff",
    "#b9a0ff",
    "#ffbd69",
    "#ff7e9d",
    "#65dbc5",
]


class OrbitView(tk.Canvas):
    def __init__(self, parent, **kwargs):
        super().__init__(
            parent,
            bg=BG,
            highlightthickness=0,
            **kwargs
        )

        self.planets = []
        self.bind("<Configure>", self.draw_system)
        self.animate()

    def set_projects(self, project_paths):
        # Keep existing planet states when projects are refreshed.
        existing = {
            planet["path"]: planet
            for planet in self.planets
        }

        updated = []

        for index, project_path in enumerate(project_paths):
            path = str(Path(project_path).resolve())

            if path in existing:
                updated.append(existing[path])
                continue

            ring = index % 5

            updated.append({
                "path": path,
                "name": Path(path).name,
                "ring": ring,
                "angle": (index * 137.5) % 360,
                "speed": 1.5 / (ring + 1),
                "color": PLANET_COLORS[
                    index % len(PLANET_COLORS)
                ],
            })

        self.planets = updated
        self.draw_system()

    def draw_system(self, event=None):
        self.delete("all")

        width = self.winfo_width()
        height = self.winfo_height()

        if width < 50 or height < 50:
            return

        cx = width / 2
        cy = height / 2

        # Scale the solar system to fit the available space.
        max_radius = min(width, height) * 0.43

        # Draw an orbit ring for each ring containing a planet.
        used_rings = sorted({
            planet["ring"]
            for planet in self.planets
        })

        for ring in used_rings:
            radius = max_radius * (
                0.30 + 0.14 * ring
            )

            self.create_oval(
                cx - radius,
                cy - radius,
                cx + radius,
                cy + radius,
                outline="#263651",
                width=1,
            )

        # Draw NorthStar at the center.
        star_size = 25

        self.create_oval(
            cx - star_size,
            cy - star_size,
            cx + star_size,
            cy + star_size,
            fill=ACCENT,
            outline="",
        )

        self.create_text(
            cx,
            cy + 38,
            text="NORTHSTAR",
            fill=TEXT,
            font=("Consolas", 10, "bold"),
        )

        # Draw each real project as a planet.
        for planet in self.planets:
            radius = max_radius * (
                0.30 + 0.14 * planet["ring"]
            )

            angle = math.radians(planet["angle"])

            x = cx + radius * math.cos(angle)
            y = cy + radius * math.sin(angle)

            size = 10

            self.create_oval(
                x - size,
                y - size,
                x + size,
                y + size,
                fill=planet["color"],
                outline="",
                tags=("planet", planet["path"]),
            )

            self.create_text(
                x,
                y + 20,
                text=planet["name"],
                fill=TEXT,
                font=("Consolas", 9),
                tags=("planet", planet["path"]),
            )

        # Friendly empty state when no projects have been added.
        if not self.planets:
            self.create_text(
                cx,
                cy + 75,
                text="Your projects will orbit here.",
                fill=MUTED,
                font=("Segoe UI", 10),
            )

    def animate(self):
        for planet in self.planets:
            planet["angle"] = (
                planet["angle"] + planet["speed"]
            ) % 360

        self.draw_system()
        self.after(30, self.animate)


if __name__ == "__main__":
    root = tk.Tk()
    root.title("NorthStar — Project Orbit")
    root.geometry("800x600")
    root.configure(bg=BG)

    orbit = OrbitView(root)
    orbit.pack(fill="both", expand=True)

    root.mainloop()
