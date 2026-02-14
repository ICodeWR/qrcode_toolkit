#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主窗口模块 - QR Toolkit的主界面

模块名称：main_window.py
功能描述：提供QR Toolkit的主窗口界面，集成所有功能模块
作者：码上工坊
联系：微信公众号（码上工坊）
版权声明：Copyright (c) 2026 码上工坊
开源协议：MIT License
免责声明：本软件按"原样"提供，不作任何明示或暗示的担保
修改记录：
版本 0.9.0 2026-02-10 - 码上工坊 - 初始版本创建
"""

import csv
import json
import os
from typing import Dict, List, Optional

from PySide6.QtCore import QByteArray, QSettings, Qt, Slot
from PySide6.QtGui import (
    QAction,
    QCloseEvent,
    QImage,
    QKeySequence,
    QPixmap,
)
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDockWidget,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QSplitter,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QToolBar,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.database import QRCodeDatabase
from core.engine import QRCodeEngine
from core.models import OutputFormat, QRCodeData, QRCodeType
from core.scanner import QRCodeScanner
from gui.widgets import ColorPickerButton, QRPreviewWidget
from utils.constants import APP_NAME, SETTINGS_VERSION


class QRToolkit(QMainWindow):
    """QR Toolkit 主窗口"""

    def __init__(self) -> None:
        """初始化主窗口"""
        super().__init__()

        # 设置窗口属性
        self.setWindowTitle(APP_NAME + " - 二维码工具箱")
        work_area = QApplication.primaryScreen().availableGeometry()
        # 根据不同分辨率设置合适尺寸
        if work_area.width() >= 1920 and work_area.height() >= 1080:
            # 高清屏用1400x800
            window_width, window_height = 1400, 800
        elif work_area.width() >= 1366 and work_area.height() >= 768:
            # 普通笔记本用1200x700
            window_width, window_height = 1200, 700
        else:
            # 小屏幕用工作区90%
            window_width = int(work_area.width() * 0.9)
            window_height = int(work_area.height() * 0.9)

        # 居中显示
        x = (work_area.width() - window_width) // 2
        y = (work_area.height() - window_height) // 2

        self.setGeometry(x, y, window_width, window_height)

        # 初始化组件
        self.database = QRCodeDatabase()
        self.qr_engine = QRCodeEngine()
        self.scanner = QRCodeScanner()

        # 当前状态
        self.current_qr_data: Optional[QRCodeData] = None
        self.current_qr_image = None
        self.history: List[Dict] = []

        # 状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage(APP_NAME + " 就绪")

        # 初始化UI
        self.init_ui()
        self.init_connections()
        self.load_settings()

    def init_ui(self) -> None:
        """初始化用户界面"""
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)

        # 创建左侧控制面板
        control_panel = self.create_control_panel()

        # 创建右侧预览面板
        self.preview_widget = QRPreviewWidget()

        # 使用分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(control_panel)
        splitter.addWidget(self.preview_widget)
        splitter.setSizes([400, 1000])
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)

        main_layout.addWidget(splitter)

        # 创建菜单栏
        self.create_menu_bar()

        # 创建停靠窗口
        self.create_dock_widgets()

    def create_menu_bar(self) -> None:
        """创建菜单栏"""
        menubar = self.menuBar()

        # 文件菜单
        file_menu = menubar.addMenu("文件(&F)")

        new_action = QAction("新建(&N)", self)
        new_action.setShortcut(QKeySequence.StandardKey.New)
        new_action.triggered.connect(self.new_qrcode)
        file_menu.addAction(new_action)

        open_action = QAction("打开(&O)...", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self.open_qrcode)
        file_menu.addAction(open_action)

        save_action = QAction("保存(&S)", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self.save_qrcode)
        file_menu.addAction(save_action)

        save_as_action = QAction("另存为(&A)...", self)
        save_as_action.setShortcut(QKeySequence.StandardKey.SaveAs)
        save_as_action.triggered.connect(self.save_qrcode_as)
        file_menu.addAction(save_as_action)

        file_menu.addSeparator()

        import_action = QAction("导入(&I)...", self)
        import_action.triggered.connect(self.import_qrcode)
        file_menu.addAction(import_action)

        export_action = QAction("导出(&E)...", self)
        export_action.triggered.connect(self.export_qrcode)
        file_menu.addAction(export_action)

        file_menu.addSeparator()

        print_action = QAction("打印(&P)...", self)
        print_action.setShortcut(QKeySequence.StandardKey.Print)
        print_action.triggered.connect(self.print_qrcode)
        file_menu.addAction(print_action)

        file_menu.addSeparator()

        exit_action = QAction("退出(&X)", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 编辑菜单
        edit_menu = menubar.addMenu("编辑(&E)")

        copy_action = QAction("复制(&C)", self)
        copy_action.setShortcut(QKeySequence.StandardKey.Copy)
        copy_action.triggered.connect(self.copy_qrcode)
        edit_menu.addAction(copy_action)

        paste_action = QAction("粘贴(&V)", self)
        paste_action.setShortcut(QKeySequence.StandardKey.Paste)
        paste_action.triggered.connect(self.paste_qrcode)
        edit_menu.addAction(paste_action)

        edit_menu.addSeparator()

        clear_action = QAction("清空(&L)", self)
        clear_action.triggered.connect(self.clear_all)
        edit_menu.addAction(clear_action)

        # 视图菜单
        view_menu = menubar.addMenu("视图(&V)")

        zoom_in_action = QAction("放大(&I)", self)
        zoom_in_action.setShortcut(QKeySequence.StandardKey.ZoomIn)
        zoom_in_action.triggered.connect(self.preview_widget.zoom_in)
        view_menu.addAction(zoom_in_action)

        zoom_out_action = QAction("缩小(&O)", self)
        zoom_out_action.setShortcut(QKeySequence.StandardKey.ZoomOut)
        zoom_out_action.triggered.connect(self.preview_widget.zoom_out)
        view_menu.addAction(zoom_out_action)

        zoom_reset_action = QAction("重置缩放(&R)", self)
        zoom_reset_action.setShortcut("Ctrl+0")
        zoom_reset_action.triggered.connect(self.preview_widget.zoom_reset)
        view_menu.addAction(zoom_reset_action)

        zoom_fit_action = QAction("适应窗口(&F)", self)
        zoom_fit_action.setShortcut("Ctrl+1")
        zoom_fit_action.triggered.connect(self.preview_widget.zoom_fit)
        view_menu.addAction(zoom_fit_action)

        view_menu.addSeparator()

        self.show_info_dock_action = QAction("显示二维码信息", self)
        self.show_info_dock_action.setCheckable(True)
        self.show_info_dock_action.setChecked(True)
        self.show_info_dock_action.triggered.connect(
            lambda checked: self.toggle_dock_visibility("infoDockWidget", checked)
        )
        view_menu.addAction(self.show_info_dock_action)

        view_menu.addSeparator()

        restore_layout_action = QAction("恢复默认布局", self)
        restore_layout_action.triggered.connect(self.restore_default_layout)
        view_menu.addAction(restore_layout_action)

        # 工具菜单
        tools_menu = menubar.addMenu("工具(&T)")

        template_action = QAction("模板管理器(&M)...", self)
        template_action.triggered.connect(self.open_template_manager)
        tools_menu.addAction(template_action)

        batch_action = QAction("批量处理器(&B)...", self)
        batch_action.triggered.connect(self.open_batch_processor)
        tools_menu.addAction(batch_action)

        tools_menu.addSeparator()

        settings_action = QAction("设置(&S)...", self)
        settings_action.triggered.connect(self.open_settings)
        tools_menu.addAction(settings_action)

        # 帮助菜单
        help_menu = menubar.addMenu("帮助(&H)")

        about_action = QAction("关于(&A)...", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

        docs_action = QAction("使用说明(&D)...", self)
        docs_action.triggered.connect(self.show_documentation)
        help_menu.addAction(docs_action)

    def create_control_panel(self) -> QWidget:
        """创建控制面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 5, 5, 5)

        # 创建选项卡
        self.tab_widget = QTabWidget()

        # 生成选项卡
        self.generate_tab = self.create_generate_tab()

        # 扫描选项卡
        self.scan_tab = self.create_scan_tab()

        # 历史选项卡
        self.history_tab = self.create_history_tab()

        # 添加到选项卡
        self.tab_widget.addTab(self.generate_tab, "生成")
        self.tab_widget.addTab(self.scan_tab, "扫描")
        self.tab_widget.addTab(self.history_tab, "历史")

        layout.addWidget(self.tab_widget)

        # 生成按钮
        self.generate_btn = QPushButton("生成二维码")
        self.generate_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 12px;
                border-radius: 6px;
                font-size: 14px;
                margin: 10px 5px;
                border: none;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """
        )
        layout.addWidget(self.generate_btn)

        return panel

    def create_generate_tab(self) -> QWidget:
        """创建生成选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(5, 5, 5, 5)

        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)

        # 数据输入区域
        data_group = QGroupBox("数据设置")
        data_layout = QVBoxLayout()

        # 类型选择
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("类型:"))

        self.type_combo = QComboBox()
        for qr_type in QRCodeType:
            self.type_combo.addItem(qr_type.value, qr_type)
        type_layout.addWidget(self.type_combo)
        type_layout.addStretch()

        # 数据输入
        self.data_text = QTextEdit()
        self.data_text.setPlaceholderText("请输入要编码的数据...")
        self.data_text.setMaximumHeight(120)

        data_layout.addLayout(type_layout)
        data_layout.addWidget(QLabel("数据:"))
        data_layout.addWidget(self.data_text)

        # 格式助手按钮
        format_btn_layout = QHBoxLayout()
        self.format_btn_wifi = QPushButton("WiFi格式")
        self.format_btn_vcard = QPushButton("电子名片")
        self.format_btn_url = QPushButton("URL格式")
        self.format_btn_email = QPushButton("邮件格式")

        format_btn_layout.addWidget(self.format_btn_wifi)
        format_btn_layout.addWidget(self.format_btn_vcard)
        format_btn_layout.addWidget(self.format_btn_url)
        format_btn_layout.addWidget(self.format_btn_email)
        format_btn_layout.addStretch()

        data_layout.addLayout(format_btn_layout)
        data_group.setLayout(data_layout)

        # 二维码参数区域
        param_group = QGroupBox("二维码参数")
        param_layout = QFormLayout()

        self.version_spin = QSpinBox()
        self.version_spin.setRange(1, 40)
        self.version_spin.setSpecialValueText("自动")
        self.version_spin.setValue(0)

        self.error_combo = QComboBox()
        self.error_combo.addItems(["L (7%)", "M (15%)", "Q (25%)", "H (30%)"])
        self.error_combo.setCurrentIndex(3)

        self.size_spin = QSpinBox()
        self.size_spin.setRange(1, 50)
        self.size_spin.setValue(10)

        self.border_spin = QSpinBox()
        self.border_spin.setRange(0, 10)
        self.border_spin.setValue(4)

        param_layout.addRow("版本:", self.version_spin)
        param_layout.addRow("纠错级别:", self.error_combo)
        param_layout.addRow("模块大小:", self.size_spin)
        param_layout.addRow("边框大小:", self.border_spin)
        param_group.setLayout(param_layout)

        # 颜色设置区域
        color_group = QGroupBox("颜色设置")
        color_layout = QFormLayout()

        self.foreground_picker = ColorPickerButton("#000000")
        self.background_picker = ColorPickerButton("#FFFFFF")

        self.gradient_check = QCheckBox("启用渐变")
        self.gradient_start_picker = ColorPickerButton("#FF6B6B")
        self.gradient_end_picker = ColorPickerButton("#4ECDC4")
        self.gradient_type_combo = QComboBox()
        self.gradient_type_combo.addItems(["线性渐变", "径向渐变"])

        color_layout.addRow("前景色:", self.foreground_picker)
        color_layout.addRow("背景色:", self.background_picker)
        color_layout.addRow("", self.gradient_check)
        color_layout.addRow("起始色:", self.gradient_start_picker)
        color_layout.addRow("结束色:", self.gradient_end_picker)
        color_layout.addRow("渐变类型:", self.gradient_type_combo)
        color_group.setLayout(color_layout)

        # Logo设置区域
        logo_group = QGroupBox("Logo设置")
        logo_layout = QVBoxLayout()

        # 路径和按钮
        logo_path_layout = QHBoxLayout()
        self.logo_path_edit = QLineEdit()
        self.logo_path_edit.setPlaceholderText("Logo图片路径")
        self.logo_browse_btn = QPushButton("浏览...")
        self.logo_clear_btn = QPushButton("清除")

        logo_path_layout.addWidget(self.logo_path_edit)
        logo_path_layout.addWidget(self.logo_browse_btn)
        logo_path_layout.addWidget(self.logo_clear_btn)

        # 缩放比例
        logo_scale_layout = QHBoxLayout()
        logo_scale_layout.addWidget(QLabel("缩放比例:"))

        self.logo_scale_spin = QSpinBox()
        self.logo_scale_spin.setRange(5, 50)  # 5% - 50%
        self.logo_scale_spin.setValue(20)  # 默认20%
        self.logo_scale_spin.setSuffix("%")
        self.logo_scale_spin.setToolTip(
            "Logo在二维码中的大小比例，建议设置在15%-30%之间"
        )

        self.logo_scale_slider = QSlider(Qt.Orientation.Horizontal)
        self.logo_scale_slider.setRange(5, 50)
        self.logo_scale_slider.setValue(20)
        self.logo_scale_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.logo_scale_slider.setTickInterval(5)

        # 连接滑块和数字输入框
        self.logo_scale_spin.valueChanged.connect(self.logo_scale_slider.setValue)
        self.logo_scale_slider.valueChanged.connect(self.logo_scale_spin.setValue)

        logo_scale_layout.addWidget(self.logo_scale_spin)
        logo_scale_layout.addWidget(self.logo_scale_slider, 1)  # 1表示拉伸因子

        # 预览提示
        logo_hint_label = QLabel("提示：过大的Logo会影响二维码的识别率")
        logo_hint_label.setStyleSheet("color: #666; font-size: 11px;")
        logo_hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 组装布局
        logo_layout.addLayout(logo_path_layout)
        logo_layout.addLayout(logo_scale_layout)
        logo_layout.addWidget(logo_hint_label)

        logo_group.setLayout(logo_layout)

        # 其他设置区域
        other_group = QGroupBox("其他设置")
        other_layout = QFormLayout()

        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText("用逗号分隔，如: 工作,个人,支付")

        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(80)
        self.notes_edit.setPlaceholderText("添加备注信息...")

        self.format_combo = QComboBox()
        for fmt in OutputFormat:
            self.format_combo.addItem(fmt.value, fmt)

        other_layout.addRow("标签:", self.tags_edit)
        other_layout.addRow("备注:", self.notes_edit)
        other_layout.addRow("输出格式:", self.format_combo)
        other_group.setLayout(other_layout)

        # 模板按钮
        template_btn_layout = QHBoxLayout()
        self.template_load_btn = QPushButton("加载模板")
        self.template_save_btn = QPushButton("保存为模板")

        template_btn_layout.addWidget(self.template_load_btn)
        template_btn_layout.addWidget(self.template_save_btn)
        template_btn_layout.addStretch()

        # 添加到滚动布局
        scroll_layout.addWidget(data_group)
        scroll_layout.addWidget(param_group)
        scroll_layout.addWidget(color_group)
        scroll_layout.addWidget(logo_group)
        scroll_layout.addWidget(other_group)
        scroll_layout.addLayout(template_btn_layout)
        scroll_layout.addStretch()

        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

        return tab

    def create_scan_tab(self) -> QWidget:
        """创建扫描选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(5, 5, 5, 5)

        # 扫描方式选择
        scan_method_group = QGroupBox("扫描方式")
        method_layout = QHBoxLayout()

        self.scan_file_radio = QRadioButton("扫描文件")
        self.scan_camera_radio = QRadioButton("摄像头扫描")
        self.scan_file_radio.setChecked(True)

        method_layout.addWidget(self.scan_file_radio)
        method_layout.addWidget(self.scan_camera_radio)
        method_layout.addStretch()
        scan_method_group.setLayout(method_layout)

        # 文件选择区域
        self.file_group = QGroupBox("文件选择")
        file_layout = QVBoxLayout()

        self.file_list = QListWidget()
        self.file_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)

        file_btn_layout = QHBoxLayout()
        self.add_files_btn = QPushButton("添加文件")
        self.add_folder_btn = QPushButton("添加文件夹")
        self.clear_files_btn = QPushButton("清空列表")

        file_btn_layout.addWidget(self.add_files_btn)
        file_btn_layout.addWidget(self.add_folder_btn)
        file_btn_layout.addStretch()
        file_btn_layout.addWidget(self.clear_files_btn)

        file_layout.addWidget(self.file_list)
        file_layout.addLayout(file_btn_layout)
        self.file_group.setLayout(file_layout)

        # 摄像头设置区域
        self.camera_group = QGroupBox("摄像头设置")
        camera_layout = QVBoxLayout()

        camera_select_layout = QHBoxLayout()
        camera_select_layout.addWidget(QLabel("选择摄像头:"))

        self.camera_combo = QComboBox()
        camera_select_layout.addWidget(self.camera_combo)
        camera_select_layout.addStretch()

        self.refresh_camera_btn = QPushButton("刷新")
        camera_select_layout.addWidget(self.refresh_camera_btn)

        camera_layout.addLayout(camera_select_layout)

        # 摄像头预览区域
        self.camera_preview = QLabel()
        self.camera_preview.setMinimumHeight(240)
        self.camera_preview.setMinimumWidth(320)
        self.camera_preview.setStyleSheet(
            """
            QLabel {
                background-color: #1e1e1e;
                border: 2px solid #444;
                border-radius: 4px;
                color: #888;
                font-size: 14px;
            }
        """
        )
        self.camera_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.camera_preview.setText("摄像头预览区域\n点击'开始扫描'启动摄像头")

        camera_layout.addWidget(self.camera_preview)
        self.camera_group.setLayout(camera_layout)
        self.camera_group.setVisible(False)

        # 扫描按钮
        self.scan_btn = QPushButton("开始扫描")
        self.scan_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
                margin: 10px 0;
                border: none;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """
        )

        # 进度条
        self.scan_progress = QProgressBar()
        self.scan_progress.setTextVisible(True)
        self.scan_progress.setVisible(False)

        # 结果区域
        result_group = QGroupBox("扫描结果")
        result_layout = QVBoxLayout()

        self.result_table = QTableWidget()
        self.result_table.setColumnCount(4)
        self.result_table.setHorizontalHeaderLabels(["来源", "类型", "数据", "时间"])
        self.result_table.horizontalHeader().setStretchLastSection(True)

        result_btn_layout = QHBoxLayout()
        self.save_results_btn = QPushButton("保存结果")
        self.clear_results_btn = QPushButton("清空结果")
        self.copy_result_btn = QPushButton("复制")

        result_btn_layout.addWidget(self.save_results_btn)
        result_btn_layout.addWidget(self.clear_results_btn)
        result_btn_layout.addStretch()
        result_btn_layout.addWidget(self.copy_result_btn)

        result_layout.addWidget(self.result_table)
        result_layout.addLayout(result_btn_layout)
        result_group.setLayout(result_layout)

        # 添加到主布局
        layout.addWidget(scan_method_group)
        layout.addWidget(self.file_group)
        layout.addWidget(self.camera_group)
        layout.addWidget(self.scan_btn)
        layout.addWidget(self.scan_progress)
        layout.addWidget(result_group)

        return tab

    def create_history_tab(self) -> QWidget:
        """创建历史选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(5, 5, 5, 5)

        # 历史列表
        self.history_tree = QTreeWidget()
        self.history_tree.setHeaderLabels(["时间", "类型", "数据", "状态"])
        self.history_tree.setColumnWidth(0, 150)
        self.history_tree.setColumnWidth(1, 100)
        self.history_tree.setColumnWidth(2, 300)
        self.history_tree.setColumnWidth(3, 80)

        # 操作按钮
        history_btn_layout = QHBoxLayout()

        self.history_refresh_btn = QPushButton("刷新")
        self.history_load_btn = QPushButton("加载")
        self.history_delete_btn = QPushButton("删除")
        self.history_clear_btn = QPushButton("清空")
        self.history_export_btn = QPushButton("导出")

        history_btn_layout.addWidget(self.history_refresh_btn)
        history_btn_layout.addWidget(self.history_load_btn)
        history_btn_layout.addWidget(self.history_delete_btn)
        history_btn_layout.addStretch()
        history_btn_layout.addWidget(self.history_clear_btn)
        history_btn_layout.addWidget(self.history_export_btn)

        layout.addWidget(self.history_tree)
        layout.addLayout(history_btn_layout)

        return tab

    def create_dock_widgets(self) -> None:
        """创建停靠窗口"""
        # 信息停靠窗口
        info_dock = QDockWidget("二维码信息", self)
        info_dock.setObjectName("infoDockWidget")
        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)

        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setMaximumHeight(800)
        self.info_text.setFixedHeight(800)
        info_layout.addWidget(
            self.info_text,
            alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft,
        )

        self.info_text.setFrameStyle(QFrame.Shape.NoFrame)
        self.info_text.setStyleSheet(
            """
            QTextEdit {
                background-color: transparent;
                border: none;
                padding: 5px;
            }
        """
        )

        info_dock.setWidget(info_widget)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, info_dock)

        info_dock.visibilityChanged.connect(self.on_info_dock_visibility_changed)

    def on_info_dock_visibility_changed(self, visible: bool) -> None:
        """信息停靠窗口可见性变化时的处理"""
        # 更新菜单项的勾选状态
        if hasattr(self, "show_info_dock_action"):
            self.show_info_dock_action.setChecked(visible)

            if not visible:
                self.status_bar.showMessage("二维码信息面板已隐藏")
            else:
                self.status_bar.showMessage("二维码信息面板已显示")

    def toggle_dock_visibility(self, dock_name: str, visible: bool) -> None:
        """切换停靠窗口显示"""
        dock = self.findChild(QDockWidget, dock_name)
        if dock:
            # 直接设置可见性，会触发 visibilityChanged 信号
            dock.setVisible(visible)

    def restore_default_layout(self) -> None:
        """恢复默认布局"""
        # 显示所有组件
        self.show_info_dock_action.setChecked(True)

        self.toggle_dock_visibility("infoDockWidget", True)

        # 确保停靠窗口在正确的位置
        info_dock = self.findChild(QDockWidget, "infoDockWidget")

        if info_dock:
            # 移除并重新添加以确保正确位置
            self.removeDockWidget(info_dock)
            self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, info_dock)
            info_dock.setVisible(True)

        self.status_bar.showMessage("已恢复默认布局")

    def init_connections(self) -> None:
        """初始化信号连接"""
        # 生成按钮
        self.generate_btn.clicked.connect(self.generate_qrcode)

        # 颜色选择器
        self.foreground_picker.color_changed.connect(self.update_preview)
        self.background_picker.color_changed.connect(self.update_preview)
        self.gradient_start_picker.color_changed.connect(self.update_preview)
        self.gradient_end_picker.color_changed.connect(self.update_preview)

        # Logo按钮
        self.logo_browse_btn.clicked.connect(self.browse_logo)
        self.logo_clear_btn.clicked.connect(self.clear_logo)

        # Logo缩放比例信号连接
        self.logo_scale_spin.valueChanged.connect(self.update_preview)
        self.logo_scale_slider.valueChanged.connect(self.update_preview)

        # 格式助手按钮
        self.format_btn_wifi.clicked.connect(self.create_wifi_format)
        self.format_btn_vcard.clicked.connect(self.create_vcard_format)
        self.format_btn_url.clicked.connect(self.create_url_format)
        self.format_btn_email.clicked.connect(self.create_email_format)

        # 模板按钮
        self.template_load_btn.clicked.connect(self.open_template_manager)
        self.template_save_btn.clicked.connect(self.save_as_template)

        # 扫描相关
        self.scan_file_radio.toggled.connect(self.update_scan_mode)
        self.scan_camera_radio.toggled.connect(self.update_scan_mode)
        self.add_files_btn.clicked.connect(self.add_scan_files)
        self.add_folder_btn.clicked.connect(self.add_scan_folder)
        self.clear_files_btn.clicked.connect(self.clear_scan_files)
        self.refresh_camera_btn.clicked.connect(self.refresh_camera_list)
        self.scan_btn.clicked.connect(self.start_scanning)
        self.save_results_btn.clicked.connect(self.save_scan_results)
        self.clear_results_btn.clicked.connect(self.clear_scan_results)
        self.copy_result_btn.clicked.connect(self.copy_scan_result)

        # 历史相关
        self.history_refresh_btn.clicked.connect(self.refresh_history)
        self.history_load_btn.clicked.connect(self.load_from_history)
        self.history_delete_btn.clicked.connect(self.delete_history_item)
        self.history_clear_btn.clicked.connect(self.clear_history)
        self.history_export_btn.clicked.connect(self.export_history)
        self.history_tree.itemDoubleClicked.connect(self.load_history_item)

        # 二维码引擎信号
        self.qr_engine.qr_generated.connect(self.on_qr_generated)
        self.qr_engine.progress_updated.connect(self.update_progress)
        self.qr_engine.error_occurred.connect(self.show_error)

        # 扫描器信号
        self.scanner.qr_scanned.connect(self.on_qr_scanned)
        self.scanner.progress_updated.connect(self.update_scan_progress)
        self.scanner.error_occurred.connect(self.show_error)
        self.scanner.camera_frame.connect(self.update_camera_preview)

    def load_settings(self) -> None:
        """加载设置"""
        settings = QSettings(SETTINGS_VERSION.replace(" ", ""), SETTINGS_VERSION)

        # 窗口几何状态
        geometry_bytes = settings.value("geometry")
        if geometry_bytes is not None:
            if isinstance(geometry_bytes, QByteArray):
                self.restoreGeometry(geometry_bytes)
            elif isinstance(geometry_bytes, (bytes, bytearray)):
                self.restoreGeometry(QByteArray(geometry_bytes))

        window_state_bytes = settings.value("windowState")
        if window_state_bytes is not None:
            if isinstance(window_state_bytes, QByteArray):
                self.restoreState(window_state_bytes)
            elif isinstance(window_state_bytes, (bytes, bytearray)):
                self.restoreState(QByteArray(window_state_bytes))

        # 在窗口状态恢复后，同步各个停靠窗口的可见性状态到对应的菜单项
        info_dock = self.findChild(QDockWidget, "infoDockWidget")
        if info_dock and hasattr(self, "show_info_dock_action"):
            is_visible = info_dock.isVisible()
            self.show_info_dock_action.setChecked(is_visible)

        # 应用设置
        default_size = settings.value("default_size", 10)
        default_border = settings.value("default_border", 4)
        default_format = settings.value("default_format", "PNG")
        default_logo_scale = settings.value("default_logo_scale", 20)

        # 安全转为 int
        size_val = int(default_size) if isinstance(default_size, (int, str)) else 10
        border_val = (
            int(default_border) if isinstance(default_border, (int, str)) else 4
        )
        logo_scale_val = (
            int(default_logo_scale)
            if isinstance(default_logo_scale, (int, str))
            else 20
        )

        # 确保在有效范围内
        logo_scale_val = max(5, min(50, logo_scale_val))

        self.size_spin.setValue(int(size_val))
        self.border_spin.setValue(int(border_val))
        self.logo_scale_spin.setValue(int(logo_scale_val))
        self.logo_scale_slider.setValue(int(logo_scale_val))

        index = self.format_combo.findText(str(default_format))
        if index >= 0:
            self.format_combo.setCurrentIndex(index)

        # 刷新摄像头列表
        self.refresh_camera_list()

        # 刷新历史记录
        self.refresh_history()

    def closeEvent(self, event: QCloseEvent) -> None:
        """关闭事件"""
        # 保存设置
        settings = QSettings(SETTINGS_VERSION.replace(" ", ""), SETTINGS_VERSION)
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("windowState", self.saveState())
        settings.setValue("default_logo_scale", self.logo_scale_spin.value())

        # 停止扫描器
        self.scanner.stop_scanning()

        event.accept()

    # ==================== 槽函数 ====================
    @Slot()
    def generate_qrcode(self) -> None:
        """生成二维码"""
        try:
            # 获取数据
            data = self.data_text.toPlainText().strip()
            if not data:
                QMessageBox.warning(self, "警告", "请输入要编码的数据")
                return

            # 创建二维码数据对象 - 添加 logo_scale 参数
            qr_data = QRCodeData(
                id=QRCodeData.generate_id(data),
                data=data,
                qr_type=self.type_combo.currentData(),
                version=self.version_spin.value(),
                error_correction=self.error_combo.currentText()[0],
                size=self.size_spin.value(),
                border=self.border_spin.value(),
                foreground_color=self.foreground_picker.get_color(),
                background_color=self.background_picker.get_color(),
                logo_path=(
                    self.logo_path_edit.text() if self.logo_path_edit.text() else None
                ),
                logo_scale=self.logo_scale_spin.value()
                / 100.0,  # 转换为小数，如20% -> 0.2
                gradient_start=(
                    self.gradient_start_picker.get_color()
                    if self.gradient_check.isChecked()
                    else None
                ),
                gradient_end=(
                    self.gradient_end_picker.get_color()
                    if self.gradient_check.isChecked()
                    else None
                ),
                gradient_type=(
                    "linear"
                    if self.gradient_type_combo.currentIndex() == 0
                    else "radial"
                ),
                tags=[
                    tag.strip()
                    for tag in self.tags_edit.text().split(",")
                    if tag.strip()
                ],
                notes=self.notes_edit.toPlainText() or None,
                output_format=self.format_combo.currentText(),
            )

            # 验证数据
            is_valid, message = qr_data.validate()
            if not is_valid:
                QMessageBox.warning(self, "数据验证失败", message)
                return

            # 保存到数据库
            if self.database.save_qrcode(qr_data):
                self.status_bar.showMessage("二维码数据已保存")

            # 开始生成
            self.current_qr_data = qr_data
            self.generate_btn.setEnabled(False)
            self.status_bar.showMessage("正在生成二维码...")

            self.qr_engine.generate(qr_data)

        except Exception as e:
            self.show_error(f"生成失败: {str(e)}")

    @Slot(QRCodeData, QImage)
    def on_qr_generated(self, qr_data: QRCodeData, qimage) -> None:
        """二维码生成完成"""
        self.current_qr_data = qr_data
        self.current_qr_image = qimage

        # 更新预览
        self.preview_widget.set_qr_image(qimage, qr_data)

        # 更新信息面板
        self.update_info_panel(qr_data)

        # 启用按钮
        self.generate_btn.setEnabled(True)
        self.status_bar.showMessage("二维码生成完成")

        # 添加到历史
        self.add_to_history(qr_data, "生成")

    @Slot(int, str)
    def update_progress(self, value: int, message: str) -> None:
        """更新进度"""
        self.status_bar.showMessage(f"{message} ({value}%)")

    @Slot(str)
    def show_error(self, error_message: str) -> None:
        """显示错误"""
        QMessageBox.critical(self, "错误", error_message)
        self.generate_btn.setEnabled(True)
        self.status_bar.showMessage("操作失败")

    @Slot()
    def update_preview(self) -> None:
        """更新预览 - 实时预览功能"""
        # 检查是否有足够的数据进行预览
        data = self.data_text.toPlainText().strip()
        if data and not self.generate_btn.isEnabled():
            # 如果已经有生成任务在进行，不重复触发
            return

        # 如果有当前二维码数据且数据不为空，可以触发自动生成
        # 但为了避免频繁生成，可以添加延迟或只在特定条件下触发
        # 这里简化处理：不自动生成，只显示状态提示
        if data:
            self.status_bar.showMessage("参数已更新，点击生成按钮查看效果")
        else:
            self.status_bar.showMessage("请输入数据")

    @Slot()
    def browse_logo(self) -> None:
        """浏览Logo文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择Logo图片", "", "图片文件 (*.png *.jpg *.jpeg *.bmp *.gif)"
        )

        if file_path:
            self.logo_path_edit.setText(file_path)
            # 触发预览更新
            self.update_preview()

    @Slot()
    def clear_logo(self) -> None:
        """清除Logo"""
        self.logo_path_edit.clear()
        # 触发预览更新
        self.update_preview()

    @Slot()
    def create_wifi_format(self) -> None:
        """创建WiFi格式"""
        dialog = QDialog(self)
        dialog.setWindowTitle("WiFi连接设置")
        dialog.setMinimumWidth(400)

        layout = QFormLayout(dialog)

        ssid_edit = QLineEdit()
        password_edit = QLineEdit()
        password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        encryption_combo = QComboBox()
        encryption_combo.addItems(["WPA", "WEP", "nopass"])
        hidden_check = QCheckBox("隐藏网络")

        layout.addRow("网络名称 (SSID):", ssid_edit)
        layout.addRow("密码:", password_edit)
        layout.addRow("加密类型:", encryption_combo)
        layout.addRow("", hidden_check)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)

        layout.addRow(button_box)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            wifi_str = f"WIFI:S:{ssid_edit.text()};T:{encryption_combo.currentText()};P:{password_edit.text()};;"
            if hidden_check.isChecked():
                wifi_str += "H:true;"

            self.data_text.setText(wifi_str)
            self.type_combo.setCurrentText(QRCodeType.WIFI.value)
            self.update_preview()

    @Slot()
    def create_vcard_format(self) -> None:
        """创建电子名片格式"""
        dialog = QDialog(self)
        dialog.setWindowTitle("电子名片设置")
        dialog.setMinimumWidth(500)

        layout = QFormLayout(dialog)

        name_edit = QLineEdit()
        company_edit = QLineEdit()
        title_edit = QLineEdit()
        phone_edit = QLineEdit()
        email_edit = QLineEdit()
        website_edit = QLineEdit()

        layout.addRow("姓名:", name_edit)
        layout.addRow("公司:", company_edit)
        layout.addRow("职位:", title_edit)
        layout.addRow("电话:", phone_edit)
        layout.addRow("邮箱:", email_edit)
        layout.addRow("网站:", website_edit)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)

        layout.addRow(button_box)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            vcard = f"""BEGIN:VCARD
VERSION:3.0
FN:{name_edit.text()}
ORG:{company_edit.text()}
TITLE:{title_edit.text()}
TEL:{phone_edit.text()}
EMAIL:{email_edit.text()}
URL:{website_edit.text()}
END:VCARD"""

            self.data_text.setText(vcard)
            self.type_combo.setCurrentText(QRCodeType.VCARD.value)
            self.update_preview()

    @Slot()
    def create_url_format(self) -> None:
        """创建URL格式"""
        dialog = QDialog(self)
        dialog.setWindowTitle("URL设置")
        dialog.setMinimumWidth(400)

        layout = QFormLayout(dialog)

        url_edit = QLineEdit()
        url_edit.setPlaceholderText("https://www.example.com")

        layout.addRow("URL:", url_edit)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)

        layout.addRow(button_box)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.data_text.setText(url_edit.text())
            self.type_combo.setCurrentText(QRCodeType.URL.value)
            self.update_preview()

    @Slot()
    def create_email_format(self) -> None:
        """创建邮件格式"""
        from urllib.parse import quote

        dialog = QDialog(self)
        dialog.setWindowTitle("邮件设置")
        dialog.setMinimumWidth(400)

        layout = QFormLayout(dialog)

        to_edit = QLineEdit()
        to_edit.setPlaceholderText("收件人邮箱")
        subject_edit = QLineEdit()
        subject_edit.setPlaceholderText("邮件主题")
        body_edit = QTextEdit()
        body_edit.setMaximumHeight(100)
        body_edit.setPlaceholderText("邮件正文")

        layout.addRow("收件人:", to_edit)
        layout.addRow("主题:", subject_edit)
        layout.addRow("正文:", body_edit)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)

        layout.addRow(button_box)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            email_str = f"mailto:{to_edit.text()}?subject={quote(subject_edit.text())}&body={quote(body_edit.toPlainText())}"
            self.data_text.setText(email_str)
            self.type_combo.setCurrentText(QRCodeType.EMAIL.value)
            self.update_preview()

    @Slot(bool)
    def update_scan_mode(self, checked: bool) -> None:
        """更新扫描模式"""
        if checked:
            is_camera = self.scan_camera_radio.isChecked()
            self.file_group.setVisible(not is_camera)
            self.camera_group.setVisible(is_camera)

    @Slot()
    def refresh_camera_list(self) -> None:
        """刷新摄像头列表"""
        self.camera_combo.clear()

        # 显示正在检测的状态
        self.camera_combo.addItem("正在检测摄像头...", -2)
        self.camera_combo.setEnabled(False)
        QApplication.processEvents()  # 刷新UI

        try:
            cameras = self.scanner.get_available_cameras()

            self.camera_combo.clear()

            if cameras and cameras[0][0] != -1:  # 有可用摄像头
                for index, name in cameras:
                    self.camera_combo.addItem(name, index)

                # 默认选择第一个摄像头
                if self.camera_combo.count() > 0:
                    self.camera_combo.setCurrentIndex(0)

                self.scan_camera_radio.setEnabled(True)
                self.status_bar.showMessage(f"找到 {len(cameras)} 个摄像头")
            else:
                self.camera_combo.addItem("未找到摄像头", -1)
                self.scan_camera_radio.setEnabled(False)
                self.status_bar.showMessage("未找到可用摄像头")
        except Exception as e:
            self.camera_combo.clear()
            self.camera_combo.addItem(f"摄像头检测失败", -1)
            self.scan_camera_radio.setEnabled(False)
            print(f"刷新摄像头列表失败: {e}")
        finally:
            self.camera_combo.setEnabled(True)

    @Slot()
    def add_scan_files(self) -> None:
        """添加扫描文件"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "选择二维码图片",
            "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.gif *.tiff *.webp)",
        )

        for file_path in file_paths:
            item = QListWidgetItem(file_path)
            item.setData(Qt.ItemDataRole.UserRole, file_path)
            self.file_list.addItem(item)

    @Slot()
    def add_scan_folder(self) -> None:
        """添加扫描文件夹"""
        folder_path = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if folder_path:
            # 查找图片文件
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    if file.lower().endswith(
                        (".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tiff", ".webp")
                    ):
                        file_path = os.path.join(root, file)
                        item = QListWidgetItem(file_path)
                        item.setData(Qt.ItemDataRole.UserRole, file_path)
                        self.file_list.addItem(item)

    @Slot()
    def clear_scan_files(self) -> None:
        """清空扫描文件列表"""
        self.file_list.clear()

    @Slot()
    def start_scanning(self) -> None:
        """开始扫描 - 支持实时预览"""
        if self.scan_file_radio.isChecked():
            # 文件扫描逻辑
            if self.file_list.count() == 0:
                QMessageBox.warning(self, "警告", "请先添加要扫描的文件")
                return

            file_paths = []
            for i in range(self.file_list.count()):
                file_paths.append(self.file_list.item(i).data(Qt.ItemDataRole.UserRole))

            self.scanner.scan_files(file_paths)
            self.scan_btn.setEnabled(False)
            self.scan_progress.setVisible(True)
            self.status_bar.showMessage("正在扫描文件...")

        else:  # 摄像头扫描
            if self.camera_combo.currentData() == -1:
                QMessageBox.warning(self, "警告", "未找到可用的摄像头")
                return

            # 清空预览
            self.camera_preview.clear()
            self.camera_preview.setText("正在启动摄像头...")
            QApplication.processEvents()

            camera_index = self.camera_combo.currentData()

            # 设置扫描参数
            self.scanner.set_min_confidence(0.5)  # 设置最低置信度

            # 开始扫描（会自动发送预览帧）
            self.scanner.scan_camera(camera_index)

            self.scan_btn.setEnabled(False)
            self.scan_progress.setVisible(True)
            self.scan_progress.setValue(0)
            self.status_bar.showMessage("正在启动摄像头...")

    @Slot(list)
    def on_qr_scanned(self, results: List[Dict]) -> None:
        """扫描完成"""
        self.scan_btn.setEnabled(True)
        self.scan_progress.setVisible(False)

        if not results:
            self.status_bar.showMessage("扫描完成，未发现二维码")
            QMessageBox.information(self, "提示", "未发现二维码")
            return

        # 显示结果
        self.result_table.setRowCount(len(results))
        for i, result in enumerate(results):
            # 文件路径
            file_item = QTableWidgetItem(result.get("source", "未知"))
            self.result_table.setItem(i, 0, file_item)

            # 类型
            type_item = QTableWidgetItem(result.get("type", "QRCODE"))
            self.result_table.setItem(i, 1, type_item)

            # 数据
            data = result.get("data", "")
            data_item = QTableWidgetItem(
                data[:100] + "..." if len(data) > 100 else data
            )
            data_item.setToolTip(data)
            self.result_table.setItem(i, 2, data_item)

            # 时间
            time_item = QTableWidgetItem(result.get("timestamp", ""))
            self.result_table.setItem(i, 3, time_item)

        self.status_bar.showMessage(f"扫描完成，发现 {len(results)} 个二维码")

    @Slot(QImage)
    def update_camera_preview(self, qimage) -> None:
        """更新摄像头预览 - 实时显示"""
        if not qimage or qimage.isNull():
            return

        try:
            # 转换为QPixmap
            pixmap = QPixmap.fromImage(qimage)

            # 获取预览标签的尺寸
            preview_size = self.camera_preview.size()

            # 如果预览标签大小有效
            if preview_size.width() > 0 and preview_size.height() > 0:
                # 缩放图像以适应预览区域（保持宽高比）
                scaled_pixmap = pixmap.scaled(
                    preview_size,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )

                # 设置预览
                self.camera_preview.setPixmap(scaled_pixmap)

                # 清除文本（因为现在显示图像）
                if self.camera_preview.text():
                    self.camera_preview.setText("")
            else:
                # 预览标签尚未初始化，直接显示原图
                self.camera_preview.setPixmap(pixmap)
                self.camera_preview.setText("")

        except Exception as e:
            print(f"更新摄像头预览失败: {e}")

    @Slot(int, str)
    def update_scan_progress(self, value: int, message: str) -> None:
        """更新扫描进度"""
        self.scan_progress.setValue(value)
        self.status_bar.showMessage(f"{message} ({value}%)")

    @Slot()
    def save_scan_results(self) -> None:
        """保存扫描结果"""
        if self.result_table.rowCount() == 0:
            QMessageBox.warning(self, "警告", "没有扫描结果可保存")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存扫描结果",
            "",
            "CSV文件 (*.csv);;文本文件 (*.txt);;JSON文件 (*.json)",
        )

        if file_path:
            try:
                if file_path.endswith(".csv"):
                    self._save_scan_results_csv(file_path)
                elif file_path.endswith(".json"):
                    self._save_scan_results_json(file_path)
                else:
                    self._save_scan_results_txt(file_path)

                QMessageBox.information(self, "成功", f"扫描结果已保存到:\n{file_path}")

            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败: {str(e)}")

    def _save_scan_results_csv(self, file_path: str) -> None:
        """保存扫描结果为CSV格式"""
        with open(file_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["来源", "类型", "数据", "时间"])

            for i in range(self.result_table.rowCount()):
                row = []
                for j in range(self.result_table.columnCount()):
                    item = self.result_table.item(i, j)
                    row.append(item.text() if item else "")
                writer.writerow(row)

    def _save_scan_results_json(self, file_path: str) -> None:
        """保存扫描结果为JSON格式"""
        results = []
        for i in range(self.result_table.rowCount()):
            result = {
                "source": (
                    self.result_table.item(i, 0).text()
                    if self.result_table.item(i, 0)
                    else ""
                ),
                "type": (
                    self.result_table.item(i, 1).text()
                    if self.result_table.item(i, 1)
                    else ""
                ),
                "data": (
                    self.result_table.item(i, 2).text()
                    if self.result_table.item(i, 2)
                    else ""
                ),
                "timestamp": (
                    self.result_table.item(i, 3).text()
                    if self.result_table.item(i, 3)
                    else ""
                ),
            }
            results.append(result)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

    def _save_scan_results_txt(self, file_path: str) -> None:
        """保存扫描结果为文本格式"""
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("扫描结果\n")
            f.write("=" * 50 + "\n")
            for i in range(self.result_table.rowCount()):
                f.write(f"结果 {i+1}:\n")
                f.write(
                    f"  来源: {self.result_table.item(i, 0).text() if self.result_table.item(i, 0) else ''}\n"
                )
                f.write(
                    f"  类型: {self.result_table.item(i, 1).text() if self.result_table.item(i, 1) else ''}\n"
                )
                f.write(
                    f"  数据: {self.result_table.item(i, 2).text() if self.result_table.item(i, 2) else ''}\n"
                )
                f.write(
                    f"  时间: {self.result_table.item(i, 3).text() if self.result_table.item(i, 3) else ''}\n"
                )
                f.write("\n")

    @Slot()
    def clear_scan_results(self) -> None:
        """清空扫描结果"""
        self.result_table.setRowCount(0)

    @Slot()
    def copy_scan_result(self) -> None:
        """复制扫描结果"""
        current_row = self.result_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "警告", "请先选择一个结果")
            return

        data_item = self.result_table.item(current_row, 2)
        if data_item:
            clipboard = QApplication.clipboard()
            clipboard.setText(data_item.text())
            QMessageBox.information(self, "成功", "数据已复制到剪贴板")

    @Slot()
    def refresh_history(self) -> None:
        """刷新历史记录"""
        self.history_tree.clear()

        qrcodes = self.database.get_all_qrcodes()
        for qrcode_data in qrcodes:
            item = QTreeWidgetItem(self.history_tree)
            item.setText(0, qrcode_data.created_at[:19].replace("T", " "))
            item.setText(1, qrcode_data.qr_type.value)
            item.setText(
                2,
                (
                    qrcode_data.data[:50] + "..."
                    if len(qrcode_data.data) > 50
                    else qrcode_data.data
                ),
            )
            item.setText(3, "已保存")
            item.setData(0, Qt.ItemDataRole.UserRole, qrcode_data.id)

    @Slot()
    def load_from_history(self) -> None:
        """从历史记录加载"""
        selected = self.history_tree.currentItem()
        if selected:
            qrcode_id = selected.data(0, Qt.ItemDataRole.UserRole)
            qrcode_data = self.database.load_qrcode(qrcode_id)

            if qrcode_data:
                self.load_qrcode_data(qrcode_data)
                self.status_bar.showMessage("已从历史记录加载")
                self.tab_widget.setCurrentIndex(0)  # 切换到生成选项卡

    @Slot(QTreeWidgetItem, int)
    def load_history_item(self, item: QTreeWidgetItem, column: int) -> None:
        """加载历史项目（双击）"""
        self.load_from_history()

    def load_qrcode_data(self, qr_data: QRCodeData) -> None:
        """加载二维码数据到界面"""
        self.data_text.setText(qr_data.data)

        # 设置类型
        index = self.type_combo.findText(qr_data.qr_type.value)
        if index >= 0:
            self.type_combo.setCurrentIndex(index)

        # 设置参数
        self.version_spin.setValue(qr_data.version)

        # 设置纠错级别
        error_index = {"L": 0, "M": 1, "Q": 2, "H": 3}.get(qr_data.error_correction, 3)
        self.error_combo.setCurrentIndex(error_index)

        self.size_spin.setValue(qr_data.size)
        self.border_spin.setValue(qr_data.border)

        # 设置颜色
        self.foreground_picker.set_color(qr_data.foreground_color)
        self.background_picker.set_color(qr_data.background_color)

        # 安全地设置Logo和缩放比例
        if qr_data.logo_path:
            self.logo_path_edit.setText(qr_data.logo_path)

            # 安全地设置Logo缩放比例
            try:
                if hasattr(qr_data, "logo_scale") and qr_data.logo_scale is not None:
                    scale_value = qr_data.logo_scale
                    # 处理可能是小数（0.2）或整数（20）的情况
                    if isinstance(scale_value, float) and scale_value <= 1:
                        scale_percent = int(scale_value * 100)
                    else:
                        scale_percent = int(scale_value)

                    # 确保在有效范围内
                    scale_percent = max(5, min(50, scale_percent))
                    self.logo_scale_spin.setValue(scale_percent)
                    self.logo_scale_slider.setValue(scale_percent)
                else:
                    # 旧版本数据，使用默认值
                    self.logo_scale_spin.setValue(20)
                    self.logo_scale_slider.setValue(20)
            except (ValueError, TypeError, AttributeError):
                # 转换失败时使用默认值
                self.logo_scale_spin.setValue(20)
                self.logo_scale_slider.setValue(20)
        else:
            self.logo_path_edit.clear()
            # 重置为默认值
            self.logo_scale_spin.setValue(20)
            self.logo_scale_slider.setValue(20)
        # ====================================================================

        # 设置渐变
        if qr_data.gradient_start and qr_data.gradient_end:
            self.gradient_check.setChecked(True)
            self.gradient_start_picker.set_color(qr_data.gradient_start)
            self.gradient_end_picker.set_color(qr_data.gradient_end)
            self.gradient_type_combo.setCurrentIndex(
                0 if qr_data.gradient_type == "linear" else 1
            )
        else:
            self.gradient_check.setChecked(False)

        # 设置标签
        if qr_data.tags:
            self.tags_edit.setText(", ".join(qr_data.tags))
        else:
            self.tags_edit.clear()

        # 设置备注
        self.notes_edit.setText(qr_data.notes or "")

        # 设置输出格式
        format_index = self.format_combo.findText(qr_data.output_format)
        if format_index >= 0:
            self.format_combo.setCurrentIndex(format_index)

    @Slot()
    def delete_history_item(self) -> None:
        """删除历史项目"""
        selected = self.history_tree.currentItem()
        if selected:
            qrcode_id = selected.data(0, Qt.ItemDataRole.UserRole)
            reply = QMessageBox.question(
                self,
                "确认删除",
                "确定要删除这条记录吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )

            if reply == QMessageBox.StandardButton.Yes:
                if self.database.delete_qrcode(qrcode_id):
                    self.refresh_history()
                    QMessageBox.information(self, "成功", "记录已删除")

    @Slot()
    def clear_history(self) -> None:
        """清空历史记录"""
        reply = QMessageBox.question(
            self,
            "确认清空",
            "确定要清空所有历史记录吗？\n此操作不可撤销！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            # 从数据库删除所有记录
            conn = self.database._conn if hasattr(self.database, "_conn") else None
            if not conn:
                import sqlite3

                conn = sqlite3.connect(self.database.db_path)

            cursor = conn.cursor()
            cursor.execute("DELETE FROM qrcodes")
            conn.commit()

            if not hasattr(self.database, "_conn"):
                conn.close()

            self.refresh_history()
            QMessageBox.information(self, "成功", "历史记录已清空")

    @Slot()
    def export_history(self) -> None:
        """导出历史记录"""
        qrcodes = self.database.get_all_qrcodes()
        if not qrcodes:
            QMessageBox.warning(self, "警告", "没有历史记录可导出")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出历史记录", "qr_history.json", "JSON文件 (*.json)"
        )

        if file_path:
            try:
                history_data = []
                for qr in qrcodes:
                    history_data.append(qr.to_dict())

                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(history_data, f, indent=2, ensure_ascii=False)

                QMessageBox.information(self, "成功", f"历史记录已导出到:\n{file_path}")

            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")

    def add_to_history(self, qr_data: QRCodeData, operation: str) -> None:
        """添加到历史记录"""
        # 刷新历史列表
        self.refresh_history()

    def update_info_panel(self, qr_data: QRCodeData) -> None:
        """更新信息面板"""
        info_text = f"""
<b>二维码信息</b>
<hr>
<strong>ID:</strong> {qr_data.id}<br>
<strong>类型:</strong> {qr_data.qr_type.value}<br>
<strong>版本:</strong> {qr_data.version if qr_data.version > 0 else '自动'}<br>
<strong>纠错级别:</strong> {qr_data.error_correction}<br>
<strong>模块大小:</strong> {qr_data.size}px<br>
<strong>边框:</strong> {qr_data.border}模块<br>
<strong>前景色:</strong> {qr_data.foreground_color}<br>
<strong>背景色:</strong> {qr_data.background_color}<br>
<strong>数据长度:</strong> {len(qr_data.data)} 字符<br>
<strong>创建时间:</strong> {qr_data.created_at}<br>
<strong>输出格式:</strong> {qr_data.output_format}<br>
"""

        if qr_data.logo_path:
            info_text += (
                f"<strong>Logo:</strong> {os.path.basename(qr_data.logo_path)}<br>"
            )
            # 安全地显示Logo缩放比例
            try:
                if hasattr(qr_data, "logo_scale") and qr_data.logo_scale:
                    scale_value = qr_data.logo_scale
                    if isinstance(scale_value, float) and scale_value <= 1:
                        scale_percent = int(scale_value * 100)
                    else:
                        scale_percent = int(scale_value)
                    info_text += f"<strong>Logo缩放:</strong> {scale_percent}%<br>"
                else:
                    info_text += f"<strong>Logo缩放:</strong> 20% (默认)<br>"
            except:
                info_text += f"<strong>Logo缩放:</strong> 20% (默认)<br>"

        if qr_data.gradient_start and qr_data.gradient_end:
            info_text += f"<strong>渐变:</strong> {qr_data.gradient_start} → {qr_data.gradient_end} ({qr_data.gradient_type})<br>"

        if qr_data.tags:
            info_text += f"<strong>标签:</strong> {', '.join(qr_data.tags)}<br>"

        if qr_data.notes:
            info_text += f"<strong>备注:</strong> {qr_data.notes}<br>"

        self.info_text.setHtml(info_text)

    # ==================== 文件操作 ====================
    def new_qrcode(self) -> None:
        """新建二维码"""
        self.data_text.clear()
        self.tags_edit.clear()
        self.notes_edit.clear()
        self.logo_path_edit.clear()
        # 重置Logo缩放比例为默认值
        self.logo_scale_spin.setValue(20)
        self.logo_scale_slider.setValue(20)
        self.status_bar.showMessage("已新建")

    def open_qrcode(self) -> None:
        """打开二维码文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "打开二维码图片",
            "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.gif *.webp)",
        )

        if file_path:
            # 扫描图片中的二维码
            self.file_list.clear()
            item = QListWidgetItem(file_path)
            item.setData(Qt.ItemDataRole.UserRole, file_path)
            self.file_list.addItem(item)

            # 切换到扫描选项卡并开始扫描
            self.tab_widget.setCurrentIndex(1)
            self.scan_file_radio.setChecked(True)
            self.start_scanning()

    def save_qrcode(self) -> None:
        """保存二维码"""
        if self.current_qr_image:
            self.preview_widget.save_image()
        else:
            QMessageBox.warning(self, "警告", "没有二维码可保存")

    def save_qrcode_as(self) -> None:
        """另存二维码"""
        if self.current_qr_image:
            self.preview_widget.save_image()
        else:
            QMessageBox.warning(self, "警告", "没有二维码可保存")

    def import_qrcode(self) -> None:
        """导入二维码配置"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "导入配置", "", "JSON文件 (*.json)"
        )

        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    config = json.load(f)

                # 创建QRCodeData对象
                qr_data = QRCodeData.from_dict(config)

                # 加载到界面
                self.load_qrcode_data(qr_data)

                QMessageBox.information(self, "成功", "配置导入成功")

            except Exception as e:
                QMessageBox.critical(self, "错误", f"导入失败: {str(e)}")

    def export_qrcode(self) -> None:
        """导出二维码配置"""
        if not self.current_qr_data:
            QMessageBox.warning(self, "警告", "没有二维码数据可导出")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出配置", "qrcode_config.json", "JSON文件 (*.json)"
        )

        if file_path:
            try:
                config = self.current_qr_data.to_dict()

                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)

                QMessageBox.information(self, "成功", f"配置已导出到:\n{file_path}")

            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")

    def print_qrcode(self) -> None:
        """打印二维码"""
        self.preview_widget.print_image()

    def copy_qrcode(self) -> None:
        """复制二维码"""
        if self.current_qr_image:
            self.preview_widget.copy_image()
        else:
            QMessageBox.warning(self, "警告", "没有二维码可复制")

    def paste_qrcode(self) -> None:
        """粘贴数据"""
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        if text:
            self.data_text.setText(text)
            self.update_preview()

    def clear_all(self) -> None:
        """清空所有输入"""
        self.new_qrcode()
        self.preview_widget.clear()
        self.info_text.clear()
        self.status_bar.showMessage("已清空")

    @Slot()
    def open_template_manager(self) -> None:
        """打开模板管理器"""
        from .template_manager import TemplateManager

        manager = TemplateManager(self)
        manager.template_selected.connect(self.apply_template)
        manager.exec()

    @Slot(dict)
    def apply_template(self, template: Dict) -> None:
        """应用模板"""
        config = template.get("config", {})

        # 根据模板设置参数
        if "color" in config:
            self.foreground_picker.set_color(config["color"])

        if "size" in config:
            self.size_spin.setValue(config["size"])

        if "border" in config:
            self.border_spin.setValue(config["border"])

        if "error_correction" in config:
            error_index = {"L": 0, "M": 1, "Q": 2, "H": 3}.get(
                config["error_correction"], 3
            )
            self.error_combo.setCurrentIndex(error_index)

        if "type" in config:
            index = self.type_combo.findText(config["type"])
            if index >= 0:
                self.type_combo.setCurrentIndex(index)

        if "gradient" in config:
            self.gradient_check.setChecked(True)
            self.gradient_start_picker.set_color(config["gradient"][0])
            self.gradient_end_picker.set_color(config["gradient"][1])

        # 安全地应用Logo缩放比例
        if "logo_scale" in config:
            try:
                scale_value = config["logo_scale"]
                # 处理可能是小数（0.2）或整数（20）的情况
                if isinstance(scale_value, float) and scale_value <= 1:
                    scale_percent = int(scale_value * 100)
                else:
                    scale_percent = int(scale_value)

                # 确保在有效范围内
                scale_percent = max(5, min(50, scale_percent))
                self.logo_scale_spin.setValue(scale_percent)
                self.logo_scale_slider.setValue(scale_percent)
            except (ValueError, TypeError):
                # 如果转换失败，使用默认值
                self.logo_scale_spin.setValue(20)
                self.logo_scale_slider.setValue(20)

        self.status_bar.showMessage(f"已应用模板: {template.get('name', '未知')}")

    @Slot()
    def save_as_template(self) -> None:
        """保存为模板"""
        if not self.current_qr_data:
            QMessageBox.warning(self, "警告", "没有二维码数据可保存为模板")
            return

        name, ok = QInputDialog.getText(self, "保存模板", "模板名称:")
        if ok and name:
            config = {
                "type": self.current_qr_data.qr_type.value,
                "size": self.current_qr_data.size,
                "border": self.current_qr_data.border,
                "error_correction": self.current_qr_data.error_correction,
                "color": self.current_qr_data.foreground_color,
                "gradient": (
                    [
                        (
                            self.current_qr_data.gradient_start
                            if self.current_qr_data.gradient_start
                            else "#000000"
                        ),
                        (
                            self.current_qr_data.gradient_end
                            if self.current_qr_data.gradient_end
                            else "#000000"
                        ),
                    ]
                    if self.current_qr_data.gradient_start
                    and self.current_qr_data.gradient_end
                    else None
                ),
                "logo_scale": (
                    self.current_qr_data.logo_scale
                    if hasattr(self.current_qr_data, "logo_scale")
                    else 0.2
                ),
            }

            if self.database.save_template(name, config):
                QMessageBox.information(self, "成功", "模板保存成功")
            else:
                QMessageBox.critical(self, "错误", "模板保存失败")

    @Slot()
    def open_batch_processor(self) -> None:
        """打开批量处理器"""
        from .batch_processor import BatchProcessor

        processor = BatchProcessor(self)
        processor.exec()
        self.refresh_history()

    @Slot()
    def open_settings(self) -> None:
        """打开设置对话框"""
        dialog = QDialog(self)
        dialog.setWindowTitle("设置")
        dialog.setMinimumWidth(400)

        layout = QFormLayout(dialog)

        # 默认设置
        default_size_spin = QSpinBox()
        default_size_spin.setRange(1, 50)
        default_size_spin.setValue(self.size_spin.value())

        default_border_spin = QSpinBox()
        default_border_spin.setRange(0, 10)
        default_border_spin.setValue(self.border_spin.value())

        default_format_combo = QComboBox()
        default_format_combo.addItems(["PNG", "JPEG", "SVG", "PDF"])
        default_format_combo.setCurrentText(self.format_combo.currentText())

        default_logo_scale_spin = QSpinBox()
        default_logo_scale_spin.setRange(5, 50)
        default_logo_scale_spin.setValue(self.logo_scale_spin.value())
        default_logo_scale_spin.setSuffix("%")
        default_logo_scale_spin.setToolTip("默认的Logo缩放比例")

        auto_save_check = QCheckBox("自动保存生成记录")
        auto_save_check.setChecked(True)

        preview_check = QCheckBox("启用实时预览")
        preview_check.setChecked(True)

        layout.addRow("默认模块大小:", default_size_spin)
        layout.addRow("默认边框大小:", default_border_spin)
        layout.addRow("默认输出格式:", default_format_combo)
        layout.addRow("默认Logo缩放比例:", default_logo_scale_spin)  # 新增
        layout.addRow("", auto_save_check)
        layout.addRow("", preview_check)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)

        layout.addRow(button_box)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            # 保存设置
            settings = QSettings(SETTINGS_VERSION.replace(" ", ""), SETTINGS_VERSION)
            settings.setValue("default_size", default_size_spin.value())
            settings.setValue("default_border", default_border_spin.value())
            settings.setValue("default_format", default_format_combo.currentText())
            settings.setValue("default_logo_scale", default_logo_scale_spin.value())
            settings.setValue("auto_save", auto_save_check.isChecked())
            settings.setValue("preview_enabled", preview_check.isChecked())

            # 应用设置
            self.size_spin.setValue(default_size_spin.value())
            self.border_spin.setValue(default_border_spin.value())

            # 确保在有效范围内
            logo_scale_val = max(5, min(50, default_logo_scale_spin.value()))
            self.logo_scale_spin.setValue(logo_scale_val)
            self.logo_scale_slider.setValue(logo_scale_val)

            index = self.format_combo.findText(default_format_combo.currentText())
            if index >= 0:
                self.format_combo.setCurrentIndex(index)

            QMessageBox.information(dialog, "成功", "设置已保存")

    @Slot()
    def show_about(self) -> None:
        """显示关于对话框"""
        about_text = """
<h1>QR Toolkit - 二维码工具箱</h1>
<p><strong>版本:</strong> 0.9.0</p>
<p><strong>作者:</strong> 码上工坊</p>
<p><strong>联系:</strong> 微信公众号（码上工坊）</p>
<p><strong>一个功能全面的二维码解决方案</strong></p>
<p><strong>功能特性:</strong></p>
<ul>
<li>二维码生成和扫描</li>
<li>批量处理和模板管理</li>
<li>历史记录和数据库支持</li>
<li>多种格式导出（PNG、JPEG、SVG、PDF）</li>
<li>高级编辑功能（渐变、Logo、Logo缩放）</li>
<li>文件扫描和摄像头扫描</li>
<li>批量生成和扫描</li>
</ul>
<p><strong>开源协议:</strong> MIT License</p>
<p><strong>版权:</strong> © 2026 码上工坊</p>
"""

        QMessageBox.about(self, "关于 QR Toolkit", about_text)

    @Slot()
    def show_documentation(self) -> None:
        """显示文档"""
        dialog = QDialog(self)
        dialog.setWindowTitle("使用说明")
        dialog.setMinimumSize(600, 800)

        layout = QVBoxLayout(dialog)

        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setHtml(self._get_documentation_text())

        layout.addWidget(text_edit)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        button_box.accepted.connect(dialog.accept)
        layout.addWidget(button_box)

        dialog.exec()

    def _get_documentation_text(self) -> str:
        """获取文档文本"""
        return """
<h2>QR Toolkit 使用说明</h2>

<h3>1. 生成二维码</h3>
<ol>
<li>在"数据设置"区域输入要编码的数据</li>
<li>选择二维码类型（URL、文本、WiFi等）</li>
<li>调整二维码参数（版本、纠错级别、大小、边框）</li>
<li>设置颜色（前景色、背景色，可选渐变）</li>
<li>可添加Logo（点击"浏览..."选择Logo图片）</li>
<li>可调节Logo缩放比例（5%-50%，建议15%-30%）</li>
<li>点击"生成二维码"按钮</li>
</ol>

<h3>2. 扫描二维码</h3>
<ol>
<li>切换到"扫描"选项卡</li>
<li>选择扫描方式（文件或摄像头）</li>
<li>添加要扫描的图片文件或选择摄像头</li>
<li>点击"开始扫描"按钮</li>
<li>查看扫描结果</li>
</ol>

<h3>3. 历史管理</h3>
<ol>
<li>切换到"历史"选项卡查看所有生成记录</li>
<li>双击记录可重新加载到编辑器</li>
<li>可删除、清空或导出历史记录</li>
</ol>

<h3>4. 模板功能</h3>
<ol>
<li>使用"模板管理器"创建和管理模板</li>
<li>可将当前设置（包括Logo缩放比例）保存为模板</li>
<li>应用模板时自动恢复所有参数</li>
</ol>

<h3>5. 快捷键</h3>
<ul>
<li>Ctrl+N: 新建</li>
<li>Ctrl+O: 打开</li>
<li>Ctrl+S: 保存</li>
<li>Ctrl+P: 打印</li>
<li>Ctrl+C: 复制</li>
<li>Ctrl+V: 粘贴</li>
<li>Ctrl++: 放大预览</li>
<li>Ctrl+-: 缩小预览</li>
<li>Ctrl+0: 重置缩放</li>
<li>Ctrl+1: 适应窗口</li>
</ul>

<h3>6. 高级功能</h3>
<ul>
<li>渐变二维码：启用渐变功能可创建彩色渐变二维码</li>
<li>Logo添加：支持添加自定义Logo到二维码中心，可调节缩放比例</li>
<li>批量处理：可批量生成或扫描多个二维码</li>
<li>多种输出格式：支持PNG、JPEG、SVG、PDF等格式</li>
</ul>
"""

    def __repr__(self) -> str:
        """返回字符串表示"""
        return f"QRToolkit(window_title='{self.windowTitle()}')"
