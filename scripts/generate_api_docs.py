#!/usr/bin/env python3
"""
生成API文档
"""
import json
from pathlib import Path
import sys

# 添加项目路径
project_root = Path(__file__).parent.parent
src_dir = project_root / "src"
sys.path.insert(0, str(src_dir))

from embedded_analyzer.api.main import app

def generate_openapi_spec():
    """生成OpenAPI规范"""
    openapi_spec = app.openapi()
    
    # 保存为JSON文件
    docs_dir = project_root / "docs"
    docs_dir.mkdir(exist_ok=True)
    
    spec_path = docs_dir / "openapi.json"
    with open(spec_path, 'w', encoding='utf-8') as f:
        json.dump(openapi_spec, f, indent=2, ensure_ascii=False)
    
    print(f"✅ OpenAPI规范已生成: {spec_path}")
    
    # 统计API信息
    endpoints = []
    for route in app.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            for method in route.methods:
                endpoints.append({
                    'method': method,
                    'path': route.path,
                    'name': getattr(route, 'name', '未命名'),
                    'tags': getattr(route, 'tags', [])
                })
    
    print(f"\n📊 API统计:")
    print(f"  总端点数: {len(endpoints)}")
    
    # 按标签分组
    tags = {}
    for endpoint in endpoints:
        for tag in endpoint['tags']:
            if tag not in tags:
                tags[tag] = 0
            tags[tag] += 1
    
    for tag, count in tags.items():
        print(f"  {tag}: {count}个端点")
    
    return spec_path

if __name__ == "__main__":
    spec_path = generate_openapi_spec()
    print(f"\n📚 可以在浏览器中查看API文档:")
    print(f"  1. 启动服务: python run.py")
    print(f"  2. 访问: http://localhost:8000/docs")
    print(f"  3. 或访问: http://localhost:8000/redoc")
