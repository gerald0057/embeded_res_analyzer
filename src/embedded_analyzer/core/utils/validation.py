"""
验证工具函数
"""
import subprocess
import shutil
from pathlib import Path
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


def validate_toolchain(tool_path: str, expected_tool: str = "size") -> Tuple[bool, str]:
    """
    验证工具链
    
    Args:
        tool_path: 工具路径
        expected_tool: 期望的工具名称
    
    Returns:
        (是否有效, 错误信息或版本信息)
    """
    try:
        path = Path(tool_path)
        
        # 检查文件是否存在
        if not path.exists():
            return False, f"文件不存在: {tool_path}"
        
        # 检查是否可执行
        if not path.is_file() or not os.access(path, os.X_OK):
            return False, f"文件不可执行: {tool_path}"
        
        # 检查工具版本
        try:
            result = subprocess.run(
                [str(path), "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                version_output = result.stdout.strip()[:100]  # 取前100字符
                return True, f"工具验证成功: {version_output}"
            else:
                # 尝试其他参数
                result = subprocess.run(
                    [str(path), "-V"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    return True, f"工具验证成功: {result.stdout.strip()[:100]}"
                else:
                    return False, f"工具执行失败: {result.stderr[:200]}"
                    
        except subprocess.TimeoutExpired:
            return False, "工具执行超时"
        except Exception as e:
            return False, f"工具验证异常: {str(e)}"
            
    except Exception as e:
        logger.error(f"工具链验证失败: {e}")
        return False, f"验证过程异常: {str(e)}"


def find_tool_in_path(tool_name: str) -> Optional[str]:
    """在系统PATH中查找工具"""
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
        ""
    ]
    
    for prefix in common_prefixes:
        full_name = f"{prefix}{tool_name}"
        tool_path = shutil.which(full_name)
        if tool_path:
            return tool_path
    
    return None
