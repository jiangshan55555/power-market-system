#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
电力市场投标策略优化主程序
基于预测结果生成最优投标策略
"""

import sys
import os
from pathlib import Path
import logging
import json
import time
import traceback

# --- 路径设置 ---
# 获取项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)
print(f"当前工作目录: {os.getcwd()}")

# 导入自定义模块
from src.optimization.bidding_optimizer import BiddingOptimizationModel

def setup_logging():
    """設置日誌配置"""
    # 確保日誌目錄存在
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
    """加載配置文件"""
    try:
        # 使用絕對路徑
        config_path = os.path.join(os.getcwd(), 'config', 'config.json')
        print(f"嘗試加載配置文件: {config_path}")
        print(f"文件是否存在: {os.path.exists(config_path)}")

        print("正在读取配置文件...")
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        print("配置文件解析成功")

        print("正在构建投标配置...")
        # 更新路径配置以适应新的目录结构
        bidding_config = {
            'INPUT_FILE': 'output/predictions/prediction_results.csv',
            'OUTPUT_DIR': 'output/bidding',
            'PRICE_GRID_STEP': 1,  # 减小到1元步长，增加精度
            'PRICE_MIN': 350,      # 扩大价格范围
            'PRICE_MAX': 500,
            'COST_PARAMS': {
                'c_g': 380,  # 發電邊際成本 (CNY/MWh)
                'c_up': 500, # 上調整成本 (CNY/MWh)
                'c_dn': 300  # 下調整成本 (CNY/MWh)
            },
            'CAPACITY_PARAMS': {
                'P_max': 100, # 最大出力
                'R_up_max': 3, # 最大上調整
                'R_dn_max': 3  # 最大下調整
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
        logging.error(f"加載配置文件失敗: {e}")
        return None

def main():
    """主執行函數"""
    print("=" * 60)
    print("      電力市場投標策略優化系統      ")
    print("=" * 60)
    
    # 設置日誌
    setup_logging()
    
    # 加载配置
    print("步骤 1: 开始加载配置...")
    config = load_config()
    if not config:
        print("❌ 配置加载失败")
        return
    print("✅ 配置加载成功")
    
    try:
        # 檢查預測結果文件是否存在
        if not os.path.exists(config['INPUT_FILE']):
            logging.error(f"預測結果文件不存在: {config['INPUT_FILE']}")
            logging.error("請先運行預測程序生成預測結果")
            return
        
        # 創建輸出目錄
        os.makedirs(config['OUTPUT_DIR'], exist_ok=True)
        os.makedirs('output/logs', exist_ok=True)
        
        # 步骤 1: 初始化投标优化模型
        print("步骤 3: 开始初始化投标优化模型...")
        logging.info("步骤 1: 初始化投标优化模型...")
        optimizer = BiddingOptimizationModel(config)
        print("✅ 投标优化模型初始化成功")
        
        # 步驟 2: 執行投標策略優化
        method = config.get('OPTIMIZATION_METHOD', 'neurodynamic')
        method_name = "神經動力學自適應網格" if method == 'neurodynamic' else "SciPy"
        
        print(f"步骤 4: 开始执行{method_name}投标策略优化...")
        logging.info(f"步驟 2: 執行{method_name}投標策略優化...")
        optimizer.run(mode='full', target_date='2025-05-31')
        print("✅ 投标优化运行完成")
        
        logging.info("✅ 投標策略優化成功完成！")
        logging.info(f"結果已保存到: {config['OUTPUT_DIR']}")
        
        # 顯示主要結果
        if hasattr(optimizer, 'optimization_results') and optimizer.optimization_results:
            results = optimizer.optimization_results
            total_points = len(results)
            converged_points = sum(1 for res in results.values() if res.get('converged', False))
            
            logging.info("=" * 50)
            logging.info("優化結果摘要:")
            logging.info("=" * 50)
            logging.info(f"優化方法: {method_name}")
            logging.info(f"總優化點數: {total_points}")
            logging.info(f"收敛點數: {converged_points} ({100*converged_points/total_points:.1f}%)")
            
            if method == 'neurodynamic':
                avg_iter = sum(res.get('iterations', 0) for res in results.values()) / total_points
                logging.info(f"平均迭代次數: {avg_iter:.1f}")
        
    except Exception as e:
        logging.error(f"投標策略優化執行失敗: {e}")
        logging.error(traceback.format_exc())

if __name__ == "__main__":
    main()
