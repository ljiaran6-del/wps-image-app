import sys
import os
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # 设置应用级样式
    app.setStyleSheet("""
        QMainWindow {
            background-color: #1e1e1e;
        }
        QMenuBar {
            background-color: #2d2d2d;
            color: #ffffff;
        }
        QMenuBar::item:selected {
            background-color: #3c3c3c;
        }
        QMenu {
            background-color: #2d2d2d;
            color: #ffffff;
            border: 1px solid #3c3c3c;
        }
        QMenu::item:selected {
            background-color: #00a8ff;
        }
        QToolBar {
            background-color: #2d2d2d;
            border: none;
            spacing: 4px;
        }
        QToolBar QToolButton {
            color: #ffffff;
            background-color: #3c3c3c;
            border: none;
            padding: 6px 12px;
            border-radius: 4px;
        }
        QToolBar QToolButton:hover {
            background-color: #4c4c4c;
        }
        QStatusBar {
            background-color: #007acc;
            color: white;
        }
        QLabel {
            color: #ffffff;
        }
        QMessageBox {
            background-color: #f0f0f0;
            color: #000000;
        }
        QMessageBox QLabel {
            color: #000000;
        }
        QMessageBox QPushButton {
            background-color: #e0e0e0;
            color: #000000;
            border: 1px solid #aaaaaa;
            padding: 4px 12px;
        }
        QInputDialog {
            background-color: #f0f0f0;
            color: #000000;
        }
        QInputDialog QLabel {
            color: #000000;
        }
        QInputDialog QLineEdit {
            background-color: #ffffff;
            color: #000000;
            border: 1px solid #cccccc;
            padding: 4px;
        }
        QPushButton {
            background-color: #4a4a4a;
            color: white;
            border: 1px solid #666666;
            padding: 6px 12px;
            border-radius: 4px;
        }
        QPushButton:hover {
            background-color: #5a5a5a;
            border: 1px solid #777777;
        }
        QPushButton:checked {
            background-color: #00a8ff;
            border: 1px solid #00a8ff;
        }
        QComboBox {
            background-color: #3c3c3c;
            color: white;
            border: 1px solid #555555;
            padding: 4px 8px;
            border-radius: 4px;
            min-width: 80px;
        }
        QComboBox::drop-down {
            border: none;
            width: 20px;
        }
        QComboBox::down-arrow {
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 6px solid white;
            width: 0px;
            height: 0px;
        }
        QComboBox QAbstractItemView {
            background-color: #3c3c3c;
            color: white;
            selection-background-color: #00a8ff;
            selection-color: white;
            border: 1px solid #555555;
        }
        QSpinBox {
            background-color: #3c3c3c;
            color: white;
            border: 1px solid #555555;
            padding: 4px;
            border-radius: 4px;
        }
        QSpinBox::up-button, QSpinBox::down-button {
            background-color: #4a4a4a;
            border: 1px solid #555555;
            width: 16px;
        }
        QSpinBox::up-button:hover, QSpinBox::down-button:hover {
            background-color: #5a5a5a;
        }
        QSpinBox::up-arrow {
            image: none;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-bottom: 5px solid white;
        }
        QSpinBox::down-arrow {
            image: none;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 5px solid white;
        }
        QSlider::groove:horizontal {
            height: 4px;
            background: #3c3c3c;
        }
        QSlider::handle:horizontal {
            background: #00a8ff;
            width: 12px;
            margin: -4px 0;
            border-radius: 6px;
        }
        QTextEdit {
            background-color: #3c3c3c;
            color: white;
            border: 1px solid #555555;
            border-radius: 4px;
        }
    """)

    window = MainWindow()
    window.show()

    # 如果命令行传入图片路径，自动打开
    if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
        window._load_image(sys.argv[1])

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
