import os
from typing import List, Dict, Any, Tuple, Optional
import copy


def analyze_json_structure(json_data: dict) -> dict:
    """
    分析JSON结构，返回文件数、总大小、最大层级、目录树字符串。
    """
    if not json_data or not isinstance(json_data.get('files'), list):
        return {"error": "JSON数据格式无效，缺少 'files' 数组。"}
    tree = {}
    max_depth = 0
    common_path_prefix = (json_data.get('commonPath') or '').rstrip('/') + ('/' if json_data.get('commonPath') else '')
    for file in json_data['files']:
        full_path = common_path_prefix + file['path']
        parts = [p for p in full_path.split('/') if p]
        current = tree
        for idx, part in enumerate(parts):
            if idx == len(parts) - 1:
                current[part] = None
            else:
                if part not in current:
                    current[part] = {}
                current = current[part]
        if len(parts) > max_depth:
            max_depth = len(parts)

    def format_tree(node, prefix='', depth=1):
        result = ''
        keys = list(node.keys())
        for i, key in enumerate(keys):
            is_last = (i == len(keys) - 1)
            connector = '└── ' if is_last else '├── '
            item_prefix = '📄 ' if node[key] is None else '📁 '
            result += f"{prefix}{connector}{item_prefix}{key}  (Lv. {depth})\n"
            if node[key] is not None:
                new_prefix = prefix + ('    ' if is_last else '│   ')
                result += format_tree(node[key], new_prefix, depth + 1)
        return result

    tree_string = format_tree(tree)
    file_count = len(json_data['files'])
    total_size = sum(int(file.get('size', 0)) for file in json_data['files'])
    return {
        'fileCount': file_count,
        'totalSize': total_size,
        'maxDepth': max_depth,
        'treeString': tree_string
    }

def filter_json_files(json_data: dict, extensions: List[str]) -> dict:
    """
    按扩展名过滤文件，返回新json_data。
    extensions: 需要过滤掉的扩展名（不区分大小写，无点号）
    """
    if not extensions:
        return json_data
    filtered = copy.deepcopy(json_data)
    filtered['files'] = [
        f for f in json_data['files']
        if not ('.' in f['path'] and f['path'].split('.')[-1].lower() in extensions)
    ]
    return filtered

def split_json_by_count(json_data: dict, chunk_size: int) -> List[dict]:
    """
    按文件数量拆分，返回多个json对象列表。
    """
    if chunk_size <= 0:
        raise ValueError('chunk_size必须为正整数')
    base_metadata = copy.deepcopy(json_data)
    base_metadata.pop('files', None)
    base_metadata.pop('totalFilesCount', None)
    base_metadata.pop('totalSize', None)
    base_metadata.pop('formattedTotalSize', None)
    files = json_data['files']
    chunks = []
    for i in range(0, len(files), chunk_size):
        chunk_files = files[i:i+chunk_size]
        chunk_total_size = sum(int(f.get('size', 0)) for f in chunk_files)
        chunk_json = copy.deepcopy(base_metadata)
        chunk_json['files'] = chunk_files
        chunk_json['totalFilesCount'] = len(chunk_files)
        chunk_json['totalSize'] = chunk_total_size
        chunks.append(chunk_json)
    return chunks

def split_json_by_folder(json_data: dict, level: int) -> List[dict]:
    """
    按目录层级拆分，返回多个json对象列表。
    """
    if level <= 0:
        raise ValueError('level必须为正整数')
    base_metadata = copy.deepcopy(json_data)
    base_metadata.pop('files', None)
    base_metadata.pop('totalFilesCount', None)
    base_metadata.pop('totalSize', None)
    base_metadata.pop('formattedTotalSize', None)
    common_path = (json_data.get('commonPath') or '').rstrip('/') + ('/' if json_data.get('commonPath') else '')
    folders = {}
    for file in json_data['files']:
        full_path = common_path + file['path']
        parts = [p for p in full_path.split('/') if p]
        dir_parts = parts[:-1]
        group_key = '/'.join(dir_parts[:level]) if len(dir_parts) >= level else '_root_'
        folders.setdefault(group_key, []).append(file)
    chunks = []
    for group_key, files_in_group in folders.items():
        if group_key == '_root_':
            new_common_path = common_path
            new_files = files_in_group
        else:
            new_common_path = group_key + '/'
            new_files = []
            for f in files_in_group:
                full_path = common_path + f['path']
                new_rel_path = full_path[len(group_key):].lstrip('/')
                f2 = copy.deepcopy(f)
                f2['path'] = new_rel_path
                new_files.append(f2)
        chunk_total_size = sum(int(f.get('size', 0)) for f in new_files)
        chunk_json = copy.deepcopy(base_metadata)
        chunk_json['files'] = new_files
        chunk_json['commonPath'] = new_common_path
        chunk_json['totalFilesCount'] = len(new_files)
        chunk_json['totalSize'] = chunk_total_size
        chunks.append(chunk_json)
    return chunks 