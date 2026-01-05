"""
配置管理器 - 更新为Pydantic V2
"""
import json
import yaml
from pathlib import Path
from typing import Optional, Any, Dict
import logging
from ..core.models.config_models import AppConfig, ToolchainConfig

logger = logging.getLogger(__name__)


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_dir: Optional[Path] = None):
        """
        初始化配置管理器
        
        Args:
            config_dir: 配置目录，默认为 ~/.config/embedded-analyzer
        """
        if config_dir is None:
            config_dir = self.get_default_config_dir()
        
        self.config_dir = Path(config_dir)
        self.config_file = self.config_dir / "config.yaml"
        self.workspaces_dir = self.config_dir / "workspaces"
        
        # 确保目录存在
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.workspaces_dir.mkdir(parents=True, exist_ok=True)
        
        self._config: Optional[AppConfig] = None
    
    @staticmethod
    def get_default_config_dir() -> Path:
        """获取默认配置目录（跨平台）"""
        home = Path.home()
        
        import platform
        system = platform.system()
        
        if system == "Windows":
            return home / "AppData" / "Roaming" / "embedded-analyzer"
        elif system == "Darwin":  # macOS
            return home / "Library" / "Application Support" / "embedded-analyzer"
        else:  # Linux/Unix
            return home / ".config" / "embedded-analyzer"
    
    def get_default_config(self) -> AppConfig:
        """获取默认配置"""
        return AppConfig(
            toolchain=ToolchainConfig(
                size_path="",  # 空路径，需要用户配置
                readelf_path=None,
                arch=None
            )
        )
    
    def load_config(self) -> AppConfig:
        """加载配置"""
        if self._config is not None:
            return self._config
        
        if not self.config_file.exists():
            logger.info("配置文件不存在，创建默认配置")
            self._config = self.get_default_config()
            self.save_config(self._config)
            return self._config
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            # 验证配置版本
            version = config_data.get('version', '1.0.0')
            if version != '1.0.0':
                logger.warning(f"配置版本不匹配: {version}，尝试迁移或使用默认配置")
                # TODO: 实现配置迁移逻辑
                self._config = self.get_default_config()
            else:
                self._config = AppConfig(**config_data)
            
            logger.info(f"配置加载成功: {self.config_file}")
            return self._config
            
        except Exception as e:
            logger.error(f"加载配置失败: {e}")
            # 创建备份并返回默认配置
            if self.config_file.exists():
                backup_file = self.config_file.with_suffix('.yaml.bak')
                self.config_file.rename(backup_file)
                logger.warning(f"原配置文件已备份到: {backup_file}")
            
            self._config = self.get_default_config()
            self.save_config(self._config)
            return self._config
    
    def save_config(self, config: AppConfig) -> bool:
        """保存配置"""
        try:
            # 更新配置版本
            config.version = "1.0.0"
            
            # 转换为字典 - 使用model_dump
            config_dict = config.model_dump()
            
            # 保存为YAML
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True, indent=2)
            
            self._config = config
            logger.info(f"配置保存成功: {self.config_file}")
            return True
            
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
            return False
    
    def update_config(self, **kwargs) -> bool:
        """更新配置（部分更新）"""
        try:
            config = self.load_config()
            
            # 更新toolchain配置
            if 'toolchain' in kwargs:
                # 获取当前配置字典
                toolchain_dict = config.toolchain.model_dump()
                # 合并更新
                toolchain_dict.update(kwargs['toolchain'])
                # 创建新对象
                config.toolchain = ToolchainConfig(**toolchain_dict)
            
            # 更新ui配置
            if 'ui' in kwargs:
                ui_dict = config.ui.model_dump()
                ui_dict.update(kwargs['ui'])
                # 对于嵌套模型，可以直接创建新对象
                from ..core.models.config_models import UIConfig
                config.ui = UIConfig(**ui_dict)
            
            # 更新analysis配置
            if 'analysis' in kwargs:
                analysis_dict = config.analysis.model_dump()
                analysis_dict.update(kwargs['analysis'])
                from ..core.models.config_models import AnalysisConfig
                config.analysis = AnalysisConfig(**analysis_dict)
            
            return self.save_config(config)
            
        except Exception as e:
            logger.error(f"更新配置失败: {e}")
            return False
    
    def get_workspace_path(self, workspace_name: str = "default") -> Path:
        """获取工作区文件路径"""
        return self.workspaces_dir / f"{workspace_name}.json"
    
    def save_workspace(self, workspace_data: Dict, workspace_name: str = "default") -> bool:
        """保存工作区"""
        try:
            workspace_file = self.get_workspace_path(workspace_name)
            with open(workspace_file, 'w', encoding='utf-8') as f:
                json.dump(workspace_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"保存工作区失败: {e}")
            return False
    
    def load_workspace(self, workspace_name: str = "default") -> Optional[Dict]:
        """加载工作区"""
        try:
            workspace_file = self.get_workspace_path(workspace_name)
            if not workspace_file.exists():
                return None
            
            with open(workspace_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载工作区失败: {e}")
            return None