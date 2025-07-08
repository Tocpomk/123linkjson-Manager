"""
链接面板模块

此模块提供了应用程序上部的链接输入和导出面板。
主要功能包括：
- 链接输入和解析
- 链接导出
- 链接验证
"""

import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from gui.link_viewer import LinkViewer


class LinkPanel:
    """链接输入和导出面板类"""
    
    def __init__(self, parent, app):
        """
        初始化链接面板
        
        Args:
            parent: 父级窗口部件
            app: 应用程序实例
        """
        self.parent = parent
        self.app = app
        self.link_viewer = None
        
        # 创建面板
        self.create_panel()
    
    def create_panel(self):
        """创建链接面板"""
        # 创建主框架
        self.frame = ttk.LabelFrame(self.parent, text="秒链操作", padding="10")
        self.frame.pack(fill=X, expand=True, padx=10, pady=10)
        
        # 创建链接输入框架
        input_frame = ttk.Frame(self.frame)
        input_frame.pack(fill=X, expand=True, pady=(0, 10))
        
        # 链接输入标签
        ttk.Label(input_frame, text="输入123云盘秒链:").pack(side=LEFT, padx=(0, 5))
        
        # 创建链接输入框架
        text_frame = ttk.Frame(input_frame)
        text_frame.pack(side=LEFT, fill=X, expand=True, padx=(0, 5))
        
        # 链接输入文本框
        self.link_text = tk.Text(text_frame, height=3, wrap=tk.WORD)
        self.link_text.pack(side=LEFT, fill=X, expand=True)
        
        # 添加Ctrl+Enter快捷键
        self.link_text.bind("<Control-Return>", self.add_link)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(text_frame, command=self.link_text.yview)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.link_text.config(yscrollcommand=scrollbar.set)
        
        # 创建链接操作框架
        input_btn_frame = ttk.Frame(self.frame)
        input_btn_frame.pack(fill=X, expand=True)
        
        # 创建一个居中的框架
        center_frame = ttk.Frame(input_btn_frame)
        center_frame.pack(anchor=CENTER, expand=True)
        
        # 粘贴按钮
        ttk.Button(center_frame, text="粘贴秒链", 
                  command=self.paste_from_clipboard,
                  bootstyle="secondary",
                  width=8).pack(side=LEFT, padx=(0, 5))
        
        # 清除按钮
        ttk.Button(center_frame, text="清除秒链", 
                  command=self.clear_text,
                  bootstyle="secondary",
                  width=8).pack(side=LEFT, padx=(0, 5))
        
        # 添加链接按钮
        ttk.Button(center_frame, text="添加秒链", 
                  command=self.add_link,
                  bootstyle="success",
                  width=10).pack(side=LEFT, padx=(0, 5))
        
        # 查看秒链按钮
        ttk.Button(center_frame, text="查看秒链", 
                  command=self.view_links,
                  bootstyle="info",
                  width=10).pack(side=LEFT, padx=(0, 5))
    
    def view_links(self):
        """查看并解析秒链(弹窗形式)"""
        # 首先尝试从文本框获取内容
        link_text = self.link_text.get("1.0", tk.END).strip()
        
        # 如果文本框为空，提示用户输入
        if not link_text:
            messagebox.showwarning("提示", "请输入秒链")
            return
        
        # 创建新的链接查看器弹窗
        self.link_viewer = LinkViewer(self.app.root, self.app)
        
        # 解析并显示链接
        self.link_viewer.parse_and_show_links(link_text)
    
    def add_link(self, event=None):
        """
        添加链接
        
        Args:
            event: 事件对象，用于绑定Enter键
        """
        # 检查是否已选择JSON文件
        if not self.app.current_file:
            messagebox.showwarning("警告", "请先添加或选择JSON文件")
            return
            
        # 获取文本框内容
        link_text = self.link_text.get("1.0", tk.END).strip()
        if not link_text:
            messagebox.showwarning("警告", "请输入链接")
            return
        
        # 检查是否有多行内容
        if '\n' in link_text or len(link_text) > 500:
            # 多行内容，使用批量处理
            self._process_links_in_background(link_text)
            return
        
        # 单行内容，正常处理
        from utils.link_parser import LinkParser
        valid, error_msg = LinkParser.validate_link_format(link_text)
        if not valid:
            messagebox.showerror("错误", error_msg)
            return
        
        # 添加链接
        try:
            result = self.app.add_link(link_text)
            
            # 处理不同返回值格式
            if isinstance(result, (list, tuple)) and len(result) >= 2:
                success, message = result[0], result[1]
            elif isinstance(result, bool):
                success, message = result, "操作成功" if result else "操作失败"
            else:
                success, message = False, "未知的返回值格式"
            
            if success:
                # 清空输入框
                self.link_text.delete("1.0", tk.END)
                messagebox.showinfo("成功", message)
            else:
                messagebox.showerror("错误", message)
                
        except Exception as e:
            messagebox.showerror("错误", f"添加链接时出错: {str(e)}")
    
    def clear_text(self):
        """清除文本框内容"""
        self.link_text.delete("1.0", tk.END)
    
    def paste_from_clipboard(self):
        """从剪贴板粘贴内容并处理链接"""
        try:
            # 获取剪贴板内容
            clipboard_content = self.parent.clipboard_get()
            
            if not clipboard_content:
                messagebox.showwarning("警告", "剪贴板中没有文本内容")
                return
            
            # 直接粘贴到文本框，不进行预处理
            self.link_text.delete("1.0", tk.END)
            self.link_text.insert("1.0", clipboard_content)
            
        except tk.TclError:
            # 剪贴板为空或格式不支持
            messagebox.showwarning("警告", "剪贴板中没有文本内容")
    
    def _process_links_in_background(self, content):
        """在后台线程中处理链接"""
        import threading
        import queue
        from queue import Queue
        
        # 创建进度条窗口
        progress_window = tk.Toplevel(self.app.root)
        progress_window.title("处理中")
        progress_window.geometry("300x150")
        progress_window.transient(self.app.root)
        progress_window.grab_set()
        
        # 居中显示进度条窗口
        progress_window.update_idletasks()
        width = progress_window.winfo_width()
        height = progress_window.winfo_height()
        x = (progress_window.winfo_screenwidth() // 2) - (width // 2)
        y = (progress_window.winfo_screenheight() // 2) - (height // 2)
        progress_window.geometry(f"{width}x{height}+{x}+{y}")
        
        # 添加进度条和标签
        status_var = tk.StringVar(value="正在处理链接...")
        label = ttk.Label(progress_window, textvariable=status_var, padding=(20, 10))
        label.pack()
        
        progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(
            progress_window, 
            variable=progress_var,
            maximum=100,
            mode='determinate',
            length=200
        )
        progress_bar.pack(pady=20)
        
        # 添加取消按钮
        cancel_var = tk.BooleanVar(value=False)
        cancel_button = ttk.Button(
            progress_window, 
            text="取消", 
            command=lambda: [cancel_var.set(True), progress_window.destroy()],
            bootstyle="danger"
        )
        cancel_button.pack(pady=10)
        
        # 创建结果队列
        result_queue = Queue()
        
        # 在后台线程中处理链接
        def process_link():
            try:
                # 检查是否包含多个链接
                links = self._extract_links(content)
                total_links = len(links)
                
                if total_links == 0:
                    result_queue.put(("error", "未找到有效链接"))
                    return
                
                # 更新状态
                self.app.root.after(0, lambda: status_var.set(f"找到 {total_links} 个链接，开始处理..."))
                
                # 分批处理链接，每批100个
                batch_size = 100
                success_count = 0
                error_messages = []
                total_files_added = 0
                
                for i in range(0, total_links, batch_size):
                    if cancel_var.get():
                        result_queue.put("cancelled", "处理已取消")
                        return
                        
                    batch = links[i:i+batch_size]
                    batch_success, _, batch_errors, batch_files = self.app.batch_add_links(batch)
                    
                    success_count += batch_success
                    error_messages.extend(batch_errors)
                    total_files_added += batch_files
                    
                    # 更新进度
                    progress = min(100, int((i + len(batch)) / total_links * 100))
                    self.app.root.after(0, lambda p=progress: [
                        progress_var.set(p),
                        status_var.set(f"已处理 {i + len(batch)}/{total_links} 个链接...")
                    ])
                
                # 处理完成，发送结果
                result = {
                    "success_count": success_count,
                    "total_count": total_links,
                    "error_messages": error_messages,
                    "total_files_added": total_files_added
                }
                result_queue.put(("success", result))
                
            except Exception as e:
                result_queue.put(("error", str(e)))
        
        # 启动后台线程
        thread = threading.Thread(target=process_link)
        thread.daemon = True
        thread.start()
        
        # 定期检查结果队列
        def check_result():
            try:
                status, data = result_queue.get_nowait()
                
                # 关闭进度窗口
                if progress_window.winfo_exists():
                    progress_window.destroy()
                
                if status == "success":
                    # 显示成功结果
                    if data["success_count"] > 0:
                        result_message = f"成功处理 {data["success_count"]}/{data["total_count"]} 个链接，共添加 {data["total_files_added"]} 个文件"
                        if data["error_messages"]:
                            result_message += "\n\n以下链接处理失败:\n" + "\n".join(data["error_messages"][:5])
                            if len(data["error_messages"]) > 5:
                                result_message += f"\n...等共 {len(data['error_messages'])} 个错误"
                        messagebox.showinfo("处理完成", result_message)
                    else:
                        error_msg = "所有链接处理失败:\n" + "\n".join(data["error_messages"][:5])
                        if len(data["error_messages"]) > 5:
                            error_msg += f"\n...等共 {len(data['error_messages'])} 个错误"
                        messagebox.showerror("处理失败", error_msg)
                
                elif status == "error":
                    messagebox.showerror("错误", f"处理链接时出错: {data}")
                
                elif status == "cancelled":
                    messagebox.showinfo("已取消", "链接处理已取消")
                
            except queue.Empty:
                if progress_window.winfo_exists():
                    self.app.root.after(100, check_result)
        
        # 开始检查结果
        self.app.root.after(100, check_result)
    
    def _update_progress(self, status_var, message, window, update_progress=False, progress_value=0, progress_bar=None):
        """更新进度条和状态信息"""
        if window.winfo_exists():
            status_var.set(message)
            if update_progress and progress_bar:
                progress_bar.stop()
                progress_bar.config(mode='determinate')
                progress_bar['value'] = progress_value
    
    def _extract_links(self, content):
        """从文本内容中提取链接"""
        from utils.link_parser import LinkParser
        
        # 按行分割内容
        lines = content.strip().split('\n')
        
        # 提取有效链接
        valid_links = []
        for line in lines:
            line = line.strip()
            if line and LinkParser.validate_link_format(line)[0]:
                valid_links.append(line)
        
        return valid_links