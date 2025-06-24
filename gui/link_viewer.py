"""
秒链查看器模块(弹窗版)

此模块提供了秒链解析和树状图显示功能，作为独立弹窗实现。
主要功能包括：
- 解析剪贴板中的秒链
- 在树状图中显示解析结果
- 支持选择性导出部分链接
- 弹窗管理功能(居中、模态、置顶)
"""

import tkinter as tk
from tkinter import ttk, messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from utils.link_parser import LinkParser


class LinkViewer(ttk.Toplevel):
    """秒链查看器弹窗"""
    
    def __init__(self, parent, app=None):
        """
        初始化秒链查看器弹窗
        
        Args:
            parent: 父级窗口部件
            app: 应用程序实例(可选)
        """
        super().__init__(parent)
        self.title("秒链查看器")
        self.geometry("800x600")
        self.transient(parent)  # 设为父窗口的子窗口
        self.grab_set()  # 设为模态窗口
        
        self.parent = parent
        self.app = app  # 保留app引用但不强制依赖
        
        # 窗口居中显示
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"+{x}+{y}")
        
        # 创建UI组件
        self.create_widgets()
        
        # 绑定窗口关闭事件
        self.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def create_widgets(self):
        """创建UI组件"""
        # 主框架
        self.frame = ttk.LabelFrame(self, text="秒链查看", padding="10")
        self.frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        # 树状图
        self.tree = ttk.Treeview(
            self.frame,
            columns=('name', 'size', 'link'),
            show='headings',
            selectmode='extended'
        )
        # 配置tag样式
        self.tree.tag_configure('full_link', foreground='black')
        
        # 绑定右键菜单
        self.tree.bind("<Button-3>", self.show_context_menu)
        
        # 设置列标题
        self.tree.heading('name', text='名称')
        self.tree.heading('size', text='大小')
        self.tree.heading('link', text='秒链')
        
        # 设置列宽
        self.tree.column('name', width=150, stretch=True)  # 名称列自动扩展
        self.tree.column('size', width=80, anchor='center', stretch=False)  # 固定宽度
        self.tree.column('link', width=200, stretch=True)  # 秒链列自动扩展
        
        # 滚动条
        scrollbar = ttk.Scrollbar(
            self.frame,
            orient=VERTICAL,
            command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # 布局
        self.tree.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)
        
        # 按钮框架
        btn_frame = ttk.Frame(self.frame)
        btn_frame.pack(fill=X, pady=(10, 0))
        
        # 导出选中按钮
        ttk.Button(
            btn_frame,
            text="导出选中",
            command=self.export_selected,
            bootstyle="success"
        ).pack(side=LEFT, padx=(0, 5))
        
        # 清空按钮
        ttk.Button(
            btn_frame,
            text="清空",
            command=self.clear_viewer,
            bootstyle="danger"
        ).pack(side=LEFT)
    
    def parse_and_show_links(self, link_text):
        """
        解析并显示秒链
        
        Args:
            link_text: 包含秒链的文本
        """
        # 清空现有内容
        self.clear_viewer()
        
        # 确保窗口显示在最前
        self.deiconify()
        self.lift()
        
        # 解析链接
        try:
            parsed_links, error = LinkParser.parse_link(link_text)
            if error:
                messagebox.showerror("解析错误", error)
                return
                
            # 按名称排序
            parsed_links.sort(key=lambda x: x['path'].split('/')[-1].lower())
                
            # 在树状图中显示
            for link in parsed_links:
                # 获取文件名
                name = link['path'].split('/')[-1] if '/' in link['path'] else link['path']
                
                # 生成完整秒链格式
                file_info = {
                    'path': link['path'],
                    'size': link['size'],
                    'etag': link['etag']
                }
                full_link = LinkParser.generate_link([file_info])
                # 显示时截断秒链，保留前30个字符
                display_link = full_link[:30] + "..." if len(full_link) > 30 else full_link
                
                self.tree.insert(
                    '',
                    'end',
                    values=(name, link['size'], display_link),
                    tags=(full_link,)  # 存储完整秒链作为tag
                )
                
        except Exception as e:
            messagebox.showerror("解析错误", f"解析秒链时出错: {str(e)}")
    
    def show_context_menu(self, event):
        """显示右键菜单"""
        item = self.tree.identify_row(event.y)
        if item:
            # 选中右键点击的行
            self.tree.selection_set(item)
            
            # 创建菜单
            menu = tk.Menu(self, tearoff=0)
            menu.add_command(label="导出选中", command=self.export_selected)
            menu.post(event.x_root, event.y_root)
    
    def export_selected(self):
        """导出选中的链接"""
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("警告", "请先选择要导出的链接")
            return
        
        # 获取选中项的数据并构建完整秒链
        links_to_export = []
        for item in selected_items:
            item_data = self.tree.item(item)
            # 从tag中获取完整秒链
            full_link = item_data['tags'][0] if item_data['tags'] else item_data['values'][2]
            if isinstance(full_link, str) and (full_link.startswith("123FSLink") or full_link.startswith("123FLCPV2")):
                links_to_export.append(full_link)
        
        # 将完整秒链复制到剪贴板
        try:
            export_text = "\n".join(links_to_export)
            self.clipboard_clear()
            self.clipboard_append(export_text)
            messagebox.showinfo("导出成功", f"已复制 {len(links_to_export)} 个完整秒链到剪贴板")
        except Exception as e:
            messagebox.showerror("导出错误", f"导出失败: {str(e)}")
    
    def clear_viewer(self):
        """清空树状图"""
        for item in self.tree.get_children():
            self.tree.delete(item)
    
    def on_close(self):
        """处理窗口关闭事件"""
        self.destroy()