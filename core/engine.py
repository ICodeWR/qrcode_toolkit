#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
二维码引擎模块 - QR Toolkit的核心二维码生成引擎

模块名称：engine.py
功能描述：提供二维码生成、渐变效果、Logo添加等核心功能，支持单线程和多线程生成
作者：码上工坊
联系：微信公众号（码上工坊）
版权声明：Copyright (c) 2026 码上工坊
开源协议：MIT License
免责声明：本软件按"原样"提供，不作任何明示或暗示的担保
修改记录：
版本 0.9.0 2026-01-10 - 码上工坊 - 初始版本创建
"""

import io
import os
from typing import List, Optional, Tuple

import qrcode
from PIL import Image, ImageDraw
from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QImage
from qrcode.constants import (
    ERROR_CORRECT_H,
    ERROR_CORRECT_L,
    ERROR_CORRECT_M,
    ERROR_CORRECT_Q,
)

from .models import QRCodeData


class QRCodeEngine(QThread):
    """二维码生成引擎（支持多线程）"""

    # 信号定义
    qr_generated = Signal(object, QImage)  # QRCodeData, QImage
    progress_updated = Signal(int, str)  # 进度值, 状态信息
    error_occurred = Signal(str)  # 错误信息
    batch_completed = Signal(int, int)  # 已完成, 总数

    def __init__(self, parent=None) -> None:
        """
        初始化二维码生成引擎

        Args:
            parent: 父对象
        """
        super().__init__(parent)
        self.qr_data: Optional[QRCodeData] = None
        self.batch_data: List[QRCodeData] = []
        self.generate_logo: bool = True
        self.running: bool = False

    def generate(self, qr_data: QRCodeData) -> None:
        """
        生成单个二维码

        Args:
            qr_data: 二维码数据对象
        """
        self.qr_data = qr_data
        self.batch_data = []
        self.running = True
        self.start()

    def generate_batch(self, qr_data_list: List[QRCodeData]) -> None:
        """
        批量生成二维码

        Args:
            qr_data_list: 二维码数据对象列表
        """
        self.qr_data = None
        self.batch_data = qr_data_list
        self.running = True
        self.start()

    def stop(self) -> None:
        """停止生成"""
        self.running = False

    def run(self) -> None:
        """线程运行方法"""
        try:
            if self.batch_data:
                self._generate_batch()
            else:
                self._generate_single()
        except Exception as e:
            self.error_occurred.emit(f"生成失败: {str(e)}")
        finally:
            self.running = False

    def _generate_single(self) -> None:
        """生成单个二维码"""
        if not self.qr_data:
            self.error_occurred.emit("没有可生成的二维码数据")
            return

        try:
            self.progress_updated.emit(10, "初始化参数...")

            # 验证数据
            is_valid, message = self.qr_data.validate()
            if not is_valid:
                self.error_occurred.emit(f"数据验证失败: {message}")
                return

            # 创建二维码对象
            qr = qrcode.QRCode(
                version=self.qr_data.version if self.qr_data.version > 0 else None,
                error_correction=self._get_error_correction(
                    self.qr_data.error_correction
                ),
                box_size=self.qr_data.size,
                border=self.qr_data.border,
            )

            qr.add_data(self.qr_data.data)
            qr.make(fit=True)

            self.progress_updated.emit(30, "生成二维码矩阵...")

            # 处理渐变颜色
            if self.qr_data.gradient_start and self.qr_data.gradient_end:
                image = self._generate_gradient_qr(qr)
            else:
                qr_image = qr.make_image(
                    fill_color=self.qr_data.foreground_color,
                    back_color=self.qr_data.background_color,
                )
                image = self._convert_to_pil_image(qr_image)

            self.progress_updated.emit(60, "处理Logo...")

            # 添加Logo
            if (
                self.generate_logo
                and self.qr_data.logo_path
                and os.path.exists(self.qr_data.logo_path)
            ):
                image = self._add_logo(image)

            self.progress_updated.emit(80, "转换为QImage...")

            # 转换为QImage
            qimage = self._pil_to_qimage(image)

            self.progress_updated.emit(100, "生成完成")
            self.qr_generated.emit(self.qr_data, qimage)

        except Exception as e:
            self.error_occurred.emit(f"生成失败: {str(e)}")

    def _generate_batch(self) -> None:
        """批量生成二维码"""
        total = len(self.batch_data)
        successful = 0

        self.progress_updated.emit(0, f"开始批量生成，共 {total} 个二维码")

        for i, qr_data in enumerate(self.batch_data):
            if not self.running:
                self.progress_updated.emit(0, "批量生成已取消")
                # 发送当前进度，但不发送最终完成信号
                self.batch_completed.emit(i, total)
                break

            try:
                # 更新进度
                progress = int((i + 1) / total * 100) if total > 0 else 0
                self.progress_updated.emit(
                    progress, f"正在生成 {i+1}/{total}: {qr_data.id[:8]}"
                )

                # 二维码生成核心代码
                qr = qrcode.QRCode(
                    version=qr_data.version if qr_data.version > 0 else None,
                    error_correction=self._get_error_correction(
                        qr_data.error_correction
                    ),
                    box_size=qr_data.size,
                    border=qr_data.border,
                )
                qr.add_data(qr_data.data)
                qr.make(fit=True)

                if qr_data.gradient_start and qr_data.gradient_end:
                    image = self._generate_gradient_qr(qr, qr_data)
                else:
                    qr_image = qr.make_image(
                        fill_color=qr_data.foreground_color,
                        back_color=qr_data.background_color,
                    )
                    image = self._convert_to_pil_image(qr_image)

                if qr_data.logo_path and os.path.exists(qr_data.logo_path):
                    image = self._add_logo(image, qr_data)

                # 保存文件
                output_dir = qr_data.notes if hasattr(qr_data, "notes") else None

                # 确定输出格式
                output_format = "PNG"
                if hasattr(qr_data, "output_format") and qr_data.output_format:
                    output_format = qr_data.output_format.upper()

                # 扩展名映射
                ext_map = {
                    "PNG": ".png",
                    "JPEG": ".jpg",
                    "JPG": ".jpg",
                    "BMP": ".bmp",
                    "SVG": ".svg",
                    "PDF": ".pdf",
                    "GIF": ".gif",
                }
                ext = ext_map.get(output_format, ".png")

                # 生成文件名
                filename = f"qrcode_{qr_data.id}{ext}"

                if output_dir:
                    os.makedirs(output_dir, exist_ok=True)
                    filepath = os.path.join(output_dir, filename)
                else:
                    filepath = filename

                # 根据格式保存
                if output_format == "PNG":
                    image.save(filepath, format="PNG", optimize=True)
                elif output_format in ["JPEG", "JPG"]:
                    # 转换为RGB（去除透明通道）
                    if image.mode in ("RGBA", "LA", "P"):
                        rgb_image = Image.new("RGB", image.size, (255, 255, 255))
                        if image.mode == "RGBA":
                            rgb_image.paste(image, mask=image.split()[-1])
                        else:
                            rgb_image.paste(image)
                        rgb_image.save(filepath, format="JPEG", quality=95)
                    else:
                        image.save(filepath, format="JPEG", quality=95)
                elif output_format == "BMP":
                    image.save(filepath, format="BMP")
                else:
                    # 默认保存为PNG
                    image.save(filepath, format="PNG")

                successful += 1

                # 发送进度信号（但这不是完成信号）
                self.batch_completed.emit(i + 1, total)

            except Exception as e:
                print(f"生成 {qr_data.id} 失败: {e}")
                self.error_occurred.emit(f"生成 {qr_data.id[:8]} 失败: {str(e)[:50]}")
                # 即使失败也要发送进度
                self.batch_completed.emit(i + 1, total)

        # 最终只发送一次完成信号
        if self.running:
            self.progress_updated.emit(100, f"批量生成完成，成功 {successful}/{total}")

    def _convert_to_pil_image(self, qr_image) -> Image.Image:
        """
        将 qrcode 生成的图像转换为 PIL Image 对象

        支持多种输入类型：
        - PIL Image
        - qrcode.image.pil.PilImage
        - qrcode.image.svg.SvgImage
        - 其他（通过保存到内存再读取）

        Args:
            qr_image: qrcode 库生成的图像

        Returns:
            PIL Image 对象
        """
        try:
            # 如果已经是 PIL Image，直接返回
            if isinstance(qr_image, Image.Image):
                return qr_image

            # 如果是 qrcode 的 PilImage 对象，获取其 image 属性
            elif hasattr(qr_image, "image") and isinstance(qr_image.image, Image.Image):
                return qr_image.image

            # 其他情况，通过字节流转换
            else:
                buffer = io.BytesIO()
                qr_image.save(buffer, format="PNG")
                buffer.seek(0)
                return Image.open(buffer).convert("RGB")

        except Exception as e:
            print(f"PIL图像转换失败: {e}")
            # 返回一个默认的空白图像
            return Image.new("RGB", (100, 100), color="white")

    def _get_error_correction(self, level: str) -> int:
        """获取纠错级别对应的常量"""
        level_map = {
            "L": ERROR_CORRECT_L,  # 7%
            "M": ERROR_CORRECT_M,  # 15%
            "Q": ERROR_CORRECT_Q,  # 25%
            "H": ERROR_CORRECT_H,  # 30%
        }
        if not level or not isinstance(level, str):
            return ERROR_CORRECT_H
        return level_map.get(level.upper(), ERROR_CORRECT_H)

    def _generate_gradient_qr(
        self, qr: qrcode.QRCode, qr_data: Optional[QRCodeData] = None
    ) -> Image.Image:
        """
        生成渐变二维码

        Args:
            qr: 二维码对象
            qr_data: 二维码数据对象（可选，如果不提供则使用self.qr_data）

        Returns:
            Image.Image: 渐变二维码图像

        Raises:
            ValueError: 如果渐变颜色无效或二维码数据未设置
        """
        data = qr_data or self.qr_data
        if not data:
            raise ValueError("二维码数据未设置")

        matrix = qr.get_matrix()
        if not matrix:
            raise ValueError("二维码矩阵为空")

        size = len(matrix) * data.size

        # 创建PIL图像
        image = Image.new("RGB", (size, size), data.background_color)
        draw = ImageDraw.Draw(image)

        # 解析颜色
        if not data.gradient_start or not data.gradient_end:
            raise ValueError("渐变颜色未设置")

        color_start = self._parse_color(data.gradient_start)
        color_end = self._parse_color(data.gradient_end)

        # 绘制渐变
        for y in range(len(matrix)):
            for x in range(len(matrix[y])):
                if matrix[y][x]:
                    # 计算渐变比例
                    if data.gradient_type == "radial":
                        center_x, center_y = len(matrix) // 2, len(matrix) // 2
                        distance = ((x - center_x) ** 2 + (y - center_y) ** 2) ** 0.5
                        max_distance = ((len(matrix) ** 2) * 2) ** 0.5
                        ratio = distance / max_distance if max_distance > 0 else 0
                    else:  # linear
                        ratio = (x + y) / (len(matrix) * 2)

                    # 颜色插值
                    r = int(color_start[0] * (1 - ratio) + color_end[0] * ratio)
                    g = int(color_start[1] * (1 - ratio) + color_end[1] * ratio)
                    b = int(color_start[2] * (1 - ratio) + color_end[2] * ratio)

                    draw.rectangle(
                        [
                            x * data.size,
                            y * data.size,
                            (x + 1) * data.size,
                            (y + 1) * data.size,
                        ],
                        fill=(r, g, b),
                    )

        return image

    def _parse_color(self, color_str: str) -> Tuple[int, int, int]:
        """解析颜色字符串"""
        if (
            not color_str
            or not isinstance(color_str, str)
            or not color_str.startswith("#")
        ):
            raise ValueError(f"无效的颜色格式: {color_str}")

        color_str = color_str[1:]  # 移除#

        # 处理3位简写格式
        if len(color_str) == 3:
            color_str = "".join([c * 2 for c in color_str])
        elif len(color_str) != 6:
            raise ValueError(f"颜色格式长度无效: {color_str}")

        try:
            return (
                int(color_str[0:2], 16),
                int(color_str[2:4], 16),
                int(color_str[4:6], 16),
            )
        except ValueError:
            raise ValueError(f"颜色值包含无效字符: {color_str}")

    def _add_logo(
        self, qr_image: Image.Image, qr_data: Optional[QRCodeData] = None
    ) -> Image.Image:
        """
        添加Logo到二维码

        Args:
            qr_image: 二维码图像
            qr_data: 二维码数据对象（可选，如果不提供则使用self.qr_data）

        Returns:
            Image.Image: 添加Logo后的图像

        Raises:
            FileNotFoundError: 如果Logo文件不存在
            ValueError: 如果二维码数据未设置
        """
        data = qr_data or self.qr_data
        if not data or not data.logo_path:
            return qr_image

        if not os.path.exists(data.logo_path):
            raise FileNotFoundError(f"Logo文件不存在: {data.logo_path}")

        try:
            logo: Image.Image = Image.open(data.logo_path)

            # 从QRCodeData获取缩放比例，默认为0.2（20%）
            scale_ratio = getattr(data, "logo_scale", 0.2)
            logo_size = int(min(qr_image.size) * scale_ratio)

            # 边界保护
            if logo_size < 20:
                logo_size = 20
            if logo_size > min(qr_image.size) // 2:
                logo_size = min(qr_image.size) // 2

            # 调整Logo大小
            logo = logo.convert("RGBA")
            logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)

            # 创建圆形遮罩
            mask = Image.new("L", (logo_size, logo_size), 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0, logo_size, logo_size), fill=255)

            # 粘贴Logo
            pos = (
                (qr_image.size[0] - logo_size) // 2,
                (qr_image.size[1] - logo_size) // 2,
            )

            qr_image.paste(logo, pos, mask)
            return qr_image

        except Exception as e:
            print(f"添加Logo失败: {e}")
            return qr_image

    def _pil_to_qimage(self, pil_image: Image.Image) -> QImage:
        """
        将PIL图像转换为QImage

        Args:
            pil_image: PIL图像对象

        Returns:
            QImage: Qt图像对象
        """
        # 确保为RGB模式
        if pil_image.mode != "RGB":
            pil_image = pil_image.convert("RGB")

        # 获取图像数据
        buffer = io.BytesIO()
        pil_image.save(buffer, format="PNG")
        buffer.seek(0)

        # 创建QImage
        qimage = QImage()
        qimage.loadFromData(buffer.getvalue())
        return qimage

    def get_qr_size(
        self, data: str, version: int = 0, size: int = 10, border: int = 4
    ) -> Tuple[int, int]:
        """
        计算二维码的理论大小

        Args:
            data: 二维码数据
            version: 二维码版本，0表示自动
            size: 模块大小
            border: 边框大小

        Returns:
            Tuple[int, int]: (宽度, 高度)
        """
        try:
            qr = qrcode.QRCode(
                version=version if version > 0 else None,
                error_correction=ERROR_CORRECT_H,
                box_size=size,
                border=border,
            )
            qr.add_data(data)
            qr.make(fit=True)

            matrix_size = len(qr.get_matrix())
            total_size = matrix_size * size
            return (total_size, total_size)
        except Exception:
            # 如果计算失败，返回默认大小
            return (200, 200)

    def validate_data_capacity(
        self, data: str, version: int, error_correction: str
    ) -> bool:
        """
        验证数据容量是否适合指定版本和纠错级别

        Args:
            data: 要编码的数据
            version: 二维码版本（1-40）
            error_correction: 纠错级别（L、M、Q、H）

        Returns:
            bool: 数据是否适合
        """
        # 检查版本有效性
        if version < 1 or version > 40:
            return False

        try:
            qr = qrcode.QRCode(
                version=version,
                error_correction=self._get_error_correction(error_correction),
                box_size=10,
                border=4,
            )
            qr.add_data(data)
            qr.make(fit=False)  # 不自动调整，用于验证
            return True
        except ValueError as e:
            # qrcode 库通常使用 ValueError 表示数据溢出
            error_msg = str(e).lower()
            if "data overflow" in error_msg or "data too large" in error_msg:
                return False
            elif "invalid version" in error_msg:
                return False
            # 重新抛出其他 ValueError
            raise
        except Exception:
            return False

    def get_supported_versions(self) -> List[int]:
        """获取支持的二维码版本列表（1-40）"""
        return list(range(1, 41))

    def get_error_correction_levels(self) -> List[Tuple[str, str]]:
        """获取支持的纠错级别列表"""
        return [
            ("L", "L (7%) - 低"),
            ("M", "M (15%) - 中"),
            ("Q", "Q (25%) - 较高"),
            ("H", "H (30%) - 高"),
        ]

    def is_running(self) -> bool:
        """检查引擎是否正在运行"""
        return self.running

    def __repr__(self) -> str:
        """返回字符串表示"""
        status = "运行中" if self.running else "空闲"
        return f"QRCodeEngine(status='{status}', batch_size={len(self.batch_data)})"
