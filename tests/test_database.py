#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库模块单元测试 - QR Toolkit的数据库操作测试

模块名称：test_database.py
功能描述：对QRCodeDatabase类的所有方法进行单元测试
作者：码上工坊
联系：微信公众号（码上工坊）
版权声明：Copyright (c) 2026 码上工坊
开源协议：MIT License
免责声明：本软件按"原样"提供，不作任何明示或暗示的担保
修改记录：
版本 1.0.0 2026-01-01 - 码上工坊 - 初始版本创建
"""


import os
import sqlite3
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from core.database import QRCodeDatabase
from core.models import QRCodeData, QRCodeType


class TestQRCodeDatabase:
    """QRCodeDatabase类测试"""

    @pytest.fixture
    def temp_db_path(self):
        """创建临时数据库文件"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        yield db_path
        # 测试结束后清理
        if os.path.exists(db_path):
            os.unlink(db_path)

    @pytest.fixture
    def sample_qrcode_data(self):
        """创建测试用二维码数据"""
        return QRCodeData(
            id="test123",
            data="测试数据",
            qr_type=QRCodeType.TEXT,
            version=5,
            error_correction="H",
            size=10,
            border=4,
            foreground_color="#000000",
            background_color="#FFFFFF",
            tags=["test", "sample"],
            notes="测试备注",
        )

    @pytest.fixture
    def database(self, temp_db_path):
        """创建数据库实例"""
        return QRCodeDatabase(temp_db_path)

    def test_init_database_creates_tables(self, temp_db_path):
        """测试初始化数据库创建表"""
        db = QRCodeDatabase(temp_db_path)

        # 验证数据库文件存在
        assert os.path.exists(temp_db_path)

        # 验证表结构
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()

        # 检查表是否存在
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = [row[0] for row in cursor.fetchall()]

        expected_tables = ["qrcodes", "templates"]
        for table in expected_tables:
            assert table in tables

        conn.close()

    def test_init_database_existing_file(self, temp_db_path):
        """测试初始化已存在的数据库文件"""
        # 先创建数据库
        db1 = QRCodeDatabase(temp_db_path)

        # 再次初始化不应出错
        db2 = QRCodeDatabase(temp_db_path)
        assert db2.db_path == temp_db_path

    def test_save_qrcode(self, database, sample_qrcode_data):
        """测试保存二维码数据"""
        result = database.save_qrcode(sample_qrcode_data)
        assert result is True

        # 验证数据已保存
        conn = sqlite3.connect(database.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM qrcodes WHERE id = ?", (sample_qrcode_data.id,))
        row = cursor.fetchone()
        conn.close()

        assert row is not None
        assert row[0] == sample_qrcode_data.id
        assert row[1] == sample_qrcode_data.data
        assert row[2] == sample_qrcode_data.qr_type.value

    def test_save_qrcode_duplicate_id(self, database, sample_qrcode_data):
        """测试保存重复ID的二维码数据"""
        # 第一次保存
        result1 = database.save_qrcode(sample_qrcode_data)
        assert result1 is True

        # 修改数据后再次保存（相同ID）
        modified_data = QRCodeData(
            id=sample_qrcode_data.id,  # 相同ID
            data="修改后的数据",
            qr_type=QRCodeType.URL,
            version=3,
            error_correction="L",
            size=5,
            border=2,
            foreground_color="#FF0000",
            background_color="#00FF00",
        )

        result2 = database.save_qrcode(modified_data)
        assert result2 is True

        # 验证数据被更新
        loaded_data = database.load_qrcode(sample_qrcode_data.id)
        assert loaded_data is not None
        assert loaded_data.data == "修改后的数据"
        assert loaded_data.qr_type == QRCodeType.URL

    def test_save_qrcode_with_optional_fields(self, database):
        """测试保存包含可选字段的二维码数据"""
        qr_data = QRCodeData(
            id="test456",
            data="测试数据",
            qr_type=QRCodeType.WIFI,
            version=5,
            error_correction="H",
            size=10,
            border=4,
            foreground_color="#000000",
            background_color="#FFFFFF",
            logo_path="/path/to/logo.png",
            gradient_start="#FF0000",
            gradient_end="#00FF00",
            gradient_type="radial",
            tags=["work", "home"],
            notes="包含所有可选字段的测试",
            output_format="SVG",
        )

        result = database.save_qrcode(qr_data)
        assert result is True

        # 验证数据
        loaded_data = database.load_qrcode("test456")
        assert loaded_data is not None
        assert loaded_data.logo_path == "/path/to/logo.png"
        assert loaded_data.gradient_start == "#FF0000"
        assert loaded_data.gradient_end == "#00FF00"
        assert loaded_data.gradient_type == "radial"
        assert loaded_data.tags == ["work", "home"]
        assert loaded_data.notes == "包含所有可选字段的测试"
        assert loaded_data.output_format == "SVG"

    # 在文件顶部确保导入了 patch

    def test_save_qrcode_database_error(self, database, sample_qrcode_data):
        """测试数据库错误时的保存"""
        from unittest.mock import MagicMock, patch

        # 使用 patch 来 mock sqlite3.connect
        with patch("sqlite3.connect") as mock_connect:
            # 创建一个 mock connection
            mock_conn = MagicMock()
            # 让 cursor().execute() 正常工作（返回一个 mock cursor）
            mock_cursor = MagicMock()
            mock_conn.cursor.return_value = mock_cursor
            # 让 commit 抛出异常
            mock_conn.commit.side_effect = sqlite3.Error("模拟提交错误")

            # 让 sqlite3.connect 返回我们的 mock connection
            mock_connect.return_value = mock_conn

            # 执行保存操作
            result = database.save_qrcode(sample_qrcode_data)

            # 断言结果为 False
            assert result is False

    def test_load_qrcode_existing(self, database, sample_qrcode_data):
        """测试加载存在的二维码数据"""
        # 先保存数据
        database.save_qrcode(sample_qrcode_data)

        # 加载数据
        loaded_data = database.load_qrcode(sample_qrcode_data.id)

        assert loaded_data is not None
        assert loaded_data.id == sample_qrcode_data.id
        assert loaded_data.data == sample_qrcode_data.data
        assert loaded_data.qr_type == sample_qrcode_data.qr_type
        assert loaded_data.version == sample_qrcode_data.version
        assert loaded_data.error_correction == sample_qrcode_data.error_correction
        assert loaded_data.size == sample_qrcode_data.size
        assert loaded_data.border == sample_qrcode_data.border
        assert loaded_data.foreground_color == sample_qrcode_data.foreground_color
        assert loaded_data.background_color == sample_qrcode_data.background_color
        assert loaded_data.tags == sample_qrcode_data.tags
        assert loaded_data.notes == sample_qrcode_data.notes

    def test_load_qrcode_nonexistent(self, database):
        """测试加载不存在的二维码数据"""
        loaded_data = database.load_qrcode("nonexistent_id")
        assert loaded_data is None

    def test_load_qrcode_invalid_row_data(self, database, temp_db_path):
        """测试加载无效的行数据"""
        # 手动插入无效数据
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO qrcodes (id, data, qr_type) VALUES (?, ?, ?)",
            ("invalid_id", "test data", "INVALID_TYPE"),
        )
        conn.commit()
        conn.close()

        # 尝试加载应返回None
        db = QRCodeDatabase(temp_db_path)
        loaded_data = db.load_qrcode("invalid_id")
        assert loaded_data is not None  # 应该能创建对象，但类型可能默认
        assert loaded_data.qr_type == QRCodeType.TEXT  # 应回退到默认类型

    def test_get_all_qrcodes(self, database):
        """测试获取所有二维码数据"""
        # 创建多个测试数据
        test_data_list = []
        for i in range(5):
            qr_data = QRCodeData(
                id=f"test{i}",
                data=f"测试数据{i}",
                qr_type=QRCodeType.TEXT,
                version=i,
                error_correction="H",
                size=10 + i,
                border=4,
                foreground_color="#000000",
                background_color="#FFFFFF",
            )
            database.save_qrcode(qr_data)
            test_data_list.append(qr_data)

        # 获取所有数据
        all_data = database.get_all_qrcodes()

        assert len(all_data) == 5
        # 验证数据按创建时间倒序排列
        assert all_data[0].created_at >= all_data[1].created_at

    def test_get_all_qrcodes_empty(self, database):
        """测试获取空数据库的所有数据"""
        all_data = database.get_all_qrcodes()
        assert len(all_data) == 0

    def test_delete_qrcode_existing(self, database, sample_qrcode_data):
        """测试删除存在的二维码数据"""
        # 先保存
        database.save_qrcode(sample_qrcode_data)

        # 删除
        result = database.delete_qrcode(sample_qrcode_data.id)
        assert result is True

        # 验证已删除
        loaded_data = database.load_qrcode(sample_qrcode_data.id)
        assert loaded_data is None

    def test_delete_qrcode_nonexistent(self, database):
        """测试删除不存在的二维码数据"""
        result = database.delete_qrcode("nonexistent_id")
        assert result is False

    def test_search_qrcodes_by_keyword(self, database):
        """测试按关键词搜索"""
        # 创建测试数据
        data1 = QRCodeData(
            id="test1",
            data="这是一个测试数据",
            qr_type=QRCodeType.TEXT,
            version=5,
            error_correction="H",
            size=10,
            border=4,
            foreground_color="#000000",
            background_color="#FFFFFF",
            notes="测试备注",
        )

        data2 = QRCodeData(
            id="test2",
            data="另一个数据",
            qr_type=QRCodeType.URL,
            version=5,
            error_correction="H",
            size=10,
            border=4,
            foreground_color="#000000",
            background_color="#FFFFFF",
            notes="不同备注",
        )

        database.save_qrcode(data1)
        database.save_qrcode(data2)

        # 搜索包含"测试"的数据
        results, total = database.search_qrcodes(keyword="测试")
        assert total == 1
        assert len(results) == 1
        assert results[0].id == "test1"

        # 搜索包含"数据"的数据
        results, total = database.search_qrcodes(keyword="数据")
        assert total == 2
        assert len(results) == 2

    def test_search_qrcodes_by_type(self, database):
        """测试按类型搜索"""
        # 创建不同类型的数据
        for i, qr_type in enumerate([QRCodeType.TEXT, QRCodeType.URL, QRCodeType.WIFI]):
            qr_data = QRCodeData(
                id=f"test{i}",
                data=f"数据{i}",
                qr_type=qr_type,
                version=5,
                error_correction="H",
                size=10,
                border=4,
                foreground_color="#000000",
                background_color="#FFFFFF",
            )
            database.save_qrcode(qr_data)

        # 搜索TEXT类型
        results, total = database.search_qrcodes(qr_type=QRCodeType.TEXT)
        assert total == 1
        assert results[0].qr_type == QRCodeType.TEXT

        # 搜索URL类型
        results, total = database.search_qrcodes(qr_type=QRCodeType.URL)
        assert total == 1
        assert results[0].qr_type == QRCodeType.URL

    def test_search_qrcodes_by_tags(self, database):
        """测试按标签搜索"""
        # 创建带标签的数据
        data1 = QRCodeData(
            id="test1",
            data="数据1",
            qr_type=QRCodeType.TEXT,
            version=5,
            error_correction="H",
            size=10,
            border=4,
            foreground_color="#000000",
            background_color="#FFFFFF",
            tags=["work", "important"],
        )

        data2 = QRCodeData(
            id="test2",
            data="数据2",
            qr_type=QRCodeType.TEXT,
            version=5,
            error_correction="H",
            size=10,
            border=4,
            foreground_color="#000000",
            background_color="#FFFFFF",
            tags=["personal"],
        )

        database.save_qrcode(data1)
        database.save_qrcode(data2)

        # 搜索work标签
        results, total = database.search_qrcodes(tags=["work"])
        assert total == 1
        assert results[0].id == "test1"

        # 搜索多个标签
        results, total = database.search_qrcodes(tags=["work", "important"])
        assert total == 1
        assert results[0].id == "test1"

    def test_search_qrcodes_pagination(self, database):
        """测试搜索结果分页"""
        # 创建大量测试数据
        for i in range(25):
            qr_data = QRCodeData(
                id=f"test{i:02d}",
                data=f"测试数据{i:02d}",
                qr_type=QRCodeType.TEXT,
                version=5,
                error_correction="H",
                size=10,
                border=4,
                foreground_color="#000000",
                background_color="#FFFFFF",
            )
            database.save_qrcode(qr_data)

        # 第一页，每页10条
        results1, total1 = database.search_qrcodes(limit=10, offset=0)
        assert total1 == 25
        assert len(results1) == 10

        # 第二页
        results2, total2 = database.search_qrcodes(limit=10, offset=10)
        assert total2 == 25
        assert len(results2) == 10

        # 第三页（最后一页）
        results3, total3 = database.search_qrcodes(limit=10, offset=20)
        assert total3 == 25
        assert len(results3) == 5

    def test_get_qrcodes_by_tag(self, database):
        """测试根据标签获取数据"""
        data1 = QRCodeData(
            id="test1",
            data="数据1",
            qr_type=QRCodeType.TEXT,
            version=5,
            error_correction="H",
            size=10,
            border=4,
            foreground_color="#000000",
            background_color="#FFFFFF",
            tags=["tag1", "tag2"],
        )

        data2 = QRCodeData(
            id="test2",
            data="数据2",
            qr_type=QRCodeType.TEXT,
            version=5,
            error_correction="H",
            size=10,
            border=4,
            foreground_color="#000000",
            background_color="#FFFFFF",
            tags=["tag1"],
        )

        database.save_qrcode(data1)
        database.save_qrcode(data2)

        results = database.get_qrcodes_by_tag("tag1")
        assert len(results) == 2

        results = database.get_qrcodes_by_tag("tag2")
        assert len(results) == 1

        results = database.get_qrcodes_by_tag("nonexistent")
        assert len(results) == 0

    def test_save_template(self, database):
        """测试保存模板"""
        config = {"size": 10, "color": "#000000", "border": 4}

        result = database.save_template("测试模板", config, "测试分类")
        assert result is True

        # 验证模板已保存
        templates = database.get_templates()
        assert len(templates) == 1
        assert templates[0]["name"] == "测试模板"
        assert templates[0]["config"] == config
        assert templates[0]["category"] == "测试分类"
        assert "created_at" in templates[0]

    def test_get_templates(self, database):
        """测试获取模板"""
        # 保存多个模板
        configs = [
            {"name": "模板1", "config": {"size": 10}, "category": "分类1"},
            {"name": "模板2", "config": {"size": 15}, "category": "分类1"},
            {"name": "模板3", "config": {"size": 20}, "category": "分类2"},
        ]

        for config in configs:
            database.save_template(config["name"], config["config"], config["category"])

        # 获取所有模板
        all_templates = database.get_templates()
        assert len(all_templates) == 3
        assert all_templates[0]["name"] == "模板1"
        assert all_templates[1]["name"] == "模板2"
        assert all_templates[2]["name"] == "模板3"

        # 按分类获取
        category1_templates = database.get_templates(category="分类1")
        assert len(category1_templates) == 2

        category2_templates = database.get_templates(category="分类2")
        assert len(category2_templates) == 1

        # 不存在的分类
        nonexistent_templates = database.get_templates(category="不存在")
        assert len(nonexistent_templates) == 0

    def test_get_template_by_id(self, database):
        """测试根据ID获取模板"""
        config = {"size": 10, "color": "#000000"}
        database.save_template("测试模板", config, "测试分类")

        # 获取模板列表以获取ID
        templates = database.get_templates()
        assert len(templates) == 1

        template_id = templates[0]["id"]

        # 根据ID获取模板
        template = database.get_template(template_id)
        assert template is not None
        assert template["name"] == "测试模板"
        assert template["config"] == config

        # 不存在的ID
        nonexistent = database.get_template(999)
        assert nonexistent is None

    def test_delete_template(self, database):
        """测试删除模板"""
        config = {"size": 10}
        database.save_template("测试模板", config, "测试分类")

        # 获取ID
        templates = database.get_templates()
        template_id = templates[0]["id"]

        # 删除
        result = database.delete_template(template_id)
        assert result is True

        # 验证已删除
        templates = database.get_templates()
        assert len(templates) == 0

        # 删除不存在的模板
        result = database.delete_template(999)
        assert result is False

    def test_get_statistics(self, database):
        """测试获取统计信息"""
        # 创建测试数据
        for i in range(3):
            qr_data = QRCodeData(
                id=f"test{i}",
                data=f"数据{i}",
                qr_type=QRCodeType.TEXT,
                version=5,
                error_correction="H",
                size=10,
                border=4,
                foreground_color="#000000",
                background_color="#FFFFFF",
                tags=["test"] if i < 2 else [],  # 前两个有标签
            )
            database.save_qrcode(qr_data)

        # 添加模板
        database.save_template("模板1", {"size": 10}, "分类1")

        # 获取统计信息
        stats = database.get_statistics()

        assert "total_qrcodes" in stats
        assert stats["total_qrcodes"] == 3

        assert "qrcodes_by_type" in stats
        assert stats["qrcodes_by_type"]["文本"] == 3

        assert "total_templates" in stats
        assert stats["total_templates"] == 1

        assert "average_data_length" in stats
        # 数据长度："数据0" = 3字符 * 3 = 9，平均 = 9/3 = 3
        assert stats["average_data_length"] == 3.0

    def test_context_manager(self, temp_db_path):
        """测试上下文管理器"""
        with QRCodeDatabase(temp_db_path) as db:
            assert db._conn is not None
            # 验证连接可用
            db._conn.execute("SELECT 1")

        # 退出 with 块后，连接应已关闭
        # 尝试操作应抛出异常
        with pytest.raises(
            sqlite3.ProgrammingError, match="Cannot operate on a closed database"
        ):
            db._conn.execute("SELECT 1")

    def test_repr(self, database):
        """测试字符串表示"""
        repr_str = repr(database)
        assert "QRCodeDatabase" in repr_str
        assert database.db_path in repr_str

    def test_row_to_qrcode_data_conversion(self, database, temp_db_path):
        """测试行数据转换"""
        # 手动插入一行数据
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO qrcodes (
                id, data, qr_type, version, error_correction, size, border,
                foreground_color, background_color, logo_path, gradient_start,
                gradient_end, gradient_type, created_at, tags, notes, output_format
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                "test123",
                "测试数据",
                "TEXT",
                5,
                "H",
                10,
                4,
                "#000000",
                "#FFFFFF",
                "/path/to/logo.png",
                "#FF0000",
                "#00FF00",
                "radial",
                "2024-01-01T12:00:00",
                '["tag1", "tag2"]',
                "测试备注",
                "PNG",
            ),
        )
        conn.commit()

        cursor.execute("SELECT * FROM qrcodes WHERE id = ?", ("test123",))
        row = cursor.fetchone()
        conn.close()

        # 测试转换
        db = QRCodeDatabase(temp_db_path)
        qr_data = db._row_to_qrcode_data(row)

        assert qr_data is not None
        assert qr_data.id == "test123"
        assert qr_data.data == "测试数据"
        assert qr_data.qr_type == QRCodeType.TEXT
        assert qr_data.version == 5
        assert qr_data.error_correction == "H"
        assert qr_data.size == 10
        assert qr_data.border == 4
        assert qr_data.foreground_color == "#000000"
        assert qr_data.background_color == "#FFFFFF"
        assert qr_data.logo_path == "/path/to/logo.png"
        assert qr_data.gradient_start == "#FF0000"
        assert qr_data.gradient_end == "#00FF00"
        assert qr_data.gradient_type == "radial"
        assert qr_data.created_at == "2024-01-01T12:00:00"
        assert qr_data.tags == ["tag1", "tag2"]
        assert qr_data.notes == "测试备注"
        assert qr_data.output_format == "PNG"

    def test_row_to_qrcode_data_invalid_json(self, database, temp_db_path):
        """测试无效JSON标签的转换"""
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO qrcodes (id, data, qr_type, tags)
            VALUES (?, ?, ?, ?)
        """,
            ("test123", "数据", "TEXT", "invalid json"),
        )
        conn.commit()

        cursor.execute("SELECT * FROM qrcodes WHERE id = ?", ("test123",))
        row = cursor.fetchone()
        conn.close()

        db = QRCodeDatabase(temp_db_path)
        qr_data = db._row_to_qrcode_data(row)

        assert qr_data is not None
        assert qr_data.tags == []  # 无效JSON应返回空列表

    def test_row_to_qrcode_data_missing_fields(self, database, temp_db_path):
        """测试缺少字段的行数据转换"""
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO qrcodes (id, data, qr_type)
            VALUES (?, ?, ?)
        """,
            ("test123", "数据", "TEXT"),
        )
        conn.commit()

        cursor.execute("SELECT * FROM qrcodes WHERE id = ?", ("test123",))
        row = cursor.fetchone()
        conn.close()

        db = QRCodeDatabase(temp_db_path)
        qr_data = db._row_to_qrcode_data(row)

        assert qr_data is not None
        assert qr_data.id == "test123"
        assert qr_data.data == "数据"
        assert qr_data.qr_type == QRCodeType.TEXT
        # 验证默认值
        assert qr_data.version == 0
        assert qr_data.error_correction == "H"
        assert qr_data.size == 10
        assert qr_data.border == 4
        assert qr_data.foreground_color == "#000000"
        assert qr_data.background_color == "#FFFFFF"
        assert qr_data.gradient_type == "linear"
        assert qr_data.output_format == "PNG"
