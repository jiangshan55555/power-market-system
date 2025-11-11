#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
特征工程模块 - 遵守GAP规则
"""

import pandas as pd
import numpy as np
from datetime import timedelta

def create_lag_features(df, price_column, time_column, gap_days=1, max_lags=3):
    """
    创建滞后特征（遵守GAP规则）
    
    Args:
        df: 数据框
        price_column: 电价列名
        time_column: 时间列名
        gap_days: GAP天数（T值），默认为1天
        max_lags: 最大滞后期数
    
    Returns:
        添加了滞后特征的数据框
    """
    df = df.copy()
    
    # 确保按时间排序
    df = df.sort_values(by=time_column).reset_index(drop=True)
    
    # 计算每天有多少个时间点（假设是15分钟间隔，一天96个点）
    time_diff = df[time_column].diff().mode()[0]
    points_per_day = int(pd.Timedelta(days=1) / time_diff)
    
    # GAP限制：需要跳过gap_days天的数据
    gap_points = gap_days * points_per_day
    
    print(f"   特征工程参数:")
    print(f"   - 每天时间点数: {points_per_day}")
    print(f"   - GAP天数: {gap_days}天")
    print(f"   - GAP点数: {gap_points}个点")
    
    # 创建滞后特征（从gap_points开始）
    for lag in range(1, max_lags + 1):
        lag_shift = gap_points + lag
        df[f'price_lag_{lag}'] = df[price_column].shift(lag_shift)
        print(f"   - 创建滞后特征: price_lag_{lag} (shift={lag_shift})")
    
    return df

def create_rolling_features(df, price_column, time_column, gap_days=1, windows=[7, 14, 30]):
    """
    创建滚动统计特征（遵守GAP规则）
    
    Args:
        df: 数据框
        price_column: 电价列名
        time_column: 时间列名
        gap_days: GAP天数
        windows: 滚动窗口大小列表（天数）
    
    Returns:
        添加了滚动特征的数据框
    """
    df = df.copy()
    
    # 计算每天的时间点数
    time_diff = df[time_column].diff().mode()[0]
    points_per_day = int(pd.Timedelta(days=1) / time_diff)
    gap_points = gap_days * points_per_day
    
    for window_days in windows:
        window_points = window_days * points_per_day
        
        # 滚动均值（需要考虑GAP）
        df[f'rolling_mean_{window_days}d'] = df[price_column].shift(gap_points).rolling(window=window_points, min_periods=1).mean()
        
        # 滚动标准差
        df[f'rolling_std_{window_days}d'] = df[price_column].shift(gap_points).rolling(window=window_points, min_periods=1).std()
        
        # 滚动最大值
        df[f'rolling_max_{window_days}d'] = df[price_column].shift(gap_points).rolling(window=window_points, min_periods=1).max()
        
        # 滚动最小值
        df[f'rolling_min_{window_days}d'] = df[price_column].shift(gap_points).rolling(window=window_points, min_periods=1).min()
        
        print(f"   - 创建滚动特征: {window_days}天窗口 (window={window_points}点)")
    
    return df

def create_time_features(df, time_column):
    """
    创建时间特征
    
    Args:
        df: 数据框
        time_column: 时间列名
    
    Returns:
        添加了时间特征的数据框
    """
    df = df.copy()
    
    # 确保时间列是datetime类型
    if not pd.api.types.is_datetime64_any_dtype(df[time_column]):
        df[time_column] = pd.to_datetime(df[time_column])
    
    # 小时
    df['hour'] = df[time_column].dt.hour
    
    # 星期几（0=周一，6=周日）
    df['day_of_week'] = df[time_column].dt.dayofweek
    
    # 月份
    df['month'] = df[time_column].dt.month
    
    # 是否周末
    df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
    
    # 季节（1=春，2=夏，3=秋，4=冬）
    df['season'] = df['month'].apply(lambda x: (x % 12 + 3) // 3)
    
    # 一天中的时段（0=凌晨，1=早上，2=中午，3=下午，4=晚上，5=深夜）
    df['time_of_day'] = pd.cut(df['hour'], bins=[0, 6, 9, 12, 18, 22, 24], labels=[0, 1, 2, 3, 4, 5], include_lowest=True).astype(int)
    
    print(f"   - 创建时间特征: hour, day_of_week, month, is_weekend, season, time_of_day")
    
    return df

def create_all_features(df, price_column, time_column, gap_days=1):
    """
    创建所有特征 - 简化版，只使用原项目的5个核心特征

    原项目使用的5个特征：
    1. hour - 小时
    2. dayofweek - 星期几
    3. day - 日期
    4. price_lag1 - 前1个时间点的价格
    5. price_lag4 - 前4个时间点的价格

    Args:
        df: 数据框
        price_column: 电价列名
        time_column: 时间列名
        gap_days: GAP天数（在简化版本中不使用）

    Returns:
        添加了5个核心特征的数据框
    """
    print(f"\n{'='*60}")
    print(f"开始特征工程（使用原项目的5个核心特征）")
    print(f"{'='*60}\n")

    df = df.copy()

    # 确保时间列是datetime类型
    if not pd.api.types.is_datetime64_any_dtype(df[time_column]):
        df[time_column] = pd.to_datetime(df[time_column])

    # 按时间排序
    df = df.sort_values(time_column).reset_index(drop=True)

    # 1. 时间特征（3个）
    print("1️⃣ 创建时间特征...")
    df['hour'] = df[time_column].dt.hour
    df['dayofweek'] = df[time_column].dt.dayofweek
    df['day'] = df[time_column].dt.day
    print(f"   ✅ 时间特征: hour, dayofweek, day")

    # 2. 滞后特征（2个）
    print(f"\n2️⃣ 创建滞后特征...")

    # 滞后1个时间点（15分钟）
    df['price_lag1'] = df[price_column].shift(1)
    # 第一个值用自己填充
    if len(df) > 0:
        df.loc[0, 'price_lag1'] = df.loc[0, price_column]

    # 滞后4个时间点（1小时）
    df['price_lag4'] = df[price_column].shift(4)
    # 前4个值用向后填充
    for i in range(min(4, len(df))):
        df.loc[i, 'price_lag4'] = df.loc[i, price_column]

    print(f"   ✅ price_lag1 (滞后1个点 = 15分钟)")
    print(f"   ✅ price_lag4 (滞后4个点 = 1小时)")

    print(f"\n{'='*60}")
    print(f"特征工程完成！")
    print(f"{'='*60}")
    print(f"总特征数: 5 (hour, dayofweek, day, price_lag1, price_lag4)")
    print(f"数据形状: {df.shape}")
    print(f"{'='*60}\n")

    return df

