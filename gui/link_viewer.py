"""
秒链查看器模块(弹窗版)

此模块提供了秒链解析和树状图显示功能，作为独立弹窗实现。
主要功能包括：
- 解析剪贴板中的秒链
- 在树状图中显示解析结果
- 支持选择性导出部分链接
- 分页显示功能
- 排序功能（点击列标题切换升序/降序）
- 弹窗管理功能(居中、模态、置顶)
"""

import tkinter as tk
from tkinter import ttk, messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from utils.link_parser import LinkParser
from collections import OrderedDict


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
        self.geometry("800x560")
        self.transient(parent)  # 设为父窗口的子窗口
        self.grab_set()  # 设为模态窗口
        
        self.parent = parent
        self.app = app  # 保留app引用但不强制依赖
        
        # 分页相关变量
        self.page_size = 50  # 每页显示的文件数
        self.current_page = 1  # 当前页码
        self.total_pages = 1   # 总页数
        
        # 排序状态
        self.sort_column = None
        self.sort_reverse = False
        
        # 数据存储
        self.all_links = []  # 存储所有解析的链接
        
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
        
        # 创建树形视图容器
        tree_container = ttk.Frame(self.frame)
        tree_container.pack(side=TOP, fill=BOTH, expand=True)
        
        # 树状图
        self.tree = ttk.Treeview(
            tree_container,
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
        
        # 绑定排序事件
        self.tree.heading('name', command=lambda: self.sort_tree("name"))
        self.tree.heading('size', command=lambda: self.sort_tree("size"))
        self.tree.heading('link', command=lambda: self.sort_tree("link"))
        
        # 设置列宽
        self.tree.column('name', width=200, stretch=True)  # 名称列自动扩展
        self.tree.column('size', width=100, anchor='center', stretch=False)  # 固定宽度
        self.tree.column('link', width=300, stretch=True)  # 秒链列自动扩展
        
        # 滚动条
        scrollbar = ttk.Scrollbar(
            tree_container,
            orient=VERTICAL,
            command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # 按钮框架（右侧）
        btn_frame = ttk.Frame(tree_container)
        btn_frame.pack(side=RIGHT, fill=Y, padx=(5, 0))
        
        # 导出选中按钮
        ttk.Button(
            btn_frame,
            text="导出选中",
            command=self.export_selected,
            bootstyle="success",
            width=10
        ).pack(side=TOP, pady=(0, 5))

        # 保存JSON按钮
        ttk.Button(
            btn_frame,
            text="保存JSON",
            command=self.save_json_file,
            bootstyle="primary",
            width=10
        ).pack(side=TOP, pady=(0, 5))

        # 清空按钮
        ttk.Button(
            btn_frame,
            text="清空",
            command=self.clear_viewer,
            bootstyle="danger",
            width=10
        ).pack(side=TOP)
        
        # 布局
        self.tree.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)
        
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
            
            # 处理解析的链接
            self.all_links = []
            for link in parsed_links:
                # 获取文件名
                name = link['path'].split('/')[-1] if '/' in link['path'] else link['path']
                
                # 格式化文件大小（以GB为单位）
                size = int(link['size'])
                size_str = f"{size/1024/1024/1024:.2f} GB"
                
                # 生成完整秒链格式
                file_info = {
                    'path': link['path'],
                    'size': link['size'],
                    'etag': link['etag']
                }
                full_link = LinkParser.generate_link([file_info])
                # 显示时截断秒链，保留前30个字符
                display_link = full_link[:30] + "..." if len(full_link) > 30 else full_link
                
                # 存储链接信息
                self.all_links.append({
                    'name': name,
                    'size_str': size_str,
                    'size_bytes': size,
                    'display_link': display_link,
                    'full_link': full_link
                })
            
            # 默认按名称排序
            self.sort_column = "name"
            self.sort_reverse = False
            self.current_page = 1
            
            # 更新显示
            self.update_view()
                
        except Exception as e:
            messagebox.showerror("解析错误", f"解析秒链时出错: {str(e)}")
    
    def update_view(self):
        """更新树形视图显示"""
        if not self.all_links:
            # 清空视图并更新分页状态
            self.reset_view()
            self.update_pagination_status(0)
            return
        
        # 排序数据
        sorted_links = self.sort_links(self.all_links)
        total_links = len(sorted_links)
        
        # 计算总页数
        self.total_pages = max(1, (total_links + self.page_size - 1) // self.page_size)
        
        # 确保当前页码有效
        if self.current_page > self.total_pages:
            self.current_page = self.total_pages
        
        # 计算当前页的文件范围
        start_idx = (self.current_page - 1) * self.page_size
        end_idx = min(start_idx + self.page_size, total_links)
        current_page_links = sorted_links[start_idx:end_idx]
        
        # 清空现有项目
        self.reset_view()
        
        # 添加当前页的链接
        for link in current_page_links:
            self.tree.insert(
                '',
                'end',
                values=(link['name'], link['size_str'], link['display_link']),
                tags=(link['full_link'],)  # 存储完整秒链作为tag
            )
        
        # 更新分页状态
        self.update_pagination_status(total_links)
    
    def sort_links(self, links):
        """对链接进行排序"""
        if not self.sort_column:
            return links
        
        reverse = self.sort_reverse
        
        if self.sort_column == "name":
            return sorted(links, key=lambda x: x['name'].lower(), reverse=reverse)
        elif self.sort_column == "size":
            return sorted(links, key=lambda x: x['size_bytes'], reverse=reverse)
        elif self.sort_column == "link":
            return sorted(links, key=lambda x: x['display_link'].lower(), reverse=reverse)
        
        return links
    
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
        
        # 重置到第一页
        self.current_page = 1
        
        # 更新显示
        self.update_view()
    
    def reset_view(self):
        """清空树形视图"""
        for item in self.tree.get_children():
            self.tree.delete(item)
    
    def update_pagination_status(self, total_links):
        """更新分页状态"""
        # 更新页码标签
        self.page_label.config(text=f"第 {self.current_page} 页 / 共 {self.total_pages} 页 (共 {total_links} 项)")
        
        # 更新按钮状态
        self.first_page_btn.config(state="normal" if self.current_page > 1 else "disabled")
        self.prev_page_btn.config(state="normal" if self.current_page > 1 else "disabled")
        self.next_page_btn.config(state="normal" if self.current_page < self.total_pages else "disabled")
        self.last_page_btn.config(state="normal" if self.current_page < self.total_pages else "disabled")
    
    def goto_first_page(self):
        """跳转到第一页"""
        if self.current_page > 1:
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
        if self.current_page < self.total_pages:
            self.current_page = self.total_pages
            self.update_view()
    
    def on_page_size_change(self, event):
        """处理每页显示数量变化"""
        try:
            new_size = int(self.page_size_var.get())
            if new_size != self.page_size:
                self.page_size = new_size
                self.current_page = 1  # 重置到第一页
                self.update_view()
        except ValueError:
            pass
    
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
    
    def save_json_file(self):
        import json
        from tkinter import filedialog, messagebox
        from collections import OrderedDict
        # 当前展示的所有链接
        links = self.all_links if hasattr(self, 'all_links') else []
        if not links:
            messagebox.showwarning("提示", "当前没有可保存的秒链")
            return
        # 构造标准 files 列表
        export_files = []
        for f in links:
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
        # 用 OrderedDict 保证字段顺序
        export_json = OrderedDict()
        export_json['scriptVersion'] = '1.0.1'
        export_json['exportVersion'] = '1.0'
        export_json['usesBase62EtagsInExport'] = True
        export_json['commonPath'] = ''
        export_json['totalFilesCount'] = total_files
        export_json['totalSize'] = total_size
        export_json['formattedTotalSize'] = formatted_size
        export_json['files'] = export_files
        save_path = filedialog.asksaveasfilename(
            title="保存JSON文件",
            defaultextension=".json",
            filetypes=[("JSON文件", "*.json")]
        )
        if save_path:
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(export_json, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("完成", f"已保存JSON文件到: {save_path}")
    
    def clear_viewer(self):
        """清空树状图"""
        self.all_links = []
        self.reset_view()
        self.sort_column = None
        self.sort_reverse = False
        self.current_page = 1
        self.total_pages = 1
        self.update_pagination_status(0)
    
    def on_close(self):
        """处理窗口关闭事件"""
        self.destroy()