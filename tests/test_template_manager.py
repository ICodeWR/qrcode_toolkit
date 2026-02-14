#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模板管理器模块单元测试

模块名称：test_template_manager.py
功能描述：测试 TemplateManager 对话框的各项功能
"""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, Mock, call, patch

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QDialog, QListWidgetItem, QMessageBox

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from gui.template_manager import TemplateManager


@pytest.fixture(scope="session")
def qapp():
    """创建QApplication实例（会话级）"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


@pytest.fixture
def template_manager(qapp):
    """创建TemplateManager实例"""
    with patch("gui.template_manager.QRCodeDatabase") as mock_db_class:
        # 模拟数据库
        mock_db = MagicMock()
        mock_db.get_templates.return_value = []
        mock_db_class.return_value = mock_db

        # 创建 manager 实例 - 此时不 mock TemplateEditor
        manager = TemplateManager()
        manager.database = mock_db

        yield manager
        manager.close()


@pytest.fixture
def sample_templates():
    """创建示例模板列表"""
    return [
        {
            "id": 1,
            "name": "网站模板",
            "category": "网络",
            "config": {
                "type": "URL",
                "size": 10,
                "border": 4,
                "error_correction": "H",
                "color": "#1a73e8",
            },
            "created_at": "2026-02-12 10:00:00",
        },
        {
            "id": 2,
            "name": "WiFi模板",
            "category": "网络",
            "config": {
                "type": "WIFI",
                "size": 12,
                "border": 2,
                "error_correction": "H",
                "color": "#34a853",
            },
            "created_at": "2026-02-12 11:00:00",
        },
        {
            "id": 3,
            "name": "名片模板",
            "category": "商务",
            "config": {
                "type": "VCARD",
                "size": 15,
                "border": 4,
                "error_correction": "H",
                "color": "#ea4335",
                "logo_path": "/path/to/logo.png",
                "logo_scale": 0.2,
            },
            "created_at": "2026-02-12 12:00:00",
        },
    ]


class TestTemplateManagerInit:
    """测试TemplateManager初始化"""

    def test_initialization(self, template_manager):
        """测试初始化"""
        assert template_manager.windowTitle() == "模板管理器"
        assert template_manager.current_template is None
        assert hasattr(template_manager, "template_list")
        assert hasattr(template_manager, "search_edit")
        assert hasattr(template_manager, "name_label")
        assert hasattr(template_manager, "category_label")
        assert hasattr(template_manager, "config_text")

    def test_initial_button_states(self, template_manager):
        """测试初始按钮状态"""
        assert template_manager.new_btn.isEnabled() is True
        assert template_manager.edit_btn.isEnabled() is False
        assert template_manager.delete_btn.isEnabled() is False
        assert template_manager.apply_btn.isEnabled() is False

    def test_load_templates(self, template_manager, sample_templates):
        """测试加载模板列表"""
        template_manager.database.get_templates.return_value = sample_templates

        template_manager.load_templates()

        assert template_manager.template_list.count() == 3

        # 验证第一个模板
        first_item = template_manager.template_list.item(0)
        assert first_item.text() == "网站模板"
        assert first_item.data(Qt.ItemDataRole.UserRole) == 1
        assert "分类: 网络" in first_item.toolTip()

    @patch("gui.template_manager.TemplateManager._create_default_templates")
    def test_load_templates_empty(self, mock_create_default, template_manager):
        """测试加载空模板列表"""
        template_manager.database.get_templates.return_value = []

        template_manager.load_templates()

        mock_create_default.assert_called_once()

    def test_create_default_templates(self, template_manager):
        """测试创建默认模板"""
        template_manager.database.save_template = MagicMock()

        # 模拟 load_templates 方法
        template_manager.load_templates = MagicMock()

        template_manager._create_default_templates()

        # 验证保存了多个默认模板
        assert template_manager.database.save_template.call_count >= 7
        # _create_default_templates 现在不应该调用 load_templates()
        template_manager.load_templates.assert_not_called()


class TestTemplateManagerSelection:
    """测试模板选择功能"""

    def test_on_template_selected(self, template_manager, sample_templates):
        """测试选择模板"""
        # 准备
        template_manager.database.get_template.return_value = sample_templates[0]

        # 创建模拟项
        item = QListWidgetItem("网站模板")
        item.setData(Qt.ItemDataRole.UserRole, 1)

        # 执行
        template_manager.on_template_selected(item)

        # 验证
        assert template_manager.current_template == sample_templates[0]
        assert template_manager.name_label.text() == "网站模板"
        assert template_manager.category_label.text() == "网络"
        assert template_manager.edit_btn.isEnabled() is True
        assert template_manager.delete_btn.isEnabled() is True
        assert template_manager.apply_btn.isEnabled() is True

        # 验证配置预览
        assert "类型: URL" in template_manager.config_text.text()

    def test_on_template_selected_with_logo(self, template_manager, sample_templates):
        """测试选择带Logo的模板"""
        template_manager.database.get_template.return_value = sample_templates[2]

        item = QListWidgetItem("名片模板")
        item.setData(Qt.ItemDataRole.UserRole, 3)

        template_manager.on_template_selected(item)

        config_text = template_manager.config_text.text()
        assert "Logo: logo.png..." in config_text
        assert "Logo缩放: 20%" in config_text

    def test_clear_details(self, template_manager):
        """测试清除详情显示"""
        template_manager.name_label.setText("测试")
        template_manager.category_label.setText("测试")
        template_manager.config_text.setText("测试")
        template_manager.edit_btn.setEnabled(True)
        template_manager.delete_btn.setEnabled(True)
        template_manager.apply_btn.setEnabled(True)

        template_manager.clear_details()

        assert template_manager.name_label.text() == ""
        assert template_manager.category_label.text() == ""
        assert template_manager.config_text.text() == ""
        assert template_manager.edit_btn.isEnabled() is False
        assert template_manager.delete_btn.isEnabled() is False
        assert template_manager.apply_btn.isEnabled() is False

    def test_filter_templates(self, template_manager, sample_templates):
        """测试过滤模板列表"""
        # 加载模板
        template_manager.database.get_templates.return_value = sample_templates
        template_manager.load_templates()

        # 过滤
        template_manager.filter_templates("网站")

        # 验证
        assert template_manager.template_list.item(0).isHidden() is False
        assert template_manager.template_list.item(1).isHidden() is True
        assert template_manager.template_list.item(2).isHidden() is True

    def test_filter_templates_no_match(self, template_manager, sample_templates):
        """测试过滤无匹配"""
        template_manager.database.get_templates.return_value = sample_templates
        template_manager.load_templates()

        template_manager.filter_templates("不存在")

        for i in range(template_manager.template_list.count()):
            assert template_manager.template_list.item(i).isHidden() is True


class TestTemplateManagerOperations:
    """测试模板操作"""

    def test_new_template_accepted(self, template_manager):
        """测试新建模板（接受）"""
        # 清除默认模板调用记录
        template_manager.database.save_template.reset_mock()

        # 在方法内部使用 patch，模拟 TemplateEditor
        with patch("gui.template_manager.TemplateEditor") as mock_editor_class:
            # 创建并设置 mock_editor
            mock_editor = MagicMock()
            mock_editor.exec.return_value = QDialog.DialogCode.Accepted
            mock_editor.get_template_data.return_value = {
                "name": "新模板",
                "category": "通用",
                "config": {"type": "TEXT", "size": 10},
            }

            # 设置 TemplateEditor 类的返回值
            mock_editor_class.return_value = mock_editor

            # 模拟数据库保存成功
            template_manager.database.save_template.return_value = True

            with patch.object(template_manager, "load_templates") as mock_load:
                with patch("gui.template_manager.QMessageBox.information") as mock_info:
                    template_manager.new_template()

                    mock_editor.exec.assert_called_once()
                    template_manager.database.save_template.assert_called_once_with(
                        "新模板", {"type": "TEXT", "size": 10}, "通用"
                    )
                    mock_load.assert_called_once()
                    mock_info.assert_called_once()

    def test_new_template_rejected(self, template_manager):
        """测试新建模板（拒绝）"""
        # 清除默认模板调用记录
        template_manager.database.save_template.reset_mock()

        with patch("gui.template_manager.TemplateEditor") as mock_editor_class:
            # 创建并设置 mock_editor
            mock_editor = MagicMock()
            mock_editor.exec.return_value = QDialog.DialogCode.Rejected

            # 设置 TemplateEditor 类的返回值
            mock_editor_class.return_value = mock_editor

            with patch.object(template_manager, "load_templates") as mock_load:
                template_manager.new_template()

                mock_editor.exec.assert_called_once()
                template_manager.database.save_template.assert_not_called()
                mock_load.assert_not_called()

    def test_new_template_save_failed(self, template_manager):
        """测试新建模板保存失败"""
        # 清除默认模板调用记录
        template_manager.database.save_template.reset_mock()

        with patch("gui.template_manager.TemplateEditor") as mock_editor_class:
            # 创建并设置 mock_editor
            mock_editor = MagicMock()
            mock_editor.exec.return_value = QDialog.DialogCode.Accepted
            mock_editor.get_template_data.return_value = {
                "name": "新模板",
                "category": "通用",
                "config": {},
            }

            # 设置 TemplateEditor 类的返回值
            mock_editor_class.return_value = mock_editor

            template_manager.database.save_template.return_value = False

            with patch("gui.template_manager.QMessageBox.critical") as mock_critical:
                template_manager.new_template()

                template_manager.database.save_template.assert_called_once()
                mock_critical.assert_called_once()

    def test_edit_template(self, template_manager, sample_templates):
        """测试编辑模板"""
        # 设置当前模板
        template_manager.current_template = sample_templates[0]

        # 清除默认模板调用记录
        template_manager.database.save_template.reset_mock()
        template_manager.database.delete_template.reset_mock()

        with patch("gui.template_manager.TemplateEditor") as mock_editor_class:
            # 创建并设置 mock_editor
            mock_editor = MagicMock()
            mock_editor.exec.return_value = QDialog.DialogCode.Accepted
            mock_editor.get_template_data.return_value = {
                "name": "编辑后的模板",
                "category": "商务",
                "config": {"type": "URL", "size": 20},
            }

            # 设置 TemplateEditor 类的返回值
            mock_editor_class.return_value = mock_editor

            # 模拟数据库操作
            template_manager.database.delete_template.return_value = True
            template_manager.database.save_template.return_value = True

            with patch.object(template_manager, "load_templates") as mock_load:
                with patch.object(template_manager, "clear_details") as mock_clear:
                    with patch(
                        "gui.template_manager.QMessageBox.information"
                    ) as mock_info:
                        template_manager.edit_template()

                        template_manager.database.delete_template.assert_called_once_with(
                            1
                        )
                        template_manager.database.save_template.assert_called_once_with(
                            "编辑后的模板", {"type": "URL", "size": 20}, "商务"
                        )
                        mock_load.assert_called_once()
                        mock_clear.assert_called_once()
                        mock_info.assert_called_once()

    def test_edit_template_no_current(self, template_manager):
        """测试无当前模板时编辑"""
        template_manager.current_template = None

        with patch.object(template_manager, "load_templates") as mock_load:
            template_manager.edit_template()
            mock_load.assert_not_called()

    @patch("gui.template_manager.QMessageBox.question")
    def test_delete_template_yes(
        self, mock_question, template_manager, sample_templates
    ):
        """测试删除模板（确认）"""
        template_manager.current_template = sample_templates[0]
        mock_question.return_value = QMessageBox.StandardButton.Yes
        template_manager.database.delete_template.return_value = True

        with patch.object(template_manager, "load_templates") as mock_load:
            with patch.object(template_manager, "clear_details") as mock_clear:
                with patch("gui.template_manager.QMessageBox.information") as mock_info:
                    template_manager.delete_template()

                    template_manager.database.delete_template.assert_called_once_with(1)
                    mock_load.assert_called_once()
                    mock_clear.assert_called_once()
                    mock_info.assert_called_once()

    @patch("gui.template_manager.QMessageBox.question")
    def test_delete_template_no(
        self, mock_question, template_manager, sample_templates
    ):
        """测试删除模板（取消）"""
        template_manager.current_template = sample_templates[0]
        mock_question.return_value = QMessageBox.StandardButton.No

        with patch.object(template_manager, "load_templates") as mock_load:
            template_manager.delete_template()

            template_manager.database.delete_template.assert_not_called()
            mock_load.assert_not_called()

    def test_apply_template(self, template_manager, sample_templates):
        """测试应用模板"""
        template_manager.current_template = sample_templates[0]

        with patch.object(template_manager, "template_selected") as mock_signal:
            with patch.object(template_manager, "accept") as mock_accept:
                template_manager.apply_template()

                mock_signal.emit.assert_called_once_with(sample_templates[0])
                mock_accept.assert_called_once()

    def test_apply_template_no_current(self, template_manager):
        """测试无当前模板时应用"""
        template_manager.current_template = None

        with patch.object(template_manager, "template_selected") as mock_signal:
            with patch.object(template_manager, "accept") as mock_accept:
                template_manager.apply_template()

                mock_signal.emit.assert_not_called()
                mock_accept.assert_not_called()


class TestTemplateManagerDoubleClick:
    """测试双击事件"""

    def test_on_template_double_clicked(self, template_manager, sample_templates):
        """测试模板双击"""
        # 准备
        template_manager.database.get_template.return_value = sample_templates[0]

        item = QListWidgetItem("网站模板")
        item.setData(Qt.ItemDataRole.UserRole, 1)

        with patch.object(template_manager, "on_template_selected") as mock_select:
            with patch.object(template_manager, "apply_template") as mock_apply:
                template_manager.on_template_double_clicked(item)

                mock_select.assert_called_once_with(item)
                mock_apply.assert_called_once()


class TestTemplateManagerFormatConfig:
    """测试配置预览格式化"""

    def test_format_config_preview_basic(self, template_manager):
        """测试基本配置格式化"""
        config = {
            "type": "URL",
            "size": 10,
            "border": 4,
            "error_correction": "H",
            "color": "#1a73e8",
        }

        preview = template_manager._format_config_preview(config)

        assert "类型: URL" in preview
        assert "大小: 10" in preview
        assert "边框: 4" in preview
        assert "纠错: 高(30%)" in preview
        assert "颜色: #1a73e8" in preview

    def test_format_config_preview_with_logo(self, template_manager):
        """测试包含Logo的配置格式化"""
        config = {
            "type": "VCARD",
            "size": 15,
            "logo_path": "/path/to/company_logo.png",
            "logo_scale": 0.25,
        }

        preview = template_manager._format_config_preview(config)

        assert "Logo: company_logo.png..." in preview
        assert "Logo缩放: 25%" in preview

    def test_format_config_preview_with_gradient(self, template_manager):
        """测试包含渐变的配置格式化"""
        config = {"type": "TEXT", "gradient": ["#FF0000", "#0000FF"]}

        preview = template_manager._format_config_preview(config)

        assert "渐变: #FF0000 → #0000FF" in preview

    def test_format_config_preview_ec_mapping(self, template_manager):
        """测试纠错级别映射"""
        ec_map = {"L": "低(7%)", "M": "中(15%)", "Q": "较高(25%)", "H": "高(30%)"}

        for code, text in ec_map.items():
            config = {"error_correction": code}
            preview = template_manager._format_config_preview(config)
            assert f"纠错: {text}" in preview

    def test_format_config_preview_invalid_ec(self, template_manager):
        """测试无效纠错级别"""
        config = {"error_correction": "X"}
        preview = template_manager._format_config_preview(config)
        assert "纠错: X" in preview


class TestTemplateManagerCloseEvent:
    """测试关闭事件"""

    def test_close_event(self, template_manager):
        """测试关闭事件"""
        event = MagicMock()

        # 直接测试 closeEvent 方法
        template_manager.closeEvent(event)

        event.accept.assert_called_once()


class TestTemplateManagerRepr:
    """测试字符串表示"""

    def test_repr(self, template_manager):
        """测试字符串表示"""
        template_manager.template_list.count = MagicMock(return_value=5)

        repr_str = repr(template_manager)

        assert "TemplateManager" in repr_str
        assert "templates=5" in repr_str
