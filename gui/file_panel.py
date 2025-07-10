"""
文件面板模块

此模块提供了应用程序左侧的文件列表面板。
主要功能包括：
- 显示JSON文件列表
- 添加、删除和重命名文件
- 处理文件拖放
- 文件排序
"""

import tkinter as tk
import os
from tkinter import filedialog, messagebox
from tkinterdnd2 import DND_FILES
import ttkbootstrap as ttk
from ttkbootstrap.constants import *


class FilePanel:
    """文件列表面板类"""
    
    def __init__(self, parent, app):
        """
        初始化文件面板
        
        Args:
            parent: 父级窗口部件
            app: 应用程序实例
        """
        self.parent = parent
        self.app = app
        
        # 数据存储
        self.files_list = []  # 存储文件名列表
        self.file_paths = {}  # 存储文件名到完整路径的映射
        
        # 重命名相关
        self.rename_entry = None  # 用于重命名的Entry控件
        self.rename_frame = None  # 重命名框架
        self.rename_index = None  # 当前正在重命名的索引
        
        # 创建面板
        self.create_panel()
    
    def create_panel(self):
        """创建文件面板"""
        # 创建主框架
        self.frame = ttk.LabelFrame(self.parent, text="JSON文件", padding="10")
        
        # 创建支持拖放的Listbox，设置为多选模式
        self.file_listbox = tk.Listbox(self.frame, width=30, selectmode=tk.EXTENDED)
        self.file_listbox.pack(fill=Y, expand=True)
        self.file_listbox.bind('<<ListboxSelect>>', self.on_file_select)
        self.file_listbox.bind('<Double-Button-1>', self.start_rename)
        self.file_listbox.bind('<Return>', self.finish_rename)
        self.file_listbox.bind('<Escape>', lambda e: self.cancel_rename())
        
        # 配置拖放功能
        self.file_listbox.drop_target_register(DND_FILES)
        self.file_listbox.dnd_bind('<<Drop>>', self.on_drop)
        
        # 创建文件列表右键菜单
        self.file_menu = tk.Menu(self.file_listbox, tearoff=0)
        self.file_menu.add_command(label="列表删除", command=self.remove_selected_files)
        self.file_menu.add_command(label="重命名", command=self.start_rename)
        self.file_menu.add_command(label="删除文件", command=self.delete_selected_files)
        
        # 绑定右键点击事件
        self.file_listbox.bind("<Button-3>", self.show_file_menu)
        
        # 文件操作按钮框架
        file_ops_frame = ttk.Frame(self.frame)
        file_ops_frame.pack(fill=X, pady=5)
        
        # 排序按钮框架（左侧）
        # sort_frame = ttk.Frame(file_ops_frame)
        # sort_frame.pack(side=LEFT, fill=X, expand=True)
        
        # 排序按钮
        # ttk.Button(sort_frame, text="↑", width=3, 
        #           command=lambda: self.sort_files(reverse=False),
        #           bootstyle="primary-outline").pack(side=LEFT, padx=2)
        # ttk.Button(sort_frame, text="↓", width=3,
        #           command=lambda: self.sort_files(reverse=True),
        #           bootstyle="primary-outline").pack(side=LEFT, padx=2)
        
        # 按钮框架（右侧）
        btn_frame = ttk.Frame(self.frame)
        btn_frame.pack(fill=X, pady=5, padx=5)

        # 2*2网格布局按钮（不含推送列表）
        btn_add = ttk.Button(btn_frame, text="添加文件", command=self.add_files, bootstyle="primary")
        btn_compare = ttk.Button(btn_frame, text="文件对比", command=self.compare_files, bootstyle="warning")
        btn_split = ttk.Button(btn_frame, text="拆分文件", command=self.split_files, bootstyle="info")
        btn_merge = ttk.Button(btn_frame, text="合并文件", command=self.merge_files, bootstyle="primary")

        btn_add.grid(row=0, column=0, sticky="ew", padx=2, pady=2, ipady=3)
        btn_compare.grid(row=0, column=1, sticky="ew", padx=2, pady=2, ipady=3)
        btn_split.grid(row=1, column=0, sticky="ew", padx=2, pady=2, ipady=3)
        btn_merge.grid(row=1, column=1, sticky="ew", padx=2, pady=2, ipady=3)

        btn_frame.columnconfigure(0, weight=1)
        btn_frame.columnconfigure(1, weight=1)
    
    def add_files(self):
        """通过文件对话框添加JSON文件"""
        files = filedialog.askopenfilenames(
            title="选择JSON文件",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if files:
            self.add_json_files(files)
    
    def on_drop(self, event):
        """处理文件拖放事件"""
        files = self.app.root.tk.splitlist(event.data)
        json_files = [f for f in files if f.lower().endswith('.json')]
        if json_files:
            self.add_json_files(json_files)
        elif files:
            messagebox.showwarning("警告", "只能添加JSON文件")
    
    def add_json_files(self, files):
        """
        添加JSON文件到列表
        
        Args:
            files: JSON文件路径列表
        """
        for filepath in files:
            # 获取文件名
            filename = os.path.basename(filepath)
            # 检查文件是否已在列表中
            if filename not in self.files_list:
                self.files_list.append(filename)
                self.file_paths[filename] = filepath  # 保存文件路径映射
                # 如果是第一个文件，自动加载它
                if len(self.files_list) == 1:
                    self.app.load_json_file(filepath)
        
        # 更新显示
        self.update_display()
    
    def add_file_to_list(self, filename, filepath):
        """
        添加单个文件到列表
        
        Args:
            filename: 文件名
            filepath: 文件路径
        """
        if filename not in self.files_list:
            self.files_list.append(filename)
            self.file_paths[filename] = filepath
            self.update_display()
    
    def on_file_select(self, event):
        """当选择JSON文件时触发"""
        selection = self.file_listbox.curselection()
        if not selection:
            return
            
        filename = self.file_listbox.get(selection[0])
        if filename in self.file_paths:
            filepath = self.file_paths[filename]
            # 检查文件是否存在
            if not os.path.exists(filepath):
                messagebox.showwarning("警告", f"文件不存在: {filepath}\n将从列表中移除")
                self.remove_file_from_list(filename)
                return
            
            self.app.load_json_file(filepath)
    
    def update_display(self):
        """更新文件列表显示"""
        # 清空当前列表
        self.file_listbox.delete(0, tk.END)
        
        # 显示所有文件
        for filename in self.files_list:
            self.file_listbox.insert(tk.END, filename)
    
    def sort_files(self, reverse=False):
        """
        排序文件列表
        
        Args:
            reverse: 是否逆序排序
        """
        self.files_list.sort(reverse=reverse)
        self.update_display()
    
    def show_file_menu(self, event):
        """显示文件列表的右键菜单"""
        # 获取点击位置对应的项目索引
        index = self.file_listbox.nearest(event.y)
        if index >= 0:
            # 如果点击位置有项目，确保它被选中
            if index not in self.file_listbox.curselection():
                self.file_listbox.selection_clear(0, tk.END)
                self.file_listbox.selection_set(index)
            # 显示菜单
            self.file_menu.post(event.x_root, event.y_root)
    
    def remove_selected_files(self):
        """从列表中删除选中的文件（不删除实际文件）"""
        selected = self.file_listbox.curselection()
        if not selected:
            messagebox.showwarning("警告", "请选择要删除的文件")
            return
        
        # 获取选中的文件名
        selected_files = [self.file_listbox.get(idx) for idx in selected]
        
        # 从文件列表中删除选中的文件
        for filename in selected_files:
            if filename in self.files_list:
                self.files_list.remove(filename)
            if filename in self.file_paths:
                del self.file_paths[filename]
        
        # 更新显示
        self.update_display()
        
        # 如果当前没有文件，清空树形视图
        if not self.files_list:
            self.app.json_data = None
            self.app.current_file = None
            self.app.tree_view.clear_view()
    
    def delete_selected_files(self):
        """删除选中的文件（从磁盘上删除）"""
        selected = self.file_listbox.curselection()
        if not selected:
            messagebox.showwarning("警告", "请选择要删除的文件")
            return
        
        # 获取选中的文件名
        selected_files = [self.file_listbox.get(idx) for idx in selected]
        
        # 确认删除
        if len(selected_files) == 1:
            confirm = messagebox.askyesno("确认删除", f"确定要删除文件 {selected_files[0]}？\n此操作将从磁盘上永久删除该文件。")
        else:
            confirm = messagebox.askyesno("确认删除", f"确定要删除选中的 {len(selected_files)} 个文件？\n此操作将从磁盘上永久删除这些文件。")
        
        if not confirm:
            return
        
        deleted_count = 0
        for filename in selected_files:
            if filename in self.file_paths:
                filepath = self.file_paths[filename]
                try:
                    # 删除文件
                    if os.path.exists(filepath):
                        os.remove(filepath)
                        deleted_count += 1
                    
                    # 从列表中移除
                    if filename in self.files_list:
                        self.files_list.remove(filename)
                        del self.file_paths[filename]
                except Exception as e:
                    messagebox.showerror("错误", f"删除文件 {filename} 时出错: {str(e)}")
        
        # 更新显示
        self.update_display()
        
        # 如果当前没有文件，清空树形视图
        if not self.files_list:
            self.app.json_data = None
            self.app.current_file = None
            self.app.tree_view.clear_view()
        
        messagebox.showinfo("成功", f"已删除 {deleted_count} 个文件")
    
    def start_rename(self, event=None):
        """开始重命名文件"""
        selected = self.file_listbox.curselection()
        if not selected or len(selected) != 1:
            return
        
        index = selected[0]
        filename = self.file_listbox.get(index)
        
        # 检查文件是否存在
        if filename in self.file_paths:
            filepath = self.file_paths[filename]
            if not os.path.exists(filepath):
                messagebox.showwarning("警告", f"文件不存在: {filepath}\n将从列表中移除")
                self.remove_file_from_list(filename)
                return
        
        # 创建Entry控件用于编辑
        x, y, width, height = self.file_listbox.bbox(index)
        
        # 创建一个框架来容纳Entry
        self.rename_frame = tk.Frame(self.file_listbox, bd=0, highlightthickness=1)
        self.rename_frame.place(x=0, y=y, width=width, height=height)
        
        # 创建Entry控件
        self.rename_entry = tk.Entry(self.rename_frame, bd=0)
        self.rename_entry.insert(0, filename)
        self.rename_entry.select_range(0, len(filename))
        self.rename_entry.pack(fill=tk.BOTH, expand=True)
        self.rename_entry.focus_set()
        
        # 绑定事件
        self.rename_entry.bind("<Return>", self.finish_rename)
        self.rename_entry.bind("<Escape>", lambda e: self.cancel_rename())
        self.rename_entry.bind("<FocusOut>", self.finish_rename)
        
        # 保存当前正在重命名的索引
        self.rename_index = index
    
    def finish_rename(self, event=None):
        """完成重命名"""
        if self.rename_entry is None or self.rename_index is None:
            return
        
        try:
            old_filename = self.file_listbox.get(self.rename_index)
            new_filename = self.rename_entry.get().strip()
            
            # 检查新文件名是否为空
            if not new_filename:
                messagebox.showwarning("警告", "文件名不能为空")
                self.cancel_rename()
                return
            
            # 检查新文件名是否已存在
            if new_filename != old_filename and new_filename in self.files_list:
                messagebox.showwarning("警告", f"文件名 {new_filename} 已存在")
                self.cancel_rename()
                return
            
            # 检查旧文件是否存在映射
            if old_filename not in self.file_paths:
                messagebox.showerror("错误", f"无法找到文件 {old_filename} 的路径映射")
                self.cancel_rename()
                return
                
            # 获取旧文件路径
            old_filepath = self.file_paths[old_filename]
            
            # 检查文件是否存在
            if not os.path.exists(old_filepath):
                messagebox.showwarning("警告", f"文件不存在: {old_filepath}\n将从列表中移除")
                self.remove_file_from_list(old_filename)
                self.cancel_rename()
                return
            
            # 构建新文件路径
            new_filepath = os.path.join(os.path.dirname(old_filepath), new_filename)
            
            # 原子性操作：先尝试重命名文件
            try:
                os.rename(old_filepath, new_filepath)
            except Exception as e:
                messagebox.showerror("错误", f"重命名文件时出错: {str(e)}")
                self.cancel_rename()
                return
            
            # 更新文件列表和映射
            self.files_list[self.rename_index] = new_filename
            self.file_paths[new_filename] = new_filepath
            del self.file_paths[old_filename]
            
            # 更新显示
            self.update_display()
            
            # 如果当前加载的是这个文件，更新当前文件路径
            if self.app.current_file == old_filepath:
                self.app.current_file = new_filepath
            
        finally:
            self.cancel_rename()
    
    def cancel_rename(self):
        """取消重命名"""
        if self.rename_frame:
            self.rename_frame.destroy()
            self.rename_frame = None
            self.rename_entry = None
            self.rename_index = None
    
    def remove_file_from_list(self, filename):
        """
        从列表中移除文件
        
        Args:
            filename: 要移除的文件名
        """
        if filename in self.files_list:
            self.files_list.remove(filename)
        if filename in self.file_paths:
            del self.file_paths[filename]
        self.update_display()
    
    def check_all_files_exist(self):
        """检查所有文件是否存在，移除不存在的文件"""
        files_to_remove = []
        
        for filename in self.files_list:
            filepath = self.file_paths.get(filename)
            if filepath and not os.path.exists(filepath):
                files_to_remove.append(filename)
        
        if files_to_remove:
            for filename in files_to_remove:
                self.remove_file_from_list(filename)
            
            if self.files_list:
                # 如果还有文件，加载第一个
                filename = self.files_list[0]
                filepath = self.file_paths[filename]
                self.app.load_json_file(filepath)
            else:
                # 如果没有文件了，清空树形视图
                self.app.json_data = None
                self.app.current_file = None
                self.app.tree_view.clear_view()
    
    def merge_files(self):
        """合并选中的文件"""
        selected = self.file_listbox.curselection()
        if not selected or len(selected) < 2:
            messagebox.showwarning("警告", "请选择至少两个文件进行合并")
            return
        
        # 获取选中的文件路径
        filepaths = []
        for idx in selected:
            filename = self.file_listbox.get(idx)
            if filename in self.file_paths:
                filepath = self.file_paths[filename]
                if os.path.exists(filepath):
                    filepaths.append(filepath)
        
        if len(filepaths) < 2:
            messagebox.showwarning("警告", "至少需要两个有效的文件才能合并")
            return
        
        # 确认合并
        confirm = messagebox.askyesno("确认合并", f"确定要合并选中的 {len(filepaths)} 个文件？")
        if not confirm:
            return
        
        # 执行合并
        success, message, merged_filename = self.app.merge_files(filepaths)
        
        if success:
            # 添加合并后的文件到列表
            self.add_file_to_list(os.path.basename(merged_filename), merged_filename)
            messagebox.showinfo("成功", message)
        else:
            messagebox.showerror("错误", message)
    
    def compare_files(self):
        """对比选中的两个文件"""
        selected = self.file_listbox.curselection()
        if not selected or len(selected) != 2:
            messagebox.showwarning("警告", "请选择恰好两个文件进行对比")
            return
        
        # 获取选中的文件路径
        filepaths = []
        filenames = []
        for idx in selected:
            filename = self.file_listbox.get(idx)
            if filename in self.file_paths:
                filepath = self.file_paths[filename]
                if os.path.exists(filepath):
                    filepaths.append(filepath)
                    filenames.append(filename)
        
        if len(filepaths) != 2:
            messagebox.showwarning("警告", "需要恰好两个有效的文件才能对比")
            return
        
        # 创建对比选择对话框
        self.show_compare_dialog(filepaths, filenames)
    
    def show_compare_dialog(self, filepaths, filenames):
        """显示对比选择对话框"""
        # 创建对话框
        dialog = tk.Toplevel(self.app.root)
        dialog.title("文件对比选择")
        dialog.geometry("400x200")
        dialog.transient(self.app.root)
        dialog.grab_set()
        
        # 居中显示
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # 创建主框架
        main_frame = ttk.Frame(dialog, padding="20")
        main_frame.pack(fill=BOTH, expand=True)
        
        # 标题
        ttk.Label(main_frame, text="选择对比类型", font=("", 12, "bold")).pack(pady=(0, 20))
        
        # 显示选中的文件
        ttk.Label(main_frame, text=f"文件1: {filenames[0]}", font=("", 10)).pack(anchor=W, pady=2)
        ttk.Label(main_frame, text=f"文件2: {filenames[1]}", font=("", 10)).pack(anchor=W, pady=2)
        
        # 按钮框架
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=20)
        
        # 相同秒链按钮
        ttk.Button(
            btn_frame,
            text="相同秒链",
            command=lambda: self.perform_compare(filepaths, "same", dialog),
            bootstyle="success",
            width=12
        ).pack(side=LEFT, padx=(0, 10))
        
        # 不同秒链按钮
        ttk.Button(
            btn_frame,
            text="不同秒链",
            command=lambda: self.perform_compare(filepaths, "different", dialog),
            bootstyle="warning",
            width=12
        ).pack(side=LEFT, padx=(0, 10))
        
        # 取消按钮
        ttk.Button(
            btn_frame,
            text="取消",
            command=dialog.destroy,
            bootstyle="secondary",
            width=12
        ).pack(side=LEFT)
    
    def perform_compare(self, filepaths, compare_type, dialog):
        """执行文件对比"""
        dialog.destroy()
        
        try:
            # 加载两个文件的数据
            from models.json_data import JsonData
            
            data1 = JsonData()
            success1, error1 = data1.load(filepaths[0])
            if not success1:
                messagebox.showerror("错误", f"无法加载文件1: {error1}")
                return
            
            data2 = JsonData()
            success2, error2 = data2.load(filepaths[1])
            if not success2:
                messagebox.showerror("错误", f"无法加载文件2: {error2}")
                return
            
            # 获取文件中的秒链
            files1 = data1.files if data1.files else []
            files2 = data2.files if data2.files else []
            
            # 创建秒链集合
            links1 = set()
            links2 = set()
            
            for file in files1:
                # 生成完整秒链
                from utils.link_parser import LinkParser
                full_link = LinkParser.generate_link([file])
                links1.add(full_link)
            
            for file in files2:
                # 生成完整秒链
                from utils.link_parser import LinkParser
                full_link = LinkParser.generate_link([file])
                links2.add(full_link)
            
            # 根据对比类型获取结果
            if compare_type == "same":
                # 相同秒链（交集）
                result_links = links1.intersection(links2)
                title = "相同秒链"
            else:
                # 不同秒链（对称差集）
                result_links = links1.symmetric_difference(links2)
                title = "不同秒链"
            
            # 显示结果
            if result_links:
                # 创建秒链查看器显示结果
                from gui.link_viewer import LinkViewer
                viewer = LinkViewer(self.app.root, self.app)
                viewer.title(f"文件对比结果 - {title}")
                
                # 将秒链转换为文本格式
                link_text = "\n".join(result_links)
                viewer.parse_and_show_links(link_text)
                
                messagebox.showinfo("对比完成", f"找到 {len(result_links)} 个{title}")
            else:
                messagebox.showinfo("对比完成", f"没有找到{title}")
                
        except Exception as e:
            messagebox.showerror("错误", f"执行文件对比时出错: {str(e)}")

    def split_files(self):
        """拆分文件功能入口，弹窗设置和预览"""
        # 获取当前选中文件
        selection = self.file_listbox.curselection()
        if not selection:
            messagebox.showwarning("提示", "请先选择要拆分的JSON文件")
            return
        filename = self.file_listbox.get(selection[0])
        filepath = self.file_paths.get(filename)
        if not filepath or not os.path.exists(filepath):
            messagebox.showerror("错误", f"文件不存在: {filepath}")
            return
        # 读取JSON内容
        import json
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
        except Exception as e:
            messagebox.showerror("错误", f"读取JSON文件失败: {e}")
            return
        # 分析结构
        from utils import json_splitter
        analysis = json_splitter.analyze_json_structure(json_data)
        # 居中弹窗函数
        def center_window(win, width, height):
            win.update_idletasks()
            x = win.winfo_screenwidth() // 2 - width // 2
            y = win.winfo_screenheight() // 2 - height // 2
            win.geometry(f"{width}x{height}+{x}+{y}")
        # 创建弹窗
        win = tk.Toplevel(self.parent)
        win.title(f"拆分文件 - {filename}")
        center_window(win, 520, 520)
        win.transient(self.parent)
        win.grab_set()
        # 结构分析区
        frm_top = ttk.Frame(win)
        frm_top.pack(fill=tk.X, padx=10, pady=8)
        ttk.Label(frm_top, text="结构分析:", font=(None, 11, 'bold')).pack(anchor='w')
        txt = tk.Text(frm_top, height=15, wrap='none', font=('Consolas', 10))
        txt.pack(fill=tk.X, pady=2)
        txt.insert('1.0', f"文件数: {analysis.get('fileCount')}\n总大小: {analysis.get('totalSize')}\n最大层级: {analysis.get('maxDepth')}\n\n目录结构:\n{analysis.get('treeString')}")
        txt.config(state='disabled')
        # 拆分方式选择
        frm_mode = ttk.LabelFrame(win, text="选择拆分模式:")
        frm_mode.pack(fill=tk.X, padx=10, pady=8)
        split_mode = tk.StringVar(value='folder')
        frm1 = ttk.Frame(frm_mode)
        frm1.pack(anchor='w', pady=2)
        r1 = ttk.Radiobutton(frm1, text="按目录层级", variable=split_mode, value='folder')
        r1.pack(side='left')
        ttk.Label(frm1, text="层数:").pack(side='left', padx=(8,0))
        level_var = tk.IntVar(value=1)
        level_spin = ttk.Spinbox(frm1, from_=1, to=20, textvariable=level_var, width=4)
        level_spin.pack(side='left')
        frm2 = ttk.Frame(frm_mode)
        frm2.pack(anchor='w', pady=2)
        r2 = ttk.Radiobutton(frm2, text="按文件数量", variable=split_mode, value='count')
        r2.pack(side='left')
        ttk.Label(frm2, text="每份:").pack(side='left', padx=(8,0))
        count_var = tk.IntVar(value=500)
        count_entry = ttk.Entry(frm2, textvariable=count_var, width=6)
        count_entry.pack(side='left')
        # 过滤设置
        frm_filter = ttk.LabelFrame(win, text="元数据过滤设置(可选):")
        frm_filter.pack(fill=tk.X, padx=10, pady=8)
        ext_vars = {ext: tk.BooleanVar() for ext in ['nfo','jpg','jpeg','png']}
        row = ttk.Frame(frm_filter)
        row.pack(anchor='w', pady=2)
        ttk.Checkbutton(row, text='.nfo', variable=ext_vars['nfo']).pack(side='left', padx=2)
        ttk.Checkbutton(row, text='.jpg/.jpeg', variable=ext_vars['jpg']).pack(side='left', padx=2)
        ttk.Checkbutton(row, text='.png', variable=ext_vars['png']).pack(side='left', padx=2)
        ttk.Label(row, text='自定义:').pack(side='left', padx=(8,0))
        custom_ext_var = tk.StringVar()
        custom_entry = ttk.Entry(row, textvariable=custom_ext_var, width=18)
        custom_entry.pack(side='left')
        ttk.Label(row, text='(逗号隔开)').pack(side='left', padx=(2,0))

        def ellipsis_filename(idx, base, ext):
            idx_str = f"{idx+1:02d}_"
            maxlen = 30
            name = idx_str + base + ext
            if len(name) <= maxlen:
                return name
            else:
                prefix = base[:6]
                suffix = base[-8:] if len(base) > 8 else base
                return f"{idx_str}{prefix}...{suffix}{ext}"

        def on_push_all():
            exts = []
            if ext_vars['nfo'].get(): exts.append('nfo')
            if ext_vars['jpg'].get(): exts.extend(['jpg','jpeg'])
            if ext_vars['png'].get(): exts.append('png')
            custom = custom_ext_var.get().strip()
            if custom:
                exts += [e.strip().lower() for e in custom.split(',') if e.strip()]
            filtered_json = json_splitter.filter_json_files(json_data, exts)
            try:
                if split_mode.get() == 'folder':
                    level = level_var.get()
                    chunks = json_splitter.split_json_by_folder(filtered_json, level)
                else:
                    count = count_var.get()
                    chunks = json_splitter.split_json_by_count(filtered_json, count)
            except Exception as e:
                messagebox.showerror("错误", f"拆分失败: {e}")
                return
            if not chunks:
                messagebox.showwarning("提示", "拆分结果为空！")
                return
            import os
            import json as _json
            base, ext = os.path.splitext(filename)
            orig_dir = os.path.dirname(filepath)
            pushed = 0
            for i, chunk in enumerate(chunks):
                full_name = f"{i+1:02d}_{base}{ext}"
                save_path = os.path.join(orig_dir, full_name)
                with open(save_path, 'w', encoding='utf-8') as f:
                    _json.dump(chunk, f, ensure_ascii=False, indent=2)
                self.add_file_to_list(full_name, save_path)
                pushed += 1
            messagebox.showinfo("完成", f"已推送 {pushed} 个文件到列表\n文件已保存在: {orig_dir}")
            win.destroy()

        def on_confirm():
            exts = []
            if ext_vars['nfo'].get(): exts.append('nfo')
            if ext_vars['jpg'].get(): exts.extend(['jpg','jpeg'])
            if ext_vars['png'].get(): exts.append('png')
            custom = custom_ext_var.get().strip()
            if custom:
                exts += [e.strip().lower() for e in custom.split(',') if e.strip()]
            filtered_json = json_splitter.filter_json_files(json_data, exts)
            try:
                if split_mode.get() == 'folder':
                    level = level_var.get()
                    chunks = json_splitter.split_json_by_folder(filtered_json, level)
                else:
                    count = count_var.get()
                    chunks = json_splitter.split_json_by_count(filtered_json, count)
            except Exception as e:
                messagebox.showerror("错误", f"拆分失败: {e}")
                return
            if not chunks:
                messagebox.showwarning("提示", "拆分结果为空！")
                return
            win.destroy()
            show_split_result(chunks)

        # 再创建按钮，只保留“开始拆分”
        frm_btn = ttk.Frame(win)
        frm_btn.pack(pady=10)
        ttk.Button(frm_btn, text="开始拆分", bootstyle="success", command=on_confirm, width=12).pack(side='left', padx=18)

        def show_split_result(chunks):
            import os
            res_win = tk.Toplevel(self.parent)
            res_win.title("拆分结果 - 请选择要保存/推送的文件")
            center_window(res_win, 480, 420)
            res_win.transient(self.parent)
            res_win.grab_set()
            ttk.Label(res_win, text=f"共拆分为 {len(chunks)} 个文件：", font=(None, 11, 'bold')).pack(anchor='w', padx=10, pady=(10,2))
            listbox = tk.Listbox(res_win, selectmode=tk.MULTIPLE, height=12)
            listbox.pack(fill=tk.BOTH, expand=True, padx=12, pady=6)
            base, ext = os.path.splitext(filename)
            full_filenames = [f"{idx+1:02d}_{base}{ext}" for idx in range(len(chunks))]
            for idx, chunk in enumerate(chunks):
                name = ellipsis_filename(idx, base, ext)
                listbox.insert(tk.END, f"{name}  (文件数:{chunk.get('totalFilesCount', len(chunk.get('files',[])))})")
            btn_frame = ttk.Frame(res_win)
            btn_frame.pack(pady=8)
            def save_selected():
                sel = listbox.curselection()
                if not sel:
                    messagebox.showwarning("提示", "请先选择要保存的文件")
                    return
                import json as _json
                from tkinter import filedialog
                for i in sel:
                    chunk = chunks[i]
                    save_path = filedialog.asksaveasfilename(
                        title="保存拆分文件",
                        defaultextension=ext,
                        initialfile=full_filenames[i],
                        filetypes=[("JSON文件", "*.json")]
                    )
                    if save_path:
                        with open(save_path, 'w', encoding='utf-8') as f:
                            _json.dump(chunk, f, ensure_ascii=False, indent=2)
                messagebox.showinfo("完成", "已保存所选文件，可继续操作或手动关闭窗口")
            def push_selected():
                sel = listbox.curselection()
                if not sel:
                    messagebox.showwarning("提示", "请先选择要推送的文件")
                    return
                import os
                import json as _json
                orig_dir = os.path.dirname(filepath)
                pushed = 0
                for i in sel:
                    chunk = chunks[i]
                    full_name = full_filenames[i]
                    save_path = os.path.join(orig_dir, full_name)
                    with open(save_path, 'w', encoding='utf-8') as f:
                        _json.dump(chunk, f, ensure_ascii=False, indent=2)
                    self.add_file_to_list(full_name, save_path)
                    if os.path.exists(save_path):
                        pushed += 1
                messagebox.showinfo("完成", f"已推送 {pushed} 个文件到列表\n文件已保存在: {orig_dir}\n可继续操作或手动关闭窗口")
                # 不自动关闭弹窗
            ttk.Button(btn_frame, text="保存到本地", bootstyle="primary", command=save_selected, width=12).pack(side='left', padx=18)
            ttk.Button(btn_frame, text="推送列表", bootstyle="success", command=push_selected, width=12).pack(side='left', padx=18)