"""
解析器工厂
"""
import logging
from typing import Optional, Dict, Any, TYPE_CHECKING
from pathlib import Path

# 为类型提示导入
if TYPE_CHECKING:
    from .base_parser import BaseParser
    from .size_parser import SizeParser
    from .readelf_parser import ReadelfParser

logger = logging.getLogger(__name__)


class ParserFactory:
    """解析器工厂"""
    
    @staticmethod
    def create_size_parser(tool_path: str, timeout: int = 30) -> 'SizeParser':
        """
        创建size解析器
        
        Args:
            tool_path: size工具路径
            timeout: 超时时间
            
        Returns:
            SizeParser实例
        """
        from .size_parser import SizeParser
        return SizeParser(tool_path, timeout)
    
    @staticmethod
    def create_readelf_parser(tool_path: str, timeout: int = 30) -> 'ReadelfParser':
        """
        创建readelf解析器
        
        Args:
            tool_path: readelf工具路径
            timeout: 超时时间
            
        Returns:
            ReadelfParser实例
        """
        from .readelf_parser import ReadelfParser
        return ReadelfParser(tool_path, timeout)
    
    @staticmethod
    def create_parser_from_config(
        size_path: str,
        readelf_path: Optional[str] = None,
        timeout: int = 30
    ) -> Dict[str, 'BaseParser']:
        """
        从配置创建解析器
        
        Args:
            size_path: size工具路径
            readelf_path: readelf工具路径（可选）
            timeout: 超时时间
            
        Returns:
            解析器字典 {'size': SizeParser, 'readelf': ReadelfParser（可选）}
        """
        parsers = {}
        
        # 创建size解析器
        try:
            size_parser = ParserFactory.create_size_parser(size_path, timeout)
            parsers['size'] = size_parser
            logger.info(f"创建size解析器成功: {size_path}")
        except Exception as e:
            logger.error(f"创建size解析器失败: {e}")
            raise
        
        # 创建readelf解析器（如果提供了路径）
        if readelf_path:
            try:
                readelf_parser = ParserFactory.create_readelf_parser(readelf_path, timeout)
                parsers['readelf'] = readelf_parser
                logger.info(f"创建readelf解析器成功: {readelf_path}")
            except Exception as e:
                logger.warning(f"创建readelf解析器失败: {e}")
                # 不抛出异常，因为readelf是可选的
        
        return parsers
    
    @staticmethod
    def find_tool_in_system(tool_name: str) -> Optional[str]:
        """
        在系统中查找工具
        
        Args:
            tool_name: 工具名称
            
        Returns:
            工具路径，如果未找到则返回None
        """
        import shutil
        import os
        
        # 直接查找
        tool_path = shutil.which(tool_name)
        if tool_path:
            return tool_path
        
        # 尝试常见的前缀
        common_prefixes = [
            "riscv64-unknown-elf-",
            "arm-none-eabi-",
            "xtensa-esp32-elf-",
            "avr-",
            "msp430-",
            "x86_64-linux-gnu-",
            ""
        ]
        
        for prefix in common_prefixes:
            full_name = f"{prefix}{tool_name}"
            tool_path = shutil.which(full_name)
            if tool_path:
                return tool_path
        
        # 尝试在常见工具链目录中查找
        common_paths = [
            "/usr/bin",
            "/usr/local/bin",
            "/opt/bin",
            "/opt/riscv/bin",
            "/opt/arm/gcc-arm-none-eabi/bin",
            os.path.expanduser("~/bin")
        ]
        
        for base_path in common_paths:
            test_path = Path(base_path) / tool_name
            if test_path.exists() and os.access(test_path, os.X_OK):
                return str(test_path)
        
        return None