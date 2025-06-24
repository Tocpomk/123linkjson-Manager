"""
123FastLink JSON工具 - 主程序入口

此模块是应用程序的入口点，负责启动GUI应用程序。
"""

import os
import sys
import tkinter as tk
from tkinterdnd2 import TkinterDnD

# 确保可以导入自定义模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gui.app import App


def main():
    """主函数，启动应用程序"""
    # 创建支持拖放的Tk根窗口
    root = TkinterDnD.Tk()
    
    # 创建并启动应用程序
    app = App(root)
    
    # 进入主循环
    root.mainloop()


if __name__ == "__main__":
    main()