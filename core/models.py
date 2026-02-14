#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QR Toolkit - 二维码工具箱
数据模型模块

此模块定义二维码相关的数据模型和枚举类。

作者: 码上工坊
协议: MIT License
修改记录:
版本 0.9.0 2026-01-10 - 码上工坊 - 初始版本创建
"""

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from utils.constants import OutputFormat, QRCodeType


@dataclass
class QRCodeData:
    """二维码数据类"""

    id: str
    data: str
    qr_type: QRCodeType
    version: int
    error_correction: str
    size: int
    border: int
    foreground_color: str
    background_color: str
    logo_path: Optional[str] = None
    logo_scale: float = 0.2
    gradient_start: Optional[str] = None
    gradient_end: Optional[str] = None
    gradient_type: str = "linear"
    created_at: str = ""
    tags: Optional[List[str]] = None
    notes: Optional[str] = None
    output_format: str = "PNG"

    def __post_init__(self) -> None:
        """
        初始化后处理

        如果未提供创建时间，则自动生成当前时间
        如果标签为None，则初始化为空列表
        确保logo_scale在有效范围内
        """
        if self.created_at == "":
            self.created_at = datetime.now().isoformat()
        if self.tags is None:
            self.tags = []
        # 确保logo_scale在5%-50%之间（0.05-0.5）
        if self.logo_scale < 0.05:
            self.logo_scale = 0.05
        elif self.logo_scale > 0.5:
            self.logo_scale = 0.5
        # 如果没有logo_path，将logo_scale设置为默认值
        if not self.logo_path:
            self.logo_scale = 0.2

    @classmethod
    def generate_id(cls, data: str) -> str:
        """
        生成唯一ID

        Args:
            data: 二维码数据内容

        Returns:
            str: 8位十六进制ID
        """
        timestamp = datetime.now().timestamp()
        data_str = f"{data}_{timestamp}"
        hash_digest = hashlib.md5(data_str.encode()).hexdigest()
        return hash_digest[:8]

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典

        Returns:
            Dict[str, Any]: 包含所有属性的字典
        """
        result = asdict(self)
        result["qr_type"] = self.qr_type.value
        return result

    @classmethod
    def from_dict(cls, data_dict: Dict[str, Any]) -> "QRCodeData":
        """
        从字典创建QRCodeData实例

        Args:
            data_dict: 包含QRCodeData属性的字典

        Returns:
            QRCodeData: 新实例

        Raises:
            ValueError: 如果字典格式无效
        """
        try:
            # 转换QRCodeType枚举
            if "qr_type" in data_dict:
                if isinstance(data_dict["qr_type"], QRCodeType):
                    qr_type = data_dict["qr_type"]
                elif isinstance(data_dict["qr_type"], str):
                    # 从字符串创建枚举
                    qr_type = QRCodeType(data_dict["qr_type"])
                else:
                    raise ValueError(f"无效的qr_type值: {data_dict['qr_type']}")
            else:
                qr_type = QRCodeType.TEXT

            # 确保tags为列表
            tags = data_dict.get("tags", [])
            if isinstance(tags, str):
                tags = json.loads(tags) if tags else []
            elif tags is None:
                tags = []

            # 转换OutputFormat
            output_format = data_dict.get("output_format", "PNG")
            if isinstance(output_format, OutputFormat):
                output_format = output_format.value

            # 处理logo_scale字段（兼容旧版本）
            logo_scale = data_dict.get("logo_scale", 0.2)
            if logo_scale is None:
                logo_scale = 0.2
            # 如果是从百分比转换来的，可能需要处理
            if isinstance(logo_scale, int) or (
                isinstance(logo_scale, float) and logo_scale > 1
            ):
                logo_scale = float(logo_scale) / 100.0

            return cls(
                id=data_dict.get("id", cls.generate_id(data_dict.get("data", ""))),
                data=data_dict.get("data", ""),
                qr_type=qr_type,
                version=data_dict.get("version", 0),
                error_correction=data_dict.get("error_correction", "H"),
                size=data_dict.get("size", 10),
                border=data_dict.get("border", 4),
                foreground_color=data_dict.get("foreground_color", "#000000"),
                background_color=data_dict.get("background_color", "#FFFFFF"),
                logo_path=data_dict.get("logo_path"),
                logo_scale=logo_scale,
                gradient_start=data_dict.get("gradient_start"),
                gradient_end=data_dict.get("gradient_end"),
                gradient_type=data_dict.get("gradient_type", "linear"),
                created_at=data_dict.get("created_at", ""),
                tags=tags,
                notes=data_dict.get("notes", ""),
                output_format=output_format,
            )
        except Exception as e:
            raise ValueError(f"从字典创建QRCodeData失败: {e}")

    def validate(self) -> Tuple[bool, str]:
        """
        验证数据有效性

        Returns:
            Tuple[bool, str]: (是否有效, 错误消息)
        """
        if not self.data or self.data.strip() == "":
            return False, "二维码数据不能为空"

        if self.size < 1 or self.size > 50:
            return False, "模块大小必须在1到50之间"

        if self.border < 0 or self.border > 10:
            return False, "边框大小必须在0到10之间"

        if self.version < 0 or self.version > 40:
            return False, "版本必须在0到40之间（0表示自动）"

        if self.error_correction not in ["L", "M", "Q", "H"]:
            return False, "纠错级别必须是L、M、Q或H"

        # 验证Logo缩放比例
        if self.logo_scale < 0.05 or self.logo_scale > 0.5:
            return False, "Logo缩放比例必须在5%到50%之间"

        # 如果有Logo路径但没有文件，只给警告
        if self.logo_path:
            import os

            if not os.path.exists(self.logo_path):
                # 这里只警告，不阻止生成
                pass

        # 使用统一的颜色验证函数
        from utils.constants import is_valid_color

        for color_name, color_value in [
            ("前景色", self.foreground_color),
            ("背景色", self.background_color),
        ]:
            if not is_valid_color(color_value):
                return False, f"{color_name}格式无效: {color_value}"

        # 验证渐变颜色
        if self.gradient_start and not is_valid_color(self.gradient_start):
            return False, f"渐变起始颜色格式无效: {self.gradient_start}"

        if self.gradient_end and not is_valid_color(self.gradient_end):
            return False, f"渐变结束颜色格式无效: {self.gradient_end}"

        # 如果设置了渐变，必须同时有起始和结束颜色
        if (self.gradient_start and not self.gradient_end) or (
            self.gradient_end and not self.gradient_start
        ):
            return False, "渐变必须同时设置起始和结束颜色"

        if self.gradient_type not in ["linear", "radial"]:
            return False, "渐变类型必须是linear或radial"

        return True, "数据有效"

    def get_info_summary(self) -> str:
        """
        获取二维码信息摘要

        Returns:
            str: 格式化的信息摘要
        """
        summary_lines = [
            f"二维码ID: {self.id}",
            f"类型: {self.qr_type.value}",
            f"版本: {self.version if self.version > 0 else '自动'}",
            f"纠错级别: {self.error_correction}",
            f"模块大小: {self.size}px",
            f"边框: {self.border}模块",
            f"前景色: {self.foreground_color}",
            f"背景色: {self.background_color}",
            f"数据长度: {len(self.data)} 字符",
            f"创建时间: {self.created_at}",
            f"输出格式: {self.output_format}",
        ]

        if self.logo_path:
            summary_lines.append(f"Logo: {self.logo_path}")
            summary_lines.append(f"Logo缩放: {int(self.logo_scale * 100)}%")

        if self.gradient_start and self.gradient_end:
            summary_lines.append(
                f"渐变: {self.gradient_start} → {self.gradient_end} ({self.gradient_type})"
            )

        if self.tags:
            summary_lines.append(f"标签: {', '.join(self.tags)}")

        if self.notes:
            summary_lines.append(
                f"备注: {self.notes[:50]}{'...' if len(self.notes) > 50 else ''}"
            )

        return "\n".join(summary_lines)
