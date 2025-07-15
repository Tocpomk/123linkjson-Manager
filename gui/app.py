"""
主应用程序模块

此模块提供了应用程序的主窗口和整体布局。
主要功能包括：
- 初始化应用程序窗口
- 协调各个面板之间的交互
- 处理全局事件
"""

import tkinter as tk
import os
import base64
from tkinter import messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from gui.file_panel import FilePanel
from gui.link_panel import LinkPanel
from gui.tree_view import TreeView
from gui.link_viewer import LinkViewer
from models.json_data import JsonData


class App:
    """123云盘秒链JSON管理器应用程序类"""
    
    def __init__(self, root):
        """
        初始化应用程序
        
        Args:
            root: TkinterDnD.Tk实例，主窗口
        """
        self.root = root
        self.root.title("123云盘秒链json管理器1.3")
        
        # 设置窗口图标
        self.set_window_icon()
        
        # 设置窗口大小并居中显示
        self.center_window(1040, 600)
        
        # 初始化数据模型
        self.json_data = None
        self.current_file = None
        self.init_json_data()
        
        # 创建GUI组件
        self.create_gui()
        
        # 程序启动后检查文件是否存在
        self.root.after(500, self.check_all_files_exist)
    
    def init_json_data(self):
        """初始化JSON数据模型"""
        if self.json_data is None:
            self.json_data = JsonData()
    
    def center_window(self, width, height):
        """
        将窗口居中显示
        
        Args:
            width: 窗口宽度
            height: 窗口高度
        """
        # 获取屏幕尺寸
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # 计算窗口居中的位置
        x_position = int((screen_width - width) / 2)
        y_position = int((screen_height - height) / 2)
        
        # 设置窗口大小和位置
        self.root.geometry(f"{width}x{height}+{x_position}+{y_position}")
    
    def set_window_icon(self):
        """设置窗口图标"""
        try:
            # 首先尝试使用base64内置图标
            from resources.icon_date import icon_data
            import base64
            from io import BytesIO
            
            # 解码base64数据
            img_data = base64.b64decode(icon_data.strip())
            self.icon = tk.PhotoImage(data=img_data)
            self.root.iconphoto(True, self.icon)
            
        except Exception as e:
            print(f"无法加载内置图标: {str(e)}")
            try:
                # 如果base64图标加载失败，尝试从resources目录加载图标文件
                icon_path = os.path.join("resources", "icn.png")
                if os.path.exists(icon_path):
                    self.icon = tk.PhotoImage(file=icon_path)
                    self.root.iconphoto(True, self.icon)
                else:
                    # 如果找不到图标文件，尝试从old目录加载
                    old_icon_path = os.path.join("old", "icn.png")
                    if os.path.exists(old_icon_path):
                        self.icon = tk.PhotoImage(file=old_icon_path)
                        self.root.iconphoto(True, self.icon)
            except Exception as e:
                print(f"无法加载图标文件: {str(e)}")
    
    def create_gui(self):
        """创建GUI组件"""
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.pack(fill=BOTH, expand=True)
        
        # 创建左侧文件面板
        self.file_panel = FilePanel(main_frame, self)
        self.file_panel.frame.pack(side=LEFT, fill=Y, padx=(0, 10), pady=5)
        
        # 创建右侧面板
        right_frame = ttk.Frame(main_frame, padding=(5, 0))
        right_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=5, pady=5)
        
        # 创建链接面板
        self.link_panel = LinkPanel(right_frame, self)
        self.link_panel.frame.pack(fill=X, pady=(0, 10), padx=5)
        
        # 创建树形视图面板
        self.tree_view = TreeView(right_frame, self)
        self.tree_view.frame.pack(fill=BOTH, expand=True, padx=5, pady=(0, 5))
        
        # 创建链接查看器面板
        self.link_viewer = None
    
    def check_all_files_exist(self):
        """检查所有文件是否存在，移除不存在的文件"""
        self.file_panel.check_all_files_exist()
    
    def load_json_file(self, filepath):
        """
        加载JSON文件
        
        Args:
            filepath: JSON文件路径
        """
        self.init_json_data()
        success, message = self.json_data.load(filepath)
        
        if success:
            self.current_file = filepath
            
            # 更新树形视图
            self.tree_view.reset_view()
            self.tree_view.update_view()
        else:
            messagebox.showerror("错误", f"无法加载文件: {message}")
    
    def add_link(self, link, batch_mode=False):
        """
        添加新链接
        
        Args:
            link: 123FSLink格式的链接字符串
            batch_mode: 是否为批量处理模式，批量模式下不会立即更新UI和保存文件
            
        Returns:
            Tuple[bool, str, int]: (是否成功, 消息, 添加的文件数)
        """
        from utils.link_parser import LinkParser
        
        # 解析链接
        files, error_msg = LinkParser.parse_link(link)
        
        if error_msg:
            return False, error_msg, 0
        
        if not files:
            return False, "未能从链接中解析出任何有效文件信息", 0
        
        # 如果没有加载任何JSON文件，创建新的
        if not self.json_data.data or 'files' not in self.json_data.data:
            filename = self.json_data.create_new()
            self.current_file = filename
        
        # 添加新文件
        added_count = self.json_data.add_files(files)
        
        # 如果不是批量模式，则立即保存和更新UI
        if not batch_mode:
            # 保存文件
            success, message = self.json_data.save(self.current_file)
            
            if not success:
                return False, message, 0
            
            # 更新树形视图
            self.tree_view.reset_view()
            self.tree_view.update_view()
            
            # 如果是新文件，添加到文件列表
            if self.current_file:
                filename = os.path.basename(self.current_file)
                self.file_panel.add_file_to_list(filename, self.current_file)
        
        return True, f"已添加 {added_count} 个新链接", added_count
    
    def batch_add_links(self, links):
        """
        批量添加多个链接
        
        Args:
            links: 链接列表
            
        Returns:
            Tuple[int, int, list]: (成功数, 总数, 错误信息列表)
        """
        success_count = 0
        total_count = len(links)
        error_messages = []
        total_files_added = 0
        
        # 批量处理所有链接
        for i, link in enumerate(links):
            success, message, added_count = self.add_link(link, batch_mode=True)
            
            if success:
                success_count += 1
                total_files_added += added_count
            else:
                error_messages.append(f"链接 {i+1}: {message}")
        
        # 批量处理完成后，保存文件并更新UI
        if success_count > 0:
            # 保存文件
            success, message = self.json_data.save(self.current_file)
            
            if not success:
                error_messages.append(f"保存文件失败: {message}")
            
            # 更新树形视图
            self.tree_view.reset_view()
            self.tree_view.update_view()
            
            # 如果是新文件，添加到文件列表
            if self.current_file:
                filename = os.path.basename(self.current_file)
                self.file_panel.add_file_to_list(filename, self.current_file)
        
        return success_count, total_count, error_messages, total_files_added
    
    def export_selected_links(self, selected_files):
        """
        导出选中文件的链接
        
        Args:
            selected_files: 选中的文件信息列表
            
        Returns:
            str: 生成的链接
        """
        from utils.link_parser import LinkParser
        
        # 生成123FSLinkV2格式的链接
        link = LinkParser.generate_link(selected_files)
        
        # 复制到剪贴板
        self.root.clipboard_clear()
        self.root.clipboard_append(link)
        
        return link
    
    def sort_current_file(self):
        """
        排序当前文件
        
        Returns:
            Tuple[bool, str]: (是否成功, 消息)
        """
        if not self.current_file:
            return False, "没有加载任何JSON文件"
        
        from utils.file_sorter import check_and_sort_json_file
        needs_sort, success, message = check_and_sort_json_file(self.current_file)
        
        if needs_sort and success:
            # 重新加载排序后的文件
            self.load_json_file(self.current_file)
            return True, "文件已成功排序"
        elif not needs_sort:
            return True, "文件已经是有序的"
        else:
            return False, f"排序失败: {message}"
    
    def merge_files(self, filepaths):
        """
        合并多个JSON文件
        
        Args:
            filepaths: JSON文件路径列表
            
        Returns:
            Tuple[bool, str, str]: (是否成功, 消息, 合并后的文件名)
        """
        if len(filepaths) < 2:
            return False, "请选择至少两个文件进行合并", ""
        
        try:
            # 合并文件
            merged_data, total_added = JsonData.merge_json_files(filepaths)
            
            if not merged_data:
                return False, "合并文件失败，无法读取文件数据", ""
            
            # 创建新的JsonData实例
            self.json_data = JsonData()
            self.json_data.data = merged_data
            
            # 生成新文件名并保存
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            merged_filename = f"123FastLink_merged_{timestamp}.json"
            
            success, message = self.json_data.save(merged_filename)
            
            if not success:
                return False, f"保存合并文件失败: {message}", ""
            
            # 更新当前文件
            self.current_file = merged_filename
            
            # 更新树形视图
            self.tree_view.reset_view()
            self.tree_view.update_view()
            
            return True, f"文件已合并，共合并了 {total_added} 个新链接", merged_filename
            
        except Exception as e:
            return False, f"合并文件时出错: {str(e)}", ""


def main():
    """应用程序入口点"""
    try:
        # 创建支持拖放的窗口
        root = TkinterDnD.Tk()
        # 配置ttkbootstrap主题
        style = ttk.Style(theme="darkly")
        app = App(root)
        root.mainloop()
    except Exception as e:
        # 如果TkinterDnD不可用，显示错误消息
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("错误", 
            f"无法初始化拖放功能: {str(e)}\n\n请确保已安装tkinterdnd2:\npip install tkinterdnd2")
        root.destroy()


if __name__ == "__main__":
    main()