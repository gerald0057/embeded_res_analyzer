"""
延迟导入工具
"""


class LazyImport:
    """延迟导入类"""
    
    def __init__(self, module_name: str, class_name: str = None):
        """
        初始化延迟导入
        
        Args:
            module_name: 模块名
            class_name: 类名（如果只导入一个类）
        """
        self.module_name = module_name
        self.class_name = class_name
        self._module = None
        self._class = None
    
    def __getattr__(self, name):
        if self._module is None:
            self._module = __import__(self.module_name, fromlist=[''])
        
        if self.class_name:
            if self._class is None:
                self._class = getattr(self._module, self.class_name)
            return getattr(self._class, name)
        else:
            return getattr(self._module, name)
    
    def __call__(self, *args, **kwargs):
        if self.class_name:
            if self._class is None:
                module = __import__(self.module_name, fromlist=[''])
                self._class = getattr(module, self.class_name)
            return self._class(*args, **kwargs)
        raise TypeError(f"'{self.__class__.__name__}' object is not callable")


# 创建延迟导入实例
ConfigManager = LazyImport('embedded_analyzer.config.manager', 'ConfigManager')
ToolchainManager = LazyImport('embedded_analyzer.core.toolchain_manager', 'ToolchainManager')
