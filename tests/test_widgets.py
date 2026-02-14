#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUI组件模块单元测试

模块名称：test_widgets.py
功能描述：测试 ColorPickerButton 和 QRPreviewWidget 等自定义组件
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, create_autospec, patch

import pytest
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPixmap
from PySide6.QtPrintSupport import QPrintDialog, QPrinter
from PySide6.QtWidgets import QApplication, QColorDialog, QMessageBox

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.models import QRCodeData, QRCodeType
from gui.widgets import ColorPickerButton, QRPreviewWidget


@pytest.fixture(scope="session")
def qapp():
    """创建QApplication实例（会话级）"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app
    app.quit()


@pytest.fixture
def color_button(qapp):
    """创建ColorPickerButton实例 - 函数级作用域"""
    button = ColorPickerButton("#FF0000")
    yield button
    button.deleteLater()
    qapp.processEvents()


@pytest.fixture
def preview_widget(qapp):
    """创建QRPreviewWidget实例 - 函数级作用域"""
    widget = QRPreviewWidget()
    yield widget
    widget.deleteLater()
    qapp.processEvents()


@pytest.fixture
def sample_qr_data():
    """创建示例二维码数据"""
    return QRCodeData(
        id="test_id",
        data="https://example.com",
        qr_type=QRCodeType.URL,
        version=0,
        error_correction="H",
        size=10,
        border=4,
        foreground_color="#000000",
        background_color="#FFFFFF",
        logo_scale=0.2,
        output_format="PNG",
    )


@pytest.fixture
def sample_qimage():
    """创建示例QImage"""
    image = QImage(200, 200, QImage.Format.Format_RGB32)
    image.fill(QColor(255, 255, 255))

    # 绘制一些内容
    painter = QPainter(image)
    painter.fillRect(50, 50, 100, 100, QColor(0, 0, 0))
    painter.end()

    return image


@pytest.fixture
def preview_with_image(preview_widget, sample_qimage):
    """创建带有图像的预览部件"""
    preview_widget.set_qr_image(sample_qimage, None)
    return preview_widget


class TestColorPickerButton:
    """测试颜色选择按钮"""

    def test_initialization(self, color_button):
        """测试初始化"""
        assert color_button.color == QColor("#FF0000")
        assert color_button.width() == 60
        assert color_button.height() == 30
        assert "background-color: #ff0000" in color_button.styleSheet().lower()

    def test_set_color_valid(self, color_button):
        """测试设置有效颜色"""
        color_button.set_color("#00FF00")
        assert color_button.color.name() == "#00ff00"
        assert "background-color: #00ff00" in color_button.styleSheet().lower()

    def test_set_color_invalid(self, color_button):
        """测试设置无效颜色"""
        original_color = color_button.color.name()
        color_button.set_color("invalid_color")
        assert color_button.color.name() == original_color

    def test_set_color_same(self, color_button):
        """测试设置相同颜色不应该触发信号"""
        color_button.set_color("#FF0000")
        mock_callback = MagicMock()
        color_button.color_changed.connect(mock_callback)

        color_button.set_color("#FF0000")
        mock_callback.assert_not_called()

    def test_get_color(self, color_button):
        """测试获取颜色"""
        assert color_button.get_color() == "#ff0000"

        color_button.set_color("#0000FF")
        assert color_button.get_color() == "#0000ff"

    def test_pick_color_accepted(self, color_button, mocker):
        """测试选择颜色（确认）- 使用 patch.object"""
        with patch.object(
            QColorDialog, "exec", return_value=QColorDialog.DialogCode.Accepted
        ):
            with patch.object(
                QColorDialog, "currentColor", return_value=QColor("#00FF00")
            ):
                color_button.pick_color()
                assert color_button.color.name() == "#00ff00"

    def test_color_signal(self, color_button, mocker):
        """测试颜色改变信号"""
        mock_callback = MagicMock()
        color_button.color_changed.connect(mock_callback)

        with patch.multiple(
            "PySide6.QtWidgets.QColorDialog",
            exec=mocker.MagicMock(return_value=QColorDialog.DialogCode.Accepted),
            currentColor=mocker.MagicMock(return_value=QColor("#00FF00")),
            setStyleSheet=mocker.MagicMock(),
            create=True,
        ):
            color_button.pick_color()
            mock_callback.assert_called_once_with("#00ff00")

    @patch("gui.widgets.QColorDialog")
    def test_pick_color_cancelled(self, mock_dialog_class, color_button):
        """测试选择颜色（取消）"""
        original_color = color_button.color.name()

        mock_dialog = create_autospec(QColorDialog)
        mock_dialog.exec.return_value = QColorDialog.DialogCode.Rejected
        mock_dialog_class.return_value = mock_dialog

        with patch.object(color_button, "color_changed") as mock_signal:
            color_button.pick_color()
            assert color_button.color.name() == original_color
            mock_signal.emit.assert_not_called()


class TestQRPreviewWidgetInit:
    """测试QRPreviewWidget初始化"""

    def test_initialization(self, preview_widget):
        """测试初始化"""
        assert preview_widget.current_qr_image is None
        assert preview_widget.current_qr_data is None
        assert preview_widget.zoom_level == 1.0
        assert preview_widget.info_label.text() == "暂无二维码预览"

        # 验证UI组件
        assert hasattr(preview_widget, "zoom_in_btn")
        assert hasattr(preview_widget, "zoom_out_btn")
        assert hasattr(preview_widget, "zoom_reset_btn")
        assert hasattr(preview_widget, "zoom_fit_btn")
        assert hasattr(preview_widget, "save_btn")
        assert hasattr(preview_widget, "copy_btn")
        assert hasattr(preview_widget, "print_btn")
        assert hasattr(preview_widget, "graphics_view")
        assert hasattr(preview_widget, "graphics_scene")
        assert hasattr(preview_widget, "info_label")

    def test_zoom_buttons_connections(self, preview_widget):
        """测试缩放按钮连接"""
        with patch.object(preview_widget, "zoom_in") as mock_zoom_in:
            preview_widget.zoom_in_btn.clicked.emit()
            mock_zoom_in.assert_called_once()

        with patch.object(preview_widget, "zoom_out") as mock_zoom_out:
            preview_widget.zoom_out_btn.clicked.emit()
            mock_zoom_out.assert_called_once()

        with patch.object(preview_widget, "zoom_reset") as mock_zoom_reset:
            preview_widget.zoom_reset_btn.clicked.emit()
            mock_zoom_reset.assert_called_once()

        with patch.object(preview_widget, "zoom_fit") as mock_zoom_fit:
            preview_widget.zoom_fit_btn.clicked.emit()
            mock_zoom_fit.assert_called_once()


class TestQRPreviewWidgetSetImage:
    """测试设置二维码图像"""

    def test_set_qr_image_valid(self, preview_widget, sample_qimage, sample_qr_data):
        """测试设置有效图像"""
        preview_widget.set_qr_image(sample_qimage, sample_qr_data)

        assert preview_widget.current_qr_image is not None
        assert preview_widget.current_qr_data == sample_qr_data
        assert preview_widget.graphics_scene.items().__len__() > 0
        assert "尺寸: 200×200" in preview_widget.info_label.text()
        assert (
            f"类型: {sample_qr_data.qr_type.value}" in preview_widget.info_label.text()
        )

    def test_set_qr_image_without_data(self, preview_widget, sample_qimage):
        """测试设置图像但不提供数据"""
        preview_widget.set_qr_image(sample_qimage, None)

        assert preview_widget.current_qr_image is not None
        assert preview_widget.current_qr_data is None
        assert "尺寸: 200×200" in preview_widget.info_label.text()
        assert "格式: PNG" in preview_widget.info_label.text()

    def test_set_qr_image_null(self, preview_widget):
        """测试设置空图像"""
        null_image = QImage()
        preview_widget.set_qr_image(null_image, None)

        assert preview_widget.current_qr_image is None
        assert preview_widget.current_qr_data is None
        assert preview_widget.info_label.text() == "二维码生成失败"
        assert preview_widget.graphics_scene.items().__len__() == 0

    def test_clear(self, preview_widget, sample_qimage, sample_qr_data):
        """测试清除预览"""
        preview_widget.set_qr_image(sample_qimage, sample_qr_data)
        assert preview_widget.current_qr_image is not None

        preview_widget.clear()

        assert preview_widget.current_qr_image is None
        assert preview_widget.current_qr_data is None
        assert preview_widget.info_label.text() == "暂无二维码预览"
        assert preview_widget.graphics_scene.items().__len__() == 0


class TestQRPreviewWidgetZoom:
    """测试缩放功能"""

    def test_zoom_in(self, preview_widget):
        """测试放大"""
        with patch.object(preview_widget.graphics_view, "scale") as mock_scale:
            preview_widget.zoom_level = 1.0
            preview_widget.zoom_in()

            assert preview_widget.zoom_level == 1.2
            mock_scale.assert_called_once_with(1.2, 1.2)

    def test_zoom_in_max(self, preview_widget):
        """测试放大到最大限制"""
        with patch.object(preview_widget.graphics_view, "scale") as mock_scale:
            preview_widget.zoom_level = 4.9
            preview_widget.zoom_in()

            assert preview_widget.zoom_level == 5.88
            mock_scale.assert_called_once()

    def test_zoom_out(self, preview_widget):
        """测试缩小"""
        with patch.object(preview_widget.graphics_view, "scale") as mock_scale:
            preview_widget.zoom_level = 1.0
            preview_widget.zoom_out()

            assert preview_widget.zoom_level == 0.8
            mock_scale.assert_called_once_with(0.8, 0.8)

    def test_zoom_out_min(self, preview_widget):
        """测试缩小到最小限制"""
        with patch.object(preview_widget.graphics_view, "scale") as mock_scale:
            preview_widget.zoom_level = 0.11
            preview_widget.zoom_out()

            assert preview_widget.zoom_level == pytest.approx(0.088, rel=1e-9)
            mock_scale.assert_called_once()

    def test_zoom_reset(self, preview_widget):
        """测试重置缩放"""
        with patch.object(preview_widget.graphics_view, "resetTransform") as mock_reset:
            preview_widget.zoom_level = 2.0
            preview_widget.zoom_reset()

            assert preview_widget.zoom_level == 1.0
            mock_reset.assert_called_once()

    def test_zoom_fit_with_items(self, preview_widget, sample_qimage):
        """测试适应窗口（有图像）"""
        preview_widget.set_qr_image(sample_qimage, None)

        with patch.object(preview_widget.graphics_view, "fitInView") as mock_fit:
            preview_widget.zoom_fit()
            mock_fit.assert_called_once()

    def test_zoom_fit_no_items(self, preview_widget):
        """测试适应窗口（无图像）"""
        with patch.object(preview_widget.graphics_view, "fitInView") as mock_fit:
            preview_widget.zoom_fit()
            mock_fit.assert_not_called()

    def test_update_zoom_info(self, preview_widget):
        """测试更新缩放信息"""
        from PySide6.QtWidgets import QMainWindow

        parent = QMainWindow()
        mock_status_bar = MagicMock()
        parent.statusBar = MagicMock(return_value=mock_status_bar)
        preview_widget.setParent(parent)

        preview_widget._update_zoom_info()

        mock_status_bar.showMessage.assert_called_with("缩放: 100%")
        preview_widget.setParent(None)
        parent.deleteLater()


class TestQRPreviewWidgetSave:
    """测试保存功能"""

    @patch("PySide6.QtWidgets.QFileDialog.getSaveFileName")
    @patch("PySide6.QtWidgets.QMessageBox.warning")
    def test_save_image_no_image(self, mock_warning, mock_dialog, preview_widget):
        """测试无图像时保存"""
        preview_widget.current_qr_image = None
        preview_widget.save_image()

        mock_dialog.assert_not_called()
        mock_warning.assert_called_once()

    @patch("PySide6.QtWidgets.QFileDialog.getSaveFileName")
    @patch("PySide6.QtWidgets.QMessageBox.information")
    def test_save_image_png(
        self, mock_info, mock_dialog, preview_widget, sample_qimage
    ):
        """测试保存为PNG格式"""
        preview_widget.current_qr_image = QPixmap.fromImage(sample_qimage)
        mock_dialog.return_value = ("/path/to/image.png", "PNG 图片 (*.png)")

        with patch.object(preview_widget.current_qr_image, "save") as mock_save:
            mock_save.return_value = True
            preview_widget.save_image()

            mock_save.assert_called_once_with("/path/to/image.png", "PNG")
            mock_info.assert_called_once()

    @patch("PySide6.QtWidgets.QFileDialog.getSaveFileName")
    @patch("PySide6.QtWidgets.QMessageBox.information")
    def test_save_image_jpeg(
        self, mock_info, mock_dialog, preview_widget, sample_qimage
    ):
        """测试保存为JPEG格式"""
        preview_widget.current_qr_image = QPixmap.fromImage(sample_qimage)
        mock_dialog.return_value = ("/path/to/image.jpg", "JPEG 图片 (*.jpg *.jpeg)")

        with patch.object(preview_widget.current_qr_image, "save") as mock_save:
            mock_save.return_value = True
            preview_widget.save_image()

            mock_save.assert_called_once_with("/path/to/image.jpg", "JPEG", quality=95)
            mock_info.assert_called_once()

    @patch("PySide6.QtWidgets.QFileDialog.getSaveFileName")
    @patch("PySide6.QtWidgets.QMessageBox.information")
    def test_save_image_svg(
        self, mock_info, mock_dialog, preview_widget, sample_qimage
    ):
        """测试保存为SVG格式"""
        import sys
        from unittest.mock import MagicMock

        mock_segno = MagicMock()
        mock_qrcode = MagicMock()
        mock_segno.make.return_value = mock_qrcode

        original_segno = sys.modules.get("segno", None)

        try:
            sys.modules["segno"] = mock_segno

            preview_widget.current_qr_image = QPixmap.fromImage(sample_qimage)
            preview_widget.current_qr_data = MagicMock()
            mock_dialog.return_value = ("/path/to/image.svg", "SVG 矢量图 (*.svg)")

            preview_widget.save_image()

            mock_segno.make.assert_called_once()
            mock_qrcode.save.assert_called_once()
            mock_info.assert_called_once()

        finally:
            if original_segno:
                sys.modules["segno"] = original_segno
            else:
                del sys.modules["segno"]

    @patch("builtins.__import__")
    def test_save_as_svg(self, mock_import, preview_widget):
        """测试保存SVG格式"""
        mock_segno = MagicMock()
        mock_qrcode = MagicMock()
        mock_segno.make.return_value = mock_qrcode

        def import_side_effect(name, *args, **kwargs):
            if name == "segno":
                return mock_segno
            return __import__(name, *args, **kwargs)

        mock_import.side_effect = import_side_effect

        preview_widget.current_qr_data = MagicMock()
        preview_widget.current_qr_data.data = "test data"
        preview_widget.current_qr_data.error_correction = "H"
        preview_widget.current_qr_data.size = 10
        preview_widget.current_qr_data.border = 4
        preview_widget.current_qr_data.foreground_color = "#000000"
        preview_widget.current_qr_data.background_color = "#FFFFFF"

        preview_widget._save_as_svg("/path/to/image.svg")

        mock_segno.make.assert_called_once_with("test data", error="H")
        mock_qrcode.save.assert_called_once_with(
            "/path/to/image.svg", scale=10, border=4, dark="#000000", light="#FFFFFF"
        )


class TestQRPreviewWidgetCopy:
    """测试复制功能"""

    @patch("PySide6.QtWidgets.QApplication.clipboard")
    @patch("PySide6.QtWidgets.QMessageBox.information")
    def test_copy_image_success(
        self, mock_info, mock_clipboard, preview_widget, sample_qimage
    ):
        """测试成功复制图像"""
        preview_widget.current_qr_image = QPixmap.fromImage(sample_qimage)
        mock_clipboard_instance = MagicMock()
        mock_clipboard.return_value = mock_clipboard_instance

        preview_widget.copy_image()

        mock_clipboard_instance.setPixmap.assert_called_once_with(
            preview_widget.current_qr_image
        )
        mock_info.assert_called_once()

    @patch("PySide6.QtWidgets.QMessageBox.warning")
    def test_copy_image_no_image(self, mock_warning, preview_widget):
        """测试无图像时复制"""
        preview_widget.current_qr_image = None
        preview_widget.copy_image()
        mock_warning.assert_called_once()


class TestQRPreviewWidgetPrint:
    """测试打印功能（重构后）"""

    def test_print_image_no_image(self, preview_widget, mocker):
        """测试无图像时打印"""
        mock_warning = mocker.patch("PySide6.QtWidgets.QMessageBox.warning")
        preview_widget.current_qr_image = None

        preview_widget.print_image()

        mock_warning.assert_called_once_with(
            preview_widget, "警告", "没有二维码图像可打印"
        )

    def test_print_image_with_image_calls_execute_print(self, preview_widget, mocker):
        """测试有图像时调用 _execute_print"""
        # 准备
        real_pixmap = QPixmap(200, 200)
        real_pixmap.fill(Qt.GlobalColor.white)
        preview_widget.current_qr_image = real_pixmap

        # Mock _execute_print 方法
        mock_execute = mocker.patch.object(preview_widget, "_execute_print")

        # 执行
        preview_widget.print_image()

        # 验证 _execute_print 被调用，且参数正确
        mock_execute.assert_called_once()
        args, kwargs = mock_execute.call_args
        assert len(args) == 2
        assert isinstance(args[0], QPrinter)  # printer 参数
        assert args[1] == QPrintDialog  # dialog_class 参数

    def test_execute_print_dialog_accepted_painter_begin_success(self, preview_widget, mocker):
        """测试对话框接受且 painter.begin 成功的情况"""
        # 准备
        real_pixmap = QPixmap(200, 200)
        real_pixmap.fill(Qt.GlobalColor.white)
        preview_widget.current_qr_image = real_pixmap

        # 创建 mock 对象
        mock_printer = mocker.MagicMock(spec=QPrinter)
        mock_dialog = mocker.MagicMock(spec=QPrintDialog)
        mock_dialog.exec.return_value = QPrintDialog.DialogCode.Accepted

        mock_painter = mocker.MagicMock(spec=QPainter)
        mock_painter.begin.return_value = True

        # Mock QPainter 构造函数
        mocker.patch("PySide6.QtGui.QPainter", return_value=mock_painter)

        # Mock _render_print 方法
        mock_render = mocker.patch.object(preview_widget, "_render_print")

        # 执行
        result = preview_widget._execute_print(mock_printer, lambda *args: mock_dialog)

        # 验证
        assert result is True
        mock_dialog.exec.assert_called_once()
        mock_painter.begin.assert_called_once_with(mock_printer)
        mock_render.assert_called_once_with(mock_painter, mock_printer)
        mock_painter.end.assert_called_once()

    def test_execute_print_dialog_accepted_painter_begin_fails(self, preview_widget, mocker):
        """测试对话框接受但 painter.begin 失败的情况"""
        # 准备
        real_pixmap = QPixmap(200, 200)
        real_pixmap.fill(Qt.GlobalColor.white)
        preview_widget.current_qr_image = real_pixmap

        # 创建 mock 对象
        mock_printer = mocker.MagicMock(spec=QPrinter)
        mock_dialog = mocker.MagicMock(spec=QPrintDialog)
        mock_dialog.exec.return_value = QPrintDialog.DialogCode.Accepted

        mock_painter = mocker.MagicMock(spec=QPainter)
        mock_painter.begin.return_value = False  # begin 失败

        # Mock QPainter 构造函数
        mocker.patch("PySide6.QtGui.QPainter", return_value=mock_painter)

        # Mock _render_print 方法（不应该被调用）
        mock_render = mocker.patch.object(preview_widget, "_render_print")

        # 执行
        result = preview_widget._execute_print(mock_printer, lambda *args: mock_dialog)

        # 验证
        assert result is False
        mock_dialog.exec.assert_called_once()
        mock_painter.begin.assert_called_once_with(mock_printer)
        mock_render.assert_not_called()
        mock_painter.end.assert_called_once()

    def test_execute_print_dialog_rejected(self, preview_widget, mocker):
        """测试对话框被拒绝的情况"""
        # 准备
        real_pixmap = QPixmap(200, 200)
        real_pixmap.fill(Qt.GlobalColor.white)
        preview_widget.current_qr_image = real_pixmap

        # 创建 mock 对象
        mock_printer = mocker.MagicMock(spec=QPrinter)
        mock_dialog = mocker.MagicMock(spec=QPrintDialog)
        mock_dialog.exec.return_value = QPrintDialog.DialogCode.Rejected

        mock_painter = mocker.MagicMock(spec=QPainter)

        # Mock QPainter 构造函数
        mocker.patch("PySide6.QtGui.QPainter", return_value=mock_painter)

        # Mock _render_print 方法
        mock_render = mocker.patch.object(preview_widget, "_render_print")

        # 执行
        result = preview_widget._execute_print(mock_printer, lambda *args: mock_dialog)

        # 验证
        assert result is False
        mock_dialog.exec.assert_called_once()
        mock_painter.begin.assert_not_called()
        mock_render.assert_not_called()
        mock_painter.end.assert_not_called()

    def test_render_print_calculates_correct_position(self, preview_widget):
        """测试 _render_print 方法计算正确的打印位置"""
        # 准备
        from PySide6.QtCore import QRectF, QSize

        # 创建真实图像 (200x200)
        real_pixmap = QPixmap(200, 200)
        real_pixmap.fill(Qt.GlobalColor.white)
        preview_widget.current_qr_image = real_pixmap

        # 创建 mock painter 和 printer
        mock_painter = MagicMock(spec=QPainter)
        mock_printer = MagicMock(spec=QPrinter)

        # 设置 pageRect 返回 800x600 的页面
        mock_page_rect = QRectF(0, 0, 800, 600)
        mock_printer.pageRect.return_value = mock_page_rect

        # 执行
        preview_widget._render_print(mock_painter, mock_printer)

        # 验证 pageRect 被正确调用
        mock_printer.pageRect.assert_called_once_with(QPrinter.Unit.DevicePixel)

        # 验证 drawPixmap 被调用
        mock_painter.drawPixmap.assert_called_once()

        # 验证计算的位置（200x200 的图像在 800x600 的页面上，保持宽高比）
        # 缩放后应为 600x600 (因为高度限制)
        # X 坐标应为 (800 - 600) / 2 = 100
        # Y 坐标应为 (600 - 600) / 2 = 0
        args, kwargs = mock_painter.drawPixmap.call_args
        assert len(args) == 5
        assert args[0] == 100  # x
        assert args[1] == 0     # y
        assert args[2] == 600   # width
        assert args[3] == 600   # height
        assert args[4] == real_pixmap  # pixmap

    def test_render_print_with_different_image_sizes(self, preview_widget):
        """测试不同尺寸图像的渲染计算"""
        from PySide6.QtCore import QRectF

        test_cases = [
            # (图像宽, 图像高, 页面宽, 页面高, 预期缩放宽, 预期缩放宽, 预期X, 预期Y)
            (200, 200, 800, 600, 600, 600, 100, 0),    # 正方形
            (400, 200, 800, 600, 800, 400, 0, 100),    # 宽图
            (200, 400, 800, 600, 300, 600, 250, 0),    # 长图
            (100, 100, 800, 600, 600, 600, 100, 0),    # 小图
        ]

        for img_w, img_h, page_w, page_h, exp_w, exp_h, exp_x, exp_y in test_cases:
            # 准备
            pixmap = QPixmap(img_w, img_h)
            pixmap.fill(Qt.GlobalColor.white)
            preview_widget.current_qr_image = pixmap

            mock_painter = MagicMock(spec=QPainter)
            mock_printer = MagicMock(spec=QPrinter)
            mock_page_rect = QRectF(0, 0, page_w, page_h)
            mock_printer.pageRect.return_value = mock_page_rect

            # 执行
            preview_widget._render_print(mock_painter, mock_printer)

            # 验证
            args, kwargs = mock_painter.drawPixmap.call_args
            assert args[0] == exp_x, f"X坐标错误 for {img_w}x{img_h}"
            assert args[1] == exp_y, f"Y坐标错误 for {img_w}x{img_h}"
            assert args[2] == exp_w, f"宽度错误 for {img_w}x{img_h}"
            assert args[3] == exp_h, f"高度错误 for {img_w}x{img_h}"


class TestQRPreviewWidgetUtility:
    """测试工具方法"""

    def test_get_current_image(self, preview_widget, sample_qimage):
        """测试获取当前图像"""
        assert preview_widget.get_current_image() is None

        pixmap = QPixmap.fromImage(sample_qimage)
        preview_widget.current_qr_image = pixmap

        assert preview_widget.get_current_image() == pixmap

    def test_repr_with_image(self, preview_widget, sample_qimage):
        """测试有图像时的字符串表示"""
        preview_widget.current_qr_image = QPixmap.fromImage(sample_qimage)
        preview_widget.zoom_level = 1.5

        repr_str = repr(preview_widget)

        assert "QRPreviewWidget" in repr_str
        assert "status='有图像'" in repr_str
        assert "zoom=1.5x" in repr_str

    def test_repr_no_image(self, preview_widget):
        """测试无图像时的字符串表示"""
        preview_widget.current_qr_image = None

        repr_str = repr(preview_widget)

        assert "QRPreviewWidget" in repr_str
        assert "status='无图像'" in repr_str
