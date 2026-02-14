#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模板编辑器模块 - QR Toolkit的模板编辑对话框

模块名称：template_editor.py
功能描述：提供模板的创建和编辑功能
作者：码上工坊
联系：微信公众号（码上工坊）
版权声明：Copyright (c) 2026 码上工坊
开源协议：MIT License
免责声明：本软件按"原样"提供，不作任何明示或暗示的担保
修改记录：
版本 0.9.0 2026-01-01 - 码上工坊 - 初始版本创建
"""

from typing import Dict, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from core.models import QRCodeType
from gui.widgets import ColorPickerButton
from utils import TemplateConstants


class TemplateEditor(QDialog):
    """模板编辑器对话框"""

    def __init__(self, parent=None, template_data: Optional[Dict] = None) -> None:
        """
        初始化模板编辑器

        Args:
            parent: 父窗口
            template_data: 模板数据（编辑时传入）
        """
        super().__init__(parent)

        # 设置窗口属性
        self.setWindowTitle("编辑模板" if template_data else "新建模板")
        self.setMinimumWidth(500)

        # 模板数据
        self.template_data = template_data

        # 初始化UI
        self.init_ui()

        # 确保渐变部件初始状态正确
        if hasattr(self, "gradient_container"):
            self.gradient_container.setVisible(False)
            print(
                f"Initial gradient_container visibility: {self.gradient_container.isVisible()}"
            )

        # 如果是编辑模式，加载数据
        if template_data:
            self.load_template_data(template_data)

    def init_ui(self) -> None:
        """初始化用户界面"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)

        # 基本信息区域
        basic_group = QGroupBox("基本信息")
        basic_layout = QFormLayout()

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("输入模板名称")

        self.category_combo = QComboBox()
        self.category_combo.addItems(TemplateConstants().CATEGORIES)
        self.category_combo.setCurrentText("通用")

        basic_layout.addRow("名称:", self.name_edit)
        basic_layout.addRow("分类:", self.category_combo)
        basic_group.setLayout(basic_layout)

        # 二维码设置区域
        qrcode_group = QGroupBox("二维码设置")
        qrcode_layout = QFormLayout()

        # 类型选择
        self.type_combo = QComboBox()
        for qr_type in QRCodeType:
            self.type_combo.addItem(qr_type.value, qr_type)
        qrcode_layout.addRow("类型:", self.type_combo)

        # 大小设置
        size_layout = QHBoxLayout()
        self.size_spin = QSpinBox()
        self.size_spin.setRange(1, 50)
        self.size_spin.setValue(10)
        self.size_spin.setSuffix(" px")
        size_layout.addWidget(self.size_spin)
        size_layout.addStretch()
        qrcode_layout.addRow("模块大小:", size_layout)

        # 边框设置
        border_layout = QHBoxLayout()
        self.border_spin = QSpinBox()
        self.border_spin.setRange(0, 10)
        self.border_spin.setValue(4)
        border_layout.addWidget(self.border_spin)
        border_layout.addStretch()
        qrcode_layout.addRow("边框大小:", border_layout)

        # 纠错级别
        self.ec_combo = QComboBox()
        self.ec_combo.addItems(["L (7%)", "M (15%)", "Q (25%)", "H (30%)"])
        self.ec_combo.setCurrentIndex(3)  # 默认H
        qrcode_layout.addRow("纠错级别:", self.ec_combo)

        qrcode_group.setLayout(qrcode_layout)

        # Logo设置区域
        logo_group = QGroupBox("Logo设置")
        logo_layout = QVBoxLayout()

        # Logo路径（模板中只存储路径，不存储实际图片）
        self.logo_check = QCheckBox("包含Logo设置")
        self.logo_check.setChecked(False)
        self.logo_check.stateChanged.connect(self.toggle_logo_settings)

        # Logo设置面板
        logo_settings_widget = QWidget()
        logo_settings_layout = QVBoxLayout(logo_settings_widget)

        # Logo路径输入
        logo_path_layout = QHBoxLayout()
        self.logo_path_edit = QLineEdit()
        self.logo_path_edit.setPlaceholderText(
            "Logo图片路径（保存时存储，应用时需重新选择）"
        )
        self.logo_path_edit.setEnabled(False)
        self.logo_browse_btn = QPushButton("浏览...")
        self.logo_browse_btn.setEnabled(False)
        self.logo_clear_btn = QPushButton("清除")
        self.logo_clear_btn.setEnabled(False)

        logo_path_layout.addWidget(self.logo_path_edit)
        logo_path_layout.addWidget(self.logo_browse_btn)
        logo_path_layout.addWidget(self.logo_clear_btn)

        # Logo缩放比例
        logo_scale_layout = QHBoxLayout()
        logo_scale_layout.addWidget(QLabel("缩放比例:"))

        self.logo_scale_spin = QSpinBox()
        self.logo_scale_spin.setRange(5, 50)
        self.logo_scale_spin.setValue(20)
        self.logo_scale_spin.setSuffix("%")
        self.logo_scale_spin.setEnabled(False)

        self.logo_scale_slider = QSlider(Qt.Orientation.Horizontal)
        self.logo_scale_slider.setRange(5, 50)
        self.logo_scale_slider.setValue(20)
        self.logo_scale_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.logo_scale_slider.setTickInterval(5)
        self.logo_scale_slider.setEnabled(False)

        # 连接滑块和数字输入框
        self.logo_scale_spin.valueChanged.connect(self.logo_scale_slider.setValue)
        self.logo_scale_slider.valueChanged.connect(self.logo_scale_spin.setValue)

        logo_scale_layout.addWidget(self.logo_scale_spin)
        logo_scale_layout.addWidget(self.logo_scale_slider, 1)

        # Logo提示
        logo_hint_label = QLabel(
            "提示：Logo路径仅在当前环境有效，应用模板时需重新选择Logo文件"
        )
        logo_hint_label.setStyleSheet("color: #666; font-size: 11px;")
        logo_hint_label.setWordWrap(True)

        logo_settings_layout.addLayout(logo_path_layout)
        logo_settings_layout.addLayout(logo_scale_layout)
        logo_settings_layout.addWidget(logo_hint_label)

        logo_layout.addWidget(self.logo_check)
        logo_layout.addWidget(logo_settings_widget)
        logo_group.setLayout(logo_layout)

        # 连接Logo按钮
        self.logo_browse_btn.clicked.connect(self.browse_logo)
        self.logo_clear_btn.clicked.connect(self.clear_logo)

        # 颜色设置区域
        color_group = QGroupBox("颜色设置")
        color_layout = QVBoxLayout(color_group)

        # 前景色
        foreground_layout = QHBoxLayout()
        foreground_layout.addWidget(QLabel("前景色:"))
        self.foreground_picker = ColorPickerButton("#000000")
        foreground_layout.addWidget(self.foreground_picker)
        foreground_layout.addStretch()
        color_layout.addLayout(foreground_layout)

        # 渐变设置
        self.gradient_check = QCheckBox("启用渐变")
        color_layout.addWidget(self.gradient_check)

        # 渐变颜色选择器 - 使用QFrame替代QWidget以获得更好的样式控制

        self.gradient_container = QFrame()
        self.gradient_container.setFrameShape(QFrame.Shape.NoFrame)
        self.gradient_container.setVisible(False)  # 初始隐藏

        # 容器内部布局
        container_layout = QVBoxLayout(self.gradient_container)
        container_layout.setContentsMargins(0, 0, 0, 0)

        # 渐变表单布局
        gradient_form_layout = QFormLayout()
        self.gradient_start_picker = ColorPickerButton("#FF6B6B")
        gradient_form_layout.addRow("起始色:", self.gradient_start_picker)
        self.gradient_end_picker = ColorPickerButton("#4ECDC4")
        gradient_form_layout.addRow("结束色:", self.gradient_end_picker)
        self.gradient_type_combo = QComboBox()
        self.gradient_type_combo.addItems(["线性渐变", "径向渐变"])
        gradient_form_layout.addRow("渐变类型:", self.gradient_type_combo)

        container_layout.addLayout(gradient_form_layout)

        # 只添加一次 gradient_container
        color_layout.addWidget(self.gradient_container)
        color_layout.addStretch()

        # 连接信号 - 使用清晰的类方法
        self.gradient_check.toggled.connect(self.on_gradient_toggled)

        color_group.setLayout(color_layout)

        # 按钮区域
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.validate_and_accept)
        button_box.rejected.connect(self.reject)

        # 添加到主布局
        main_layout.addWidget(basic_group)
        main_layout.addWidget(qrcode_group)
        main_layout.addWidget(logo_group)
        main_layout.addWidget(color_group)
        main_layout.addWidget(button_box)

    def on_gradient_toggled(self, checked: bool) -> None:
        """响应渐变复选框的切换，控制渐变容器的可见性"""
        self.gradient_container.setVisible(checked)

    def load_template_data(self, template_data: Dict) -> None:
        """加载模板数据到界面"""
        # 基本信息
        self.name_edit.setText(template_data.get("name", ""))

        category = template_data.get("category", "通用")
        index = self.category_combo.findText(category)
        if index >= 0:
            self.category_combo.setCurrentIndex(index)

        # 二维码设置
        config = template_data.get("config", {})

        # 类型
        qr_type = config.get("type", "TEXT")
        for i in range(self.type_combo.count()):
            if self.type_combo.itemText(i) == qr_type:
                self.type_combo.setCurrentIndex(i)
                break

        # 大小和边框
        self.size_spin.setValue(config.get("size", 10))
        self.border_spin.setValue(config.get("border", 4))

        # 纠错级别
        error_correction = config.get("error_correction", "H")
        ec_index = {"L": 0, "M": 1, "Q": 2, "H": 3}.get(error_correction, 3)
        self.ec_combo.setCurrentIndex(ec_index)

        # 加载Logo设置
        logo_path = config.get("logo_path")
        logo_scale = config.get("logo_scale", 0.2)

        if logo_path:
            self.logo_check.setChecked(True)
            self.logo_path_edit.setText(logo_path)
            # 转换为百分比
            scale_percent = (
                int(logo_scale * 100) if logo_scale <= 1 else int(logo_scale)
            )
            self.logo_scale_spin.setValue(scale_percent)
            self.logo_scale_slider.setValue(scale_percent)
        else:
            self.logo_check.setChecked(False)

        # 颜色设置
        color = config.get("color", "#000000")
        self.foreground_picker.set_color(color)

        # 渐变设置
        gradient = config.get("gradient")
        if gradient and len(gradient) == 2:
            self.gradient_check.setChecked(True)
            self.gradient_start_picker.set_color(gradient[0])
            self.gradient_end_picker.set_color(gradient[1])

            # 渐变类型（如果有）
            gradient_type = config.get("gradient_type", "linear")
            self.gradient_type_combo.setCurrentIndex(
                0 if gradient_type == "linear" else 1
            )
        else:
            self.gradient_check.setChecked(False)

    def toggle_logo_settings(self, state: int) -> None:
        """切换Logo设置的启用状态"""
        is_enabled = state == Qt.CheckState.Checked.value
        self.logo_path_edit.setEnabled(is_enabled)
        self.logo_browse_btn.setEnabled(is_enabled)
        self.logo_clear_btn.setEnabled(is_enabled)
        self.logo_scale_spin.setEnabled(is_enabled)
        self.logo_scale_slider.setEnabled(is_enabled)

    def browse_logo(self) -> None:
        """浏览Logo文件"""
        from PySide6.QtWidgets import QFileDialog

        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择Logo图片", "", "图片文件 (*.png *.jpg *.jpeg *.bmp *.gif)"
        )

        if file_path:
            self.logo_path_edit.setText(file_path)

    def clear_logo(self) -> None:
        """清除Logo路径"""
        self.logo_path_edit.clear()

    def validate_and_accept(self) -> None:
        """验证数据并接受对话框"""
        # 验证名称
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "警告", "请输入模板名称")
            self.name_edit.setFocus()
            return

        # 验证配置
        config = self.get_config()
        if not config:
            QMessageBox.warning(self, "警告", "模板配置无效")
            return

        self.accept()

    def get_template_data(self) -> Dict:
        """获取模板数据"""
        name = self.name_edit.text().strip()
        category = self.category_combo.currentText()
        config = self.get_config()

        return {"name": name, "category": category, "config": config}

    def get_config(self) -> Dict:
        """获取配置数据"""
        config = {
            "type": self.type_combo.currentText(),
            "size": self.size_spin.value(),
            "border": self.border_spin.value(),
            "error_correction": self.ec_combo.currentText()[0],  # 取第一个字符
            "color": self.foreground_picker.get_color(),
        }

        # 保存Logo设置
        if self.logo_check.isChecked() and self.logo_path_edit.text():
            config["logo_path"] = self.logo_path_edit.text()
            config["logo_scale"] = self.logo_scale_spin.value() / 100.0

        # 渐变设置
        if self.gradient_check.isChecked():
            config["gradient"] = [
                self.gradient_start_picker.get_color(),
                self.gradient_end_picker.get_color(),
            ]
            config["gradient_type"] = (
                "linear" if self.gradient_type_combo.currentIndex() == 0 else "radial"
            )

        return config

    def __repr__(self) -> str:
        """返回字符串表示"""
        mode = "编辑" if self.template_data else "新建"
        return f"TemplateEditor(mode='{mode}')"
