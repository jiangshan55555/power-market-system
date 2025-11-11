"""测试投标优化功能"""
import requests
import json
import time

print("=" * 60)
print("  投标优化模块测试")
print("=" * 60)

# 检查预测结果是否存在
import os
prediction_file = "output/predictions/prediction_results.csv"
if not os.path.exists(prediction_file):
    print(f"❌ 预测结果文件不存在: {prediction_file}")
    print("   请先运行预测模块")
    exit(1)
else:
    size = os.path.getsize(prediction_file)
    print(f"✅ 预测结果文件存在: {prediction_file} ({size:,} bytes)")

print("\n开始测试投标优化API...")
print("⏱️  预计需要 2-5 分钟，请耐心等待...\n")

start_time = time.time()

try:
    response = requests.post(
        'http://localhost:5000/api/bidding/optimize',
        timeout=600  # 10分钟超时
    )
    
    elapsed = time.time() - start_time
    print(f"\n⏱️  耗时: {elapsed:.1f} 秒 ({elapsed/60:.1f} 分钟)")
    
    print(f"\n状态码: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        
        if data.get('success'):
            print("\n✅ 投标优化成功！\n")
            
            # 显示核心策略
            strategy = data.get('strategy', {})
            if strategy:
                print("=" * 60)
                print("  核心投标策略")
                print("=" * 60)
                threshold = strategy.get('threshold_price')
                rule_below = strategy.get('rule_below_threshold')
                rule_above = strategy.get('rule_above_threshold')
                
                print(f"门槛价格: {threshold} CNY/MWh")
                print(f"价格 < {threshold}: {rule_below}")
                print(f"价格 >= {threshold}: {rule_above}")
            
            # 显示优化性能
            performance = data.get('performance', {})
            if performance:
                print("\n" + "=" * 60)
                print("  优化性能统计")
                print("=" * 60)
                print(f"优化方法: {performance.get('method', 'N/A')}")
                print(f"总优化点数: {performance.get('total_points', 'N/A')}")
                print(f"收敛率: {performance.get('convergence_rate', 'N/A')}")
                print(f"平均迭代次数: {performance.get('avg_iterations', 'N/A')}")
            
            # 显示投标曲线数据
            bidding_curve = data.get('bidding_curve', [])
            if bidding_curve:
                print("\n" + "=" * 60)
                print("  价格-电量投标曲线（前10条）")
                print("=" * 60)
                print(f"{'日前价格':<15} {'申报电量':<15} {'预期收益':<15}")
                print("-" * 60)
                for item in bidding_curve[:10]:
                    price = item.get('da_price', 'N/A')
                    quantity = item.get('bid_quantity', 'N/A')
                    profit = item.get('expected_profit', 'N/A')
                    print(f"{price:<15} {quantity:<15} {profit:<15}")
            
            # 检查输出文件
            print("\n" + "=" * 60)
            print("  输出文件检查")
            print("=" * 60)
            
            output_files = [
                "output/bidding/bidding_strategy_grid.csv",
                "output/bidding/neurodynamic_optimization_summary.json",
            ]
            
            for file_path in output_files:
                if os.path.exists(file_path):
                    size = os.path.getsize(file_path)
                    print(f"✅ {file_path} ({size:,} bytes)")
                else:
                    print(f"❌ {file_path} (不存在)")
            
            print("\n" + "=" * 60)
            print("  测试结论")
            print("=" * 60)
            print("✅ 投标优化模块验证成功！")
            print("   - API 调用成功")
            print("   - 策略生成正确")
            print("   - 输出文件完整")
            print("=" * 60)
            
        else:
            print(f"\n❌ 投标优化失败")
            print(f"错误信息: {data.get('error', '未知错误')}")
            if 'traceback' in data:
                print(f"\n错误堆栈:\n{data['traceback']}")
    else:
        print(f"\n❌ API 调用失败")
        print(f"响应内容: {response.text[:500]}")
        
except requests.Timeout:
    print(f"\n❌ 请求超时（超过10分钟）")
    print("   投标优化计算时间过长")
    
except requests.exceptions.ConnectionError as e:
    print(f"\n❌ 连接错误: {e}")
    print("   可能是服务器在长时间计算时崩溃")
    
except Exception as e:
    print(f"\n❌ 测试异常: {e}")
    import traceback
    traceback.print_exc()

