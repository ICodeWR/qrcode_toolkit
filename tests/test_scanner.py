#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
扫描器模块单元测试

模块名称：test_scanner.py
功能描述：测试 QRCodeScanner 和 QRCodeBatchScanner 类的各项功能
"""

import os
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import cv2
import numpy as np
import pytest
from PySide6.QtCore import QCoreApplication, QThread, QTimer
from PySide6.QtGui import QImage

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.scanner import QRCodeBatchScanner, QRCodeScanner


@pytest.fixture(scope="session")
def qapp():
    """创建QApplication实例（会话级）"""
    app = QCoreApplication.instance()
    if app is None:
        app = QCoreApplication(sys.argv)
    yield app


@pytest.fixture
def scanner(qapp):
    """创建QRCodeScanner实例，确保线程正确清理"""
    scanner = QRCodeScanner()
    yield scanner
    # 确保停止扫描并等待线程结束
    scanner.stop_scanning()
    if scanner.isRunning():
        scanner.wait(2000)  # 等待最多2秒
    scanner.deleteLater()
    # 处理事件
    qapp.processEvents()


@pytest.fixture
def batch_scanner(qapp):
    """创建QRCodeBatchScanner实例"""
    batch_scanner = QRCodeBatchScanner()
    yield batch_scanner
    batch_scanner.stop()
    if batch_scanner.scanner.isRunning():
        batch_scanner.scanner.wait(2000)
    batch_scanner.scanner.deleteLater()
    qapp.processEvents()


@pytest.fixture
def temp_image_file():
    """创建临时测试图片文件"""
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        temp_path = f.name

    # 创建一个简单的测试图像
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    cv2.imwrite(temp_path, img)

    yield temp_path

    # 清理
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def temp_folder_with_images():
    """创建包含测试图片的临时文件夹"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # 创建一些虚拟图片文件
        for i, ext in enumerate([".png", ".jpg", ".bmp"]):
            file_path = os.path.join(temp_dir, f"test{i}{ext}")
            img = np.zeros((50, 50, 3), dtype=np.uint8)
            cv2.imwrite(file_path, img)

        # 创建子文件夹
        sub_dir = os.path.join(temp_dir, "subfolder")
        os.makedirs(sub_dir, exist_ok=True)

        # 在子文件夹中创建图片
        sub_file = os.path.join(sub_dir, "sub_test.png")
        img = np.zeros((50, 50, 3), dtype=np.uint8)
        cv2.imwrite(sub_file, img)

        # 创建一个非图片文件
        txt_file = os.path.join(temp_dir, "not_image.txt")
        with open(txt_file, "w") as f:
            f.write("text file")

        yield temp_dir


class TestQRCodeScannerInit:
    """测试QRCodeScanner初始化"""

    def test_initialization(self, scanner):
        """测试初始化"""
        assert scanner.image_paths == []
        assert scanner.use_camera is False
        assert scanner.camera_index == 0
        assert scanner.scanning is False
        assert scanner.scan_timeout == 30
        assert scanner.min_confidence == 0.0
        assert scanner.camera_resolution == (640, 480)
        assert isinstance(scanner, QThread)

    def test_set_min_confidence(self, scanner):
        """测试设置最小置信度"""
        scanner.set_min_confidence(0.5)
        assert scanner.min_confidence == 0.5

        scanner.set_min_confidence(1.5)
        assert scanner.min_confidence == 1.0

        scanner.set_min_confidence(-0.5)
        assert scanner.min_confidence == 0.0

    def test_get_scanner_info(self, scanner):
        """测试获取扫描器信息"""
        scanner.image_paths = ["test.png", "test2.png"]
        info = scanner.get_scanner_info()

        assert info["use_camera"] is False
        assert info["scanning"] is False
        assert info["camera_index"] == 0
        assert info["scan_timeout"] == 30
        assert info["min_confidence"] == 0.0
        assert info["pending_files"] == 2

    def test_clear_pending_files(self, scanner):
        """测试清除待扫描文件列表"""
        scanner.image_paths = ["test.png", "test2.png"]
        scanner.clear_pending_files()
        assert scanner.image_paths == []

    def test_repr(self, scanner):
        """测试字符串表示"""
        scanner.scanning = True
        scanner.use_camera = True
        repr_str = repr(scanner)
        assert "QRCodeScanner" in repr_str
        assert "status='扫描中'" in repr_str
        assert "mode='摄像头'" in repr_str


class TestQRCodeScannerScanFiles:
    """测试文件扫描功能"""

    @patch("core.scanner.cv2.imread")
    @patch("core.scanner.decode_qr")
    def test_scan_image_success(
        self, mock_decode, mock_imread, scanner, temp_image_file
    ):
        """测试成功扫描图像"""
        # 模拟图像
        mock_image = np.zeros((100, 100, 3), dtype=np.uint8)
        mock_imread.return_value = mock_image

        # 模拟解码结果
        mock_decoded = MagicMock()
        mock_decoded.data = b"test qr data"
        mock_decoded.type = "QRCODE"
        mock_decoded.rect.left = 10
        mock_decoded.rect.top = 10
        mock_decoded.rect.width = 80
        mock_decoded.rect.height = 80

        # 创建模拟的多边形点
        class Point:
            def __init__(self, x, y):
                self.x = x
                self.y = y

        mock_decoded.polygon = [
            Point(10, 10),
            Point(90, 10),
            Point(90, 90),
            Point(10, 90),
        ]
        mock_decode.return_value = [mock_decoded]

        results = scanner._scan_image(mock_image, temp_image_file)

        assert len(results) == 1
        assert results[0]["data"] == "test qr data"
        assert results[0]["type"] == "QRCODE"
        assert results[0]["source"] == temp_image_file
        assert "confidence" in results[0]
        assert "timestamp" in results[0]
        assert "rect" in results[0]
        assert "polygon" in results[0]

    @patch("core.scanner.cv2.imread")
    @patch("core.scanner.decode_qr")
    def test_scan_image_no_qr(self, mock_decode, mock_imread, scanner):
        """测试扫描无二维码的图像"""
        mock_image = np.zeros((100, 100, 3), dtype=np.uint8)
        mock_imread.return_value = mock_image
        mock_decode.return_value = []

        results = scanner._scan_image(mock_image, "test.png")

        assert len(results) == 0

    @patch("core.scanner.os.path.exists")
    @patch("core.scanner.cv2.imread")
    def test_scan_image_invalid_image(self, mock_imread, mock_exists, scanner):
        """测试扫描无效图像 - 添加os.path.exists模拟"""
        mock_exists.return_value = True  # 文件存在
        mock_imread.return_value = None  # 但无法读取

        # 设置文件列表
        scanner.image_paths = ["invalid.png"]
        scanner.scanning = True

        with patch.object(scanner, "error_occurred") as mock_error:
            scanner._scan_files()
            # 应该触发"无法读取图像文件"错误
            mock_error.emit.assert_called_once()
            assert "无法读取图像文件" in mock_error.emit.call_args[0][0]

    @patch("core.scanner.os.path.exists")
    @patch("core.scanner.cv2.imread")
    @patch("core.scanner.decode_qr")
    def test_scan_files_with_results(
        self, mock_decode, mock_imread, mock_exists, scanner
    ):
        """测试扫描多个文件并返回结果"""
        # 设置
        mock_exists.return_value = True
        mock_image = np.zeros((100, 100, 3), dtype=np.uint8)
        mock_imread.return_value = mock_image

        mock_decoded = MagicMock()
        mock_decoded.data = b"test qr data"
        mock_decoded.type = "QRCODE"
        mock_decoded.rect.left = 10
        mock_decoded.rect.top = 10
        mock_decoded.rect.width = 80
        mock_decoded.rect.height = 80
        mock_decoded.polygon = []
        mock_decode.return_value = [mock_decoded]

        scanner.image_paths = ["test1.png", "test2.png"]
        scanner.scanning = True

        # 模拟信号
        scanner.qr_scanned = MagicMock()
        scanner.progress_updated = MagicMock()

        # 执行
        scanner._scan_files()

        # 验证
        scanner.qr_scanned.emit.assert_called_once()
        assert scanner.progress_updated.emit.call_count >= 2

    @patch("core.scanner.os.path.exists")
    def test_scan_files_file_not_exists(self, mock_exists, scanner):
        """测试扫描不存在的文件"""
        mock_exists.return_value = False
        scanner.image_paths = ["nonexistent.png"]
        scanner.scanning = True

        with patch.object(scanner, "error_occurred") as mock_error:
            scanner._scan_files()
            mock_error.emit.assert_called_once()
            assert "文件不存在" in mock_error.emit.call_args[0][0]

    def test_scan_files_no_files(self, scanner):
        """测试没有要扫描的文件"""
        scanner.image_paths = []
        scanner.scanning = True

        with patch.object(scanner, "error_occurred") as mock_error:
            scanner._scan_files()
            mock_error.emit.assert_called_once()
            assert "没有要扫描的文件" in mock_error.emit.call_args[0][0]


class TestQRCodeScannerScanCamera:
    """测试摄像头扫描功能"""

    @patch("core.scanner.cv2.VideoCapture")
    def test_scan_camera_success(self, mock_video_capture, scanner):
        """测试成功开启摄像头扫描"""
        # 模拟摄像头
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.read.return_value = (True, np.zeros((480, 640, 3), dtype=np.uint8))
        mock_cap.get.side_effect = lambda x: (
            640
            if x == cv2.CAP_PROP_FRAME_WIDTH
            else 480 if x == cv2.CAP_PROP_FRAME_HEIGHT else 30
        )
        mock_video_capture.return_value = mock_cap

        # 直接设置 scanner 状态
        scanner.use_camera = True
        scanner.camera_index = 0
        scanner.scan_timeout = 1
        scanner.camera_resolution = (640, 480)
        scanner.scanning = True

        # 模拟信号
        scanner.camera_frame = MagicMock()
        scanner.progress_updated = MagicMock()
        scanner.qr_scanned = MagicMock()

        # 直接测试 _scan_with_camera，但我们需要控制循环
        with patch.object(scanner, "_scan_with_camera") as mock_scan:
            # 不实际执行，只验证参数设置
            scanner.scan_camera(0, timeout=1)
            scanner.stop_scanning()
            assert scanner.use_camera is True
            assert scanner.camera_index == 0
            assert scanner.scan_timeout == 1
            assert scanner.scanning is False

    @patch("core.scanner.cv2.VideoCapture")
    def test_scan_camera_not_opened(self, mock_video_capture, scanner):
        """测试摄像头无法打开"""
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = False
        mock_video_capture.return_value = mock_cap

        with patch.object(scanner, "error_occurred") as mock_error:
            scanner._scan_with_camera()
            mock_error.emit.assert_called_once()
            assert "无法打开摄像头" in mock_error.emit.call_args[0][0]

    @patch("core.scanner.cv2.VideoCapture")
    def test_scan_camera_read_failure(self, mock_video_capture, scanner):
        """测试摄像头读取失败"""
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.read.return_value = (False, None)
        mock_cap.get.return_value = 640
        mock_video_capture.return_value = mock_cap

        # 设置扫描状态
        scanner.scanning = True
        scanner.scan_timeout = 0.1

        # 不应该抛出异常
        scanner._scan_with_camera()

    def test_stop_scanning(self, scanner):
        """测试停止扫描"""
        scanner.scanning = True
        scanner.stop_scanning()
        assert scanner.scanning is False

    def test_draw_qr_bounding_box(self, scanner):
        """测试绘制二维码边框"""
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        class Point:
            def __init__(self, x, y):
                self.x = x
                self.y = y

        mock_obj = MagicMock()
        mock_obj.polygon = [
            Point(100, 100),
            Point(200, 100),
            Point(200, 200),
            Point(100, 200),
        ]

        # 应该不会抛出异常
        scanner._draw_qr_bounding_box(frame, mock_obj)
        assert frame is not None


class TestQRCodeScannerUtility:
    """测试工具方法"""

    def test_calculate_confidence(self, scanner):
        """测试计算置信度"""
        # 模拟完整的二维码
        mock_obj = MagicMock()
        mock_obj.rect.width = 100
        mock_obj.rect.height = 100
        mock_obj.polygon = [1, 2, 3, 4]

        confidence = scanner._calculate_confidence(mock_obj)
        assert 0 <= confidence <= 1.0

        # 模拟不完整的二维码
        mock_obj.rect.width = 10
        mock_obj.rect.height = 10
        mock_obj.polygon = [1, 2]

        confidence = scanner._calculate_confidence(mock_obj)
        assert confidence < 0.5

    def test_detect_orientation_normal(self, scanner):
        """检测方向 - 正常"""

        class Point:
            def __init__(self, x, y):
                self.x = x
                self.y = y

        # 模拟一个接近正方形的多边形
        polygon = [Point(10, 10), Point(90, 10), Point(90, 90), Point(10, 90)]

        orientation = scanner._detect_orientation(polygon)
        assert orientation in ["正常", "未知"]

    def test_detect_orientation_insufficient_points(self, scanner):
        """检测方向 - 点数不足"""

        class Point:
            def __init__(self, x, y):
                self.x = x
                self.y = y

        polygon = [Point(10, 10), Point(90, 10)]

        orientation = scanner._detect_orientation(polygon)
        assert orientation == "未知"

    @patch("core.scanner.cv2.cvtColor")
    def test_cv2_to_qimage(self, mock_cvtColor, scanner):
        """测试OpenCV图像转QImage"""
        # 创建测试图像
        test_image = np.zeros((100, 100, 3), dtype=np.uint8)

        # 模拟cvtColor返回原始图像
        mock_cvtColor.return_value = test_image

        qimage = scanner._cv2_to_qimage(test_image)

        assert isinstance(qimage, QImage)
        assert not qimage.isNull()
        assert qimage.width() == 100
        assert qimage.height() == 100

    @patch("core.scanner.cv2.VideoCapture")
    def test_get_available_cameras_windows(self, mock_video_capture, scanner):
        """测试Windows平台获取可用摄像头列表"""
        with patch("platform.system", return_value="Windows"):
            # 模拟第一个摄像头可用
            mock_cap1 = MagicMock()
            mock_cap1.isOpened.return_value = True
            mock_cap1.read.return_value = (
                True,
                np.zeros((480, 640, 3), dtype=np.uint8),
            )
            mock_cap1.get.side_effect = lambda x: (
                640 if x == cv2.CAP_PROP_FRAME_WIDTH else 480
            )

            # 模拟第二个摄像头不可用
            mock_cap2 = MagicMock()
            mock_cap2.isOpened.return_value = False

            mock_video_capture.side_effect = [
                mock_cap1,
                MagicMock(),
                mock_cap2,
                MagicMock(),
                MagicMock(),
            ]

            cameras = scanner.get_available_cameras()

            assert isinstance(cameras, list)

    @patch("core.scanner.cv2.VideoCapture")
    def test_get_available_cameras_linux(self, mock_video_capture, scanner):
        """测试Linux/Mac平台获取可用摄像头列表"""
        with patch("platform.system", return_value="Linux"):
            mock_cap = MagicMock()
            mock_cap.isOpened.return_value = True
            mock_cap.read.return_value = (True, np.zeros((480, 640, 3), dtype=np.uint8))

            mock_video_capture.return_value = mock_cap

            cameras = scanner.get_available_cameras()

            assert isinstance(cameras, list)

    def test_is_scanning(self, scanner):
        """测试检查扫描状态"""
        scanner.scanning = True
        assert scanner.is_scanning() is True

        scanner.scanning = False
        assert scanner.is_scanning() is False


class TestQRCodeBatchScanner:
    """测试批量扫描器"""

    def test_initialization(self, batch_scanner):
        """测试初始化"""
        assert batch_scanner.results == []
        assert batch_scanner.callbacks == {
            "on_progress": None,
            "on_result": None,
            "on_error": None,
            "on_finish": None,
        }
        assert hasattr(batch_scanner, "scanner")

    def test_scan_folder_recursive(self, batch_scanner, temp_folder_with_images):
        """测试递归扫描文件夹"""
        batch_scanner.scanner = MagicMock()

        batch_scanner.scan_folder(temp_folder_with_images, recursive=True)

        batch_scanner.scanner.scan_files.assert_called_once()
        args, _ = batch_scanner.scanner.scan_files.call_args
        file_list = args[0]
        assert len(file_list) >= 3
        assert any("subfolder" in f for f in file_list)

    def test_scan_folder_non_recursive(self, batch_scanner, temp_folder_with_images):
        """测试非递归扫描文件夹"""
        batch_scanner.scanner = MagicMock()

        batch_scanner.scan_folder(temp_folder_with_images, recursive=False)

        batch_scanner.scanner.scan_files.assert_called_once()
        args, _ = batch_scanner.scanner.scan_files.call_args
        file_list = args[0]
        assert not any("subfolder" in f for f in file_list)

    def test_scan_folder_no_images(self, batch_scanner):
        """测试扫描无图片的文件夹"""
        batch_scanner.scanner = MagicMock()

        with tempfile.TemporaryDirectory() as empty_dir:
            mock_callback = MagicMock()
            batch_scanner.callbacks["on_error"] = mock_callback

            batch_scanner.scan_folder(empty_dir)

            batch_scanner.scanner.scan_files.assert_not_called()
            mock_callback.assert_called_once_with("未找到图片文件")

    def test_scan_folder_custom_extensions(
        self, batch_scanner, temp_folder_with_images
    ):
        """测试自定义扩展名"""
        batch_scanner.scanner = MagicMock()

        batch_scanner.scan_folder(
            temp_folder_with_images, extensions=[".png"], recursive=True
        )

        batch_scanner.scanner.scan_files.assert_called_once()
        args, _ = batch_scanner.scanner.scan_files.call_args
        file_list = args[0]
        assert all(f.endswith(".png") for f in file_list)

    def test_set_callback(self, batch_scanner):
        """测试设置回调函数"""

        def test_callback():
            pass

        batch_scanner.set_callback("on_progress", test_callback)
        assert batch_scanner.callbacks["on_progress"] == test_callback

        batch_scanner.set_callback("invalid", test_callback)
        assert "invalid" not in batch_scanner.callbacks

    def test_stop(self, batch_scanner):
        """测试停止扫描"""
        batch_scanner.scanner = MagicMock()
        batch_scanner.stop()
        batch_scanner.scanner.stop_scanning.assert_called_once()

    def test_get_results(self, batch_scanner):
        """测试获取扫描结果"""
        batch_scanner.results = [{"data": "test1"}, {"data": "test2"}]
        results = batch_scanner.get_results()
        assert len(results) == 2
        assert results[0]["data"] == "test1"
        assert results is not batch_scanner.results  # 应该是副本

    def test_clear_results(self, batch_scanner):
        """测试清除扫描结果"""
        batch_scanner.results = [{"data": "test1"}, {"data": "test2"}]
        batch_scanner.clear_results()
        assert batch_scanner.results == []

    def test_handle_results(self, batch_scanner):
        """测试处理扫描结果"""
        callback = MagicMock()
        batch_scanner.callbacks["on_result"] = callback
        results = [{"data": "test"}]

        batch_scanner._handle_results(results)

        assert batch_scanner.results == results
        callback.assert_called_once_with(results)

    def test_handle_progress(self, batch_scanner):
        """测试处理进度更新"""
        callback = MagicMock()
        batch_scanner.callbacks["on_progress"] = callback

        batch_scanner._handle_progress(50, "正在扫描...")

        callback.assert_called_once_with(50, "正在扫描...")

    def test_handle_error(self, batch_scanner):
        """测试处理错误"""
        callback = MagicMock()
        batch_scanner.callbacks["on_error"] = callback

        batch_scanner._handle_error("测试错误")

        callback.assert_called_once_with("测试错误")

    def test_handle_finish(self, batch_scanner):
        """测试处理完成"""
        callback = MagicMock()
        batch_scanner.callbacks["on_finish"] = callback
        batch_scanner.results = [{"data": "test"}]

        batch_scanner._handle_finish()

        callback.assert_called_once_with(batch_scanner.results)

    def test_repr(self, batch_scanner):
        """测试字符串表示"""
        batch_scanner.results = [{"data": "test"}]
        batch_scanner.scanner = MagicMock()
        batch_scanner.scanner.is_scanning.return_value = True

        repr_str = repr(batch_scanner)
        assert "QRCodeBatchScanner" in repr_str
        assert "results=1" in repr_str
        assert "scanning=True" in repr_str


class TestQRCodeScannerThreadSafety:
    """测试线程安全"""

    def test_scan_files_thread_real(self, scanner, temp_image_file, qapp):
        """测试真实的文件扫描线程"""
        # 设置真实文件
        scanner.image_paths = [temp_image_file]

        # 创建事件循环处理信号
        loop_created = False
        try:
            from PySide6.QtCore import QEventLoop

            loop = QEventLoop()
            loop_created = True
        except ImportError:
            loop_created = False

        # 连接信号
        mock_finished = MagicMock()
        scanner.scan_finished.connect(mock_finished)

        # 连接完成信号到事件循环退出
        if loop_created:
            scanner.scan_finished.connect(loop.quit)

        mock_scanned = MagicMock()
        scanner.qr_scanned.connect(mock_scanned)

        # 开始扫描
        scanner.scan_files([temp_image_file])

        # 等待线程完成
        if loop_created:
            # 使用事件循环等待信号，超时5秒
            QTimer.singleShot(5000, loop.quit)
            loop.exec()

        # 确保线程结束
        finished = scanner.wait(3000)
        assert finished is True

        # 处理事件
        qapp.processEvents()
        time.sleep(0.2)
        qapp.processEvents()

        # 验证信号被调用（真实扫描可能没有二维码，但scan_finished应该被调用）
        mock_finished.emit.assert_called_once()

        # 断开连接
        scanner.scan_finished.disconnect(mock_finished)
        scanner.qr_scanned.disconnect(mock_scanned)

    @patch("core.scanner.cv2.imread")
    @patch("core.scanner.decode_qr")
    @patch("core.scanner.os.path.exists")
    def test_scan_files_thread_mocked(
        self, mock_exists, mock_decode, mock_imread, scanner, temp_image_file, qapp
    ):
        """测试模拟的文件扫描线程"""
        # 设置模拟
        mock_exists.return_value = True
        mock_image = np.zeros((100, 100, 3), dtype=np.uint8)
        mock_imread.return_value = mock_image

        # 模拟解码成功
        mock_decoded = MagicMock()
        mock_decoded.data = b"test qr data"
        mock_decoded.type = "QRCODE"
        mock_decoded.rect.left = 10
        mock_decoded.rect.top = 10
        mock_decoded.rect.width = 80
        mock_decoded.rect.height = 80
        mock_decoded.polygon = []
        mock_decode.return_value = [mock_decoded]

        # 创建事件循环
        try:
            from PySide6.QtCore import QEventLoop

            loop = QEventLoop()
            use_loop = True
        except ImportError:
            use_loop = False

        # 连接信号
        mock_finished = MagicMock()
        scanner.scan_finished.connect(mock_finished)

        if use_loop:
            scanner.scan_finished.connect(loop.quit)

        mock_scanned = MagicMock()
        scanner.qr_scanned.connect(mock_scanned)

        # 设置扫描状态
        scanner.image_paths = [temp_image_file]
        scanner.scanning = True

        # 直接启动线程（不通过scan_files，避免重复设置）
        scanner.use_camera = False
        scanner.start()

        # 等待线程完成
        if use_loop:
            QTimer.singleShot(5000, loop.quit)
            loop.exec()

        finished = scanner.wait(3000)
        assert finished is True

        # 处理事件
        qapp.processEvents()
        time.sleep(0.2)
        qapp.processEvents()

        # 验证信号被调用
        mock_finished.emit.assert_called_once()
        mock_scanned.emit.assert_called_once()

        # 断开连接
        scanner.scan_finished.disconnect(mock_finished)
        scanner.qr_scanned.disconnect(mock_scanned)

    def test_stop_during_scan(self, scanner):
        """测试扫描中停止"""
        scanner.image_paths = ["test1.png", "test2.png"]

        # 模拟长时间运行的扫描
        with patch.object(scanner, "_scan_files") as mock_scan:

            def slow_scan():
                time.sleep(0.5)

            mock_scan.side_effect = slow_scan

            # 启动线程
            scanner.scanning = True
            scanner.start()

            # 立即停止
            scanner.stop_scanning()

            # 等待线程结束
            scanner.wait(1000)

            assert scanner.scanning is False
            assert scanner.isRunning() is False
