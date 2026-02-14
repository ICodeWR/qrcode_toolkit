#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库管理模块 - QR Toolkit的数据库操作

模块名称：database.py
功能描述：提供二维码数据的SQLite数据库管理功能，包括增删改查、模板管理和历史记录
作者：码上工坊
联系：微信公众号（码上工坊）
版权声明：Copyright (c) 2026 码上工坊
开源协议：MIT License
免责声明：本软件按"原样"提供，不作任何明示或暗示的担保
修改记录：
版本 0.9.0 2026-01-10 - 码上工坊 - 初始版本创建
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# 导入统一的常量
from utils.constants import DEFAULT_DB_PATH, ensure_directories

from .models import QRCodeData, QRCodeType


class QRCodeDatabase:
    """二维码数据库管理类"""

    def __init__(self, db_path: Optional[str] = None) -> None:
        """
        初始化数据库管理器

        Args:
            db_path: 数据库文件路径，默认为用户数据目录下的qr_toolkit.db
        """
        if db_path is None:
            # 使用默认路径
            ensure_directories()  # 确保目录存在
            self.db_path = str(DEFAULT_DB_PATH)
        else:
            self.db_path = db_path

        self.init_database()

    def init_database(self) -> None:
        """
        初始化数据库表结构

        如果数据库文件不存在则创建，并创建所有必要的表
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # 创建二维码表
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS qrcodes (
                    id TEXT PRIMARY KEY,
                    data TEXT NOT NULL,
                    qr_type TEXT NOT NULL,
                    version INTEGER,
                    error_correction TEXT,
                    size INTEGER,
                    border INTEGER,
                    foreground_color TEXT,
                    background_color TEXT,
                    logo_path TEXT,
                    gradient_start TEXT,
                    gradient_end TEXT,
                    gradient_type TEXT,
                    created_at TEXT,
                    tags TEXT,
                    notes TEXT,
                    output_format TEXT
                )
            """
            )

            # 获取表信息
            cursor.execute("PRAGMA table_info(qrcodes)")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]

            # 如果logo_scale字段不存在，添加它
            if "logo_scale" not in column_names:
                try:
                    cursor.execute(
                        "ALTER TABLE qrcodes ADD COLUMN logo_scale REAL DEFAULT 0.2"
                    )
                    print("成功添加logo_scale字段到数据库")
                except sqlite3.Error as e:
                    print(f"添加logo_scale字段失败: {e}")

            # 创建模板表
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    config TEXT NOT NULL,
                    category TEXT,
                    created_at TEXT
                )
            """
            )

            conn.commit()
        except sqlite3.Error as e:
            print(f"数据库初始化失败: {e}")
            raise
        finally:
            conn.close()

    def save_qrcode(self, qr_data: QRCodeData) -> bool:
        """
        保存二维码数据到数据库

        Args:
            qr_data: QRCodeData实例

        Returns:
            bool: 保存是否成功
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 检查logo_scale字段是否存在
            cursor.execute("PRAGMA table_info(qrcodes)")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]
            has_logo_scale = "logo_scale" in column_names

            if has_logo_scale:
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO qrcodes 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        qr_data.id,
                        qr_data.data,
                        qr_data.qr_type.value,
                        qr_data.version,
                        qr_data.error_correction,
                        qr_data.size,
                        qr_data.border,
                        qr_data.foreground_color,
                        qr_data.background_color,
                        qr_data.logo_path,
                        qr_data.gradient_start,
                        qr_data.gradient_end,
                        qr_data.gradient_type,
                        qr_data.created_at,
                        json.dumps(qr_data.tags, ensure_ascii=False),
                        qr_data.notes,
                        qr_data.output_format,
                        qr_data.logo_scale,
                    ),
                )
            else:
                # 不包含logo_scale字段
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO qrcodes 
                    (id, data, qr_type, version, error_correction, size, border, 
                    foreground_color, background_color, logo_path, gradient_start, 
                    gradient_end, gradient_type, created_at, tags, notes, output_format)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        qr_data.id,
                        qr_data.data,
                        qr_data.qr_type.value,
                        qr_data.version,
                        qr_data.error_correction,
                        qr_data.size,
                        qr_data.border,
                        qr_data.foreground_color,
                        qr_data.background_color,
                        qr_data.logo_path,
                        qr_data.gradient_start,
                        qr_data.gradient_end,
                        qr_data.gradient_type,
                        qr_data.created_at,
                        json.dumps(qr_data.tags, ensure_ascii=False),
                        qr_data.notes,
                        qr_data.output_format,
                    ),
                )

            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"保存二维码数据失败: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def load_qrcode(self, qrcode_id: str) -> Optional[QRCodeData]:
        """
        从数据库加载二维码数据

        Args:
            qrcode_id: 二维码ID

        Returns:
            Optional[QRCodeData]: 如果找到则返回QRCodeData实例，否则返回None
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM qrcodes WHERE id = ?", (qrcode_id,))
            row = cursor.fetchone()

            if row:
                return self._row_to_qrcode_data(row)
        except sqlite3.Error as e:
            print(f"加载二维码数据失败: {e}")
        finally:
            if conn:
                conn.close()

        return None

    def get_all_qrcodes(self) -> List[QRCodeData]:
        """
        获取所有二维码数据

        Returns:
            List[QRCodeData]: 按创建时间倒序排列的二维码数据列表
        """
        qrcodes = []
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM qrcodes ORDER BY created_at DESC")

            for row in cursor.fetchall():
                qrcode_data = self._row_to_qrcode_data(row)
                if qrcode_data:
                    qrcodes.append(qrcode_data)
        except sqlite3.Error as e:
            print(f"获取所有二维码数据失败: {e}")
        finally:
            if conn:
                conn.close()

        return qrcodes

    def delete_qrcode(self, qrcode_id: str) -> bool:
        """
        删除二维码数据

        Args:
            qrcode_id: 二维码ID

        Returns:
            bool: 删除是否成功
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM qrcodes WHERE id = ?", (qrcode_id,))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"删除二维码数据失败: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def search_qrcodes(
        self,
        keyword: Optional[str] = None,
        qr_type: Optional[QRCodeType] = None,
        tags: Optional[List[str]] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[List[QRCodeData], int]:
        """
        搜索二维码数据

        Args:
            keyword: 搜索关键词，搜索数据和备注字段
            qr_type: 二维码类型过滤
            tags: 标签过滤
            limit: 返回结果数量限制
            offset: 结果偏移量

        Returns:
            Tuple[List[QRCodeData], int]: (二维码数据列表, 总数量)
        """
        qrcodes = []
        total = 0

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 构建查询条件
            conditions = []
            params = []

            if keyword:
                conditions.append("(data LIKE ? OR notes LIKE ?)")
                params.extend([f"%{keyword}%", f"%{keyword}%"])

            if qr_type:
                conditions.append("qr_type = ?")
                params.append(qr_type.value)

            if tags:
                for tag in tags:
                    conditions.append("tags LIKE ?")
                    params.append(f'%"{tag}"%')

            # 构建查询语句
            where_clause = " AND ".join(conditions) if conditions else "1=1"

            # 查询总数
            count_query = f"SELECT COUNT(*) FROM qrcodes WHERE {where_clause}"
            cursor.execute(count_query, params)
            total = cursor.fetchone()[0]

            # 查询数据
            query = f"""
                SELECT * FROM qrcodes 
                WHERE {where_clause}
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """
            params.extend([str(limit), str(offset)])

            cursor.execute(query, params)

            for row in cursor.fetchall():
                qrcode_data = self._row_to_qrcode_data(row)
                if qrcode_data:
                    qrcodes.append(qrcode_data)

        except sqlite3.Error as e:
            print(f"搜索二维码数据失败: {e}")
        finally:
            if conn:
                conn.close()

        return qrcodes, total

    def get_qrcodes_by_tag(self, tag: str) -> List[QRCodeData]:
        """
        根据标签获取二维码数据

        Args:
            tag: 标签名称

        Returns:
            List[QRCodeData]: 包含指定标签的二维码数据列表
        """
        return self.search_qrcodes(tags=[tag])[0]

    def save_template(
        self, name: str, config: Dict[str, Any], category: str = "General"
    ) -> bool:
        """
        保存模板到数据库

        Args:
            name: 模板名称
            config: 模板配置字典
            category: 模板分类

        Returns:
            bool: 保存是否成功
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO templates (name, config, category, created_at)
                VALUES (?, ?, ?, ?)
            """,
                (
                    name,
                    json.dumps(config, ensure_ascii=False),
                    category,
                    datetime.now().isoformat(),
                ),
            )

            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"保存模板失败: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def get_templates(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取所有模板

        Args:
            category: 模板分类过滤

        Returns:
            List[Dict[str, Any]]: 模板列表，每个模板包含id、name、config等字段
        """
        templates = []
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            if category:
                cursor.execute(
                    "SELECT * FROM templates WHERE category = ? ORDER BY name",
                    (category,),
                )
            else:
                cursor.execute("SELECT * FROM templates ORDER BY name")

            for row in cursor.fetchall():
                templates.append(
                    {
                        "id": row[0],
                        "name": row[1],
                        "config": json.loads(row[2]),
                        "category": row[3],
                        "created_at": row[4],
                    }
                )
        except (sqlite3.Error, json.JSONDecodeError) as e:
            print(f"获取模板失败: {e}")
        finally:
            if conn:
                conn.close()

        return templates

    def get_template(self, template_id: int) -> Optional[Dict[str, Any]]:
        """
        根据ID获取模板

        Args:
            template_id: 模板ID

        Returns:
            Optional[Dict[str, Any]]: 模板数据，如果未找到则返回None
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM templates WHERE id = ?", (template_id,))
            row = cursor.fetchone()

            if row:
                return {
                    "id": row[0],
                    "name": row[1],
                    "config": json.loads(row[2]),
                    "category": row[3],
                    "created_at": row[4],
                }
        except (sqlite3.Error, json.JSONDecodeError) as e:
            print(f"获取模板失败: {e}")
        finally:
            if conn:
                conn.close()

        return None

    def delete_template(self, template_id: int) -> bool:
        """
        删除模板

        Args:
            template_id: 模板ID

        Returns:
            bool: 删除是否成功
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM templates WHERE id = ?", (template_id,))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"删除模板失败: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取数据库统计信息

        Returns:
            Dict[str, Any]: 包含各种统计信息的字典
        """
        stats = {}
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 二维码总数
            cursor.execute("SELECT COUNT(*) FROM qrcodes")
            stats["total_qrcodes"] = cursor.fetchone()[0]

            # 按类型统计
            cursor.execute(
                "SELECT qr_type, COUNT(*) FROM qrcodes GROUP BY qr_type ORDER BY COUNT(*) DESC"
            )
            stats["qrcodes_by_type"] = dict(cursor.fetchall())

            # 模板统计
            cursor.execute("SELECT COUNT(*) FROM templates")
            stats["total_templates"] = cursor.fetchone()[0]

            # 最近7天生成数量
            cursor.execute(
                """
                SELECT DATE(created_at) as date, COUNT(*) as count
                FROM qrcodes
                WHERE created_at >= DATE('now', '-7 days')
                GROUP BY DATE(created_at)
                ORDER BY date DESC
            """
            )
            stats["recent_7_days"] = cursor.fetchall()

            # 平均数据长度
            cursor.execute("SELECT AVG(LENGTH(data)) FROM qrcodes")
            avg_length = cursor.fetchone()[0]
            stats["average_data_length"] = round(avg_length or 0, 2)

        except sqlite3.Error as e:
            print(f"获取统计信息失败: {e}")
        finally:
            if conn:
                conn.close()

        return stats

    def _row_to_qrcode_data(self, row: tuple) -> Optional[QRCodeData]:
        """
        将数据库行转换为QRCodeData对象

        Args:
            row: 数据库查询结果行

        Returns:
            Optional[QRCodeData]: 转换后的QRCodeData对象，转换失败返回None
        """
        try:
            # 解析标签
            tags = []
            if row[14]:  # tags字段
                try:
                    tags = json.loads(row[14])
                except json.JSONDecodeError:
                    tags = []

            # 创建QRCodeType枚举
            try:
                qr_type = QRCodeType(row[2])
            except ValueError:
                qr_type = QRCodeType.TEXT

            # 处理可选字段
            logo_path = row[9] if row[9] else None
            logo_scale = 0.2  # 默认值

            # 检查是否是新版数据库（有足够的列）
            if len(row) > 17:
                try:
                    logo_scale_val = row[17] if row[17] else 0.2
                    # 兼容旧数据：如果是字符串或整数，转换为浮点数
                    if isinstance(logo_scale_val, str):
                        logo_scale = float(logo_scale_val)
                    elif isinstance(logo_scale_val, (int, float)):
                        logo_scale = float(logo_scale_val)
                        # 如果是大于1的值，可能是百分比，转换为小数
                        if logo_scale > 1:
                            logo_scale = logo_scale / 100.0
                    else:
                        logo_scale = 0.2
                except (ValueError, TypeError, IndexError):
                    logo_scale = 0.2

            gradient_start = row[10] if row[10] else None
            gradient_end = row[11] if row[11] else None

            return QRCodeData(
                id=row[0],
                data=row[1],
                qr_type=qr_type,
                version=row[3] if row[3] is not None else 0,
                error_correction=row[4] if row[4] else "H",
                size=row[5] if row[5] is not None else 10,
                border=row[6] if row[6] is not None else 4,
                foreground_color=row[7] if row[7] else "#000000",
                background_color=row[8] if row[8] else "#FFFFFF",
                logo_path=logo_path,
                logo_scale=logo_scale,
                gradient_start=gradient_start,
                gradient_end=gradient_end,
                gradient_type=row[12] if row[12] else "linear",
                created_at=row[13] if row[13] else "",
                tags=tags,
                notes=row[15] if row[15] else "",
                output_format=row[16] if len(row) > 16 and row[16] else "PNG",
            )
        except (IndexError, ValueError, TypeError) as e:
            print(f"转换数据库行失败: {e}, row: {row}")
            return None

    def __enter__(self):
        """上下文管理器入口"""
        self._conn = sqlite3.connect(self.db_path)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        if self._conn:
            self._conn.close()

    def __repr__(self) -> str:
        """返回字符串表示"""
        return f"QRCodeDatabase(db_path='{self.db_path}')"
