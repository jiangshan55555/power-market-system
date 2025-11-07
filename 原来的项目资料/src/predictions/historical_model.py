#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
歷史同期預測模型模塊
基於歷史同期數據進行預測
"""

import pandas as pd
import numpy as np
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
import logging

class HistoricalModel:
    """歷史同期電價預測模型"""
    
    def __init__(self, config=None):
        """初始化歷史同期模型
        
        Args:
            config: 模型配置參數
        """
        # 默認配置
        self.config = {
            'HISTORICAL_PARAMS': {
                'max_days_back': 14,     # 最大回溯天數（同一個月內）
                'min_samples': 1,         # 最小樣本數
                'fallback_to_hour': True, # 是否在無同期數據時使用同小時數據
                'use_mean_fallback': True # 是否在無數據時使用均值
            }
        }
        
        # 使用傳入的配置覆蓋默認配置
        if config and 'HISTORICAL_PARAMS' in config:
            for key, value in config['HISTORICAL_PARAMS'].items():
                self.config['HISTORICAL_PARAMS'][key] = value
        
        self.model_name = 'Historical'
        self.trained = False
        self.historical_data = None
        self.target_column = None
    
    def train(self, X_train, y_train):
        """訓練模型（對於歷史模型，只是存儲歷史數據）
        
        Args:
            X_train: 訓練特徵
            y_train: 訓練目標
            
        Returns:
            self: 訓練後的模型
        """
        logging.info("準備歷史同期預測模型...")
        
        # 存儲目標列名
        self.target_column = y_train.name if hasattr(y_train, 'name') else None
        
        # 合併特徵和目標，確保索引一致
        self.historical_data = None
        
        # 檢查輸入數據格式
        if isinstance(X_train, pd.DataFrame) and hasattr(y_train, 'values'):
            # 檢查索引是否為時間類型
            if isinstance(X_train.index, pd.DatetimeIndex):
                self.historical_data = pd.DataFrame(index=X_train.index)
                self.historical_data[self.target_column] = y_train
                logging.info(f"歷史同期模型準備完成，共 {len(self.historical_data)} 筆歷史記錄")
                self.trained = True
            else:
                logging.error("訓練數據索引不是時間類型，無法使用歷史同期模型")
        else:
            logging.error("訓練數據格式不正確，需要pandas DataFrame和Series")
        
        return self
    
    def predict(self, X_test):
        """使用歷史同期數據進行預測
        
        Args:
            X_test: 測試特徵或日期索引
            
        Returns:
            np.ndarray: 預測結果
        """
        if not self.trained or self.historical_data is None:
            logging.error("模型尚未訓練，無法進行預測")
            return None
        
        # 檢查測試數據是否為DataFrame且索引為時間類型，或者直接是時間索引
        test_dates = None
        if isinstance(X_test, pd.DataFrame) and isinstance(X_test.index, pd.DatetimeIndex):
            test_dates = X_test.index
        elif isinstance(X_test, pd.DatetimeIndex):
            test_dates = X_test
        elif isinstance(X_test, list) and all(isinstance(x, (pd.Timestamp, np.datetime64)) for x in X_test):
            test_dates = pd.DatetimeIndex(X_test)
        else:
            logging.error("測試數據格式不正確，需要pandas DataFrame且索引為時間類型，或者直接是時間索引")
            return None
        
        logging.info(f"使用歷史同期模型預測 {len(test_dates)} 筆數據...")
        
        # 簡化預測方法：對每個預測時間點，找出相同小時和星期幾的歷史數據
        predictions = []
        
        for dt in test_dates:
            hour = dt.hour
            dayofweek = dt.dayofweek
            
            # 找出相同小時和星期幾的所有歷史數據（且時間在預測時間之前）
            same_hour_day_data = self.historical_data[
                (self.historical_data.index < dt) &
                (self.historical_data.index.hour == hour) & 
                (self.historical_data.index.dayofweek == dayofweek)
            ]
            
            if len(same_hour_day_data) > 0:
                # 使用這些數據的平均值作為預測結果
                predictions.append(same_hour_day_data[self.target_column].mean())
            else:
                # 如果沒有找到相同小時和星期幾的數據，則使用相同小時的所有歷史數據
                same_hour_data = self.historical_data[
                    (self.historical_data.index < dt) &
                    (self.historical_data.index.hour == hour)
                ]
                
                if len(same_hour_data) > 0:
                    predictions.append(same_hour_data[self.target_column].mean())
                else:
                    # 如果還是找不到，使用所有歷史數據的平均值
                    predictions.append(self.historical_data[self.target_column].mean())
        
        logging.info("歷史同期預測完成")
        return np.array(predictions)
    
    def evaluate(self, X_test, y_test):
        """評估模型性能
        
        Args:
            X_test: 測試特徵
            y_test: 測試目標
            
        Returns:
            dict: 性能指標
        """
        if not self.trained:
            logging.error("模型尚未訓練，無法評估")
            return {}
        
        # 進行預測
        y_pred = self.predict(X_test)
        
        if y_pred is None or len(y_pred) == 0:
            logging.error("預測失敗，無法評估")
            return {}
        
        # 計算性能指標
        metrics = {}
        try:
            metrics['r2'] = r2_score(y_test, y_pred)
            metrics['mae'] = mean_absolute_error(y_test, y_pred)
            metrics['rmse'] = np.sqrt(mean_squared_error(y_test, y_pred))
            
            logging.info(f"歷史同期模型評估結果: R² = {metrics['r2']:.4f}, MAE = {metrics['mae']:.2f}, RMSE = {metrics['rmse']:.2f}")
        except Exception as e:
            logging.error(f"計算性能指標時出錯: {e}")
        
        return metrics
    
    def get_params(self):
        """獲取模型參數
        
        Returns:
            dict: 模型參數
        """
        return self.config['HISTORICAL_PARAMS']
    
    def get_feature_importance(self):
        """獲取特徵重要性（歷史模型不適用）
        
        Returns:
            None: 歷史模型不支持特徵重要性
        """
        return None 