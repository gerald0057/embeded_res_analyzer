"""
核心模块
"""
# 注意：不要在这里导入会产生循环依赖的模块
# 改为在需要时单独导入

# 这些导入是安全的，因为它们不依赖config模块
from . import models
from . import parsers
from . import utils
from .exceptions import (
    ToolchainError,
    CommandExecutionError,
    ParserError,
    ToolNotFoundError,
    InvalidObjectFileError,
    SegmentParseError
)

# 注意：ToolchainManager 现在不在这里导入，因为它依赖config模块
# 用户需要时应该直接从 embedded_analyzer.core.toolchain_manager 导入

__all__ = [
    'models',
    'parsers', 
    'utils',
    'ToolchainError',
    'CommandExecutionError',
    'ParserError', 
    'ToolNotFoundError',
    'InvalidObjectFileError',
    'SegmentParseError',
    # 'ToolchainManager'  # 移除，避免循环导入
]