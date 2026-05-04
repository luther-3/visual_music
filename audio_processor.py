"""Audio loading and spectral feature extraction."""

from dataclasses import dataclass
from typing import Optional, Tuple

import numpy as np
import soundfile as sf
from scipy.signal import stft as scipy_stft

from config import (
    HIGH_FREQ_RANGE,
    HOP_LENGTH,
    LOW_FREQ_RANGE,
    MID_FREQ_RANGE,
    N_FFT,
    NORMALIZATION_WINDOW_SIZE,
    SAMPLE_RATE,
    WINDOW_TYPE,
)
from utils import freq_to_bin, normalize_energy


@dataclass
class AudioData:
    audio_samples: np.ndarray
    sample_rate: int
    duration: float
    n_frames: int
    low_freq_energy: np.ndarray
    mid_freq_energy: np.ndarray
    high_freq_energy: np.ndarray
    phase: np.ndarray

    def get_normalized_energy(
        self, frame_index: int, window_size: int = NORMALIZATION_WINDOW_SIZE
    ) -> Tuple[float, float, float]:
        if self.n_frames <= 0:
            return 0.0, 0.0, 0.0

        frame_index = max(0, min(frame_index, self.n_frames - 1))
        half_window = window_size // 2
        start = max(0, frame_index - half_window)
        end = min(self.n_frames, frame_index + half_window)

        low_local_max = float(np.max(self.low_freq_energy[start:end])) if end > start else 0.0
        mid_local_max = float(np.max(self.mid_freq_energy[start:end])) if end > start else 0.0
        high_local_max = float(np.max(self.high_freq_energy[start:end])) if end > start else 0.0

        low = normalize_energy(float(self.low_freq_energy[frame_index]), low_local_max)
        mid = normalize_energy(float(self.mid_freq_energy[frame_index]), mid_local_max)
        high = normalize_energy(float(self.high_freq_energy[frame_index]), high_local_max)
        return low, mid, high


class AudioProcessor:
    @staticmethod
    def load(file_path: str) -> Optional[AudioData]:
        try:
            print("正在加载音频文件...")
            audio_samples, source_sr = sf.read(file_path, always_2d=False)

            if isinstance(audio_samples, np.ndarray) and audio_samples.ndim > 1:
                audio_samples = np.mean(audio_samples, axis=1)

            audio_samples = np.asarray(audio_samples, dtype=np.float32)

            if source_sr != SAMPLE_RATE:
                raise ValueError(
                    f"当前实现要求采样率为 {SAMPLE_RATE}，实际为 {source_sr}。"
                    "请先用目标采样率导出音频。"
                )

            print("正在处理音频数据...")
            _, _, stft_matrix = scipy_stft(
                audio_samples,
                fs=SAMPLE_RATE,
                window=WINDOW_TYPE,
                nperseg=N_FFT,
                noverlap=N_FFT - HOP_LENGTH,
                nfft=N_FFT,
                boundary=None,
                padded=False,
            )
            magnitude = np.abs(stft_matrix)
            phase = np.angle(stft_matrix)

            low_energy = AudioProcessor._calculate_band_energy(magnitude, LOW_FREQ_RANGE)
            mid_energy = AudioProcessor._calculate_band_energy(magnitude, MID_FREQ_RANGE)
            high_energy = AudioProcessor._calculate_band_energy(magnitude, HIGH_FREQ_RANGE)

            low_log_energy = np.log10(low_energy + 1)
            mid_log_energy = np.log10(mid_energy + 1)
            high_log_energy = np.log10(high_energy + 1)

            duration = float(len(audio_samples) / SAMPLE_RATE)
            n_frames = int(magnitude.shape[1])

            print("完成！")
            return AudioData(
                audio_samples=audio_samples,
                sample_rate=SAMPLE_RATE,
                duration=duration,
                n_frames=n_frames,
                low_freq_energy=low_log_energy,
                mid_freq_energy=mid_log_energy,
                high_freq_energy=high_log_energy,
                phase=phase,
            )
        except Exception as exc:
            print(f"错误：无法加载音频文件。{exc}")
            return None

    @staticmethod
    def _calculate_band_energy(magnitude: np.ndarray, freq_range: Tuple[int, int]) -> np.ndarray:
        start_freq, end_freq = freq_range
        start_bin = freq_to_bin(start_freq, SAMPLE_RATE, N_FFT)
        end_bin = freq_to_bin(end_freq, SAMPLE_RATE, N_FFT) + 1
        return np.sum(magnitude[start_bin:end_bin, :], axis=0)
