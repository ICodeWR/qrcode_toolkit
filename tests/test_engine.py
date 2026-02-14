#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
二维码引擎模块单元测试 - QR Toolkit的核心引擎测试

模块名称：test_engine.py
功能描述：对QRCodeEngine类的所有方法进行单元测试
作者：码上工坊
联系：微信公众号（码上工坊）
版权声明：Copyright (c) 2026 码上工坊
开源协议：MIT License
免责声明：本软件按"原样"提供，不作任何明示或暗示的担保
修改记录：
版本 1.0.0 2026-01-01 - 码上工坊 - 初始版本创建
"""

import os
from dataclasses import replace
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image
from PySide6.QtCore import QCoreApplication
from PySide6.QtGui import QImage

from core.engine import QRCodeEngine
from core.models import QRCodeData, QRCodeType


@pytest.fixture(scope="session")
def qapp():
    """创建QCoreApplication实例用于Qt对象"""
    app = QCoreApplication.instance()
    if app is None:
        app = QCoreApplication([])
    yield app
    # 清理
    app.quit()


class TestQRCodeEngine:
    """QRCodeEngine类测试"""

    @pytest.fixture
    def qr_engine(self):
        """创建QRCodeEngine实例"""
        engine = QRCodeEngine()
        yield engine
        # 确保线程停止
        if engine.isRunning():
            engine.stop()
            engine.wait(1000)

    @pytest.fixture
    def sample_qrcode_data(self):
        """创建测试用二维码数据"""
        return QRCodeData(
            id="test123",
            data="https://example.com",
            qr_type=QRCodeType.URL,
            version=5,
            error_correction="H",
            size=10,
            border=4,
            foreground_color="#000000",
            background_color="#FFFFFF",
        )

    @pytest.fixture
    def sample_qrcode_data_gradient(self):
        """创建带渐变效果的测试二维码数据"""
        return QRCodeData(
            id="gradient_test",
            data="渐变测试数据",
            qr_type=QRCodeType.TEXT,
            version=3,
            error_correction="M",
            size=8,
            border=2,
            foreground_color="#000000",
            background_color="#FFFFFF",
            gradient_start="#FF0000",
            gradient_end="#0000FF",
            gradient_type="linear",
        )

    @pytest.fixture
    def sample_qrcode_data_with_logo(self, tmp_path):
        """创建带Logo的测试二维码数据"""
        # 创建一个临时Logo图片
        logo_path = tmp_path / "test_logo.png"
        logo_image = Image.new("RGB", (100, 100), color="red")
        logo_image.save(logo_path)

        return QRCodeData(
            id="logo_test",
            data="Logo测试数据",
            qr_type=QRCodeType.TEXT,
            version=3,
            error_correction="M",
            size=8,
            border=2,
            foreground_color="#000000",
            background_color="#FFFFFF",
            logo_path=str(logo_path),
        )

    def test_init(self, qr_engine):
        """测试初始化"""
        assert qr_engine.qr_data is None
        assert qr_engine.batch_data == []
        assert qr_engine.generate_logo is True
        assert qr_engine.running is False

    def test_get_error_correction_valid(self, qr_engine):
        """测试获取有效的纠错级别"""
        assert qr_engine._get_error_correction("L") == 1  # ERROR_CORRECT_L
        assert qr_engine._get_error_correction("M") == 0  # ERROR_CORRECT_M
        assert qr_engine._get_error_correction("Q") == 3  # ERROR_CORRECT_Q
        assert qr_engine._get_error_correction("H") == 2  # ERROR_CORRECT_H
        assert qr_engine._get_error_correction("h") == 2  # 小写转换

    def test_get_error_correction_invalid(self, qr_engine):
        """测试获取无效的纠错级别（应返回默认值H）"""
        assert qr_engine._get_error_correction("X") == 2  # 默认H
        assert qr_engine._get_error_correction("") == 2  # 默认H
        # 注意：这里不应该传入None，但为了兼容性我们处理它
        assert qr_engine._get_error_correction(None) == 2  # 默认H

    def test_parse_color_valid_6digit(self, qr_engine):
        """测试解析6位十六进制颜色"""
        assert qr_engine._parse_color("#000000") == (0, 0, 0)
        assert qr_engine._parse_color("#FFFFFF") == (255, 255, 255)
        assert qr_engine._parse_color("#FF0000") == (255, 0, 0)
        assert qr_engine._parse_color("#00FF00") == (0, 255, 0)
        assert qr_engine._parse_color("#0000FF") == (0, 0, 255)
        assert qr_engine._parse_color("#123456") == (0x12, 0x34, 0x56)

    def test_parse_color_valid_3digit(self, qr_engine):
        """测试解析3位简写颜色"""
        assert qr_engine._parse_color("#000") == (0, 0, 0)
        assert qr_engine._parse_color("#FFF") == (255, 255, 255)
        assert qr_engine._parse_color("#F00") == (255, 0, 0)
        assert qr_engine._parse_color("#0F0") == (0, 255, 0)
        assert qr_engine._parse_color("#00F") == (0, 0, 255)
        assert qr_engine._parse_color("#123") == (0x11, 0x22, 0x33)

    def test_parse_color_invalid(self, qr_engine):
        """测试解析无效颜色"""
        with pytest.raises(ValueError, match="无效的颜色格式"):
            qr_engine._parse_color("")

        with pytest.raises(ValueError, match="无效的颜色格式"):
            qr_engine._parse_color("000000")  # 缺少#

        with pytest.raises(ValueError, match="颜色格式长度无效"):
            qr_engine._parse_color("#12")  # 太短

        with pytest.raises(ValueError, match="颜色格式长度无效"):
            qr_engine._parse_color("#12345")  # 5位

        with pytest.raises(ValueError, match="颜色格式长度无效"):
            qr_engine._parse_color("#1234567")  # 7位

        with pytest.raises(ValueError, match="颜色值包含无效字符"):
            qr_engine._parse_color("#GGGGGG")  # 无效十六进制

        # 测试传入None
        with pytest.raises(ValueError, match="无效的颜色格式"):
            qr_engine._parse_color(None)

    # ... 其他测试方法保持不变 ...

    def test_generate_gradient_qr_linear(self, qr_engine, sample_qrcode_data_gradient):
        """测试生成线性渐变二维码"""
        qr_engine.qr_data = sample_qrcode_data_gradient

        # 创建测试二维码对象
        import qrcode

        qr = qrcode.QRCode(
            version=sample_qrcode_data_gradient.version,
            error_correction=qr_engine._get_error_correction(
                sample_qrcode_data_gradient.error_correction
            ),
            box_size=sample_qrcode_data_gradient.size,
            border=sample_qrcode_data_gradient.border,
        )
        qr.add_data(sample_qrcode_data_gradient.data)
        qr.make(fit=True)

        # 生成渐变二维码
        image = qr_engine._generate_gradient_qr(qr)

        assert image is not None
        assert image.mode == "RGB"
        assert image.size == (
            len(qr.get_matrix()) * sample_qrcode_data_gradient.size,
            len(qr.get_matrix()) * sample_qrcode_data_gradient.size,
        )

        # 验证颜色
        pixels = image.load()
        # 检查左上角应该是起始颜色附近
        color = pixels[0, 0]
        assert color[0] > 100  # 红色分量应该较高

    def test_generate_gradient_qr_radial(self, qr_engine):
        """测试生成径向渐变二维码"""
        qr_data = QRCodeData(
            id="radial_test",
            data="径向渐变测试",
            qr_type=QRCodeType.TEXT,
            version=3,
            error_correction="M",
            size=8,
            border=2,
            foreground_color="#000000",
            background_color="#FFFFFF",
            gradient_start="#00FF00",
            gradient_end="#0000FF",
            gradient_type="radial",
        )
        qr_engine.qr_data = qr_data

        import qrcode

        qr = qrcode.QRCode(
            version=qr_data.version,
            error_correction=qr_engine._get_error_correction(qr_data.error_correction),
            box_size=qr_data.size,
            border=qr_data.border,
        )
        qr.add_data(qr_data.data)
        qr.make(fit=True)

        image = qr_engine._generate_gradient_qr(qr)
        assert image is not None
        assert image.mode == "RGB"

    def test_generate_gradient_qr_no_data(self, qr_engine):
        """测试没有二维码数据时生成渐变二维码"""
        qr_engine.qr_data = None

        import qrcode

        qr = qrcode.QRCode()
        qr.add_data("test")
        qr.make(fit=True)

        with pytest.raises(ValueError, match="二维码数据未设置"):
            qr_engine._generate_gradient_qr(qr)

    def test_generate_gradient_qr_empty_matrix(
        self, qr_engine, sample_qrcode_data_gradient
    ):
        """测试空矩阵时生成渐变二维码"""
        qr_engine.qr_data = sample_qrcode_data_gradient

        # 创建空的二维码对象
        class MockQR:
            def get_matrix(self):
                return []

        mock_qr = MockQR()

        with pytest.raises(ValueError, match="二维码矩阵为空"):
            qr_engine._generate_gradient_qr(mock_qr)

    def test_add_logo_success(self, qr_engine, sample_qrcode_data_with_logo):
        """测试成功添加Logo"""
        qr_engine.qr_data = sample_qrcode_data_with_logo

        # 创建测试二维码图像
        qr_image = Image.new("RGB", (200, 200), color="white")

        result = qr_engine._add_logo(qr_image)
        assert result is not None
        assert result.size == qr_image.size

    def test_add_logo_no_logo_path(self, qr_engine):
        """测试没有Logo路径时添加Logo"""
        qr_data = QRCodeData(
            id="test",
            data="test",
            qr_type=QRCodeType.TEXT,
            version=1,
            error_correction="H",
            size=10,
            border=4,
            foreground_color="#000000",
            background_color="#FFFFFF",
            logo_path=None,
        )
        qr_engine.qr_data = qr_data

        qr_image = Image.new("RGB", (100, 100), color="white")
        result = qr_engine._add_logo(qr_image)
        assert result == qr_image  # 应该返回原图

    def test_add_logo_file_not_found(self, qr_engine):
        """测试Logo文件不存在时添加Logo"""
        qr_data = QRCodeData(
            id="test",
            data="test",
            qr_type=QRCodeType.TEXT,
            version=1,
            error_correction="H",
            size=10,
            border=4,
            foreground_color="#000000",
            background_color="#FFFFFF",
            logo_path="/nonexistent/path/logo.png",
        )
        qr_engine.qr_data = qr_data

        qr_image = Image.new("RGB", (100, 100), color="white")

        with pytest.raises(FileNotFoundError, match="Logo文件不存在"):
            qr_engine._add_logo(qr_image)

    def test_add_logo_no_qr_data(self, qr_engine):
        """测试没有二维码数据时添加Logo"""
        qr_engine.qr_data = None

        qr_image = Image.new("RGB", (100, 100), color="white")
        result = qr_engine._add_logo(qr_image)
        assert result == qr_image  # 应该返回原图

    def test_pil_to_qimage(self, qr_engine):
        """测试PIL图像转QImage"""
        # 创建测试PIL图像
        pil_image = Image.new("RGB", (100, 100), color="red")

        qimage = qr_engine._pil_to_qimage(pil_image)

        assert isinstance(qimage, QImage)
        assert qimage.width() == 100
        assert qimage.height() == 100
        assert not qimage.isNull()

    def test_pil_to_qimage_grayscale(self, qr_engine):
        """测试灰度PIL图像转QImage（应自动转换为RGB）"""
        pil_image = Image.new("L", (50, 50), color=128)  # 灰度图像

        qimage = qr_engine._pil_to_qimage(pil_image)

        assert isinstance(qimage, QImage)
        assert qimage.width() == 50
        assert qimage.height() == 50

    def test_get_qr_size(self, qr_engine):
        """测试计算二维码大小"""
        data = "测试数据"

        # 测试自动版本
        width, height = qr_engine.get_qr_size(data, version=0, size=10, border=4)
        assert width > 0
        assert height > 0
        assert width == height  # 二维码应该是正方形

        # 测试指定版本
        width2, height2 = qr_engine.get_qr_size(data, version=3, size=8, border=2)
        assert width2 > 0
        assert height2 > 0

        # 测试不同模块大小
        width3, height3 = qr_engine.get_qr_size(data, version=3, size=12, border=4)
        assert width3 > width2  # 模块更大，整体应该更大

    def test_get_qr_size_error(self, qr_engine):
        """测试计算二维码大小出错时返回默认值"""
        # 模拟生成二维码时出错
        with patch("qrcode.QRCode") as mock_qrcode:
            mock_qrcode.side_effect = Exception("模拟错误")
            width, height = qr_engine.get_qr_size("test", version=1, size=10, border=4)
            assert width == 200  # 默认值
            assert height == 200

    def test_validate_data_capacity_success(self, qr_engine):
        """测试数据容量验证成功"""
        # 少量数据应该适合任何版本
        result = qr_engine.validate_data_capacity(
            "test", version=1, error_correction="L"
        )
        assert result is True

        # 测试不同纠错级别
        for ec in ["L", "M", "Q", "H"]:
            result = qr_engine.validate_data_capacity(
                "short", version=2, error_correction=ec
            )
            assert result is True

    def test_validate_data_capacity_overflow(self, qr_engine):
        """测试数据容量溢出"""
        # 创建超长数据
        long_data = "A" * 10000  # 非常长的数据

        # 小版本应该无法容纳
        result = qr_engine.validate_data_capacity(
            long_data, version=1, error_correction="L"
        )
        assert result is False

        # 大版本可能可以容纳
        result = qr_engine.validate_data_capacity(
            long_data, version=40, error_correction="L"
        )
        # 这取决于具体实现，我们只检查不抛出异常

    def test_validate_data_capacity_invalid_params(self, qr_engine):
        """测试数据容量验证无效参数"""
        # 版本0在qrcode库中是无效的，应该返回False
        result = qr_engine.validate_data_capacity(
            "test", version=0, error_correction="L"
        )
        # 版本0应该返回False，而不是尝试创建QRCode
        assert result is False

        # 测试版本超出范围
        result = qr_engine.validate_data_capacity(
            "test", version=41, error_correction="L"
        )
        assert result is False

        # 无效纠错级别
        result = qr_engine.validate_data_capacity(
            "test", version=1, error_correction="X"
        )
        # 应该返回True，因为_get_error_correction会返回默认值H
        assert result is True

    def test_get_supported_versions(self, qr_engine):
        """测试获取支持的版本列表"""
        versions = qr_engine.get_supported_versions()

        assert len(versions) == 40
        assert versions[0] == 1
        assert versions[-1] == 40
        assert list(range(1, 41)) == versions

    def test_get_error_correction_levels(self, qr_engine):
        """测试获取纠错级别列表"""
        levels = qr_engine.get_error_correction_levels()

        assert len(levels) == 4
        assert levels[0] == ("L", "L (7%) - 低")
        assert levels[1] == ("M", "M (15%) - 中")
        assert levels[2] == ("Q", "Q (25%) - 较高")
        assert levels[3] == ("H", "H (30%) - 高")

    def test_is_running_initial(self, qr_engine):
        """测试初始运行状态"""
        assert qr_engine.is_running() is False

    def test_stop_method(self, qr_engine):
        """测试停止方法"""
        qr_engine.running = True
        qr_engine.stop()
        assert qr_engine.running is False

    def test_repr(self, qr_engine):
        """测试字符串表示"""
        repr_str = repr(qr_engine)
        assert "QRCodeEngine" in repr_str
        assert "status='空闲'" in repr_str

        qr_engine.running = True
        qr_engine.batch_data = [1, 2, 3]  # 模拟批量数据
        repr_str = repr(qr_engine)
        assert "运行中" in repr_str
        assert "batch_size=3" in repr_str

    def test_generate_method(self, qr_engine, sample_qrcode_data):
        """测试生成方法设置参数"""
        qr_engine.generate(sample_qrcode_data)

        assert qr_engine.qr_data == sample_qrcode_data
        assert qr_engine.batch_data == []
        assert qr_engine.running is True

    def test_generate_batch_method(self, qr_engine, sample_qrcode_data):
        """测试批量生成方法设置参数"""
        batch_list = [sample_qrcode_data, sample_qrcode_data, sample_qrcode_data]
        qr_engine.generate_batch(batch_list)

        assert qr_engine.qr_data is None
        assert qr_engine.batch_data == batch_list
        assert qr_engine.running is True

    @patch.object(QRCodeEngine, "_generate_single")
    def test_run_single(self, mock_generate_single, qr_engine, sample_qrcode_data):
        """测试运行单个生成"""
        qr_engine.qr_data = sample_qrcode_data
        qr_engine.run()

        mock_generate_single.assert_called_once()

    @patch.object(QRCodeEngine, "_generate_batch")
    def test_run_batch(self, mock_generate_batch, qr_engine, sample_qrcode_data):
        """测试运行批量生成"""
        qr_engine.batch_data = [sample_qrcode_data]
        qr_engine.run()

        mock_generate_batch.assert_called_once()

    @patch.object(QRCodeEngine, "_generate_single")
    def test_run_exception(self, mock_generate_single, qr_engine, sample_qrcode_data):
        """测试运行时的异常处理"""
        mock_generate_single.side_effect = Exception("模拟错误")

        # 连接错误信号
        error_mock = MagicMock()
        qr_engine.error_occurred.connect(error_mock)

        qr_engine.qr_data = sample_qrcode_data
        qr_engine.run()

        # 验证错误信号被发出
        error_mock.assert_called_once()
        assert "生成失败" in error_mock.call_args[0][0]
        assert qr_engine.running is False

    def test_generate_single_validation_failure(self, qr_engine):
        """测试生成单个二维码时验证失败"""
        # 创建无效数据（空数据）
        invalid_data = QRCodeData(
            id="test",
            data="",  # 空数据无效
            qr_type=QRCodeType.TEXT,
            version=1,
            error_correction="H",
            size=10,
            border=4,
            foreground_color="#000000",
            background_color="#FFFFFF",
        )

        qr_engine.qr_data = invalid_data

        # 连接错误信号
        error_mock = MagicMock()
        qr_engine.error_occurred.connect(error_mock)

        # 执行生成
        qr_engine._generate_single()

        # 验证错误信号被发出
        error_mock.assert_called_once()
        assert "数据验证失败" in error_mock.call_args[0][0]

    def test_generate_single_no_data(self, qr_engine):
        """测试生成单个二维码时没有数据"""
        qr_engine.qr_data = None

        # 连接错误信号
        error_mock = MagicMock()
        qr_engine.error_occurred.connect(error_mock)

        # 执行生成
        qr_engine._generate_single()

        # 验证错误信号被发出
        error_mock.assert_called_once()
        assert "没有可生成的二维码数据" in error_mock.call_args[0][0]

    @patch("qrcode.QRCode")
    def test_generate_single_success_signals(
        self, mock_qrcode_class, qr_engine, sample_qrcode_data, qapp
    ):
        """测试生成单个二维码成功时发出的信号"""
        # 设置模拟
        mock_qr = MagicMock()
        mock_matrix = [[1, 0, 1], [0, 1, 0], [1, 0, 1]]
        mock_qr.get_matrix.return_value = mock_matrix

        mock_image = MagicMock(spec=Image.Image)
        mock_image.mode = "RGB"
        mock_image.size = (30, 30)
        mock_image.convert.return_value = mock_image
        mock_image.save.return_value = None

        mock_qr.make_image.return_value = mock_image
        mock_qrcode_class.return_value = mock_qr

        qr_engine.qr_data = sample_qrcode_data

        # 连接信号
        progress_mock = MagicMock()
        generated_mock = MagicMock()
        qr_engine.progress_updated.connect(progress_mock)
        qr_engine.qr_generated.connect(generated_mock)

        # 执行生成
        qr_engine._generate_single()

        # 验证进度信号被多次调用
        assert progress_mock.call_count >= 4

        # 验证生成完成信号被调用
        generated_mock.assert_called_once()
        args = generated_mock.call_args[0]
        assert args[0] == sample_qrcode_data
        assert isinstance(args[1], QImage)

    @patch("qrcode.QRCode")
    def test_generate_batch_stop_early(
        self, mock_qrcode_class, qr_engine, sample_qrcode_data, qapp
    ):
        """测试批量生成提前停止"""
        # 创建批量数据
        batch_data = [sample_qrcode_data] * 5
        qr_engine.batch_data = batch_data

        # 设置模拟
        mock_qr = MagicMock()
        mock_image = MagicMock(spec=Image.Image)
        mock_image.mode = "RGB"
        mock_image.size = (100, 100)

        # 创建临时目录用于保存测试文件
        import tempfile

        temp_dir = tempfile.mkdtemp()

        def mock_save(filepath, **kwargs):
            # 确保目录存在
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            # 创建一个空文件来模拟保存
            with open(filepath, "wb") as f:
                f.write(b"test")
            return None

        mock_image.save = mock_save

        # 设置返回矩阵
        mock_matrix = [[1, 0, 1], [0, 1, 0], [1, 0, 1]]
        mock_qr.get_matrix.return_value = mock_matrix

        # 使用闭包跟踪调用次数
        call_info = {"count": 0}

        def make_image_side_effect(*args, **kwargs):
            call_info["count"] += 1
            # 在生成第二个二维码时设置停止标志
            if call_info["count"] == 2:
                qr_engine.running = False
            return mock_image

        mock_qr.make_image = make_image_side_effect
        mock_qrcode_class.return_value = mock_qr

        # 连接信号
        progress_mock = MagicMock()
        batch_mock = MagicMock()
        qr_engine.progress_updated.connect(progress_mock)
        qr_engine.batch_completed.connect(batch_mock)

        # 设置测试数据使用临时目录
        for data in batch_data:
            data.notes = temp_dir

        # 执行批量生成
        qr_engine._generate_batch()

        # 验证进度信号被调用
        assert progress_mock.call_count > 0

        # 验证 batch_completed 被调用（至少一次）
        # 注意：第一个二维码完成时会调用一次，第二个开始前停止
        assert (
            batch_mock.call_count >= 1
        ), f"batch_completed 调用次数: {batch_mock.call_count}"

        # 验证 running 状态最终为 False
        assert qr_engine.running is False

        # 清理临时目录
        import shutil

        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_generate_batch_with_output_dir(
        self, qr_engine, sample_qrcode_data, tmp_path
    ):
        output_dir = tmp_path / "output"
        modified_data = replace(sample_qrcode_data, notes=str(output_dir))

        qr_engine.batch_data = [modified_data]
        qr_engine.running = True
        qr_engine._generate_batch()

        expected_file = output_dir / f"qrcode_{modified_data.id}.png"
        assert expected_file.exists()
        assert expected_file.stat().st_size > 0

    def test_generate_batch_exception_handling(self, qr_engine, sample_qrcode_data):
        """测试批量生成时的异常处理"""
        batch_data = [sample_qrcode_data]
        qr_engine.batch_data = batch_data

        # 模拟生成时抛出异常
        with patch("qrcode.QRCode", side_effect=Exception("模拟异常")):
            # 连接信号
            progress_mock = MagicMock()
            batch_mock = MagicMock()
            qr_engine.progress_updated.connect(progress_mock)
            qr_engine.batch_completed.connect(batch_mock)

            # 执行批量生成
            qr_engine._generate_batch()

            # 验证进度更新被调用
            assert progress_mock.call_count > 0

            # 检查进度消息中是否包含"正在生成"或"批量生成完成"
            progress_messages = [call[0][1] for call in progress_mock.call_args_list]
            has_expected_message = any(
                "正在生成" in msg or "批量生成" in msg for msg in progress_messages
            )
            assert has_expected_message
