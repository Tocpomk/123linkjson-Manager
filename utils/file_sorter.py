"""
文件排序模块

此模块提供了用于排序JSON文件的功能。
主要功能包括：
- 检查文件是否已排序
- 对文件进行排序
- 保存排序后的文件
"""

import os
import json
from typing import Tuple, List, Dict, Any


def check_and_sort_json_file(filepath: str) -> Tuple[bool, bool, str]:
    """
    检查并排序JSON文件
    
    Args:
        filepath: JSON文件路径
        
    Returns:
        Tuple[bool, bool, str]: (是否需要排序, 是否成功, 消息)
        - 如果文件已经是有序的，第一个值为False
        - 如果排序成功，第二个值为True
    """
    try:
        # 读取文件
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 检查文件格式
        if not isinstance(data, dict) or 'files' not in data:
            return False, False, "无效的JSON格式：缺少files字段"
        
        # 检查是否需要排序
        needs_sort, sorted_data = check_if_needs_sort(data)
        
        if not needs_sort:
            return False, True, "文件已经是有序的"
        
        # 保存排序后的文件
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(sorted_data, f, indent=2, ensure_ascii=False)
        
        return True, True, "文件已成功排序"
        
    except Exception as e:
        return False, False, f"排序文件时出错: {str(e)}"


def check_if_needs_sort(data: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    """
    检查JSON数据是否需要排序
    
    Args:
        data: JSON数据
        
    Returns:
        Tuple[bool, Dict[str, Any]]: (是否需要排序, 排序后的数据)
        - 如果数据已经是有序的，第一个值为False
    """
    if not isinstance(data, dict) or 'files' not in data:
        return False, data
    
    # 复制数据
    sorted_data = data.copy()
    
    # 获取文件列表
    files = data['files']
    if not isinstance(files, list):
        return False, data
    
    # 按路径排序
    sorted_files = sorted(files, key=lambda x: x.get('path', '').lower())
    
    # 检查是否已经排序
    is_sorted = files == sorted_files
    
    if not is_sorted:
        sorted_data['files'] = sorted_files
    
    return not is_sorted, sorted_data


def sort_json_files(filepaths: List[str]) -> Tuple[int, int, str]:
    """
    批量排序JSON文件
    
    Args:
        filepaths: JSON文件路径列表
        
    Returns:
        Tuple[int, int, str]: (成功排序的文件数, 总文件数, 错误消息)
    """
    success_count = 0
    total_count = len(filepaths)
    errors = []
    
    for filepath in filepaths:
        try:
            needs_sort, success, message = check_and_sort_json_file(filepath)
            if success:
                success_count += 1
            else:
                errors.append(f"{os.path.basename(filepath)}: {message}")
        except Exception as e:
            errors.append(f"{os.path.basename(filepath)}: {str(e)}")
    
    if errors:
        error_message = "\n".join(errors)
    else:
        error_message = ""
    
    return success_count, total_count, error_message


def sort_json_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    对JSON数据进行排序
    
    Args:
        data: JSON数据
        
    Returns:
        Dict[str, Any]: 排序后的JSON数据
    """
    if not isinstance(data, dict) or 'files' not in data:
        return data
    
    # 复制数据
    sorted_data = data.copy()
    
    # 获取文件列表
    files = data['files']
    if not isinstance(files, list):
        return data
    
    # 按路径排序
    sorted_files = sorted(files, key=lambda x: x.get('path', '').lower())
    sorted_data['files'] = sorted_files
    
    return sorted_data