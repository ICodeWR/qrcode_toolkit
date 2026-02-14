#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
常量模块单元测试

模块名称：test_constants.py
功能描述：测试 constants.py 中定义的所有常量和工具函数
"""

import re
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.constants import (
    APP_AUTHOR,
    APP_DATA_DIR,
    # 应用常量
    APP_NAME,
    APP_ORGANIZATION,
    APP_VERSION,
    BACKUPS_DIR,
    DEFAULT_DB_PATH,
    EXPORTS_DIR,
    SETTINGS_VERSION,
    # 路径常量
    USER_HOME,
    ColorConstants,
    DatabaseConstants,
    FileConstants,
    OutputFormat,
    # 常量类
    QRCodeConstants,
    # 枚举
    QRCodeType,
    RegexConstants,
    ScannerConstants,
    TemplateConstants,
    UIConstants,
    # 工具函数
    ensure_directories,
    is_valid_color,
)


class TestAppConstants:
    """测试应用程序常量"""

    def test_app_info(self):
        """测试应用信息常量"""
        assert APP_NAME == "QR Toolkit"
        assert APP_VERSION == "0.9.0"
        assert APP_AUTHOR == "码上工坊"
        assert APP_ORGANIZATION == "码上工坊"
        assert SETTINGS_VERSION == "v0.9.0"


class TestPathConstants:
    """测试路径常量"""

    def test_user_home(self):
        """测试用户目录"""
        assert USER_HOME == Path.home()

    def test_app_data_dir(self):
        """测试应用数据目录"""
        assert APP_DATA_DIR == USER_HOME / ".qrtoolkit"

    def test_db_path(self):
        """测试数据库路径"""
        assert DEFAULT_DB_PATH == APP_DATA_DIR / "qr_toolkit.db"

    def test_directories(self):
        """测试目录常量"""
        assert EXPORTS_DIR == APP_DATA_DIR / "exports"
        assert BACKUPS_DIR == APP_DATA_DIR / "backups"


class TestEnums:
    """测试枚举类型"""

    def test_qrcode_type_enum(self):
        """测试二维码类型枚举"""
        assert QRCodeType.URL.value == "URL"
        assert QRCodeType.TEXT.value == "文本"
        assert QRCodeType.WIFI.value == "WiFi"
        assert QRCodeType.VCARD.value == "电子名片"
        assert QRCodeType.EMAIL.value == "电子邮件"
        assert QRCodeType.PHONE.value == "电话"
        assert len(QRCodeType) >= 11

    def test_output_format_enum(self):
        """测试输出格式枚举"""
        assert OutputFormat.PNG.value == "PNG"
        assert OutputFormat.JPEG.value == "JPEG"
        assert OutputFormat.SVG.value == "SVG"
        assert OutputFormat.PDF.value == "PDF"
        assert len(OutputFormat) == 4


class TestFileConstants:
    """测试文件常量类"""

    def test_supported_image_formats(self):
        """测试支持的图片格式"""
        formats = FileConstants().SUPPORTED_IMAGE_FORMATS
        assert ".png" in formats
        assert ".jpg" in formats
        assert ".jpeg" in formats
        assert ".gif" in formats
        assert len(formats) >= 7


class TestScannerConstants:
    """测试扫描器常量类"""

    def test_camera_settings(self):
        """测试摄像头设置"""
        assert ScannerConstants().CAMERA_DEFAULT_INDEX == 0
        assert ScannerConstants().CAMERA_DEFAULT_WIDTH == 640
        assert ScannerConstants().CAMERA_DEFAULT_HEIGHT == 480
        assert ScannerConstants().CAMERA_DEFAULT_FPS == 30

    def test_scan_settings(self):
        """测试扫描设置"""
        assert ScannerConstants().SCAN_TIMEOUT == 30
        assert ScannerConstants().SCAN_INTERVAL == 100
        assert ScannerConstants().SCAN_MIN_CONFIDENCE == 0.3


class TestDatabaseConstants:
    """测试数据库常量类"""

    def test_table_names(self):
        """测试表名"""
        assert DatabaseConstants().TABLE_QRCODES == "qrcodes"
        assert DatabaseConstants().TABLE_HISTORY == "history"
        assert DatabaseConstants().TABLE_TEMPLATES == "templates"


class TestTemplateConstants:
    """测试模板常量类"""

    def test_categories(self):
        """测试模板分类"""
        categories = TemplateConstants().CATEGORIES
        assert "通用" in categories
        assert "商务" in categories
        assert len(categories) >= 8

    # ✅ 删除 PRESET_TEMPLATES 测试，因为它已被移除


class TestRegexConstants:
    """测试正则表达式常量类"""

    def test_color_hex_pattern(self):
        """测试颜色代码正则（唯一被使用的）"""
        pattern = RegexConstants().COLOR_HEX_PATTERN
        assert re.match(pattern, "#000000") is not None
        assert re.match(pattern, "#FFF") is not None
        assert re.match(pattern, "#GGGGGG") is None
        assert re.match(pattern, "000000") is None

    # ✅ 删除其他未使用正则的测试


class TestUtilityFunctions:
    """测试工具函数"""

    @patch("utils.constants.Path.exists")
    @patch("utils.constants.Path.mkdir")
    def test_ensure_directories(self, mock_mkdir, mock_exists):
        """测试确保目录存在"""
        mock_exists.return_value = False

        ensure_directories()

        # ✅ 修正为实际目录数量
        assert mock_mkdir.call_count >= 3  # APP_DATA_DIR, EXPORTS_DIR, BACKUPS_DIR
        mock_mkdir.assert_called_with(parents=True, exist_ok=True)

    def test_is_valid_color(self):
        """测试颜色验证"""
        assert is_valid_color("#000000") is True
        assert is_valid_color("#FFF") is True
        assert is_valid_color("#GGGGGG") is False
        assert is_valid_color("red") is False
        assert is_valid_color("") is False
