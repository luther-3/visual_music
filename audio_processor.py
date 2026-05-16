"""Audio loading and spectral feature extraction."""

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly, stft as scipy_stft

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
            audio_samples, source_sr, used_path = AudioProcessor._read_audio_with_fallback(file_path)

            if isinstance(audio_samples, np.ndarray) and audio_samples.ndim > 1:
                audio_samples = np.mean(audio_samples, axis=1)

            audio_samples = np.asarray(audio_samples, dtype=np.float32)

            if source_sr != SAMPLE_RATE:
                print(f"检测到采样率 {source_sr}，正在自动重采样到 {SAMPLE_RATE}...")
                gcd = int(np.gcd(source_sr, SAMPLE_RATE))
                up = SAMPLE_RATE // gcd
                down = source_sr // gcd
                audio_samples = resample_poly(audio_samples, up, down).astype(np.float32)
                source_sr = SAMPLE_RATE

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
            AudioProcessor._export_band_energy_timeseries(file_path, low_energy, mid_energy, high_energy)

            low_log_energy = np.log10(low_energy + 1)
            mid_log_energy = np.log10(mid_energy + 1)
            high_log_energy = np.log10(high_energy + 1)

            duration = float(len(audio_samples) / SAMPLE_RATE)
            n_frames = int(magnitude.shape[1])

            if used_path != file_path:
                print(f"已自动转换文件：{used_path}")
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
    def _read_audio_with_fallback(file_path: str):
        try:
            audio_samples, source_sr = sf.read(file_path, always_2d=False)
            return audio_samples, source_sr, file_path
        except Exception as read_exc:
            path = Path(file_path)
            if path.suffix.lower() != ".mp3":
                raise read_exc

            wav_path = path.with_suffix(".wav")
            AudioProcessor._convert_mp3_to_wav_ffmpeg(path, wav_path)
            audio_samples, source_sr = sf.read(str(wav_path), always_2d=False)
            return audio_samples, source_sr, str(wav_path)

    @staticmethod
    def _convert_mp3_to_wav_ffmpeg(mp3_path: Path, wav_path: Path):
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(mp3_path),
            "-ar",
            str(SAMPLE_RATE),
            "-ac",
            "1",
            str(wav_path),
        ]
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
        except FileNotFoundError as exc:
            raise RuntimeError(
                "未找到 ffmpeg。请先安装 ffmpeg 并确保当前终端可执行 ffmpeg 命令。"
            ) from exc
        except subprocess.CalledProcessError as exc:
            stderr = (exc.stderr or "").strip()
            raise RuntimeError(f"ffmpeg 转换 mp3 失败：{stderr}") from exc

    @staticmethod
    def _calculate_band_energy(magnitude: np.ndarray, freq_range: Tuple[int, int]) -> np.ndarray:
        start_freq, end_freq = freq_range
        start_bin = freq_to_bin(start_freq, SAMPLE_RATE, N_FFT)
        end_bin = freq_to_bin(end_freq, SAMPLE_RATE, N_FFT) + 1
        return np.sum(magnitude[start_bin:end_bin, :], axis=0)

    @staticmethod
    def _export_band_energy_timeseries(
        file_path: str, low_energy: np.ndarray, mid_energy: np.ndarray, high_energy: np.ndarray
    ):
        out_dir = Path("visual_spectrum")
        out_dir.mkdir(parents=True, exist_ok=True)

        audio_name = Path(file_path).stem
        out_path = out_dir / f"{audio_name}_band_energy_timeseries.png"
        frame_idx = np.arange(len(low_energy))

        plt.figure(figsize=(12, 5))
        plt.plot(frame_idx, low_energy, label="Low Band Energy (20-250Hz)", color="#ff7043", linewidth=1.2)
        plt.plot(frame_idx, mid_energy, label="Mid Band Energy (250-4000Hz)", color="#29b6f6", linewidth=1.2)
        plt.plot(frame_idx, high_energy, label="High Band Energy (4000-11025Hz)", color="#ffee58", linewidth=1.2)
        plt.title(f"{audio_name} - Band Energy Time Series")
        plt.xlabel("Time Frame")
        plt.ylabel("Energy")
        plt.legend(loc="upper right")
        plt.grid(alpha=0.25)
        plt.tight_layout()
        plt.savefig(out_path, dpi=200)
        plt.close()
