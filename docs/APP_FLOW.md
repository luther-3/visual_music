# 应用流程文档 (APP_FLOW)

## 概述
本文档详细描述音乐可视化工具的每个页面、用户交互路径和状态转换。

---

## 应用状态图

```
[启动] → [文件选择] → [音频加载] → [可视化播放] → [文件选择]
                ↓           ↓                           ↓
           [退出程序]   [文件选择]                  [退出程序]
            （取消）   （加载失败）                  （取消）
```

---

## 页面 1：文件选择界面

### 页面描述
系统原生文件对话框，用户选择要可视化的音频文件。

### 页面元素
- **标题**：选择音频文件
- **文件类型过滤器**：
  - 显示文本："音频文件 (*.mp3 *.wav *.flac *.ogg)"
  - 过滤规则：只显示 .mp3, .wav, .flac, .ogg 文件
- **按钮**：
  - "打开"按钮：确认选择
  - "取消"按钮：取消选择

### 用户操作
1. **操作**：用户浏览文件系统
   - **触发**：对话框打开时自动显示
   - **结果**：显示文件列表

2. **操作**：用户选择一个音频文件并点击"打开"
   - **触发**：用户点击"打开"按钮
   - **验证**：检查文件扩展名是否在支持列表中
   - **成功路径**：
     - 关闭文件对话框
     - 进入"音频加载"状态
   - **失败路径**：
     - 显示错误消息："不支持的文件格式"
     - 返回文件选择界面

3. **操作**：用户点击"取消"或关闭对话框
   - **触发**：用户点击"取消"按钮或关闭窗口
   - **结果**：程序退出

### 状态转换
- **进入条件**：
  - 程序启动
  - 从可视化播放界面退出（ESC 键）
  - 音频播放结束
- **退出条件**：
  - 用户选择文件 → 进入"音频加载"
  - 用户取消选择 → 程序退出

---

## 状态 2：音频加载

### 状态描述
后台加载和预处理音频文件，用户看到控制台输出的进度信息。

### 显示内容
控制台输出：
```
正在加载音频文件...
正在处理音频数据...
完成！
```

### 处理流程
1. **步骤 1**：加载音频文件
   - **操作**：使用 librosa.load() 加载音频
   - **参数**：
     - 文件路径：用户选择的文件
     - 采样率：22050 Hz
   - **输出**：音频波形数据 (numpy array)
   - **控制台输出**："正在加载音频文件..."
   - **预计时间**：1-3 秒

2. **步骤 2**：计算 STFT
   - **操作**：使用 librosa.stft() 计算短时傅立叶变换
   - **参数**：
     - n_fft: 2048
     - hop_length: 512
     - window: 'hann'
   - **输出**：复数频谱矩阵
   - **控制台输出**："正在处理音频数据..."
   - **预计时间**：2-5 秒

3. **步骤 3**：提取幅度谱和相位谱
   - **操作**：
     - 幅度谱：`magnitude = np.abs(stft)`
     - 相位谱：`phase = np.angle(stft)`（保留但不使用）
   - **输出**：幅度谱矩阵

4. **步骤 4**：频段分离
   - **操作**：根据频率范围提取对应的 bin 索引
   - **低频**：20-250 Hz
     - 起始 bin：`int(20 * 2048 / 22050)` = 1
     - 结束 bin：`int(250 * 2048 / 22050)` = 23
   - **中频**：250-4000 Hz
     - 起始 bin：23
     - 结束 bin：`int(4000 * 2048 / 22050)` = 371
   - **高频**：4000-11025 Hz（奈奎斯特频率上限）
     - 起始 bin：371
     - 结束 bin（切片exclusive上界）：`int(11025 * 2048 / 22050) + 1` = 1025，即 `magnitude[371:1025]` 覆盖 bin 371-1024

5. **步骤 5**：计算频段能量
   - **操作**：对每一帧的每个频段求和
   - **公式**：`energy = np.sum(magnitude[start_bin:end_bin, :], axis=0)`
   - **注意**：`end_bin` 为切片的 exclusive 上界，即 `freq_to_bin(freq_max) + 1`，确保最高频率的 bin 被包含
   - **输出**：三个能量数组（低/中/高频），每个数组长度 = 帧数

6. **步骤 6**：对数映射
   - **操作**：对能量值取对数
   - **公式**：`log_energy = np.log10(energy + 1)`
   - **输出**：对数能量数组

7. **步骤 7**：存储数据
   - **操作**：将以下数据存储在内存中
     - 音频波形数据
     - 对数能量数组（低/中/高频）
     - 音频总时长
     - 总帧数
   - **控制台输出**："完成！"

### 错误处理
1. **错误**：文件加载失败
   - **原因**：文件损坏、格式不支持、缺少依赖（ffmpeg）
   - **处理**：
     - 控制台输出："错误：无法加载音频文件"
     - 显示错误详情
     - 返回文件选择界面（不退出程序）

2. **错误**：内存不足
   - **原因**：音频文件过大
   - **处理**：
     - 控制台输出："错误：内存不足，请选择较短的音频文件"
     - 返回文件选择界面（不退出程序）

### 状态转换
- **进入条件**：用户在文件选择界面选择文件
- **退出条件**：
  - 加载成功 → 进入"可视化播放"
  - 加载失败 → 返回文件选择界面

---

## 页面 3：可视化播放界面

### 页面描述
固定大小的 Pygame 窗口（1280x720），显示实时的粒子系统可视化效果。

### 页面元素
- **窗口大小**：1280x720 像素
- **窗口标题**："音乐可视化"
- **背景**：深色 (RGB: 10, 10, 20)
- **粒子**：三层粒子系统（低/中/高频）
- **信息显示**（可选）：
  - 当前时间 / 总时间（右上角）
  - FPS（左上角）
  - 当前显示模式（左下角）

### 初始化流程
1. **步骤 1**：初始化 Pygame
   - **操作**：`pygame.init()`
   - **创建窗口**：`pygame.display.set_mode((1280, 720))`
   - **设置标题**：`pygame.display.set_caption("音乐可视化")`

2. **步骤 2**：加载音频到 Pygame.mixer
   - **操作**：
     - 初始化 mixer：`pygame.mixer.init(frequency=22050)`
     - 加载音频：`pygame.mixer.music.load(audio_file)`
     - 开始播放：`pygame.mixer.music.play()`

3. **步骤 3**：初始化粒子系统
   - **操作**：创建三个空的粒子列表
     - `low_freq_particles = []`
     - `mid_freq_particles = []`
     - `high_freq_particles = []`

4. **步骤 4**：初始化状态变量
   - `is_paused = False`（播放状态）
   - `display_mode = 'all'`（显示模式：'all', 'low', 'mid', 'high'）
   - `clock = pygame.time.Clock()`（帧率控制）

### 主循环流程

#### 每帧执行的步骤：

**步骤 1：事件处理**
- **操作**：检查所有 Pygame 事件
- **事件类型**：
  1. `QUIT`：用户关闭窗口
     - **处理**：退出主循环，返回文件选择
  2. `KEYDOWN`：用户按下键盘
     - **处理**：根据按键执行相应操作（见下文）

**步骤 2：获取当前播放时间**
- **操作**：`current_time_ms = pygame.mixer.music.get_pos()`
- **转换为秒**：`current_time_s = current_time_ms / 1000.0`
- **计算帧索引**：`frame_index = int(current_time_s * 22050 / 512)`
- **边界检查**：如果 `frame_index >= total_frames`，播放结束

**步骤 3：读取当前帧的能量数据**
- **操作**：从预处理的数据中读取
  - `low_energy = low_freq_energy[frame_index]`
  - `mid_energy = mid_freq_energy[frame_index]`
  - `high_energy = high_freq_energy[frame_index]`

**步骤 4：局部归一化**
- **操作**：计算滑动窗口内的最大值
- **窗口大小**：43 帧（前后各 43 帧，共 86 帧 ≈ 2 秒）
- **计算**：
  ```
  start = max(0, frame_index - 43)
  end = min(total_frames, frame_index + 43)
  low_max = max(low_freq_energy[start:end])
  mid_max = max(mid_freq_energy[start:end])
  high_max = max(high_freq_energy[start:end])
  ```
- **归一化**：
  ```
  normalized_low = low_energy / low_max if low_max > 0 else 0
  normalized_mid = mid_energy / mid_max if mid_max > 0 else 0
  normalized_high = high_energy / high_max if high_max > 0 else 0
  ```

**步骤 5：发射粒子**（如果未暂停）
- **低频粒子**：
  - 计算发射数量：`num = int(normalized_low * 100)`
  - 限制上限：`num = min(num, 100)`
  - 循环 num 次：
    - 创建粒子对象
    - 设置初始位置：(640, 360)
    - 设置随机角度：`angle = random.uniform(0, 2*pi)`
    - 计算速度：`speed = 2 + normalized_low * 6`
    - 设置速度分量：`vx = speed * cos(angle)`, `vy = speed * sin(angle)`
    - 设置大小：`size = 8 + normalized_low * 12`
    - 设置颜色：插值 (200,50,50) 到 (255,150,50)
    - 设置生命周期：`lifetime = random.randint(30, 60)`
    - 添加到 `low_freq_particles` 列表

- **中频粒子**：
  - 计算发射数量：`num = int(normalized_mid * 200)`
  - 限制上限：`num = min(num, 200)`
  - 循环 num 次：
    - 创建粒子对象
    - 随机选择轨道中心：从 5 个中心点中随机选一个
    - 设置初始角度：`angle = random.uniform(0, 2*pi)`
    - 计算轨道半径：`radius = 50 + normalized_mid * 150`
    - 计算初始位置：`x = center_x + radius * cos(angle)`, `y = center_y + radius * sin(angle)`
    - 设置角速度：`angular_speed = 0.05 + normalized_mid * 0.05`
    - 设置大小：`size = 4 + normalized_mid * 6`
    - 设置颜色：插值 (50,100,200) 到 (50,200,200)
    - 设置生命周期：`lifetime = random.randint(40, 80)`
    - 添加到 `mid_freq_particles` 列表

- **高频粒子**：
  - 计算发射数量：`num = int(normalized_high * 300)`
  - 限制上限：`num = min(num, 300)`
  - 循环 num 次：
    - 创建粒子对象
    - 设置随机初始位置：`x = random.randint(0, 1280)`, `y = random.randint(0, 720)`
    - 设置随机初始方向：`angle = random.uniform(0, 2*pi)`
    - 计算速度：`speed = 0.5 + normalized_high * 2.5`
    - 设置速度分量：`vx = speed * cos(angle)`, `vy = speed * sin(angle)`
    - 设置大小：`size = 2 + normalized_high * 3`
    - 设置颜色：插值 (255,255,200) 到 (255,255,100)
    - 设置生命周期：`lifetime = random.randint(20, 40)`
    - 添加到 `high_freq_particles` 列表

**步骤 6：更新粒子**（如果未暂停）
- **低频粒子**：
  - 遍历 `low_freq_particles` 列表
  - 对每个粒子：
    - 更新位置：`x += vx`, `y += vy`
    - 减少生命周期：`lifetime -= 1`
    - 计算衰减因子：`decay = lifetime / max_lifetime`
    - 更新 alpha：`alpha = 255 * decay`
    - 更新大小：`current_size = original_size * decay`
    - 如果 `lifetime <= 0`，标记为死亡
  - 移除死亡粒子

- **中频粒子**：
  - 遍历 `mid_freq_particles` 列表
  - 对每个粒子：
    - 更新角度：`angle += angular_speed`
    - 更新位置：`x = center_x + radius * cos(angle)`, `y = center_y + radius * sin(angle)`
    - 减少生命周期：`lifetime -= 1`
    - 计算衰减因子：`decay = lifetime / max_lifetime`
    - 更新 alpha：`alpha = 255 * decay`
    - 更新大小：`current_size = original_size * decay`
    - 如果 `lifetime <= 0`，标记为死亡
  - 移除死亡粒子

- **高频粒子**：
  - 遍历 `high_freq_particles` 列表
  - 对每个粒子：
    - 随机微调方向：`angle += random.uniform(-0.2, 0.2)`
    - 更新位置：`x += vx`, `y += vy`
    - 检查边界：如果 `x < 0 or x > 1280 or y < 0 or y > 720`，标记为死亡
    - 减少生命周期：`lifetime -= 1`
    - 计算衰减因子：`decay = lifetime / max_lifetime`
    - 更新 alpha：`alpha = 255 * decay`
    - 更新大小：`current_size = original_size * decay`
    - 如果 `lifetime <= 0` 或超出边界，标记为死亡
  - 移除死亡粒子

**步骤 7：渲染**
1. **绘制半透明背景**：
   - 创建半透明表面：`surface = pygame.Surface((1280, 720))`
   - 设置颜色：`surface.fill((10, 10, 20))`
   - 设置透明度：`surface.set_alpha(40)`
   - 绘制到屏幕：`screen.blit(surface, (0, 0))`

2. **绘制粒子**（根据显示模式）：
   - 如果 `display_mode == 'all'` 或 `display_mode == 'low'`：
     - 遍历 `low_freq_particles`
     - 对每个粒子：
       - 创建带 alpha 的表面
       - 绘制圆形：`pygame.draw.circle(surface, color, (x, y), size)`
       - 绘制到屏幕
   - 如果 `display_mode == 'all'` 或 `display_mode == 'mid'`：
     - 遍历 `mid_freq_particles`
     - 绘制方式同上
   - 如果 `display_mode == 'all'` 或 `display_mode == 'high'`：
     - 遍历 `high_freq_particles`
     - 绘制方式同上

3. **绘制信息**（可选）：
   - 当前时间 / 总时间
   - FPS
   - 当前显示模式

4. **更新显示**：
   - `pygame.display.flip()`

**步骤 8：帧率控制**
- **操作**：`clock.tick(60)`
- **效果**：限制帧率为 60 FPS

**步骤 9：检查播放结束**
- **条件**：`pygame.mixer.music.get_busy() == False`
- **处理**：退出主循环，返回文件选择

### 用户交互

#### 交互 1：暂停/继续（SPACE 键）
- **触发**：用户按下 SPACE 键
- **当前状态**：正在播放
- **操作**：
  1. 切换 `is_paused` 状态
  2. 如果 `is_paused == True`：
     - 暂停音频：`pygame.mixer.music.pause()`
     - 停止发射和更新粒子
  3. 如果 `is_paused == False`：
     - 继续音频：`pygame.mixer.music.unpause()`
     - 恢复发射和更新粒子
- **视觉反馈**：粒子停止运动（暂停时）

#### 交互 2：退出（ESC 键）
- **触发**：用户按下 ESC 键
- **操作**：
  1. 停止音频：`pygame.mixer.music.stop()`
  2. 清空粒子列表
  3. 关闭 Pygame 窗口
  4. 返回文件选择界面

#### 交互 3：切换显示模式（1/2/3/A 键）
- **触发**：用户按下 1/2/3/A 键
- **操作**：
  - **1 键**：设置 `display_mode = 'low'`
  - **2 键**：设置 `display_mode = 'mid'`
  - **3 键**：设置 `display_mode = 'high'`
  - **A 键**：设置 `display_mode = 'all'`
- **效果**：只渲染对应频段的粒子
- **视觉反馈**：屏幕上只显示选定频段的粒子

#### 交互 4：快进/快退（左右箭头，可选）
- **触发**：用户按下左箭头或右箭头
- **操作**：
  - **左箭头**：
    - 计算新位置：`new_pos = current_time_s - 5`
    - 边界检查：`new_pos = max(0, new_pos)`
    - 设置播放位置：`pygame.mixer.music.set_pos(new_pos)`
  - **右箭头**：
    - 计算新位置：`new_pos = current_time_s + 5`
    - 边界检查：`new_pos = min(total_duration, new_pos)`
    - 设置播放位置：`pygame.mixer.music.set_pos(new_pos)`
- **注意**：`pygame.mixer.music.set_pos()` 可能不支持所有格式

### 状态转换
- **进入条件**：音频加载成功
- **退出条件**：
  - 用户按 ESC 键 → 返回文件选择
  - 音频播放结束 → 返回文件选择
  - 用户关闭窗口 → 返回文件选择

---

## 完整用户旅程示例

### 场景 1：正常使用流程
1. 用户启动程序
2. 系统显示文件选择对话框
3. 用户浏览到音乐文件夹
4. 用户选择 "song.mp3" 并点击"打开"
5. 系统关闭对话框，控制台显示"正在加载音频文件..."
6. 系统加载音频（2 秒）
7. 控制台显示"正在处理音频数据..."
8. 系统计算 STFT 并提取频谱（3 秒）
9. 控制台显示"完成！"
10. 系统打开 Pygame 窗口（1280x720）
11. 音频开始播放，粒子开始出现
12. 用户观看可视化效果（3 分钟）
13. 音频播放结束
14. 系统自动关闭 Pygame 窗口
15. 系统返回文件选择对话框
16. 用户点击"取消"
17. 程序退出

### 场景 2：使用交互控制
1. 用户启动程序并选择音频文件
2. 系统加载并开始播放
3. 用户按下 "1" 键
4. 屏幕只显示低频粒子（红-橙色）
5. 用户按下 "2" 键
6. 屏幕只显示中频粒子（蓝-青色）
7. 用户按下 "3" 键
8. 屏幕只显示高频粒子（白-黄色）
9. 用户按下 "A" 键
10. 屏幕显示所有粒子
11. 用户按下 SPACE 键
12. 音频暂停，粒子停止运动
13. 用户再次按下 SPACE 键
14. 音频继续，粒子恢复运动
15. 用户按下 ESC 键
16. 系统返回文件选择对话框

### 场景 3：错误处理
1. 用户启动程序并选择音频文件
2. 系统尝试加载文件
3. 加载失败（文件损坏）
4. 控制台显示"错误：无法加载音频文件"
5. 控制台显示错误详情
6. 系统返回文件选择对话框
7. 用户可以重新选择其他文件

---

## 状态持久化

### 不需要持久化的数据
- 当前播放位置（每次重新开始）
- 粒子状态（每次重新生成）
- 显示模式（每次默认为 'all'）

### 临时存储的数据（内存中）
- 音频波形数据
- 频谱能量数组
- 粒子列表
- 播放状态

---

## 性能考虑

### 关键性能指标
- **帧率**：目标 60 FPS，最低 30 FPS
- **粒子更新时间**：< 10ms/帧
- **渲染时间**：< 6ms/帧
- **总帧时间**：< 16.67ms（60 FPS）

### 性能优化点
1. **粒子数量控制**：
   - 每帧检查总粒子数
   - 如果超过 3000，停止发射新粒子
   - 优先移除生命周期短的粒子

2. **渲染优化**：
   - 使用 Pygame 的硬件加速（如果可用）
   - 批量绘制相同颜色的粒子
   - 跳过屏幕外的粒子

3. **内存优化**：
   - 使用对象池复用粒子对象
   - 及时清理死亡粒子
   - 限制音频长度（< 10 分钟）
