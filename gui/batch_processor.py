#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量处理器模块 - QR Toolkit的批量处理对话框

模块名称：batch_processor.py
功能描述：提供二维码的批量生成和批量扫描功能
作者：码上工坊
联系：微信公众号（码上工坊）
版权声明：Copyright (c) 2026 码上工坊
开源协议：MIT License
免责声明：本软件按"原样"提供，不作任何明示或暗示的担保
修改记录：
版本 0.9.0 2026-02-11 - 码上工坊 - 初始版本创建
"""

import csv
import os
import random
import time
from typing import Dict, List, Optional

import chardet
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSlider,
    QSpinBox,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from core.database import QRCodeDatabase
from core.engine import QRCodeEngine
from core.models import OutputFormat, QRCodeData, QRCodeType
from core.scanner import QRCodeBatchScanner
from utils import FileConstants


class BatchProcessor(QDialog):
    """批量处理器对话框"""

    # 信号定义
    batch_completed = Signal(str, int)  # 操作类型, 成功数量

    def __init__(self, parent=None) -> None:
        """
        初始化批量处理器

        Args:
            parent: 父窗口
        """
        super().__init__(parent)

        # 设置窗口属性
        self.setWindowTitle("批量处理器")
        self.setMinimumSize(800, 600)
        self.showMaximized()

        # 初始化组件
        self.database = QRCodeDatabase()
        self.qr_engine = QRCodeEngine()
        self.batch_scanner = QRCodeBatchScanner()

        # 当前任务
        self.current_task: Optional[str] = None
        self.is_processing = False

        # 批量生成相关
        self.batch_qr_list: List[QRCodeData] = []
        self.batch_total = 0
        self.batch_current = 0
        self.batch_successful = 0
        self.batch_failed = 0

        # 状态跟踪变量
        self._signals_connected = False  # 信号是否已连接
        self._batch_saved = False  # 是否已保存到数据库
        self._batch_saved_count = 0  # 已保存的记录数
        self._disconnecting = False  # 防重复断开保护
        self._saving_in_progress = False  # 防重复保存保护
        self._is_resetting = False  # 防重复重置保护

        # 初始化UI
        self.init_ui()
        self.init_connections()

    def init_ui(self) -> None:
        """初始化用户界面"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)

        # 1. 创建选项卡
        self.tab_widget = QTabWidget()

        # 批量生成选项卡
        self.generate_tab = self.create_batch_generate_tab()
        # 批量扫描选项卡
        self.scan_tab = self.create_batch_scan_tab()

        # 添加到选项卡
        self.tab_widget.addTab(self.generate_tab, "批量生成")
        self.tab_widget.addTab(self.scan_tab, "批量扫描")

        # 2. 创建进度区域控件
        progress_group = QGroupBox("进度")
        progress_layout = QVBoxLayout()

        self.progress_label = QLabel("就绪")
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #666; font-size: 11px;")
        self.progress_bar = QProgressBar()

        progress_layout.addWidget(self.progress_label)
        progress_layout.addWidget(self.status_label)
        progress_layout.addWidget(self.progress_bar)
        progress_group.setLayout(progress_layout)

        # 3. 创建控制按钮
        button_layout = QHBoxLayout()

        self.start_btn = QPushButton("开始")
        self.pause_btn = QPushButton("暂停")
        self.stop_btn = QPushButton("停止")
        self.close_btn = QPushButton("关闭")

        self.pause_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)

        button_layout.addWidget(self.start_btn)
        button_layout.addWidget(self.pause_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.stop_btn)
        button_layout.addWidget(self.close_btn)

        # 4. 组装布局
        main_layout.addWidget(self.tab_widget)
        main_layout.addWidget(progress_group)
        main_layout.addLayout(button_layout)

        # 5. 所有控件创建完成后，再连接信号
        self.tab_widget.currentChanged.connect(self._on_tab_changed)

        # 6. 初始化状态显示
        self._reset_progress_display()
        self.progress_label.setText("就绪 - 批量生成")
        self.status_label.setText("请选择CSV文件或输入文本数据")

    def create_batch_generate_tab(self) -> QWidget:
        """创建批量生成选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(10)

        # 数据源区域
        source_group = QGroupBox("数据源")
        source_layout = QVBoxLayout()

        # CSV文件导入
        csv_layout = QHBoxLayout()
        self.csv_path_edit = QLineEdit()
        self.csv_path_edit.setPlaceholderText("CSV文件路径")
        self.csv_browse_btn = QPushButton("浏览...")

        csv_layout.addWidget(self.csv_path_edit)
        csv_layout.addWidget(self.csv_browse_btn)

        source_layout.addLayout(csv_layout)

        # 文本数据输入
        self.data_text = QTextEdit()
        self.data_text.setPlaceholderText(
            "每行一个二维码数据，格式: 数据,标签1;标签2,备注"
        )
        self.data_text.setMaximumHeight(80)

        source_layout.addWidget(QLabel("或输入文本数据:"))
        source_layout.addWidget(self.data_text)

        source_group.setLayout(source_layout)

        # 输出设置区域
        output_group = QGroupBox("输出设置")
        output_layout = QVBoxLayout()

        # 输出目录
        dir_layout = QHBoxLayout()
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setPlaceholderText("输出目录（留空则在程序目录生成）")
        self.output_dir_browse_btn = QPushButton("浏览...")

        dir_layout.addWidget(self.output_dir_edit)
        dir_layout.addWidget(self.output_dir_browse_btn)

        output_layout.addLayout(dir_layout)

        # 文件名前缀
        prefix_layout = QHBoxLayout()
        prefix_layout.addWidget(QLabel("文件名前缀:"))
        self.filename_prefix_edit = QLineEdit()
        self.filename_prefix_edit.setText("qrcode_")
        prefix_layout.addWidget(self.filename_prefix_edit)
        prefix_layout.addStretch()

        output_layout.addLayout(prefix_layout)

        # 输出格式
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("输出格式:"))
        self.format_combo = QComboBox()
        for fmt in OutputFormat:
            self.format_combo.addItem(fmt.value, fmt)
        format_layout.addWidget(self.format_combo)
        format_layout.addStretch()

        output_layout.addLayout(format_layout)

        output_group.setLayout(output_layout)

        # 二维码设置区域
        qrcode_group = QGroupBox("二维码设置")
        qrcode_layout = QVBoxLayout()

        # 类型选择
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("类型:"))
        self.type_combo = QComboBox()
        for qr_type in QRCodeType:
            self.type_combo.addItem(qr_type.value, qr_type)
        type_layout.addWidget(self.type_combo)

        type_layout.addWidget(QLabel("大小:"))
        self.size_spin = QComboBox()
        self.size_spin.addItems(["10", "15", "20", "25", "30"])
        self.size_spin.setCurrentIndex(0)
        type_layout.addWidget(self.size_spin)

        type_layout.addWidget(QLabel("边框:"))
        self.border_spin = QComboBox()
        self.border_spin.addItems(["2", "4", "6", "8"])
        self.border_spin.setCurrentIndex(1)
        type_layout.addWidget(self.border_spin)

        # 颜色设置
        type_layout.addWidget(QLabel("前景色:"))
        self.foreground_combo = QComboBox()
        self.foreground_combo.addItems(["黑色", "蓝色", "绿色", "红色", "紫色"])
        self.foreground_combo.setCurrentIndex(0)
        type_layout.addWidget(self.foreground_combo)

        type_layout.addWidget(QLabel("背景色:"))
        self.background_combo = QComboBox()
        self.background_combo.addItems(["白色", "浅灰", "浅蓝", "浅绿", "透明"])
        self.background_combo.setCurrentIndex(0)
        type_layout.addWidget(self.background_combo)

        type_layout.addStretch()

        qrcode_layout.addLayout(type_layout)

        # Logo设置区域
        line = QWidget()
        line.setFixedHeight(1)
        line.setStyleSheet("background-color: #cccccc;")
        line.setMaximumWidth(16777215)
        qrcode_layout.addWidget(line)

        # Logo图片路径行
        logo_path_layout = QHBoxLayout()
        logo_path_layout.addWidget(QLabel("Logo图片:"))
        self.logo_path_edit = QLineEdit()
        self.logo_path_edit.setPlaceholderText("选择Logo图片（可选）")
        self.logo_browse_btn = QPushButton("浏览...")
        self.logo_browse_btn.setFixedWidth(80)
        self.logo_clear_btn = QPushButton("清除")
        self.logo_clear_btn.setFixedWidth(80)

        logo_path_layout.addWidget(self.logo_path_edit, 1)
        logo_path_layout.addWidget(self.logo_browse_btn)
        logo_path_layout.addWidget(self.logo_clear_btn)

        qrcode_layout.addLayout(logo_path_layout)

        # Logo缩放比例行
        logo_scale_layout = QHBoxLayout()
        logo_scale_layout.addWidget(QLabel("缩放比例:"))

        self.logo_scale_spin = QSpinBox()
        self.logo_scale_spin.setRange(5, 50)
        self.logo_scale_spin.setValue(20)
        self.logo_scale_spin.setSuffix("%")
        self.logo_scale_spin.setFixedWidth(80)
        self.logo_scale_spin.setToolTip(
            "Logo在二维码中的大小比例，建议设置在15%-30%之间"
        )
        self.logo_scale_spin.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.logo_scale_slider = QSlider(Qt.Orientation.Horizontal)
        self.logo_scale_slider.setRange(5, 50)
        self.logo_scale_slider.setValue(20)
        self.logo_scale_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.logo_scale_slider.setTickInterval(5)

        # 连接滑块和数字输入框
        self.logo_scale_spin.valueChanged.connect(self.logo_scale_slider.setValue)
        self.logo_scale_slider.valueChanged.connect(self.logo_scale_spin.setValue)

        logo_scale_layout.addWidget(self.logo_scale_spin)
        logo_scale_layout.addWidget(self.logo_scale_slider, 1)

        qrcode_layout.addLayout(logo_scale_layout)

        # 提示信息
        logo_hint_label = QLabel(
            "提示：过大的Logo会影响二维码的识别率，建议设置在15%-30%之间"
        )
        logo_hint_label.setStyleSheet(
            "color: #666; font-size: 11px; font-style: italic; padding-left: 80px;"
        )
        logo_hint_label.setWordWrap(True)

        qrcode_layout.addWidget(logo_hint_label)

        # 设置二维码组的布局
        qrcode_group.setLayout(qrcode_layout)

        # 任务列表预览
        preview_group = QGroupBox("任务预览")
        preview_layout = QVBoxLayout()

        self.preview_list = QListWidget()
        self.preview_list.setMaximumHeight(60)

        preview_layout.addWidget(self.preview_list)
        preview_group.setLayout(preview_layout)

        # 添加到选项卡布局
        layout.addWidget(source_group)
        layout.addWidget(output_group)
        layout.addWidget(qrcode_group)
        layout.addWidget(preview_group)
        layout.addStretch()

        return tab

    def create_batch_scan_tab(self) -> QWidget:
        """创建批量扫描选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(10)

        # 扫描源区域
        source_group = QGroupBox("扫描源")
        source_layout = QVBoxLayout()

        # 文件夹选择
        folder_layout = QHBoxLayout()
        self.scan_folder_edit = QLineEdit()
        self.scan_folder_edit.setPlaceholderText("选择包含二维码图片的文件夹")
        self.scan_folder_browse_btn = QPushButton("浏览...")

        folder_layout.addWidget(self.scan_folder_edit)
        folder_layout.addWidget(self.scan_folder_browse_btn)

        source_layout.addLayout(folder_layout)

        # 递归扫描选项
        self.recursive_check = QCheckBox("递归扫描子文件夹")
        self.recursive_check.setChecked(True)

        source_layout.addWidget(self.recursive_check)

        # 文件过滤
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("文件格式:"))
        self.format_filter_edit = QLineEdit()
        self.format_filter_edit.setText("*.png;*.jpg;*.jpeg;*.bmp;*.gif")
        filter_layout.addWidget(self.format_filter_edit)
        filter_layout.addStretch()

        source_layout.addLayout(filter_layout)

        source_group.setLayout(source_layout)

        # 输出设置区域
        scan_output_group = QGroupBox("输出设置")
        scan_output_layout = QVBoxLayout()

        # 输出文件
        output_file_layout = QHBoxLayout()
        self.scan_output_edit = QLineEdit()
        self.scan_output_edit.setPlaceholderText("扫描结果输出文件（CSV格式）")
        self.scan_output_browse_btn = QPushButton("浏览...")

        output_file_layout.addWidget(self.scan_output_edit)
        output_file_layout.addWidget(self.scan_output_browse_btn)

        scan_output_layout.addLayout(output_file_layout)

        # 扫描选项
        options_layout = QHBoxLayout()

        self.group_by_folder_check = QCheckBox("按文件夹分组结果")
        self.group_by_folder_check.setChecked(True)

        self.save_images_check = QCheckBox("保存扫描的图片")
        self.save_images_check.setChecked(False)

        options_layout.addWidget(self.group_by_folder_check)
        options_layout.addWidget(self.save_images_check)
        options_layout.addStretch()

        scan_output_layout.addLayout(options_layout)

        scan_output_group.setLayout(scan_output_layout)

        # 文件列表预览
        file_preview_group = QGroupBox("文件列表预览")
        file_preview_layout = QVBoxLayout()

        self.file_preview_list = QListWidget()
        self.file_preview_list.setMaximumHeight(150)

        file_preview_layout.addWidget(self.file_preview_list)
        file_preview_group.setLayout(file_preview_layout)

        # 统计信息
        stats_group = QGroupBox("统计信息")
        stats_layout = QVBoxLayout()

        self.stats_label = QLabel("就绪")
        self.stats_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        stats_layout.addWidget(self.stats_label)
        stats_group.setLayout(stats_layout)

        # 添加到选项卡布局
        layout.addWidget(source_group)
        layout.addWidget(scan_output_group)
        layout.addWidget(file_preview_group)
        layout.addWidget(stats_group)
        layout.addStretch()

        return tab

    def init_connections(self) -> None:
        """初始化信号连接"""
        # 批量生成选项卡
        self.csv_browse_btn.clicked.connect(self.browse_csv_file)
        self.output_dir_browse_btn.clicked.connect(self.browse_output_dir)
        self.logo_browse_btn.clicked.connect(self.browse_logo)
        self.logo_clear_btn.clicked.connect(self.clear_logo)

        # 批量扫描选项卡
        self.scan_folder_browse_btn.clicked.connect(self.browse_scan_folder)
        self.scan_output_browse_btn.clicked.connect(self.browse_scan_output)

        # 控制按钮
        self.start_btn.clicked.connect(self.start_processing)
        self.pause_btn.clicked.connect(self.pause_processing)
        self.stop_btn.clicked.connect(self.stop_processing)
        self.close_btn.clicked.connect(self.close)

        # 数据源变化
        self.csv_path_edit.textChanged.connect(self.update_generate_preview)
        self.data_text.textChanged.connect(self.update_generate_preview)
        self.scan_folder_edit.textChanged.connect(self.update_scan_preview)

    def _on_tab_changed(self, index: int) -> None:
        """
        选项卡切换时的处理

        Args:
            index: 选项卡索引 (0: 批量生成, 1: 批量扫描)
        """
        # 检查必要属性是否存在
        if not hasattr(self, "progress_label") or not hasattr(self, "progress_bar"):
            return

        # 如果正在处理中，不允许切换选项卡
        if self.is_processing:
            current_index = 0 if self.current_task == "generate" else 1
            if index != current_index:
                self.tab_widget.setCurrentIndex(current_index)
                QMessageBox.warning(
                    self, "提示", "正在处理中，请先停止当前任务再切换功能"
                )
            return

        # 重置进度显示
        self._reset_progress_display()

        # 根据选项卡更新界面提示
        if index == 0:  # 批量生成
            self.progress_label.setText("就绪 - 批量生成")
            self.status_label.setText("请选择CSV文件或输入文本数据")
        else:  # 批量扫描
            self.progress_label.setText("就绪 - 批量扫描")
            self.status_label.setText("请选择要扫描的文件夹")

    def _reset_progress_display(self) -> None:
        """重置进度显示 - 防御性编程"""
        # 检查所有必要属性是否存在
        if not hasattr(self, "progress_bar"):
            return

        # 安全设置进度条
        try:
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(0)
        except Exception:
            pass

        # 安全设置标签
        if hasattr(self, "progress_label"):
            try:
                self.progress_label.setText("就绪")
            except Exception:
                pass

        if hasattr(self, "status_label"):
            try:
                self.status_label.setText("")
            except Exception:
                pass

    def browse_csv_file(self) -> None:
        """浏览CSV文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择CSV文件", "", "CSV文件 (*.csv);;所有文件 (*.*)"
        )

        if file_path:
            self.csv_path_edit.setText(file_path)

    def browse_output_dir(self) -> None:
        """浏览输出目录"""
        dir_path = QFileDialog.getExistingDirectory(self, "选择输出目录")

        if dir_path:
            self.output_dir_edit.setText(dir_path)

    def browse_logo(self) -> None:
        """浏览Logo文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择Logo图片", "", "图片文件 (*.png *.jpg *.jpeg *.bmp *.gif)"
        )

        if file_path:
            self.logo_path_edit.setText(file_path)

    def clear_logo(self) -> None:
        """清除Logo路径"""
        self.logo_path_edit.clear()

    def browse_scan_folder(self) -> None:
        """浏览扫描文件夹"""
        dir_path = QFileDialog.getExistingDirectory(self, "选择扫描文件夹")

        if dir_path:
            self.scan_folder_edit.setText(dir_path)

    def browse_scan_output(self) -> None:
        """浏览扫描输出文件"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "选择输出文件", "", "CSV文件 (*.csv);;文本文件 (*.txt)"
        )

        if file_path:
            self.scan_output_edit.setText(file_path)

    def update_generate_preview(self) -> None:
        """更新生成任务预览"""
        self.preview_list.clear()

        # 从CSV文件获取数据
        csv_path = self.csv_path_edit.text()
        if csv_path and os.path.exists(csv_path):
            try:
                with open(csv_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    for i, line in enumerate(lines[:5]):
                        data = line.strip()
                        if data:
                            self.preview_list.addItem(f"行 {i+1}: {data[:50]}...")

                if len(lines) > 5:
                    self.preview_list.addItem(f"... 还有 {len(lines)-5} 行")

            except Exception as e:
                self.preview_list.addItem(f"读取CSV失败: {e}")

        # 从文本输入获取数据
        else:
            text = self.data_text.toPlainText()
            if text:
                lines = text.strip().split("\n")
                for i, line in enumerate(lines[:5]):
                    data = line.strip()
                    if data:
                        self.preview_list.addItem(f"行 {i+1}: {data[:50]}...")

                if len(lines) > 5:
                    self.preview_list.addItem(f"... 还有 {len(lines)-5} 行")

    def update_scan_preview(self) -> None:
        """更新扫描文件预览"""
        self.file_preview_list.clear()

        folder_path = self.scan_folder_edit.text()
        if not folder_path or not os.path.exists(folder_path):
            self.stats_label.setText("文件夹不存在")
            return

        try:
            # 收集图片文件
            image_files = []
            recursive = self.recursive_check.isChecked()

            if recursive:
                for root, dirs, files in os.walk(folder_path):
                    for file in files:
                        if self._is_image_file(file):
                            image_files.append(os.path.join(root, file))
            else:
                for file in os.listdir(folder_path):
                    if self._is_image_file(file):
                        image_files.append(os.path.join(folder_path, file))

            # 更新预览
            for i, file_path in enumerate(image_files[:10]):
                filename = os.path.basename(file_path)
                self.file_preview_list.addItem(filename)

            if len(image_files) > 10:
                self.file_preview_list.addItem(f"... 还有 {len(image_files)-10} 个文件")

            # 更新统计
            self.stats_label.setText(f"找到 {len(image_files)} 个图片文件")

        except Exception as e:
            self.stats_label.setText(f"扫描失败: {e}")

    def _is_image_file(self, filename: str) -> bool:
        """检查是否为图片文件"""
        filename_lower = filename.lower()
        return any(
            filename_lower.endswith(ext)
            for ext in FileConstants().SUPPORTED_IMAGE_FORMATS
        )

    def start_processing(self) -> None:
        """开始处理"""
        if self.is_processing:
            QMessageBox.warning(
                self, "提示", f"正在执行{self.current_task}任务，请先停止或等待完成"
            )
            return

        current_tab = self.tab_widget.currentIndex()

        if current_tab == 0:  # 批量生成
            self.start_batch_generate()
        else:  # 批量扫描
            self.start_batch_scan()

    def pause_processing(self) -> None:
        """暂停处理"""
        if not self.is_processing:
            return

        if self.current_task == "scan":
            self.batch_scanner.stop()

        self.is_processing = False
        self.update_ui_state(False)
        self.progress_label.setText("已暂停")

    def stop_processing(self) -> None:
        """停止处理"""
        if self.current_task == "scan":
            self.batch_scanner.stop()

        self.reset_processing()
        self.progress_label.setText("已停止")

    def reset_processing(self) -> None:
        """重置处理状态 - 防重复重置保护"""
        # 如果已经不在处理状态，可能是二次调用，跳过
        if self._is_resetting:
            print("跳过重复重置")
            return

        if not self.is_processing and self.current_task is None:
            print("跳过重复重置")
            return

        self._is_resetting = True

        try:
            self.is_processing = False
            self.current_task = None
            self.update_ui_state(False)

            self.batch_qr_list = []
            self.batch_total = 0
            self.batch_current = 0
            self.batch_successful = 0
            self.batch_failed = 0

            # 重置保存状态
            self._batch_saved = False
            self._batch_saved_count = 0
            self._saving_in_progress = False

            # 重置进度显示
            self._reset_progress_display()

            # 根据当前选项卡更新状态提示
            current_tab = self.tab_widget.currentIndex()
            if current_tab == 0:
                self.progress_label.setText("就绪 - 批量生成")
                self.status_label.setText("请选择CSV文件或输入文本数据")
            else:
                self.progress_label.setText("就绪 - 批量扫描")
                self.status_label.setText("请选择要扫描的文件夹")

            # 断开信号
            self._disconnect_batch_signals_safe()

        finally:
            self._is_resetting = False

    def update_ui_state(self, processing: bool) -> None:
        """
        更新UI状态

        Args:
            processing: 是否正在处理中
        """
        self.start_btn.setEnabled(not processing)
        self.pause_btn.setEnabled(processing)
        self.stop_btn.setEnabled(processing)
        self.tab_widget.setEnabled(not processing)

        # 批量生成选项卡内的控件
        if hasattr(self, "csv_path_edit"):
            self.csv_path_edit.setEnabled(not processing)
            self.csv_browse_btn.setEnabled(not processing)
            self.data_text.setEnabled(not processing)
            self.output_dir_edit.setEnabled(not processing)
            self.output_dir_browse_btn.setEnabled(not processing)
            self.filename_prefix_edit.setEnabled(not processing)
            self.format_combo.setEnabled(not processing)
            self.type_combo.setEnabled(not processing)
            self.size_spin.setEnabled(not processing)
            self.border_spin.setEnabled(not processing)
            self.foreground_combo.setEnabled(not processing)
            self.background_combo.setEnabled(not processing)
            self.logo_path_edit.setEnabled(not processing)
            self.logo_browse_btn.setEnabled(not processing)
            self.logo_clear_btn.setEnabled(not processing)
            self.logo_scale_spin.setEnabled(not processing)
            self.logo_scale_slider.setEnabled(not processing)

    def start_batch_generate(self) -> None:
        """开始批量生成"""
        # 1. 验证输入
        csv_path = self.csv_path_edit.text().strip()
        text_data = self.data_text.toPlainText().strip()

        if not csv_path and not text_data:
            QMessageBox.warning(self, "警告", "请提供CSV文件或输入文本数据")
            return

        try:
            # 重置所有状态
            self._batch_saved = False
            self._batch_saved_count = 0
            self._saving_in_progress = False
            self._disconnecting = False
            self._is_resetting = False

            # 2. 准备数据
            self.batch_qr_list = []

            # 从CSV文件读取
            if csv_path:
                if not os.path.exists(csv_path):
                    QMessageBox.warning(self, "警告", f"CSV文件不存在: {csv_path}")
                    return
                self._load_data_from_csv(csv_path)

            # 从文本输入读取
            if text_data:
                self._load_data_from_text(text_data)

            if not self.batch_qr_list:
                QMessageBox.warning(self, "警告", "没有有效的二维码数据")
                return

            # 3. 设置输出目录
            output_dir = self.output_dir_edit.text().strip()
            if output_dir:
                try:
                    os.makedirs(output_dir, exist_ok=True)
                    # 为每个二维码数据设置输出目录（存储在notes字段）
                    for qr_data in self.batch_qr_list:
                        qr_data.notes = output_dir
                except Exception as e:
                    QMessageBox.warning(self, "警告", f"创建输出目录失败: {str(e)}")
                    return

            # 4. 初始化进度状态
            self.batch_total = len(self.batch_qr_list)
            self.batch_current = 0
            self.batch_successful = 0
            self.batch_failed = 0

            # 5. 更新界面状态
            self.is_processing = True
            self.current_task = "generate"
            self.update_ui_state(True)

            # 6. 设置进度显示
            self.progress_bar.setRange(0, self.batch_total)
            self.progress_bar.setValue(0)
            self.progress_label.setText(f"开始批量生成 {self.batch_total} 个二维码...")
            self.status_label.setText("正在初始化...")

            # 7. 连接批量生成信号
            self._connect_batch_signals()

            # 8. 调用真实批量生成引擎
            self.qr_engine.generate_batch(self.batch_qr_list)

        except Exception as e:
            QMessageBox.critical(self, "错误", f"批量生成失败: {str(e)}")
            self.reset_processing()

    def _connect_batch_signals(self):
        """
        连接批量生成信号

        总是先彻底断开所有现有连接，再重新连接
        """
        # 先彻底断开所有现有连接
        self._disconnect_batch_signals_safe()

        # 重新连接信号
        self.qr_engine.batch_completed.connect(self._on_batch_progress)
        self.qr_engine.progress_updated.connect(self._on_batch_status)
        self.qr_engine.error_occurred.connect(self._on_batch_error)
        self._signals_connected = True
        print("批量生成信号已连接")

    def _disconnect_batch_signals_safe(self) -> None:
        """
        安全断开批量生成信号 - PySide6 兼容
        使用 PySide6 正确的方式断开信号，避免 RuntimeWarning
        """
        # 防重入保护
        if self._disconnecting:
            return

        # 如果信号没有被连接过，直接返回
        if not self._signals_connected:
            return

        self._disconnecting = True
        try:
            # PySide6 中直接尝试断开，捕获所有异常
            try:
                self.qr_engine.batch_completed.disconnect(self._on_batch_progress)
                print("已断开 batch_completed 信号")
            except (TypeError, RuntimeError):
                # 信号未连接时断开会抛出异常，忽略
                pass

            try:
                self.qr_engine.progress_updated.disconnect(self._on_batch_status)
                print("已断开 progress_updated 信号")
            except (TypeError, RuntimeError):
                pass

            try:
                self.qr_engine.error_occurred.disconnect(self._on_batch_error)
                print("已断开 error_occurred 信号")
            except (TypeError, RuntimeError):
                pass

            self._signals_connected = False
            print("批量生成信号已完全断开")

        except Exception as e:
            print(f"断开信号时发生异常: {e}")
        finally:
            self._disconnecting = False

    # ============ 数据加载 ============

    def _detect_file_encoding(self, file_path: str) -> str:
        """
        检测文件编码

        自动检测CSV文件的编码格式，支持 UTF-8、GBK、GB2312、BIG5 等
        """
        try:
            with open(file_path, "rb") as f:
                raw_data = f.read(1024)
                result = chardet.detect(raw_data)
                encoding = result.get("encoding", "utf-8")
                confidence = result.get("confidence", 0)

                print(f"文件编码检测: {encoding} (置信度: {confidence:.2%})")

                # 常见编码映射
                encoding_map = {
                    "gb2312": "gbk",
                    "gb18030": "gbk",
                    "big5": "big5",
                    "ascii": "utf-8",
                }
                if encoding is None:
                    return "utf-8"

                return encoding_map.get(encoding.lower(), encoding)
        except Exception as e:
            print(f"编码检测失败，使用默认编码 UTF-8: {e}")
            return "utf-8"

    def _load_data_from_csv(self, csv_path: str):
        """
        从CSV文件加载数据

        """
        # 检测文件编码
        encoding = self._detect_file_encoding(csv_path)

        encodings_to_try = [
            encoding,
            "utf-8-sig",
            "utf-8",
            "gbk",
            "gb2312",
            "big5",
            "shift-jis",
            "euc-kr",
        ]

        # 去重
        encodings_to_try = list(dict.fromkeys(encodings_to_try))

        last_error = None
        for enc in encodings_to_try:
            try:
                with open(csv_path, "r", encoding=enc) as f:
                    f.readline()
                    f.seek(0)
                    reader = csv.reader(f)
                    row_count = 0
                    for row_num, row in enumerate(reader, 1):
                        if not row or not row[0].strip():
                            continue
                        first_col = row[0].strip()
                        if first_col.startswith("#") or first_col.startswith("//"):
                            continue

                        data = first_col
                        tags = []
                        notes = None

                        if len(row) > 1 and row[1].strip():
                            tag_str = row[1].strip()
                            if ";" in tag_str:
                                tags = [
                                    t.strip() for t in tag_str.split(";") if t.strip()
                                ]
                            elif "," in tag_str:
                                tags = [
                                    t.strip() for t in tag_str.split(",") if t.strip()
                                ]
                            else:
                                tags = [tag_str] if tag_str else []

                        if len(row) > 2:
                            notes = ",".join(row[2:]).strip()

                        qr_data = self._create_qrcode_data(data, row_num, tags, notes)
                        self.batch_qr_list.append(qr_data)
                        row_count += 1

                    print(
                        f"成功读取CSV文件: {os.path.basename(csv_path)} (编码: {enc}, 行数: {row_count})"
                    )
                    return

            except UnicodeDecodeError as e:
                last_error = f"{str(e)}"
                continue
            except Exception as e:
                last_error = f"{str(e)}"
                break

        error_msg = f"无法读取CSV文件，请确保文件编码为 UTF-8 或 GBK"
        if last_error:
            error_msg += f"\n详细信息: {str(last_error)}"
        raise Exception(error_msg)

    def _load_data_from_text(self, text_data: str):
        """从文本输入加载数据"""
        lines = text_data.strip().split("\n")
        row_count = 0

        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("//"):
                continue

            parts = line.split(",")
            data = parts[0].strip()

            tags = []
            notes = None

            if len(parts) > 1 and parts[1].strip():
                tag_str = parts[1].strip()
                if ";" in tag_str:
                    tags = [t.strip() for t in tag_str.split(";") if t.strip()]
                elif "," in tag_str:
                    tags = [t.strip() for t in tag_str.split(",") if t.strip()]
                else:
                    tags = [tag_str] if tag_str else []

            if len(parts) > 2:
                notes = ",".join(parts[2:]).strip()
            qr_data = self._create_qrcode_data(data, line_num, tags, notes)
            self.batch_qr_list.append(qr_data)
            row_count += 1

        print(f"成功读取文本输入，共 {row_count} 行")

    def _create_qrcode_data(
        self,
        data: str,
        index: int,
        tags: Optional[List[str]] = None,
        notes: Optional[str] = None,
    ) -> QRCodeData:
        """
        创建二维码数据对象

        从界面控件读取配置，生成完整的 QRCodeData 对象
        """
        # 获取QRCodeType枚举
        qr_type_data = self.type_combo.currentData()
        if isinstance(qr_type_data, QRCodeType):
            qr_type = qr_type_data
        else:
            try:
                qr_type = QRCodeType(self.type_combo.currentText())
            except:
                qr_type = QRCodeType.URL

        # 获取OutputFormat枚举
        format_data = self.format_combo.currentData()
        if isinstance(format_data, OutputFormat):
            output_format = format_data
        else:
            try:
                output_format = OutputFormat(self.format_combo.currentText())
            except:
                output_format = OutputFormat.PNG

        # 生成唯一ID
        unique_str = f"{data}_{index}_{time.time()}_{random.randint(1000, 9999)}"
        unique_id = QRCodeData.generate_id(unique_str)

        return QRCodeData(
            id=unique_id,
            data=data,
            qr_type=qr_type,
            version=0,
            error_correction="H",
            size=int(self.size_spin.currentText()),
            border=int(self.border_spin.currentText()),
            foreground_color=self._get_color_code(self.foreground_combo.currentText()),
            background_color=self._get_color_code(
                self.background_combo.currentText(), True
            ),
            logo_path=(
                self.logo_path_edit.text() if self.logo_path_edit.text() else None
            ),
            logo_scale=self.logo_scale_spin.value() / 100.0,
            tags=tags or [],
            notes=notes,
            output_format=output_format.value if output_format else "PNG",
        )

    def _get_color_code(self, color_name: str, is_background: bool = False) -> str:
        """获取颜色代码"""
        color_map = {
            "黑色": "#000000",
            "蓝色": "#0000FF",
            "绿色": "#00FF00",
            "红色": "#FF0000",
            "紫色": "#800080",
            "白色": "#FFFFFF",
            "浅灰": "#F0F0F0",
            "浅蓝": "#E6F3FF",
            "浅绿": "#E6FFE6",
            "透明": "#FFFFFF" if is_background else "#000000",
        }
        return color_map.get(color_name, "#000000")

    # ============ 批量生成信号槽 ============

    def _on_batch_progress(self, completed: int, total: int):
        """
        批量生成进度更新槽函数

        Args:
            completed: 已完成数量
            total: 总数量
        """
        self.batch_current = completed
        self.batch_total = total

        self.progress_bar.setValue(completed)

        if completed == total:
            self.progress_label.setText(f"批量生成完成，共生成 {total} 个二维码")
            self.status_label.setText("处理完成")
            self._on_batch_finished()
        else:
            self.progress_label.setText(f"正在生成 {completed}/{total}...")
            self.status_label.setText(f"进度: {int(completed/total*100)}%")

    def _on_batch_status(self, progress: int, message: str):
        """批量生成状态更新"""
        self.status_label.setText(message)

    def _on_batch_error(self, error_message: str):
        """批量生成错误处理"""
        self.batch_failed += 1
        print(f"批量生成错误 [{self.batch_failed}]: {error_message[:100]}")
        self.status_label.setText(f"错误: {error_message[:50]}...")

    def _on_batch_finished(self):
        """批量生成完成处理"""
        # 保存成功数量用于显示
        success_count = self.batch_current
        failed_count = self.batch_failed
        output_dir = self.output_dir_edit.text().strip() or "当前目录"

        # 先确保数据库保存完成
        # 断开信号，防止保存过程中触发其他事件
        self._disconnect_batch_signals_safe()

        # 立即同步保存到数据库
        saved_count = 0
        try:
            for i, qr_data in enumerate(self.batch_qr_list):
                if i >= self.batch_current:
                    break
                if self.database.save_qrcode(qr_data):
                    saved_count += 1
                    # self.database.add_history_record(
                    #     qr_data.id,
                    #     "批量生成",
                    #     f"输出格式: {qr_data.output_format}, 目录: {qr_data.notes or '默认'}",
                    # )
            print(f"已保存 {saved_count} 条记录到数据库")
            print(
                f"批量生成统计: 成功={self.batch_current}, 失败={self.batch_failed}, 保存={saved_count}"
            )
        except Exception as e:
            print(f"保存到数据库失败: {e}")
            saved_count = 0

        # 更新保存状态
        self._batch_saved = True
        self._batch_saved_count = saved_count

        summary = (
            f"成功生成: {success_count} 个二维码\n"
            f"失败: {failed_count} 个\n"
            f"输出目录: {output_dir}\n"
            f"保存到数据库: {saved_count} 条"
        )

        # 发射完成信号
        self.batch_completed.emit("generate", success_count)

        # 保持进度条完成状态
        self.progress_bar.setValue(self.batch_total)
        self.progress_label.setText(f"批量生成完成，共生成 {self.batch_total} 个二维码")
        self.status_label.setText("处理完成")

        # 标记处理已完成
        self.is_processing = False
        self.current_task = None

        # 更新UI状态（启用控件）
        self.update_ui_state(False)

        # 清空批量数据
        self.batch_qr_list = []
        self.batch_total = 0
        self.batch_current = 0
        self.batch_successful = 0
        self.batch_failed = 0

        # 重置保存状态（但保留已保存计数用于显示）
        self._batch_saved = False
        self._saving_in_progress = False

        # 显示完成对话框（只显示一次）
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("批量生成完成")
        msg_box.setText(summary)
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)

        # 阻塞直到用户点击OK
        msg_box.exec()

        # 用户点击OK后，恢复为就绪状态
        self.progress_label.setText("就绪 - 批量生成")
        self.status_label.setText("请选择CSV文件或输入文本数据")
        self.progress_bar.setValue(0)

    def start_batch_scan(self) -> None:
        """开始批量扫描"""
        folder_path = self.scan_folder_edit.text()

        if not folder_path or not os.path.exists(folder_path):
            QMessageBox.warning(self, "警告", "请选择有效的扫描文件夹")
            return

        output_file = self.scan_output_edit.text()
        if not output_file:
            QMessageBox.warning(self, "警告", "请指定输出文件")
            return

        # 更新界面状态
        self.is_processing = True
        self.current_task = "scan"
        self.update_ui_state(True)

        # 重置并设置进度显示
        self._reset_progress_display()
        self.progress_label.setText("正在批量扫描...")
        self.status_label.setText("正在扫描文件夹中的图片...")
        self.progress_bar.setRange(0, 0)

        # 设置扫描器回调
        self.batch_scanner.set_callback("on_progress", self.on_scan_progress)
        self.batch_scanner.set_callback("on_result", self.on_scan_result)
        self.batch_scanner.set_callback("on_error", self.on_scan_error)
        self.batch_scanner.set_callback("on_finish", self.on_scan_finish)

        # 开始扫描
        recursive = self.recursive_check.isChecked()
        self.batch_scanner.scan_folder(folder_path, recursive=recursive)

    def on_scan_progress(self, progress: int, message: str) -> None:
        """扫描进度回调"""
        self.status_label.setText(message)
        if progress >= 0:
            self.progress_bar.setValue(progress)
            self.progress_label.setText(f"扫描进度: {progress}%")

    def on_scan_result(self, results: List[Dict]) -> None:
        """扫描结果回调"""
        pass

    def on_scan_error(self, error_message: str) -> None:
        """扫描错误回调"""
        QMessageBox.warning(self, "扫描错误", error_message)

    def on_scan_finish(self, results: List[Dict]) -> None:
        """扫描完成回调"""
        # 保持进度条完成状态
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)
        self.progress_label.setText("扫描完成")
        self.status_label.setText(f"发现 {len(results)} 个二维码")

        # 保存结果
        if self.save_scan_results(results):
            # 标记处理已完成
            self.is_processing = False
            self.current_task = None

            # 更新UI状态（启用控件）
            self.update_ui_state(False)

            # 发射完成信号
            self.batch_completed.emit("scan", len(results))

            # 显示完成对话框
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("批量扫描完成")
            msg_box.setText(
                f"扫描完成，发现 {len(results)} 个二维码\n"
                f"结果保存至: {self.scan_output_edit.text()}"
            )
            msg_box.setIcon(QMessageBox.Icon.Information)
            msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)

            # 阻塞直到用户点击OK
            msg_box.exec()

            # 恢复为就绪状态
            self.progress_label.setText("就绪 - 批量扫描")
            self.status_label.setText("请选择要扫描的文件夹")
            self.progress_bar.setValue(0)
        else:
            QMessageBox.warning(self, "警告", "扫描完成，但保存结果失败")
            self.reset_processing()

    def save_scan_results(self, results: List[Dict]) -> bool:
        """保存扫描结果"""
        output_file = self.scan_output_edit.text()
        if not output_file:
            return False

        try:
            with open(output_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["文件路径", "二维码数据", "类型", "置信度", "时间"])

                for result in results:
                    writer.writerow(
                        [
                            result.get("source", ""),
                            result.get("data", ""),
                            result.get("type", ""),
                            result.get("confidence", ""),
                            result.get("timestamp", ""),
                        ]
                    )

            print(f"扫描结果已保存: {output_file}")
            return True

        except Exception as e:
            print(f"保存扫描结果失败: {e}")
            return False

    # ============ 其他 ============

    def closeEvent(self, event) -> None:
        """关闭事件"""
        if self.is_processing:
            reply = QMessageBox.question(
                self,
                "确认关闭",
                "批量处理正在进行中，确定要关闭吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )

            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return

            self.stop_processing()

        event.accept()

    def __repr__(self) -> str:
        """返回字符串表示"""
        status = "处理中" if self.is_processing else "空闲"
        return f"BatchProcessor(status='{status}', task='{self.current_task}')"
