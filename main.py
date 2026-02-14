#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
应用程序入口模块 - QR Toolkit的主程序入口

模块名称：main.py
功能描述：QR Toolkit应用程序的启动入口，初始化应用程序和主窗口
作者：码上工坊
联系：微信公众号（码上工坊）
版权声明：Copyright (c) 2026 码上工坊
开源协议：MIT License
免责声明：本软件按"原样"提供，不作任何明示或暗示的担保
修改记录：
版本 0.9.0 2026-01-10 - 码上工坊 - 初始版本创建
"""

import os
import sys
from pathlib import Path

# 设置系统编码为UTF-8
if sys.platform == "win32":
    os.environ["QT_QPA_PLATFORM"] = "windows:darkmode=0"
    os.environ["QT_LOGGING_RULES"] = "qt.qpa.dialogs.debug=false"
    # 设置控制台编码
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

# 抑制OpenCV警告
os.environ["OPENCV_LOG_LEVEL"] = "ERROR"
os.environ["OPENCV_VIDEOIO_DEBUG"] = "0"
os.environ["OPENCV_VIDEOIO_PRIORITY_DSHOW"] = "0"

# 添加当前目录到Python路径
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from PySide6.QtCore import QLocale
from PySide6.QtGui import QColor, QFont, QIcon, QPalette
from PySide6.QtWidgets import QApplication, QStyleFactory

from gui.main_window import QRToolkit
from utils.constants import APP_AUTHOR, APP_NAME, APP_VERSION


def setup_application() -> QApplication:
    """
    设置应用程序
    Returns:
        QApplication: 配置好的Qt应用程序实例
    """
    # 设置Qt本地化
    QLocale.setDefault(QLocale(QLocale.Language.Chinese, QLocale.Country.China))

    # 创建应用程序
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(APP_AUTHOR)
    app.setOrganizationDomain("qrcode.work")
    app.setApplicationDisplayName(f"{APP_NAME} - 二维码工具箱")

    # 设置应用程序版本
    app.setApplicationVersion(APP_VERSION)

    # 设置应用程序图标
    try:

        # 尝试多种路径查找图标
        icon_paths = [
            current_dir / "resources" / "icons" / "logo.png",
            current_dir / "resources" / "icon.png",
            current_dir / "icon.png",
        ]

        icon_found = False
        for icon_path in icon_paths:
            if icon_path.exists():
                app.setWindowIcon(QIcon(str(icon_path)))
                print(f"图标加载成功: {icon_path}")
                icon_found = True
                break

        if not icon_found:
            print("提示: 图标文件未找到，使用默认图标")
    except Exception as e:
        print(f"警告: 图标加载失败: {e}")

    # 设置样式
    app.setStyle(QStyleFactory.create("Fusion"))

    # 设置调色板
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(240, 240, 240))  # type: ignore
    palette.setColor(QPalette.ColorRole.WindowText, QColor(0, 0, 0))  # type: ignore
    palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))  # type: ignore
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(245, 245, 245))  # type: ignore
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 220))  # type: ignore
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(0, 0, 0))  # type: ignore
    palette.setColor(QPalette.ColorRole.Text, QColor(0, 0, 0))  # type: ignore
    palette.setColor(QPalette.ColorRole.Button, QColor(240, 240, 240))  # type: ignore
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(0, 0, 0))  # type: ignore
    palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))  # type: ignore
    palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))  # type: ignore
    palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))  # type: ignore
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))  # type: ignore

    # 设置禁用状态的颜色
    palette.setColor(
        QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(120, 120, 120)
    )
    palette.setColor(
        QPalette.ColorGroup.Disabled,
        QPalette.ColorRole.ButtonText,
        QColor(120, 120, 120),
    )

    app.setPalette(palette)

    # 设置字体
    font = QFont()
    if sys.platform == "win32":
        font.setFamily("Microsoft YaHei UI")
    elif sys.platform == "darwin":
        font.setFamily("PingFang SC")
    else:
        font.setFamily("Noto Sans CJK SC")

    font.setPointSize(10)
    app.setFont(font)

    return app


def create_data_directories() -> None:
    """创建必要的数据目录"""
    directories = [
        "templates",
        "exports",
        "backups",
        "logs",
    ]

    base_dir = Path.home() / ".qrtoolkit"
    try:
        base_dir.mkdir(exist_ok=True)

        for dir_name in directories:
            dir_path = base_dir / dir_name
            dir_path.mkdir(exist_ok=True)
            print(f"创建目录: {dir_path}")

        # 创建数据库文件
        db_path = base_dir / "qr_toolkit.db"
        if not db_path.exists():
            import sqlite3

            conn = sqlite3.connect(db_path)
            conn.commit()
            conn.close()
            print(f"创建数据库: {db_path}")

    except Exception as e:
        print(f"警告: 创建数据目录时出错: {e}")
        print("程序将继续运行，但部分功能可能受限")


def main() -> int:
    """
    主函数
    Returns:
        int: 退出代码
    """
    print("=" * 50)
    print(f"{APP_NAME} - 二维码工具箱")
    print(f"版本: {APP_VERSION}")
    print(f"作者: {APP_AUTHOR}")
    print("=" * 50)

    # 创建数据目录
    try:
        create_data_directories()
    except Exception as e:
        print(f"警告: 无法创建数据目录: {e}")

    # 创建应用程序
    try:
        app = setup_application()
    except Exception as e:
        print(f"错误: 创建应用程序失败: {e}")
        input("按Enter键退出...")
        return 1

    # 创建并显示主窗口
    try:
        window = QRToolkit()

        window.show()

        # 窗口最大化
        window.showMaximized()

        print("应用程序启动成功！")
        print("提示: 如果看到OpenCV错误，可以忽略（摄像头相关）")

        # 运行应用程序
        return app.exec()

    except Exception as e:
        print(f"错误: 无法启动应用程序: {e}")

        # 显示错误对话框
        try:
            from PySide6.QtWidgets import QMessageBox

            error_msg = f"应用程序启动失败:\n\n{str(e)}\n\n请检查错误信息。"
            QMessageBox.critical(None, "启动错误", error_msg)
        except:
            print("无法显示错误对话框")

        input("按Enter键退出...")
        return 1


if __name__ == "__main__":
    # 设置异常处理
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"未处理的异常: {e}")
        import traceback

        traceback.print_exc()
        input("按Enter键退出...")
