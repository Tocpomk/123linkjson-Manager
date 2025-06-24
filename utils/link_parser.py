"""
123云盘秒链解析模块

提供对123云盘秒链格式的解析和生成功能，支持：
- 123FSLink格式：直接包含完整文件路径
- 123FLCPV2格式：使用公共路径前缀优化链接长度
"""

import os
from typing import List, Dict, Any, Optional, Tuple


class LinkParser:
    """123云盘秒链解析器，支持解析和生成两种格式的链接"""
    
    @staticmethod
    def parse_link(link: str) -> Tuple[List[Dict[str, Any]], str]:
        """
        解析云盘秒链，自动识别格式
        
        Args:
            link: 要解析的链接字符串
            
        Returns:
            Tuple[List[Dict], str]: (文件信息列表, 错误消息)
            文件信息包含: path, size, etag
        """
        if not link:
            return [], "链接不能为空"
            
        try:
            if link.startswith("123FSLink"):
                return LinkParser._parse_fslink(link)
            elif link.startswith("123FLCPV2"):
                return LinkParser._parse_flcp_link(link)
            return [], "无效链接格式: 必须以123FSLink或123FLCPV2开头"
        except Exception as e:
            return [], f"解析链接出错: {str(e)}"
            
    @staticmethod
    def _parse_fslink(link: str) -> Tuple[List[Dict[str, Any]], str]:
        """解析123FSLink格式链接"""
        files = []
        parts = link.split('$')
        
        for part in parts[1:]:  # 跳过格式标识符
            if not part.strip():
                continue
                
            try:
                etag, size, path = part.split('#', 2)
                files.append({
                    "path": path.replace('\\', '/').strip(),
                    "size": size.strip(),
                    "etag": etag.strip()
                })
            except ValueError:
                continue
                
        return files or [], "未解析到有效文件信息" if not files else ""
        
    @staticmethod
    def _parse_flcp_link(link: str) -> Tuple[List[Dict[str, Any]], str]:
        """解析123FLCPV2格式链接"""
        files = []
        parts = link.split('$')
        
        if len(parts) < 3:
            return [], "无效FLCPV2格式: 缺少必要部分"
            
        base_path = parts[1].replace('\\', '/').strip('/')
        
        for part in parts[2:]:
            if not part.strip():
                continue
                
            try:
                # 分割出etag, size和完整路径部分
                etag, size, full_path_part = part.split('#', 2)
                # 提取真正的文件名（最后一个#之后的内容）
                name = full_path_part.split('#')[-1].strip()
                # 解码URL编码的特殊字符
                try:
                    from urllib.parse import unquote
                    name = unquote(name)
                except:
                    pass
                # 组合完整路径（确保基础路径不以/结尾）
                clean_base = base_path.rstrip('/')
                # 直接使用提取的文件名，不拼接基础路径
                full_path = name
                files.append({
                    "path": full_path.replace('\\', '/'),
                    "size": size.strip(),
                    "etag": etag.strip()
                })
            except ValueError:
                continue
                
        return files or [], "未解析到有效文件信息" if not files else ""
    
    @staticmethod
    def generate_link(files: List[Dict[str, Any]]) -> str:
        """
        生成云盘秒链，自动选择最优格式
        
        Args:
            files: 文件信息列表，每个需包含path,size,etag
            
        Returns:
            str: 生成的链接字符串
        """
        if not files:
            return "123FSLinkV2"
            
        common_path = LinkParser._find_common_path([f['path'] for f in files])
        return (LinkParser._generate_flcp_link(files, common_path) 
                if common_path 
                else LinkParser._generate_fslink(files))
            
    @staticmethod
    def _generate_fslink(files: List[Dict[str, Any]]) -> str:
        """生成123FSLink格式链接"""
        link = "123FSLinkV2"
        for file in files:
            path = file['path'].replace('\\', '/').strip()
            link += f"${file['etag']}#{file['size']}#{path}"
        return link
        
    @staticmethod
    def _generate_flcp_link(files: List[Dict[str, Any]], base_path: str) -> str:
        """生成123FLCPV2格式链接"""
        # 标准化基础路径，去除结尾斜杠
        base_path = base_path.replace('\\', '/').strip('/')
        link = f"123FLCPV2${base_path}"
        
        for file in files:
            path = file['path'].replace('\\', '/').strip('/')
            # 确保文件名部分不包含基础路径
            if path.startswith(base_path):
                name = path[len(base_path):].lstrip('/')
            else:
                name = path
            link += f"${file['etag']}#{file['size']}#{name}"
        return link
        
    @staticmethod
    def _find_common_path(paths: List[str]) -> str:
        """查找多个路径的最长公共前缀"""
        if not paths:
            return ""
            
        normalized = [p.replace('\\', '/').strip('/') for p in paths]
        common = os.path.commonprefix(normalized)
        return common.rsplit('/', 1)[0] if '/' in common else ""
    
    @staticmethod
    def validate_link_format(link: str) -> Tuple[bool, str]:
        """
        验证链接格式是否有效
        
        Args:
            link: 要验证的链接字符串
            
        Returns:
            Tuple[bool, str]: (是否有效, 错误消息)
        """
        if not link:
            return False, "链接不能为空"
            
        if not (link.startswith("123FSLink") or link.startswith("123FLCPV2")):
            return False, "必须以123FSLink或123FLCPV2开头"
            
        parts = link.split('$')
        if len(parts) < 2:
            return False, "缺少文件信息部分"
            
        for part in parts[1:]:
            if not part:
                continue
                
            try:
                etag, size, _ = part.split('#', 2)
                if not size.isdigit():
                    return False, "文件大小必须为数字"
            except ValueError:
                return False, "文件信息格式错误"
                
        return True, ""
    
    @staticmethod
    def extract_file_info(link_part: str) -> Optional[Dict[str, Any]]:
        """
        从链接部分提取单个文件信息
        
        Args:
            link_part: 链接中的文件部分(etag#size#path)
            
        Returns:
            Optional[Dict]: 文件信息字典或None(解析失败时)
        """
        try:
            etag, size, path = link_part.split('#', 2)
            return {
                "path": path,
                "size": size,
                "etag": etag
            }
        except ValueError:
            return None