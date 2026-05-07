"""Pygame visualizer engine."""

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
        self.font = pygame.font.SysFont(None, 24)
        self.contrast_mode = True

        self._last_audio_data = None
        self._audio_file_path = None
        self.playback_finished = False

    def run(self, audio_data, audio_file_path: str):
        self._last_audio_data = audio_data
        self._audio_file_path = audio_file_path
        self.particle_system.clear_all()
        self.is_paused = False
        self.playback_finished = False

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
                self.particle_system.update(low, mid, high)

            particles = self.particle_system.get_particles_to_render()
            self._render(particles)
            pygame.display.flip()
            self.clock.tick(FPS)

    def _handle_events(self) -> bool:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.KEYDOWN:
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
                elif event.key == pygame.K_r:
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
                elif event.key == pygame.K_a:
                    self.display_mode = "all"
                    self.particle_system.set_display_mode("all")
                elif event.key == pygame.K_c:
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
