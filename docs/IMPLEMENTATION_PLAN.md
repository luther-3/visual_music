# 实现计划 (IMPLEMENTATION_PLAN)

## 概述
本文档描述音乐可视化工具的逐步构建序列。按照此顺序开发可以确保每一步都有可运行的版本，便于调试和验证。

---

## 第 0 步：环境准备

### 目标
确保所有依赖正确安装，项目结构就绪。

### 任务
1. 创建项目目录结构（`assets/`、`docs/`）
2. 创建 `requirements.txt`，安装依赖：`pip install -r requirements.txt`
3. 安装 FFmpeg（用于 MP3 支持）
4. 创建并运行 `verify_installation.py`

### 验证
- `verify_installation.py` 所有必需项输出 ✓
- `python -c "import librosa, pygame, numpy"` 无报错

---

## 第 1 步：实现 config.py

### 目标
集中管理所有配置参数。

### 任务
1. 窗口参数：`WINDOW_WIDTH=1280`，`WINDOW_HEIGHT=720`，`FPS=60`，`BACKGROUND_COLOR=(10,10,20)`
2. 音频参数：`SAMPLE_RATE=22050`，`N_FFT=2048`，`HOP_LENGTH=512`，`WINDOW_TYPE='hann'`
3. 频段范围：`LOW_FREQ_RANGE=(20,250)`，`MID_FREQ_RANGE=(250,4000)`，`HIGH_FREQ_RANGE=(4000,11025)`（上限为奈奎斯特频率）
4. 粒子配置：`LOW_FREQ_PARTICLE_CONFIG`，`MID_FREQ_PARTICLE_CONFIG`，`HIGH_FREQ_PARTICLE_CONFIG`（含 size_range、speed_range、lifetime_range、color_start、color_end、max_count、orbit_centers）
5. 归一化参数：`NORMALIZATION_WINDOW_SIZE=86`
6. 拖尾参数：`TRAIL_ALPHA=40`
7. 调试开关：`DEBUG_MODE=False`，`SHOW_INFO=True`

### 验证
- `python -c "import config; print(config.WINDOW_WIDTH)"` 输出 `1280`

---

## 第 2 步：实现 utils.py

### 目标
提供通用工具函数，供其他模块调用。

### 任务
1. `interpolate_color(color1, color2, factor) -> tuple`
   - 输入：两个 RGB 元组，插值因子 [0,1]
   - 输出：插值后的 RGB 元组
   - 实现：对 R/G/B 分量分别线性插值，用 `np.clip` 限制范围

2. `map_value(value, in_min, in_max, out_min, out_max) -> float`
   - 将数值从一个范围映射到另一个范围

3. `freq_to_bin(freq, sample_rate, n_fft) -> int`
   - 公式：`int(freq * n_fft / sample_rate)`

4. `normalize_energy(energy, local_max) -> float`
   - 公式：`np.clip(energy / local_max, 0, 1) if local_max > 0 else 0`

### 验证
```python
from utils import interpolate_color
print(interpolate_color((0,0,0), (255,255,255), 0.5))  # 应输出 (127, 127, 127)
```

---

## 第 3 步：实现 audio_processor.py

### 目标
加载音频文件，执行 STFT，提取三个频段的对数能量数组。

### 任务

**AudioProcessor 类：**

1. `load(file_path: str) -> AudioData`
   - 调用 `librosa.load(file_path, sr=22050)` 加载音频
   - 打印"正在加载音频文件..."
   - 调用 `librosa.stft(y, n_fft=2048, hop_length=512, window='hann')` 计算 STFT
   - 打印"正在处理音频数据..."
   - 计算幅度谱：`magnitude = np.abs(stft)`
   - 计算相位谱：`phase = np.angle(stft)`（保留备用）
   - 调用 `_calculate_band_energy()` 计算三个频段能量
   - 对数映射：`log_energy = np.log10(energy + 1)`
   - 打印"完成！"
   - 返回 `AudioData` 对象
   - 用 `try/except` 包裹，失败时打印错误并返回 None（由 main.py 捕获后返回文件选择界面）

2. `_calculate_band_energy(magnitude, freq_range) -> np.ndarray`
   - 用 `freq_to_bin()` 计算 start_bin 和 end_bin
   - 返回 `np.sum(magnitude[start_bin:end_bin, :], axis=0)`

**AudioData 类（数据容器）：**
- 属性：`audio_samples`，`sample_rate`，`duration`，`n_frames`
- 属性：`low_freq_energy`，`mid_freq_energy`，`high_freq_energy`（均为对数能量数组）
- 属性：`phase`（相位谱，备用）
- 方法：`get_normalized_energy(frame_index, window_size=86) -> (float, float, float)`
  - 计算滑动窗口范围：`start=max(0, frame_index-43)`，`end=min(n_frames, frame_index+43)`
  - 分别计算三个频段的局部最大值
  - 返回归一化后的三个能量值，范围 [0,1]

### 验证
```python
from audio_processor import AudioProcessor
data = AudioProcessor.load("test.wav")
print(data.n_frames)  # 应输出正整数
print(data.get_normalized_energy(0))  # 应输出三个 [0,1] 的浮点数
```

---

## 第 4 步：实现 particle_system.py

### 目标
实现三层粒子系统，每层对应一个频段。

### 任务

**Particle 类：**
- 属性：`x`，`y`，`vx`，`vy`，`size`，`original_size`，`color`，`alpha`，`lifetime`，`max_lifetime`，`particle_type`
- 中频专属：`orbit_center_x`，`orbit_center_y`，`orbit_radius`，`angle`，`angular_speed`
- 高频专属：`direction_angle`
- 方法：`update()` - 更新位置/生命周期/alpha/size
- 方法：`is_alive() -> bool` - 返回 `self.lifetime > 0`
- 方法：`is_out_of_bounds(width, height) -> bool`

**低频粒子 `update()` 逻辑：**
```python
self.x += self.vx
self.y += self.vy
self.lifetime -= 1
decay = self.lifetime / self.max_lifetime
self.alpha = int(255 * decay)
self.size = self.original_size * decay
```

**中频粒子 `update()` 逻辑：**
```python
self.angle += self.angular_speed
self.x = self.orbit_center_x + self.orbit_radius * math.cos(self.angle)
self.y = self.orbit_center_y + self.orbit_radius * math.sin(self.angle)
self.lifetime -= 1
decay = self.lifetime / self.max_lifetime
self.alpha = int(255 * decay)
self.size = self.original_size * decay
```

**高频粒子 `update()` 逻辑：**
```python
self.direction_angle += random.uniform(-0.3, 0.3)
speed = math.sqrt(self.vx**2 + self.vy**2)
self.vx = speed * math.cos(self.direction_angle)
self.vy = speed * math.sin(self.direction_angle)
self.x += self.vx
self.y += self.vy
self.lifetime -= 1
decay = self.lifetime / self.max_lifetime
self.alpha = int(255 * decay)
self.size = self.original_size * decay
```

**ParticleEmitter 类：**
- `__init__(emitter_type, config)`：初始化，`self.particles = []`
- `emit(normalized_energy)`：
  - 计算数量：`num = int(normalized_energy * config['max_count'])`
  - 创建粒子，根据 `emitter_type` 设置不同初始参数
  - 添加到 `self.particles`
- `update_particles()`：调用每个粒子的 `update()`，移除 `is_alive()==False` 或越界的粒子
- `get_active_particles() -> list`：返回 `self.particles`
- `clear()`：`self.particles = []`

**ParticleSystem 类：**
- `__init__()`：创建三个 `ParticleEmitter`，`display_mode = 'all'`
- `update(low_energy, mid_energy, high_energy)`：
  - 调用三个 emitter 的 `emit()` 和 `update_particles()`
  - 检查总粒子数，超过 `MAX_PARTICLES=3000` 时跳过 `emit()`
- `get_particles_to_render() -> list`：根据 `display_mode` 返回对应粒子列表
- `set_display_mode(mode)`：设置 `display_mode`
- `clear_all()`：清空三个 emitter

### 验证
```python
from particle_system import ParticleSystem
ps = ParticleSystem()
ps.update(0.8, 0.5, 0.3)
print(len(ps.get_particles_to_render()))  # 应输出正整数
```

---

## 第 5 步：实现 visualizer.py

### 目标
实现 Pygame 可视化引擎，包含主循环、渲染、事件处理。

### 任务

**Visualizer 类：**

1. `__init__()`
   - `pygame.init()`
   - `pygame.display.set_mode((1280, 720))`
   - `pygame.display.set_caption("音乐可视化")`
   - `pygame.mixer.init(frequency=22050)`
   - 初始化 `ParticleSystem`
   - 初始化状态变量：`is_paused=False`，`display_mode='all'`，`clock=pygame.time.Clock()`

2. `run(audio_data: AudioData, audio_file_path: str)`
   - `pygame.mixer.music.load(audio_file_path)`
   - `pygame.mixer.music.play()`
   - 进入主循环

3. `_handle_events() -> bool`（返回 False 表示退出）
   - 处理 `QUIT`：返回 False
   - 处理 `KEYDOWN`：
     - `K_ESCAPE`：返回 False
     - `K_SPACE`：切换暂停/继续
     - `K_1`：`particle_system.set_display_mode('low')`
     - `K_2`：`particle_system.set_display_mode('mid')`
     - `K_3`：`particle_system.set_display_mode('high')`
     - `K_a`：`particle_system.set_display_mode('all')`

4. `_get_current_frame(audio_data) -> int`
   - `time_ms = pygame.mixer.music.get_pos()`
   - `return int((time_ms / 1000.0) * 22050 / 512)`
   - 边界检查：不超过 `audio_data.n_frames - 1`

5. `_render(particles)`
   - 绘制拖尾背景（半透明矩形，alpha=40）
   - 对每个粒子：
     - 创建 `Surface((size*2, size*2), pygame.SRCALPHA)`
     - `pygame.draw.circle(surface, (*particle.color, particle.alpha), (size, size), size)`
     - `screen.blit(surface, (particle.x - size, particle.y - size))`
   - 如果 `SHOW_INFO=True`，绘制时间和 FPS 文本

6. **主循环结构：**
```python
while True:
    if not self._handle_events():
        break
    if not pygame.mixer.music.get_busy() and not self.is_paused:
        break  # 播放结束
    if not self.is_paused:
        frame_index = self._get_current_frame(audio_data)
        low, mid, high = audio_data.get_normalized_energy(frame_index)
        self.particle_system.update(low, mid, high)
    particles = self.particle_system.get_particles_to_render()
    self._render(particles)
    pygame.display.flip()
    self.clock.tick(60)
```

### 验证
- 运行后出现 1280x720 的黑色窗口
- ESC 键可以退出
- 粒子在播放音频时出现并移动

---

## 第 6 步：实现 main.py

### 目标
程序入口，串联文件选择、音频加载、可视化播放的完整流程。

### 任务

1. 主循环（允许用户多次选择文件）：
```python
def select_audio_file() -> str | None:
    import tkinter as tk
    from tkinter import filedialog
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    file_path = filedialog.askopenfilename(
        title="选择音频文件",
        filetypes=[("音频文件", "*.mp3 *.wav *.flac *.ogg"), ("所有文件", "*.*")]
    )
    root.destroy()
    return file_path if file_path else None

def main():
    while True:
        file_path = select_audio_file()
        if not file_path:
            print("未选择文件，程序退出。")
            break
        audio_data = AudioProcessor.load(file_path)
        if audio_data is None:
            continue  # 加载失败，返回文件选择界面
        visualizer = Visualizer()
        visualizer.run(audio_data, file_path)
        visualizer.cleanup()
        # 循环回文件选择

if __name__ == "__main__":
    main()
```

2. `Visualizer.cleanup()`：`pygame.mixer.music.stop()`，`pygame.quit()`

### 验证
- `python main.py` 弹出文件选择对话框
- 选择 `.wav` 文件后出现可视化窗口
- ESC 后重新弹出文件选择对话框
- 取消选择后程序退出

---

## 第 7 步：集成测试与效果调优

### 目标
测试完整流程，调整参数使视觉效果达到最佳。

### 测试项目
1. 使用 `.wav` 文件测试（无 FFmpeg 依赖）
2. 使用 `.mp3` 文件测试（需要 FFmpeg）
3. 测试不同类型音乐：流行、古典、电子
4. 测试键盘交互：1/2/3/A 切换模式，SPACE 暂停，ESC 退出
5. 测试帧率稳定性（应在 30 FPS 以上）
6. 测试播放结束后自动返回文件选择

### 调优参数（在 config.py 中调整）
- `TRAIL_ALPHA`：拖尾速度（越小拖尾越长）
- `max_count`：各频段粒子数量上限
- `size_range`：粒子大小范围
- `lifetime_range`：粒子生命周期
- `NORMALIZATION_WINDOW_SIZE`：归一化窗口大小（影响动态范围）

### 验证通过标准
- [ ] 文件选择流程正常
- [ ] 音频加载和 STFT 处理无报错
- [ ] 粒子系统三层效果清晰可见
- [ ] 音频和视觉效果同步
- [ ] 帧率 ≥ 30 FPS
- [ ] ESC 返回文件选择
- [ ] 播放结束自动返回文件选择
- [ ] 1/2/3/A 键切换显示模式正常

---

## 构建顺序总结

| 步骤 | 文件 | 依赖 | 预计时间 |
|------|------|------|---------|
| 0 | requirements.txt, verify_installation.py | 无 | 30 分钟 |
| 1 | config.py | 无 | 30 分钟 |
| 2 | utils.py | config.py | 30 分钟 |
| 3 | audio_processor.py | utils.py, config.py | 2 小时 |
| 4 | particle_system.py | utils.py, config.py | 3 小时 |
| 5 | visualizer.py | particle_system.py, config.py | 2 小时 |
| 6 | main.py | 所有模块 | 1 小时 |
| 7 | 集成测试和调优 | 全部 | 2 小时 |

**总预计时间：11-12 小时**

---

## 关键注意事项

1. **不要跳步**：每一步完成后先运行验证，确认无报错再进入下一步
2. **先用 WAV 测试**：WAV 格式无需 FFmpeg，更容易验证音频处理逻辑
3. **粒子 alpha 渲染**：Pygame 的 per-pixel alpha 需要使用 `pygame.SRCALPHA` 标志创建 Surface
4. **tkinter 和 Pygame 不能同时显示窗口**：在启动 Pygame 之前必须用 `root.destroy()` 关闭 tkinter 窗口
5. **pygame.mixer.music.get_pos() 在暂停后继续计时**：暂停时需要记录暂停时间并手动补偿
