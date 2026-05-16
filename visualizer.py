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
        self.contrast_mode = True

        self._last_audio_data = None
        self._audio_file_path = None
        self.playback_finished = False
        self._prev_total_energy = 0.0
        self._pulse_frames_left = 0
        self._pulse_strength = 0.0
        self._current_low = 0.0
        self._current_mid = 0.0
        self._current_high = 0.0

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
                elif event.key == pygame.K_c or key_char == "c":
                    self.contrast_mode = not self.contrast_mode
                    self.particle_system.set_contrast_mode(self.contrast_mode)

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
        trail_surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        trail_surface.fill((*BACKGROUND_COLOR, TRAIL_ALPHA))
        self.screen.blit(trail_surface, (0, 0))

        for particle in particles:
            size = int(max(1, particle.size))
            particle_surface = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            pygame.draw.circle(
                particle_surface,
                (*particle.color, particle.alpha),
                (size, size),
                size,
            )
            self.screen.blit(particle_surface, (particle.x - size, particle.y - size))

        if SHOW_INFO and self._last_audio_data is not None:
            self._draw_info()

        self._draw_frequency_hud(self._current_low, self._current_mid, self._current_high)
        self._draw_pulse_overlay()

    def _draw_frequency_hud(self, low: float, mid: float, high: float):
        hud_surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        cx, cy = WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2

        rings = [
            {"energy": low, "base_r": 110, "max_expand": 42, "base_w": 7, "max_w": 10, "color": (255, 120, 80)},
            {"energy": mid, "base_r": 170, "max_expand": 54, "base_w": 6, "max_w": 9, "color": (70, 190, 255)},
            {"energy": high, "base_r": 240, "max_expand": 68, "base_w": 5, "max_w": 8, "color": (255, 245, 120)},
        ]

        for r in rings:
            e = max(0.0, min(1.0, r["energy"]))
            radius = int(r["base_r"] + r["max_expand"] * e)
            width = max(1, int(r["base_w"] + r["max_w"] * e))
            alpha = int(40 + 170 * e)
            color = (*r["color"], alpha)
            pygame.draw.circle(hud_surface, color, (cx, cy), radius, width)

        self.screen.blit(hud_surface, (0, 0))

    def _draw_pulse_overlay(self):
        if self._pulse_frames_left <= 0:
            return
        alpha = int(35 + 70 * self._pulse_strength)
        pulse_surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        pulse_surface.fill((255, 255, 255, alpha))
        self.screen.blit(pulse_surface, (0, 0))

    def _draw_info(self):
        current_sec = max(0.0, pygame.mixer.music.get_pos() / 1000.0)
        duration_sec = float(self._last_audio_data.duration)
        fps_text = self.font.render(f"FPS: {self.clock.get_fps():.1f}", True, (220, 220, 220))
        time_text = self.font.render(
            f"Time: {current_sec:.1f}s / {duration_sec:.1f}s", True, (220, 220, 220)
        )
        mode_text = self.font.render(f"Mode: {self.display_mode}", True, (220, 220, 220))
        hint_text = self.font.render(
            "ESC: 退出  SPACE: 暂停  R: 重播  C: 对比模式", True, (220, 220, 220)
        )
        status = "播放结束，按 R 重播" if self.playback_finished else "播放中"
        status_text = self.font.render(f"Status: {status}", True, (220, 220, 220))
        contrast_text = self.font.render(
            f"Contrast: {'ON' if self.contrast_mode else 'OFF'}", True, (220, 220, 220)
        )

        self.screen.blit(fps_text, (10, 10))
        self.screen.blit(time_text, (10, 35))
        self.screen.blit(mode_text, (10, 60))
        self.screen.blit(status_text, (10, 85))
        self.screen.blit(contrast_text, (10, 110))
        self.screen.blit(hint_text, (10, 135))

    def cleanup(self):
        pygame.mixer.music.stop()
        pygame.quit()
