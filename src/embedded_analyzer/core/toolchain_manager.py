"""
工具链管理器
"""
import logging
from typing import Optional, Dict, Any, TYPE_CHECKING
from pathlib import Path

# 为类型提示导入
if TYPE_CHECKING:
    from .parsers.size_parser import SizeParser
    from .parsers.readelf_parser import ReadelfParser
    from ..config.manager import ConfigManager

logger = logging.getLogger(__name__)


class ToolchainManager:
    """工具链管理器"""
    
    def __init__(self, config_manager: Optional['ConfigManager'] = None):
        """
        初始化工具链管理器
        
        Args:
            config_manager: 配置管理器实例
        """
        # 延迟导入以避免循环
        from ..config.manager import ConfigManager
        
        self.config_manager = config_manager or ConfigManager()
        self.config = self.config_manager.load_config()
        
        # 解析器缓存
        self._parsers: Dict[str, Any] = {}
        self._initialized = False
    
    def initialize(self, force: bool = False) -> bool:
        """
        初始化工具链
        
        Args:
            force: 是否强制重新初始化
            
        Returns:
            是否初始化成功
        """
        if self._initialized and not force:
            return True
        
        try:
            # 获取配置
            toolchain_config = self.config.toolchain
            
            # 验证size工具
            if not toolchain_config.size_path:
                raise ValueError("size工具路径未配置")
            
            # 创建解析器
            from .parsers.parser_factory import ParserFactory
            self._parsers = ParserFactory.create_parser_from_config(
                size_path=toolchain_config.size_path,
                readelf_path=toolchain_config.readelf_path,
                timeout=30
            )
            
            self._initialized = True
            logger.info("工具链管理器初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"工具链管理器初始化失败: {e}")
            self._initialized = False
            return False
    
    def get_size_parser(self) -> 'SizeParser':
        """获取size解析器"""
        if not self._initialized:
            self.initialize()
        
        if 'size' not in self._parsers:
            raise ValueError("size解析器未初始化")
        
        return self._parsers['size']
    
    def get_readelf_parser(self) -> Optional['ReadelfParser']:
        """获取readelf解析器（如果可用）"""
        if not self._initialized:
            self.initialize()
        
        return self._parsers.get('readelf')
    
    def has_readelf(self) -> bool:
        """检查是否有readelf解析器"""
        return 'readelf' in self._parsers
    
    def analyze_file(self, file_path: str, detailed: bool = False) -> Dict[str, Any]:
        """
        分析单个文件
        
        Args:
            file_path: 文件路径
            detailed: 是否获取详细信息
            
        Returns:
            分析结果
        """
        if not self._initialized:
            self.initialize()
        
        try:
            # 使用size解析器获取基础信息
            size_parser = self.get_size_parser()
            stats = size_parser.parse_single(file_path)
            
            result = {
                "basic": stats.model_dump(),
                "detailed": None
            }
            
            # 如果请求详细信息且有readelf解析器
            if detailed and self.has_readelf():
                readelf_parser = self.get_readelf_parser()
                if readelf_parser:
                    try:
                        sections = readelf_parser.get_sections(file_path)
                        # 更新统计信息中的详细段
                        stats.detailed_segments = sections
                        result["detailed"] = {
                            "sections": [s.model_dump() for s in sections],
                            "section_count": len(sections)
                        }
                    except Exception as e:
                        logger.warning(f"获取详细段信息失败: {e}")
                        result["detailed_error"] = str(e)
            
            return result
            
        except Exception as e:
            logger.error(f"分析文件失败: {file_path}, {e}")
            raise
    
    def analyze_directory(self, directory: str, pattern: str = "*.o", recursive: bool = False) -> Dict[str, Any]:
        """
        分析目录
        
        Args:
            directory: 目录路径
            pattern: 文件匹配模式
            recursive: 是否递归
            
        Returns:
            分析结果
        """
        if not self._initialized:
            self.initialize()
        
        try:
            size_parser = self.get_size_parser()
            results = size_parser.parse_directory(directory, pattern, recursive)
            
            # 转换为字典格式
            modules = {path: stats.model_dump() for path, stats in results.items()}
            
            # 计算总计
            total_text = sum(stats.text_size for stats in results.values())
            total_data = sum(stats.data_size for stats in results.values())
            total_bss = sum(stats.bss_size for stats in results.values())
            total_size = sum(stats.total_size for stats in results.values())
            
            return {
                "directory": directory,
                "modules": modules,
                "totals": {
                    "text": total_text,
                    "data": total_data,
                    "bss": total_bss,
                    "total": total_size,
                    "flash": total_text + total_data,
                    "ram": total_data + total_bss
                },
                "file_count": len(results),
                "recursive": recursive,
                "pattern": pattern
            }
            
        except Exception as e:
            logger.error(f"分析目录失败: {directory}, {e}")
            raise
    
    def test_toolchain(self) -> Dict[str, Any]:
        """
        测试工具链
        
        Returns:
            测试结果
        """
        results = {
            "initialized": self._initialized,
            "tools": {},
            "overall": "failed"
        }
        
        try:
            if not self._initialized:
                self.initialize()
            
            # 测试size工具
            size_parser = self.get_size_parser()
            size_version = size_parser.get_version()
            results["tools"]["size"] = {
                "available": True,
                "version": size_version,
                "path": size_parser.tool_path
            }
            
            # 测试readelf工具（如果可用）
            readelf_parser = self.get_readelf_parser()
            if readelf_parser:
                readelf_version = readelf_parser.get_version()
                results["tools"]["readelf"] = {
                    "available": True,
                    "version": readelf_version,
                    "path": readelf_parser.tool_path
                }
            else:
                results["tools"]["readelf"] = {
                    "available": False,
                    "message": "readelf工具未配置或不可用"
                }
            
            # 测试命令执行（使用/bin/ls作为测试文件）
            test_file = "/bin/ls"
            if Path(test_file).exists():
                try:
                    # size命令应该能处理任何ELF文件
                    stats = size_parser.parse_single(test_file)
                    results["tools"]["size"]["test_passed"] = True
                    results["tools"]["size"]["test_output"] = {
                        "text": stats.text_size,
                        "data": stats.data_size,
                        "bss": stats.bss_size
                    }
                except Exception as e:
                    results["tools"]["size"]["test_passed"] = False
                    results["tools"]["size"]["test_error"] = str(e)
            
            # 确定整体状态
            all_passed = all(
                tool.get("test_passed", True) 
                for tool in results["tools"].values() 
                if tool.get("available", False)
            )
            
            results["overall"] = "passed" if all_passed else "partial"
            if not results["tools"]["size"]["available"]:
                results["overall"] = "failed"
            
            return results
            
        except Exception as e:
            logger.error(f"工具链测试失败: {e}")
            results["error"] = str(e)
            return results
    
    def update_config(self, size_path: str, readelf_path: Optional[str] = None, arch: Optional[str] = None) -> bool:
        """
        更新工具链配置
        
        Args:
            size_path: size工具路径
            readelf_path: readelf工具路径
            arch: 架构
            
        Returns:
            是否更新成功
        """
        try:
            # 更新配置
            success = self.config_manager.update_config(
                toolchain={
                    "size_path": size_path,
                    "readelf_path": readelf_path,
                    "arch": arch
                }
            )
            
            if success:
                # 重新加载配置并重新初始化
                self.config = self.config_manager.load_config()
                self._initialized = False
                self.initialize(force=True)
            
            return success
            
        except Exception as e:
            logger.error(f"更新工具链配置失败: {e}")
            return False