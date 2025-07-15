
"""
树形视图模块

此模块提供了应用程序下部的文件树形视图。
主要功能包括：
- 显示文件列表
- 文件选择
- 文件排序
- 右键菜单操作
"""

import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from gui.search_bar import SearchBar
import re


class TreeView:
    """文件树形视图类"""
    
    def __init__(self, parent, app):
        """
        初始化树形视图
        
        Args:
            parent: 父级窗口部件
            app: 应用程序实例
        """
        self.parent = parent
        self.app = app
        
        # 分页相关变量
        self.page_size = 50  # 每页显示的文件数
        self.current_page = 1  # 当前页码
        self.total_pages = 1   # 总页数
        
        # 创建视图
        self.create_view()
    
    def create_view(self):
        """创建树形视图"""
        # 创建主框架
        self.frame = ttk.LabelFrame(self.parent, text="秒链展示列表", padding="10")

        # 顶部一行：搜索框+按钮
        top_row = ttk.Frame(self.frame)
        top_row.pack(side=TOP, fill=X, pady=(0, 5))
        self.search_value = ''
        def on_search(value):
            self.search_value = value
            self.update_view()
        self.search_bar = SearchBar(top_row, on_search=on_search)
        self.search_bar.pack(side='left', fill='x', expand=True, padx=(0, 8))
        ttk.Button(top_row, text="导出秒链", command=self.export_selected_links, bootstyle="info").pack(side='left', padx=5)
        ttk.Button(top_row, text="秒链排序", command=self.sort_current_file, bootstyle="warning").pack(side='left', padx=5)

        # 树形视图区域+滚动条
        tree_container = ttk.Frame(self.frame)
        tree_container.pack(side=TOP, fill=BOTH, expand=True)
        self.tree = ttk.Treeview(tree_container, selectmode="extended")
        self.tree.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar = ttk.Scrollbar(tree_container, orient=VERTICAL, command=self.tree.yview)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.tree.configure(yscrollcommand=scrollbar.set)

        # 创建分页控制面板
        pagination_frame = ttk.Frame(self.frame)
        pagination_frame.pack(side=BOTTOM, fill=X, pady=(5, 0))
        
        # 首页按钮
        self.first_page_btn = ttk.Button(pagination_frame, text="<<", 
                                       command=self.goto_first_page,
                                       width=3)
        self.first_page_btn.pack(side=LEFT, padx=2)
        
        # 上一页按钮
        self.prev_page_btn = ttk.Button(pagination_frame, text="<", 
                                      command=self.goto_prev_page,
                                      width=3)
        self.prev_page_btn.pack(side=LEFT, padx=2)
        
        # 页码标签
        self.page_label = ttk.Label(pagination_frame, text="第 1 页 / 共 1 页")
        self.page_label.pack(side=LEFT, padx=10)
        
        # 下一页按钮
        self.next_page_btn = ttk.Button(pagination_frame, text=">", 
                                      command=self.goto_next_page,
                                      width=3)
        self.next_page_btn.pack(side=LEFT, padx=2)
        
        # 末页按钮
        self.last_page_btn = ttk.Button(pagination_frame, text=">>", 
                                      command=self.goto_last_page,
                                      width=3)
        self.last_page_btn.pack(side=LEFT, padx=2)
        
        # 每页显示数量选择
        ttk.Label(pagination_frame, text="每页显示:").pack(side=LEFT, padx=(20, 5))
        self.page_size_var = tk.StringVar(value=str(self.page_size))
        page_size_combo = ttk.Combobox(pagination_frame, 
                                     textvariable=self.page_size_var,
                                     values=["20", "50", "100", "200", "500"],
                                     width=5,
                                     state="readonly")
        page_size_combo.pack(side=LEFT)
        page_size_combo.bind("<<ComboboxSelected>>", self.on_page_size_change)
        
        # 配置列
        self.tree["columns"] = ("size", "etag")
        self.tree.column("#0", width=400, minwidth=200)  # 文件名列
        self.tree.column("size", width=100, minwidth=100)
        self.tree.column("etag", width=200, minwidth=150)
        
        # 配置表头
        self.tree.heading("#0", text="文件名", anchor=W)
        self.tree.heading("size", text="大小", anchor=W)
        self.tree.heading("etag", text="ETag", anchor=W)
        
        # 绑定排序事件
        self.tree.heading("#0", command=lambda: self.sort_tree("path"))
        self.tree.heading("size", command=lambda: self.sort_tree("size"))
        self.tree.heading("etag", command=lambda: self.sort_tree("etag"))
        
        # 创建右键菜单
        self.context_menu = tk.Menu(self.tree, tearoff=0)
        self.context_menu.add_command(label="导出选中链接", command=self.export_selected)
        self.context_menu.add_command(label="删除链接", command=self.delete_selected)
        
        # 绑定右键点击事件
        self.tree.bind("<Button-3>", self.show_context_menu)
        
        # 排序状态
        self.sort_column = None
        self.sort_reverse = False
    
    def update_view(self):
        """更新树形视图显示"""
        if not self.app.json_data or not self.app.json_data.files:
            # 清空视图并更新分页状态
            self.reset_view()
            self.update_pagination_status(0)
            return
        
        # 获取所有文件
        all_files = self.app.json_data.files
        # 搜索过滤
        if hasattr(self, 'search_value') and self.search_value:
            keyword = self.search_value.lower()
            def clean_name(s):
                if not s:
                    return ''
                # 去除年份、分辨率、编码等
                s = re.sub(r'\b(19|20)\d{2}\b', '', s, flags=re.IGNORECASE)  # 年份
                s = re.sub(r'(480p|720p|1080p|2160p|4k)', '', s, flags=re.IGNORECASE)  # 分辨率
                s = re.sub(r'(h265|h264|aac|acc|flac|mp3|hevc|x264|x265|ac3|dts|ddp|mkv|mp4|avi|wmv|mov|ts|mpeg|mpg)', '', s, flags=re.IGNORECASE)  # 编码/格式
                s = re.sub(r'\s+', ' ', s)  # 多余空格
                return s.strip()
            all_files = [f for f in all_files if keyword in clean_name(f['path'].lower()) or keyword in clean_name(f.get('name', '').lower())]
        total_files = len(all_files)
        
        # 计算总页数
        self.total_pages = max(1, (total_files + self.page_size - 1) // self.page_size)
        
        # 确保当前页码有效
        if self.current_page > self.total_pages:
            self.current_page = self.total_pages
        
        # 计算当前页的文件范围
        start_idx = (self.current_page - 1) * self.page_size
        end_idx = min(start_idx + self.page_size, total_files)
        current_page_files = all_files[start_idx:end_idx]
        
        # 清空现有项目
        self.reset_view()
        
        # 添加当前页的文件
        for file in current_page_files:
            # 格式化文件大小
            size = int(file['size'])
            if size < 1024:
                size_str = f"{size} B"
            elif size < 1024 * 1024:
                size_str = f"{size/1024:.2f} KB"
            elif size < 1024 * 1024 * 1024:
                size_str = f"{size/1024/1024:.2f} MB"
            else:
                size_str = f"{size/1024/1024/1024:.2f} GB"
            
            # 插入项目
            self.tree.insert("", "end", text=file['path'],
                           values=(size_str, file['etag']))
        
        # 更新分页状态
        self.update_pagination_status(total_files)
    
    def reset_view(self):
        """清空树形视图"""
        for item in self.tree.get_children():
            self.tree.delete(item)
    
    def clear_view(self):
        """清空视图并重置状态"""
        self.reset_view()
        self.sort_column = None
        self.sort_reverse = False
    
    def sort_tree(self, column):
        """
        对树形视图进行排序
        
        Args:
            column: 要排序的列名
        """
        # 如果点击的是当前排序列，反转排序顺序
        if self.sort_column == column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = column
            self.sort_reverse = False
        
        # 获取所有项目
        items = [(self.tree.item(item)["text"],  # 文件名
                 self.tree.item(item)["values"],  # [size_str, etag]
                 item)  # item ID
                for item in self.tree.get_children("")]
        
        # 根据列进行排序
        if column == "path":
            items.sort(key=lambda x: x[0].lower(), reverse=self.sort_reverse)
        elif column == "size":
            # 将大小字符串转换回字节数进行排序
            def parse_size(size_str):
                try:
                    num = float(size_str.split()[0])
                    unit = size_str.split()[1]
                    if unit == "KB":
                        return num * 1024
                    elif unit == "MB":
                        return num * 1024 * 1024
                    elif unit == "GB":
                        return num * 1024 * 1024 * 1024
                    return num
                except:
                    return 0
            
            items.sort(key=lambda x: parse_size(x[1][0]), reverse=self.sort_reverse)
        else:  # etag
            items.sort(key=lambda x: x[1][1].lower(), reverse=self.sort_reverse)
        
        # 重新插入排序后的项目
        for index, (text, values, item) in enumerate(items):
            self.tree.move(item, "", index)
    
    def show_context_menu(self, event):
        """显示右键菜单"""
        # 获取点击位置的项目
        item = self.tree.identify_row(event.y)
        if item:
            # 如果点击的项目未被选中，清除现有选择并选中该项目
            if item not in self.tree.selection():
                self.tree.selection_set(item)
            # 显示菜单
            self.context_menu.post(event.x_root, event.y_root)
    
    def copy_filename(self):
        """复制选中项的文件名到剪贴板"""
        selected = self.tree.selection()
        if not selected:
            return
        
        # 获取第一个选中项的文件名
        filename = self.tree.item(selected[0])["text"]
        
        # 复制到剪贴板
        self.app.root.clipboard_clear()
        self.app.root.clipboard_append(filename)
    
    def copy_full_path(self):
        """复制选中项的完整路径到剪贴板"""
        selected = self.tree.selection()
        if not selected:
            return
        
        # 获取所有选中项的路径
        paths = [self.tree.item(item)["text"] for item in selected]
        
        # 复制到剪贴板
        self.app.root.clipboard_clear()
        self.app.root.clipboard_append("\n".join(paths))
    
    def copy_etag(self):
        """复制选中项的ETag到剪贴板"""
        selected = self.tree.selection()
        if not selected:
            return
        
        # 获取第一个选中项的ETag
        etag = self.tree.item(selected[0])["values"][1]
        
        # 复制到剪贴板
        self.app.root.clipboard_clear()
        self.app.root.clipboard_append(etag)
    
    def export_selected(self):
        """导出选中项的链接"""
        # 直接调用新的导出方法
        self.export_selected_links()
    
    def get_selected_files(self):
        """
        获取选中的文件信息
        
        Returns:
            List[Dict[str, Any]]: 选中的文件信息列表
        """
        selected = self.tree.selection()
        if not selected:
            return []
        
        selected_files = []
        for item in selected:
            path = self.tree.item(item)["text"]
            file_info = self.app.json_data.get_file_by_path(path)
            if file_info:
                selected_files.append(file_info)
        
        return selected_files
    
    def delete_selected(self):
        """删除选中的链接"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请选择要删除的文件")
            return
        
        # 确认删除
        count = len(selected)
        if not messagebox.askyesno("确认删除", f"确定要删除选中的 {count} 个链接吗？"):
            return
        
        # 获取选中项的路径
        paths = [self.tree.item(item)["text"] for item in selected]
        
        # 从数据中删除
        removed = self.app.json_data.remove_files(paths)
        
        # 从树形视图中删除
        for item in selected:
            self.tree.delete(item)
        
        # 删除后不需要更新链接面板
        
        # 保存更改到文件
        if removed > 0 and self.app.current_file:
            success, error_msg = self.app.json_data.save(self.app.current_file)
            if not success:
                messagebox.showerror("保存失败", f"保存文件时出错: {error_msg}")
                return
        
        messagebox.showinfo("删除成功", f"已删除 {removed} 个链接")
    
    def export_selected_links(self):
        """导出选中的链接"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请选择要导出的文件")
            return
        
        # 获取选中的文件信息
        selected_files = []
        for item in selected:
            path = self.tree.item(item)["text"]
            file_info = self.app.json_data.get_file_by_path(path)
            if file_info:
                selected_files.append(file_info)
        
        if not selected_files:
            messagebox.showwarning("警告", "无法获取选中文件的信息")
            return
        
        # 导出链接
        link = self.app.export_selected_links(selected_files)
        
        # 复制到剪贴板
        self.app.root.clipboard_clear()
        self.app.root.clipboard_append(link)
        
        # 显示导出结果
        export_dialog = tk.Toplevel(self.app.root)
        export_dialog.title("导出链接")
        export_dialog.geometry("600x300")
        export_dialog.transient(self.app.root)
        export_dialog.grab_set()
        
        # 设置对话框居中
        export_dialog.update_idletasks()
        width = export_dialog.winfo_width()
        height = export_dialog.winfo_height()
        x = (export_dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (export_dialog.winfo_screenheight() // 2) - (height // 2)
        export_dialog.geometry(f"{width}x{height}+{x}+{y}")
        
        # 创建文本框
        frame = ttk.Frame(export_dialog, padding="10")
        frame.pack(fill=BOTH, expand=True)
        
        ttk.Label(frame, text="链接已复制到剪贴板").pack(pady=(0, 5))
        
        text = tk.Text(frame, wrap=tk.WORD)
        text.pack(fill=BOTH, expand=True, pady=(0, 10))
        text.insert(tk.END, link)
        text.config(state=tk.DISABLED)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(text, command=text.yview)
        scrollbar.pack(side=RIGHT, fill=Y)
        text.config(yscrollcommand=scrollbar.set)
        
        # 关闭按钮
        ttk.Button(frame, text="关闭", 
                  command=export_dialog.destroy,
                  bootstyle="secondary").pack(pady=(0, 5))
    
    def sort_current_file(self):
        """排序当前文件"""
        if not self.app.current_file:
            messagebox.showwarning("警告", "请先打开一个文件")
            return
        
        # 排序文件
        success, message = self.app.sort_current_file()
        
        if success:
            messagebox.showinfo("成功", message)
            # 更新视图显示
            self.update_view()
        else:
            messagebox.showerror("错误", message)
    
    def update_pagination_status(self, total_files):
        """
        更新分页状态和按钮
        
        Args:
            total_files: 文件总数
        """
        # 更新页码标签
        self.page_label.config(text=f"第 {self.current_page} 页 / 共 {self.total_pages} 页 (共 {total_files} 个文件)")
        
        # 更新按钮状态
        self.first_page_btn.config(state="normal" if self.current_page > 1 else "disabled")
        self.prev_page_btn.config(state="normal" if self.current_page > 1 else "disabled")
        self.next_page_btn.config(state="normal" if self.current_page < self.total_pages else "disabled")
        self.last_page_btn.config(state="normal" if self.current_page < self.total_pages else "disabled")
    
    def goto_first_page(self):
        """跳转到第一页"""
        if self.current_page != 1:
            self.current_page = 1
            self.update_view()
    
    def goto_prev_page(self):
        """跳转到上一页"""
        if self.current_page > 1:
            self.current_page -= 1
            self.update_view()
    
    def goto_next_page(self):
        """跳转到下一页"""
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.update_view()
    
    def goto_last_page(self):
        """跳转到最后一页"""
        if self.current_page != self.total_pages:
            self.current_page = self.total_pages
            self.update_view()
    
    def on_page_size_change(self, event):
        """
        处理每页显示数量变化
        
        Args:
            event: 事件对象
        """
        try:
            new_size = int(self.page_size_var.get())
            if new_size != self.page_size:
                self.page_size = new_size
                self.current_page = 1  # 重置到第一页
                self.update_view()
        except ValueError:
            pass
