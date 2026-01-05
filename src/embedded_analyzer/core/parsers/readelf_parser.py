"""
readelf命令解析器
"""
import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from .base_parser import BaseParser
from ..exceptions import ParserError
from ..models.statistics_models import SegmentInfo, SegmentType

logger = logging.getLogger(__name__)


class ReadelfParser(BaseParser):
    """readelf命令解析器"""
    
    def __init__(self, tool_path: str, timeout: int = 30):
        super().__init__(tool_path, timeout)
        self._version_cache: Optional[str] = None
    
    def get_version(self) -> str:
        """获取readelf版本"""
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
    
    def get_sections(self, file_path: str) -> List[SegmentInfo]:
        """
        获取ELF文件的所有段
        
        Args:
            file_path: ELF文件路径
            
        Returns:
            段信息列表
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        # 使用readelf -S获取段信息
        stdout, stderr = self.execute_command(["-S", str(path)])
        
        try:
            return self._parse_sections_output(stdout)
        except Exception as e:
            raise ParserError("ReadelfParser", f"解析段信息失败: {e}", stdout)
    
    def get_symbols(self, file_path: str) -> List[Dict[str, Any]]:
        """
        获取ELF文件的符号表
        
        Args:
            file_path: ELF文件路径
            
        Returns:
            符号信息列表
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        # 使用readelf -s获取符号表
        stdout, stderr = self.execute_command(["-s", str(path)])
        
        try:
            return self._parse_symbols_output(stdout)
        except Exception as e:
            raise ParserError("ReadelfParser", f"解析符号表失败: {e}", stdout)
    
    def _parse_sections_output(self, output: str) -> List[SegmentInfo]:
        """解析段信息输出"""
        lines = output.strip().split('\n')
        sections = []
        
        # 查找段表开始位置
        start_index = -1
        for i, line in enumerate(lines):
            if "Section Headers:" in line:
                start_index = i + 2  # 跳过标题和分隔线
                break
        
        if start_index == -1:
            raise ParserError("ReadelfParser", "未找到段表", output)
        
        # 解析每个段
        i = start_index
        while i < len(lines):
            line = lines[i].strip()
            if not line or line.startswith("Key to Flags") or line.startswith("Elf file type"):
                break
            
            # 检查是否是段行（包含方括号中的数字）
            if re.search(r'\[\s*\d+\]', line):
                section = self._parse_section_line(line)
                if section:
                    sections.append(section)
            
            i += 1
        
        return sections
    
    def _parse_section_line(self, line: str) -> Optional[SegmentInfo]:
        """解析单个段行"""
        # 示例行: "[ 1] .text             PROGBITS        00000000 000034 0001e4 00  AX  0   0  4"
        pattern = r'\[\s*(\d+)\]\s+(\S+)\s+(\S+)\s+([0-9a-fA-F]+)\s+([0-9a-fA-F]+)\s+([0-9a-fA-F]+)'
        match = re.match(pattern, line)
        
        if not match:
            return None
        
        try:
            section_name = match.group(2).strip()
            section_type = match.group(3)
            size_hex = match.group(6)
            
            # 转换大小
            size = int(size_hex, 16)
            
            # 确定段类型
            segment_type = self._map_section_to_type(section_name, section_type)
            
            return SegmentInfo(
                name=section_name,
                type=segment_type,
                size=size
            )
        except Exception as e:
            logger.warning(f"解析段行失败: {line}, 错误: {e}")
            return None
    
    def _map_section_to_type(self, name: str, elf_type: str) -> SegmentType:
        """映射ELF段类型到我们的类型"""
        name_lower = name.lower()
        
        if name_lower == '.text' or '.text.' in name_lower:
            return SegmentType.TEXT
        elif name_lower == '.data' or '.data.' in name_lower:
            return SegmentType.DATA
        elif name_lower == '.bss' or '.bss.' in name_lower:
            return SegmentType.BSS
        elif name_lower == '.rodata' or '.rodata.' in name_lower:
            return SegmentType.RODATA
        elif name_lower.startswith('.comment'):
            return SegmentType.COMMENT
        elif 'vector' in name_lower or name_lower.startswith('.isr_vector'):
            return SegmentType.VECTOR
        elif 'heap' in name_lower:
            return SegmentType.HEAP
        elif 'stack' in name_lower:
            return SegmentType.STACK
        elif elf_type == 'PROGBITS':
            return SegmentType.TEXT  # 默认代码段
        elif elf_type == 'NOBITS':
            return SegmentType.BSS   # 默认BSS段
        else:
            return SegmentType.OTHER
    
    def _parse_symbols_output(self, output: str) -> List[Dict[str, Any]]:
        """解析符号表输出"""
        lines = output.strip().split('\n')
        symbols = []
        
        # 查找符号表开始位置
        start_index = -1
        for i, line in enumerate(lines):
            if "Symbol table" in line and ".symtab" in line:
                start_index = i + 1  # 下一行开始
                break
        
        if start_index == -1:
            return symbols
        
        # 解析符号行
        for i in range(start_index, len(lines)):
            line = lines[i].strip()
            if not line or line.startswith("Symbol table") or line.startswith("Key to"):
                continue
            
            # 尝试解析符号行
            symbol = self._parse_symbol_line(line)
            if symbol:
                symbols.append(symbol)
        
        return symbols
    
    def _parse_symbol_line(self, line: str) -> Optional[Dict[str, Any]]:
        """解析单个符号行"""
        # 简化解析，只提取基本信息
        parts = line.split()
        if len(parts) < 8:
            return None
        
        try:
            return {
                "value": parts[0],
                "size": parts[1],
                "type": parts[2],
                "bind": parts[3],
                "vis": parts[4],
                "ndx": parts[5],
                "name": ' '.join(parts[6:]) if len(parts) > 6 else ""
            }
        except Exception:
            return None
    
    def parse(self, file_path: str, **kwargs) -> Dict[str, Any]:
        """实现基类抽象方法"""
        sections = self.get_sections(file_path)
        symbols = self.get_symbols(file_path)
        
        return {
            "sections": [section.model_dump() for section in sections],
            "symbols": symbols,
            "section_count": len(sections),
            "symbol_count": len(symbols)
        }
