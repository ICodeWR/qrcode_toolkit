#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模板管理器模块 - QR Toolkit的模板管理对话框

模块名称：template_manager.py
功能描述：提供模板的创建、编辑、删除和应用功能
作者：码上工坊
联系：微信公众号（码上工坊）
版权声明：Copyright (c) 2026 码上工坊
开源协议：MIT License
免责声明：本软件按"原样"提供，不作任何明示或暗示的担保
修改记录：
版本 0.9.0 2026-02-11 - 码上工坊 - 初始版本创建
"""

from typing import Dict, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from core.database import QRCodeDatabase

from .template_editor import TemplateEditor


class TemplateManager(QDialog):
    """模板管理器对话框"""

    # 信号定义
    template_selected = Signal(dict)  # 模板选择信号

    def __init__(self, parent=None) -> None:
        """
        初始化模板管理器

        Args:
            parent: 父窗口
        """
        super().__init__(parent)

        # 设置窗口属性
        self.setWindowTitle("模板管理器")
        self.setMinimumSize(600, 500)

        # 初始化数据库
        self.database = QRCodeDatabase()

        # 当前选择的模板
        self.current_template: Optional[Dict] = None

        # 初始化UI
        self.init_ui()
        self.load_templates()

    def init_ui(self) -> None:
        """初始化用户界面"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)

        # 模板列表区域
        list_group = QGroupBox("模板列表")
        list_layout = QVBoxLayout()

        # 搜索框
        search_layout = QHBoxLayout()
        search_label = QLabel("搜索:")
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("输入模板名称...")
        self.search_edit.textChanged.connect(self.filter_templates)

        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_edit)
        search_layout.addStretch()

        # 模板列表
        self.template_list = QListWidget()
        self.template_list.setAlternatingRowColors(True)
        self.template_list.itemClicked.connect(self.on_template_selected)
        self.template_list.itemDoubleClicked.connect(self.on_template_double_clicked)

        list_layout.addLayout(search_layout)
        list_layout.addWidget(self.template_list)
        list_group.setLayout(list_layout)

        # 模板详情区域
        detail_group = QGroupBox("模板详情")
        detail_layout = QVBoxLayout()

        # 模板信息
        info_layout = QHBoxLayout()
        info_layout.addWidget(QLabel("名称:"))
        self.name_label = QLabel()
        info_layout.addWidget(self.name_label)
        info_layout.addStretch()

        info_layout.addWidget(QLabel("分类:"))
        self.category_label = QLabel()
        info_layout.addWidget(self.category_label)
        info_layout.addStretch()

        # 模板配置预览
        self.config_text = QLabel()
        self.config_text.setWordWrap(True)
        self.config_text.setMinimumHeight(120)
        self.config_text.setStyleSheet(
            """
            QLabel {
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                border-radius: 3px;
                padding: 5px;
            }
        """
        )

        detail_layout.addLayout(info_layout)
        detail_layout.addWidget(QLabel("配置预览:"))
        detail_layout.addWidget(self.config_text)
        detail_group.setLayout(detail_layout)

        # 按钮区域
        button_layout = QHBoxLayout()

        self.new_btn = QPushButton("新建")
        self.edit_btn = QPushButton("编辑")
        self.delete_btn = QPushButton("删除")
        self.apply_btn = QPushButton("应用")
        self.close_btn = QPushButton("关闭")

        self.new_btn.clicked.connect(self.new_template)
        self.edit_btn.clicked.connect(self.edit_template)
        self.delete_btn.clicked.connect(self.delete_template)
        self.apply_btn.clicked.connect(self.apply_template)
        self.close_btn.clicked.connect(self.reject)

        # 设置按钮状态
        self.edit_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)
        self.apply_btn.setEnabled(False)

        button_layout.addWidget(self.new_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.edit_btn)
        button_layout.addWidget(self.delete_btn)
        button_layout.addWidget(self.apply_btn)
        button_layout.addWidget(self.close_btn)

        # 添加到主布局
        main_layout.addWidget(list_group, 3)  # 3份高度
        main_layout.addWidget(detail_group, 2)  # 2份高度
        main_layout.addLayout(button_layout)

    def load_templates(self) -> None:
        """加载模板列表"""
        self.template_list.clear()

        # 从数据库获取模板
        templates = self.database.get_templates()

        for template in templates:
            item = QListWidgetItem(template["name"])
            item.setData(Qt.ItemDataRole.UserRole, template["id"])

            # 添加分类信息
            category = template.get("category", "未分类")
            item.setToolTip(
                f"分类: {category}\n创建时间: {template.get('created_at', '未知')}"
            )

            self.template_list.addItem(item)

        # 如果数据库中没有模板，添加一些默认模板
        if self.template_list.count() == 0:
            self._create_default_templates()
            # 注意：_create_default_templates 不应该再调用 load_templates()
            # 需要重新加载模板列表显示刚刚创建的默认模板
            templates = self.database.get_templates()
            for template in templates:
                item = QListWidgetItem(template["name"])
                item.setData(Qt.ItemDataRole.UserRole, template["id"])
                category = template.get("category", "未分类")
                item.setToolTip(
                    f"分类: {category}\n创建时间: {template.get('created_at', '未知')}"
                )
                self.template_list.addItem(item)

    def _create_default_templates(self) -> None:
        """创建默认模板"""
        default_templates = {
            "网站链接": {
                "type": "URL",
                "color": "#1a73e8",
                "size": 10,
                "border": 4,
                "error_correction": "H",
                "logo_scale": 0.2,
            },
            "WiFi": {
                "type": "WIFI",
                "color": "#34a853",
                "size": 12,
                "border": 2,
                "error_correction": "H",
                "logo_scale": 0.2,
            },
            "名片": {
                "type": "VCARD",
                "color": "#ea4335",
                "size": 15,
                "border": 4,
                "error_correction": "H",
                "logo_scale": 0.2,
            },
            "邮件": {
                "type": "EMAIL",
                "color": "#4285f4",
                "size": 10,
                "border": 3,
                "error_correction": "M",
                "logo_scale": 0.2,
            },
            "电话": {
                "type": "PHONE",
                "color": "#ea4335",
                "size": 10,
                "border": 4,
                "error_correction": "H",
                "logo_scale": 0.2,
            },
            "位置": {
                "type": "LOCATION",
                "color": "#fbbc05",
                "size": 12,
                "border": 3,
                "error_correction": "H",
                "logo_scale": 0.2,
            },
            "事件": {
                "type": "EVENT",
                "color": "#34a853",
                "size": 15,
                "border": 4,
                "error_correction": "H",
                "logo_scale": 0.2,
            },
            "文本": {
                "type": "TEXT",
                "color": "#000000",
                "size": 10,
                "border": 4,
                "error_correction": "L",
                "logo_scale": 0.2,
            },
        }

        for name, config in default_templates.items():
            self.database.save_template(name, config, "默认")

    def filter_templates(self, text: str) -> None:
        """过滤模板列表"""
        for i in range(self.template_list.count()):
            item = self.template_list.item(i)
            item.setHidden(text.lower() not in item.text().lower())

    def on_template_selected(self, item: QListWidgetItem) -> None:
        """处理模板选择"""
        template_id = item.data(Qt.ItemDataRole.UserRole)
        template = self.database.get_template(template_id)

        if template:
            self.current_template = template

            # 更新详情显示
            self.name_label.setText(template["name"])
            self.category_label.setText(template.get("category", "未分类"))

            # 格式化配置预览
            config = template["config"]
            config_text = self._format_config_preview(config)
            self.config_text.setText(config_text)

            # 启用按钮
            self.edit_btn.setEnabled(True)
            self.delete_btn.setEnabled(True)
            self.apply_btn.setEnabled(True)

    def on_template_double_clicked(self, item: QListWidgetItem) -> None:
        """处理模板双击（直接应用）"""
        self.on_template_selected(item)
        self.apply_template()

    def new_template(self) -> None:
        """创建新模板"""

        editor = TemplateEditor(self)
        if editor.exec() == QDialog.DialogCode.Accepted:
            template_data = editor.get_template_data()

            # 保存到数据库
            if self.database.save_template(
                template_data["name"],
                template_data["config"],
                template_data["category"],
            ):
                QMessageBox.information(self, "成功", "模板创建成功")
                self.load_templates()
            else:
                QMessageBox.critical(self, "错误", "模板保存失败")

    def edit_template(self) -> None:
        """编辑模板"""
        if not self.current_template:
            return

        editor = TemplateEditor(self, self.current_template)
        if editor.exec() == QDialog.DialogCode.Accepted:
            template_data = editor.get_template_data()

            # 删除旧模板，创建新模板（简化处理）
            self.database.delete_template(self.current_template["id"])

            if self.database.save_template(
                template_data["name"],
                template_data["config"],
                template_data["category"],
            ):
                QMessageBox.information(self, "成功", "模板修改成功")
                self.load_templates()
                self.current_template = None
                self.clear_details()
            else:
                QMessageBox.critical(self, "错误", "模板修改失败")

    def delete_template(self) -> None:
        """删除模板"""
        if not self.current_template:
            return

        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除模板 '{self.current_template['name']}' 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            if self.database.delete_template(self.current_template["id"]):
                QMessageBox.information(self, "成功", "模板删除成功")
                self.load_templates()
                self.current_template = None
                self.clear_details()
            else:
                QMessageBox.critical(self, "错误", "模板删除失败")

    def apply_template(self) -> None:
        """应用模板"""
        if self.current_template:
            self.template_selected.emit(self.current_template)
            self.accept()

    def clear_details(self) -> None:
        """清除详情显示"""
        self.name_label.clear()
        self.category_label.clear()
        self.config_text.clear()

        # 禁用按钮
        self.edit_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)
        self.apply_btn.setEnabled(False)

    def _format_config_preview(self, config: Dict) -> str:
        """格式化配置预览文本"""
        lines = []

        if "type" in config:
            lines.append(f"类型: {config['type']}")

        if "size" in config:
            lines.append(f"大小: {config['size']}")

        if "border" in config:
            lines.append(f"边框: {config['border']}")

        if "error_correction" in config:
            ec_map = {"L": "低(7%)", "M": "中(15%)", "Q": "较高(25%)", "H": "高(30%)"}
            lines.append(
                f"纠错: {ec_map.get(config['error_correction'], config['error_correction'])}"
            )

        if "color" in config:
            lines.append(f"颜色: {config['color']}")

        if "gradient" in config and config["gradient"]:
            lines.append(f"渐变: {config['gradient'][0]} → {config['gradient'][1]}")

        # 显示Logo设置预览
        if "logo_path" in config and config["logo_path"]:
            import os

            logo_name = os.path.basename(config["logo_path"])
            lines.append(f"Logo: {logo_name[:20]}...")

        if "logo_scale" in config:
            scale = config["logo_scale"]
            if isinstance(scale, float) and scale <= 1:
                scale_percent = int(scale * 100)
            else:
                scale_percent = int(scale)
            lines.append(f"Logo缩放: {scale_percent}%")

        return "\n".join(lines)

    def closeEvent(self, event) -> None:
        """关闭事件"""
        event.accept()

    def __repr__(self) -> str:
        """返回字符串表示"""
        return f"TemplateManager(templates={self.template_list.count()})"
