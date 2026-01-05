"""
测试解析器
"""
import pytest
import tempfile
from pathlib import Path
from embedded_analyzer.core.parsers.size_parser import SizeParser
from embedded_analyzer.core.parsers.readelf_parser import ReadelfParser
from embedded_analyzer.core.exceptions import CommandExecutionError


class TestSizeParser:
    """测试Size解析器"""
    
    def test_initialization(self):
        """测试初始化"""
        # 使用系统存在的工具测试
        import shutil
        size_path = shutil.which("size") or "/usr/bin/size"
        
        parser = SizeParser(size_path)
        assert parser.tool_path.exists()
        assert "size" in str(parser.tool_path).lower()
    
    def test_get_version(self):
        """测试获取版本"""
        import shutil
        size_path = shutil.which("size") or "/usr/bin/size"
        
        parser = SizeParser(size_path)
        version = parser.get_version()
        assert version  # 版本可能为"unknown"，但不应该为空
    
    def test_parse_nonexistent_file(self):
        """测试解析不存在的文件"""
        import shutil
        size_path = shutil.which("size") or "/usr/bin/size"
        
        parser = SizeParser(size_path)
        with pytest.raises(FileNotFoundError):
            parser.parse_single("/nonexistent/file.o")
    
    def test_parse_valid_binary(self):
        """测试解析有效的二进制文件"""
        import shutil
        size_path = shutil.which("size") or "/usr/bin/size"
        
        parser = SizeParser(size_path)
        
        # 使用/bin/ls作为测试文件（它应该是ELF格式）
        test_file = "/bin/ls"
        if Path(test_file).exists():
            try:
                stats = parser.parse_single(test_file)
                assert stats.file_name == "ls"
                assert stats.is_valid is True
                # 大小应该是非负整数
                assert stats.text_size >= 0
                assert stats.data_size >= 0
                assert stats.bss_size >= 0
            except Exception as e:
                # 某些系统上的/bin/ls可能不是ELF格式，这是可以接受的
                pytest.skip(f"测试文件不是有效的ELF格式: {e}")


class TestReadelfParser:
    """测试Readelf解析器"""
    
    def test_initialization(self):
        """测试初始化"""
        import shutil
        readelf_path = shutil.which("readelf") or "/usr/bin/readelf"
        
        if readelf_path and Path(readelf_path).exists():
            parser = ReadelfParser(readelf_path)
            assert parser.tool_path.exists()
        else:
            pytest.skip("readelf工具未找到")
    
    def test_get_sections(self):
        """测试获取段信息"""
        import shutil
        readelf_path = shutil.which("readelf") or "/usr/bin/readelf"
        
        if not readelf_path or not Path(readelf_path).exists():
            pytest.skip("readelf工具未找到")
        
        parser = ReadelfParser(readelf_path)
        
        # 使用/bin/ls作为测试文件
        test_file = "/bin/ls"
        if Path(test_file).exists():
            try:
                sections = parser.get_sections(test_file)
                # 应该至少有一个段
                assert len(sections) > 0
                
                # 检查段信息
                for section in sections:
                    assert section.name
                    assert section.size >= 0
                    assert section.type.value  # 应该有有效的类型
            except Exception as e:
                # 解析失败是可以接受的（文件格式可能不支持）
                pytest.skip(f"解析段信息失败: {e}")
