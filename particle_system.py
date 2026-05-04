"""Three-layer particle system for low/mid/high frequency visualization."""

import math
import random
from dataclasses import dataclass
from typing import List

from config import (
    HIGH_FREQ_PARTICLE_CONFIG,
    LOW_FREQ_PARTICLE_CONFIG,
    MAX_PARTICLES,
    MID_FREQ_PARTICLE_CONFIG,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)
from utils import interpolate_color


@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    size: float
    original_size: float
    color: tuple
    alpha: int
    lifetime: int
    max_lifetime: int
    particle_type: str
    orbit_center_x: float = 0.0
    orbit_center_y: float = 0.0
    orbit_radius: float = 0.0
    angle: float = 0.0
    angular_speed: float = 0.0
    direction_angle: float = 0.0

    def update(self):
        if self.particle_type == "low":
            self.x += self.vx
            self.y += self.vy
        elif self.particle_type == "mid":
            self.angle += self.angular_speed
            self.x = self.orbit_center_x + self.orbit_radius * math.cos(self.angle)
            self.y = self.orbit_center_y + self.orbit_radius * math.sin(self.angle)
        elif self.particle_type == "high":
            self.direction_angle += random.uniform(-0.3, 0.3)
            speed = math.sqrt(self.vx**2 + self.vy**2)
            self.vx = speed * math.cos(self.direction_angle)
            self.vy = speed * math.sin(self.direction_angle)
            self.x += self.vx
            self.y += self.vy

        self.lifetime -= 1
        decay = max(0.0, self.lifetime / self.max_lifetime)
        self.alpha = int(255 * decay)
        self.size = self.original_size * decay

    def is_alive(self) -> bool:
        return self.lifetime > 0 and self.size > 0

    def is_out_of_bounds(self, width: int, height: int) -> bool:
        return self.x < 0 or self.x > width or self.y < 0 or self.y > height


class ParticleEmitter:
    def __init__(self, emitter_type: str, config: dict):
        self.emitter_type = emitter_type
        self.config = config
        self.particles: List[Particle] = []

    def emit(self, normalized_energy: float):
        normalized_energy = max(0.0, min(1.0, normalized_energy))
        num = int(normalized_energy * self.config["max_count"])
        if num <= 0:
            return

        for _ in range(num):
            self.particles.append(self._create_particle(normalized_energy))

    def _create_particle(self, normalized_energy: float) -> Particle:
        size_min, size_max = self.config["size_range"]
        life_min, life_max = self.config["lifetime_range"]
        color = interpolate_color(
            self.config["color_start"], self.config["color_end"], normalized_energy
        )
        size = random.uniform(size_min, size_max)
        lifetime = random.randint(life_min, life_max)

        if self.emitter_type == "low":
            angle = random.uniform(0, 2 * math.pi)
            speed = 2 + normalized_energy * 6
            return Particle(
                x=WINDOW_WIDTH / 2,
                y=WINDOW_HEIGHT / 2,
                vx=speed * math.cos(angle),
                vy=speed * math.sin(angle),
                size=size,
                original_size=size,
                color=color,
                alpha=255,
                lifetime=lifetime,
                max_lifetime=lifetime,
                particle_type="low",
            )

        if self.emitter_type == "mid":
            center_x, center_y = random.choice(self.config["orbit_centers"])
            angle = random.uniform(0, 2 * math.pi)
            radius = 50 + normalized_energy * 150
            angular_speed = 0.05 + normalized_energy * 0.05
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            return Particle(
                x=x,
                y=y,
                vx=0.0,
                vy=0.0,
                size=size,
                original_size=size,
                color=color,
                alpha=255,
                lifetime=lifetime,
                max_lifetime=lifetime,
                particle_type="mid",
                orbit_center_x=center_x,
                orbit_center_y=center_y,
                orbit_radius=radius,
                angle=angle,
                angular_speed=angular_speed,
            )

        angle = random.uniform(0, 2 * math.pi)
        speed = 0.5 + normalized_energy * 2.5
        return Particle(
            x=random.uniform(0, WINDOW_WIDTH),
            y=random.uniform(0, WINDOW_HEIGHT),
            vx=speed * math.cos(angle),
            vy=speed * math.sin(angle),
            size=size,
            original_size=size,
            color=color,
            alpha=255,
            lifetime=lifetime,
            max_lifetime=lifetime,
            particle_type="high",
            direction_angle=angle,
        )

    def update_particles(self):
        alive_particles: List[Particle] = []
        for particle in self.particles:
            particle.update()
            if particle.is_alive() and not particle.is_out_of_bounds(
                WINDOW_WIDTH, WINDOW_HEIGHT
            ):
                alive_particles.append(particle)
        self.particles = alive_particles

    def get_active_particles(self) -> List[Particle]:
        return self.particles

    def clear(self):
        self.particles = []


class ParticleSystem:
    def __init__(self):
        self.low_emitter = ParticleEmitter("low", LOW_FREQ_PARTICLE_CONFIG)
        self.mid_emitter = ParticleEmitter("mid", MID_FREQ_PARTICLE_CONFIG)
        self.high_emitter = ParticleEmitter("high", HIGH_FREQ_PARTICLE_CONFIG)
        self.display_mode = "all"

    def update(self, low_energy: float, mid_energy: float, high_energy: float):
        total_particles = (
            len(self.low_emitter.particles)
            + len(self.mid_emitter.particles)
            + len(self.high_emitter.particles)
        )

        if total_particles < MAX_PARTICLES:
            self.low_emitter.emit(low_energy)
            self.mid_emitter.emit(mid_energy)
            self.high_emitter.emit(high_energy)

        self.low_emitter.update_particles()
        self.mid_emitter.update_particles()
        self.high_emitter.update_particles()

    def get_particles_to_render(self) -> List[Particle]:
        if self.display_mode == "low":
            return self.low_emitter.get_active_particles()
        if self.display_mode == "mid":
            return self.mid_emitter.get_active_particles()
        if self.display_mode == "high":
            return self.high_emitter.get_active_particles()
        return (
            self.low_emitter.get_active_particles()
            + self.mid_emitter.get_active_particles()
            + self.high_emitter.get_active_particles()
        )

    def set_display_mode(self, mode: str):
        if mode in {"all", "low", "mid", "high"}:
            self.display_mode = mode

    def clear_all(self):
        self.low_emitter.clear()
        self.mid_emitter.clear()
        self.high_emitter.clear()
