# 龙门式喷涂机器人模拟系统 / Gantry Spray Robot Simulation

基于 Dash + Three.js 的三轴龙门式喷涂机器人运动模拟系统。

A 3-axis gantry spray robot motion simulation system built with Dash + Three.js.

---

## 功能 / Features

- **3D 实时场景** - Three.js 渲染龙门架模型、喷涂粒子、轨迹线
- **运动控制** - X/Y/Z 三轴滑块 + 方向按钮，支持摆动关节
- **路径模板** - 矩形、直线、圆形、Z 字形、轮廓跟随
- **手动绘制轨迹** - Canvas 绘图 + RDP 简化 + 直线拉直
- **自动喷涂动画** - 分段运动执行，requestAnimationFrame 驱动
- **喷涂效果模拟** - 2D 桌面 Canvas 实时喷漆纹理
- **轨迹可视化** - 红线（喷枪轨迹）、绿线（喷涂效果）、紫线（桌面 Y 轴）

---

## 运行 / Getting Started

```bash
# 安装依赖 / Install dependencies
pip install -r requirements.txt

# 启动 / Run
python app.py
```

浏览器打开 http://127.0.0.1:8050

---

## 文件结构 / Project Structure

```
spray_robot_sim/
├── app.py              # 主入口，UI 布局
├── callbacks.py        # Dash 回调逻辑（运动控制、喷涂、路径规划、动画）
├── path_planner.py     # 路径规划器（矩形/直线/圆形/Z 字形/轮廓）
├── kinematics.py       # 机器人运动学模型（3 轴龙门式）
├── state_manager.py    # 全局状态管理
├── spray_sim.py        # 喷涂效果模拟器（厚度图、热力图）
├── requirements.txt    # Python 依赖
└── assets/
    ├── 01_three.min.js # Three.js 库
    ├── 02_scene.js     # 3D 场景（龙门架、轨迹线、粒子）
    └── 03_style.css    # 暗色主题样式
```

---

## 技术栈 / Tech Stack

| 层 | 技术 |
|---|---|
| 后端 | Python, Dash 2.17, Flask |
| 前端 | Three.js, Dash Bootstrap Components |
| 喷涂模拟 | NumPy, Pillow |
| 主题 | Dash Bootstrap CYBORG (暗色) |

---

## 已知问题 / Known Issues

- **圆形路径规划** - 喷涂轨迹与绿线存在偏移，路径起点对齐有 bug
- **Z 字形路径规划** - 喷漆实际效果与绿线规划不完全一致
- **喷涂模拟** - 红色喷漆印记与绿色参考线在动画过程中存在位置偏差

> 上述问题正在修复中，欢迎提 Issue 讨论。
>
> The above issues are being worked on. Feel free to open an Issue to discuss.

---

## 许可证 / License

MIT
