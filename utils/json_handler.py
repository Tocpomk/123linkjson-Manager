
"""
JSON处理模块

此模块提供了用于处理JSON文件的通用功能。
主要功能包括：
- 读取和写入JSON文件
- 检查文件是否存在
- 验证JSON格式
"""

import json
import os
from typing import Dict, Any, Tuple, Optional, List


def read_json_file(filepath: str) -> Tuple[Optional[Dict[str, Any]], str]:
    """
    读取JSON文件
    
    Args:
        filepath: JSON文件路径
        
    Returns:
        Tuple[Optional[Dict[str, Any]], str]: (JSON数据, 错误消息)
        - 如果读取成功，错误消息为空字符串
        - 如果读取失败，JSON数据为None
    """
    if not os.path.exists(filepath):
        return None, f"文件不存在: {filepath}"
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data, ""
    except json.JSONDecodeError:
        return None, "无效的JSON格式"
    except Exception as e:
        return None, f"读取文件时出错: {str(e)}"


def write_json_file(filepath: str, data: Dict[str, Any]) -> Tuple[bool, str]:
    """
    写入JSON文件
    
    Args:
        filepath: JSON文件路径
        data: 要写入的JSON数据
        
    Returns:
        Tuple[bool, str]: (是否成功, 错误消息)
        - 如果写入成功，错误消息为空字符串
    """
    try:
        # 确保目录存在
        directory = os.path.dirname(filepath)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True, ""
    except Exception as e:
        return False, f"写入文件时出错: {str(e)}"


def is_valid_json_file(filepath: str) -> Tuple[bool, str]:
    """
    检查文件是否为有效的JSON文件
    
    Args:
        filepath: 文件路径
        
    Returns:
        Tuple[bool, str]: (是否有效, 错误消息)
        - 如果文件有效，错误消息为空字符串
    """
    if not os.path.exists(filepath):
        return False, f"文件不存在: {filepath}"
    
    if not filepath.lower().endswith('.json'):
        return False, "文件不是JSON格式"
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            json.load(f)
        return True, ""
    except json.JSONDecodeError:
        return False, "无效的JSON格式"
    except Exception as e:
        return False, f"检查文件时出错: {str(e)}"


def is_valid_123_json(data: Dict[str, Any]) -> Tuple[bool, str]:
    """
    检查JSON数据是否为有效的123云盘JSON格式或123FastLink格式
    
    Args:
        data: JSON数据
        
    Returns:
        Tuple[bool, str]: (是否有效, 错误消息)
        - 如果数据有效，错误消息为空字符串
    """
    # 检查是否是123FastLink格式 (新版本)
    if ('files' in data and isinstance(data['files'], list) and 
        ('scriptVersion' in data or 'exportVersion' in data)):
        # 转换为标准格式
        files = data['files']
        total_size = 0
        
        # 处理文件列表
        for i, item in enumerate(files):
            if not isinstance(item, dict):
                continue
                
            # 确保size字段是整数
            if 'size' in item:
                try:
                    size = int(item['size'])
                    item['size'] = size
                    total_size += size
                except (ValueError, TypeError):
                    item['size'] = 0
            else:
                item['size'] = 0
                
            # 确保path和etag字段存在
            if 'path' not in item:
                if 'name' in item:
                    item['path'] = item['name']
                else:
                    item['path'] = f"未命名文件{i+1}"
                    
            if 'etag' not in item:
                if 'hash' in item:
                    item['etag'] = item['hash']
                elif 'sha1' in item:
                    item['etag'] = item['sha1']
                else:
                    item['etag'] = ""
        
        # 添加必要字段
        if 'totalFilesCount' not in data:
            data['totalFilesCount'] = len(files)
            
        if 'totalSize' not in data:
            data['totalSize'] = total_size
        
        return True, ""
    
    # 检查是否是123FastLink格式 (旧版本)
    elif 'list' in data and isinstance(data['list'], list):
        # 转换为标准格式
        files = []
        total_size = 0
        
        for item in data['list']:
            if not isinstance(item, dict):
                continue
                
            file = {}
            # 映射字段
            if 'name' in item:
                file['path'] = item['name']
            elif 'path' in item:
                file['path'] = item['path']
            else:
                continue
                
            if 'size' in item:
                try:
                    size = int(item['size'])
                    file['size'] = size
                    total_size += size
                except (ValueError, TypeError):
                    file['size'] = 0
            else:
                file['size'] = 0
                
            if 'hash' in item:
                file['etag'] = item['hash']
            elif 'sha1' in item:
                file['etag'] = item['sha1']
            else:
                file['etag'] = ""
                
            files.append(file)
        
        # 创建新的数据结构，而不是修改原始数据
        converted_data = {
            'files': files,
            'totalFilesCount': len(files),
            'totalSize': total_size
        }
        
        # 更新原始数据
        data.clear()
        data.update(converted_data)
        
        return True, ""
    
    # 检查标准123云盘格式
    required_fields = ['files', 'totalFilesCount', 'totalSize']
    for field in required_fields:
        if field not in data:
            return False, f"缺少必要字段: {field}"
    
    # 检查files字段是否为列表
    if not isinstance(data['files'], list):
        return False, "files字段必须是列表"
    
    # 检查文件列表中的每个文件是否包含必要的字段
    for i, file in enumerate(data['files']):
        if not isinstance(file, dict):
            return False, f"文件 #{i+1} 必须是字典"
        
        file_required_fields = ['path', 'size', 'etag']
        for field in file_required_fields:
            if field not in file:
                return False, f"文件 #{i+1} 缺少必要字段: {field}"
    
    return True, ""


def get_json_files_in_directory(directory: str) -> List[str]:
    """
    获取目录中的所有JSON文件
    
    Args:
        directory: 目录路径
        
    Returns:
        List[str]: JSON文件路径列表
    """
    json_files = []
    
    if not os.path.exists(directory) or not os.path.isdir(directory):
        return json_files
    
    for filename in os.listdir(directory):
        if filename.lower().endswith('.json'):
            json_files.append(os.path.join(directory, filename))
    
    return json_files


def backup_json_file(filepath: str) -> Tuple[bool, str]:
    """
    备份JSON文件
    
    Args:
        filepath: JSON文件路径
        
    Returns:
        Tuple[bool, str]: (是否成功, 备份文件路径或错误消息)
    """
    if not os.path.exists(filepath):
        return False, f"文件不存在: {filepath}"
    
    try:
        # 生成备份文件名
        backup_filepath = f"{filepath}.bak"
        
        # 复制文件内容
        with open(filepath, 'r', encoding='utf-8') as src:
            with open(backup_filepath, 'w', encoding='utf-8') as dst:
                dst.write(src.read())
        
        return True, backup_filepath
    except Exception as e:
        return False, f"备份文件时出错: {str(e)}"