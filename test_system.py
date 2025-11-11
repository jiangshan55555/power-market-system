"""
系统功能测试脚本
测试所有核心功能是否正常工作
"""

import requests
import json
import os
import sys
from pathlib import Path

# 测试配置
BASE_URL = "http://localhost:5000"
TEST_DATA_FILE = "uploads/rawdata_56月.xlsx"

def print_section(title):
    """打印分节标题"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def test_health_check():
    """测试1: 健康检查"""
    print_section("测试1: 健康检查")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 健康检查通过")
            print(f"   状态: {data.get('status')}")
            print(f"   消息: {data.get('message')}")
            return True
        else:
            print(f"❌ 健康检查失败: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 健康检查异常: {str(e)}")
        return False

def test_file_exists():
    """测试2: 数据文件存在性"""
    print_section("测试2: 数据文件存在性")
    
    files_to_check = [
        "data/rawdata_0501.xlsx",
        "data/rawdata_0601.xlsx",
        "uploads/rawdata_56月.xlsx",
        "config/config.json",
        "src/main_prediction.py",
        "src/main_bidding.py"
    ]
    
    all_exist = True
    for file_path in files_to_check:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"✅ {file_path} - {size:,} bytes")
        else:
            print(f"❌ {file_path} - 文件不存在")
            all_exist = False
    
    return all_exist

def test_prediction_api():
    """测试3: 预测API"""
    print_section("测试3: 预测API")
    try:
        print("📡 调用预测API...")
        response = requests.post(
            f"{BASE_URL}/api/predict-original-file",
            timeout=300  # 5分钟超时
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"✅ 预测成功")
                
                # 检查预测结果
                results = data.get('results', [])
                print(f"   预测数据条数: {len(results)}")
                
                # 检查性能指标
                metrics = data.get('performance_metrics', {})
                if metrics:
                    print(f"   性能指标:")
                    for model, model_metrics in metrics.items():
                        if isinstance(model_metrics, dict):
                            mae = model_metrics.get('mae', 'N/A')
                            rmse = model_metrics.get('rmse', 'N/A')
                            r2 = model_metrics.get('r2', 'N/A')
                            print(f"     {model}: MAE={mae}, RMSE={rmse}, R²={r2}")
                
                # 检查输出文件
                output_file = "output/predictions/prediction_results.csv"
                if os.path.exists(output_file):
                    print(f"✅ 预测结果文件已生成: {output_file}")
                else:
                    print(f"⚠️  预测结果文件未找到: {output_file}")
                
                return True
            else:
                print(f"❌ 预测失败: {data.get('error')}")
                return False
        else:
            print(f"❌ API调用失败: HTTP {response.status_code}")
            print(f"   响应: {response.text[:200]}")
            return False
            
    except requests.Timeout:
        print(f"❌ 预测超时（超过5分钟）")
        return False
    except Exception as e:
        print(f"❌ 预测异常: {str(e)}")
        return False

def test_bidding_optimization_api():
    """测试4: 投标优化API"""
    print_section("测试4: 投标优化API")
    
    # 检查预测结果是否存在
    prediction_file = "output/predictions/prediction_results.csv"
    if not os.path.exists(prediction_file):
        print(f"⚠️  跳过投标优化测试: 需要先运行预测")
        return None
    
    try:
        print("📡 调用投标优化API...")
        response = requests.post(
            f"{BASE_URL}/api/bidding/optimize",
            timeout=600  # 10分钟超时
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"✅ 投标优化成功")
                
                # 检查优化结果
                strategy = data.get('strategy', {})
                if strategy:
                    threshold = strategy.get('threshold_price')
                    print(f"   门槛价格: {threshold} CNY/MWh")
                
                # 检查性能统计
                performance = data.get('performance', {})
                if performance:
                    print(f"   优化性能:")
                    print(f"     收敛率: {performance.get('convergence_rate', 'N/A')}")
                    print(f"     平均迭代: {performance.get('avg_iterations', 'N/A')}")
                
                # 检查输出文件
                output_file = "output/bidding/bidding_strategy_grid.csv"
                if os.path.exists(output_file):
                    print(f"✅ 投标策略文件已生成: {output_file}")
                else:
                    print(f"⚠️  投标策略文件未找到: {output_file}")
                
                return True
            else:
                print(f"❌ 投标优化失败: {data.get('error')}")
                return False
        else:
            print(f"❌ API调用失败: HTTP {response.status_code}")
            print(f"   响应: {response.text[:200]}")
            return False
            
    except requests.Timeout:
        print(f"❌ 投标优化超时（超过10分钟）")
        return False
    except Exception as e:
        print(f"❌ 投标优化异常: {str(e)}")
        return False

def main():
    """主测试流程"""
    print("\n" + "🔬 电力市场预测系统 - 完整功能测试".center(60, "="))
    print(f"测试时间: {__import__('datetime').datetime.now()}")
    
    results = {}
    
    # 测试1: 健康检查
    results['health'] = test_health_check()
    
    # 测试2: 文件存在性
    results['files'] = test_file_exists()
    
    # 测试3: 预测功能
    results['prediction'] = test_prediction_api()
    
    # 测试4: 投标优化
    results['optimization'] = test_bidding_optimization_api()
    
    # 总结
    print_section("测试总结")
    passed = sum(1 for v in results.values() if v is True)
    failed = sum(1 for v in results.values() if v is False)
    skipped = sum(1 for v in results.values() if v is None)
    total = len(results)
    
    print(f"✅ 通过: {passed}/{total}")
    print(f"❌ 失败: {failed}/{total}")
    print(f"⚠️  跳过: {skipped}/{total}")
    
    if failed == 0:
        print("\n🎉 所有测试通过！系统运行正常。")
        return 0
    else:
        print("\n⚠️  部分测试失败，请检查上述错误信息。")
        return 1

if __name__ == "__main__":
    sys.exit(main())

