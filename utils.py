"""
工具函数
"""
import numpy as np


def interpolate_color(color1, color2, factor):
    """
    在两个颜色之间插值

    Args:
        color1: 起始颜色 (R, G, B)
        color2: 结束颜色 (R, G, B)
        factor: 插值因子 [0, 1]

    Returns:
        插值后的颜色 (R, G, B)
    """
    factor = np.clip(factor, 0, 1)
    r = int(color1[0] + (color2[0] - color1[0]) * factor)
    g = int(color1[1] + (color2[1] - color1[1]) * factor)
    b = int(color1[2] + (color2[2] - color1[2]) * factor)
    return (r, g, b)


def map_value(value, in_min, in_max, out_min, out_max):
    """
    将值从一个范围映射到另一个范围

    Args:
        value: 输入值
        in_min: 输入范围最小值
        in_max: 输入范围最大值
        out_min: 输出范围最小值
        out_max: 输出范围最大值

    Returns:
        映射后的值
    """
    value = np.clip(value, in_min, in_max)
    return (value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min


def freq_to_bin(freq, sample_rate, n_fft):
    """
    将频率转换为 FFT bin 索引

    Args:
        freq: 频率 (Hz)
        sample_rate: 采样率
        n_fft: FFT 大小

    Returns:
        bin 索引
    """
    return int(freq * n_fft / sample_rate)


def calculate_energy(spectrum, start_bin, end_bin):
    """
    计算频谱某个范围的能量

    Args:
        spectrum: 频谱数组
        start_bin: 起始 bin
        end_bin: 结束 bin

    Returns:
        能量值
    """
    return np.sum(spectrum[start_bin:end_bin])


def normalize_energy(energy, scale=1.0):
    """
    归一化能量值

    Args:
        energy: 原始能量
        scale: 缩放因子

    Returns:
        归一化后的能量 [0, 1]
    """
    # 使用对数映射，使能量变化更平滑
    normalized = np.log10(energy + 1) * scale
    return np.clip(normalized, 0, 1)
