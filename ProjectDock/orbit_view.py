
import tkinter as tk
import math
import random
import time

from pathlib import Path


BG = "#0A1221"
TEXT = "#E8F0FC"
MUTED = "#8295B2"
ACCENT = "#65E8D0"
PURPLE = "#A994FF"
AMBER = "#FFBD69"

FRAME_TIME = 16

INCOMING_TIME = 0.7
INSERTION_TIME = 2.2
EJECTION_TIME = 1.8
RECOVERY_TIME = 2.0


class OrbitView(tk.Canvas):

    def __init__(
        self,
        parent,
        on_select=None,
        instability_enabled=True,
        instability_interval=60,
        show_labels=True,
        starfield_enabled=True,
        reduce_motion=False,
        accent_color=ACCENT,
        **kwargs
    ):

        super().__init__(
            parent,
            bg=BG,
            highlightthickness=0,
            **kwargs
        )

        self.on_select = on_select

        self.planets = []
        self.metadata_map = {}

        self.selected_path = None
        self.hovered_path = None

        self.animation_queue = []
        self.active_animation = None
        self.emergency = None

        self.instability_enabled = instability_enabled
        self.instability_interval = max(
            15,
            min(120, int(instability_interval))
        )

        self.show_labels = show_labels
        self.starfield_enabled = starfield_enabled
        self.reduce_motion = reduce_motion
        self.accent_color = accent_color

        self.random_generator = random.Random()
        self.stars = []
        self.decorations = []

        self.last_frame = time.perf_counter()
        self.anomaly_timer = self.next_anomaly_time()

        self.bind("<Configure>", self.draw_system)
        self.bind("<Button-1>", self.handle_click)
        self.bind("<Motion>", self.handle_hover)
        self.bind("<Leave>", self.clear_hover)

        self.animate()

    # --------------------------------------------------
    # MATH AND COLOR HELPERS
    # --------------------------------------------------

    @staticmethod
    def clamp(value, low=0.0, high=1.0):
        return max(low, min(high, value))

    @staticmethod
    def lerp(a, b, t):
        return a + (b - a) * t

    @staticmethod
    def ease_out(t):
        return 1 - (1 - t) ** 3

    @staticmethod
    def ease_in_out(t):
        return t * t * (3 - 2 * t)

    @staticmethod
    def hex_rgb(color):

        color = color.lstrip("#")

        return (
            int(color[0:2], 16),
            int(color[2:4], 16),
            int(color[4:6], 16)
        )

    @classmethod
    def blend(cls, color_a, color_b, amount):

        amount = cls.clamp(amount)

        a = cls.hex_rgb(color_a)
        b = cls.hex_rgb(color_b)

        result = tuple(
            int(cls.lerp(a[i], b[i], amount))
            for i in range(3)
        )

        return "#{:02X}{:02X}{:02X}".format(*result)

    def next_anomaly_time(self):

        return self.random_generator.uniform(
            self.instability_interval * 0.65,
            self.instability_interval * 1.35
        )

    # --------------------------------------------------
    # SETTINGS
    # --------------------------------------------------

    def set_instability_settings(self, enabled, interval):

        self.instability_enabled = bool(enabled)

        self.instability_interval = max(
            15,
            min(120, int(interval))
        )

        self.anomaly_timer = self.next_anomaly_time()

        if not self.instability_enabled:
            self.emergency = None

        self.draw_system()

    def set_visual_settings(
        self,
        show_labels=None,
        starfield_enabled=None,
        reduce_motion=None,
        accent_color=None
    ):

        if show_labels is not None:
            self.show_labels = bool(show_labels)

        if starfield_enabled is not None:
            self.starfield_enabled = bool(starfield_enabled)

        if reduce_motion is not None:
            self.reduce_motion = bool(reduce_motion)

        if accent_color is not None:
            self.accent_color = accent_color

        self.draw_system()

    # --------------------------------------------------
    # PROJECT METADATA
    # --------------------------------------------------

    def set_project_metadata(self, metadata_map):

        self.metadata_map = metadata_map or {}

        for planet in self.planets:
            self.apply_metadata(planet)

        if self.active_animation:
            self.apply_metadata(
                self.active_animation["planet"]
            )

        for animation in self.animation_queue:
            self.apply_metadata(animation["planet"])

        if self.emergency:
            self.apply_metadata(self.emergency["planet"])

        self.draw_system()

    def update_project_metadata(self, path, metadata):

        normalized = str(Path(path).resolve())

        self.metadata_map[normalized] = metadata

        for planet in self.planets:
            if planet["path"] == normalized:
                self.apply_metadata(planet)

        if self.active_animation:
            planet = self.active_animation["planet"]
            if planet["path"] == normalized:
                self.apply_metadata(planet)

        for animation in self.animation_queue:
            planet = animation["planet"]
            if planet["path"] == normalized:
                self.apply_metadata(planet)

        if self.emergency:
            planet = self.emergency["planet"]
            if planet["path"] == normalized:
                self.apply_metadata(planet)

        self.draw_system()

    def apply_metadata(self, planet):

        metadata = self.metadata_map.get(
            planet["path"],
            {}
        )

        planet["name"] = metadata.get(
            "display_name",
            Path(planet["path"]).name
        )

        planet["color"] = metadata.get(
            "color",
            ACCENT
        )

        planet["icon"] = metadata.get(
            "icon",
            "◇"
        )

        planet["project_type"] = metadata.get(
            "project_type",
            "Other"
        )

    # --------------------------------------------------
    # PLANET DATA
    # --------------------------------------------------

    def create_planet_data(self, project_path, index):

        path = str(Path(project_path).resolve())

        ring = index % 5

        planet = {
            "path": path,
            "name": Path(path).name,
            "icon": "◇",
            "project_type": "Other",
            "ring": ring,
            "angle": (index * 137.5) % 360,
            "speed": 0.28 / (ring + 1),
            "color": ACCENT
        }

        self.apply_metadata(planet)

        return planet

    def get_orbit_radius(self, planet, max_radius):

        return max_radius * (
            0.25 + 0.135 * planet["ring"]
        )

    def get_orbit_position(
        self,
        planet,
        cx,
        cy,
        max_radius
    ):

        radius = self.get_orbit_radius(
            planet,
            max_radius
        )

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

        pending = set()

        if self.active_animation:
            pending.add(
                self.active_animation["planet"]["path"]
            )

        for animation in self.animation_queue:
            pending.add(animation["planet"]["path"])

        updated = []

        for index, project_path in enumerate(project_paths):

            path = str(Path(project_path).resolve())

            if path in existing:

                planet = existing[path]
                self.apply_metadata(planet)
                updated.append(planet)

            elif path in pending:

                # A planet already being captured must not
                # be added a second time.

                continue

            else:

                updated.append(
                    self.create_planet_data(path, index)
                )

        self.planets = updated

        valid = {
            planet["path"]
            for planet in self.planets
        }

        if self.selected_path not in valid:
            self.selected_path = None

        self.draw_system()

    def add_project_animated(self, project_path):

        path = str(Path(project_path).resolve())

        known = {
            planet["path"]
            for planet in self.planets
        }

        if path in known:
            return

        if (
            self.active_animation
            and self.active_animation["planet"]["path"] == path
        ):
            return

        if any(
            item["planet"]["path"] == path
            for item in self.animation_queue
        ):
            return

        index = len(self.planets) + len(self.animation_queue)

        if self.active_animation:
            index += 1

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
                item for item in self.planets
                if item["path"] == path
            ),
            None
        )

        # Cancel a queued capture if it hasn't started.
        self.animation_queue = [
            item for item in self.animation_queue
            if item["planet"]["path"] != path
        ]

        if planet is None:

            if (
                self.active_animation
                and self.active_animation["planet"]["path"] == path
            ):
                self.active_animation = None
                self.start_next_animation()

            return

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
            "phase": "ejection",
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

            planet["angle"] = animation.get(
                "end_angle",
                planet["angle"]
            )

            if not any(
                item["path"] == planet["path"]
                for item in self.planets
            ):
                self.planets.append(planet)

            self.selected_path = planet["path"]

            if self.on_select:
                self.on_select(planet["path"])

        self.active_animation = None
        self.start_next_animation()

    # --------------------------------------------------
    # INPUT
    # --------------------------------------------------

    def get_project_tag(self, event):

        items = self.find_overlapping(
            event.x - 3,
            event.y - 3,
            event.x + 3,
            event.y + 3
        )

        for item in reversed(items):

            for tag in self.gettags(item):

                if tag.startswith("project:"):
                    return tag[len("project:"):]

        return None

    def handle_click(self, event):

        path = self.get_project_tag(event)

        if path:

            self.selected_path = path

            if self.on_select:
                self.on_select(path)

            self.draw_system()

    def handle_hover(self, event):

        hovered = self.get_project_tag(event)

        if hovered != self.hovered_path:

            self.hovered_path = hovered

            self.configure(
                cursor="hand2" if hovered else ""
            )

            self.draw_system()

    def clear_hover(self, event=None):

        self.hovered_path = None
        self.configure(cursor="")
        self.draw_system()

    # --------------------------------------------------
    # BACKGROUND
    # --------------------------------------------------

    def ensure_background_objects(self, width, height):

        count = max(50, int(width * height / 6500))

        if len(self.stars) == count:
            return

        self.stars = []

        for _ in range(count):

            self.stars.append({
                "x": self.random_generator.random() * width,
                "y": self.random_generator.random() * height,
                "size": self.random_generator.choice([1, 1, 1, 2]),
                "brightness": self.random_generator.random()
            })

        self.decorations = []

        for _ in range(7):

            self.decorations.append({
                "x": self.random_generator.random() * width,
                "y": self.random_generator.random() * height,
                "radius": self.random_generator.randint(30, 85)
            })

    def draw_background(self, width, height):

        self.create_rectangle(
            0, 0, width, height,
            fill=BG,
            outline=""
        )

        if not self.starfield_enabled:
            return

        self.ensure_background_objects(width, height)

        # Distant nebula-like circles.
        for item in self.decorations:

            x = item["x"]
            y = item["y"]
            r = item["radius"]

            self.create_oval(
                x - r,
                y - r,
                x + r,
                y + r,
                fill="#0D1B2D",
                outline=""
            )

        for star in self.stars:

            brightness = star["brightness"]

            color = (
                "#344963"
                if brightness < 0.35
                else "#536B87"
                if brightness < 0.75
                else "#8BA5C4"
            )

            size = star["size"]

            self.create_oval(
                star["x"] - size,
                star["y"] - size,
                star["x"] + size,
                star["y"] + size,
                fill=color,
                outline=""
            )

    # --------------------------------------------------
    # DRAWING HELPERS
    # --------------------------------------------------

    def draw_orbit(self, cx, cy, radius, active=False):

        color = (
            self.blend("#243650", self.accent_color, 0.25)
            if active
            else "#20314A"
        )

        self.create_oval(
            cx - radius,
            cy - radius,
            cx + radius,
            cy + radius,
            outline=color,
            width=2 if active else 1
        )

        # Small orbital marker.
        if active:
            self.create_oval(
                cx - radius - 2,
                cy - radius - 2,
                cx - radius + 2,
                cy - radius + 2,
                fill=self.accent_color,
                outline=""
            )

    def draw_glow(self, x, y, color, radius):

        layers = [
            (2.4, 0.10),
            (1.9, 0.17),
            (1.45, 0.27),
            (1.15, 0.42)
        ]

        for scale, blend_amount in layers:

            r = radius * scale

            glow_color = self.blend(
                BG,
                color,
                blend_amount
            )

            self.create_oval(
                x - r,
                y - r,
                x + r,
                y + r,
                fill=glow_color,
                outline=""
            )

    def draw_planet(
        self,
        planet,
        x,
        y,
        selected=False,
        hovered=False,
        tags=()
    ):

        color = planet["color"]
        size = 9

        if selected or hovered:

            pulse = (
                1.0
                if self.reduce_motion
                else 0.5 + 0.5 * math.sin(time.perf_counter() * 3)
            )

            ring_color = (
                self.accent_color
                if selected
                else self.blend(MUTED, color, 0.5)
            )

            radius = 17 + pulse * 2

            self.create_oval(
                x - radius,
                y - radius,
                x + radius,
                y + radius,
                outline=ring_color,
                width=2,
                tags=tags
            )

        self.draw_glow(x, y, color, size)

        # Outer atmosphere.
        self.create_oval(
            x - size - 2,
            y - size - 2,
            x + size + 2,
            y + size + 2,
            outline=self.blend(BG, color, 0.75),
            width=1,
            tags=tags
        )

        # Main planet body.
        self.create_oval(
            x - size,
            y - size,
            x + size,
            y + size,
            fill=color,
            outline="",
            tags=tags
        )

        # Surface highlight.
        self.create_arc(
            x - size + 2,
            y - size + 2,
            x + size - 2,
            y + size - 2,
            start=35,
            extent=120,
            style="arc",
            outline="#FFFFFF",
            width=1,
            tags=tags
        )

        if self.show_labels:

            label_color = (
                color
                if selected
                else TEXT
            )

            label = f"{planet['icon']}  {planet['name']}"

            self.create_text(
                x,
                y + 27,
                text=label[:30],
                fill=label_color,
                font=(
                    "Segoe UI",
                    8,
                    "bold" if selected or hovered else "normal"
                ),
                tags=tags
            )

    def draw_star_core(self, cx, cy):

        pulse = (
            0.0
            if self.reduce_motion
            else math.sin(time.perf_counter() * 1.8) * 2
        )

        self.draw_glow(
            cx,
            cy,
            self.accent_color,
            17 + pulse
        )

        # Outer ring.
        self.create_oval(
            cx - 24,
            cy - 24,
            cx + 24,
            cy + 24,
            outline=self.blend(BG, self.accent_color, 0.8),
            width=2
        )

        # Core.
        self.create_oval(
            cx - 16,
            cy - 16,
            cx + 16,
            cy + 16,
            fill=self.accent_color,
            outline=""
        )

        self.create_oval(
            cx - 8,
            cy - 8,
            cx + 8,
            cy + 8,
            fill="#E8FFFC",
            outline=""
        )

        # Four-point star.
        points = [
            cx, cy - 30,
            cx + 3, cy - 3,
            cx + 30, cy,
            cx + 3, cy + 3,
            cx, cy + 30,
            cx - 3, cy + 3,
            cx - 30, cy,
            cx - 3, cy - 3
        ]

        self.create_polygon(
            points,
            fill=self.accent_color,
            outline=""
        )

        self.create_text(
            cx,
            cy + 48,
            text="N O R T H S T A R",
            fill=TEXT,
            font=("Consolas", 8, "bold")
        )

    # --------------------------------------------------
    # CAPTURE DEVICE
    # --------------------------------------------------

    def draw_capture_device(self, cx, cy):

        x = cx + 55
        y = cy - 5

        if self.emergency:
            color = AMBER
        elif self.active_animation:
            color = (
                PURPLE
                if self.active_animation["kind"] == "ejection"
                else self.accent_color
            )
        else:
            color = "#3A6072"

        self.create_oval(
            x - 16,
            y - 16,
            x + 16,
            y + 16,
            outline=color,
            width=2
        )

        self.create_oval(
            x - 10,
            y - 10,
            x + 10,
            y + 10,
            fill="#172C43",
            outline=color,
            width=2
        )

        self.create_oval(
            x - 4,
            y - 4,
            x + 4,
            y + 4,
            fill=color,
            outline=""
        )

        self.create_text(
            x,
            y + 27,
            text="DOCK",
            fill=color,
            font=("Consolas", 7, "bold")
        )

    # --------------------------------------------------
    # ANIMATION TRAILS AND BEAMS
    # --------------------------------------------------

    def draw_trail(self, trail, color):

        if len(trail) < 2:
            return

        for index in range(1, len(trail)):

            x1, y1 = trail[index - 1]
            x2, y2 = trail[index]

            intensity = index / len(trail)

            self.create_line(
                x1,
                y1,
                x2,
                y2,
                fill=self.blend(BG, color, intensity),
                width=max(1, int(4 * intensity)),
                capstyle=tk.ROUND
            )

    def draw_beam(
        self,
        x1,
        y1,
        x2,
        y2,
        color,
        intensity=1.0
    ):

        self.create_line(
            x1, y1, x2, y2,
            fill=self.blend(BG, color, 0.35),
            width=10 * intensity,
            capstyle=tk.ROUND
        )

        self.create_line(
            x1, y1, x2, y2,
            fill=self.blend(BG, color, 0.75),
            width=5 * intensity,
            capstyle=tk.ROUND
        )

        self.create_line(
            x1, y1, x2, y2,
            fill="#E8FFFC",
            width=1.5 * intensity,
            capstyle=tk.ROUND
        )

    # --------------------------------------------------
    # CAPTURE ANIMATION
    # --------------------------------------------------

    def draw_capture_animation(
        self,
        animation,
        cx,
        cy,
        max_radius
    ):

        planet = animation["planet"]
        progress = animation["progress"]

        device_x = cx + 55
        device_y = cy - 5

        if animation["phase"] == "incoming":

            target_radius = (
                self.get_orbit_radius(planet, max_radius)
                + max_radius * 0.30
            )

            target_angle = -0.85

            target_x = cx + target_radius * math.cos(target_angle)
            target_y = cy + target_radius * math.sin(target_angle)

            t = self.ease_out(progress)

            x = self.lerp(
                self.winfo_width() + 40,
                target_x,
                t
            )

            y = self.lerp(
                cy - max_radius * 0.55,
                target_y,
                t
            )

            self.create_line(
                x + 55,
                y - 10,
                x,
                y,
                fill=self.blend(BG, planet["color"], 0.7),
                width=5,
                capstyle=tk.ROUND
            )

            self.draw_planet(planet, x, y)

            return

        radius = self.get_orbit_radius(
            planet,
            max_radius
        )

        t = self.ease_in_out(progress)

        start_radius = radius + max_radius * 0.30
        current_radius = self.lerp(
            start_radius,
            radius,
            t
        )

        start_angle = -0.85
        end_angle = start_angle + math.pi * 1.2

        angle = self.lerp(
            start_angle,
            end_angle,
            t
        )

        x = cx + current_radius * math.cos(angle)
        y = cy + current_radius * math.sin(angle)

        animation["end_angle"] = math.degrees(end_angle)

        pulse = (
            0.85
            if self.reduce_motion
            else 0.7 + 0.3 * math.sin(progress * math.pi * 12)
        )

        self.draw_beam(
            device_x,
            device_y,
            x,
            y,
            planet["color"],
            pulse
        )

        animation["trail"].append((x, y))

        if len(animation["trail"]) > 45:
            animation["trail"].pop(0)

        self.draw_trail(
            animation["trail"],
            planet["color"]
        )

        self.draw_planet(planet, x, y)

    # --------------------------------------------------
    # EJECTION ANIMATION
    # --------------------------------------------------

    def draw_ejection_animation(
        self,
        animation,
        cx,
        cy,
        max_radius
    ):

        planet = animation["planet"]
        progress = self.ease_in_out(animation["progress"])

        radius = self.get_orbit_radius(
            planet,
            max_radius
        )

        angle = math.radians(animation["start_angle"])

        outer_radius = radius + max_radius * 0.45

        current_radius = self.lerp(
            radius,
            outer_radius,
            progress
        )

        current_angle = angle - math.pi * 0.55 * progress

        x = cx + current_radius * math.cos(current_angle)
        y = cy + current_radius * math.sin(current_angle)

        device_x = cx + 55
        device_y = cy - 5

        self.draw_beam(
            device_x,
            device_y,
            x,
            y,
            PURPLE,
            0.9
        )

        animation["trail"].append((x, y))

        if len(animation["trail"]) > 45:
            animation["trail"].pop(0)

        self.draw_trail(animation["trail"], PURPLE)
        self.draw_planet(planet, x, y)

    # --------------------------------------------------
    # ORBITAL INSTABILITY
    # --------------------------------------------------

    def start_instability(self):

        if (
            not self.instability_enabled
            or self.reduce_motion
            or not self.planets
            or self.active_animation
            or self.animation_queue
            or self.emergency
        ):
            return

        planet = self.random_generator.choice(self.planets)

        self.emergency = {
            "planet": planet,
            "phase": "decay",
            "progress": 0.0,
            "start_angle": planet["angle"],
            "trail": []
        }

    def emergency_position(
        self,
        emergency,
        cx,
        cy,
        max_radius
    ):

        planet = emergency["planet"]

        orbit_radius = self.get_orbit_radius(
            planet,
            max_radius
        )

        start_angle = math.radians(
            emergency["start_angle"]
        )

        progress = self.ease_in_out(
            emergency["progress"]
        )

        if emergency["phase"] == "decay":

            radius = self.lerp(
                orbit_radius,
                orbit_radius - max_radius * 0.14,
                progress
            )

            angle = start_angle + 0.32 * progress

        else:

            radius = self.lerp(
                orbit_radius - max_radius * 0.14,
                orbit_radius,
                progress
            )

            angle = self.lerp(
                start_angle + 0.32,
                start_angle + 0.44,
                progress
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

        x, y, _ = self.emergency_position(
            emergency,
            cx,
            cy,
            max_radius
        )

        color = (
            AMBER
            if emergency["phase"] == "decay"
            else PURPLE
        )

        self.draw_beam(
            cx + 55,
            cy - 5,
            x,
            y,
            color
        )

        emergency["trail"].append((x, y))

        if len(emergency["trail"]) > 45:
            emergency["trail"].pop(0)

        self.draw_trail(
            emergency["trail"],
            color
        )

        self.draw_planet(planet, x, y)

        label = (
            "ORBITAL INSTABILITY"
            if emergency["phase"] == "decay"
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
    # MAIN RENDERING
    # --------------------------------------------------

    def draw_system(self, event=None):

        self.delete("all")

        width = self.winfo_width()
        height = self.winfo_height()

        if width < 80 or height < 80:
            return

        self.draw_background(width, height)

        cx = width / 2
        cy = height / 2

        max_radius = min(width, height) * 0.43

        used_rings = {
            planet["ring"]
            for planet in self.planets
        }

        if self.active_animation:
            used_rings.add(
                self.active_animation["planet"]["ring"]
            )

        for ring in sorted(used_rings):

            radius = max_radius * (
                0.25 + 0.135 * ring
            )

            active = any(
                planet["ring"] == ring
                and planet["path"] == self.selected_path
                for planet in self.planets
            )

            self.draw_orbit(
                cx,
                cy,
                radius,
                active
            )

        # Draw central star and dock.
        self.draw_star_core(cx, cy)
        self.draw_capture_device(cx, cy)

        # Normal planets.
        emergency_planet = (
            self.emergency["planet"]
            if self.emergency
            else None
        )

        for planet in self.planets:

            if planet is emergency_planet:
                continue

            x, y = self.get_orbit_position(
                planet,
                cx,
                cy,
                max_radius
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

        # Emergency event.
        if self.emergency:
            self.draw_emergency(
                cx,
                cy,
                max_radius
            )

        # Capture or ejection.
        if self.active_animation:

            animation = self.active_animation

            if animation["kind"] == "capture":

                self.draw_capture_animation(
                    animation,
                    cx,
                    cy,
                    max_radius
                )

            elif animation["kind"] == "ejection":

                self.draw_ejection_animation(
                    animation,
                    cx,
                    cy,
                    max_radius
                )

        # Empty state.
        if (
            not self.planets
            and not self.active_animation
            and not self.animation_queue
            and not self.emergency
        ):

            self.create_text(
                cx,
                cy + 95,
                text="NO REGISTERED PROJECTS",
                fill=MUTED,
                font=("Consolas", 9, "bold")
            )

            self.create_text(
                cx,
                cy + 115,
                text="Add a project to initialize your orbit.",
                fill="#526783",
                font=("Segoe UI", 8)
            )

    # --------------------------------------------------
    # ANIMATION UPDATES
    # --------------------------------------------------

    def update_capture(self, animation, delta):

        phase = animation["phase"]

        if phase == "incoming":

            animation["progress"] += delta / INCOMING_TIME

            if animation["progress"] >= 1:

                animation["phase"] = "insertion"
                animation["progress"] = 0.0
                animation["trail"] = []

        elif phase == "insertion":

            animation["progress"] += delta / INSERTION_TIME

            if animation["progress"] >= 1:
                self.finish_animation()

    def update_ejection(self, animation, delta):

        animation["progress"] += delta / EJECTION_TIME

        if animation["progress"] >= 1:
            self.finish_animation()

    def update_emergency(self, delta):

        emergency = self.emergency

        if not emergency:
            return

        if emergency["phase"] == "decay":

            emergency["progress"] += delta / RECOVERY_TIME

            if emergency["progress"] >= 1:

                emergency["phase"] = "boost"
                emergency["progress"] = 0.0
                emergency["trail"] = []

        elif emergency["phase"] == "boost":

            emergency["progress"] += delta / RECOVERY_TIME

            if emergency["progress"] >= 1:

                planet = emergency["planet"]

                _, _, final_angle = self.emergency_position(
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

        now = time.perf_counter()

        delta = min(
            now - self.last_frame,
            0.05
        )

        self.last_frame = now

        if not self.reduce_motion:

            for planet in self.planets:

                if (
                    self.emergency
                    and planet is self.emergency["planet"]
                ):
                    continue

                planet["angle"] = (
                    planet["angle"]
                    + planet["speed"] * delta * 60
                ) % 360

        if self.active_animation:

            animation = self.active_animation

            if animation["kind"] == "capture":
                self.update_capture(animation, delta)

            elif animation["kind"] == "ejection":
                self.update_ejection(animation, delta)

        elif self.emergency:

            self.update_emergency(delta)

        else:

            if (
                self.instability_enabled
                and not self.reduce_motion
                and self.planets
            ):

                self.anomaly_timer -= delta

                if self.anomaly_timer <= 0:
                    self.start_instability()

            elif not self.planets:
                self.anomaly_timer = self.next_anomaly_time()

        self.draw_system()

        self.after(FRAME_TIME, self.animate)


if __name__ == "__main__":

    root = tk.Tk()
    root.title("NorthStar — Project Orbit")
    root.geometry("1000x700")
    root.configure(bg=BG)

    orbit = OrbitView(root)
    orbit.pack(fill="both", expand=True)

    root.mainloop()
