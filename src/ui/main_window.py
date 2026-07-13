import sys
from pathlib import Path
from PIL import Image

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QToolBar, QStatusBar, QFileDialog, QMessageBox,
    QPushButton, QLabel, QProgressDialog,
    QApplication, QScrollArea, QSizePolicy, QDialog
)
from PySide6.QtCore import Qt, QThread, Signal, QSize, QPoint
from PySide6.QtGui import QAction, QKeySequence, QIcon
from PySide6.QtWidgets import QLineEdit

from config import Config
from core.file_manager import FileManager
from core.image_viewer import ImageViewer
from services.ai_service import AIService
from tools.base_tool import BaseTool
from ui.dialogs import APISettingsDialog
from tools.ai_erase_tool import AIEraseTool
from tools.ai_edit_tool import AIEditTool
from tools.ai_watermark_tool import AIWatermarkTool
from tools.ai_outpaint_tool import AIOutpaintTool
from tools.annotation_tool import AnnotationTool


class AIWorker(QThread):
    """AI 处理后台线程"""
    finished = Signal(object)
    error = Signal(str)

    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            result = self.func(*self.args, **self.kwargs)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class HistoryManager:
    """简单的图片状态历史管理"""

    def __init__(self, max_steps: int = 50):
        self.max_steps = max_steps
        self._history = []
        self._index = -1

    def push(self, image: Image.Image):
        """添加一个历史状态"""
        # 删除当前位置之后的历史
        self._history = self._history[:self._index + 1]
        self._history.append(image.copy())
        if len(self._history) > self.max_steps:
            self._history.pop(0)
        else:
            self._index += 1

    def undo(self) -> Image.Image | None:
        if self._index > 0:
            self._index -= 1
            return self._history[self._index].copy()
        return None

    def redo(self) -> Image.Image | None:
        if self._index < len(self._history) - 1:
            self._index += 1
            return self._history[self._index].copy()
        return None

    def can_undo(self) -> bool:
        return self._index > 0

    def can_redo(self) -> bool:
        return self._index < len(self._history) - 1

    def clear(self):
        self._history = []
        self._index = -1


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = Config()
        self.file_manager = FileManager()
        self.ai_service = AIService(
            self.config.openai_api_key,
            self.config.openai_base_url,
            self.config.openai_model
        )
        self.history = HistoryManager(self.config.history_max_steps)
        self.current_tool: BaseTool | None = None
        self.tools = {}
        self.worker: AIWorker | None = None

        self.setWindowTitle("WPS图片复刻版")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)

        self._build_ui()
        self._build_menu()
        self._build_toolbar()
        self._build_tools()
        self._connect_signals()
        self._update_ui_state()

    def _build_ui(self):
        """构建主界面"""
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 左侧工具箱
        self.tool_panel = QWidget()
        self.tool_panel.setFixedWidth(90)
        self.tool_panel.setStyleSheet("background-color: #1e1e1e;")
        self.tool_layout = QVBoxLayout(self.tool_panel)
        self.tool_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.tool_layout.setSpacing(4)
        self.tool_layout.setContentsMargins(4, 8, 4, 8)
        main_layout.addWidget(self.tool_panel)

        # 中间区域
        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(0)

        # 图片查看器
        self.viewer = ImageViewer()
        center_layout.addWidget(self.viewer)
        main_layout.addWidget(center_widget, 1)

        # 右侧属性面板
        self.property_panel = QWidget()
        self.property_panel.setFixedWidth(250)
        self.property_panel.setStyleSheet("background-color: #252526;")
        self.property_layout = QVBoxLayout(self.property_panel)
        self.property_layout.setContentsMargins(8, 8, 8, 8)
        self.property_placeholder = QLabel("选择一个工具以查看属性")
        self.property_placeholder.setStyleSheet("color: #888888;")
        self.property_layout.addWidget(self.property_placeholder)
        self.property_layout.addStretch()
        main_layout.addWidget(self.property_panel)

        # 状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_label = QLabel("就绪")
        self.status_bar.addWidget(self.status_label)

    def _build_menu(self):
        """构建菜单栏"""
        menubar = self.menuBar()

        # 文件菜单
        file_menu = menubar.addMenu("文件")

        open_action = QAction("打开", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self.on_open)
        file_menu.addAction(open_action)

        save_action = QAction("保存", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self.on_save)
        file_menu.addAction(save_action)

        save_as_action = QAction("另存为...", self)
        save_as_action.setShortcut(QKeySequence("Ctrl+Shift+S"))
        save_as_action.triggered.connect(self.on_save_as)
        file_menu.addAction(save_as_action)

        file_menu.addSeparator()

        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 视图菜单
        view_menu = menubar.addMenu("视图")

        fit_action = QAction("适应窗口", self)
        fit_action.triggered.connect(self.viewer.fit_to_window)
        view_menu.addAction(fit_action)

        actual_action = QAction("实际大小", self)
        actual_action.triggered.connect(self.viewer.actual_size)
        view_menu.addAction(actual_action)

        zoom_in_action = QAction("放大", self)
        zoom_in_action.setShortcut(QKeySequence("Ctrl++"))
        zoom_in_action.triggered.connect(self.viewer.zoom_in)
        view_menu.addAction(zoom_in_action)

        zoom_out_action = QAction("缩小", self)
        zoom_out_action.setShortcut(QKeySequence("Ctrl+-"))
        zoom_out_action.triggered.connect(self.viewer.zoom_out)
        view_menu.addAction(zoom_out_action)

        # 上一个/下一个
        nav_menu = menubar.addMenu("导航")

        prev_action = QAction("上一张", self)
        prev_action.setShortcut(QKeySequence("Left"))
        prev_action.triggered.connect(self.on_prev_image)
        nav_menu.addAction(prev_action)

        next_action = QAction("下一张", self)
        next_action.setShortcut(QKeySequence("Right"))
        next_action.triggered.connect(self.on_next_image)
        nav_menu.addAction(next_action)

        # 编辑菜单
        edit_menu = menubar.addMenu("编辑")

        undo_action = QAction("撤销", self)
        undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        undo_action.triggered.connect(self.on_undo)
        edit_menu.addAction(undo_action)

        redo_action = QAction("重做", self)
        redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        redo_action.triggered.connect(self.on_redo)
        edit_menu.addAction(redo_action)

        # 设置
        settings_menu = menubar.addMenu("设置")
        api_action = QAction("API Key 设置", self)
        api_action.triggered.connect(self.on_api_settings)
        settings_menu.addAction(api_action)

    def _build_toolbar(self):
        """构建顶部工具栏"""
        toolbar = QToolBar()
        self.addToolBar(toolbar)

        toolbar.addAction("打开", self.on_open)
        toolbar.addAction("保存", self.on_save)
        toolbar.addSeparator()
        toolbar.addAction("撤销", self.on_undo)
        toolbar.addAction("重做", self.on_redo)
        toolbar.addSeparator()
        toolbar.addAction("适应窗口", self.viewer.fit_to_window)
        toolbar.addAction("实际大小", self.viewer.actual_size)
        toolbar.addSeparator()
        toolbar.addAction("上一张", self.on_prev_image)
        toolbar.addAction("下一张", self.on_next_image)

    def _build_tools(self):
        """构建左侧工具箱按钮"""
        tools_config = [
            ("浏览", "pan", self._activate_pan_tool),
            ("AI消除", "ai_erase", self._activate_ai_erase),
            ("AI改图", "ai_edit", self._activate_ai_edit),
            ("去水印", "ai_watermark", self._activate_ai_watermark),
            ("AI扩图", "ai_outpaint", self._activate_ai_outpaint),
            ("标注", "annotation", self._activate_annotation),
        ]

        for label, name, callback in tools_config:
            btn = QPushButton(label)
            btn.setFixedSize(78, 52)
            btn.setCheckable(True)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #3c3c3c;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    font-size: 11px;
                    padding: 2px;
                }
                QPushButton:checked {
                    background-color: #00a8ff;
                }
                QPushButton:hover {
                    background-color: #4c4c4c;
                }
            """)
            btn.clicked.connect(callback)
            self.tool_layout.addWidget(btn)
            self.tools[name] = btn

        self.tool_layout.addStretch()

        # 默认激活浏览工具
        self._activate_pan_tool()

    def _connect_signals(self):
        """连接信号"""
        self.viewer.scale_changed.connect(self._on_scale_changed)
        self.viewer.mouse_moved.connect(self._on_mouse_moved)
        self.viewer.image_loaded.connect(self._on_image_loaded)

    def _update_ui_state(self):
        """更新 UI 状态"""
        has_image = self.viewer.get_image() is not None
        self.status_label.setText(
            f"缩放: {self.viewer.get_scale() * 100:.0f}%" if not has_image else
            self._get_status_text()
        )

    def _get_status_text(self) -> str:
        info = self.file_manager.get_file_info()
        if not info:
            return f"缩放: {self.viewer.get_scale() * 100:.0f}%"
        return f"{info.get('name', '')} | {info.get('width', 0)}x{info.get('height', 0)} | 缩放: {self.viewer.get_scale() * 100:.0f}%"

    def _on_scale_changed(self, scale: float):
        self.status_label.setText(self._get_status_text())

    def _on_mouse_moved(self, pos: QPoint):
        img_pos = self.viewer.widget_to_image_pos(pos)
        if img_pos.x() >= 0:
            self.status_label.setText(f"{self._get_status_text()} | 坐标: ({img_pos.x()}, {img_pos.y()})")
        else:
            self.status_label.setText(self._get_status_text())

    def _on_image_loaded(self):
        self._update_ui_state()

    # ===== 工具激活 =====

    def _uncheck_all_tools(self):
        for btn in self.tools.values():
            btn.setChecked(False)

    def _set_tool(self, tool: BaseTool):
        if self.current_tool:
            self.current_tool.deactivate()

        self.current_tool = tool
        self.current_tool.activate()
        self.viewer.set_tool(tool)

        # 更新右侧面板
        # 清除旧内容
        while self.property_layout.count():
            item = self.property_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        prop_widget = self.current_tool.get_property_widget()
        if prop_widget:
            self.property_layout.addWidget(prop_widget)
        else:
            self.property_layout.addWidget(QLabel("无属性"))

        self.property_layout.addStretch()
        self.viewer.update()

    def _activate_pan_tool(self):
        self._uncheck_all_tools()
        self.tools["pan"].setChecked(True)
        # 浏览工具不需要特殊工具类，直接清空当前工具
        self.current_tool = None
        self.viewer.set_tool(None)
        while self.property_layout.count():
            item = self.property_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.property_layout.addWidget(QLabel("浏览模式\n滚轮缩放，中键拖动"))
        self.property_layout.addStretch()
        self.viewer.setCursor(Qt.CursorShape.ArrowCursor)

    def _activate_ai_erase(self):
        self._uncheck_all_tools()
        self.tools["ai_erase"].setChecked(True)
        tool = AIEraseTool(self.viewer)
        tool.set_process_callback(self._on_ai_erase_process)
        self._set_tool(tool)

    def _activate_ai_edit(self):
        self._uncheck_all_tools()
        self.tools["ai_edit"].setChecked(True)
        tool = AIEditTool(self.viewer)
        tool.set_process_callback(self._on_ai_edit_process)
        self._set_tool(tool)

    def _activate_ai_watermark(self):
        self._uncheck_all_tools()
        self.tools["ai_watermark"].setChecked(True)
        tool = AIWatermarkTool(self.viewer)
        tool.set_process_callback(self._on_ai_watermark_process)
        self._set_tool(tool)

    def _activate_ai_outpaint(self):
        self._uncheck_all_tools()
        self.tools["ai_outpaint"].setChecked(True)
        tool = AIOutpaintTool(self.viewer)
        tool.set_process_callback(self._on_ai_outpaint_process)
        self._set_tool(tool)

    def _activate_annotation(self):
        self._uncheck_all_tools()
        self.tools["annotation"].setChecked(True)
        tool = AnnotationTool(self.viewer)
        self.annotation_tool = tool
        self._set_tool(tool)

    # ===== AI 处理 =====

    def _on_ai_erase_process(self, tool: AIEraseTool):
        self._run_ai_process(tool, "erase")

    def _on_ai_edit_process(self, tool: AIEditTool):
        prompt = tool.get_prompt()
        if not prompt:
            QMessageBox.warning(self, "提示", "请输入提示词")
            return
        self._run_ai_process(tool, "edit", prompt=prompt)

    def _on_ai_watermark_process(self, tool: AIWatermarkTool):
        self._run_ai_process(tool, "watermark")

    def _on_ai_outpaint_process(self, tool: AIOutpaintTool):
        target_size = tool.get_target_size()
        anchor = tool.get_anchor()
        if target_size is None:
            QMessageBox.warning(self, "提示", "无法计算目标尺寸")
            return

        if not self.ai_service.api_key:
            QMessageBox.warning(self, "未设置 API Key", "请先在 设置 -> API Key 设置 中填写 OpenAI API Key")
            return

        image = self.viewer.get_image()
        if image is None:
            return

        if target_size[0] < image.width or target_size[1] < image.height:
            QMessageBox.warning(self, "提示", "扩图目标尺寸必须大于原图")
            return

        self.progress = QProgressDialog("AI 扩图中，请稍候...", "取消", 0, 0, self)
        self.progress.setWindowTitle("处理中")
        self.progress.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.progress.show()

        self.worker = AIWorker(self.ai_service.outpaint, image, target_size, anchor)
        self.worker.finished.connect(self._on_ai_finished)
        self.worker.error.connect(self._on_ai_error)
        self.worker.start()

    def _run_ai_process(self, tool, mode: str, **kwargs):
        if not self.ai_service.api_key:
            QMessageBox.warning(self, "未设置 API Key", "请先在 设置 -> API Key 设置 中填写 OpenAI API Key")
            return

        image = self.viewer.get_image()
        if image is None:
            return

        mask = tool.get_mask()
        if mask is None:
            QMessageBox.warning(self, "提示", "请先选择要处理的区域")
            return

        # 检查 mask 是否有选中区域
        if not any(p > 0 for p in mask.getdata()):
            QMessageBox.warning(self, "提示", "请先选择要处理的区域")
            return

        # 显示进度对话框
        self.progress = QProgressDialog("AI 处理中，请稍候...", "取消", 0, 0, self)
        self.progress.setWindowTitle("处理中")
        self.progress.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.progress.show()

        # 在后台线程执行 AI 调用
        if mode == "erase":
            self.worker = AIWorker(self.ai_service.erase, image, mask)
        elif mode == "edit":
            self.worker = AIWorker(self.ai_service.edit_region, image, mask, kwargs.get("prompt", ""))
        elif mode == "watermark":
            self.worker = AIWorker(self.ai_service.remove_watermark, image, mask)
        else:
            self.progress.close()
            return

        self.worker.finished.connect(self._on_ai_finished)
        self.worker.error.connect(self._on_ai_error)
        self.worker.start()

    def _on_ai_finished(self, result_image: Image.Image):
        self.progress.close()
        if result_image:
            self._push_history()
            self.viewer.update_image(result_image)
            self.status_label.setText("AI 处理完成")

    def _on_ai_error(self, error_msg: str):
        self.progress.close()
        QMessageBox.critical(self, "AI 处理失败", error_msg)

    # ===== 文件操作 =====

    def on_open(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "打开图片",
            "",
            "图片文件 (*.png *.jpg *.jpeg *.webp *.bmp *.gif)"
        )
        if path:
            self._load_image(path)

    def _load_image(self, path: str):
        try:
            image = self.file_manager.open(path)
            self.viewer.set_image(image)
            self.history.clear()
            self.history.push(image)
            # 清除标注
            if hasattr(self, "annotation_tool") and self.annotation_tool:
                self.annotation_tool.layer.clear()
            self._update_ui_state()
        except Exception as e:
            QMessageBox.critical(self, "打开失败", str(e))

    def _get_image_with_annotations(self) -> Image.Image:
        """获取合并标注后的图片"""
        image = self.viewer.get_image()
        if image is None:
            return None
        if hasattr(self, "annotation_tool") and self.annotation_tool:
            return self.annotation_tool.layer.merge_to_image(image)
        return image

    def on_save(self):
        image = self._get_image_with_annotations()
        if image is None:
            return
        try:
            path = self.file_manager.save(image)
            self.status_label.setText(f"已保存: {path}")
        except Exception as e:
            QMessageBox.critical(self, "保存失败", str(e))

    def on_save_as(self):
        image = self._get_image_with_annotations()
        if image is None:
            return

        default_path = ""
        if self.file_manager.current_path:
            default_path = str(self.file_manager.current_path.with_suffix(f".{self.config.default_save_format}"))

        path, _ = QFileDialog.getSaveFileName(
            self,
            "另存为",
            default_path,
            "PNG 图片 (*.png);;JPEG 图片 (*.jpg *.jpeg);;WebP 图片 (*.webp);;BMP 图片 (*.bmp)"
        )
        if path:
            try:
                # 根据过滤器推断格式
                ext = Path(path).suffix.lower()
                format_map = {".png": "PNG", ".jpg": "JPEG", ".jpeg": "JPEG", ".webp": "WEBP", ".bmp": "BMP"}
                fmt = format_map.get(ext, self.config.default_save_format.upper())
                saved_path = self.file_manager.save(image, path, fmt)
                self.status_label.setText(f"已保存: {saved_path}")
            except Exception as e:
                QMessageBox.critical(self, "保存失败", str(e))

    def on_prev_image(self):
        try:
            image = self.file_manager.prev_image()
            if image:
                self.viewer.set_image(image)
                self.history.clear()
                self.history.push(image)
        except Exception as e:
            QMessageBox.critical(self, "导航失败", str(e))

    def on_next_image(self):
        try:
            image = self.file_manager.next_image()
            if image:
                self.viewer.set_image(image)
                self.history.clear()
                self.history.push(image)
        except Exception as e:
            QMessageBox.critical(self, "导航失败", str(e))

    # ===== 撤销/重做 =====

    def _push_history(self):
        image = self.viewer.get_image()
        if image:
            self.history.push(image)

    def on_undo(self):
        image = self.history.undo()
        if image:
            self.viewer.update_image(image)

    def on_redo(self):
        image = self.history.redo()
        if image:
            self.viewer.update_image(image)

    # ===== 设置 =====

    def on_api_settings(self):
        dialog = APISettingsDialog(
            self,
            api_key=self.config.openai_api_key,
            base_url=self.config.openai_base_url,
            model=self.config.openai_model
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            values = dialog.get_values()
            self.config.openai_api_key = values["api_key"]
            self.config.openai_base_url = values["base_url"]
            self.config.openai_model = values["model"]
            self.ai_service.set_config(
                api_key=values["api_key"],
                base_url=values["base_url"],
                model=values["model"]
            )
            QMessageBox.information(self, "设置成功",
                f"API 配置已保存\nMODEL: {values['model']}\nBASE_URL: {values['base_url'] or '默认'}")

    # ===== 事件转发给当前工具 =====

    def eventFilter(self, obj, event):
        return super().eventFilter(obj, event)


# 重载 viewer 的事件处理，将事件转发给当前工具
# 这里我们直接在 ImageViewer 中处理，但为了不破坏 viewer 的独立性，
# 我们在 MainWindow 中为 viewer 安装事件过滤器
# 实际上更简单的方式是修改 ImageViewer 暴露工具回调
