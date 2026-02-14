#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模板编辑器模块单元测试

模块名称：test_template_editor.py
功能描述：测试 TemplateEditor 对话框的各项功能
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from utils.constants import TemplateConstants

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from gui.template_editor import TemplateEditor


@pytest.fixture(scope="session")
def qapp():
    """创建QApplication实例（会话级）"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


@pytest.fixture
def template_editor(qapp):
    """创建TemplateEditor实例（新建模式）"""
    editor = TemplateEditor()
    yield editor
    editor.close()


@pytest.fixture
def sample_template():
    """创建示例模板数据"""
    return {
        "name": "测试模板",
        "category": "商务",
        "config": {
            "type": "URL",
            "size": 15,
            "border": 3,
            "error_correction": "H",
            "color": "#1a73e8",
            "logo_path": "/path/to/logo.png",
            "logo_scale": 0.25,
            "gradient": ["#FF6B6B", "#4ECDC4"],
            "gradient_type": "linear",
        },
    }


@pytest.fixture
def template_editor_edit(qapp, sample_template):
    """创建TemplateEditor实例（编辑模式）"""
    editor = TemplateEditor(template_data=sample_template)
    yield editor
    editor.close()


class TestTemplateEditorInit:
    """测试TemplateEditor初始化"""

    def test_initialization_new(self, template_editor):
        """测试新建模式初始化"""
        assert template_editor.windowTitle() == "新建模板"
        assert template_editor.template_data is None
        assert template_editor.name_edit.text() == ""
        assert template_editor.category_combo.currentText() == "通用"

    def test_initialization_edit(self, template_editor_edit, sample_template):
        """测试编辑模式初始化"""
        assert template_editor_edit.windowTitle() == "编辑模板"
        assert template_editor_edit.template_data == sample_template
        assert template_editor_edit.name_edit.text() == "测试模板"
        assert template_editor_edit.category_combo.currentText() == "商务"

    def test_ui_components(self, template_editor):
        """测试UI组件"""
        # 基本信息
        assert hasattr(template_editor, "name_edit")
        assert hasattr(template_editor, "category_combo")
        assert template_editor.category_combo.count() == len(
            TemplateConstants().CATEGORIES
        )

        # 二维码设置
        assert hasattr(template_editor, "type_combo")
        assert hasattr(template_editor, "size_spin")
        assert hasattr(template_editor, "border_spin")
        assert hasattr(template_editor, "ec_combo")

        # Logo设置
        assert hasattr(template_editor, "logo_check")
        assert hasattr(template_editor, "logo_path_edit")
        assert hasattr(template_editor, "logo_browse_btn")
        assert hasattr(template_editor, "logo_clear_btn")
        assert hasattr(template_editor, "logo_scale_spin")
        assert hasattr(template_editor, "logo_scale_slider")

        # 颜色设置
        assert hasattr(template_editor, "foreground_picker")
        assert hasattr(template_editor, "gradient_check")
        assert hasattr(template_editor, "gradient_start_picker")
        assert hasattr(template_editor, "gradient_end_picker")
        assert hasattr(template_editor, "gradient_type_combo")


class TestTemplateEditorLoadData:
    """测试加载模板数据"""

    def test_load_template_data_basic(self, template_editor, sample_template):
        """测试加载基本模板数据"""
        template_editor.load_template_data(sample_template)

        assert template_editor.name_edit.text() == "测试模板"
        assert template_editor.category_combo.currentText() == "商务"
        assert template_editor.size_spin.value() == 15
        assert template_editor.border_spin.value() == 3
        assert template_editor.ec_combo.currentIndex() == 3  # H

    def test_load_template_data_logo(self, template_editor, sample_template):
        """测试加载Logo设置"""
        template_editor.load_template_data(sample_template)

        assert template_editor.logo_check.isChecked() is True
        assert template_editor.logo_path_edit.text() == "/path/to/logo.png"
        assert template_editor.logo_scale_spin.value() == 25

    def test_load_template_data_gradient(self, template_editor, sample_template):
        """测试加载渐变设置"""
        template_editor.load_template_data(sample_template)

        assert template_editor.gradient_check.isChecked() is True
        assert template_editor.gradient_start_picker.get_color() == "#ff6b6b"
        assert template_editor.gradient_end_picker.get_color() == "#4ecdc4"
        assert template_editor.gradient_type_combo.currentIndex() == 0

    def test_load_template_data_no_logo(self, template_editor):
        """测试加载无Logo的模板"""
        template_data = {
            "name": "无Logo模板",
            "category": "通用",
            "config": {
                "type": "TEXT",
                "size": 10,
                "border": 4,
                "error_correction": "M",
                "color": "#000000",
            },
        }

        template_editor.load_template_data(template_data)

        assert template_editor.logo_check.isChecked() is False
        assert template_editor.logo_path_edit.text() == ""
        assert template_editor.logo_path_edit.isEnabled() is False

    def test_load_template_data_invalid_ec(self, template_editor):
        """测试加载无效纠错级别"""
        template_data = {
            "name": "测试",
            "category": "通用",
            "config": {
                "type": "TEXT",
                "size": 10,
                "border": 4,
                "error_correction": "X",  # 无效
                "color": "#000000",
            },
        }

        template_editor.load_template_data(template_data)
        # 应该使用默认值
        assert template_editor.ec_combo.currentIndex() == 3  # H


class TestTemplateEditorToggleFunctions:
    """测试切换功能"""

    def test_toggle_gradient_checked(self, template_editor):
        assert template_editor.gradient_container.isVisible() is False

        # 直接触发逻辑，而非依赖信号+事件循环
        template_editor.on_gradient_toggled(True)

        assert not template_editor.gradient_container.isHidden()

    def test_toggle_gradient_unchecked(self, template_editor):
        """测试禁用渐变"""
        from PySide6.QtCore import QCoreApplication

        # 强制设置为可见
        template_editor.gradient_container.setVisible(True)
        template_editor.gradient_container.show()
        template_editor.gradient_container.raise_()
        QCoreApplication.processEvents()

        # 验证可见
        assert not template_editor.gradient_container.isHidden()

        # 取消选中
        template_editor.gradient_check.setChecked(False)

        # 多次处理事件
        for _ in range(3):
            QCoreApplication.processEvents()

        template_editor.gradient_container.update()
        QCoreApplication.processEvents()

        assert template_editor.gradient_container.isVisible() is False

    def test_toggle_logo_settings_checked(self, template_editor):
        """测试启用Logo设置"""
        template_editor.logo_check.setChecked(True)
        template_editor.toggle_logo_settings(Qt.CheckState.Checked.value)

        assert template_editor.logo_path_edit.isEnabled() is True
        assert template_editor.logo_browse_btn.isEnabled() is True
        assert template_editor.logo_clear_btn.isEnabled() is True
        assert template_editor.logo_scale_spin.isEnabled() is True
        assert template_editor.logo_scale_slider.isEnabled() is True

    def test_toggle_logo_settings_unchecked(self, template_editor):
        """测试禁用Logo设置"""
        template_editor.logo_check.setChecked(False)
        template_editor.toggle_logo_settings(Qt.CheckState.Unchecked.value)

        assert template_editor.logo_path_edit.isEnabled() is False
        assert template_editor.logo_browse_btn.isEnabled() is False
        assert template_editor.logo_clear_btn.isEnabled() is False
        assert template_editor.logo_scale_spin.isEnabled() is False
        assert template_editor.logo_scale_slider.isEnabled() is False


class TestTemplateEditorLogoOperations:
    """测试Logo操作"""

    @patch("PySide6.QtWidgets.QFileDialog.getOpenFileName")
    def test_browse_logo(self, mock_file_dialog, template_editor):
        """测试浏览Logo文件"""
        # 启用Logo设置
        template_editor.logo_check.setChecked(True)
        template_editor.toggle_logo_settings(Qt.CheckState.Checked.value)

        mock_file_dialog.return_value = ("/path/to/logo.png", "PNG Files (*.png)")

        template_editor.browse_logo()

        assert template_editor.logo_path_edit.text() == "/path/to/logo.png"

    @patch("PySide6.QtWidgets.QFileDialog.getOpenFileName")
    def test_browse_logo_cancelled(self, mock_file_dialog, template_editor):
        """测试取消浏览Logo文件"""
        template_editor.logo_check.setChecked(True)
        template_editor.toggle_logo_settings(Qt.CheckState.Checked.value)

        mock_file_dialog.return_value = ("", "")

        template_editor.browse_logo()

        assert template_editor.logo_path_edit.text() == ""

    def test_clear_logo(self, template_editor):
        """测试清除Logo路径"""
        template_editor.logo_path_edit.setText("/path/to/logo.png")

        template_editor.clear_logo()

        assert template_editor.logo_path_edit.text() == ""


class TestTemplateEditorGetData:
    """测试获取模板数据"""

    def test_get_config_basic(self, template_editor):
        """测试获取基本配置"""
        template_editor.name_edit.setText("测试模板")
        template_editor.size_spin.setValue(12)
        template_editor.border_spin.setValue(2)
        template_editor.foreground_picker.set_color("#00FF00")

        config = template_editor.get_config()

        assert config["size"] == 12
        assert config["border"] == 2
        assert config["color"] == "#00ff00"
        assert "logo_path" not in config

    def test_get_config_with_logo(self, template_editor):
        """测试获取包含Logo的配置"""
        template_editor.logo_check.setChecked(True)
        template_editor.toggle_logo_settings(Qt.CheckState.Checked.value)
        template_editor.logo_path_edit.setText("/path/to/logo.png")
        template_editor.logo_scale_spin.setValue(30)

        config = template_editor.get_config()

        assert config["logo_path"] == "/path/to/logo.png"
        assert config["logo_scale"] == 0.3

    def test_get_config_with_gradient(self, template_editor):
        """测试获取包含渐变的配置"""
        # 设置渐变参数
        template_editor.gradient_check.setChecked(True)

        # 处理事件循环，确保信号被处理
        from PySide6.QtCore import QCoreApplication

        QCoreApplication.processEvents()

        template_editor.gradient_start_picker.set_color("#FF0000")
        template_editor.gradient_end_picker.set_color("#0000FF")
        template_editor.gradient_type_combo.setCurrentIndex(1)  # 径向渐变

        config = template_editor.get_config()

        assert "gradient" in config
        assert config["gradient"][0] == "#ff0000"
        assert config["gradient"][1] == "#0000ff"
        assert config["gradient_type"] == "radial"

    def test_get_config_logo_not_checked(self, template_editor):
        """测试Logo未勾选时不包含Logo配置"""
        template_editor.logo_check.setChecked(False)
        template_editor.toggle_logo_settings(Qt.CheckState.Unchecked.value)
        template_editor.logo_path_edit.setText("/path/to/logo.png")

        config = template_editor.get_config()

        assert "logo_path" not in config
        assert "logo_scale" not in config

    def test_get_config_logo_path_empty(self, template_editor):
        """测试Logo路径为空时不包含Logo配置"""
        template_editor.logo_check.setChecked(True)
        template_editor.toggle_logo_settings(Qt.CheckState.Checked.value)
        template_editor.logo_path_edit.clear()

        config = template_editor.get_config()

        assert "logo_path" not in config
        assert "logo_scale" not in config

    def test_get_template_data(self, template_editor):
        """测试获取完整模板数据"""
        template_editor.name_edit.setText("完整模板")
        template_editor.category_combo.setCurrentText("商务")
        template_editor.size_spin.setValue(15)

        template_data = template_editor.get_template_data()

        assert template_data["name"] == "完整模板"
        assert template_data["category"] == "商务"
        assert "config" in template_data
        assert template_data["config"]["size"] == 15


class TestTemplateEditorValidation:
    """测试数据验证"""

    @patch("gui.template_editor.QMessageBox.warning")
    def test_validate_and_accept_empty_name(self, mock_warning, template_editor):
        """测试空名称验证"""
        template_editor.name_edit.clear()

        with patch.object(template_editor, "accept") as mock_accept:
            template_editor.validate_and_accept()

            mock_warning.assert_called_once()
            mock_accept.assert_not_called()

    @patch("gui.template_editor.QMessageBox.warning")
    def test_validate_and_accept_valid(self, mock_warning, template_editor):
        """测试有效数据验证"""
        template_editor.name_edit.setText("有效模板")

        with patch.object(template_editor, "accept") as mock_accept:
            template_editor.validate_and_accept()

            mock_warning.assert_not_called()
            mock_accept.assert_called_once()

    @patch("gui.template_editor.QMessageBox.warning")
    def test_validate_and_accept_invalid_config(self, mock_warning, template_editor):
        """测试无效配置验证"""
        template_editor.name_edit.setText("测试模板")

        # 模拟get_config返回空字典
        with patch.object(template_editor, "get_config", return_value={}):
            with patch.object(template_editor, "accept") as mock_accept:
                template_editor.validate_and_accept()

                mock_warning.assert_called_once()
                mock_accept.assert_not_called()


class TestTemplateEditorConnections:
    """测试信号连接"""

    def test_logo_scale_connections(self, template_editor):
        """测试Logo缩放比例信号连接"""
        # 测试滑块和数字输入框的双向绑定
        template_editor.logo_scale_spin.setValue(35)
        assert template_editor.logo_scale_slider.value() == 35

        template_editor.logo_scale_slider.setValue(40)
        assert template_editor.logo_scale_spin.value() == 40

    def test_gradient_check_connection(self, template_editor):
        assert template_editor.gradient_container.isHidden() is True  # 初始隐藏

        template_editor.gradient_check.setChecked(True)

        assert not template_editor.gradient_container.isHidden()

    def test_logo_check_connection(self, template_editor):
        """测试Logo复选框信号连接"""
        template_editor.logo_check.setChecked(True)
        template_editor.toggle_logo_settings(Qt.CheckState.Checked.value)
        assert template_editor.logo_path_edit.isEnabled() is True

        template_editor.logo_check.setChecked(False)
        template_editor.toggle_logo_settings(Qt.CheckState.Unchecked.value)
        assert template_editor.logo_path_edit.isEnabled() is False


class TestTemplateEditorRepr:
    """测试字符串表示"""

    def test_repr_new(self, template_editor):
        """测试新建模式字符串表示"""
        template_editor.template_data = None
        repr_str = repr(template_editor)
        assert "TemplateEditor" in repr_str
        assert "mode='新建'" in repr_str

    def test_repr_edit(self, template_editor_edit):
        """测试编辑模式字符串表示"""
        repr_str = repr(template_editor_edit)
        assert "TemplateEditor" in repr_str
        assert "mode='编辑'" in repr_str
