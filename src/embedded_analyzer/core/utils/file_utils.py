"""
文件操作工具函数
"""
import os
import re
from pathlib import Path
from typing import List, Optional, Generator
import logging

logger = logging.getLogger(__name__)


def find_object_files(directory: str, pattern: str = "*.o", recursive: bool = True) -> List[str]:
    """
    查找目标文件
    
    Args:
        directory: 目录路径
        pattern: 文件匹配模式（支持通配符）
        recursive: 是否递归查找
    
    Returns:
        文件路径列表
    """
    try:
        dir_path = Path(directory)
        if not dir_path.exists():
            raise ValueError(f"目录不存在: {directory}")
        if not dir_path.is_dir():
            raise ValueError(f"不是目录: {directory}")
        
        if recursive:
            # 递归查找
            files = list(dir_path.rglob(pattern))
        else:
            # 非递归查找
            files = list(dir_path.glob(pattern))
        
        # 转换为字符串并排序
        return sorted([str(f.absolute()) for f in files])
        
    except Exception as e:
        logger.error(f"查找文件失败: {e}")
        return []


def get_file_size(file_path: str) -> int:
    """获取文件大小（字节）"""
    try:
        return Path(file_path).stat().st_size
    except Exception as e:
        logger.error(f"获取文件大小失败: {file_path}, {e}")
        return 0


def is_valid_object_file(file_path: str) -> bool:
    """检查是否是有效的目标文件"""
    try:
        path = Path(file_path)
        if not path.exists():
            return False
        
        # 检查文件扩展名
        if path.suffix.lower() != '.o':
            return False
        
        # 检查文件大小（最小合理大小）
        size = path.stat().st_size
        if size < 64:  # 太小的文件可能不是有效的.o文件
            return False
            
        # TODO: 可以添加ELF魔数检查
        return True
        
    except Exception:
        return False


def sanitize_path(path: str) -> str:
    """清理路径，移除多余的斜杠和点"""
    return str(Path(path).resolve())


def get_relative_path(base_path: str, target_path: str) -> str:
    """获取相对路径"""
    try:
        base = Path(base_path).resolve()
        target = Path(target_path).resolve()
        return str(target.relative_to(base))
    except ValueError:
        # 如果不属于同一根目录，返回绝对路径
        return target_path


def split_path_components(path: str) -> List[str]:
    """拆分路径为组件（用于面包屑）"""
    path_obj = Path(path)
    components = []
    
    # 从根目录开始
    current = path_obj.resolve()
    
    while current != current.parent:  # 直到根目录
        components.insert(0, str(current))
        current = current.parent
    
    return components
