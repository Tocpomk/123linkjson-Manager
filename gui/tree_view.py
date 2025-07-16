
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
import tkinter.font as tkFont
from gui.dir_filter_menu import DirFilterMenu


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
        self.is_reversed = False  # 记录当前是否为反转顺序
    
    def create_view(self):
        """
        创建树形视图
        """
        # 创建主框架
        self.frame = ttk.LabelFrame(self.parent, text="秒链展示列表", padding="10")

        # 顶部一行：搜索框+按钮
        top_row = ttk.Frame(self.frame)
        top_row.pack(side=TOP, fill=X, pady=(0, 0))  # 进一步缩小间距
        self.search_value = ''
        def on_search(value):
            self.search_value = value
            self.update_view()
        self.search_bar = SearchBar(top_row, on_search=on_search)
        self.search_bar.pack(side='left', fill='x', expand=True, padx=(0, 8))
        ttk.Button(top_row, text="导出秒链", command=self.export_all_links, bootstyle="info").pack(side='left', padx=5)
        ttk.Button(top_row, text="秒链排序", command=self.sort_current_file, bootstyle="warning").pack(side='left', padx=5)
        # 目录层级下拉框单独一行
        dir_row = ttk.Frame(self.frame)
        dir_row.pack(side=TOP, fill=X, pady=(6, 4))  # 增大与上方间距，底部略留空
        ttk.Label(dir_row, text="目录筛选:").pack(side='left', padx=(0, 2))
        self.dir_level_var = tk.StringVar(value="全部")
        self.dir_level_combo = ttk.Combobox(dir_row, textvariable=self.dir_level_var, width=18, state="readonly")
        self.dir_level_combo.pack(side='left')
        self.dir_level_combo.bind("<<ComboboxSelected>>", lambda e: self.update_view())
        # 移除保存JSON按钮
        # ttk.Button(top_row, text="保存JSON", command=self.save_json_file, bootstyle="primary").pack(side='left', padx=5)

        # 树形视图区域+滚动条
        tree_container = ttk.Frame(self.frame)
        tree_container.pack(side=TOP, fill=BOTH, expand=True)
        self.tree = ttk.Treeview(tree_container, columns=("name", "size", "etag"), show="headings", selectmode="extended")
        self.tree.heading("name", text="文件名", command=lambda: self.sort_tree("name"))
        self.tree.heading("size", text="文件大小", command=lambda: self.sort_tree("size"))
        self.tree.heading("etag", text="秒链", command=lambda: self.sort_tree("etag"))
        self.tree.column("name", width=320, minwidth=180, anchor="w")      # 文件名左对齐，宽度更紧凑
        self.tree.column("size", width=100, minwidth=80, anchor="e")      # 文件大小右对齐，宽度更紧凑
        self.tree.column("etag", width=260, minwidth=180, anchor="center") # 秒链居中，宽度更紧凑
        # 设置字体和行高，让表格更紧凑
        style = ttk.Style()
        style.configure("Treeview", font=("微软雅黑", 9))
        style.configure("Treeview.Heading", font=("微软雅黑", 9))
        # 鼠标拖动多选支持
        self.tree.bind('<Button-1>', self.on_tree_mouse_down)
        self.tree.bind('<B1-Motion>', self.on_tree_mouse_drag)
        self.tree.bind('<ButtonRelease-1>', self.on_tree_mouse_up)
        self.tree.bind('<Button-3>', self.show_context_menu)
        scrollbar = ttk.Scrollbar(tree_container, orient=VERTICAL, command=self.tree.yview)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=LEFT, fill=BOTH, expand=True)

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
        
        # 配置列（删除多余的列配置，避免覆盖三列设置）
        # self.tree["columns"] = ("size", "etag")
        # self.tree.column("size", width=100, minwidth=100)
        # self.tree.column("etag", width=200, minwidth=150)
        # self.tree.heading("size", text="大小", anchor=W)
        # self.tree.heading("etag", text="ETag", anchor=W)
        
        # 绑定排序事件
        # self.tree.heading("#0", command=lambda: self.sort_tree("path")) # This line is removed as per the new_code
        # self.tree.heading("size", command=lambda: self.sort_tree("size")) # This line is removed as per the new_code
        # self.tree.heading("etag", command=lambda: self.sort_tree("etag")) # This line is removed as per the new_code
        
        # 创建右键菜单
        self.context_menu = tk.Menu(self.tree, tearoff=0)
        self.context_menu.add_command(label="导出选中链接", command=self.export_selected)
        self.context_menu.add_command(label="删除链接", command=self.delete_selected)
        
        # 绑定右键点击事件
        # self.tree.bind("<Button-3>", self.show_context_menu) # This line is removed as per the new_code
        
        # 排序状态
        self.sort_column = None
        self.sort_reverse = False
    
    def update_view(self):
        """
        更新树形视图显示
        """
        if not self.app.json_data or not self.app.json_data.files:
            # 清空视图并更新分页状态
            self.reset_view()
            self.update_pagination_status(0)
            return
        # 获取所有文件（保持原始顺序，不排序）
        all_files = self.app.json_data.files
        # 目录下拉菜单自动生成（只更新选项，不重建控件）
        dir_menu = DirFilterMenu(self.app.json_data.files)
        menu_options = dir_menu.get_menu_options()
        combo_values = []
        value_to_label = {}
        for opt in menu_options:
            combo_values.append(opt['label'])
            value_to_label[opt['label']] = opt['value']
            if 'children' in opt:
                for child in opt['children']:
                    combo_values.append(f"{opt['label']}→{child['label']}")
                    value_to_label[f"{opt['label']}→{child['label']}"] = child['value']
        # 只更新下拉框选项，不重建控件
        self.dir_level_combo['values'] = combo_values
        # 保持选中项有效
        if self.dir_level_var.get() not in combo_values:
            self.dir_level_var.set(combo_values[0] if combo_values else "全部")
        # 过滤文件（只有当目录筛选不是'全部'时才过滤）
        select_label = self.dir_level_var.get()
        select_value = value_to_label.get(select_label, '全部')
        if select_value != '全部':
            all_files = dir_menu.filter_files(select_value)
        # 目录筛选后再进行搜索过滤
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
        self.current_page_files = current_page_files  # 供全选用
        # 清空现有项目
        self.reset_view()
        # 添加当前页的文件
        for file in current_page_files:
            name = file.get('name', file['path'])
            size = int(file['size']) if 'size' in file else 0
            if size < 1024:
                size_str = f"{size} B"
            elif size < 1024 * 1024:
                size_str = f"{size/1024:.2f} KB"
            elif size < 1024 * 1024 * 1024:
                size_str = f"{size/1024/1024:.2f} MB"
            else:
                size_str = f"{size/1024/1024/1024:.2f} GB"
            etag = file.get('etag', '')
            self.tree.insert("", "end", iid=file['path'], values=(name, size_str, etag))
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
            column: 要排序的列名（name/size/etag）
        """
        if column == "name":
            self.is_reversed = not self.is_reversed
            if self.is_reversed:
                self.current_page_files = list(reversed(self.current_page_files))
            else:
                # 重新恢复初始顺序（即 update_view 生成的顺序）
                # 重新调用 update_view 保证顺序和分页一致
                self.update_view()
                return
            self.reset_view()
            for file in self.current_page_files:
                name = file.get('name', file['path'])
                size = int(file['size']) if 'size' in file else 0
                if size < 1024:
                    size_str = f"{size} B"
                elif size < 1024 * 1024:
                    size_str = f"{size/1024:.2f} KB"
                elif size < 1024 * 1024 * 1024:
                    size_str = f"{size/1024/1024:.2f} MB"
                else:
                    size_str = f"{size/1024/1024/1024:.2f} GB"
                etag = file.get('etag', '')
                self.tree.insert("", "end", iid=file['path'], values=(name, size_str, etag))
            return
        # 其他列保持原有排序逻辑
        # 如果点击的是当前排序列，反转排序顺序
        if self.sort_column == column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = column
            self.sort_reverse = False
        # 获取所有项目
        items = [(self.tree.item(item)["values"], item) for item in self.tree.get_children("")]
        # 根据列进行排序
        if column == "name":
            items.sort(key=lambda x: natural_key(x[0][0]), reverse=self.sort_reverse)
        elif column == "size":
            def parse_size(size_str):
                try:
                    num, unit = size_str.split()
                    num = float(num)
                    if unit == "KB":
                        return num * 1024
                    elif unit == "MB":
                        return num * 1024 * 1024
                    elif unit == "GB":
                        return num * 1024 * 1024 * 1024
                    return num
                except:
                    return 0
            items.sort(key=lambda x: parse_size(x[0][1]), reverse=self.sort_reverse)
        elif column == "etag":
            items.sort(key=lambda x: x[0][2], reverse=self.sort_reverse)
        # 重新插入排序后的项目
        for index, (values, item) in enumerate(items):
            self.tree.move(item, "", index)
    
    def show_context_menu(self, event):
        """显示右键菜单"""
        # 获取点击位置的项目
        item = self.tree.identify_row(event.y)
        if item:
            # 如果当前未多选，才切换选中项
            if item not in self.tree.selection():
                self.tree.selection_set(item)
            # 显示菜单
            self.context_menu.post(event.x_root, event.y_root)
    
    def copy_filename(self):
        """复制选中项的文件名到剪贴板"""
        selected = self.tree.selection()
        if not selected:
            return
        # 获取所有选中项的文件名
        filenames = []
        for item in selected:
            # 通过iid（即file['path']）找到文件对象
            file = self.app.json_data.get_file_by_path(item)
            if file:
                filenames.append(file.get('name', file['path']))
        self.app.root.clipboard_clear()
        self.app.root.clipboard_append("\n".join(filenames))
    
    def copy_full_path(self):
        """复制选中项的完整路径到剪贴板"""
        selected = self.tree.selection()
        if not selected:
            return
        # 获取所有选中项的路径
        paths = [item for item in selected]  # iid就是path
        self.app.root.clipboard_clear()
        self.app.root.clipboard_append("\n".join(paths))
    
    def copy_etag(self):
        """复制选中项的ETag到剪贴板"""
        selected = self.tree.selection()
        if not selected:
            return
        etags = []
        for item in selected:
            file = self.app.json_data.get_file_by_path(item)
            if file:
                etags.append(file.get('etag', ''))
        self.app.root.clipboard_clear()
        self.app.root.clipboard_append("\n".join(etags))
    
    def export_selected(self):
        """导出选中项的链接"""
        selected = self.tree.selection()
        if not selected:
            return
        files = []
        for item in selected:
            file = self.app.json_data.get_file_by_path(item)
            if file:
                files.append(file)
        if not files:
            return
        # 生成秒链（如有自定义生成逻辑可调用 app.export_selected_links）
        from utils.link_parser import LinkParser
        link = LinkParser.generate_link(files)
        self.app.root.clipboard_clear()
        self.app.root.clipboard_append(link)
        export_dialog = tk.Toplevel(self.app.root)
        export_dialog.title("导出链接")
        export_dialog.geometry("600x300")
        export_dialog.transient(self.app.root)
        export_dialog.grab_set()
        export_dialog.update_idletasks()
        width = export_dialog.winfo_width()
        height = export_dialog.winfo_height()
        x = (export_dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (export_dialog.winfo_screenheight() // 2) - (height // 2)
        export_dialog.geometry(f"{width}x{height}+{x}+{y}")
        frame = ttk.Frame(export_dialog, padding="10")
        frame.pack(fill=BOTH, expand=True)
        ttk.Label(frame, text="链接已复制到剪贴板").pack(pady=(0, 5))
        text = tk.Text(frame, wrap=tk.WORD)
        text.pack(fill=BOTH, expand=True, pady=(0, 10))
        text.insert(tk.END, link)
        text.config(state=tk.DISABLED)
        scrollbar = ttk.Scrollbar(text, command=text.yview)
        scrollbar.pack(side=RIGHT, fill=Y)
        text.config(yscrollcommand=scrollbar.set)
        ttk.Button(frame, text="关闭", command=export_dialog.destroy, bootstyle="secondary").pack(pady=(0, 5))
    
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
            path = item  # 直接用iid作为path
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
        count = len(selected)
        if not messagebox.askyesno("确认删除", f"确定要删除选中的 {count} 个链接吗？"):
            return
        # 获取选中项的路径
        paths = [item for item in selected]  # iid就是path
        removed = self.app.json_data.remove_files(paths)
        for item in selected:
            self.tree.delete(item)
        if removed > 0 and self.app.current_file:
            success, error_msg = self.app.json_data.save(self.app.current_file)
            if not success:
                messagebox.showerror("保存失败", f"保存文件时出错: {error_msg}")
                return
        messagebox.showinfo("删除成功", f"已删除 {removed} 个链接")
    
    def export_all_links(self):
        """
        导出选中的秒链（与右键菜单一致）
        """
        selected_files = self.get_selected_files()
        if not selected_files:
            messagebox.showwarning("警告", "请先选中要导出的秒链")
            return
        link = self.app.export_selected_links(selected_files)
        self.app.root.clipboard_clear()
        self.app.root.clipboard_append(link)
        export_dialog = tk.Toplevel(self.app.root)
        export_dialog.title("导出链接")
        export_dialog.geometry("600x300")
        export_dialog.transient(self.app.root)
        export_dialog.grab_set()
        export_dialog.update_idletasks()
        width = export_dialog.winfo_width()
        height = export_dialog.winfo_height()
        x = (export_dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (export_dialog.winfo_screenheight() // 2) - (height // 2)
        export_dialog.geometry(f"{width}x{height}+{x}+{y}")
        frame = ttk.Frame(export_dialog, padding="10")
        frame.pack(fill=BOTH, expand=True)
        ttk.Label(frame, text="链接已复制到剪贴板").pack(pady=(0, 5))
        text = tk.Text(frame, wrap=tk.WORD)
        text.pack(fill=BOTH, expand=True, pady=(0, 10))
        text.insert(tk.END, link)
        text.config(state=tk.DISABLED)
        scrollbar = ttk.Scrollbar(text, command=text.yview)
        scrollbar.pack(side=RIGHT, fill=Y)
        text.config(yscrollcommand=scrollbar.set)
        ttk.Button(frame, text="关闭", command=export_dialog.destroy, bootstyle="secondary").pack(pady=(0, 5))
    
    def sort_current_file(self):
        """
        秒链排序按钮：排序当前文件列表，并自动保存
        """
        if not self.app.current_file:
            messagebox.showwarning("警告", "请先打开一个文件")
            return
        # 排序规则：不带子目录的在前，带子目录的在后，各自自然顺序
        files = self.app.json_data.files
        files.sort(key=lambda f: ("/" in f["path"], natural_key(f.get('name', f['path']))))
        self.app.json_data.files = files
        # 自动保存
        success, error_msg = self.app.json_data.save(self.app.current_file)
        self.update_view()
        if success:
            messagebox.showinfo("排序完成", "已按规则排序并保存！")
        else:
            messagebox.showerror("保存失败", f"排序已完成，但保存文件时出错: {error_msg}")
    
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

    def save_json_file(self):
        import json
        from tkinter import filedialog, messagebox
        # 获取当前过滤后的文件列表
        all_files = self.app.json_data.files if self.app.json_data and self.app.json_data.files else []
        if hasattr(self, 'search_value') and self.search_value:
            keyword = self.search_value.lower()
            def clean_name(s):
                if not s:
                    return ''
                import re
                s = re.sub(r'\b(19|20)\d{2}\b', '', s, flags=re.IGNORECASE)
                s = re.sub(r'(480p|720p|1080p|2160p|4k)', '', s, flags=re.IGNORECASE)
                s = re.sub(r'(h265|h264|aac|acc|flac|mp3|hevc|x264|x265|ac3|dts|ddp|mkv|mp4|avi|wmv|mov|ts|mpeg|mpg)', '', s, flags=re.IGNORECASE)
                s = re.sub(r'\s+', ' ', s)
                return s.strip()
            all_files = [f for f in all_files if keyword in clean_name(f['path'].lower()) or keyword in clean_name(f.get('name', '').lower())]
        if not all_files:
            messagebox.showwarning("提示", "当前没有可保存的秒链文件")
            return
        # 构造导出JSON，files只包含标准字段，size/etag自动提取
        export_files = []
        for f in all_files:
            # 提取size
            size = 0
            if 'size_bytes' in f:
                size = int(f['size_bytes'])
            elif 'size' in f:
                try:
                    size = int(f['size'])
                except Exception:
                    size = 0
            elif 'size_str' in f:
                s = f['size_str'].strip().upper()
                if s.endswith('GB'):
                    size = int(float(s[:-2].strip()) * 1024 * 1024 * 1024)
                elif s.endswith('MB'):
                    size = int(float(s[:-2].strip()) * 1024 * 1024)
                elif s.endswith('KB'):
                    size = int(float(s[:-2].strip()) * 1024)
                elif s.endswith('B'):
                    size = int(float(s[:-1].strip()))
            # 提取etag
            etag = f.get('etag', '')
            if not etag and 'full_link' in f:
                parts = f['full_link'].split('#')
                if len(parts) >= 2:
                    etag = parts[0].split('$')[-1]
            # 只保留标准字段
            export_files.append({
                'path': str(f.get('path', f.get('name', ''))).split('\n')[0],
                'size': str(size),
                'etag': etag
            })
        # 统计字段
        total_files = len(export_files)
        total_size = sum(int(f['size']) for f in export_files)
        if total_size < 1024:
            formatted_size = f"{total_size} B"
        elif total_size < 1024 * 1024:
            formatted_size = f"{total_size/1024:.2f} KB"
        elif total_size < 1024 * 1024 * 1024:
            formatted_size = f"{total_size/1024/1024:.2f} MB"
        else:
            formatted_size = f"{total_size/1024/1024/1024:.2f} GB"
        # 头部字段顺序与标准一致，自动补全
        export_json = {
            'scriptVersion': self.app.json_data.data.get('scriptVersion', '1.0.1') if hasattr(self.app.json_data, 'data') else '1.0.1',
            'exportVersion': self.app.json_data.data.get('exportVersion', '1.0') if hasattr(self.app.json_data, 'data') else '1.0',
            'usesBase62EtagsInExport': self.app.json_data.data.get('usesBase62EtagsInExport', True) if hasattr(self.app.json_data, 'data') else True,
            'commonPath': self.app.json_data.data.get('commonPath', '') if hasattr(self.app.json_data, 'data') else '',
            'totalFilesCount': total_files,
            'totalSize': total_size,
            'formattedTotalSize': formatted_size,
            'files': export_files
        }
        # 保存对话框
        save_path = filedialog.asksaveasfilename(
            title="保存JSON文件",
            defaultextension=".json",
            filetypes=[("JSON文件", "*.json")]
        )
        if save_path:
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(export_json, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("完成", f"已保存JSON文件到: {save_path}")

    def on_tree_mouse_down(self, event):
        rowid = self.tree.identify_row(event.y)
        self._drag_selecting = True  # 无论点到哪都激活拖动
        if rowid:
            # 如果未按Ctrl/Shift，清空原有选择
            if not (event.state & 0x0004 or event.state & 0x0001):
                self.tree.selection_set(rowid)
            else:
                self.tree.selection_add(rowid)
            self._last_drag_row = rowid
        else:
            self._last_drag_row = None

    def on_tree_mouse_drag(self, event):
        if not getattr(self, '_drag_selecting', False):
            return
        rowid = self.tree.identify_row(event.y)
        if rowid and rowid != getattr(self, '_last_drag_row', None):
            self.tree.selection_add(rowid)
            self._last_drag_row = rowid

    def on_tree_mouse_up(self, event):
        self._drag_selecting = False
        self._last_drag_row = None

import re
def natural_key(s):
    # 提取字符串中的数字用于自然排序
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]