# tests/conftest.py
import sys
import pytest
from PySide6.QtWidgets import QApplication

@pytest.fixture(scope="session")
def qapp():
    """创建QApplication实例（会话级）"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app
    # 测试会话结束时处理事件
    app.processEvents()