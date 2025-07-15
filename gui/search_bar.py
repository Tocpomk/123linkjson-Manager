import tkinter as tk
import ttkbootstrap as ttk

class SearchBar(ttk.Frame):
    def __init__(self, parent, on_search=None, placeholder='搜索秒链...', *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.on_search = on_search
        self.var = tk.StringVar()
        self.entry = ttk.Entry(self, textvariable=self.var, width=28)
        self.entry.pack(side='left', fill='x', expand=True, padx=(0, 4))
        self.entry.insert(0, placeholder)
        self.entry.bind('<FocusIn>', self._clear_placeholder)
        self.entry.bind('<FocusOut>', self._add_placeholder)
        self.entry.bind('<Return>', self._trigger_search)
        self.placeholder = placeholder
        self.has_placeholder = True
        btn = ttk.Button(self, text='搜索', bootstyle='info', width=7, command=self._trigger_search)
        btn.pack(side='left', padx=(0, 2))
        clear_btn = ttk.Button(self, text='清空', bootstyle='secondary', width=7, command=self._clear)
        clear_btn.pack(side='left')

    def _clear_placeholder(self, event=None):
        if self.has_placeholder:
            self.entry.delete(0, tk.END)
            self.has_placeholder = False

    def _add_placeholder(self, event=None):
        if not self.entry.get():
            self.entry.insert(0, self.placeholder)
            self.has_placeholder = True

    def _trigger_search(self, event=None):
        value = self.var.get().strip()
        if self.has_placeholder:
            value = ''
        if self.on_search:
            self.on_search(value)

    def _clear(self):
        self.var.set('')
        self._add_placeholder()
        if self.on_search:
            self.on_search('') 