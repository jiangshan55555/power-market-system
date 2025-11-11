#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
投标优化API接口
完全按照原项目的 main_bidding.py 来运行投标优化
"""

import sys
import os
from pathlib import Path
import logging
import traceback
import pandas as pd
import json

# 添加原项目路径到系统路径
CURRENT_DIR = Path(__file__).parent
PROJECT_ROOT = CURRENT_DIR.parent
ORIGINAL_PROJECT_PATH = PROJECT_ROOT.parent / 'power-market-system' / '原来的项目资料'
sys.path.insert(0, str(ORIGINAL_PROJECT_PATH / 'src'))

# 保存原始工作目录
ORIGINAL_CWD = os.getcwd()

def setup_logging():
    """设置日志配置（与原项目一致）"""
    # 确保日志目录存在
    os.makedirs('output/logs', exist_ok=True)

    # 清除现有的日志处理器
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - [%(levelname)s] - %(message)s',
        handlers=[
            logging.FileHandler('output/logs/bidding.log', encoding='utf-8', mode='w'),
            logging.StreamHandler()
        ],
        force=True
    )

def load_config():
    """加载配置文件（与原项目一致）"""
    try:
        # 使用绝对路径
        config_path = os.path.join(os.getcwd(), 'config', 'config.json')
        print(f"尝试加载配置文件: {config_path}")
        print(f"文件是否存在: {os.path.exists(config_path)}")

        print("正在读取配置文件...")
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        print("配置文件解析成功")

        print("正在构建投标配置...")

        # 检查预测结果文件是否存在
        prediction_file = 'output/predictions/prediction_results.csv'
        if not os.path.exists(prediction_file):
            print(f"⚠️ 预测结果文件不存在: {prediction_file}")
            print(f"   当前工作目录: {os.getcwd()}")
            print(f"   请先运行预测模型生成预测结果")
        else:
            print(f"✅ 找到预测结果文件: {prediction_file}")

        # 更新路径配置以适应新的目录结构（与原项目完全一致）
        bidding_config = {
            'INPUT_FILE': prediction_file,
            'OUTPUT_DIR': 'output/bidding',
            'PRICE_GRID_STEP': 1,  # 减小到1元步长，增加精度
            'PRICE_MIN': 350,      # 扩大价格范围
            'PRICE_MAX': 500,
            'COST_PARAMS': {
                'c_g': 380,  # 发电边际成本 (CNY/MWh)
                'c_up': 500, # 上调整成本 (CNY/MWh)
                'c_dn': 300  # 下调整成本 (CNY/MWh)
            },
            'CAPACITY_PARAMS': {
                'P_max': 100, # 最大出力
                'R_up_max': 3, # 最大上调整
                'R_dn_max': 3  # 最大下调整
            },
            'OPTIMIZATION_METHOD': config.get('bidding', {}).get('optimization_method', 'neurodynamic'),
            'NEURODYNAMIC_PARAMS': config.get('bidding', {}).get('neurodynamic_params', {
                'eta_base': 0.1,
                'eta_min': 0.001,
                'max_iter': 500,
                'tolerance': 1e-4,
                'patience': 50,
                'adaptive_grid': True,
                'fine_step': 0.1
            })
        }

        print("投标配置构建完成")
        return bidding_config

    except Exception as e:
        logging.error(f"加载配置文件失败: {e}")
        traceback.print_exc()
        return None

def run_bidding_optimization():
    """
    运行投标优化（完全按照原项目的 main_bidding.py）
    返回: dict 包含优化结果和策略建议
    """
    # 切换到原项目目录
    os.chdir(str(ORIGINAL_PROJECT_PATH))

    try:
        print("\n" + "="*60)
        print("      电力市场投标策略优化系统      ")
        print("="*60)

        # 设置日志
        setup_logging()

        # 加载配置
        print("步骤 1: 开始加载配置...")
        config = load_config()
        if not config:
            print("❌ 配置加载失败")
            return {
                'success': False,
                'error': '配置加载失败'
            }
        print("✅ 配置加载成功")

        # 导入原项目的投标优化模型
        from optimization.bidding_optimizer import BiddingOptimizationModel

        # 检查预测结果文件是否存在
        if not os.path.exists(config['INPUT_FILE']):
            error_msg = f"预测结果文件不存在: {config['INPUT_FILE']}\n请先运行预测程序生成预测结果"
            logging.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }

        # 创建输出目录
        os.makedirs(config['OUTPUT_DIR'], exist_ok=True)
        os.makedirs('output/logs', exist_ok=True)

        # 步骤 1: 初始化投标优化模型
        print("步骤 3: 开始初始化投标优化模型...")
        logging.info("步骤 1: 初始化投标优化模型...")
        optimizer = BiddingOptimizationModel(config)
        print("✅ 投标优化模型初始化成功")

        # 步骤 2: 执行投标策略优化
        method = config.get('OPTIMIZATION_METHOD', 'neurodynamic')
        method_name = "神经动力学自适应网格" if method == 'neurodynamic' else "SciPy"

        print(f"步骤 4: 开始执行{method_name}投标策略优化...")
        logging.info(f"步骤 2: 执行{method_name}投标策略优化...")
        optimizer.run(mode='full', target_date='2025-05-31')
        print("✅ 投标优化运行完成")

        logging.info("✅ 投标策略优化成功完成！")
        logging.info(f"结果已保存到: {config['OUTPUT_DIR']}")

        # 显示主要结果
        if hasattr(optimizer, 'optimization_results') and optimizer.optimization_results:
            results = optimizer.optimization_results
            total_points = len(results)
            converged_points = sum(1 for res in results.values() if res.get('converged', False))

            logging.info("=" * 50)
            logging.info("优化结果摘要:")
            logging.info("=" * 50)
            logging.info(f"优化方法: {method_name}")
            logging.info(f"总优化点数: {total_points}")
            logging.info(f"收敛点数: {converged_points} ({100*converged_points/total_points:.1f}%)")

            if method == 'neurodynamic':
                avg_iter = sum(res.get('iterations', 0) for res in results.values()) / total_points
                logging.info(f"平均迭代次数: {avg_iter:.1f}")

        # 读取优化结果
        print("\n📊 读取优化结果...")
        result_data = _extract_optimization_results(optimizer, config)

        print("\n✅ 投标优化完成！")
        print("="*60)

        return result_data

    except Exception as e:
        error_msg = f"投标优化失败: {str(e)}\n{traceback.format_exc()}"
        logging.error(error_msg)
        print(f"\n❌ 错误: {error_msg}")
        return {
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }
    finally:
        # 恢复原始工作目录
        os.chdir(ORIGINAL_CWD)

def _extract_optimization_results(optimizer, config):
    """
    提取优化结果
    """
    try:
        results = {
            'success': True,
            'strategy': {},
            'summary': {},
            'visualization': {}
        }

        output_dir = config['OUTPUT_DIR']

        # 读取策略网格数据
        grid_file = os.path.join(output_dir, 'bidding_strategy_grid.csv')
        if os.path.exists(grid_file):
            df = pd.read_csv(grid_file)

            # 提取关键策略信息
            da_prices = sorted(df['DA_Price'].unique())

            # 计算门槛价格
            threshold_price = _calculate_threshold_price(df, config)

            # 构建策略表
            strategy_table = []
            for da_price in da_prices:
                price_data = df[df['DA_Price'] == da_price].iloc[0]
                strategy_table.append({
                    'da_price': float(da_price),
                    'p_da': float(price_data['P_DA']),
                    'objective': float(price_data['Objective'])
                })

            results['strategy'] = {
                'threshold_price': threshold_price,
                'strategy_table': strategy_table,
                'total_points': len(da_prices)
            }

        # 读取优化摘要
        summary_file = os.path.join(output_dir, 'neurodynamic_optimization_summary.json')
        if os.path.exists(summary_file):
            with open(summary_file, 'r', encoding='utf-8') as f:
                summary_data = json.load(f)
                results['summary'] = summary_data
                # 添加成本参数到摘要中
                results['summary']['generation_cost'] = config['COST_PARAMS']['c_g']
                results['summary']['max_power'] = config['CAPACITY_PARAMS']['P_max']
        else:
            # 如果没有摘要文件，手动创建基本摘要
            results['summary'] = {
                'optimization_method': config.get('OPTIMIZATION_METHOD', 'neurodynamic'),
                'generation_cost': config['COST_PARAMS']['c_g'],
                'max_power': config['CAPACITY_PARAMS']['P_max']
            }

            # 从 optimizer 对象获取统计信息
            if hasattr(optimizer, 'optimization_results') and optimizer.optimization_results:
                opt_results = optimizer.optimization_results
                total_points = len(opt_results)
                converged_points = sum(1 for res in opt_results.values() if res.get('converged', False))

                results['summary']['total_points'] = total_points
                results['summary']['converged_points'] = converged_points
                results['summary']['convergence_rate'] = 100 * converged_points / total_points if total_points > 0 else 0

                if config.get('OPTIMIZATION_METHOD') == 'neurodynamic':
                    avg_iter = sum(res.get('iterations', 0) for res in opt_results.values()) / total_points if total_points > 0 else 0
                    results['summary']['avg_iterations'] = avg_iter

        return results

    except Exception as e:
        logging.error(f"提取优化结果失败: {e}")
        logging.error(traceback.format_exc())
        return {
            'success': False,
            'error': str(e)
        }

def _calculate_threshold_price(df, config):
    """
    计算门槛价格
    """
    try:
        c_g = config['COST_PARAMS']['c_g']
        p_max = config['CAPACITY_PARAMS']['P_max']

        # 按DA价格分组，获取每个价格的P_DA
        price_groups = df.groupby('DA_Price')['P_DA'].first().sort_index()

        # 找到从低功率到高功率的转换点
        threshold = c_g
        for i in range(len(price_groups) - 1):
            current_p = price_groups.iloc[i]
            next_p = price_groups.iloc[i + 1]

            if current_p < 0.5 * p_max and next_p > 0.5 * p_max:
                threshold = (price_groups.index[i] + price_groups.index[i + 1]) / 2
                break

        return float(threshold)

    except Exception as e:
        logging.error(f"计算门槛价格失败: {e}")
        return float(config['COST_PARAMS']['c_g'])

if __name__ == '__main__':
    # 测试运行
    results = run_bidding_optimization()
    print("\n结果:")
    print(json.dumps(results, indent=2, ensure_ascii=False))

