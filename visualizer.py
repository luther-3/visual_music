"""Pygame visualizer engine."""

from pathlib import Path

import pygame

from config import (
    BACKGROUND_COLOR,
    FPS,
    HOP_LENGTH,
    SAMPLE_RATE,
    SHOW_INFO,
    TRAIL_ALPHA,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)
from particle_system import ParticleSystem


class Visualizer:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("音乐可视化")
        pygame.mixer.init(frequency=SAMPLE_RATE)

        self.particle_system = ParticleSystem()
        self.is_paused = False
        self.display_mode = "all"
        self.clock = pygame.time.Clock()
        self.font = self._create_ui_font(24)

        self._last_audio_data = None
        self._audio_file_path = None
        self.playback_finished = False
        self._prev_total_energy = 0.0
        self._pulse_frames_left = 0
        self._pulse_strength = 0.0
        self._current_low = 0.0
        self._current_mid = 0.0
        self._current_high = 0.0
        self._energy_history = []
        self._palette_check_frames = 0
        self._palette_hold_frames = 0
        self._palette_blend_t = 1.0
        self._palette_blend_speed = 0.08
        self._current_palette = self._make_palette("cool")
        self._target_palette = self._current_palette
        self._vignette_surface = self._build_vignette_surface(WINDOW_WIDTH, WINDOW_HEIGHT)

    def _create_ui_font(self, size: int):
        font_paths = [
            Path("C:/Windows/Fonts/msyh.ttc"),
            Path("C:/Windows/Fonts/msyhbd.ttc"),
            Path("C:/Windows/Fonts/simhei.ttf"),
            Path("C:/Windows/Fonts/simsun.ttc"),
            Path("/System/Library/Fonts/PingFang.ttc"),
            Path("/System/Library/Fonts/STHeiti Medium.ttc"),
            Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
            Path("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"),
        ]
        for p in font_paths:
            try:
                if p.exists():
                    return pygame.font.Font(str(p), size)
            except Exception:
                continue

        candidates = ["Microsoft YaHei", "SimHei", "SimSun", "PingFang SC", "Noto Sans CJK SC"]
        for name in candidates:
            try:
                return pygame.font.SysFont(name, size)
            except Exception:
                continue
        return pygame.font.Font(None, size)

    def _build_vignette_surface(self, width: int, height: int):
        surface = pygame.Surface((width, height), pygame.SRCALPHA)
        cx = width / 2.0
        cy = height / 2.0
        max_dist = (cx * cx + cy * cy) ** 0.5
        step = 10
        for y in range(0, height, step):
            for x in range(0, width, step):
                dx = x - cx
                dy = y - cy
                d = (dx * dx + dy * dy) ** 0.5
                ratio = min(1.0, d / max_dist)
                alpha = int((ratio**1.8) * 105)
                pygame.draw.rect(surface, (0, 0, 0, alpha), (x, y, step, step))
        return surface

    def run(self, audio_data, audio_file_path: str):
        self._last_audio_data = audio_data
        self._audio_file_path = audio_file_path
        self.particle_system.clear_all()
        self.is_paused = False
        self.playback_finished = False
        self._prev_total_energy = 0.0
        self._pulse_frames_left = 0
        self._pulse_strength = 0.0
        self._current_low = 0.0
        self._current_mid = 0.0
        self._current_high = 0.0
        self._energy_history = []
        self._palette_check_frames = 0
        self._palette_hold_frames = 0
        self._palette_blend_t = 1.0
        self._palette_blend_speed = 0.08
        self._current_palette = self._make_palette("cool")
        self._target_palette = self._current_palette

        pygame.mixer.music.load(self._audio_file_path)
        pygame.mixer.music.play()

        while True:
            if not self._handle_events():
                break

            if not pygame.mixer.music.get_busy() and not self.is_paused:
                self.playback_finished = True

            if not self.is_paused and not self.playback_finished:
                frame_index = self._get_current_frame(audio_data)
                low, mid, high = audio_data.get_normalized_energy(frame_index)
                self._current_low, self._current_mid, self._current_high = low, mid, high

                total_energy = 0.5 * low + 0.3 * mid + 0.2 * high
                onset = max(0.0, total_energy - self._prev_total_energy)
                self._prev_total_energy = total_energy
                if onset > 0.18 and total_energy > 0.45:
                    self._pulse_frames_left = 2
                    self._pulse_strength = min(1.0, onset * 2.8)

                pulse_boost = 1.0
                if self._pulse_frames_left > 0:
                    pulse_boost = 1.0 + 1.2 * self._pulse_strength
                    self._pulse_frames_left -= 1

                self._update_palette_state(low, mid, high)
                self.particle_system.update(
                    min(1.0, low * pulse_boost),
                    min(1.0, mid * pulse_boost),
                    min(1.0, high * pulse_boost),
                )

            particles = self.particle_system.get_particles_to_render()
            self._render(particles)
            pygame.display.flip()
            self.clock.tick(FPS)

    def _handle_events(self) -> bool:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.KEYDOWN:
                key_char = (getattr(event, "unicode", "") or "").lower()
                if event.key == pygame.K_ESCAPE:
                    return False
                if event.key == pygame.K_SPACE:
                    if self.playback_finished:
                        continue
                    if self.is_paused:
                        pygame.mixer.music.unpause()
                    else:
                        pygame.mixer.music.pause()
                    self.is_paused = not self.is_paused
                elif event.key == pygame.K_r or key_char == "r":
                    self._restart_playback()
                elif event.key == pygame.K_1:
                    self.display_mode = "low"
                    self.particle_system.set_display_mode("low")
                elif event.key == pygame.K_2:
                    self.display_mode = "mid"
                    self.particle_system.set_display_mode("mid")
                elif event.key == pygame.K_3:
                    self.display_mode = "high"
                    self.particle_system.set_display_mode("high")
                elif event.key == pygame.K_a or key_char == "a":
                    self.display_mode = "all"
                    self.particle_system.set_display_mode("all")

        return True

    def _get_current_frame(self, audio_data) -> int:
        time_ms = pygame.mixer.music.get_pos()
        frame_index = int((time_ms / 1000.0) * SAMPLE_RATE / HOP_LENGTH)
        if frame_index < 0:
            return 0
        return min(frame_index, audio_data.n_frames - 1)

    def _restart_playback(self):
        if not self._audio_file_path:
            return
        self.particle_system.clear_all()
        self.is_paused = False
        self.playback_finished = False
        pygame.mixer.music.load(self._audio_file_path)
        pygame.mixer.music.play()

    def _render(self, particles):
        bg = self._blended_palette()["bg"]
        trail_surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        trail_surface.fill((*bg, TRAIL_ALPHA))
        self.screen.blit(trail_surface, (0, 0))

        for particle in particles:
            size = int(max(1, particle.size))
            particle_surface = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            particle_color = self._tinted_particle_color(particle)
            pygame.draw.circle(
                particle_surface,
                (*particle_color, particle.alpha),
                (size, size),
                size,
            )
            if particle.particle_type == "low":
                fog_alpha = int(particle.alpha * 0.22)
                if fog_alpha > 0:
                    pygame.draw.circle(
                        particle_surface,
                        (*particle_color, fog_alpha),
                        (size, size),
                        int(size * 1.7),
                    )
            elif particle.particle_type == "mid" and particle.lifetime % 3 == 0:
                arc_rect = pygame.Rect(0, 0, size * 2, size * 2)
                arc_alpha = int(particle.alpha * 0.6)
                pygame.draw.arc(
                    particle_surface,
                    (*particle_color, arc_alpha),
                    arc_rect,
                    0.3,
                    1.4,
                    max(1, int(size * 0.22)),
                )
            elif particle.particle_type == "high" and particle.lifetime % 2 == 0:
                star_alpha = int(particle.alpha * 0.85)
                cx = size
                cy = size
                arm = max(2, int(size * 0.9))
                pygame.draw.line(
                    particle_surface,
                    (*particle_color, star_alpha),
                    (cx - arm, cy),
                    (cx + arm, cy),
                    1,
                )
                pygame.draw.line(
                    particle_surface,
                    (*particle_color, star_alpha),
                    (cx, cy - arm),
                    (cx, cy + arm),
                    1,
                )
            self.screen.blit(particle_surface, (particle.x - size, particle.y - size))

        if SHOW_INFO and self._last_audio_data is not None:
            self._draw_info()

        self._draw_frequency_hud(self._current_low, self._current_mid, self._current_high)
        self._apply_postprocess()

    def _apply_postprocess(self):
        if self._vignette_surface is not None:
            self.screen.blit(self._vignette_surface, (0, 0))

    def _draw_frequency_hud(self, low: float, mid: float, high: float):
        p = self._blended_palette()
        hud_surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        cx, cy = WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2

        rings = [
            {"energy": low, "base_r": 110, "max_expand": 42, "base_w": 7, "max_w": 10, "color": p["hud_low"]},
            {"energy": mid, "base_r": 170, "max_expand": 54, "base_w": 6, "max_w": 9, "color": p["hud_mid"]},
            {"energy": high, "base_r": 240, "max_expand": 68, "base_w": 5, "max_w": 8, "color": p["hud_high"]},
        ]

        for r in rings:
            e = max(0.0, min(1.0, r["energy"]))
            radius = int(r["base_r"] + r["max_expand"] * e)
            width = max(1, int(r["base_w"] + r["max_w"] * e))
            alpha = int(40 + 170 * e)
            color = (*r["color"], alpha)
            pygame.draw.circle(hud_surface, color, (cx, cy), radius, width)

        self.screen.blit(hud_surface, (0, 0))

    def _update_palette_state(self, low: float, mid: float, high: float):
        self._energy_history.append((low, mid, high))
        if len(self._energy_history) > 420:
            self._energy_history.pop(0)

        if self._palette_blend_t < 1.0:
            self._palette_blend_t = min(1.0, self._palette_blend_t + self._palette_blend_speed)
            if self._palette_blend_t >= 1.0:
                self._current_palette = self._target_palette

        self._palette_check_frames += 1
        if self._palette_hold_frames > 0:
            self._palette_hold_frames -= 1
            return
        if self._palette_check_frames < 60 or len(self._energy_history) < 120:
            return
        self._palette_check_frames = 0

        low_avg = sum(x[0] for x in self._energy_history[-180:]) / 180.0
        mid_avg = sum(x[1] for x in self._energy_history[-180:]) / 180.0
        high_avg = sum(x[2] for x in self._energy_history[-180:]) / 180.0
        total = 0.5 * low_avg + 0.3 * mid_avg + 0.2 * high_avg

        if total > 0.58 or low_avg > 0.63:
            name = "warm"
        elif high_avg > 0.6 and low_avg < 0.5:
            name = "electric"
        else:
            name = "cool"

        next_palette = self._make_palette(name)
        if next_palette != self._target_palette:
            self._current_palette = self._blended_palette()
            self._target_palette = next_palette
            self._palette_blend_t = 0.0
            self._palette_hold_frames = 180

    def _make_palette(self, name: str):
        if name == "warm":
            return {
                "name": "warm",
                "bg": (30, 8, 6),
                "hud_low": (255, 95, 45),
                "hud_mid": (255, 150, 60),
                "hud_high": (255, 210, 105),
                "mul_low": (1.25, 0.9, 0.75),
                "mul_mid": (1.2, 0.92, 0.78),
                "mul_high": (1.08, 0.95, 0.85),
            }
        if name == "electric":
            return {
                "name": "electric",
                "bg": (4, 14, 34),
                "hud_low": (70, 150, 255),
                "hud_mid": (40, 255, 230),
                "hud_high": (150, 255, 255),
                "mul_low": (0.72, 0.95, 1.35),
                "mul_mid": (0.68, 1.05, 1.4),
                "mul_high": (0.72, 1.12, 1.52),
            }
        return {
            "name": "cool",
            "bg": (8, 12, 22),
            "hud_low": (220, 100, 140),
            "hud_mid": (80, 160, 255),
            "hud_high": (190, 225, 255),
            "mul_low": (1.0, 1.0, 1.0),
            "mul_mid": (1.0, 1.0, 1.0),
            "mul_high": (1.0, 1.0, 1.0),
        }

    def _blended_palette(self):
        if self._palette_blend_t >= 1.0:
            return self._target_palette
        t = self._palette_blend_t
        a = self._current_palette
        b = self._target_palette

        def lerp_tuple(x, y):
            return tuple(int(x[i] + (y[i] - x[i]) * t) for i in range(len(x)))

        return {
            "name": b["name"],
            "bg": lerp_tuple(a["bg"], b["bg"]),
            "hud_low": lerp_tuple(a["hud_low"], b["hud_low"]),
            "hud_mid": lerp_tuple(a["hud_mid"], b["hud_mid"]),
            "hud_high": lerp_tuple(a["hud_high"], b["hud_high"]),
            "mul_low": tuple(a["mul_low"][i] + (b["mul_low"][i] - a["mul_low"][i]) * t for i in range(3)),
            "mul_mid": tuple(a["mul_mid"][i] + (b["mul_mid"][i] - a["mul_mid"][i]) * t for i in range(3)),
            "mul_high": tuple(a["mul_high"][i] + (b["mul_high"][i] - a["mul_high"][i]) * t for i in range(3)),
        }

    def _tinted_particle_color(self, particle):
        p = self._blended_palette()
        if particle.particle_type == "low":
            mul = p["mul_low"]
        elif particle.particle_type == "mid":
            mul = p["mul_mid"]
        else:
            mul = p["mul_high"]
        return tuple(max(0, min(255, int(particle.color[i] * mul[i]))) for i in range(3))

    def _draw_info(self):
        current_sec = max(0.0, pygame.mixer.music.get_pos() / 1000.0)
        duration_sec = float(self._last_audio_data.duration)
        fps_text = self.font.render(f"FPS: {self.clock.get_fps():.1f}", True, (220, 220, 220))
        time_text = self.font.render(
            f"Time: {current_sec:.1f}s / {duration_sec:.1f}s", True, (220, 220, 220)
        )
        mode_text = self.font.render(f"Mode: {self.display_mode}", True, (220, 220, 220))
        palette_name = self._blended_palette()["name"]
        palette_text = self.font.render(f"Palette: {palette_name}", True, (220, 220, 220))
        hint_text = self.font.render(
            "ESC: 退出  SPACE: 暂停  R: 重播", True, (220, 220, 220)
        )
        status = "播放结束，按 R 重播" if self.playback_finished else "播放中"
        status_text = self.font.render(f"Status: {status}", True, (220, 220, 220))

        self.screen.blit(fps_text, (10, 10))
        self.screen.blit(time_text, (10, 35))
        self.screen.blit(mode_text, (10, 60))
        self.screen.blit(status_text, (10, 85))
        self.screen.blit(palette_text, (10, 110))
        self.screen.blit(hint_text, (10, 135))

    def cleanup(self):
        pygame.mixer.music.stop()
        pygame.quit()
