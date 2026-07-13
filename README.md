# WPS图片复刻版

一个轻量级 Windows 桌面图片处理工具，复刻 WPS图片 的核心体验。

> 支持 AI 消除、去水印、局部改图、扩图，以及常用标注工具。

---

## 功能特性

### AI 功能

| 功能 | 说明 |
|------|------|
| **AI消除** | 涂抹或框选区域，自动消除并修复背景 |
| **AI去水印** | 框选水印区域，自动去除 |
| **AI局部改图** | 框选区域 + 输入提示词，按描述修改 |
| **AI扩图** | 选择目标比例或自定义尺寸，向外扩展图片 |

### 标注工具

- 画笔、箭头、矩形、圆形、文字
- 马赛克、高斯模糊
- 标注层可单独删除、清空
- 保存时自动合并标注层

### 基础功能

- 图片查看：打开、缩放、拖动、适应窗口、实际大小
- 文件夹浏览：上一张、下一张
- 保存/另存为：支持 PNG/JPG/WEBP/BMP
- 撤销/重做（默认 50 步）
- 深色主题 UI

---

## 截图

> TODO: 添加应用截图

<!-- 
![主界面](docs/screenshots/main.png)
![AI消除](docs/screenshots/ai-erase.png)
-->

---

## 快速开始

### 环境要求

- Windows 10 / Windows 11
- Python 3.11 或更高版本
- OpenAI API Key（或第三方代理）

### 安装步骤

```bash
# 1. 克隆仓库
git clone https://github.com/yourusername/wps-image-app.git
cd wps-image-app

# 2. 创建虚拟环境
python -m venv venv

# 3. 安装依赖
.\venv\Scripts\pip install -r requirements.txt

# 4. 配置 API Key
# 编辑 config.json，填写 openai_base_url 和 openai_api_key

# 5. 启动
.\venv\Scripts\python src\main.py
```

或者双击 `start.bat` 启动。

---

## 配置说明

首次启动前，编辑项目根目录的 `config.json`：

```json
{
  "openai_api_key": "sk-your-api-key",
  "openai_base_url": "https://api.openai.com/v1",
  "openai_model": "gpt-image-2"
}
```

也可以使用菜单 `设置 -> API Key 设置` 在应用内配置。

---

## 使用说明

1. 点击菜单 `文件 -> 打开` 选择图片
2. 点击左侧工具栏切换工具
3. AI 工具需要先选择区域，再点击右侧"开始"按钮
4. 标注工具在右侧面板可调整颜色、粗细、透明度等
5. 滚轮缩放，鼠标中键拖动图片

详细安装说明见 [安装说明.txt](./安装说明.txt)。

---

## 技术栈

- [Python 3.11+](https://www.python.org/)
- [PySide6](https://doc.qt.io/qtforpython-6/) - 桌面 GUI
- [Pillow](https://python-pillow.org/) - 图像处理
- [OpenAI Python SDK](https://github.com/openai/openai-python) - AI 图像编辑 API
- [NumPy](https://numpy.org/) - 数值计算

---

## 项目结构

```text
wps-image-app/
├── src/
│   ├── main.py                  # 程序入口
│   ├── config.py                # 配置管理
│   ├── core/
│   │   ├── image_viewer.py      # 图片显示、缩放、拖动
│   │   ├── file_manager.py      # 文件打开、保存、文件夹遍历
│   │   └── annotation_layer.py  # 标注元素管理
│   ├── tools/
│   │   ├── base_tool.py         # 工具基类
│   │   ├── ai_erase_tool.py     # AI消除
│   │   ├── ai_watermark_tool.py # AI去水印
│   │   ├── ai_edit_tool.py      # AI局部改图
│   │   ├── ai_outpaint_tool.py  # AI扩图
│   │   ├── annotation_tool.py   # 标注工具
│   │   └── selection_tool.py    # 选区/蒙版绘制
│   ├── services/
│   │   └── ai_service.py        # OpenAI API 封装
│   └── ui/
│       ├── main_window.py       # 主窗口
│       └── dialogs.py           # 设置对话框
├── requirements.txt
├── config.json
├── start.bat
├── LICENSE
└── README.md
```

---

## 核心设计亮点

### 1. Mask 后处理融合

`gpt-image-2` 做图像编辑时，修改容易溢出到 mask 外。本项目通过后处理，将 AI 结果与原图按 mask 融合：

- mask 内 = AI 编辑结果
- mask 外 = 原图像素（100% 不变）
- 边缘羽化过渡，避免接缝

### 2. 统一的工具系统

所有工具继承 `BaseTool`，负责自己的鼠标事件、属性面板和叠加层绘制。主窗口只负责切换和容器管理。

### 3. Image-Widget 坐标转换

`ImageViewer` 封装了完整的图片坐标与窗口坐标转换，支撑缩放、拖动、选区、标注等功能。

---

## 已知限制

1. AI 功能需要联网和有效的 OpenAI API Key
2. `gpt-image-2` 仅支持 `1024x1024`、`1536x1024`、`1024x1536` 三种输出尺寸，非标准尺寸会自动缩放
3. 马赛克和模糊标注在画布上是简化预览，保存时会正确合并
4. 打包体积较大（PyInstaller 打包后约 100MB+），主要因为包含 Qt 和 Python 运行时

---

## 后续计划

- [ ] LaMa 本地模型集成（更精准的消除）
- [ ] 深色/浅色主题切换
- [ ] 更多快捷键支持
- [ ] 批量处理
- [ ] 插件化 AI Provider

---

## 贡献

欢迎提交 Issue 和 Pull Request。

如果你发现 bug，请尽量提供：
- 操作系统版本
- Python 版本
- 复现步骤
- 报错信息

---

## 许可证

[MIT License](./LICENSE)
