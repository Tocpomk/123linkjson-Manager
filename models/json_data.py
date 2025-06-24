"""
JSON数据模型模块

此模块提供了JSON数据的核心处理逻辑。
主要功能包括：
- 加载和保存JSON文件
- 添加和删除文件
- 合并JSON文件
- 数据验证和处理
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional

from utils.json_handler import read_json_file, write_json_file, is_valid_123_json
from utils.file_sorter import sort_json_data


class JsonData:
    """JSON数据模型类"""
    
    def __init__(self):
        """初始化JSON数据模型"""
        self.data = None  # JSON数据
        self.files = []   # 文件列表的快捷引用
    
    def load(self, filepath: str) -> Tuple[bool, str]:
        """
        加载JSON文件
        
        Args:
            filepath: JSON文件路径
            
        Returns:
            Tuple[bool, str]: (是否成功, 错误消息)
        """
        # 读取文件
        data, error_msg = read_json_file(filepath)
        if error_msg:
            return False, error_msg
        
        # 验证数据格式
        valid, error_msg = is_valid_123_json(data)
        if not valid:
            return False, error_msg
        
        # 更新数据
        self.data = data
        self.files = data['files']
        
        return True, ""
    
    def save(self, filepath: str) -> Tuple[bool, str]:
        """
        保存JSON文件
        
        Args:
            filepath: JSON文件路径
            
        Returns:
            Tuple[bool, str]: (是否成功, 错误消息)
        """
        if not self.data:
            return False, "没有数据可保存"
        
        # 更新文件总数和总大小
        self.update_totals()
        
        # 写入文件
        success, error_msg = write_json_file(filepath, self.data)
        
        return success, error_msg
    
    def create_new(self) -> str:
        """
        创建新的JSON数据
        
        Returns:
            str: 新文件的文件名
        """
        # 创建基本数据结构
        self.data = {
            "files": [],
            "totalFilesCount": 0,
            "totalSize": 0
        }
        self.files = self.data['files']
        
        # 生成文件名
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        filename = f"123FastLink_{timestamp}.json"
        
        return filename
    
    def update_totals(self):
        """更新文件总数和总大小"""
        if not self.data or 'files' not in self.data:
            return
        
        total_size = sum(int(file['size']) for file in self.files)
        self.data['totalFilesCount'] = len(self.files)
        self.data['totalSize'] = total_size
    
    def add_files(self, new_files: List[Dict[str, Any]]) -> int:
        """
        添加新文件到数据中
        
        Args:
            new_files: 新文件信息列表
            
        Returns:
            int: 添加的文件数量
        """
        if not self.data:
            return 0
        
        added_count = 0
        existing_paths = {file['path'] for file in self.files}
        
        for file in new_files:
            if file['path'] not in existing_paths:
                self.files.append(file)
                existing_paths.add(file['path'])
                added_count += 1
        
        # 排序文件列表
        self.data = sort_json_data(self.data)
        self.files = self.data['files']
        
        # 更新总计
        self.update_totals()
        
        return added_count
    
    def get_file_by_path(self, path: str) -> Optional[Dict[str, Any]]:
        """
        根据路径获取文件信息
        
        Args:
            path: 文件路径
            
        Returns:
            Optional[Dict[str, Any]]: 文件信息，如果未找到则返回None
        """
        if not self.files:
            return None
        
        for file in self.files:
            if file['path'] == path:
                return file
        
        return None
    
    def remove_files(self, paths: List[str]) -> int:
        """
        从数据中删除指定路径的文件
        
        Args:
            paths: 要删除的文件路径列表
            
        Returns:
            int: 删除的文件数量
        """
        if not self.data or not paths:
            return 0
        
        removed_count = 0
        paths_set = set(paths)
        
        # 使用列表推导式过滤掉要删除的文件
        self.files = [file for file in self.files if file['path'] not in paths_set]
        self.data['files'] = self.files
        
        # 更新总计
        self.update_totals()
        
        removed_count = len(paths_set)
        return removed_count
    
    @staticmethod
    def merge_json_files(filepaths: List[str]) -> Tuple[Optional[Dict[str, Any]], int]:
        """
        合并多个JSON文件
        
        Args:
            filepaths: JSON文件路径列表
            
        Returns:
            Tuple[Optional[Dict[str, Any]], int]: (合并后的数据, 添加的文件数)
            - 如果合并失败，返回(None, 0)
        """
        if not filepaths:
            return None, 0
        
        # 创建新的数据结构
        merged_data = {
            "files": [],
            "totalFilesCount": 0,
            "totalSize": 0
        }
        
        # 用于跟踪已存在的文件路径
        existing_paths = set()
        total_added = 0
        
        # 合并文件
        for filepath in filepaths:
            # 读取文件
            data, error_msg = read_json_file(filepath)
            if error_msg:
                continue
            
            # 验证数据格式
            valid, error_msg = is_valid_123_json(data)
            if not valid:
                continue
            
            # 添加新文件
            for file in data['files']:
                if file['path'] not in existing_paths:
                    merged_data['files'].append(file)
                    existing_paths.add(file['path'])
                    total_added += 1
        
        if not merged_data['files']:
            return None, 0
        
        # 排序文件列表
        merged_data = sort_json_data(merged_data)
        
        # 更新总计
        total_size = sum(int(file['size']) for file in merged_data['files'])
        merged_data['totalFilesCount'] = len(merged_data['files'])
        merged_data['totalSize'] = total_size
        
        return merged_data, total_added