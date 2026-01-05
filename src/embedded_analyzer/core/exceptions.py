"""
工具链解析相关异常
"""


class ToolchainError(Exception):
    """工具链基础异常"""
    pass


class CommandExecutionError(ToolchainError):
    """命令执行错误"""
    def __init__(self, command: str, stderr: str, returncode: int):
        self.command = command
        self.stderr = stderr
        self.returncode = returncode
        message = f"命令执行失败: {command}\n返回码: {returncode}\n错误: {stderr[:200]}"
        super().__init__(message)


class ParserError(ToolchainError):
    """解析器错误"""
    def __init__(self, parser_name: str, message: str, raw_output: str = ""):
        self.parser_name = parser_name
        self.raw_output = raw_output
        message = f"解析器错误 [{parser_name}]: {message}"
        if raw_output:
            message += f"\n原始输出: {raw_output[:500]}"
        super().__init__(message)


class ToolNotFoundError(ToolchainError):
    """工具未找到错误"""
    def __init__(self, tool_name: str, search_paths: list = None):
        self.tool_name = tool_name
        self.search_paths = search_paths or []
        message = f"工具未找到: {tool_name}"
        if search_paths:
            message += f"\n搜索路径: {search_paths}"
        super().__init__(message)


class InvalidObjectFileError(ToolchainError):
    """无效的目标文件错误"""
    def __init__(self, file_path: str, reason: str):
        self.file_path = file_path
        self.reason = reason
        message = f"无效的目标文件: {file_path}\n原因: {reason}"
        super().__init__(message)


class SegmentParseError(ParserError):
    """段解析错误"""
    pass
