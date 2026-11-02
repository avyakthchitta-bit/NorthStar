
import tkinter as tk
import math
import random

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

FRAME_TIME = 30

INCOMING_TIME = 0.55
INSERTION_TIME = 3.0

RECOVERY_DECAY_TIME = 2.8
RECOVERY_BOOST_TIME = 1.8

EJECTION_LOCK_TIME = 1.4
EJECTION_SPIRAL_TIME = 1.8
EJECTION_LAUNCH_TIME = 1.0


class OrbitView(tk.Canvas):

    def __init__(
        self,
        parent,
        on_select=None,
        instability_enabled=True,
        instability_interval=60,
        **kwargs
    ):

        super().__init__(
            parent,
            bg=BG,
            highlightthickness=0,
            **kwargs
        )

        self.planets = []
        self.selected_path = None
        self.hovered_path = None
        self.on_select = on_select

        self.active_animation = None
        self.animation_queue = []

        self.instability_enabled = instability_enabled
        self.instability_interval = instability_interval

        self.random_generator = random.Random()
        self.anomaly_timer = self.next_anomaly_time()

        self.emergency = None

        self.bind("<Configure>", self.draw_system)
        self.bind("<Button-1>", self.handle_click)
        self.bind("<Motion>", self.handle_hover)
        self.bind("<Leave>", self.clear_hover)

        self.animate()

    # --------------------------------------------------
    # GENERAL HELPERS
    # --------------------------------------------------

    @staticmethod
    def clamp(value, minimum=0.0, maximum=1.0):
        return max(minimum, min(maximum, value))

    @staticmethod
    def lerp(a, b, t):
        return a + (b - a) * t

    @staticmethod
    def ease_out(t):
        return 1 - (1 - t) ** 3

    @staticmethod
    def ease_in_out(t):
        return 3 * t ** 2 - 2 * t ** 3

    @staticmethod
    def exponential_curve(t):
        k = 4.5
        return (1 - math.exp(-k * t)) / (1 - math.exp(-k))

    def next_anomaly_time(self):

        return self.random_generator.uniform(
            self.instability_interval * 0.65,
            self.instability_interval * 1.35
        )

    def set_instability_settings(self, enabled, interval):

        self.instability_enabled = bool(enabled)
        self.instability_interval = max(15, min(120, int(interval)))

        self.anomaly_timer = self.next_anomaly_time()

        if not self.instability_enabled:
            self.emergency = None

        self.draw_system()

    # --------------------------------------------------
    # PLANET DATA
    # --------------------------------------------------

    def create_planet_data(self, project_path, index):

        path = str(Path(project_path).resolve())
        ring = index % 5

        return {
            "path": path,
            "name": Path(path).name,
            "ring": ring,
            "angle": 0.0,
            "speed": 1.5 / (ring + 1),
            "color": PLANET_COLORS[index % len(PLANET_COLORS)]
        }

    def get_orbit_radius(self, planet, max_radius):

        return max_radius * (
            0.30 + 0.14 * planet["ring"]
        )

    def get_orbit_position(
        self, planet, cx, cy, max_radius
    ):

        radius = self.get_orbit_radius(planet, max_radius)
        angle = math.radians(planet["angle"])

        return (
            cx + radius * math.cos(angle),
            cy + radius * math.sin(angle)
        )

    # --------------------------------------------------
    # PROJECT MANAGEMENT
    # --------------------------------------------------

    def set_projects(self, project_paths):

        existing = {
            planet["path"]: planet
            for planet in self.planets
        }

        updated = []

        for index, project_path in enumerate(project_paths):

            path = str(Path(project_path).resolve())

            if path in existing:
                updated.append(existing[path])
            else:
                updated.append(
                    self.create_planet_data(path, index)
                )

        self.planets = updated

        valid_paths = {
            planet["path"] for planet in updated
        }

        if self.selected_path not in valid_paths:
            self.selected_path = None

        self.draw_system()

    def add_project_animated(self, project_path):

        path = str(Path(project_path).resolve())

        existing = {
            planet["path"] for planet in self.planets
        }

        pending = set()

        if self.active_animation:
            pending.add(
                self.active_animation["planet"]["path"]
            )

        for animation in self.animation_queue:
            pending.add(animation["planet"]["path"])

        if path in existing or path in pending:
            return

        index = len(self.planets) + len(pending)
        planet = self.create_planet_data(path, index)

        self.animation_queue.append({
            "kind": "capture",
            "planet": planet,
            "phase": "incoming",
            "progress": 0.0,
            "trail": []
        })

        if self.active_animation is None:
            self.start_next_animation()

        self.draw_system()

    def remove_project_animated(self, project_path):

        path = str(Path(project_path).resolve())

        planet = next(
            (
                p for p in self.planets
                if p["path"] == path
            ),
            None
        )

        if planet is None:
            return

        # Cancel an instability event if this planet is its target.
        if (
            self.emergency
            and self.emergency["planet"]["path"] == path
        ):
            self.emergency = None

        self.planets.remove(planet)

        if self.selected_path == path:
            self.selected_path = None

        self.animation_queue.append({
            "kind": "ejection",
            "planet": planet,
            "phase": "ejection_lock",
            "progress": 0.0,
            "start_angle": planet["angle"],
            "trail": []
        })

        if self.active_animation is None:
            self.start_next_animation()

        self.draw_system()

    def start_next_animation(self):

        if not self.animation_queue:
            self.active_animation = None
            return

        self.active_animation = self.animation_queue.pop(0)

    def finish_animation(self):

        animation = self.active_animation

        if animation is None:
            return

        if animation["kind"] == "capture":

            planet = animation["planet"]

            planet["angle"] = animation["end_angle"]

            self.planets.append(planet)
            self.selected_path = planet["path"]

            if self.on_select:
                self.on_select(planet["path"])

        # Ejection simply finishes: its planet is already removed.

        self.active_animation = None
        self.start_next_animation()

    # --------------------------------------------------
    # INTERACTION
    # --------------------------------------------------

    def handle_click(self, event):

        item = self.find_closest(event.x, event.y)

        if not item:
            return

        for tag in self.gettags(item[0]):

            if tag.startswith("project:"):

                path = tag[len("project:"):]

                self.selected_path = path

                if self.on_select:
                    self.on_select(path)

                self.draw_system()
                return

    def handle_hover(self, event):

        item = self.find_closest(event.x, event.y)
        hovered = None

        if item:

            for tag in self.gettags(item[0]):

                if tag.startswith("project:"):
                    hovered = tag[len("project:"):]
                    break

        if hovered != self.hovered_path:

            self.hovered_path = hovered
            self.configure(cursor="hand2" if hovered else "")
            self.draw_system()

    def clear_hover(self, event=None):

        self.hovered_path = None
        self.configure(cursor="")
        self.draw_system()

    # --------------------------------------------------
    # DRAWING HELPERS
    # --------------------------------------------------

    def draw_planet(
        self,
        planet,
        x,
        y,
        selected=False,
        hovered=False,
        tags=()
    ):

        size = 10

        if selected or hovered:

            outline = ACCENT if selected else MUTED

            self.create_oval(
                x - 17, y - 17,
                x + 17, y + 17,
                outline=outline,
                width=2
            )

        self.create_oval(
            x - size - 3,
            y - size - 3,
            x + size + 3,
            y + size + 3,
            outline="#263651",
            width=2
        )

        self.create_oval(
            x - size,
            y - size,
            x + size,
            y + size,
            fill=planet["color"],
            outline="",
            tags=tags
        )

        self.create_text(
            x,
            y + 22,
            text=planet["name"],
            fill=ACCENT if selected else TEXT,
            font=("Consolas", 9, "bold" if selected else "normal"),
            tags=tags
        )

    def draw_trail(self, trail, color):

        if len(trail) < 2:
            return

        for i in range(1, len(trail)):

            x1, y1 = trail[i - 1]
            x2, y2 = trail[i]

            intensity = i / len(trail)

            self.create_line(
                x1, y1, x2, y2,
                fill=color,
                width=max(1, 5 * intensity),
                capstyle=tk.ROUND
            )

    def draw_beam(
        self,
        x1,
        y1,
        x2,
        y2,
        color=ACCENT,
        intensity=1.0
    ):

        self.create_line(
            x1, y1, x2, y2,
            fill=color,
            width=12 * intensity,
            capstyle=tk.ROUND
        )

        self.create_line(
            x1, y1, x2, y2,
            fill="#347b91" if color == ACCENT else color,
            width=6 * intensity,
            capstyle=tk.ROUND
        )

        self.create_line(
            x1, y1, x2, y2,
            fill="#eaffff",
            width=2 * intensity,
            capstyle=tk.ROUND
        )

    # --------------------------------------------------
    # CAPTURE DEVICE
    # --------------------------------------------------

    def draw_capture_device(self, cx, cy):

        x = cx + 52
        y = cy - 5

        if self.emergency:

            color = (
                "#ffbd69"
                if self.emergency["phase"] == "decay"
                else "#b9a0ff"
            )

        elif self.active_animation:

            color = (
                "#b9a0ff"
                if self.active_animation["kind"] == "ejection"
                else ACCENT
            )

        else:
            color = "#416b78"

        self.create_oval(
            x - 20, y - 20,
            x + 20, y + 20,
            outline=color,
            width=2
        )

        for direction in (-1, 1):

            self.create_line(
                x - 24, y + direction * 14,
                x - 12, y + direction * 7,
                fill="#8da2c0",
                width=3
            )

            self.create_line(
                x + 24, y + direction * 14,
                x + 12, y + direction * 7,
                fill="#8da2c0",
                width=3
            )

        self.create_oval(
            x - 11, y - 11,
            x + 11, y + 11,
            fill="#172d3c",
            outline=color,
            width=2
        )

        self.create_oval(
            x - 4, y - 4,
            x + 4, y + 4,
            fill=color,
            outline=""
        )

        self.create_text(
            x,
            y + 31,
            text="CAPTURE",
            fill=color,
            font=("Consolas", 7, "bold")
        )

    # --------------------------------------------------
    # CAPTURE ANIMATION
    # --------------------------------------------------

    def get_capture_position(
        self, planet, cx, cy, max_radius
    ):

        radius = (
            self.get_orbit_radius(planet, max_radius)
            + max_radius * 0.30
        )

        angle = -0.95

        return (
            cx + radius * math.cos(angle),
            cy + radius * math.sin(angle)
        )

    def capture_position(
        self, animation, progress, cx, cy, max_radius
    ):

        planet = animation["planet"]

        orbit_radius = self.get_orbit_radius(
            planet, max_radius
        )

        start_radius = orbit_radius + max_radius * 0.30

        # Exponential radial decay.
        curve = self.exponential_curve(progress)

        radius = self.lerp(
            start_radius,
            orbit_radius,
            curve
        )

        start_angle = -0.95

        # A little more than half a revolution while
        # the planet spirals inward.
        end_angle = start_angle + math.pi * 1.15

        angle = self.lerp(
            start_angle,
            end_angle,
            curve
        )

        x = cx + radius * math.cos(angle)
        y = cy + radius * math.sin(angle)

        return x, y, math.degrees(end_angle)

    def draw_capture_animation(
        self, animation, cx, cy, max_radius
    ):

        planet = animation["planet"]
        phase = animation["phase"]
        progress = animation["progress"]

        device_x = cx + 52
        device_y = cy - 5

        if phase == "incoming":

            target_x, target_y = self.get_capture_position(
                planet, cx, cy, max_radius
            )

            t = self.ease_out(progress)

            start_x = self.winfo_width() + 50
            start_y = cy - max_radius * 0.42

            x = self.lerp(start_x, target_x, t)
            y = self.lerp(start_y, target_y, t)

            self.create_line(
                x + 85, y - 15,
                x, y,
                fill="#347b91",
                width=6,
                smooth=True,
                capstyle=tk.ROUND
            )

            self.create_line(
                x + 48, y - 8,
                x, y,
                fill="#a2eaff",
                width=2,
                smooth=True
            )

            self.draw_planet(planet, x, y)

            return

        # Three-second locked-beam insertion.
        x, y, end_angle = self.capture_position(
            animation, progress, cx, cy, max_radius
        )

        animation["end_angle"] = end_angle

        pulse = 0.82 + 0.18 * math.sin(
            progress * math.pi * 12
        )

        self.draw_beam(
            device_x, device_y,
            x, y,
            ACCENT,
            pulse
        )

        animation["trail"].append((x, y))

        if len(animation["trail"]) > 90:
            animation["trail"].pop(0)

        self.draw_trail(
            animation["trail"],
            "#347b91"
        )

        # Capture impact ring
        ring_size = 12 + 5 * math.sin(progress * math.pi * 10)

        self.create_oval(
            x - ring_size, y - ring_size,
            x + ring_size, y + ring_size,
            outline=ACCENT,
            width=2
        )

        self.draw_planet(planet, x, y)

    # --------------------------------------------------
    # ORBITAL INSTABILITY
    # --------------------------------------------------

    def start_instability(self):

        if not self.instability_enabled:
            return

        if not self.planets:
            return

        if self.active_animation or self.animation_queue:
            return

        if self.emergency:
            return

        planet = self.random_generator.choice(self.planets)

        self.emergency = {
            "planet": planet,
            "phase": "decay",
            "progress": 0.0,
            "start_angle": planet["angle"],
            "trail": []
        }

    def get_emergency_position(
        self, emergency, cx, cy, max_radius
    ):

        planet = emergency["planet"]

        orbit_radius = self.get_orbit_radius(
            planet, max_radius
        )

        start_angle = math.radians(
            emergency["start_angle"]
        )

        if emergency["phase"] == "decay":

            t = self.ease_in_out(emergency["progress"])

            radius = self.lerp(
                orbit_radius,
                orbit_radius - max_radius * 0.14,
                t
            )

            angle = start_angle + 0.30 * t

        else:

            t = self.ease_out(emergency["progress"])

            drift_radius = orbit_radius - max_radius * 0.14
            drift_angle = start_angle + 0.30

            radius = self.lerp(
                drift_radius,
                orbit_radius,
                t
            )

            angle = self.lerp(
                drift_angle,
                drift_angle + 0.12,
                t
            )

        return (
            cx + radius * math.cos(angle),
            cy + radius * math.sin(angle),
            math.degrees(angle)
        )

    def draw_emergency(self, cx, cy, max_radius):

        emergency = self.emergency

        if not emergency:
            return

        planet = emergency["planet"]
        phase = emergency["phase"]

        x, y, _ = self.get_emergency_position(
            emergency, cx, cy, max_radius
        )

        device_x = cx + 52
        device_y = cy - 5

        if phase == "decay":
            color = "#ffbd69"
        else:
            color = "#b9a0ff"

        pulse = 0.8 + 0.2 * math.sin(
            emergency["progress"] * math.pi * 10
        )

        # The device remains locked onto the unstable planet.
        self.draw_beam(
            device_x, device_y,
            x, y,
            color,
            pulse
        )

        emergency["trail"].append((x, y))

        if len(emergency["trail"]) > 90:
            emergency["trail"].pop(0)

        self.draw_trail(
            emergency["trail"],
            color
        )

        self.draw_planet(planet, x, y)

        label = (
            "ORBITAL DECAY"
            if phase == "decay"
            else "ORBITAL RECOVERY"
        )

        self.create_text(
            x,
            y - 25,
            text=label,
            fill=color,
            font=("Consolas", 7, "bold")
        )

    # --------------------------------------------------
    # EJECTION ANIMATION
    # --------------------------------------------------

    def ejection_position(
        self, animation, cx, cy, max_radius
    ):

        planet = animation["planet"]

        orbit_radius = self.get_orbit_radius(
            planet, max_radius
        )

        phase = animation["phase"]
        progress = animation["progress"]

        start_angle = math.radians(
            animation["start_angle"]
        )

        if phase == "ejection_lock":

            x = cx + orbit_radius * math.cos(start_angle)
            y = cy + orbit_radius * math.sin(start_angle)

        elif phase == "ejection_spiral":

            t = self.ease_in_out(progress)

            outer_radius = orbit_radius + max_radius * 0.30

            radius = self.lerp(
                orbit_radius,
                outer_radius,
                t
            )

            angle = start_angle - math.pi * 0.75 * t

            x = cx + radius * math.cos(angle)
            y = cy + radius * math.sin(angle)

        else:

            # Final launch: accelerate out of the canvas.
            start_radius = orbit_radius + max_radius * 0.30
            start_angle = start_angle - math.pi * 0.75

            start_x = cx + start_radius * math.cos(start_angle)
            start_y = cy + start_radius * math.sin(start_angle)

            target_x = self.winfo_width() + 150
            target_y = start_y - max_radius * 0.65

            t = self.ease_out(progress)

            x = self.lerp(start_x, target_x, t)
            y = self.lerp(start_y, target_y, t)

        return x, y

    def draw_ejection_animation(
        self, animation, cx, cy, max_radius
    ):

        planet = animation["planet"]
        phase = animation["phase"]
        progress = animation["progress"]

        x, y = self.ejection_position(
            animation, cx, cy, max_radius
        )

        device_x = cx + 52
        device_y = cy - 5

        color = "#b9a0ff"

        pulse = 0.8 + 0.2 * math.sin(
            progress * math.pi * 10
        )

        # Purple beam stays locked throughout the ejection.
        self.draw_beam(
            device_x, device_y,
            x, y,
            color,
            pulse
        )

        animation["trail"].append((x, y))

        if len(animation["trail"]) > 100:
            animation["trail"].pop(0)

        self.draw_trail(
            animation["trail"],
            color
        )

        self.draw_planet(planet, x, y)

    # --------------------------------------------------
    # MAIN RENDERING
    # --------------------------------------------------

    def draw_system(self, event=None):

        self.delete("all")

        width = self.winfo_width()
        height = self.winfo_height()

        if width < 50 or height < 50:
            return

        cx = width / 2
        cy = height / 2

        max_radius = min(width, height) * 0.43

        used_rings = {
            planet["ring"] for planet in self.planets
        }

        if self.active_animation:
            used_rings.add(
                self.active_animation["planet"]["ring"]
            )

        for ring in sorted(used_rings):

            radius = max_radius * (
                0.30 + 0.14 * ring
            )

            self.create_oval(
                cx - radius,
                cy - radius,
                cx + radius,
                cy + radius,
                outline="#263651",
                width=1
            )

        # Central NorthStar
        star_size = 25

        self.create_oval(
            cx - star_size,
            cy - star_size,
            cx + star_size,
            cy + star_size,
            fill=ACCENT,
            outline=""
        )

        self.create_text(
            cx,
            cy + 38,
            text="NORTHSTAR",
            fill=TEXT,
            font=("Consolas", 10, "bold")
        )

        self.draw_capture_device(cx, cy)

        # Hide the planet currently being recovered.
        emergency_planet = (
            self.emergency["planet"]
            if self.emergency else None
        )

        # Normal planets
        for planet in self.planets:

            if planet is emergency_planet:
                continue

            x, y = self.get_orbit_position(
                planet, cx, cy, max_radius
            )

            path = planet["path"]
            tag = f"project:{path}"

            self.draw_planet(
                planet,
                x,
                y,
                selected=(path == self.selected_path),
                hovered=(path == self.hovered_path),
                tags=(tag,)
            )

        # Special animations
        if self.emergency:
            self.draw_emergency(cx, cy, max_radius)

        if self.active_animation:

            animation = self.active_animation
            kind = animation["kind"]

            if kind == "capture":

                self.draw_capture_animation(
                    animation, cx, cy, max_radius
                )

            elif kind == "ejection":

                self.draw_ejection_animation(
                    animation, cx, cy, max_radius
                )

        if (
            not self.planets
            and not self.active_animation
            and not self.emergency
        ):

            self.create_text(
                cx,
                cy + 75,
                text="Your projects will orbit here.",
                fill=MUTED,
                font=("Segoe UI", 10)
            )

    # --------------------------------------------------
    # ANIMATION UPDATES
    # --------------------------------------------------

    def update_capture(self, animation):

        phase = animation["phase"]

        if phase == "incoming":

            animation["progress"] += (
                FRAME_TIME / 1000 / INCOMING_TIME
            )

            if animation["progress"] >= 1:

                animation["phase"] = "insertion"
                animation["progress"] = 0.0
                animation["trail"] = []

        elif phase == "insertion":

            animation["progress"] += (
                FRAME_TIME / 1000 / INSERTION_TIME
            )

            if animation["progress"] >= 1:
                self.finish_animation()

    def update_ejection(self, animation):

        phase = animation["phase"]

        if phase == "ejection_lock":

            animation["progress"] += (
                FRAME_TIME / 1000 / EJECTION_LOCK_TIME
            )

            if animation["progress"] >= 1:

                animation["phase"] = "ejection_spiral"
                animation["progress"] = 0.0

        elif phase == "ejection_spiral":

            animation["progress"] += (
                FRAME_TIME / 1000 / EJECTION_SPIRAL_TIME
            )

            if animation["progress"] >= 1:

                animation["phase"] = "ejection_launch"
                animation["progress"] = 0.0

        elif phase == "ejection_launch":

            animation["progress"] += (
                FRAME_TIME / 1000 / EJECTION_LAUNCH_TIME
            )

            if animation["progress"] >= 1:
                self.finish_animation()

    def update_emergency(self):

        emergency = self.emergency

        if not emergency:
            return

        if emergency["phase"] == "decay":

            emergency["progress"] += (
                FRAME_TIME / 1000 / RECOVERY_DECAY_TIME
            )

            if emergency["progress"] >= 1:

                emergency["phase"] = "boost"
                emergency["progress"] = 0.0
                emergency["trail"] = []

        elif emergency["phase"] == "boost":

            emergency["progress"] += (
                FRAME_TIME / 1000 / RECOVERY_BOOST_TIME
            )

            if emergency["progress"] >= 1:

                planet = emergency["planet"]

                _, _, final_angle = self.get_emergency_position(
                    emergency,
                    self.winfo_width() / 2,
                    self.winfo_height() / 2,
                    min(
                        self.winfo_width(),
                        self.winfo_height()
                    ) * 0.43
                )

                planet["angle"] = final_angle

                self.emergency = None
                self.anomaly_timer = self.next_anomaly_time()

    def animate(self):

        # Advance ordinary planets.
        for planet in self.planets:

            if (
                self.emergency
                and planet is self.emergency["planet"]
            ):
                continue

            planet["angle"] = (
                planet["angle"] + planet["speed"]
            ) % 360

        # Only one major animation runs at a time.
        if self.active_animation:

            animation = self.active_animation

            if animation["kind"] == "capture":
                self.update_capture(animation)

            elif animation["kind"] == "ejection":
                self.update_ejection(animation)

        elif self.emergency:

            self.update_emergency()

        else:

            # Random instability events.
            if self.instability_enabled and self.planets:

                self.anomaly_timer -= FRAME_TIME / 1000

                if self.anomaly_timer <= 0:
                    self.start_instability()

            elif not self.planets:

                self.anomaly_timer = self.next_anomaly_time()

        self.draw_system()

        self.after(FRAME_TIME, self.animate)


if __name__ == "__main__":

    root = tk.Tk()
    root.title("NorthStar — Project Orbit")
    root.geometry("800x600")
    root.configure(bg=BG)

    orbit = OrbitView(root)
    orbit.pack(fill="both", expand=True)

    root.mainloop()
