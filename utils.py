"""Utility helpers for visualization modules."""

import numpy as np


def interpolate_color(color1, color2, factor):
    """Linearly interpolate two RGB colors with factor in [0, 1]."""
    factor = float(np.clip(factor, 0, 1))
    r = int(color1[0] + (color2[0] - color1[0]) * factor)
    g = int(color1[1] + (color2[1] - color1[1]) * factor)
    b = int(color1[2] + (color2[2] - color1[2]) * factor)
    return (r, g, b)


def map_value(value, in_min, in_max, out_min, out_max):
    """Map value from input range to output range."""
    value = float(np.clip(value, in_min, in_max))
    if in_max == in_min:
        return float(out_min)
    return (value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min


def freq_to_bin(freq, sample_rate, n_fft):
    """Convert frequency in Hz to FFT bin index."""
    return int(freq * n_fft / sample_rate)


def normalize_energy(energy, local_max):
    """Normalize energy to [0, 1] using a local maximum."""
    if local_max > 0:
        return float(np.clip(energy / local_max, 0, 1))
    return 0.0
