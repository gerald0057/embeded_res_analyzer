# 技术栈决策文档

## 核心架构
- 后端：FastAPI (Python 3.8+)
- 前端：原生HTML + Alpine.js + Tailwind CSS
- 通信：RESTful API
- 打包：PyInstaller (单文件模式)

## 开发环境要求
- Python 3.8+
- 现代浏览器（Chrome 90+, Firefox 88+, Safari 14+）
- 推荐编辑器：VSCode

## 目录结构规范
embedded-resource-analyzer/
├── backend/           # Python后端代码
│   ├── app/          # FastAPI应用
│   ├── core/         # 核心业务逻辑
│   └── utils/        # 工具函数
├── frontend/         # 前端代码
│   ├── static/       # 静态资源
│   └── templates/    # HTML模板
├── docs/             # 文档
└── scripts/          # 构建脚本

## 配置存储
- 用户配置：~/.config/embedded-analyzer/
- 工作区文件：独立存储，支持导入导出
