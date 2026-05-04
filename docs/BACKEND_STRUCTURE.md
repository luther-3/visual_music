# 后端架构文档 (BACKEND_STRUCTURE)

## 概述
本文档定义音乐可视化工具的后端架构，包括数据结构、模块组织、类设计和数据流。

**注意**：本项目是桌面应用，没有传统意义上的"后端服务器"或"数据库"。本文档描述的是应用的核心逻辑层和数据结构。

---

## 架构概览

### 分层架构
```
┌─────────────────────────────────────┐
│      用户界面层 (UI Layer)           │
│  - tkinter 文件选择对话框            │
│  - Pygame 可视化窗口                 │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│    应用逻辑层 (Application Layer)    │
│  - main.py (主程序入口)              │
│  - visualizer.py (可视化引擎)        │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│    业务逻辑层 (Business Logic)       │
│  - audio_processor.py (音频处理)     │
│  - particle_system.py (粒子系统)     │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│    工具层 (Utility Layer)            │
│  - utils.py (工具函数)               │
│  - config.py (配置参数)              │
└─────────────────────────────────────┘
```

---

## 模块结构

### 项目目录结构
```
visual_music/
├── main.py                    # 主程序入口
├── config.py                  # 配置参数
├── audio_processor.py         # 音频处理模块
├── particle_system.py         # 粒子系统模块
├── visualizer.py              # 可视化引擎
├── utils.py                   # 工具函数
├── requirements.txt           # 依赖列表
├── README.md                  # 项目说明
├── verify_installation.py     # 依赖验证脚本
├── docs/                      # 文档目录
│   ├── PRD.md
│   ├── APP_FLOW.md
│   ├── TECH_STACK.md
│   ├── FRONTEND_GUIDELINES.md
│   ├── BACKEND_STRUCTURE.md
│   └── IMPLEMENTATION_PLAN.md
├── assets/                    # 资源文件夹（用户音频）
└── p2a-session/              # 规划文档（不提交到版本控制）
```

---

## 数据结构定义

### 1. 音频数据结构

#### AudioData 类
**文件**: `audio_processor.py`

**用途**: 存储预处理后的音频数据

**属性**:
```python
class AudioData:
    """音频数据容器"""
    
    # 原始音频数据
    audio_samples: np.ndarray          # 音频波形，shape: (n_samples,)
    sample_rate: int                   # 采样率，默认 22050 Hz
    duration: float                    # 音频时长（秒）
    
    # STFT 数据
    stft_matrix: np.ndarray           # 复数 STFT 矩阵，shape: (n_bins, n_frames)
    magnitude: np.ndarray             # 幅度谱，shape: (n_bins, n_frames)
    phase: np.ndarray                 # 相位谱，shape: (n_bins, n_frames)
    
    # 频段能量数据
    low_freq_energy: np.ndarray       # 低频能量，shape: (n_frames,)
    mid_freq_energy: np.ndarray       # 中频能量，shape: (n_frames,)
    high_freq_energy: np.ndarray      # 高频能量，shape: (n_frames,)
    
    # 元数据
    n_frames: int                     # 总帧数
    hop_length: int                   # 帧移，默认 512
    n_fft: int                        # FFT 大小，默认 2048
    
    # 频段 bin 索引
    low_freq_bins: tuple              # (start_bin, end_bin)
    mid_freq_bins: tuple              # (start_bin, end_bin)
    high_freq_bins: tuple             # (start_bin, end_bin)
```

**方法**:
```python
def __init__(self, file_path: str):
    """加载并预处理音频文件"""
    pass

def get_frame_energy(self, frame_index: int) -> tuple:
    """获取指定帧的三个频段能量
    
    Returns:
        (low_energy, mid_energy, high_energy)
    """
    pass

def get_normalized_energy(self, frame_index: int, window_size: int = 86) -> tuple:
    """获取局部归一化后的能量
    
    Args:
        frame_index: 当前帧索引
        window_size: 滑动窗口大小（帧数）
    
    Returns:
        (normalized_low, normalized_mid, normalized_high)
    """
    pass
```

---

### 2. 粒子数据结构

#### Particle 类
**文件**: `particle_system.py`

**用途**: 表示单个粒子

**属性**:
```python
class Particle:
    """粒子对象"""
    
    # 位置和运动
    x: float                          # X 坐标（像素）
    y: float                          # Y 坐标（像素）
    vx: float                         # X 方向速度（像素/帧）
    vy: float                         # Y 方向速度（像素/帧）
    
    # 视觉属性
    size: float                       # 粒子大小（直径，像素）
    original_size: float              # 初始大小（用于衰减计算）
    color: tuple                      # RGB 颜色，(r, g, b)
    alpha: int                        # 透明度，0-255
    
    # 生命周期
    lifetime: int                     # 剩余生命周期（帧数）
    max_lifetime: int                 # 最大生命周期（帧数）
    
    # 类型标识
    particle_type: str                # 'low', 'mid', 'high'
    
    # 中频粒子特有属性
    orbit_center_x: float = None      # 轨道中心 X（仅中频）
    orbit_center_y: float = None      # 轨道中心 Y（仅中频）
    orbit_radius: float = None        # 轨道半径（仅中频）
    angle: float = None               # 当前角度（仅中频）
    angular_speed: float = None       # 角速度（仅中频）
    
    # 高频粒子特有属性
    direction_angle: float = None     # 运动方向角度（仅高频）
```

**方法**:
```python
def __init__(self, particle_type: str, **kwargs):
    """初始化粒子"""
    pass

def update(self):
    """更新粒子状态（位置、生命周期、透明度、大小）"""
    pass

def is_alive(self) -> bool:
    """检查粒子是否存活"""
    pass

def is_out_of_bounds(self, width: int, height: int) -> bool:
    """检查粒子是否超出边界"""
    pass
```

---

#### ParticleEmitter 类
**文件**: `particle_system.py`

**用途**: 粒子发射器，负责生成粒子

**属性**:
```python
class ParticleEmitter:
    """粒子发射器"""
    
    emitter_type: str                 # 'low', 'mid', 'high'
    config: dict                      # 发射器配置（从 config.py 读取）
    particles: list                   # 粒子列表
    max_particles: int                # 最大粒子数
```

**方法**:
```python
def __init__(self, emitter_type: str, config: dict):
    """初始化发射器"""
    pass

def emit(self, normalized_energy: float):
    """根据能量发射粒子
    
    Args:
        normalized_energy: 归一化能量值 [0, 1]
    """
    pass

def update_particles(self):
    """更新所有粒子状态，移除死亡粒子"""
    pass

def get_active_particles(self) -> list:
    """获取所有存活的粒子"""
    pass

def clear(self):
    """清空所有粒子"""
    pass
```

---

#### ParticleSystem 类
**文件**: `particle_system.py`

**用途**: 管理三个粒子发射器

**属性**:
```python
class ParticleSystem:
    """粒子系统管理器"""
    
    low_freq_emitter: ParticleEmitter
    mid_freq_emitter: ParticleEmitter
    high_freq_emitter: ParticleEmitter
    
    display_mode: str                 # 'all', 'low', 'mid', 'high'
    total_particle_count: int         # 当前总粒子数
```

**方法**:
```python
def __init__(self):
    """初始化粒子系统"""
    pass

def update(self, low_energy: float, mid_energy: float, high_energy: float):
    """更新粒子系统
    
    Args:
        low_energy: 低频归一化能量
        mid_energy: 中频归一化能量
        high_energy: 高频归一化能量
    """
    pass

def get_particles_to_render(self) -> list:
    """根据显示模式获取需要渲染的粒子"""
    pass

def set_display_mode(self, mode: str):
    """设置显示模式"""
    pass

def clear_all(self):
    """清空所有粒子"""
    pass

def get_particle_count(self) -> dict:
    """获取各类粒子数量统计"""
    pass
```

---

### 3. 可视化状态结构

#### VisualizerState 类
**文件**: `visualizer.py`

**用途**: 管理可视化器的状态

**属性**:
```python
class VisualizerState:
    """可视化器状态"""
    
    # 播放状态
    is_playing: bool                  # 是否正在播放
    is_paused: bool                   # 是否暂停
    current_time: float               # 当前播放时间（秒）
    current_frame: int                # 当前帧索引
    
    # 显示状态
    display_mode: str                 # 'all', 'low', 'mid', 'high'
    show_info: bool                   # 是否显示信息（时间、FPS 等）
    
    # 性能统计
    fps: float                        # 当前帧率
    frame_count: int                  # 总渲染帧数
    particle_count: int               # 当前粒子总数
```

---

## 类关系图

```
┌─────────────┐
│   main.py   │
└──────┬──────┘
       │
       ├──────────────────────────────┐
       │                              │
       ↓                              ↓
┌──────────────┐              ┌──────────────┐
│ AudioProcessor│              │  Visualizer  │
└──────┬───────┘              └──────┬───────┘
       │                              │
       │ 创建                         │ 使用
       ↓                              ↓
┌──────────────┐              ┌──────────────┐
│  AudioData   │              │ParticleSystem│
└──────────────┘              └──────┬───────┘
                                     │
                                     │ 包含
                                     ↓
                              ┌──────────────┐
                              │ParticleEmitter│
                              └──────┬───────┘
                                     │
                                     │ 管理
                                     ↓
                              ┌──────────────┐
                              │   Particle   │
                              └──────────────┘
```

---

## 数据流

### 1. 音频加载和预处理流程
```
用户选择文件
    ↓
main.py 调用 AudioProcessor.load()
    ↓
AudioProcessor 读取文件 (librosa.load)
    ↓
计算 STFT (librosa.stft)
    ↓
提取幅度谱和相位谱
    ↓
频段分离（计算 bin 索引）
    ↓
计算每帧的频段能量
    ↓
对数映射 (log10)
    ↓
创建 AudioData 对象
    ↓
返回给 main.py
```

### 2. 实时渲染流程
```
主循环开始
    ↓
获取当前播放时间 (pygame.mixer.music.get_pos)
    ↓
计算当前帧索引
    ↓
从 AudioData 获取当前帧能量
    ↓
局部归一化能量
    ↓
传递给 ParticleSystem.update()
    ↓
ParticleSystem 调用三个 Emitter.emit()
    ↓
每个 Emitter 创建新粒子
    ↓
ParticleSystem 调用 Emitter.update_particles()
    ↓
每个粒子更新位置、生命周期、透明度
    ↓
移除死亡粒子
    ↓
Visualizer 获取需要渲染的粒子
    ↓
绘制背景拖尾效果
    ↓
遍历粒子列表，绘制每个粒子
    ↓
绘制 UI 信息（可选）
    ↓
pygame.display.flip()
    ↓
控制帧率 (clock.tick(60))
    ↓
回到主循环开始
```

### 3. 用户交互流程
```
用户按键
    ↓
Pygame 事件队列
    ↓
Visualizer 事件处理
    ↓
根据按键类型执行操作:
    - SPACE: 切换暂停状态
    - ESC: 退出可视化
    - 1/2/3/A: 切换显示模式
    - 左右箭头: 快进/快退（可选）
    ↓
更新 VisualizerState
    ↓
继续主循环
```

---

## 核心算法

### 1. STFT 计算
**位置**: `audio_processor.py` → `AudioProcessor.load()`

**输入**:
- 音频波形: `np.ndarray`, shape: `(n_samples,)`
- 参数: `n_fft=2048`, `hop_length=512`, `window='hann'`

**输出**:
- STFT 矩阵: `np.ndarray`, shape: `(n_bins, n_frames)`
  - `n_bins = n_fft // 2 + 1 = 1025`
  - `n_frames = (n_samples - n_fft) // hop_length + 1`

**算法**:
```python
stft_matrix = librosa.stft(
    y=audio_samples,
    n_fft=2048,
    hop_length=512,
    window='hann'
)
magnitude = np.abs(stft_matrix)
phase = np.angle(stft_matrix)
```

---

### 2. 频段能量计算
**位置**: `audio_processor.py` → `AudioProcessor._calculate_band_energy()`

**输入**:
- 幅度谱: `np.ndarray`, shape: `(1025, n_frames)`
- 频段范围: `(freq_min, freq_max)` Hz

**输出**:
- 能量数组: `np.ndarray`, shape: `(n_frames,)`

**算法**:
```python
# 计算 bin 索引（end_bin 为切片 exclusive 上界，+1 确保包含最高频率 bin）
start_bin = int(freq_min * n_fft / sample_rate)
end_bin = int(freq_max * n_fft / sample_rate) + 1

# 对每一帧求和
energy = np.sum(magnitude[start_bin:end_bin, :], axis=0)

# 对数映射
log_energy = np.log10(energy + 1)
```

---

### 3. 局部归一化
**位置**: `audio_processor.py` → `AudioData.get_normalized_energy()`

**输入**:
- 当前帧索引: `frame_index`
- 对数能量数组: `log_energy`, shape: `(n_frames,)`
- 窗口大小: `window_size = 86` 帧

**输出**:
- 归一化能量: `float`, 范围 `[0, 1]`

**算法**:
```python
# 计算窗口范围
start = max(0, frame_index - window_size // 2)
end = min(n_frames, frame_index + window_size // 2)

# 计算局部最大值
local_max = np.max(log_energy[start:end])

# 归一化
if local_max > 0:
    normalized = log_energy[frame_index] / local_max
else:
    normalized = 0

# 限制范围
normalized = np.clip(normalized, 0, 1)
```

---

### 4. 粒子发射算法
**位置**: `particle_system.py` → `ParticleEmitter.emit()`

**输入**:
- 归一化能量: `normalized_energy`, 范围 `[0, 1]`
- 发射器配置: `config` (从 config.py)

**输出**:
- 新创建的粒子列表

**算法**:
```python
# 计算发射数量
num_particles = int(normalized_energy * config['max_count'])

# 创建粒子
for i in range(num_particles):
    particle = Particle(
        particle_type=self.emitter_type,
        x=...,  # 根据类型设置初始位置
        y=...,
        vx=...,  # 根据能量计算速度
        vy=...,
        size=config['size_range'][0] + normalized_energy * (config['size_range'][1] - config['size_range'][0]),
        color=interpolate_color(config['color_start'], config['color_end'], normalized_energy),
        lifetime=random.randint(*config['lifetime_range'])
    )
    self.particles.append(particle)
```

---

### 5. 粒子更新算法
**位置**: `particle_system.py` → `Particle.update()`

**算法**:
```python
# 更新生命周期
self.lifetime -= 1

# 计算衰减因子
decay_factor = self.lifetime / self.max_lifetime

# 更新透明度和大小
self.alpha = int(255 * decay_factor)
self.size = self.original_size * decay_factor

# 根据类型更新位置
if self.particle_type == 'low':
    # 线性运动
    self.x += self.vx
    self.y += self.vy

elif self.particle_type == 'mid':
    # 圆周运动
    self.angle += self.angular_speed
    self.x = self.orbit_center_x + self.orbit_radius * math.cos(self.angle)
    self.y = self.orbit_center_y + self.orbit_radius * math.sin(self.angle)

elif self.particle_type == 'high':
    # 随机游走
    self.direction_angle += random.uniform(-0.3, 0.3)
    speed = math.sqrt(self.vx**2 + self.vy**2)
    self.vx = speed * math.cos(self.direction_angle)
    self.vy = speed * math.sin(self.direction_angle)
    self.x += self.vx
    self.y += self.vy
```

---

## 配置管理

### config.py 结构
```python
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
HIGH_FREQ_RANGE = (4000, 11025)  # 上限为奈奎斯特频率（SAMPLE_RATE=22050）

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
    'max_count': 200,
    'orbit_centers': [
        (640, 360),   # 中心
        (320, 180),   # 左上
        (960, 180),   # 右上
        (320, 540),   # 左下
        (960, 540)    # 右下
    ]
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

# 能量归一化参数
NORMALIZATION_WINDOW_SIZE = 86  # 帧数（约 2 秒）

# 拖尾效果参数
TRAIL_ALPHA = 40

# 调试模式
DEBUG_MODE = False
SHOW_FPS = True
SHOW_INFO = True
```

---

## 错误处理

### 错误类型定义
```python
class AudioLoadError(Exception):
    """音频加载失败"""
    pass

class AudioProcessError(Exception):
    """音频处理失败"""
    pass

class VisualizationError(Exception):
    """可视化错误"""
    pass
```

### 错误处理策略
1. **文件加载错误**:
   - 捕获 `librosa.load()` 异常
   - 显示友好错误信息
   - 返回 None，由 main.py 捕获后返回文件选择界面

2. **STFT 计算错误**:
   - 捕获 numpy/scipy 异常
   - 显示错误详情
   - 返回 None，由 main.py 捕获后返回文件选择界面

3. **内存不足**:
   - 捕获 `MemoryError`
   - 显示内存不足提示
   - 返回 None，由 main.py 捕获后返回文件选择界面

4. **Pygame 错误**:
   - 捕获 `pygame.error`
   - 尝试恢复或退出

---

## 性能优化策略

### 1. 粒子数量控制
- 每个发射器设置最大粒子数
- 总粒子数不超过 3000
- 及时移除死亡粒子

### 2. 内存管理
- 使用 numpy 数组存储频谱数据（连续内存）
- 粒子列表使用 Python list（动态增长）
- 避免频繁的内存分配和释放

### 3. 渲染优化
- 使用简单的圆形形状（避免复杂多边形）
- 不使用抗锯齿（性能考虑）
- 批量绘制（虽然 Pygame 不支持真正的批量渲染）

### 4. 计算优化
- 预计算对数能量（避免实时计算）
- 使用 numpy 向量化操作
- 避免不必要的数学计算

---

## 测试策略

### 单元测试（可选）
- 测试 `AudioProcessor.load()`
- 测试频段能量计算
- 测试局部归一化
- 测试粒子发射逻辑

### 集成测试
- 测试完整的音频加载到可视化流程
- 测试不同音频格式
- 测试不同音乐类型

### 性能测试
- 测试帧率稳定性
- 测试内存占用
- 测试长音频文件

---

## 日志和调试

### 日志级别
- **INFO**: 正常操作（加载文件、开始播放）
- **WARNING**: 警告信息（帧率下降、粒子数过多）
- **ERROR**: 错误信息（加载失败、渲染错误）
- **DEBUG**: 调试信息（帧索引、能量值、粒子数）

### 调试输出
```python
if config.DEBUG_MODE:
    print(f"Frame: {frame_index}, "
          f"Low: {low_energy:.2f}, "
          f"Mid: {mid_energy:.2f}, "
          f"High: {high_energy:.2f}, "
          f"Particles: {particle_count}")
```

---

## 扩展点

### 1. 新的粒子类型
- 在 `particle_system.py` 中添加新的 `ParticleEmitter` 子类
- 在 `config.py` 中添加配置
- 在 `ParticleSystem` 中注册新发射器

### 2. 新的可视化模式
- 在 `visualizer.py` 中添加新的渲染逻辑
- 添加新的显示模式键绑定

### 3. 新的音频特征
- 在 `audio_processor.py` 中添加新的特征提取方法
- 例如：节拍检测、Mel 频谱、Chroma 特征

### 4. 配置文件支持
- 添加 `config_loader.py` 模块
- 支持 JSON 或 YAML 配置文件
- 允许用户自定义参数
