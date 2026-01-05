#!/usr/bin/env python3
"""
测试所有API端点
"""
import sys
import os
from pathlib import Path
import threading
import time
import requests
import json

# 添加项目路径
project_root = Path(__file__).parent
src_dir = project_root / "src"
sys.path.insert(0, str(src_dir))

import uvicorn

def start_server():
    """启动测试服务器"""
    uvicorn.run(
        "embedded_analyzer.api.main:app",
        host="127.0.0.1",
        port=8001,
        log_level="warning",
        access_log=False
    )

def print_result(name: str, success: bool, details: str = ""):
    """打印测试结果"""
    icon = "✅" if success else "❌"
    print(f"{icon} {name}")
    if details and not success:
        print(f"   详情: {details}")

def test_health():
    """测试健康检查"""
    try:
        response = requests.get("http://127.0.0.1:8001/api/health")
        if response.status_code == 200:
            data = response.json()
            return True, f"服务状态: {data.get('status', 'unknown')}"
        return False, f"状态码: {response.status_code}"
    except Exception as e:
        return False, str(e)

def test_config_get():
    """测试获取配置"""
    try:
        response = requests.get("http://127.0.0.1:8001/config/")
        if response.status_code == 200:
            config = response.json()
            return True, f"配置版本: {config.get('version', 'unknown')}"
        return False, f"状态码: {response.status_code}"
    except Exception as e:
        return False, str(e)

def test_autodetect():
    """测试自动检测"""
    try:
        response = requests.get("http://127.0.0.1:8001/config/toolchain/autodetect")
        if response.status_code == 200:
            result = response.json()
            size_found = result.get('size', {}).get('found', False)
            return True, f"检测到size工具: {size_found}"
        return False, f"状态码: {response.status_code}"
    except Exception as e:
        return False, str(e)

def test_toolchain_test():
    """测试工具链测试"""
    try:
        response = requests.post("http://127.0.0.1:8001/config/toolchain/test")
        if response.status_code == 200:
            result = response.json()
            overall = result.get('overall', 'unknown')
            return True, f"工具链状态: {overall}"
        return False, f"状态码: {response.status_code}"
    except Exception as e:
        return False, str(e)

def test_analysis_status():
    """测试分析状态"""
    try:
        response = requests.get("http://127.0.0.1:8001/analysis/status")
        if response.status_code == 200:
            result = response.json()
            initialized = result.get('initialized', False)
            return True, f"分析器初始化: {initialized}"
        return False, f"状态码: {response.status_code}"
    except Exception as e:
        return False, str(e)

def test_update_toolchain():
    """测试更新工具链"""
    try:
        # 先获取当前配置
        response = requests.get("http://127.0.0.1:8001/config/")
        if response.status_code != 200:
            return False, "无法获取当前配置"
        
        current_config = response.json()
        current_toolchain = current_config.get('toolchain', {})
        
        # 尝试使用系统size工具
        import shutil
        size_path = shutil.which("size") or "/usr/bin/size"
        
        update_data = {
            "size_path": size_path,
            "readelf_path": current_toolchain.get('readelf_path'),
            "arch": current_toolchain.get('arch', 'x86_64')
        }
        
        response = requests.put(
            "http://127.0.0.1:8001/config/toolchain",
            json=update_data
        )
        
        if response.status_code == 200:
            return True, "工具链配置更新成功"
        return False, f"状态码: {response.status_code}"
        
    except Exception as e:
        return False, str(e)

def run_all_tests():
    """运行所有测试"""
    print("🧪 开始API测试\n")
    
    tests = [
        ("健康检查", test_health),
        ("获取配置", test_config_get),
        ("自动检测工具链", test_autodetect),
        ("测试工具链", test_toolchain_test),
        ("分析状态", test_analysis_status),
        ("更新工具链", test_update_toolchain),
    ]
    
    results = []
    for name, test_func in tests:
        success, details = test_func()
        results.append((name, success, details))
        print_result(name, success, details)
        time.sleep(0.5)  # 避免请求过快
    
    print("\n" + "="*50)
    print("📊 测试结果汇总:")
    
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    for name, success, details in results:
        status = "通过" if success else "失败"
        print(f"  {name}: {status}")
    
    print(f"\n🎯 通过率: {passed}/{total} ({passed/total*100:.0f}%)")
    
    if passed == total:
        print("\n✨ 所有API测试通过！")
        return True
    else:
        print("\n⚠️  部分测试失败，请检查日志。")
        return False

if __name__ == "__main__":
    # 在后台启动服务器
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    
    # 等待服务器启动
    print("🚀 启动测试服务器...")
    time.sleep(3)
    
    # 运行测试
    try:
        success = run_all_tests()
        if success:
            print("\n🔗 可以访问以下地址:")
            print("   API文档: http://127.0.0.1:8001/docs")
            print("   ReDoc文档: http://127.0.0.1:8001/redoc")
            print("\n按 Ctrl+C 停止服务器")
            
            # 保持服务器运行
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n👋 停止服务器")
        else:
            print("\n❌ 测试失败，请检查错误信息")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        sys.exit(1)
