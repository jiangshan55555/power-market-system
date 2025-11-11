#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
數據處理模塊，負責數據加載、預處理和特徵工程
"""

import pandas as pd
import numpy as np
import os
import logging
import traceback
from datetime import datetime
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import matplotlib.pyplot as plt
import warnings
from sklearn.preprocessing import MinMaxScaler, StandardScaler
import time

class DataProcessor:
    """数据处理类，提供数据加载、预处理和特征工程功能"""

    def __init__(self, config):
        """初始化数据处理器

        Args:
            config: 数据配置或数据文件路径
        """
        self.config = config
        warnings.filterwarnings('ignore')
        plt.rcParams['font.sans-serif'] = ['SimHei']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 默认配置
        default_config = {
            'INPUT_FILE': 'data/rawdata.xlsx',
            'TARGET_COLUMN': '实时出清电价',  # 精确匹配列名
            'TARGET_COLUMNS_ALTERNATIVES': ['实时出清电价', '电价', '日前出清电价'],  # 备选列名
            'DATE_COLUMN': 'DATE',
            'TIME_COLUMN': 'TIME',
            'FILL_METHOD': 'linear',  # 缺失值填充方法
            'FEATURE_ENGINEERING': {
                'use_time_features': True,
                'use_lag_features': True,
                'max_lag': 168,  # 最大滞后期数
                'use_rolling_features': True,
                'rolling_windows': [24, 48, 168]  # 滚动窗口大小
            },
            'OUTLIER_THRESHOLD': 3.0,  # 异常值处理阈值（标准差倍数）
            'RANDOM_STATE': 42
        }
        
        # 如果传入的是字符串，则视为文件路径
        if isinstance(config, str):
            self.config = default_config.copy()
            self.config['INPUT_FILE'] = config
        # 如果传入的是字典，则更新默认配置
        elif isinstance(config, dict):
            self.config = default_config.copy()
            # 如果config是格式化的配置，例如来自run.py的config['data']
            if 'input_file' in config:
                self.config['INPUT_FILE'] = config['input_file']
            if 'target_column' in config:
                self.config['TARGET_COLUMN'] = config['target_column']

            # 遍历配置字典，更新默认配置
            for key, value in config.items():
                if key.upper() in self.config:
                    # 转换为大写键
                    self.config[key.upper()] = value
                else:
                    # 保持原样
                    self.config[key] = value
        else:
            raise TypeError("config 必须是字符串路径或配置字典")
        
        self.df = None
        self.target_column = None
    
    def load_and_preprocess_data(self):
        """加载数据并进行预处理

        Returns:
            pd.DataFrame: 预处理后的数据
        """
        print("\n正在加载和预处理数据...")
        try:
            # 自动发现并加载data目录中的所有Excel文件
            import glob
            excel_files = glob.glob('data/*.xlsx') + glob.glob('data/*.xls')

            if not excel_files:
                # 回退到配置文件指定的单个文件
                file_path = str(self.config['INPUT_FILE'])
                logging.info(f"未找到多个数据文件，使用配置文件指定的: {file_path}")
                if not os.path.exists(file_path):
                    logging.error(f"数据文件不存在: {file_path}")
                    return None, None
                excel_files = [file_path]

            logging.info(f"发现 {len(excel_files)} 个数据文件:")
            for file in excel_files:
                logging.info(f"  - {file}")

            # 加载并合并所有文件
            dataframes = []
            file_info = []

            for file_path in sorted(excel_files):
                try:
                    logging.info(f"加载文件: {file_path}")

                    # 读取文件
                    if file_path.endswith('.csv'):
                        df_temp = pd.read_csv(file_path, header=[0, 1])
                    elif file_path.endswith('.xlsx') or file_path.endswith('.xls'):
                        df_temp = pd.read_excel(file_path, header=[0, 1])
                    else:
                        logging.warning(f"跳过不支持的文件格式: {file_path}")
                        continue

                    # 提取文件名中的日期信息
                    import re
                    filename = os.path.basename(file_path)
                    date_match = re.search(r'(\d{4})(\d{2})', filename)
                    if date_match:
                        year, month = date_match.groups()
                        file_date = f"{year}-{month}"
                    else:
                        file_date = filename.replace('.xlsx', '').replace('.xls', '').replace('.csv', '')

                    dataframes.append(df_temp)
                    file_info.append({
                        'file': filename,
                        'date': file_date,
                        'records': len(df_temp)
                    })

                    logging.info(f"  文件 {filename}: {len(df_temp)} 条记录")

                except Exception as e:
                    logging.warning(f"跳过文件 {file_path}: {e}")
                    continue

            if not dataframes:
                logging.error("没有成功加载任何数据文件")
                return None, None

            # 合并所有数据
            df = pd.concat(dataframes, ignore_index=True)
            logging.info(f"合并后总数据: {len(df)} 条记录")

            # 显示数据概览
            logging.info("数据文件概览:")
            data_periods = []
            for info in file_info:
                logging.info(f"  {info['date']}: {info['records']} 条记录 ({info['file']})")
                data_periods.append(info['date'])

            # 保存文件信息供后续使用
            self.file_info = file_info
            self.data_period_str = "、".join(data_periods)
            logging.info(f"数据时间范围: {self.data_period_str}")
            
            # 處理多層表頭
            new_columns = []
            for col in df.columns.values:
                feature_name = str(col[0]).strip()
                if pd.notna(col[1]) and not isinstance(col[1], (int, float)):
                    second_part = str(col[1]).strip()
                    if second_part:
                        feature_name = f"{feature_name}_{second_part}"
                new_columns.append(feature_name)
            df.columns = new_columns
            
            # 輸出列名以便調試
            logging.info(f"處理後的列名: {df.columns.tolist()}")
            
            # 處理時間列
            time_col = next((col for col in df.columns if '时间' in col or '時間' in col or 'time' in col.lower() or 'date' in col.lower()), None)
            if time_col:
                logging.info(f"使用 {time_col} 列作為時間索引")
                
                # 處理非標準時間格式（如 24:00）
                df[time_col] = df[time_col].astype(str).str.replace('24:00', '00:00')
                
                # 轉換為日期時間索引
                try:
                    df['timestamp'] = pd.to_datetime(df[time_col], format='mixed')
                    # 檢查是否有需要調整的日期（將 00:00 的日期加一天）
                    mask = df['timestamp'].dt.time == pd.Timestamp('00:00').time()
                    df.loc[mask, 'timestamp'] += pd.Timedelta(days=1)
                except Exception as e:
                    logging.error(f"時間格式轉換失敗: {e}")
                    # 嘗試不同的格式
                    try:
                        df['timestamp'] = pd.to_datetime(df[time_col], errors='coerce')
                    except Exception as e:
                        logging.error(f"時間格式轉換失敗: {e}")
                        return None, None
                
                # 設置索引
                df.set_index('timestamp', inplace=True)
                
                # 確保索引已排序
                df = df.sort_index()
            
            # 確保目標列存在
            target_col_pattern = self.config['TARGET_COLUMN']
            target_col = next((col for col in df.columns if target_col_pattern in col), None)
            
            if target_col:
                logging.info(f"找到目標列: {target_col}")
                self.config['TARGET_COLUMN'] = target_col
            else:
                # 嘗試使用備選列名
                alternatives = self.config.get('TARGET_COLUMNS_ALTERNATIVES', [])
                for alt in alternatives:
                    alt_col = next((col for col in df.columns if alt in col), None)
                    if alt_col:
                        self.config['TARGET_COLUMN'] = alt_col
                        logging.info(f"使用備選列名匹配到目標列: {alt_col}")
                        break
            
            if self.config['TARGET_COLUMN'] not in df.columns:
                logging.error(f"找不到目標列: {self.config['TARGET_COLUMN']} 或其替代")
                logging.error(f"可用列: {df.columns.tolist()}")
                return None, None
                
            logging.info(f"目標列設置為: {self.config['TARGET_COLUMN']}")
            
            # 數據清理
            logging.info("進行數據清理...")
            # 只保留數值型列
            df = df.select_dtypes(exclude=['object'])
            # 轉換為數值型
            df = df.apply(pd.to_numeric, errors='coerce')
            # 填充缺失值
            df = df.fillna(method='ffill').fillna(method='bfill')
            
            # 檢查預測日期是否在數據範圍內
            prediction_start_date = self.config.get('prediction_start_date', self.config.get('PREDICTION_START_DATE', '2025-06-15'))
            prediction_date = pd.to_datetime(prediction_start_date).date()
            last_date = df.index.max().date()
            
            if prediction_date > last_date:
                logging.warning(f"預測日期 {prediction_date} 在數據範圍之外。將創建空模板用於預測。")
                future_dates = pd.date_range(start=self.config['PREDICTION_START_DATE'], periods=96, freq='15min')
                future_df = pd.DataFrame(index=future_dates, columns=df.columns)
                df = pd.concat([df, future_df])
                df[self.config['TARGET_COLUMN']] = df[self.config['TARGET_COLUMN']].fillna(0)  # 預測期的實際值填充為0
            
            logging.info(f"數據預處理完成，共 {len(df)} 筆記錄，時間範圍: {df.index.min()} - {df.index.max()}")
            return df, self.config['TARGET_COLUMN']
        
        except Exception as e:
            logging.error(f"數據加載失敗: {e}")
            traceback.print_exc()
            return None, None
    
    def create_features(self, df, prediction_date):
        """創建特徵
        
        Args:
            df: 要處理的數據
            prediction_date: 預測日期
            
        Returns:
            pd.DataFrame: 添加特徵後的數據
        """
        print(f"\n正在创建特征...")
        df_features = df.copy()
        
        # 時間特徵
        if self.config['FEATURE_ENGINEERING']['use_time_features']:
            logging.info("創建時間特徵...")
            df_features['hour'] = df_features.index.hour
            df_features['dayofweek'] = df_features.index.dayofweek
            df_features['month'] = df_features.index.month
            df_features['is_weekend'] = (df_features.index.dayofweek >= 5).astype(int)
            df_features['hour_sin'] = np.sin(2 * np.pi * df_features['hour'] / 24)
            df_features['hour_cos'] = np.cos(2 * np.pi * df_features['hour'] / 24)
            df_features['dayofweek_sin'] = np.sin(2 * np.pi * df_features['dayofweek'] / 7)
            df_features['dayofweek_cos'] = np.cos(2 * np.pi * df_features['dayofweek'] / 7)
        
        # 根據T參數計算截止日期
        T = self.config['T']
        gap_days = T + 1
        cutoff_date = prediction_date - pd.Timedelta(days=gap_days)
        
        # 過濾掉 NaT 值
        df_valid = df[pd.notna(df.index)]
        available_data = df_valid[df_valid.index < cutoff_date]
        
        target_col = self.config['TARGET_COLUMN']
        points_per_day = 96
        
        available_days = (available_data.index.max() - available_data.index.min()).days if not available_data.empty else 0
        
        lag_days = range(gap_days, min(available_days, 15))
        for day in lag_days:
            df_features[f'lag_{day}d'] = df[target_col].shift(day * points_per_day)
            
            # 添加一些重要的滯後時間點
            df_features[f'lag_{day}d_same_hour'] = df[target_col].shift(day * points_per_day)
        
        # 滾動窗口特徵
        if self.config['FEATURE_ENGINEERING']['use_rolling_features']:
            logging.info("創建滾動窗口特徵...")
            for window in self.config['FEATURE_ENGINEERING']['rolling_windows']:
                df_features[f'rolling_mean_{window}'] = df[target_col].shift(gap_days * points_per_day).rolling(window=window).mean()
                df_features[f'rolling_std_{window}'] = df[target_col].shift(gap_days * points_per_day).rolling(window=window).std()
                df_features[f'rolling_max_{window}'] = df[target_col].shift(gap_days * points_per_day).rolling(window=window).max()
                df_features[f'rolling_min_{window}'] = df[target_col].shift(gap_days * points_per_day).rolling(window=window).min()
        
        # 填充缺失值
        df_features = df_features.fillna(method='bfill').fillna(0)
        
        logging.info(f"特徵創建完成，共 {len(df_features.columns)} 個特徵")
        return df_features
    
    def train_test_split_time(self, df, prediction_date):
        """根據時間進行訓練集和測試集分割
        
        Args:
            df (pd.DataFrame): 輸入數據
            prediction_date (datetime): 預測日期
            
        Returns:
            tuple: X_train, X_test, y_train, y_test, test_dates
        """
        try:
            logging.info(f"根據時間分割數據，預測日期: {prediction_date}")
            
            # 設置目標列
            target_column = self.config['TARGET_COLUMN']
            
            # 確保預測日期是datetime類型
            if isinstance(prediction_date, str):
                prediction_date = pd.to_datetime(prediction_date)
            
            # 獲取預測日的開始時間和結束時間
            prediction_day_start = pd.Timestamp(prediction_date.date())
            prediction_day_end = prediction_day_start + pd.Timedelta(days=1)
            
            logging.info(f"預測日期範圍: {prediction_day_start} - {prediction_day_end}")
            
            # 檢查數據中是否有預測日期的數據
            if prediction_day_start > df.index.max():
                logging.error(f"預測日期 {prediction_day_start} 超出數據範圍 {df.index.min()} - {df.index.max()}")
                return None, pd.DataFrame(), None, pd.Series(), []
            
            # 分割訓練集和測試集
            train_data = df[df.index < prediction_day_start].copy()
            test_data = df[(df.index >= prediction_day_start) & (df.index < prediction_day_end)].copy()
            
            # 檢查訓練集和測試集是否為空
            if train_data.empty:
                logging.error(f"訓練集為空，無法進行預測")
                return None, pd.DataFrame(), None, pd.Series(), []
                
            if test_data.empty:
                logging.warning(f"測試集為空，創建空的測試集")
                # 創建一個包含預測日期的時間序列
                test_dates = pd.date_range(start=prediction_day_start, end=prediction_day_end, freq='15min')[:-1]
                test_data = pd.DataFrame(index=test_dates)
                test_data[target_column] = np.nan
                
                # 複製訓練集的列
                for col in train_data.columns:
                    if col != target_column:
                        test_data[col] = np.nan
            
            # 獲取測試集的日期
            test_dates = test_data.index
            
            # 分離特徵和目標
            X_train = train_data.drop(columns=[target_column])
            y_train = train_data[target_column]
            
            # 處理測試集
            if target_column in test_data.columns:
                X_test = test_data.drop(columns=[target_column])
                y_test = test_data[target_column]
            else:
                X_test = test_data.copy()
                y_test = pd.Series(np.nan, index=test_data.index)
            
            # 特徵工程
            X_train, X_test = self.feature_engineering(X_train, X_test)
            
            logging.info(f"數據分割完成，訓練集: {X_train.shape}, 測試集: {X_test.shape}")
            return X_train, X_test, y_train, y_test, test_dates
            
        except Exception as e:
            logging.error(f"數據分割失敗: {str(e)}")
            traceback.print_exc()
            return None, pd.DataFrame(), None, pd.Series(), []

    def scale_data_for_lstm(self, df, target_col, look_back_days=7):
        """將數據縮放到適合LSTM模型的格式
        
        Args:
            df: 要縮放的數據
            target_col: 目標列名
            look_back_days: 回看天數
            
        Returns:
            tuple: (X, y, scaler)
        """
        scaler = StandardScaler()
        scaled_data = scaler.fit_transform(df[[target_col]])
        
        look_back = look_back_days * 96  # 假設每天有96個時間點
        X, y = [], []
        for i in range(len(scaled_data) - look_back):
            X.append(scaled_data[i:(i + look_back), 0])
            y.append(scaled_data[i + look_back, 0])
            
        X, y = np.array(X), np.array(y)
        X = np.reshape(X, (X.shape[0], X.shape[1], 1))
        
        return X, y, scaler

    def get_historical_data_for_prediction(self, prediction_date=None, days_back=14):
        """獲取用於歷史同期預測的數據
        
        Args:
            prediction_date: 預測日期，如果為None則使用配置中的PREDICTION_START_DATE
            days_back: 向前查找的天數
            
        Returns:
            pd.DataFrame: 歷史同期數據
        """
        if self.df is None:
            logging.error("無數據可供查詢")
            return None
        
        if prediction_date is None:
            prediction_date = pd.to_datetime(self.config['PREDICTION_START_DATE'])
        
        try:
            # 獲取同一月內的歷史數據（從預測日期向前推days_back天）
            start_date = prediction_date - pd.Timedelta(days=days_back)
            end_date = prediction_date - pd.Timedelta(minutes=15)  # 預測日期前一個時間點
            
            # 獲取歷史區間數據
            historical_data = self.df[(self.df.index >= start_date) & (self.df.index <= end_date)]
            
            if len(historical_data) == 0:
                logging.warning("沒有找到足夠的歷史數據")
                return None
            
            logging.info(f"獲取到 {len(historical_data)} 筆近期歷史數據，時間範圍: {historical_data.index.min()} - {historical_data.index.max()}")
            return historical_data
        
        except Exception as e:
            logging.error(f"獲取歷史數據失敗: {e}")
            return None
    
    def run_pipeline(self):
        """運行完整的數據處理流程
        
        Returns:
            tuple: (X_train, X_test, y_train, y_test, test_dates)
        """
        # 1. 加載數據
        raw_data, target_column = self.load_and_preprocess_data()
        if raw_data is None:
            return None, None, None, None, None
        
        # 2. 創建特徵
        featured_data = self.create_features(raw_data, pd.to_datetime(self.config['PREDICTION_START_DATE']))
        if featured_data is None:
            return None, None, None, None, None
        
        # 3. 分割訓練測試集
        return self.train_test_split_time(raw_data, pd.to_datetime(self.config['PREDICTION_START_DATE']))

    def engineer_features(self, df=None):
        """特徵工程，創建預測所需的特徵
        
        Args:
            df: 要處理的數據，如果為None則使用self.df
            
        Returns:
            pd.DataFrame: 添加特徵後的數據
        """
        if df is None:
            df = self.df
        
        if df is None:
            logging.error("無數據可供特徵工程")
            return None
        
        try:
            logging.info("開始創建特徵...")
            df_features = df.copy()
            
            # 時間特徵
            logging.info("創建時間特徵...")
            df_features['hour'] = df_features.index.hour
            df_features['dayofweek'] = df_features.index.dayofweek
            df_features['month'] = df_features.index.month
            df_features['is_weekend'] = (df_features.index.dayofweek >= 5).astype(int)
            df_features['hour_sin'] = np.sin(2 * np.pi * df_features['hour'] / 24)
            df_features['hour_cos'] = np.cos(2 * np.pi * df_features['hour'] / 24)
            df_features['dayofweek_sin'] = np.sin(2 * np.pi * df_features['dayofweek'] / 7)
            df_features['dayofweek_cos'] = np.cos(2 * np.pi * df_features['dayofweek'] / 7)
            
            # 滯後特徵
            logging.info("創建滯後特徵...")
            points_per_day = 96  # 15分鐘一個點，一天96個點
            
            for lag in [1, 2, 3, 4, 24, 48, 96, 96*7]:  # 15分鐘, 30分鐘, 1小時, 6小時, 1天, 7天
                df_features[f'lag_{lag}'] = df[self.config['TARGET_COLUMN']].shift(lag)
            
            # 滾動窗口特徵
            logging.info("創建滾動窗口特徵...")
            for window in [24, 48, 96]:  # 6小時, 12小時, 24小時
                df_features[f'rolling_mean_{window}'] = df[self.config['TARGET_COLUMN']].rolling(window=window).mean()
                df_features[f'rolling_std_{window}'] = df[self.config['TARGET_COLUMN']].rolling(window=window).std()
                df_features[f'rolling_max_{window}'] = df[self.config['TARGET_COLUMN']].rolling(window=window).max()
                df_features[f'rolling_min_{window}'] = df[self.config['TARGET_COLUMN']].rolling(window=window).min()
            
            # 填充缺失值
            df_features = df_features.fillna(method='bfill').fillna(0)
            
            logging.info(f"特徵創建完成，共 {len(df_features.columns)} 個特徵")
            return df_features
        
        except Exception as e:
            logging.error(f"特徵創建失敗: {e}")
            traceback.print_exc()
            return None

    def split_data(self, df, target_column, test_size=0.2):
        """分割數據為訓練集和測試集
        
        Args:
            df: 要分割的數據
            target_column: 目標列名
            test_size: 測試集比例
            
        Returns:
            tuple: (X_train, X_test, y_train, y_test, train_dates, test_dates)
        """
        try:
            # 確保目標列存在
            if target_column not in df.columns:
                logging.error(f"目標列 {target_column} 不在數據中")
                return None, None, None, None, None, None
            
            # 分割特徵和目標
            X = df.drop(columns=[target_column])
            y = df[target_column]
            
            # 按時間順序分割
            train_size = int(len(df) * (1 - test_size))
            
            X_train = X.iloc[:train_size]
            X_test = X.iloc[train_size:]
            y_train = y.iloc[:train_size]
            y_test = y.iloc[train_size:]
            
            train_dates = X_train.index
            test_dates = X_test.index
            
            logging.info(f"訓練集大小: {X_train.shape}, 測試集大小: {X_test.shape}")
            return X_train, X_test, y_train, y_test, train_dates, test_dates
        
        except Exception as e:
            logging.error(f"數據分割失敗: {e}")
            traceback.print_exc()
            return None, None, None, None, None, None

    def evaluate_model(self, predictions, actual):
        """評估模型性能
        
        Args:
            predictions: 預測值
            actual: 實際值
            
        Returns:
            dict: 性能指標
        """
        try:
            # 確保長度一致
            min_len = min(len(predictions), len(actual))
            pred = predictions[:min_len]
            act = actual[:min_len]
            
            # 計算指標
            mae = mean_absolute_error(act, pred)
            mse = mean_squared_error(act, pred)
            rmse = np.sqrt(mse)
            r2 = r2_score(act, pred)
            
            return {
                'mae': mae,
                'mse': mse,
                'rmse': rmse,
                'r2': r2
            }
        
        except Exception as e:
            logging.error(f"模型評估失敗: {e}")
            return {
                'mae': float('inf'),
                'mse': float('inf'),
                'rmse': float('inf'),
                'r2': float('-inf')
            }

    def feature_engineering(self, X_train, X_test=None):
        """對數據進行特徵工程
        
        Args:
            X_train (pd.DataFrame): 訓練集特徵
            X_test (pd.DataFrame, optional): 測試集特徵
            
        Returns:
            tuple: 處理後的訓練集和測試集特徵
        """
        try:
            logging.info("進行特徵工程...")
            
            # 檢查配置
            fe_config = self.config.get('FEATURE_ENGINEERING', {})
            use_time_features = fe_config.get('use_time_features', True)
            use_lag_features = fe_config.get('use_lag_features', True)
            use_rolling_features = fe_config.get('use_rolling_features', True)
            max_lag_days = fe_config.get('max_lag_days', 7)
            rolling_windows = fe_config.get('rolling_windows', [24, 48, 96])
            
            # 處理訓練集
            X_train_processed = X_train.copy()
            
            # 時間特徵
            if use_time_features:
                X_train_processed = self._add_time_features(X_train_processed)
            
            # 處理測試集（如果有）
            if X_test is not None:
                X_test_processed = X_test.copy()
                
                # 時間特徵
                if use_time_features:
                    X_test_processed = self._add_time_features(X_test_processed)
                
                # 確保訓練集和測試集有相同的列
                common_cols = list(set(X_train_processed.columns) & set(X_test_processed.columns))
                X_train_processed = X_train_processed[common_cols]
                X_test_processed = X_test_processed[common_cols]
                
                return X_train_processed, X_test_processed
            
            return X_train_processed, None
            
        except Exception as e:
            logging.error(f"特徵工程失敗: {str(e)}")
            traceback.print_exc()
            
            # 返回原始數據
            return X_train, X_test
    
    def _add_time_features(self, X):
        """添加時間特徵
        
        Args:
            X (pd.DataFrame): 輸入特徵
            
        Returns:
            pd.DataFrame: 添加時間特徵後的特徵
        """
        # 確保索引是時間類型
        if not isinstance(X.index, pd.DatetimeIndex):
            logging.warning("索引不是時間類型，無法添加時間特徵")
            return X
        
        X_new = X.copy()
        
        # 添加時間特徵
        X_new['hour'] = X_new.index.hour
        X_new['day'] = X_new.index.day
        X_new['month'] = X_new.index.month
        X_new['dayofweek'] = X_new.index.dayofweek
        X_new['is_weekend'] = X_new.index.dayofweek >= 5
        
        # 添加季節性特徵
        X_new['sin_hour'] = np.sin(2 * np.pi * X_new.index.hour / 24)
        X_new['cos_hour'] = np.cos(2 * np.pi * X_new.index.hour / 24)
        X_new['sin_day'] = np.sin(2 * np.pi * X_new.index.day / 31)
        X_new['cos_day'] = np.cos(2 * np.pi * X_new.index.day / 31)
        X_new['sin_month'] = np.sin(2 * np.pi * X_new.index.month / 12)
        X_new['cos_month'] = np.cos(2 * np.pi * X_new.index.month / 12)
        X_new['sin_weekday'] = np.sin(2 * np.pi * X_new.index.dayofweek / 7)
        X_new['cos_weekday'] = np.cos(2 * np.pi * X_new.index.dayofweek / 7)
        
        return X_new 