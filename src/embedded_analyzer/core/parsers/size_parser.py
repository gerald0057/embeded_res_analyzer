"""
size命令解析器
"""
import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from .base_parser import BaseParser
from ..exceptions import ParserError, InvalidObjectFileError
from ..models.statistics_models import ModuleStatistics, SegmentType

logger = logging.getLogger(__name__)


class SizeParser(BaseParser):
    """size命令解析器"""
    
    def __init__(self, tool_path: str, timeout: int = 30):
        super().__init__(tool_path, timeout)
        self._version_cache: Optional[str] = None
    
    def get_version(self) -> str:
        """获取size版本"""
        if self._version_cache:
            return self._version_cache
        
        try:
            stdout, _ = self.execute_command(["--version"])
            # 提取版本信息
            match = re.search(r'(\d+\.\d+(\.\d+)*)', stdout)
            if match:
                self._version_cache = match.group(1)
            else:
                self._version_cache = "unknown"
        except Exception as e:
            logger.warning(f"获取版本失败: {e}")
            self._version_cache = "unknown"
        
        return self._version_cache
    
    def parse_single(self, file_path: str) -> ModuleStatistics:
        """
        解析单个文件
        
        Args:
            file_path: 目标文件路径
            
        Returns:
            ModuleStatistics对象
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        # 使用size命令获取信息
        stdout, stderr = self.execute_command(["-t", str(path)])
        
        # 解析输出
        try:
            return self._parse_output(str(path), stdout)
        except Exception as e:
            raise ParserError("SizeParser", f"解析失败: {e}", stdout)
    
    def parse_multiple(self, file_paths: List[str]) -> Dict[str, ModuleStatistics]:
        """
        解析多个文件
        
        Args:
            file_paths: 目标文件路径列表
            
        Returns:
            文件名到统计信息的映射
        """
        if not file_paths:
            return {}
        
        # 构建命令参数
        args = ["-t"] + [str(Path(fp)) for fp in file_paths]
        
        try:
            stdout, stderr = self.execute_command(args)
            return self._parse_multi_output(file_paths, stdout)
        except Exception as e:
            raise ParserError("SizeParser", f"批量解析失败: {e}", stdout)
    
    def parse_directory(self, directory: str, pattern: str = "*.o", recursive: bool = False) -> Dict[str, ModuleStatistics]:
        """
        解析目录下的文件
        
        Args:
            directory: 目录路径
            pattern: 文件匹配模式
            recursive: 是否递归查找
            
        Returns:
            文件名到统计信息的映射
        """
        from ..utils.file_utils import find_object_files
        
        dir_path = Path(directory)
        if not dir_path.exists():
            raise FileNotFoundError(f"目录不存在: {directory}")
        
        # 查找文件
        files = find_object_files(directory, pattern, recursive)
        if not files:
            logger.warning(f"目录中没有找到匹配的文件: {directory}, 模式: {pattern}")
            return {}
        
        return self.parse_multiple(files)
    
    def _parse_output(self, file_path: str, output: str) -> ModuleStatistics:
        """
        解析单个文件的size输出
        
        示例输出:
           text    data     bss     dec     hex filename
           1124       0       0    1124     464 test.o
        """
        lines = output.strip().split('\n')
        if len(lines) < 2:
            raise ParserError("SizeParser", "输出格式错误", output)
        
        # 解析标题行
        header_line = lines[0].strip()
        # 使用更灵活的正则匹配列
        if not re.search(r'text\s+data\s+bss', header_line, re.IGNORECASE):
            raise ParserError("SizeParser", "输出标题格式错误", output)
        
        # 查找数据行（跳过标题）
        data_lines = []
        for line in lines[1:]:
            line = line.strip()
            if line and not line.startswith('---'):  # 跳过分隔线
                data_lines.append(line)
        
        if not data_lines:
            raise ParserError("SizeParser", "没有找到数据行", output)
        
        # 解析数据行
        path_obj = Path(file_path)
        for line in data_lines:
            # 检查是否是该文件的行
            if path_obj.name in line or str(path_obj) in line:
                return self._parse_data_line(str(path_obj), line)
        
        # 如果没有找到具体文件的行，尝试解析第一行数据
        return self._parse_data_line(str(path_obj), data_lines[0])
    
    def _parse_data_line(self, file_path: str, line: str) -> ModuleStatistics:
        """解析数据行"""
        # 使用正则表达式匹配数字和文件名
        # 格式: 数字 数字 数字 数字 十六进制 文件名
        pattern = r'(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+([0-9a-fA-F]+)\s+(.+)'
        match = re.match(pattern, line.strip())
        
        if not match:
            # 尝试更宽松的匹配
            parts = line.split()
            if len(parts) >= 6:
                try:
                    text = int(parts[0])
                    data = int(parts[1])
                    bss = int(parts[2])
                    total = int(parts[3])
                    # 文件名可能是多个部分（包含空格）
                    filename = ' '.join(parts[5:])
                    
                    # 验证文件名匹配
                    path_obj = Path(file_path)
                    if path_obj.name in filename or str(path_obj) in filename:
                        return ModuleStatistics(
                            file_path=file_path,
                            file_name=path_obj.name,
                            text_size=text,
                            data_size=data,
                            bss_size=bss,
                            total_size=total
                        )
                except (ValueError, IndexError):
                    pass
        
            raise ParserError("SizeParser", f"无法解析数据行: {line}", line)
        
        text = int(match.group(1))
        data = int(match.group(2))
        bss = int(match.group(3))
        total = int(match.group(4))
        
        path_obj = Path(file_path)
        
        return ModuleStatistics(
            file_path=file_path,
            file_name=path_obj.name,
            text_size=text,
            data_size=data,
            bss_size=bss,
            total_size=total
        )
    
    def _parse_multi_output(self, file_paths: List[str], output: str) -> Dict[str, ModuleStatistics]:
        """解析多个文件的输出"""
        lines = output.strip().split('\n')
        if len(lines) < 2:
            raise ParserError("SizeParser", "输出格式错误", output)
        
        # 跳过标题行
        data_lines = lines[1:]
        
        results = {}
        for file_path in file_paths:
            path_obj = Path(file_path)
            found = False
            
            for line in data_lines:
                line = line.strip()
                if not line:
                    continue
                    
                # 检查是否是该文件的行
                if path_obj.name in line or str(path_obj) in line:
                    try:
                        stats = self._parse_data_line(file_path, line)
                        results[file_path] = stats
                        found = True
                        break
                    except Exception as e:
                        logger.warning(f"解析文件失败 {file_path}: {e}")
                        # 创建无效的统计对象
                        results[file_path] = ModuleStatistics(
                            file_path=file_path,
                            file_name=path_obj.name,
                            is_valid=False,
                            error_message=str(e)
                        )
                        found = True
                        break
            
            if not found:
                logger.warning(f"未找到文件的统计信息: {file_path}")
                results[file_path] = ModuleStatistics(
                    file_path=file_path,
                    file_name=path_obj.name,
                    is_valid=False,
                    error_message="未找到统计信息"
                )
        
        return results
    
    def parse(self, file_path: str, **kwargs) -> Dict[str, Any]:
        """实现基类抽象方法"""
        stats = self.parse_single(file_path)
        return stats.model_dump()
