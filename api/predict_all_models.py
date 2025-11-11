#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
运行所有预测模型并返回结果
"""

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.impute import SimpleImputer
import sys
from pathlib import Path

# 添加原来项目的路径
ORIGINAL_PROJECT_PATH = Path(__file__).parent.parent.parent / 'power-market-system' / '原来的项目资料'
sys.path.insert(0, str(ORIGINAL_PROJECT_PATH))

def run_all_models(data_with_features, price_column, time_column, feature_cols):
    """
    运行所有预测模型 - 完全按照原项目的方式实现

    Args:
        data_with_features: 包含所有特征的数据框
        price_column: 电价列名
        time_column: 时间列名
        feature_cols: 特征列名列表（应该是5个：hour, dayofweek, day, price_lag1, price_lag4）

    Returns:
        dict: 包含所有模型预测结果和性能指标的字典
    """
    print(f"\n{'='*60}")
    print(f"🤖 开始运行所有预测模型（原项目方式）...")
    print(f"{'='*60}\n")

    # 按时间顺序分割：前80%训练，后20%测试
    split_idx = int(len(data_with_features) * 0.8)

    print(f"✅ 数据分割完成")
    print(f"   训练集大小: {split_idx}")
    print(f"   测试集大小: {len(data_with_features) - split_idx}")
    print(f"   特征数量: {len(feature_cols)}")
    print(f"   特征列表: {feature_cols}")

    # 提取特征和目标值（不使用reset_index，保持原始索引）
    X = data_with_features[feature_cols].values
    y = data_with_features[price_column].values
    timestamps = pd.to_datetime(data_with_features[time_column])

    # 严格按时间顺序分割
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]
    test_timestamps = timestamps[split_idx:]

    print(f"   训练集时间范围: {timestamps.iloc[0]} 到 {timestamps.iloc[split_idx-1]}")
    print(f"   测试集时间范围: {timestamps.iloc[split_idx]} 到 {timestamps.iloc[-1]}")

    # 使用SimpleImputer处理缺失值（原项目的方式）
    imputer = SimpleImputer(strategy='mean')
    X_train = imputer.fit_transform(X_train)
    X_test = imputer.transform(X_test)

    print(f"✅ 缺失值处理完成")
    
    # 存储所有模型的预测结果
    all_predictions = {}
    all_metrics = {}
    
    # 模型列表
    models_to_run = [
        ('historical', '历史同期模型'),
        ('random_forest', '随机森林'),
        ('linear_regression', '线性回归'),
        ('gradient_boosting', '梯度提升'),
        ('xgboost', 'XGBoost'),
        ('ensemble', '集成模型')
    ]
    
    # 1. 历史同期模型（修复版 - 只使用训练集数据）
    print(f"\n1️⃣ 训练历史同期模型...")
    try:
        historical_pred = []
        train_timestamps = timestamps[:split_idx]

        for i, test_time in enumerate(test_timestamps):
            # 只使用训练集中相同小时的数据
            same_hour_mask = train_timestamps.hour == test_time.hour
            same_hour_values = y_train[same_hour_mask]

            if len(same_hour_values) > 0:
                historical_pred.append(np.mean(same_hour_values))
            else:
                historical_pred.append(np.mean(y_train))

        all_predictions['historical'] = np.array(historical_pred)
        all_metrics['historical'] = calculate_metrics(y_test, all_predictions['historical'])
        print(f"   ✅ 历史同期模型完成 - MAE: {all_metrics['historical']['mae']:.2f}")
    except Exception as e:
        print(f"   ❌ 历史同期模型失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 2. 随机森林模型
    print(f"\n2️⃣ 训练随机森林模型...")
    try:
        from src.predictions.random_forest_model import RandomForestModel
        
        rf_model = RandomForestModel(config={'HYPERPARAMETER_TUNING': {'CV_FOLDS': 3, 'RF_SEARCH_ITERATIONS': 5}})
        if rf_model.train(X_train, y_train):
            all_predictions['random_forest'] = rf_model.predict(X_test)
            all_metrics['random_forest'] = calculate_metrics(y_test, all_predictions['random_forest'])
            print(f"   ✅ 随机森林模型完成 - MAE: {all_metrics['random_forest']['mae']:.2f}")
        else:
            print(f"   ❌ 随机森林模型训练失败")
    except Exception as e:
        print(f"   ❌ 随机森林模型失败: {e}")
    
    # 3. 线性回归模型
    print(f"\n3️⃣ 训练线性回归模型...")
    try:
        from src.predictions.linear_regression_model import LinearRegressionModel
        
        lr_model = LinearRegressionModel(config={'HYPERPARAMETER_TUNING': {'CV_FOLDS': 3, 'LINEAR_SEARCH_ITERATIONS': 5}})
        if lr_model.train(X_train, y_train):
            all_predictions['linear_regression'] = lr_model.predict(X_test)
            all_metrics['linear_regression'] = calculate_metrics(y_test, all_predictions['linear_regression'])
            print(f"   ✅ 线性回归模型完成 - MAE: {all_metrics['linear_regression']['mae']:.2f}")
        else:
            print(f"   ❌ 线性回归模型训练失败")
    except Exception as e:
        print(f"   ❌ 线性回归模型失败: {e}")
    
    # 4. 梯度提升模型
    print(f"\n4️⃣ 训练梯度提升模型...")
    try:
        from src.predictions.gradient_boosting_model import GradientBoostingModel
        
        gb_model = GradientBoostingModel(config={'HYPERPARAMETER_TUNING': {'CV_FOLDS': 3, 'GB_SEARCH_ITERATIONS': 5}})
        if gb_model.train(X_train, y_train):
            all_predictions['gradient_boosting'] = gb_model.predict(X_test)
            all_metrics['gradient_boosting'] = calculate_metrics(y_test, all_predictions['gradient_boosting'])
            print(f"   ✅ 梯度提升模型完成 - MAE: {all_metrics['gradient_boosting']['mae']:.2f}")
        else:
            print(f"   ❌ 梯度提升模型训练失败")
    except Exception as e:
        print(f"   ❌ 梯度提升模型失败: {e}")
    
    # 5. XGBoost模型
    print(f"\n5️⃣ 训练XGBoost模型...")
    try:
        from src.predictions.xgboost_model import XGBoostModel
        
        xgb_model = XGBoostModel(config={'HYPERPARAMETER_TUNING': {'CV_FOLDS': 3, 'XGB_SEARCH_ITERATIONS': 5}})
        if xgb_model.train(X_train, y_train):
            all_predictions['xgboost'] = xgb_model.predict(X_test)
            all_metrics['xgboost'] = calculate_metrics(y_test, all_predictions['xgboost'])
            print(f"   ✅ XGBoost模型完成 - MAE: {all_metrics['xgboost']['mae']:.2f}")
        else:
            print(f"   ❌ XGBoost模型训练失败")
    except Exception as e:
        print(f"   ❌ XGBoost模型失败: {e}")
    
    # 6. 集成模型
    print(f"\n6️⃣ 生成集成模型预测...")
    try:
        from src.predictions.ensemble_model import EnsembleModel
        
        ensemble_config = {
            'selection_method': 'top_k',
            'top_k': 4,
            'mae_threshold': 40.0,
            'rmse_threshold': 70.0,
            'r2_threshold': -0.2,
            'ensemble_method': 'weighted_average',
            'exclude_models': [],
            'min_models': 2,
        }
        
        ensemble_model = EnsembleModel(config=ensemble_config)
        ensemble_model.train(all_predictions, y_test)
        ensemble_pred = ensemble_model.predict()
        
        if ensemble_pred is not None:
            all_predictions['ensemble'] = ensemble_pred
            all_metrics['ensemble'] = calculate_metrics(y_test, ensemble_pred)
            print(f"   ✅ 集成模型完成 - MAE: {all_metrics['ensemble']['mae']:.2f}")
            ensemble_model.print_summary()
        else:
            print(f"   ❌ 集成模型预测失败")
    except Exception as e:
        print(f"   ❌ 集成模型失败: {e}")
    
    print(f"\n{'='*60}")
    print(f"✅ 所有模型运行完成！")
    print(f"{'='*60}\n")
    
    return {
        'predictions': all_predictions,
        'metrics': all_metrics,
        'y_test': y_test,
        'timestamps': test_timestamps
    }

def calculate_metrics(y_true, y_pred):
    """计算性能指标"""
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    r2 = r2_score(y_true, y_pred)
    
    # 计算MAPE (处理零值)
    mape = np.mean(np.abs((y_true - y_pred) / np.where(y_true != 0, y_true, 1))) * 100
    
    # 计算方向准确率
    if len(y_true) > 1:
        actual_diff = np.diff(y_true)
        pred_diff = np.diff(y_pred)
        direction_accuracy = np.mean((actual_diff * pred_diff) > 0) * 100
    else:
        direction_accuracy = 0.0
    
    return {
        'mae': float(mae),
        'rmse': float(rmse),
        'r2': float(r2),
        'mape': float(mape),
        'direction_accuracy': float(direction_accuracy)
    }

