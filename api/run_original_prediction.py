#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
运行原项目的预测逻辑
直接调用原项目 main_prediction.py 的 main() 函数
"""

import sys
import os
from pathlib import Path
import pandas as pd
import numpy as np
import json

# 添加原项目路径
ORIGINAL_PROJECT_PATH = Path(__file__).parent.parent.parent / "power-market-system" / "原来的项目资料"
sys.path.insert(0, str(ORIGINAL_PROJECT_PATH))

def run_original_prediction():
    """
    直接调用原项目 main_prediction.py 的 main() 函数

    Returns:
        dict: 包含预测结果和性能指标
    """
    print(f"\n{'='*60}")
    print(f"🚀 直接调用原项目 main_prediction.py...")
    print(f"{'='*60}\n")

    # 保存当前工作目录
    original_cwd = os.getcwd()

    try:
        # 切换到原项目目录
        os.chdir(ORIGINAL_PROJECT_PATH)
        print(f"✅ 切换工作目录到: {os.getcwd()}")

        # 导入原项目的 main 函数
        from src.main_prediction import main as original_main

        print("✅ 成功导入原项目 main_prediction.py")

        # 调用原项目的 main() 函数
        print("\n" + "="*60)
        print("开始运行原项目 main() 函数...")
        print("="*60 + "\n")

        original_main()

        print("\n" + "="*60)
        print("✅ 原项目 main() 函数执行完成")
        print("="*60 + "\n")

        # 读取原项目生成的预测结果文件
        prediction_file = ORIGINAL_PROJECT_PATH / 'output' / 'predictions' / 'prediction_results.csv'

        if not prediction_file.exists():
            raise FileNotFoundError(f"预测结果文件不存在: {prediction_file}")

        print(f"\n📂 读取预测结果: {prediction_file}")
        results_df = pd.read_csv(prediction_file)

        print(f"   结果数据形状: {results_df.shape}")
        print(f"   列名: {results_df.columns.tolist()}")

        # 读取原始数据文件以获取时间戳（需要合并5月和6月的数据）
        raw_data_file_may = ORIGINAL_PROJECT_PATH / 'data' / 'rawdata_0501.xlsx'
        raw_data_file_jun = ORIGINAL_PROJECT_PATH / 'data' / 'rawdata_0601.xlsx'

        print(f"\n📂 读取原始数据以获取时间戳:")
        print(f"   5月数据: {raw_data_file_may}")
        print(f"   6月数据: {raw_data_file_jun}")

        raw_df_may = pd.read_excel(raw_data_file_may)
        raw_df_jun = pd.read_excel(raw_data_file_jun)

        # 统一使用"日期"列作为时间戳（包含完整的日期和时间）
        # 5月数据的"时间"列有完整日期时间，6月数据的"时间"列只有时间
        # 但两个文件都有"日期"列包含完整的日期时间
        for df, month_name in [(raw_df_may, '5月'), (raw_df_jun, '6月')]:
            if '日期' in df.columns:
                # 使用"日期"列替换"时间"列
                df['时间'] = df['日期']
                print(f"   ✅ {month_name}数据使用'日期'列作为时间戳，示例: {df['时间'].iloc[0]}")

        # 合并两个月的数据
        raw_df = pd.concat([raw_df_may, raw_df_jun], ignore_index=True)

        # 计算测试集的起始索引（假设80/20分割）
        total_samples = len(raw_df)
        train_size = int(total_samples * 0.8)
        test_size = total_samples - train_size

        print(f"   5月数据: {len(raw_df_may)} 条")
        print(f"   6月数据: {len(raw_df_jun)} 条")
        print(f"   合并后总样本数: {total_samples}")
        print(f"   训练集大小: {train_size}")
        print(f"   测试集大小: {test_size}")
        print(f"   预测结果数量: {len(results_df)}")

        # 从原始数据中提取时间戳
        # 由于预测结果的 timestamp 列是空的，我们需要从原始数据中提取
        test_timestamps = []

        # 检查预测结果的 timestamp 列是否有效
        has_valid_timestamps = False
        if 'timestamp' in results_df.columns:
            # 检查是否有非空且非空字符串的时间戳
            # 注意：空字符串 '' 不会被 notna() 识别为缺失值
            valid_count = 0
            for ts in results_df['timestamp']:
                if pd.notna(ts) and str(ts).strip() != '':
                    valid_count += 1

            # 要求至少 80% 的时间戳有效才使用预测结果的 timestamp 列
            valid_ratio = valid_count / len(results_df) if len(results_df) > 0 else 0
            print(f"   📊 预测结果中有 {valid_count}/{len(results_df)} 个有效时间戳 ({valid_ratio:.1%})")

            if valid_ratio >= 0.8:
                has_valid_timestamps = True
                print(f"   ✅ 时间戳有效率 >= 80%，将使用预测结果的 timestamp 列")
            else:
                print(f"   ⚠️ 时间戳有效率 < 80%，将从原始数据提取时间戳")

        if has_valid_timestamps:
            # 如果预测结果中有有效的 timestamp 列，直接使用
            for ts in results_df['timestamp']:
                if pd.isna(ts) or ts == '':
                    test_timestamps.append('')
                elif isinstance(ts, pd.Timestamp):
                    test_timestamps.append(ts.strftime('%Y-%m-%d %H:%M'))
                else:
                    test_timestamps.append(str(ts))
            print(f"   ✅ 从预测结果的 timestamp 列提取时间戳")
        else:
            # 从原始数据提取时间戳
            # 取最后 len(results_df) 条数据的时间戳
            total_samples = len(raw_df)
            start_idx = total_samples - len(results_df)

            print(f"   📊 原始数据总样本数: {total_samples}")
            print(f"   📊 预测结果数量: {len(results_df)}")
            print(f"   📊 提取时间戳范围: [{start_idx}, {total_samples})")

            test_timestamps_raw = raw_df['时间'].iloc[start_idx:total_samples]
            for ts in test_timestamps_raw:
                if pd.isna(ts):
                    test_timestamps.append('')
                elif isinstance(ts, pd.Timestamp):
                    test_timestamps.append(ts.strftime('%Y-%m-%d %H:%M'))
                else:
                    # 尝试将字符串转换为 datetime 对象
                    try:
                        ts_parsed = pd.to_datetime(ts)
                        test_timestamps.append(ts_parsed.strftime('%Y-%m-%d %H:%M'))
                    except:
                        # 如果转换失败，直接使用原字符串
                        test_timestamps.append(str(ts))
            print(f"   ✅ 从原始数据提取时间戳（预测结果中无有效 timestamp）")

        print(f"   时间戳数量: {len(test_timestamps)}")
        print(f"   预测结果数量: {len(results_df)}")
        print(f"   时间戳示例（前3个）: {test_timestamps[:3] if len(test_timestamps) >= 3 else test_timestamps}")
        print(f"   时间戳示例（后3个）: {test_timestamps[-3:] if len(test_timestamps) >= 3 else test_timestamps}")

        # 提取数据
        # 原项目输出的列名是英文的: timestamp, actual, historical, random_forest, etc.
        y_test = results_df['actual'].values

        # 提取所有模型的预测值
        predictions = {}
        model_columns = {
            'historical': 'historical',
            'random_forest': 'random_forest',
            'linear_regression': 'linear_regression',
            'gradient_boosting': 'gradient_boosting',
            'xgboost': 'xgboost',
            'ensemble': 'ensemble'
        }

        for model_key, col_name in model_columns.items():
            if col_name in results_df.columns:
                predictions[model_key] = results_df[col_name].values

        # 计算性能指标
        from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

        metrics = {}
        for model_name, pred in predictions.items():
            mae = mean_absolute_error(y_test, pred)
            rmse = np.sqrt(mean_squared_error(y_test, pred))
            r2 = r2_score(y_test, pred)

            # MAPE
            mape = np.mean(np.abs((y_test - pred) / np.where(y_test != 0, y_test, 1))) * 100

            # 方向准确率
            if len(y_test) > 1:
                actual_diff = np.diff(y_test)
                pred_diff = np.diff(pred)
                direction_accuracy = np.mean((actual_diff * pred_diff) > 0) * 100
            else:
                direction_accuracy = 0.0

            # 确保所有值都是有效的 JSON 数值（处理 NaN 和 Infinity）
            def safe_float(value):
                """将值转换为安全的浮点数，处理 NaN 和 Infinity"""
                if np.isnan(value) or np.isinf(value):
                    return None
                return float(value)

            metrics[model_name] = {
                'mae': safe_float(mae),
                'rmse': safe_float(rmse),
                'r2': safe_float(r2),
                'mape': safe_float(mape),
                'direction_accuracy': safe_float(direction_accuracy)
            }

            print(f"📊 {model_name}: MAE={mae:.2f}, RMSE={rmse:.2f}, R²={r2:.4f}")

        # 处理 NaN 值的辅助函数
        def clean_array(arr):
            """将数组中的 NaN 和 Infinity 替换为 None"""
            return [None if (isinstance(x, float) and (np.isnan(x) or np.isinf(x))) else x for x in arr]

        # 返回结果
        return {
            'success': True,
            'predictions': {k: clean_array(v.tolist()) for k, v in predictions.items()},
            'metrics': metrics,
            'y_test': clean_array(y_test.tolist()),
            'timestamps': test_timestamps,  # 从原始数据中提取的时间戳
            'train_size': train_size,
            'test_size': test_size,
            'feature_names': ['hour', 'dayofweek', 'day', 'price_lag1', 'price_lag4']
        }

    except Exception as e:
        import traceback
        error_msg = f"预测失败: {str(e)}\n{traceback.format_exc()}"
        print(f"❌ {error_msg}")
        return {
            'success': False,
            'error': error_msg
        }
    finally:
        # 恢复原工作目录
        os.chdir(original_cwd)
        print(f"✅ 恢复工作目录到: {os.getcwd()}")

