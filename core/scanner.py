#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
二维码扫描器模块 - QR Toolkit的二维码扫描功能

模块名称：scanner.py
功能描述：提供二维码扫描功能，支持图片文件扫描和摄像头实时扫描
作者：码上工坊
联系：微信公众号（码上工坊）
版权声明：Copyright (c) 2026 码上工坊
开源协议：MIT License
免责声明：本软件按"原样"提供，不作任何明示或暗示的担保
修改记录：
版本 0.9.0 2026-01-10 - 码上工坊 - 初始版本创建
"""

import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np
from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QImage
from pyzbar.pyzbar import decode as decode_qr  # type: ignore


class QRCodeScanner(QThread):
    """二维码扫描器（支持多线程）"""

    # 信号定义
    qr_scanned = Signal(list)  # 扫描结果列表
    progress_updated = Signal(int, str)  # 进度值, 状态信息
    error_occurred = Signal(str)  # 错误信息
    camera_frame = Signal(QImage)  # 摄像头帧信号（实时预览）
    scan_finished = Signal()  # 扫描完成信号

    def __init__(self, parent=None) -> None:
        """
        初始化二维码扫描器

        Args:
            parent: 父对象
        """
        super().__init__(parent)
        self.image_paths: List[str] = []
        self.use_camera: bool = False
        self.camera_index: int = 0
        self.scanning: bool = False
        self.scan_timeout: int = 30  # 默认30秒超时
        self.min_confidence: float = 0.0  # 最小置信度（0.0-1.0）
        self.camera_resolution: Tuple[int, int] = (640, 480)  # 摄像头分辨率

    def scan_files(self, file_paths: List[str]) -> None:
        """
        扫描文件中的二维码

        Args:
            file_paths: 图片文件路径列表
        """
        self.image_paths = file_paths
        self.use_camera = False
        self.scanning = True
        self.start()

    def scan_camera(
        self,
        camera_index: int = 0,
        timeout: int = 30,
        resolution: Tuple[int, int] = (640, 480),
    ) -> None:
        """
        使用摄像头扫描二维码

        Args:
            camera_index: 摄像头索引
            timeout: 扫描超时时间（秒）
            resolution: 摄像头分辨率
        """
        self.use_camera = True
        self.camera_index = camera_index
        self.scan_timeout = timeout
        self.camera_resolution = resolution
        self.scanning = True
        self.start()

    def stop_scanning(self) -> None:
        """停止扫描"""
        self.scanning = False

    def run(self) -> None:
        """线程运行方法"""
        try:
            if self.use_camera:
                self._scan_with_camera()
            else:
                self._scan_files()
        except Exception as e:
            self.error_occurred.emit(f"扫描失败: {str(e)}")
        finally:
            self.scan_finished.emit()

    def _scan_files(self) -> None:
        """扫描文件中的二维码"""
        results = []
        total = len(self.image_paths)

        if total == 0:
            self.error_occurred.emit("没有要扫描的文件")
            return

        for i, image_path in enumerate(self.image_paths):
            if not self.scanning:
                break

            self.progress_updated.emit(
                int(i / total * 100), f"扫描: {os.path.basename(image_path)}"
            )

            try:
                # 检查文件是否存在
                if not os.path.exists(image_path):
                    self.error_occurred.emit(f"文件不存在: {image_path}")
                    continue

                # 使用OpenCV读取图像
                image = cv2.imread(image_path)
                if image is None:
                    self.error_occurred.emit(f"无法读取图像文件: {image_path}")
                    continue

                # 扫描二维码
                file_results = self._scan_image(image, image_path)
                results.extend(file_results)

            except Exception as e:
                error_msg = f"扫描 {image_path} 失败: {str(e)}"
                self.error_occurred.emit(error_msg)

        self.progress_updated.emit(100, "扫描完成")
        self.qr_scanned.emit(results)

    def _scan_with_camera(self) -> None:
        """
        使用摄像头扫描二维码
        """
        import platform

        cap = None
        results = []
        frame_count = 0
        scan_interval = 5  # 每5帧扫描一次二维码（提高性能）

        try:
            # 发送开始扫描信号
            self.progress_updated.emit(0, "正在初始化摄像头...")

            # 摄像头初始化 - 多重尝试
            success = False
            backend_used = "未知"

            # Windows平台
            if platform.system() == "Windows":
                # 方法1: DirectShow
                try:
                    print(f"尝试使用DirectShow打开摄像头 {self.camera_index}...")
                    cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
                    if cap.isOpened():
                        # 测试读取
                        ret, test = cap.read()
                        if ret and test is not None:
                            success = True
                            backend_used = "DirectShow"
                            print("DirectShow打开成功")
                except Exception as e:
                    print(f"DirectShow失败: {e}")

                # 方法2: MSMF
                if not success:
                    try:
                        print("尝试使用MSMF后端...")
                        cap = cv2.VideoCapture(self.camera_index, cv2.CAP_MSMF)
                        if cap.isOpened():
                            ret, test = cap.read()
                            if ret and test is not None:
                                success = True
                                backend_used = "MSMF"
                                print("MSMF打开成功")
                    except Exception as e:
                        print(f"MSMF失败: {e}")

                # 方法3: 默认后端
                if not success:
                    try:
                        print("尝试使用默认后端...")
                        cap = cv2.VideoCapture(self.camera_index)
                        if cap.isOpened():
                            ret, test = cap.read()
                            if ret and test is not None:
                                success = True
                                backend_used = "Default"
                                print("默认后端打开成功")
                    except Exception as e:
                        print(f"默认后端失败: {e}")
            else:
                # Linux/Mac
                try:
                    cap = cv2.VideoCapture(self.camera_index)
                    if cap.isOpened():
                        ret, test = cap.read()
                        if ret and test is not None:
                            success = True
                            backend_used = "Default"
                except Exception as e:
                    print(f"摄像头打开失败: {e}")

            # 最终检查
            if not success or not cap or not cap.isOpened():
                self.error_occurred.emit(
                    f"无法打开摄像头 {self.camera_index}，请检查摄像头连接"
                )
                return

            print(f"摄像头打开成功，使用后端: {backend_used}")
            # 设置摄像头参数
            # 设置目标分辨率
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.camera_resolution[0])
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.camera_resolution[1])
            cap.set(cv2.CAP_PROP_FPS, 30)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # 最小缓冲，降低延迟

            # 获取实际分辨率
            actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            actual_fps = cap.get(cv2.CAP_PROP_FPS)

            # 如果获取的分辨率为0，使用默认值
            if actual_width <= 0 or actual_height <= 0:
                actual_width, actual_height = self.camera_resolution

            print(f"摄像头参数: {actual_width}x{actual_height} @ {actual_fps:.1f}fps")
            self.progress_updated.emit(
                10, f"摄像头已就绪 ({actual_width}x{actual_height})"
            )

            # 预热摄像头，丢弃前几帧以稳定图像质量
            for i in range(5):
                cap.read()
                time.sleep(0.01)

            # 发送第一帧预览
            ret, first_frame = cap.read()
            if ret and first_frame is not None:
                try:
                    q_img = self._cv2_to_qimage(first_frame)
                    self.camera_frame.emit(q_img)
                except Exception as e:
                    print(f"发送预览帧失败: {e}")

            # 主循环
            start_time = time.time()
            last_frame_time = time.time()
            frame_interval = 1.0 / 20  # 20 FPS
            frame_count = 0

            self.progress_updated.emit(15, "开始扫描二维码...")

            while self.scanning:
                current_time = time.time()

                # 检查超时
                if (current_time - start_time) > self.scan_timeout:
                    self.progress_updated.emit(100, "扫描超时")
                    break

                # 帧率控制
                if (current_time - last_frame_time) < frame_interval:
                    time.sleep(0.001)
                    continue

                last_frame_time = current_time
                frame_count += 1

                # 读取帧
                ret, frame = cap.read()
                if not ret or frame is None or frame.size == 0:
                    continue

                # 实时预览 - 每帧都显示
                try:
                    q_img = self._cv2_to_qimage(frame)
                    self.camera_frame.emit(q_img)
                except Exception as e:
                    pass

                # 二维码扫描 - 降低频率
                if frame_count % scan_interval == 0:
                    try:
                        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                        # 如果分辨率太大，缩小图像以提高扫描速度
                        if actual_width > 800:
                            scale = 800 / actual_width
                            new_width = int(actual_width * scale)
                            new_height = int(actual_height * scale)
                            gray = cv2.resize(gray, (new_width, new_height))

                        # 解码二维码
                        decoded_objects = decode_qr(gray)

                        for obj in decoded_objects:
                            try:
                                data = obj.data.decode("utf-8", errors="ignore")

                                # 计算置信度
                                confidence = self._calculate_confidence(obj)

                                if confidence >= self.min_confidence:
                                    result = {
                                        "source": f"摄像头 {self.camera_index}",
                                        "data": data,
                                        "type": obj.type,
                                        "confidence": confidence,
                                        "timestamp": datetime.now().isoformat(),
                                        "rect": {
                                            "left": obj.rect.left,
                                            "top": obj.rect.top,
                                            "width": obj.rect.width,
                                            "height": obj.rect.height,
                                        },
                                        "polygon": [
                                            (point.x, point.y) for point in obj.polygon
                                        ],
                                    }
                                    results.append(result)

                                    # 找到二维码，在预览图上绘制边框
                                    self._draw_qr_bounding_box(frame, obj)

                                    # 发送带标记的预览帧
                                    marked_q_img = self._cv2_to_qimage(frame)
                                    self.camera_frame.emit(marked_q_img)

                                    # 发送结果并停止扫描
                                    self.qr_scanned.emit(results)
                                    self.scanning = False
                                    break
                            except Exception as e:
                                print(f"处理解码对象失败: {e}")
                                continue

                    except Exception as e:
                        print(f"扫描二维码失败: {e}")

                # 更新进度
                elapsed = current_time - start_time
                progress = min(int((elapsed / self.scan_timeout) * 100), 99)

                if frame_count % 20 == 0:
                    self.progress_updated.emit(
                        progress, f"扫描中... {int(elapsed)}/{self.scan_timeout}秒"
                    )

            if not results:
                self.qr_scanned.emit([])

        except Exception as e:
            self.error_occurred.emit(f"摄像头扫描失败: {str(e)}")
        finally:
            if cap is not None:
                cap.release()
            print("摄像头已释放")

    def _draw_qr_bounding_box(self, frame, decoded_obj) -> None:
        """
        在摄像头画面上绘制二维码边框

        Args:
            frame: OpenCV图像帧
            decoded_obj: pyzbar解码对象
        """
        try:
            # 获取多边形点
            if len(decoded_obj.polygon) > 0:
                points = [(point.x, point.y) for point in decoded_obj.polygon]

                # 绘制多边形边框（绿色）
                for i in range(len(points)):
                    pt1 = (points[i][0], points[i][1])
                    pt2 = (
                        points[(i + 1) % len(points)][0],
                        points[(i + 1) % len(points)][1],
                    )
                    cv2.line(frame, pt1, pt2, (0, 255, 0), 2)

                # 绘制中心点（红色）
                center_x = int(sum(p[0] for p in points) / len(points))
                center_y = int(sum(p[1] for p in points) / len(points))
                cv2.circle(frame, (center_x, center_y), 5, (0, 0, 255), -1)

                # 添加文字
                cv2.putText(
                    frame,
                    "QR Code",
                    (points[0][0], points[0][1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2,
                )
        except Exception as e:
            print(f"绘制边框失败: {e}")

    def _scan_image(self, image: np.ndarray, source: str = "") -> List[Dict]:
        """
        扫描图像中的二维码

        Args:
            image: OpenCV图像（BGR格式）
            source: 图像来源描述

        Returns:
            List[Dict]: 扫描结果列表
        """
        results = []

        try:
            # 转换为灰度图
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # 可选：图像增强
            if self.min_confidence > 0.5:
                # 应用直方图均衡化提高对比度
                gray = cv2.equalizeHist(gray)
                # 应用高斯模糊降噪
                gray = cv2.GaussianBlur(gray, (3, 3), 0)

            # 使用pyzbar解码
            decoded_objects = decode_qr(gray)

            for obj in decoded_objects:
                try:
                    data = obj.data.decode("utf-8", errors="ignore")

                    # 计算置信度（基于边界框质量）
                    confidence = self._calculate_confidence(obj)

                    if confidence >= self.min_confidence:
                        result = {
                            "source": source,
                            "data": data,
                            "type": obj.type,
                            "confidence": confidence,
                            "timestamp": datetime.now().isoformat(),
                            "rect": {
                                "left": obj.rect.left,
                                "top": obj.rect.top,
                                "width": obj.rect.width,
                                "height": obj.rect.height,
                            },
                            "polygon": [(point.x, point.y) for point in obj.polygon],
                            "orientation": self._detect_orientation(obj.polygon),
                        }
                        results.append(result)

                except Exception as e:
                    print(f"处理解码对象失败: {e}")
                    continue

        except Exception as e:
            print(f"扫描图像失败: {e}")

        return results

    def _calculate_confidence(self, decoded_obj) -> float:
        """
        计算解码结果的置信度

        Args:
            decoded_obj: pyzbar解码对象

        Returns:
            float: 置信度（0.0-1.0）
        """
        confidence = 1.0

        # 基于边界框完整性
        if hasattr(decoded_obj, "rect"):
            rect = decoded_obj.rect
            if rect.width > 0 and rect.height > 0:
                # 边界框越大，置信度越高
                size_factor = min(rect.width * rect.height / 10000, 1.0)
                confidence *= size_factor

        # 基于多边形点数量
        if hasattr(decoded_obj, "polygon"):
            polygon = decoded_obj.polygon
            if len(polygon) >= 4:
                # 完整的二维码应该有4个点
                point_factor = min(len(polygon) / 4, 1.0)
                confidence *= point_factor

        return round(confidence, 2)

    def _detect_orientation(self, polygon) -> str:
        """
        检测二维码方向

        Args:
            polygon: 二维码多边形点列表

        Returns:
            str: 方向描述
        """
        if len(polygon) < 3:
            return "未知"

        try:
            # 计算多边形的中心点
            points = [(p.x, p.y) for p in polygon]
            center_x = sum(p[0] for p in points) / len(points)
            center_y = sum(p[1] for p in points) / len(points)

            # 计算每个点相对于中心的角度
            angles = []
            for x, y in points:
                dx = x - center_x
                dy = y - center_y
                angle = np.degrees(np.arctan2(dy, dx))
                angles.append(angle)

            # 归一化角度
            angles = [(a + 360) % 360 for a in angles]
            angles.sort()

            # 检测角度模式
            if len(angles) >= 4:
                # 检查是否为近似90度间隔
                diffs = []
                for i in range(len(angles) - 1):
                    diff = angles[i + 1] - angles[i]
                    diffs.append(diff)

                avg_diff = sum(diffs) / len(diffs)
                if 85 < avg_diff < 95:
                    return "正常"
                elif 175 < avg_diff < 185:
                    return "旋转180°"

            return "未知"

        except Exception:
            return "未知"

    def _cv2_to_qimage(self, cv2_img: np.ndarray) -> QImage:
        """
        将OpenCV图像转换为QImage

        Args:
            cv2_img: OpenCV图像（BGR格式）

        Returns:
            QImage: Qt图像对象
        """
        try:
            height, width, channel = cv2_img.shape
            bytes_per_line = 3 * width

            # 转换BGR到RGB
            rgb_image = cv2.cvtColor(cv2_img, cv2.COLOR_BGR2RGB)

            # 创建QImage
            qimage = QImage(
                rgb_image.data,
                width,
                height,
                bytes_per_line,
                QImage.Format.Format_RGB888,
            )

            # 返回深拷贝，确保数据安全
            return qimage.copy()
        except Exception as e:
            print(f"图像转换失败: {e}")
            # 返回空白图像
            return QImage()

    def get_available_cameras(self) -> List[Tuple[int, str]]:
        """
        获取可用的摄像头列表

        Returns:
            List[Tuple[int, str]]: 摄像头索引和描述列表
        """
        import platform

        cameras = []

        # 如果正在扫描，先停止
        was_scanning = self.scanning
        if was_scanning:
            self.stop_scanning()
            time.sleep(0.1)

        try:
            # Windows平台特殊处理
            if platform.system() == "Windows":
                # 方法1: 使用DirectShow后端
                print("正在检测摄像头（DirectShow后端）...")
                for index in range(5):  # 测试前5个索引
                    cap = None
                    try:
                        cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
                        if cap.isOpened():
                            # 尝试读取一帧验证
                            ret, frame = cap.read()
                            if ret and frame is not None and frame.size > 0:
                                camera_name = f"摄像头 {index}"

                                # 获取分辨率信息
                                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

                                if width > 0 and height > 0:
                                    camera_name += f" - {width}x{height}"

                                cameras.append((index, camera_name))
                                print(f"  发现摄像头 {index}: {camera_name}")
                            cap.release()
                    except Exception:
                        pass

                    # 如果DirectShow没找到，尝试默认后端
                    if not any(cam[0] == index for cam in cameras):
                        try:
                            cap = cv2.VideoCapture(index)
                            if cap.isOpened():
                                ret, frame = cap.read()
                                if ret and frame is not None and frame.size > 0:
                                    cameras.append((index, f"摄像头 {index}"))
                                    print(f"  发现摄像头 {index} (默认后端)")
                                cap.release()
                        except Exception:
                            pass
            else:
                # Linux/Mac 平台
                for index in range(5):
                    try:
                        cap = cv2.VideoCapture(index)
                        if cap.isOpened():
                            ret, frame = cap.read()
                            if ret and frame is not None and frame.size > 0:
                                cameras.append((index, f"摄像头 {index}"))
                            cap.release()
                    except Exception:
                        pass

            # 如果没有找到任何摄像头，添加一个友好的提示
            if not cameras:
                cameras.append((-1, "未找到可用摄像头"))
                print("未找到任何可用摄像头")
            else:
                print(f"摄像头检测完成，找到 {len(cameras)} 个可用摄像头")

        finally:
            # 恢复扫描状态
            if was_scanning:
                self.scanning = True

        return cameras

    def set_min_confidence(self, confidence: float) -> None:
        """
        设置最小置信度阈值

        Args:
            confidence: 置信度阈值（0.0-1.0）
        """
        self.min_confidence = max(0.0, min(1.0, confidence))

    def get_scanner_info(self) -> Dict[str, Any]:
        """
        获取扫描器信息

        Returns:
            Dict[str, any]: 扫描器信息字典
        """
        return {
            "use_camera": self.use_camera,
            "scanning": self.scanning,
            "camera_index": self.camera_index,
            "scan_timeout": self.scan_timeout,
            "min_confidence": self.min_confidence,
            "camera_resolution": self.camera_resolution,
            "pending_files": len(self.image_paths),
        }

    def is_scanning(self) -> bool:
        """检查是否正在扫描"""
        return self.scanning

    def clear_pending_files(self) -> None:
        """清除待扫描文件列表"""
        self.image_paths.clear()

    def __repr__(self) -> str:
        """返回字符串表示"""
        status = "扫描中" if self.scanning else "空闲"
        mode = "摄像头" if self.use_camera else f"文件({len(self.image_paths)})"
        return f"QRCodeScanner(status='{status}', mode='{mode}')"


class QRCodeBatchScanner:
    """二维码批量扫描器（用于批量处理）"""

    def __init__(self) -> None:
        """初始化批量扫描器"""
        self.scanner = QRCodeScanner()
        self.results: List[Dict] = []
        self.callbacks = {
            "on_progress": None,
            "on_result": None,
            "on_error": None,
            "on_finish": None,
        }

        # 连接信号
        self.scanner.qr_scanned.connect(self._handle_results)
        self.scanner.progress_updated.connect(self._handle_progress)
        self.scanner.error_occurred.connect(self._handle_error)
        self.scanner.scan_finished.connect(self._handle_finish)

    def scan_folder(
        self,
        folder_path: str,
        extensions: Optional[List[str]] = None,
        recursive: bool = True,
    ) -> None:
        """
        扫描文件夹中的图片文件

        Args:
            folder_path: 文件夹路径
            extensions: 支持的图片扩展名列表
            recursive: 是否递归扫描子文件夹
        """
        if extensions is None:
            extensions = [".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tiff", ".webp"]

        image_files = []

        if recursive:
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    if any(file.lower().endswith(ext) for ext in extensions):
                        image_files.append(os.path.join(root, file))
        else:
            for file in os.listdir(folder_path):
                file_path = os.path.join(folder_path, file)
                if os.path.isfile(file_path):
                    if any(file.lower().endswith(ext) for ext in extensions):
                        image_files.append(file_path)

        if image_files:
            self.scanner.scan_files(image_files)
        else:
            if self.callbacks["on_error"]:
                self.callbacks["on_error"]("未找到图片文件")

    def set_callback(self, callback_type: str, callback_func) -> None:
        """
        设置回调函数

        Args:
            callback_type: 回调类型
            callback_func: 回调函数
        """
        if callback_type in self.callbacks:
            self.callbacks[callback_type] = callback_func

    def stop(self) -> None:
        """停止扫描"""
        self.scanner.stop_scanning()

    def get_results(self) -> List[Dict]:
        """获取扫描结果"""
        return self.results.copy()

    def clear_results(self) -> None:
        """清除扫描结果"""
        self.results.clear()

    def _handle_results(self, results: List[Dict]) -> None:
        """处理扫描结果"""
        self.results.extend(results)
        if self.callbacks["on_result"]:
            self.callbacks["on_result"](results)

    def _handle_progress(self, progress: int, message: str) -> None:
        """处理进度更新"""
        if self.callbacks["on_progress"]:
            self.callbacks["on_progress"](progress, message)

    def _handle_error(self, error_message: str) -> None:
        """处理错误"""
        if self.callbacks["on_error"]:
            self.callbacks["on_error"](error_message)

    def _handle_finish(self) -> None:
        """处理扫描完成"""
        if self.callbacks["on_finish"]:
            self.callbacks["on_finish"](self.results)

    def __repr__(self) -> str:
        """返回字符串表示"""
        return f"QRCodeBatchScanner(results={len(self.results)}, scanning={self.scanner.is_scanning()})"
