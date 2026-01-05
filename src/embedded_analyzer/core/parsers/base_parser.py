"""
基础命令解析器
"""
import subprocess
import logging
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any
from abc import ABC, abstractmethod
from ..exceptions import CommandExecutionError

logger = logging.getLogger(__name__)


class BaseParser(ABC):
    """基础解析器抽象类"""
    
    def __init__(self, tool_path: str, timeout: int = 30):
        """
        初始化解析器
        
        Args:
            tool_path: 工具路径
            timeout: 命令执行超时时间（秒）
        """
        self.tool_path = Path(tool_path).resolve()
        self.timeout = timeout
        self._validate_tool()
    
    def _validate_tool(self):
        """验证工具是否可用"""
        if not self.tool_path.exists():
            raise FileNotFoundError(f"工具不存在: {self.tool_path}")
        if not self.tool_path.is_file():
            raise ValueError(f"不是可执行文件: {self.tool_path}")
    
    def execute_command(self, args: List[str], cwd: Optional[Path] = None) -> Tuple[str, str]:
        """
        执行命令并返回输出
        
        Args:
            args: 命令参数列表
            cwd: 工作目录
            
        Returns:
            (stdout, stderr) 元组
        """
        cmd = [str(self.tool_path)] + args
        
        logger.debug(f"执行命令: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                encoding='utf-8',
                errors='replace'  # 替换无法解码的字符
            )
            
            if result.returncode != 0:
                raise CommandExecutionError(
                    command=' '.join(cmd),
                    stderr=result.stderr,
                    returncode=result.returncode
                )
            
            return result.stdout, result.stderr
            
        except subprocess.TimeoutExpired as e:
            logger.error(f"命令执行超时: {e}")
            raise CommandExecutionError(
                command=' '.join(cmd),
                stderr="命令执行超时",
                returncode=-1
            )
        except Exception as e:
            logger.error(f"命令执行异常: {e}")
            raise CommandExecutionError(
                command=' '.join(cmd),
                stderr=str(e),
                returncode=-1
            )
    
    @abstractmethod
    def parse(self, file_path: str, **kwargs) -> Dict[str, Any]:
        """
        解析文件
        
        Args:
            file_path: 要解析的文件路径
            **kwargs: 额外参数
            
        Returns:
            解析结果字典
        """
        pass
    
    @abstractmethod
    def get_version(self) -> str:
        """
        获取工具版本
        
        Returns:
            版本字符串
        """
        pass
