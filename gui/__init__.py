#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUI模块包初始化文件

包名称：qrcode_toolkit.gui
功能描述：二维码工具箱的图形用户界面模块
作者：码上工坊
联系：微信公众号（码上工坊）
版权声明：Copyright (c) 2026 码上工坊
开源协议：MIT License
免责声明：本软件按"原样"提供，不作任何明示或暗示的担保
修改记录：
版本 0.9.0 2026-2-10 - 码上工坊 - 初始版本创建
"""

from .batch_processor import BatchProcessor
from .main_window import QRToolkit
from .template_editor import TemplateEditor
from .template_manager import TemplateManager
from .widgets import ColorPickerButton, QRPreviewWidget

__all__ = [
    "ColorPickerButton",
    "QRPreviewWidget",
    "QRToolkit",
    "TemplateManager",
    "TemplateEditor",
    "BatchProcessor",
]
