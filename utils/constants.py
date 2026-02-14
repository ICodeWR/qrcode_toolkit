#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
常量定义模块 - QR Toolkit的所有常量定义

只保留实际使用的常量！
"""

from enum import Enum
from pathlib import Path
from typing import Final, Tuple

# ==================== 应用程序常量 ====================
APP_NAME: Final[str] = "QR Toolkit"
APP_VERSION: Final[str] = "0.9.0"
APP_AUTHOR: Final[str] = "码上工坊"
APP_ORGANIZATION: Final[str] = "码上工坊"
SETTINGS_VERSION = "v0.9.0"

# ==================== 文件路径常量 ====================
USER_HOME: Final[Path] = Path.home()
APP_DATA_DIR: Final[Path] = USER_HOME / ".qrtoolkit"
DEFAULT_DB_PATH: Final[Path] = APP_DATA_DIR / "qr_toolkit.db"
EXPORTS_DIR: Final[Path] = APP_DATA_DIR / "exports"
BACKUPS_DIR: Final[Path] = APP_DATA_DIR / "backups"


# ==================== 枚举类型 ====================
class QRCodeType(Enum):
    URL = "URL"
    TEXT = "文本"
    WIFI = "WiFi"
    VCARD = "电子名片"
    EMAIL = "电子邮件"
    SMS = "短信"
    PHONE = "电话"
    LOCATION = "地理位置"
    EVENT = "日历事件"
    BITCOIN = "比特币"
    CONTACT = "联系人"
    WHATSAPP = "WhatsApp"


class OutputFormat(Enum):
    PNG = "PNG"
    JPEG = "JPEG"
    SVG = "SVG"
    PDF = "PDF"


# ==================== 二维码常量 ====================
class QRCodeConstants:
    # 默认设置
    DEFAULT_VERSION: Final[int] = 0
    DEFAULT_ERROR_CORRECTION: Final[str] = "H"
    DEFAULT_SIZE: Final[int] = 10
    DEFAULT_BORDER: Final[int] = 4
    DEFAULT_FOREGROUND_COLOR: Final[str] = "#000000"
    DEFAULT_BACKGROUND_COLOR: Final[str] = "#FFFFFF"
    DEFAULT_OUTPUT_FORMAT: Final[str] = "PNG"

    # 范围限制
    MIN_VERSION: Final[int] = 1
    MAX_VERSION: Final[int] = 40
    MIN_MODULE_SIZE: Final[int] = 1
    MAX_MODULE_SIZE: Final[int] = 50
    MIN_BORDER_SIZE: Final[int] = 0
    MAX_BORDER_SIZE: Final[int] = 10


# ==================== 颜色常量 ====================
class ColorConstants:
    BLACK: Final[str] = "#000000"
    WHITE: Final[str] = "#FFFFFF"
    DEFAULT_FOREGROUND: Final[str] = BLACK
    DEFAULT_BACKGROUND: Final[str] = WHITE


# ==================== UI常量 ====================
class UIConstants:
    MAIN_WINDOW_WIDTH: Final[int] = 1400
    MAIN_WINDOW_HEIGHT: Final[int] = 800
    MAIN_WINDOW_MIN_WIDTH: Final[int] = 800
    MAIN_WINDOW_MIN_HEIGHT: Final[int] = 600
    CONTROL_PANEL_MIN_WIDTH: Final[int] = 350
    CONTROL_PANEL_MAX_WIDTH: Final[int] = 500
    PREVIEW_MIN_WIDTH: Final[int] = 300
    PREVIEW_MIN_HEIGHT: Final[int] = 300


# ==================== 文件常量 ====================
class FileConstants:
    SUPPORTED_IMAGE_FORMATS: Final[Tuple[str, ...]] = (
        ".png",
        ".jpg",
        ".jpeg",
        ".bmp",
        ".gif",
        ".tiff",
        ".webp",
    )


# ==================== 扫描器常量 ====================
class ScannerConstants:
    CAMERA_DEFAULT_INDEX: Final[int] = 0
    CAMERA_DEFAULT_WIDTH: Final[int] = 640
    CAMERA_DEFAULT_HEIGHT: Final[int] = 480
    CAMERA_DEFAULT_FPS: Final[int] = 30
    SCAN_TIMEOUT: Final[int] = 30
    SCAN_INTERVAL: Final[int] = 100
    SCAN_MIN_CONFIDENCE: Final[float] = 0.3


# ==================== 数据库常量 ====================
class DatabaseConstants:
    TABLE_QRCODES: Final[str] = "qrcodes"
    TABLE_HISTORY: Final[str] = "history"
    TABLE_TEMPLATES: Final[str] = "templates"
    DEFAULT_LIMIT: Final[int] = 100
    DEFAULT_OFFSET: Final[int] = 0


# ==================== 模板常量 ====================
class TemplateConstants:
    CATEGORIES: Final[Tuple[str, ...]] = (
        "通用",
        "商务",
        "个人",
        "社交",
        "支付",
        "网络",
        "联系方式",
        "其他",
    )


class RegexConstants:
    """正则表达式常量类"""

    # URL正则
    URL_PATTERN: Final[str] = r"^(https?|ftp)://[^\s/$.?#].[^\s]*$"

    # 电子邮件正则
    EMAIL_PATTERN: Final[str] = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

    # 电话号码正则
    PHONE_PATTERN: Final[str] = r"^\+?[1-9]\d{6,14}$"

    # 颜色代码正则
    COLOR_HEX_PATTERN: Final[str] = r"^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$"

    # WiFi配置正则
    WIFI_PATTERN: Final[str] = (
        r"^WIFI:(?:S:(?P<ssid>[^;]+);)?(?:T:(?P<auth>[^;]+);)?(?:P:(?P<password>[^;]+);)?(?:H:(?P<hidden>[^;]+);)?;$"
    )


# ==================== 工具函数 ====================
def ensure_directories() -> None:
    """确保所有必要的目录都存在"""
    directories = [APP_DATA_DIR, EXPORTS_DIR, BACKUPS_DIR]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


def is_valid_color(color_str: str) -> bool:
    """检查颜色字符串是否有效"""
    import re

    return bool(re.match(RegexConstants.COLOR_HEX_PATTERN, color_str))
