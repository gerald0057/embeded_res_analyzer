"""
测试序列化功能
"""
import json
from datetime import datetime
from embedded_analyzer.core.models.statistics_models import ModuleStatistics, SegmentInfo, SegmentType


def test_model_serialization():
    """测试模型序列化"""
    stats = ModuleStatistics(
        file_path="/test/test.o",
        file_name="test.o",
        text_size=1024,
        data_size=256,
        bss_size=512
    )
    
    # 测试model_dump
    data = stats.model_dump()
    assert "file_name" in data
    assert data["text_size"] == 1024
    assert isinstance(data["analyzed_at"], str)  # 应该是ISO格式字符串
    
    # 测试JSON序列化
    json_str = stats.model_dump_json()
    parsed = json.loads(json_str)
    assert parsed["file_name"] == "test.o"
    
    # 验证日期是字符串格式
    assert isinstance(parsed["analyzed_at"], str)
    # 验证格式是ISO格式
    datetime.fromisoformat(parsed["analyzed_at"])  # 应该不会抛出异常


def test_segment_serialization():
    """测试段信息序列化"""
    segment = SegmentInfo(
        name=".text",
        type=SegmentType.TEXT,
        size=4096
    )
    
    data = segment.model_dump()
    assert data["name"] == ".text"
    assert data["type"] == "text"
    assert data["size"] == 4096


def test_complex_serialization():
    """测试复杂序列化（包含SegmentInfo列表）"""
    segments = [
        SegmentInfo(name=".text", type=SegmentType.TEXT, size=1024),
        SegmentInfo(name=".data", type=SegmentType.DATA, size=256),
    ]
    
    stats = ModuleStatistics(
        file_path="/test/test.o",
        file_name="test.o",
        text_size=1024,
        data_size=256,
        bss_size=512,
        detailed_segments=segments
    )
    
    data = stats.model_dump()
    assert len(data["detailed_segments"]) == 2
    assert data["detailed_segments"][0]["name"] == ".text"
    assert data["detailed_segments"][1]["type"] == "data"