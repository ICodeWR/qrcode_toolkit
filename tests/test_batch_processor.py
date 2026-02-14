#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量处理器模块单元测试

模块名称：test_batch_processor.py
功能描述：测试 BatchProcessor 对话框的各项功能
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, call, patch

import pytest
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QApplication, QMessageBox

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))


from core.models import OutputFormat, QRCodeData, QRCodeType
from gui.batch_processor import BatchProcessor


@pytest.fixture(scope="session")
def qapp():
    """创建QApplication实例（会话级）"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


@pytest.fixture
def batch_processor(qapp):
    """创建BatchProcessor实例"""
    with (
        patch("gui.batch_processor.QRCodeDatabase"),
        patch("gui.batch_processor.QRCodeEngine"),
        patch("gui.batch_processor.QRCodeBatchScanner"),
    ):
        processor = BatchProcessor()
        yield processor
        processor.close()


@pytest.fixture
def temp_csv_file():
    """创建临时CSV文件"""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".csv", encoding="utf-8", delete=False
    ) as f:
        f.write("data1,tag1,note1\n")
        f.write("data2,tag2;tag3,note2\n")
        f.write("# 这是注释行\n")
        f.write("data3\n")
        temp_path = f.name

    yield temp_path

    # 清理
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def temp_folder_with_images():
    """创建包含测试图片的临时文件夹"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # 创建一些虚拟图片文件
        for i, ext in enumerate([".png", ".jpg", ".bmp", ".txt"]):
            file_path = os.path.join(temp_dir, f"test{i}{ext}")
            with open(file_path, "w") as f:
                f.write("dummy content")

        # 创建子文件夹
        sub_dir = os.path.join(temp_dir, "subfolder")
        os.makedirs(sub_dir, exist_ok=True)

        # 在子文件夹中创建图片
        sub_file = os.path.join(sub_dir, "sub_test.png")
        with open(sub_file, "w") as f:
            f.write("dummy content")

        yield temp_dir


class TestBatchProcessorInit:
    """测试BatchProcessor初始化"""

    def test_initialization(self, batch_processor):
        """测试初始化"""
        assert batch_processor.windowTitle() == "批量处理器"
        assert batch_processor.is_processing is False
        assert batch_processor.current_task is None
        assert batch_processor.tab_widget.count() == 2
        assert batch_processor.tab_widget.tabText(0) == "批量生成"
        assert batch_processor.tab_widget.tabText(1) == "批量扫描"
        assert batch_processor.start_btn.isEnabled() is True
        assert batch_processor.pause_btn.isEnabled() is False
        assert batch_processor.stop_btn.isEnabled() is False

    def test_ui_components_generate_tab(self, batch_processor):
        """测试批量生成选项卡的UI组件"""
        # 数据源区域
        assert hasattr(batch_processor, "csv_path_edit")
        assert hasattr(batch_processor, "csv_browse_btn")
        assert hasattr(batch_processor, "data_text")

        # 输出设置区域
        assert hasattr(batch_processor, "output_dir_edit")
        assert hasattr(batch_processor, "output_dir_browse_btn")
        assert hasattr(batch_processor, "filename_prefix_edit")
        assert hasattr(batch_processor, "format_combo")

        # 二维码设置区域
        assert hasattr(batch_processor, "type_combo")
        assert hasattr(batch_processor, "size_spin")
        assert hasattr(batch_processor, "border_spin")
        assert hasattr(batch_processor, "foreground_combo")
        assert hasattr(batch_processor, "background_combo")

        # Logo设置区域
        assert hasattr(batch_processor, "logo_path_edit")
        assert hasattr(batch_processor, "logo_browse_btn")
        assert hasattr(batch_processor, "logo_clear_btn")
        assert hasattr(batch_processor, "logo_scale_spin")
        assert hasattr(batch_processor, "logo_scale_slider")

        # 任务预览
        assert hasattr(batch_processor, "preview_list")

    def test_ui_components_scan_tab(self, batch_processor):
        """测试批量扫描选项卡的UI组件"""
        batch_processor.tab_widget.setCurrentIndex(1)

        assert hasattr(batch_processor, "scan_folder_edit")
        assert hasattr(batch_processor, "scan_folder_browse_btn")
        assert hasattr(batch_processor, "recursive_check")
        assert hasattr(batch_processor, "format_filter_edit")
        assert hasattr(batch_processor, "scan_output_edit")
        assert hasattr(batch_processor, "scan_output_browse_btn")
        assert hasattr(batch_processor, "group_by_folder_check")
        assert hasattr(batch_processor, "save_images_check")
        assert hasattr(batch_processor, "file_preview_list")
        assert hasattr(batch_processor, "stats_label")


class TestBatchGenerate:
    """测试批量生成功能"""

    def test_create_qrcode_data(self, batch_processor, monkeypatch):
        """测试创建二维码数据对象"""
        # === 直接设置控件的当前文本/值，绕过信号槽机制 ===
        batch_processor.type_combo.setCurrentIndex(0)
        batch_processor.size_spin.setCurrentText("15")
        batch_processor.border_spin.setCurrentText("4")
        batch_processor.foreground_combo.setCurrentText("蓝色")
        batch_processor.background_combo.setCurrentText("白色")

        # 直接设置 spin 和 slider 的值，并确保它们一致
        batch_processor.logo_scale_spin.setValue(25)
        batch_processor.logo_scale_slider.setValue(25)

        monkeypatch.setattr(batch_processor.logo_scale_spin, "value", lambda: 25)

        batch_processor.logo_path_edit.setText("/fake/path/logo.png")
        # 创建数据
        qr_data = batch_processor._create_qrcode_data(
            data="test_data", index=1, tags=["tag1", "tag2"], notes="note"  # 只传数据
        )

        assert isinstance(qr_data, QRCodeData)
        assert qr_data.data == "test_data"
        assert qr_data.tags == ["tag1", "tag2"]
        assert qr_data.notes == "note"
        assert qr_data.size == 15
        assert qr_data.border == 4
        # 断言期望的 0.25
        assert qr_data.logo_scale == 0.25
        assert qr_data.logo_path == "/fake/path/logo.png"  # 验证路径也被正确设置

    def test_create_qrcode_data_without_tags(self, batch_processor):
        """测试创建无标签的二维码数据"""
        qr_data = batch_processor._create_qrcode_data("simple_data", 1)

        assert qr_data.data == "simple_data"
        assert qr_data.tags == []
        assert qr_data.notes is None

    def test_get_color_code(self, batch_processor):
        """测试颜色代码转换"""
        assert batch_processor._get_color_code("黑色") == "#000000"
        assert batch_processor._get_color_code("蓝色") == "#0000FF"
        assert batch_processor._get_color_code("白色", True) == "#FFFFFF"
        assert batch_processor._get_color_code("透明", True) == "#FFFFFF"
        assert batch_processor._get_color_code("透明", False) == "#000000"
        assert batch_processor._get_color_code("未知颜色") == "#000000"

    @patch("gui.batch_processor.os.makedirs")
    @patch("gui.batch_processor.QMessageBox.warning")
    def test_start_batch_generate_no_data(
        self, mock_warning, mock_makedirs, batch_processor
    ):
        """测试无数据时开始批量生成"""
        batch_processor.csv_path_edit.clear()
        batch_processor.data_text.clear()

        batch_processor.start_batch_generate()

        mock_warning.assert_called_once()
        assert batch_processor.is_processing is False


class TestBatchScan:
    """测试批量扫描功能"""

    @patch("gui.batch_processor.QMessageBox.warning")
    def test_start_batch_scan_no_folder(self, mock_warning, batch_processor):
        """测试未选择文件夹时开始扫描"""
        batch_processor.scan_folder_edit.clear()
        batch_processor.scan_output_edit.setText("output.csv")

        batch_processor.start_batch_scan()

        mock_warning.assert_called_once()

    @patch("gui.batch_processor.QMessageBox.warning")
    def test_start_batch_scan_no_output(
        self, mock_warning, batch_processor, temp_folder_with_images
    ):
        """测试未指定输出文件时开始扫描"""
        batch_processor.scan_folder_edit.setText(temp_folder_with_images)
        batch_processor.scan_output_edit.clear()

        batch_processor.start_batch_scan()

        mock_warning.assert_called_once()

    @patch("gui.batch_processor.QRCodeBatchScanner")
    def test_start_batch_scan_success(
        self, mock_scanner_class, batch_processor, temp_folder_with_images
    ):
        """测试成功开始批量扫描"""
        # 设置
        mock_scanner = MagicMock()
        mock_scanner_class.return_value = batch_processor.batch_scanner

        batch_processor.scan_folder_edit.setText(temp_folder_with_images)
        batch_processor.scan_output_edit.setText("output.csv")

        # 执行
        batch_processor.start_batch_scan()

        # 验证
        assert batch_processor.is_processing is True
        assert batch_processor.current_task == "scan"
        assert batch_processor.start_btn.isEnabled() is False
        assert batch_processor.pause_btn.isEnabled() is True

        # 验证回调设置
        assert batch_processor.batch_scanner.set_callback.call_count == 4
        calls = [
            call("on_progress", batch_processor.on_scan_progress),
            call("on_result", batch_processor.on_scan_result),
            call("on_error", batch_processor.on_scan_error),
            call("on_finish", batch_processor.on_scan_finish),
        ]
        batch_processor.batch_scanner.set_callback.assert_has_calls(
            calls, any_order=True
        )

        # 验证扫描调用
        batch_processor.batch_scanner.scan_folder.assert_called_once_with(
            temp_folder_with_images, recursive=True
        )

    def test_on_scan_progress(self, batch_processor):
        """测试扫描进度回调"""
        batch_processor.on_scan_progress(50, "正在扫描...")

        assert batch_processor.status_label.text() == "正在扫描..."
        assert batch_processor.progress_label.text() == "扫描进度: 50%"
        assert batch_processor.progress_bar.value() == 50

    def test_on_scan_error(self, batch_processor):
        """测试扫描错误回调"""
        with patch("gui.batch_processor.QMessageBox.warning") as mock_warning:
            batch_processor.on_scan_error("测试错误")
            mock_warning.assert_called_once()

    @patch("gui.batch_processor.QMessageBox")
    @patch("gui.batch_processor.BatchProcessor.save_scan_results")
    def test_on_scan_finish_success(self, mock_save, mock_messagebox, batch_processor):
        """测试扫描完成回调（成功）"""
        mock_save.return_value = True
        results = [{"data": "test1"}, {"data": "test2"}]

        # 设置 mock
        mock_instance = MagicMock()
        mock_messagebox.return_value = mock_instance

        batch_processor.on_scan_finish(results)

        mock_save.assert_called_once_with(results)
        mock_messagebox.assert_called_once()  # 验证 QMessageBox 被实例化
        mock_instance.exec.assert_called_once()  # 验证 exec 被调用

    @patch("gui.batch_processor.QMessageBox.warning")
    @patch("gui.batch_processor.BatchProcessor.save_scan_results")
    def test_on_scan_finish_failure(self, mock_save, mock_warning, batch_processor):
        """测试扫描完成回调（保存失败）"""
        mock_save.return_value = False
        results = [{"data": "test1"}]

        batch_processor.on_scan_finish(results)

        mock_save.assert_called_once_with(results)
        mock_warning.assert_called_once()
        assert batch_processor.is_processing is False

    def test_save_scan_results(self, batch_processor, tmp_path):
        """测试保存扫描结果"""
        output_file = tmp_path / "scan_results.csv"
        batch_processor.scan_output_edit.setText(str(output_file))

        results = [
            {
                "source": "test1.png",
                "data": "QR Code 1",
                "type": "QRCODE",
                "confidence": 0.95,
                "timestamp": "2026-02-12T10:00:00",
            },
            {
                "source": "test2.png",
                "data": "QR Code 2",
                "type": "QRCODE",
                "confidence": 0.88,
                "timestamp": "2026-02-12T10:01:00",
            },
        ]

        result = batch_processor.save_scan_results(results)

        assert result is True
        assert output_file.exists()

        # 验证CSV内容
        import csv

        with open(output_file, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            rows = list(reader)
            assert len(rows) == 3  # 标题行 + 2行数据
            assert rows[0] == ["文件路径", "二维码数据", "类型", "置信度", "时间"]
            assert rows[1][0] == "test1.png"
            assert rows[1][1] == "QR Code 1"
            assert rows[2][0] == "test2.png"


class TestPreviewFunctions:
    """测试预览功能"""

    def test_update_generate_preview_from_csv(self, batch_processor, temp_csv_file):
        """测试从CSV文件更新生成预览"""
        batch_processor.csv_path_edit.setText(temp_csv_file)

        batch_processor.update_generate_preview()

        assert batch_processor.preview_list.count() > 0

    def test_update_generate_preview_from_text(self, batch_processor):
        """测试从文本输入更新生成预览"""
        batch_processor.data_text.setPlainText(
            "line1\nline2\nline3\nline4\nline5\nline6"
        )

        batch_processor.update_generate_preview()

        assert batch_processor.preview_list.count() >= 5

    def test_update_scan_preview(self, batch_processor, temp_folder_with_images):
        """测试更新扫描预览"""
        batch_processor.scan_folder_edit.setText(temp_folder_with_images)

        batch_processor.update_scan_preview()

        assert batch_processor.file_preview_list.count() >= 2
        assert "找到" in batch_processor.stats_label.text()

    def test_is_image_file(self, batch_processor):
        """测试图片文件识别"""
        assert batch_processor._is_image_file("test.png") is True
        assert batch_processor._is_image_file("test.jpg") is True
        assert batch_processor._is_image_file("test.jpeg") is True
        assert batch_processor._is_image_file("test.bmp") is True
        assert batch_processor._is_image_file("test.gif") is True
        assert batch_processor._is_image_file("test.txt") is False
        assert batch_processor._is_image_file("test.PNG") is True  # 大小写不敏感


class TestProcessingControl:
    """测试处理控制功能"""

    def test_pause_processing_scan(self, batch_processor):
        """测试暂停扫描"""
        batch_processor.is_processing = True
        batch_processor.current_task = "scan"

        with patch.object(batch_processor.batch_scanner, "stop") as mock_stop:
            batch_processor.pause_processing()

            mock_stop.assert_called_once()
            assert batch_processor.is_processing is False
            assert batch_processor.progress_label.text() == "已暂停"

    def test_stop_processing_scan(self, batch_processor):
        """测试停止扫描"""
        batch_processor.current_task = "scan"

        with patch.object(batch_processor.batch_scanner, "stop") as mock_stop:
            with patch.object(batch_processor, "reset_processing") as mock_reset:
                batch_processor.stop_processing()

                mock_stop.assert_called_once()
                mock_reset.assert_called_once()
                assert batch_processor.progress_label.text() == "已停止"

    def test_reset_processing(self, batch_processor):
        """测试重置处理状态"""
        batch_processor.is_processing = True
        batch_processor.current_task = "generate"

        # 设置一些数据
        batch_processor.batch_qr_list = [MagicMock(), MagicMock()]
        batch_processor.batch_total = 2
        batch_processor.batch_current = 1

        batch_processor.reset_processing()

        # 验证状态被重置
        assert batch_processor.is_processing is False
        assert batch_processor.current_task is None
        assert batch_processor.batch_qr_list == []
        assert batch_processor.batch_total == 0
        assert batch_processor.batch_current == 0
        assert batch_processor.start_btn.isEnabled() is True  # UI 状态更新

    def test_update_ui_state(self, batch_processor):
        """测试更新UI状态"""
        batch_processor.update_ui_state(True)

        assert batch_processor.start_btn.isEnabled() is False
        assert batch_processor.pause_btn.isEnabled() is True
        assert batch_processor.stop_btn.isEnabled() is True
        assert batch_processor.tab_widget.isEnabled() is False

        batch_processor.update_ui_state(False)

        assert batch_processor.start_btn.isEnabled() is True
        assert batch_processor.pause_btn.isEnabled() is False
        assert batch_processor.stop_btn.isEnabled() is False
        assert batch_processor.tab_widget.isEnabled() is True


class TestCloseEvent:
    """测试关闭事件"""

    @patch("gui.batch_processor.QMessageBox.question")
    def test_close_event_processing_yes(self, mock_question, batch_processor):
        batch_processor.is_processing = True
        mock_question.return_value = QMessageBox.StandardButton.Yes

        with patch.object(batch_processor, "stop_processing") as mock_stop:
            event = MagicMock()
            batch_processor.closeEvent(event)

            mock_question.assert_called_once()
            mock_stop.assert_called_once()
            event.accept.assert_called_once()
            # 不再 mock disconnect — Qt 会自动处理

    @patch("gui.batch_processor.QMessageBox.question")
    def test_close_event_processing_no(self, mock_question, batch_processor):
        """测试处理中关闭窗口（选择否）"""
        batch_processor.is_processing = True
        mock_question.return_value = QMessageBox.StandardButton.No

        event = MagicMock()
        event.ignore = MagicMock()
        event.accept = MagicMock()

        batch_processor.closeEvent(event)

        mock_question.assert_called_once()
        event.ignore.assert_called_once()
        event.accept.assert_not_called()

    @patch("gui.batch_processor.QMessageBox.question")
    def test_close_event_not_processing(self, mock_question, batch_processor):
        batch_processor.is_processing = False
        event = MagicMock()
        batch_processor.closeEvent(event)

        mock_question.assert_not_called()  # 或根据实际逻辑判断是否调用
        event.accept.assert_called_once()


class TestRepr:
    """测试字符串表示"""

    def test_repr_idle(self, batch_processor):
        """测试空闲状态"""
        batch_processor.is_processing = False
        batch_processor.current_task = None

        repr_str = repr(batch_processor)
        assert "BatchProcessor" in repr_str
        assert "status='空闲'" in repr_str
        assert "task='None'" in repr_str

    def test_repr_processing(self, batch_processor):
        """测试处理中状态"""
        batch_processor.is_processing = True
        batch_processor.current_task = "generate"

        repr_str = repr(batch_processor)
        assert "BatchProcessor" in repr_str
        assert "status='处理中'" in repr_str
        assert "task='generate'" in repr_str
