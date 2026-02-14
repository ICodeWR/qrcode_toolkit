#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工具模块 - QR Toolkit的工具函数和常量

模块名称：__init__.py
功能描述：QR Toolkit工具模块的初始化文件
作者：码上工坊
联系：微信公众号（码上工坊）
版权声明：Copyright (c) 2026 码上工坊
开源协议：MIT License
免责声明：本软件按"原样"提供，不作任何明示或暗示的担保
修改记录：
版本 0.9.0 2026-12-10 - 码上工坊 - 初始版本创建
"""

from .constants import (
    APP_AUTHOR,
    APP_DATA_DIR,
    # 应用常量
    APP_NAME,
    APP_ORGANIZATION,
    APP_VERSION,
    BACKUPS_DIR,
    DEFAULT_DB_PATH,
    EXPORTS_DIR,
    # 路径常量
    USER_HOME,
    FileConstants,
    OutputFormat,
    # 枚举
    QRCodeType,
    TemplateConstants,
    # 工具函数
    ensure_directories,
    is_valid_color,
)

# 为旧代码提供快捷方式

__all__ = [
    # 应用常量
    "APP_NAME",
    "APP_VERSION",
    "APP_AUTHOR",
    "APP_ORGANIZATION",
    # 路径常量
    "USER_HOME",
    "APP_DATA_DIR",
    "DEFAULT_DB_PATH",
    "EXPORTS_DIR",
    "BACKUPS_DIR",
    # 枚举
    "QRCodeType",
    "OutputFormat",
    "FileConstants",
    "TemplateConstants",
    # 工具函数
    "ensure_directories",
    "is_valid_color",
]
