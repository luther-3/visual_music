"""Project configuration constants."""

# 窗口设置
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
FPS = 60
BACKGROUND_COLOR = (10, 10, 20)

# 音频处理参数
SAMPLE_RATE = 22050
N_FFT = 2048
HOP_LENGTH = 512
WINDOW_TYPE = 'hann'

# 频段划分 (Hz)
LOW_FREQ_RANGE = (20, 250)
MID_FREQ_RANGE = (250, 4000)
HIGH_FREQ_RANGE = (4000, 11025)  # 奈奎斯特频率上限（SAMPLE_RATE=22050）

# 粒子系统参数
MAX_PARTICLES = 3000

# 低频粒子配置
LOW_FREQ_PARTICLE_CONFIG = {
    'size_range': (8, 20),
    'speed_range': (2, 8),
    'lifetime_range': (30, 60),
    'color_start': (200, 50, 50),
    'color_end': (255, 150, 50),
    'emission_pattern': 'burst',
    'max_count': 100
}

# 中频粒子配置
MID_FREQ_PARTICLE_CONFIG = {
    'size_range': (4, 10),
    'speed_range': (1, 5),
    'lifetime_range': (40, 80),
    'color_start': (50, 100, 200),
    'color_end': (50, 200, 200),
    'emission_pattern': 'circular',
    'max_count': 200
    ,
    'orbit_centers': [
        (640, 360),
        (320, 180),
        (960, 180),
        (320, 540),
        (960, 540),
    ],
}

# 高频粒子配置
HIGH_FREQ_PARTICLE_CONFIG = {
    'size_range': (2, 5),
    'speed_range': (0.5, 3),
    'lifetime_range': (20, 40),
    'color_start': (255, 255, 200),
    'color_end': (255, 255, 100),
    'emission_pattern': 'scatter',
    'max_count': 300
}

# 归一化参数
NORMALIZATION_WINDOW_SIZE = 86

# 拖尾参数
TRAIL_ALPHA = 40

# 调试模式
DEBUG_MODE = False
SHOW_FPS = True
SHOW_INFO = True
