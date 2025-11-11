#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
XGBoost預測模型模塊
"""

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import RandomizedSearchCV
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
import time
import logging
import traceback

class XGBoostModel:
    """XGBoost電價預測模型"""
    
    def __init__(self, config=None):
        """初始化XGBoost模型
        
        Args:
            config: 模型配置參數
        """
        # 默認配置
        self.config = {
            'XGB_SEARCH_SPACE': {
                'n_estimators': [100, 200, 300, 500],
                'learning_rate': [0.01, 0.05, 0.1],
                'max_depth': [3, 5, 7],
                'subsample': [0.7, 0.8, 0.9],
                'colsample_bytree': [0.7, 0.8, 0.9],
                'min_child_weight': [1, 3, 5]
            },
            'HYPERPARAMETER_TUNING': {
                'XGB_SEARCH_ITERATIONS': 20,
                'CV_FOLDS': 3
            }
        }
        
        # 使用傳入的配置覆蓋默認配置
        if config:
            if 'XGB_PARAMS' in config:
                self.config['XGB_SEARCH_SPACE'] = config['XGB_PARAMS']
            if 'HYPERPARAMETER_TUNING' in config:
                self.config['HYPERPARAMETER_TUNING'].update(config['HYPERPARAMETER_TUNING'])
        
        self.model = None
        self.feature_importance = None
        self.best_params = None
    
    def train(self, X_train, y_train):
        """訓練XGBoost模型
        
        Args:
            X_train: 訓練特徵
            y_train: 訓練目標
            
        Returns:
            self: 訓練好的模型實例
        """
        start_time = time.time()
        logging.info("開始XGBoost模型訓練...")
        
        # 檢查數據
        if X_train is None or y_train is None:
            logging.error("訓練數據無效")
            return None
        
        try:
            # 設置搜索參數
            search_space = self.config['XGB_SEARCH_SPACE']
            search_iter = self.config['HYPERPARAMETER_TUNING']['XGB_SEARCH_ITERATIONS']
            cv_folds = self.config['HYPERPARAMETER_TUNING']['CV_FOLDS']
            
            # 如果指定只用一折（不做交叉驗證），使用隨機分割策略
            if cv_folds <= 1:
                cv_folds = 2  # sklearn要求至少2折
                logging.info(f"快速模式：使用 {search_iter} 次迭代進行隨機參數搜索（無交叉驗證）")
            else:
                # 隨機搜索超參數
                logging.info(f"使用 {search_iter} 次迭代和 {cv_folds} 折交叉驗證進行超參數搜索")
            
            xgb_model = xgb.XGBRegressor(objective='reg:squarederror', random_state=42)
            random_search = RandomizedSearchCV(
                estimator=xgb_model,
                param_distributions=search_space,
                n_iter=search_iter,
                cv=cv_folds,
                random_state=42,
                n_jobs=-1,
                verbose=0,
                scoring='neg_mean_squared_error'
            )
            
            # 擬合模型
            random_search.fit(X_train, y_train)
            
            # 保存最佳模型和參數
            self.model = random_search.best_estimator_
            self.best_params = random_search.best_params_
            
            # 特徵重要性
            self.feature_importance = pd.Series(
                self.model.feature_importances_, 
                index=X_train.columns if hasattr(X_train, 'columns') else range(X_train.shape[1])
            ).sort_values(ascending=False)
            
            logging.info(f"XGBoost模型訓練完成，耗時 {time.time() - start_time:.2f} 秒")
            logging.info(f"最佳參數: {self.best_params}")
            logging.info(f"前5個重要特徵: {self.feature_importance.head(5).to_dict()}")
            
            return self
            
        except Exception as e:
            logging.error(f"XGBoost模型訓練失敗: {e}")
            logging.error(traceback.format_exc())
            return None
    
    def predict(self, X_test):
        """使用訓練好的模型進行預測
        
        Args:
            X_test: 測試特徵
            
        Returns:
            np.ndarray: 預測結果
        """
        if self.model is None:
            logging.error("模型未訓練，無法進行預測")
            return None
        
        try:
            predictions = self.model.predict(X_test)
            return predictions
        except Exception as e:
            logging.error(f"預測失敗: {e}")
            return None
    
    def evaluate(self, X_test, y_test):
        """評估模型性能
        
        Args:
            X_test: 測試特徵
            y_test: 測試目標
            
        Returns:
            dict: 包含評估指標的字典
        """
        if self.model is None:
            logging.error("模型未訓練，無法進行評估")
            return None
        
        try:
            # 獲取預測
            y_pred = self.predict(X_test)
            
            # 計算指標
            r2 = r2_score(y_test, y_pred)
            mae = mean_absolute_error(y_test, y_pred)
            rmse = np.sqrt(mean_squared_error(y_test, y_pred))
            
            # 返回評估結果
            metrics = {
                'r2': r2,
                'mae': mae,
                'rmse': rmse,
            }
            
            logging.info(f"評估指標: R² = {r2:.4f}, MAE = {mae:.4f}, RMSE = {rmse:.4f}")
            
            return metrics
            
        except Exception as e:
            logging.error(f"評估失敗: {e}")
            return None
    
    def get_feature_importance(self):
        """獲取特徵重要性
        
        Returns:
            pd.Series: 特徵重要性
        """
        return self.feature_importance
    
    def get_params(self):
        """獲取模型參數
        
        Returns:
            dict: 模型參數
        """
        return self.best_params
