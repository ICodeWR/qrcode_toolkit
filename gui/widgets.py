#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUI组件模块 - QR Toolkit的自定义GUI组件

模块名称：widgets.py
功能描述：提供QR Toolkit专用的自定义GUI组件
作者：码上工坊
联系：微信公众号（码上工坊）
版权声明：Copyright (c) 2026 码上工坊
开源协议：MIT License
免责声明：本软件按"原样"提供，不作任何明示或暗示的担保
修改记录：
版本 0.9.0 2026-02-10 - 码上工坊 - 初始版本创建
"""

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPixmap
from PySide6.QtPrintSupport import QPrintDialog, QPrinter
from PySide6.QtWidgets import (
    QColorDialog,
    QGraphicsScene,
    QGraphicsView,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class ColorPickerButton(QPushButton):
    """颜色选择按钮"""

    color_changed = Signal(str)  # 颜色改变信号

    def __init__(
        self, default_color: str = "#000000", parent: Optional[QWidget] = None
    ) -> None:
        """
        初始化颜色选择按钮

        Args:
            default_color: 默认颜色（十六进制格式）
            parent: 父部件
        """
        super().__init__(parent)
        self.color = QColor(default_color)
        self.setFixedSize(60, 30)
        self.clicked.connect(self.pick_color)
        self.update_color()

    def pick_color(self) -> None:
        """打开颜色选择对话框"""

        # 创建颜色对话框
        dialog = QColorDialog(self.color, self)

        # 设置样式表
        dialog.setStyleSheet(
            """
            /* ---------- 1. 对话框按钮箱中的所有按钮（OK/Cancel）---------- */
            QColorDialog QDialogButtonBox QPushButton {
                background-color: #2a82da !important;  /* 固定蓝色背景 */
                color: white !important;                /* 固定白色文字 */
                border: none !important;
                border-radius: 3px !important;
                padding: 6px 18px !important;
                font-weight: bold !important;
                min-width: 80px !important;
            }
            QColorDialog QDialogButtonBox QPushButton:hover {
                background-color: #1a6ab0 !important;  /* 悬停深蓝色 */
            }
            QColorDialog QDialogButtonBox QPushButton:pressed {
                background-color: #0a4a8a !important;  /* 按下更深的蓝色 */
            }
            
            /* ---------- 2. 专门针对 Cancel 按钮（区分颜色）---------- */
            QColorDialog QDialogButtonBox QPushButton[text="Cancel"],
            QColorDialog QDialogButtonBox QPushButton[text="取消"],
            QColorDialog QDialogButtonBox QPushButton[text="&Cancel"],
            QColorDialog QDialogButtonBox QPushButton[text="&取消"] {
                background-color: #6c757d !important;  /* 固定灰色背景 */
            }
            QColorDialog QDialogButtonBox QPushButton[text="Cancel"]:hover,
            QColorDialog QDialogButtonBox QPushButton[text="取消"]:hover,
            QColorDialog QDialogButtonBox QPushButton[text="&Cancel"]:hover,
            QColorDialog QDialogButtonBox QPushButton[text="&取消"]:hover {
                background-color: #5a6268 !important;  /* 悬停深灰色 */
            }
            
            /* ---------- 3. Pick Screen Color 按钮（吸管图标）---------- */
            QColorDialog QPushButton#pickScreenColorButton,
            QColorDialog QPushButton[text="Pick Screen Color"],
            QColorDialog QPushButton[text="屏幕取色"],
            QColorDialog QPushButton[text="&Pick Screen Color"],
            QColorDialog QPushButton[objectName*="pick"],
            QColorDialog QPushButton[objectName*="Pick"] {
                background-color: #495057 !important;  /* 固定深灰色 */
                color: white !important;
                border: 1px solid #666666 !important;
                border-radius: 3px !important;
                padding: 4px 12px !important;
            }
            QColorDialog QPushButton#pickScreenColorButton:hover,
            QColorDialog QPushButton[text="Pick Screen Color"]:hover,
            QColorDialog QPushButton[text="屏幕取色"]:hover {
                background-color: #343a40 !important;  /* 悬停更深的灰色 */
            }
            
            /* ---------- 4. Add Custom Colors 按钮 ---------- */
            QColorDialog QPushButton#addCustomColorButton,
            QColorDialog QPushButton[text="Add to Custom Colors"],
            QColorDialog QPushButton[text="添加到自定义颜色"],
            QColorDialog QPushButton[text="&Add to Custom Colors"],
            QColorDialog QPushButton[objectName*="add"],
            QColorDialog QPushButton[objectName*="Add"] {
                background-color: #495057 !important;
                color: white !important;
                border: 1px solid #666666 !important;
                border-radius: 3px !important;
                padding: 4px 12px !important;
            }
            QColorDialog QPushButton#addCustomColorButton:hover,
            QColorDialog QPushButton[text="Add to Custom Colors"]:hover,
            QColorDialog QPushButton[text="添加到自定义颜色"]:hover {
                background-color: #343a40 !important;
            }
            
            /* ---------- 5. 其他所有未匹配到的按钮（兜底策略）---------- */
            QColorDialog QPushButton {
                background-color: #6c757d !important;  /* 默认灰色 */
                color: white !important;
                border: 1px solid #666666 !important;
                border-radius: 3px !important;
                padding: 4px 12px !important;
            }
            QColorDialog QPushButton:hover {
                background-color: #5a6268 !important;
            }
            QColorDialog QPushButton:pressed {
                background-color: #484e53 !important;
            }
            QColorDialog QPushButton:disabled {
                background-color: #cccccc !important;
                color: #666666 !important;
            }
            
            /* ---------- 6. 确保对话框其他元素不受影响 ---------- */
            QColorDialog QLabel {
                color: #333333;
            }
            QColorDialog QSpinBox,
            QColorDialog QLineEdit {
                background-color: white;
                color: #333333;
                border: 1px solid #cccccc;
                border-radius: 2px;
                padding: 2px;
            }
        """
        )

        # 显示对话框
        if dialog.exec() == QColorDialog.DialogCode.Accepted:
            self.color = dialog.currentColor()
            self.update_color()
            self.color_changed.emit(self.color.name())

    def update_color(self) -> None:
        """更新按钮颜色显示"""
        self.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {self.color.name()};
                border: 2px solid #cccccc;
                border-radius: 5px;
                padding: 0px;
            }}
            QPushButton:hover {{
                border: 2px solid #666666;
            }}
            QPushButton:pressed {{
                border: 2px solid #333333;
            }}
        """
        )

    def set_color(self, color_name: str) -> None:
        """
        设置颜色

        Args:
            color_name: 颜色名称（十六进制格式）
        """
        # 使用QColor构造函数并检查有效性，避免使用已弃用的isValidColor
        color = QColor(color_name)
        if color.isValid():
            self.color = color
            self.update_color()

    def get_color(self) -> str:
        """
        获取当前颜色

        Returns:
            str: 颜色十六进制字符串
        """
        return self.color.name()


class QRPreviewWidget(QWidget):
    """二维码预览部件"""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        初始化二维码预览部件

        Args:
            parent: 父部件
        """
        super().__init__(parent)
        self.current_qr_image: Optional[QPixmap] = None
        self.current_qr_data = None
        self.zoom_level: float = 1.0
        self.init_ui()

    def init_ui(self) -> None:
        """初始化用户界面"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        # 工具栏
        toolbar_layout = QHBoxLayout()

        # 缩放按钮
        self.zoom_in_btn = QPushButton("+")
        self.zoom_out_btn = QPushButton("-")
        self.zoom_reset_btn = QPushButton("1:1")
        self.zoom_fit_btn = QPushButton("适应")

        # 设置按钮大小
        for btn in [
            self.zoom_in_btn,
            self.zoom_out_btn,
            self.zoom_reset_btn,
            self.zoom_fit_btn,
        ]:
            btn.setFixedSize(40, 30)

        # 操作按钮
        self.save_btn = QPushButton("保存")
        self.copy_btn = QPushButton("复制")
        self.print_btn = QPushButton("打印")

        # 连接信号
        self.zoom_in_btn.clicked.connect(self.zoom_in)
        self.zoom_out_btn.clicked.connect(self.zoom_out)
        self.zoom_reset_btn.clicked.connect(self.zoom_reset)
        self.zoom_fit_btn.clicked.connect(self.zoom_fit)
        self.save_btn.clicked.connect(self.save_image)
        self.copy_btn.clicked.connect(self.copy_image)
        self.print_btn.clicked.connect(self.print_image)

        # 添加到工具栏
        toolbar_layout.addWidget(QLabel("缩放:"))
        toolbar_layout.addWidget(self.zoom_in_btn)
        toolbar_layout.addWidget(self.zoom_out_btn)
        toolbar_layout.addWidget(self.zoom_reset_btn)
        toolbar_layout.addWidget(self.zoom_fit_btn)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(self.save_btn)
        toolbar_layout.addWidget(self.copy_btn)
        toolbar_layout.addWidget(self.print_btn)

        self.graphics_view = QGraphicsView()
        self.graphics_scene = QGraphicsScene()
        self.graphics_view.setScene(self.graphics_scene)
        self.graphics_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.graphics_view.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.graphics_view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.graphics_view.setBackgroundBrush(QColor(240, 240, 240))

        # 信息标签
        self.info_label = QLabel("暂无二维码预览")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_label.setStyleSheet(
            """
            QLabel {
                color: #666;
                font-size: 14px;
                padding: 10px;
                border-top: 1px solid #ddd;
            }
        """
        )

        # 添加到主布局
        main_layout.addLayout(toolbar_layout)
        main_layout.addWidget(self.graphics_view, 1)  # 拉伸因子为1
        main_layout.addWidget(self.info_label)

    def set_qr_image(self, qimage, qr_data=None) -> None:
        """
        设置二维码图像

        Args:
            qimage: QImage对象
            qr_data: 二维码数据对象
        """
        if qimage and not qimage.isNull():
            # 转换为QPixmap
            pixmap = QPixmap.fromImage(qimage)
            self.current_qr_image = pixmap
            self.current_qr_data = qr_data

            # 清空场景并添加新图像
            self.graphics_scene.clear()
            self.graphics_scene.addPixmap(pixmap)

            # 调整视图
            self.zoom_fit()
            self.zoom_level = 1.0

            # 更新信息
            if qr_data:
                self.info_label.setText(
                    f"尺寸: {pixmap.width()}×{pixmap.height()} | "
                    f"类型: {qr_data.qr_type.value} | "
                    f"数据长度: {len(qr_data.data)} 字符"
                )
            else:
                self.info_label.setText(
                    f"尺寸: {pixmap.width()}×{pixmap.height()} | 格式: PNG"
                )
        else:
            self.graphics_scene.clear()
            self.info_label.setText("二维码生成失败")
            self.current_qr_image = None
            self.current_qr_data = None

    def zoom_in(self) -> None:
        """放大视图"""
        if self.zoom_level < 5.0:  # 限制最大缩放
            self.zoom_level *= 1.2
            self.graphics_view.scale(1.2, 1.2)
            self._update_zoom_info()

    def zoom_out(self) -> None:
        """缩小视图"""
        if self.zoom_level > 0.1:  # 限制最小缩放
            self.zoom_level *= 0.8
            self.graphics_view.scale(0.8, 0.8)
            self._update_zoom_info()

    def zoom_reset(self) -> None:
        """重置缩放（原始大小）"""
        self.graphics_view.resetTransform()
        self.zoom_level = 1.0
        self._update_zoom_info()

    def zoom_fit(self) -> None:
        """适应窗口大小"""
        if self.graphics_scene.items():
            self.graphics_view.fitInView(
                self.graphics_scene.itemsBoundingRect(),
                Qt.AspectRatioMode.KeepAspectRatio,
            )
            self._update_zoom_info()

    def _update_zoom_info(self) -> None:
        """更新缩放信息（可在状态栏显示）"""
        zoom_percent = int(self.zoom_level * 100)
        parent = self.parent()
        if parent and isinstance(parent, QMainWindow):
            status_bar = parent.statusBar()
            if status_bar:
                status_bar.showMessage(f"缩放: {zoom_percent}%")

    def save_image(self) -> None:
        """保存图像到文件"""
        from PySide6.QtWidgets import QFileDialog, QMessageBox

        if not self.current_qr_image:
            QMessageBox.warning(self, "警告", "没有二维码图像可保存")
            return

        # 设置文件过滤器
        formats = (
            "PNG 图片 (*.png);;"
            "JPEG 图片 (*.jpg *.jpeg);;"
            "BMP 图片 (*.bmp);;"
            "SVG 矢量图 (*.svg);;"
            "所有文件 (*.*)"
        )

        # 获取保存路径
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self, "保存二维码", "", formats
        )

        if file_path:
            try:
                # 根据选择的格式保存
                if selected_filter.startswith("PNG"):
                    self.current_qr_image.save(file_path, "PNG")
                elif selected_filter.startswith("JPEG"):
                    self.current_qr_image.save(file_path, "JPEG", quality=95)
                elif selected_filter.startswith("BMP"):
                    self.current_qr_image.save(file_path, "BMP")
                elif selected_filter.startswith("SVG"):
                    self._save_as_svg(file_path)
                else:
                    self.current_qr_image.save(file_path, "PNG")

                QMessageBox.information(self, "成功", f"二维码已保存到:\n{file_path}")

            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败: {str(e)}")

    def _save_as_svg(self, file_path: str) -> None:
        """
        保存为SVG格式

        Args:
            file_path: 保存路径
        """
        try:
            import segno

            if self.current_qr_data:
                # 使用segno生成SVG
                qrcode = segno.make(
                    self.current_qr_data.data,
                    error=self.current_qr_data.error_correction,
                )
                qrcode.save(
                    file_path,
                    scale=self.current_qr_data.size,
                    border=self.current_qr_data.border,
                    dark=self.current_qr_data.foreground_color,
                    light=self.current_qr_data.background_color,
                )
        except Exception as e:
            raise Exception(f"保存SVG失败: {str(e)}")

    def copy_image(self) -> None:
        """复制图像到剪贴板"""
        from PySide6.QtWidgets import QApplication, QMessageBox

        if self.current_qr_image:
            clipboard = QApplication.clipboard()
            clipboard.setPixmap(self.current_qr_image)
            QMessageBox.information(self, "成功", "二维码已复制到剪贴板")
        else:
            QMessageBox.warning(self, "警告", "没有二维码图像可复制")

    def print_image(self) -> None:
        """
        打印图像 - 高层接口

        处理前置条件检查，创建必要的对象，然后调用内部打印方法。
        """

        if not self.current_qr_image:
            QMessageBox.warning(self, "警告", "没有二维码图像可打印")
            return

        # 创建打印机和对话框
        printer = QPrinter()
        self._execute_print(printer, QPrintDialog)

    def _execute_print(self, printer: QPrinter, dialog_class) -> bool:
        """
        执行打印流程，可注入依赖以便测试

        Args:
            printer: QPrinter 实例
            dialog_class: QPrintDialog 类（或其子类），用于创建打印对话框

        Returns:
            bool: 打印是否成功执行

        Note:
            此方法专为测试设计，可以通过注入 mock 对象来测试不同的场景。
        """
        from PySide6.QtGui import QPainter

        print_dialog = dialog_class(printer, self)

        # 如果用户取消打印，直接返回
        if print_dialog.exec() != QPrintDialog.DialogCode.Accepted:
            return False

        # 创建画家对象并开始绘制
        painter = QPainter()
        try:
            # 如果无法开始绘制，返回失败
            if not painter.begin(printer):
                return False

            # 执行核心渲染逻辑
            self._render_print(painter, printer)
            return True

        finally:
            # 确保 painter 总是被正确结束
            painter.end()

    def _render_print(self, painter: QPainter, printer: QPrinter) -> None:
        """
        渲染打印内容 - 核心打印逻辑

        此方法包含所有与打印相关的计算和绘制操作，
        不依赖于外部对话框或用户交互，因此易于测试。

        Args:
            painter: QPainter 实例，用于绘制
            printer: QPrinter 实例，提供打印页面信息
        """
        from PySide6.QtCore import Qt
        from PySide6.QtPrintSupport import QPrinter

        # 获取打印区域
        page_rect = printer.pageRect(QPrinter.Unit.DevicePixel)
        pixmap_rect = self.current_qr_image.rect()

        # 保持宽高比，计算合适的打印尺寸
        scaled_size = pixmap_rect.size().scaled(
            page_rect.size().toSize(),
            Qt.AspectRatioMode.KeepAspectRatio,
        )

        # 计算居中位置
        x = (page_rect.width() - scaled_size.width()) / 2
        y = (page_rect.height() - scaled_size.height()) / 2

        # 绘制图像
        painter.drawPixmap(
            int(x),
            int(y),
            scaled_size.width(),
            scaled_size.height(),
            self.current_qr_image,
        )

    # ==================== 其他方法保持不变 ====================

    def get_current_image(self) -> Optional[QPixmap]:
        """
        获取当前显示的图像

        Returns:
            Optional[QPixmap]: 当前二维码图像
        """
        return self.current_qr_image

    def clear(self) -> None:
        """清除预览"""
        self.graphics_scene.clear()
        self.info_label.setText("暂无二维码预览")
        self.current_qr_image = None
        self.current_qr_data = None

    def __repr__(self) -> str:
        """返回字符串表示"""
        status = "有图像" if self.current_qr_image else "无图像"
        return f"QRPreviewWidget(status='{status}', zoom={self.zoom_level:.1f}x)"
