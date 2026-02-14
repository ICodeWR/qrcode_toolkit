"""
QR Toolkit - 二维码工具箱
数据模型模块的单元测试

作者: 码上工坊
仓库: https://gitee.com/icodewr/QRToolkit
协议: MIT License
"""

import json
from datetime import datetime

import pytest

from core.models import OutputFormat, QRCodeData, QRCodeType
from utils.constants import is_valid_color


class TestQRCodeType:
    """QRCodeType枚举测试"""

    def test_qrcode_type_values(self):
        """测试QRCodeType枚举值"""
        # 根据 constants.py，BITCOIN的值是"比特币"
        assert QRCodeType.URL.value == "URL"
        assert QRCodeType.TEXT.value == "文本"
        assert QRCodeType.WIFI.value == "WiFi"
        assert QRCodeType.VCARD.value == "电子名片"
        assert QRCodeType.EMAIL.value == "电子邮件"
        assert QRCodeType.SMS.value == "短信"
        assert QRCodeType.PHONE.value == "电话"
        assert QRCodeType.LOCATION.value == "地理位置"
        assert QRCodeType.EVENT.value == "日历事件"
        assert QRCodeType.BITCOIN.value == "比特币"  # 修正为实际值
        assert (
            QRCodeType.WHATSAPP.value == "WhatsApp"
        )  # 注意：在constants.py中是"WhatsApp"，不是"WhatsApp消息"
        assert QRCodeType.CONTACT.value == "联系人"

    def test_qrcode_type_from_string(self):
        """测试从字符串创建枚举"""
        # 注意：这里需要使用枚举的实际字符串值
        assert QRCodeType("URL") == QRCodeType.URL
        assert QRCodeType("文本") == QRCodeType.TEXT
        assert QRCodeType("WiFi") == QRCodeType.WIFI

    def test_qrcode_type_invalid_string(self):
        """测试无效字符串创建枚举"""
        with pytest.raises(ValueError):
            QRCodeType("无效类型")


class TestOutputFormat:
    """OutputFormat枚举测试"""

    def test_output_format_values(self):
        """测试OutputFormat枚举值"""
        # 根据 constants.py，OutputFormat有PNG、JPEG、SVG、PDF、GIF、BMP，没有BASE64和EPS
        assert OutputFormat.PNG.value == "PNG"
        assert OutputFormat.JPEG.value == "JPEG"
        assert OutputFormat.SVG.value == "SVG"
        assert OutputFormat.PDF.value == "PDF"

        # 检查BASE64不存在
        assert not hasattr(OutputFormat, "BASE64")
        assert not hasattr(OutputFormat, "EPS")

    def test_output_format_from_string(self):
        """测试从字符串创建枚举"""
        assert OutputFormat("PNG") == OutputFormat.PNG
        assert OutputFormat("JPEG") == OutputFormat.JPEG
        assert OutputFormat("SVG") == OutputFormat.SVG


class TestQRCodeData:
    """QRCodeData类测试"""

    @pytest.fixture
    def sample_data(self):
        """创建测试数据"""
        return {
            "id": "test1234",
            "data": "https://example.com",
            "qr_type": QRCodeType.URL,
            "version": 5,
            "error_correction": "H",
            "size": 10,
            "border": 4,
            "foreground_color": "#000000",
            "background_color": "#FFFFFF",
            "logo_path": None,
            "gradient_start": None,
            "gradient_end": None,
            "gradient_type": "linear",
            "created_at": "2024-01-01T12:00:00",
            "tags": ["work", "personal"],
            "notes": "测试备注",
            "output_format": "PNG",
        }

    def test_create_with_defaults(self):
        """测试使用默认值创建QRCodeData"""
        qr_data = QRCodeData(
            id="test123",
            data="测试数据",
            qr_type=QRCodeType.TEXT,
            version=0,
            error_correction="L",
            size=5,
            border=2,
            foreground_color="#000000",
            background_color="#FFFFFF",
        )

        assert qr_data.id == "test123"
        assert qr_data.data == "测试数据"
        assert qr_data.qr_type == QRCodeType.TEXT
        assert qr_data.version == 0
        assert qr_data.error_correction == "L"
        assert qr_data.size == 5
        assert qr_data.border == 2
        assert qr_data.foreground_color == "#000000"
        assert qr_data.background_color == "#FFFFFF"
        assert qr_data.logo_path is None
        assert qr_data.gradient_start is None
        assert qr_data.gradient_end is None
        assert qr_data.gradient_type == "linear"
        assert qr_data.created_at != ""
        assert qr_data.tags == []
        # 根据 models.py，notes 字段默认为 None
        assert qr_data.notes is None
        assert qr_data.output_format == "PNG"

    def test_post_init_without_created_at(self):
        """测试未提供创建时间时的自动生成"""
        qr_data = QRCodeData(
            id="test123",
            data="测试数据",
            qr_type=QRCodeType.TEXT,
            version=0,
            error_correction="L",
            size=5,
            border=2,
            foreground_color="#000000",
            background_color="#FFFFFF",
            created_at="",
        )

        assert qr_data.created_at != ""
        # 验证时间格式
        try:
            datetime.fromisoformat(qr_data.created_at)
        except ValueError:
            pytest.fail(f"无效的时间格式: {qr_data.created_at}")

    def test_post_init_with_tags_none(self):
        """测试标签为None时的初始化"""
        qr_data = QRCodeData(
            id="test123",
            data="测试数据",
            qr_type=QRCodeType.TEXT,
            version=0,
            error_correction="L",
            size=5,
            border=2,
            foreground_color="#000000",
            background_color="#FFFFFF",
            tags=None,
        )

        assert qr_data.tags == []

    def test_generate_id(self):
        """测试生成ID"""
        data = "测试数据内容"
        id1 = QRCodeData.generate_id(data)
        id2 = QRCodeData.generate_id(data)

        # ID应该是8位十六进制字符串
        assert len(id1) == 8
        assert all(c in "0123456789abcdef" for c in id1)

        # 两次生成的ID应该不同（因为时间戳不同）
        assert id1 != id2

    def test_to_dict(self):
        """测试转换为字典"""
        qr_data = QRCodeData(
            id="test123",
            data="https://example.com",
            qr_type=QRCodeType.URL,
            version=5,
            error_correction="H",
            size=10,
            border=4,
            foreground_color="#000000",
            background_color="#FFFFFF",
            tags=["test"],
            notes="测试备注",
        )

        result = qr_data.to_dict()

        assert result["id"] == "test123"
        assert result["data"] == "https://example.com"
        assert result["qr_type"] == "URL"  # 应该是字符串值，不是枚举
        assert result["version"] == 5
        assert result["error_correction"] == "H"
        assert result["size"] == 10
        assert result["border"] == 4
        assert result["foreground_color"] == "#000000"
        assert result["background_color"] == "#FFFFFF"
        assert result["tags"] == ["test"]
        assert result["notes"] == "测试备注"

    def test_from_dict_with_enum(self):
        """测试从字典创建（使用枚举）"""
        data_dict = {
            "id": "test123",
            "data": "测试数据",
            "qr_type": QRCodeType.TEXT,
            "version": 3,
            "error_correction": "M",
            "size": 8,
            "border": 2,
            "foreground_color": "#FF0000",
            "background_color": "#00FF00",
        }

        qr_data = QRCodeData.from_dict(data_dict)

        assert qr_data.qr_type == QRCodeType.TEXT

    def test_from_dict_with_string(self):
        """测试从字典创建（使用字符串）"""
        # 注意：需要根据枚举的实际值使用正确的字符串
        data_dict = {
            "id": "test123",
            "data": "测试数据",
            "qr_type": "文本",  # 使用枚举的实际值，不是枚举名
            "version": 3,
            "error_correction": "M",
            "size": 8,
            "border": 2,
            "foreground_color": "#FF0000",
            "background_color": "#00FF00",
        }

        qr_data = QRCodeData.from_dict(data_dict)

        assert qr_data.qr_type == QRCodeType.TEXT

    def test_from_dict_with_invalid_type(self):
        """测试从字典创建（无效类型）"""
        data_dict = {
            "id": "test123",
            "data": "测试数据",
            "qr_type": 123,  # 无效类型
            "version": 3,
            "error_correction": "M",
            "size": 8,
            "border": 2,
            "foreground_color": "#FF0000",
            "background_color": "#00FF00",
        }

        with pytest.raises(ValueError, match="无效的qr_type值"):
            QRCodeData.from_dict(data_dict)

    def test_from_dict_with_tags_string(self):
        """测试从字典创建（标签为JSON字符串）"""
        data_dict = {
            "id": "test123",
            "data": "测试数据",
            "qr_type": "文本",  # 使用枚举的实际值
            "version": 3,
            "error_correction": "M",
            "size": 8,
            "border": 2,
            "foreground_color": "#FF0000",
            "background_color": "#00FF00",
            "tags": '["tag1", "tag2"]',  # JSON字符串
        }

        qr_data = QRCodeData.from_dict(data_dict)

        assert qr_data.tags == ["tag1", "tag2"]

    def test_from_dict_with_empty_tags_string(self):
        """测试从字典创建（空标签字符串）"""
        data_dict = {
            "id": "test123",
            "data": "测试数据",
            "qr_type": "文本",  # 使用枚举的实际值
            "version": 3,
            "error_correction": "M",
            "size": 8,
            "border": 2,
            "foreground_color": "#FF0000",
            "background_color": "#00FF00",
            "tags": "",  # 空字符串
        }

        qr_data = QRCodeData.from_dict(data_dict)

        assert qr_data.tags == []

    def test_validate_valid_data(self):
        """测试验证有效数据"""
        qr_data = QRCodeData(
            id="test123",
            data="有效数据",
            qr_type=QRCodeType.TEXT,
            version=5,
            error_correction="H",
            size=10,
            border=4,
            foreground_color="#000000",
            background_color="#FFFFFF",
        )

        is_valid, message = qr_data.validate()
        assert is_valid is True
        assert message == "数据有效"

    def test_validate_empty_data(self):
        """测试验证空数据"""
        qr_data = QRCodeData(
            id="test123",
            data="",
            qr_type=QRCodeType.TEXT,
            version=5,
            error_correction="H",
            size=10,
            border=4,
            foreground_color="#000000",
            background_color="#FFFFFF",
        )

        is_valid, message = qr_data.validate()
        assert is_valid is False
        assert "二维码数据不能为空" in message

    def test_validate_invalid_size(self):
        """测试验证无效大小"""
        qr_data = QRCodeData(
            id="test123",
            data="测试数据",
            qr_type=QRCodeType.TEXT,
            version=5,
            error_correction="H",
            size=0,  # 无效大小
            border=4,
            foreground_color="#000000",
            background_color="#FFFFFF",
        )

        is_valid, message = qr_data.validate()
        assert is_valid is False
        assert "模块大小必须在1到50之间" in message

    def test_validate_invalid_border(self):
        """测试验证无效边框"""
        qr_data = QRCodeData(
            id="test123",
            data="测试数据",
            qr_type=QRCodeType.TEXT,
            version=5,
            error_correction="H",
            size=10,
            border=11,  # 无效边框
            foreground_color="#000000",
            background_color="#FFFFFF",
        )

        is_valid, message = qr_data.validate()
        assert is_valid is False
        assert "边框大小必须在0到10之间" in message

    def test_validate_invalid_version(self):
        """测试验证无效版本"""
        qr_data = QRCodeData(
            id="test123",
            data="测试数据",
            qr_type=QRCodeType.TEXT,
            version=41,  # 无效版本
            error_correction="H",
            size=10,
            border=4,
            foreground_color="#000000",
            background_color="#FFFFFF",
        )

        is_valid, message = qr_data.validate()
        assert is_valid is False
        assert "版本必须在0到40之间" in message

    def test_validate_invalid_error_correction(self):
        """测试验证无效纠错级别"""
        qr_data = QRCodeData(
            id="test123",
            data="测试数据",
            qr_type=QRCodeType.TEXT,
            version=5,
            error_correction="X",  # 无效纠错级别
            size=10,
            border=4,
            foreground_color="#000000",
            background_color="#FFFFFF",
        )

        is_valid, message = qr_data.validate()
        assert is_valid is False
        assert "纠错级别必须是L、M、Q或H" in message

    def test_validate_invalid_color_format(self):
        """测试验证无效颜色格式"""
        qr_data = QRCodeData(
            id="test123",
            data="测试数据",
            qr_type=QRCodeType.TEXT,
            version=5,
            error_correction="H",
            size=10,
            border=4,
            foreground_color="invalid_color",  # 无效颜色格式
            background_color="#FFFFFF",
        )

        is_valid, message = qr_data.validate()
        assert is_valid is False
        assert "前景色格式无效" in message

    def test_validate_gradient_missing_end(self):
        """测试验证渐变缺少结束颜色"""
        qr_data = QRCodeData(
            id="test123",
            data="测试数据",
            qr_type=QRCodeType.TEXT,
            version=5,
            error_correction="H",
            size=10,
            border=4,
            foreground_color="#000000",
            background_color="#FFFFFF",
            gradient_start="#FF0000",  # 有起始颜色
            gradient_end=None,  # 无结束颜色
        )

        is_valid, message = qr_data.validate()
        assert is_valid is False
        assert "渐变必须同时设置起始和结束颜色" in message

    def test_validate_gradient_missing_start(self):
        """测试验证渐变缺少起始颜色"""
        qr_data = QRCodeData(
            id="test123",
            data="测试数据",
            qr_type=QRCodeType.TEXT,
            version=5,
            error_correction="H",
            size=10,
            border=4,
            foreground_color="#000000",
            background_color="#FFFFFF",
            gradient_start=None,  # 无起始颜色
            gradient_end="#00FF00",  # 有结束颜色
        )

        is_valid, message = qr_data.validate()
        assert is_valid is False
        assert "渐变必须同时设置起始和结束颜色" in message

    def test_validate_invalid_gradient_type(self):
        """测试验证无效渐变类型"""
        qr_data = QRCodeData(
            id="test123",
            data="测试数据",
            qr_type=QRCodeType.TEXT,
            version=5,
            error_correction="H",
            size=10,
            border=4,
            foreground_color="#000000",
            background_color="#FFFFFF",
            gradient_start="#FF0000",
            gradient_end="#00FF00",
            gradient_type="invalid",  # 无效渐变类型
        )

        is_valid, message = qr_data.validate()
        assert is_valid is False
        assert "渐变类型必须是linear或radial" in message

    def test_color_validation(self):
        """测试颜色验证工具函数"""
        # 测试有效颜色
        assert is_valid_color("#000000") is True
        assert is_valid_color("#FFF") is True  # 3位十六进制
        assert is_valid_color("#123456") is True  # 6位十六进制
        assert is_valid_color("#abcdef") is True  # 小写字母
        assert is_valid_color("#ABCDEF") is True  # 大写字母

        # 测试无效颜色
        assert is_valid_color("") is False
        assert is_valid_color("#") is False
        assert is_valid_color("#12") is False
        assert is_valid_color("#12345") is False  # 5位
        assert is_valid_color("#1234567") is False  # 7位
        assert is_valid_color("#GGGGGG") is False  # 无效字符
        assert is_valid_color("000000") is False  # 缺少#
        assert is_valid_color("#XYZ") is False  # 无效十六进制

    def test_get_info_summary(self):
        """测试获取信息摘要"""
        qr_data = QRCodeData(
            id="test123",
            data="https://example.com",
            qr_type=QRCodeType.URL,
            version=5,
            error_correction="H",
            size=10,
            border=4,
            foreground_color="#000000",
            background_color="#FFFFFF",
            tags=["work", "test"],
            notes="这是一个测试二维码，用于单元测试",
        )

        summary = qr_data.get_info_summary()

        # 检查是否包含关键信息
        assert "二维码ID: test123" in summary
        assert "类型: URL" in summary
        assert "版本: 5" in summary
        assert "纠错级别: H" in summary
        assert "模块大小: 10px" in summary
        assert "边框: 4模块" in summary
        assert "前景色: #000000" in summary
        assert "背景色: #FFFFFF" in summary
        assert "数据长度: 19 字符" in summary
        assert "标签: work, test" in summary
        assert "备注: 这是一个测试二维码，用于单元测试" in summary

    def test_get_info_summary_with_logo(self):
        """测试带Logo的信息摘要"""
        qr_data = QRCodeData(
            id="test123",
            data="测试数据",
            qr_type=QRCodeType.TEXT,
            version=5,
            error_correction="H",
            size=10,
            border=4,
            foreground_color="#000000",
            background_color="#FFFFFF",
            logo_path="/path/to/logo.png",
        )

        summary = qr_data.get_info_summary()
        assert "Logo: /path/to/logo.png" in summary

    def test_get_info_summary_with_gradient(self):
        """测试带渐变的信息摘要"""
        qr_data = QRCodeData(
            id="test123",
            data="测试数据",
            qr_type=QRCodeType.TEXT,
            version=5,
            error_correction="H",
            size=10,
            border=4,
            foreground_color="#000000",
            background_color="#FFFFFF",
            gradient_start="#FF0000",
            gradient_end="#00FF00",
            gradient_type="linear",
        )

        summary = qr_data.get_info_summary()
        assert "渐变: #FF0000 → #00FF00 (linear)" in summary

    def test_get_info_summary_with_long_notes(self):
        """测试长备注的信息摘要"""
        long_notes = "这是一个非常长的备注，用于测试摘要截断功能。" * 10
        qr_data = QRCodeData(
            id="test123",
            data="测试数据",
            qr_type=QRCodeType.TEXT,
            version=5,
            error_correction="H",
            size=10,
            border=4,
            foreground_color="#000000",
            background_color="#FFFFFF",
            notes=long_notes,
        )

        summary = qr_data.get_info_summary()
        assert "..." in summary  # 应该被截断
        assert len(qr_data.notes) > 50  # 确保备注确实很长

    def test_repr(self):
        """测试字符串表示"""
        qr_data = QRCodeData(
            id="test123",
            data="测试数据",
            qr_type=QRCodeType.TEXT,
            version=5,
            error_correction="H",
            size=10,
            border=4,
            foreground_color="#000000",
            background_color="#FFFFFF",
        )

        repr_str = repr(qr_data)
        assert "QRCodeData" in repr_str
        assert "id='test123'" in repr_str
        # repr 中显示的是枚举的repr，不是简单的名字
        # 所以是 "qr_type=<QRCodeType.TEXT: '文本'>" 而不是 "qr_type=QRCodeType.TEXT"
        assert "qr_type=<QRCodeType.TEXT:" in repr_str
        assert "'文本'>" in repr_str
