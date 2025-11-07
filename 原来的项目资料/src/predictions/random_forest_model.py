#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
隨機森林預測模型
"""

import numpy as np
import pandas as pd
import logging
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.model_selection import RandomizedSearchCV

class RandomForestModel:
    """隨機森林電價預測模型"""
    
    def __init__(self, config=None):
        """初始化隨機森林模型
        
        Args:
            config: 配置字典，包含超參數調整設置
        """
        self.model = None
        self.best_params = None
        self.feature_importance = None
        self.config = config
    
    def train(self, X_train, y_train):
        """訓練模型
        
        Args:
            X_train: 訓練特徵
            y_train: 訓練目標
        """
        logging.info("開始訓練隨機森林模型...")
        
        # 檢查數據
        if X_train is None or y_train is None:
            logging.error("訓練數據為空")
            return False
        
        try:
            # 定義參數網格
            param_grid = {
                'n_estimators': [100, 200, 300],
                'max_depth': [None, 10, 20, 30],
                'min_samples_split': [2, 5, 10],
                'min_samples_leaf': [1, 2, 4],
                'bootstrap': [True, False]
            }
            
            # 創建基礎模型
            rf = RandomForestRegressor(random_state=42)
            
            # 根據配置決定是否使用交叉驗證
            cv_folds = 3  # 默認值
            n_iter = 10   # 默認值
            
            if self.config and 'HYPERPARAMETER_TUNING' in self.config:
                cv_folds = self.config['HYPERPARAMETER_TUNING'].get('CV_FOLDS', 3)
                n_iter = self.config['HYPERPARAMETER_TUNING'].get('RF_SEARCH_ITERATIONS', 5)
                
            if cv_folds == 1:
                # 快速模式：不使用交叉驗證
                logging.info(f"快速模式：使用 {n_iter} 次迭代進行隨機參數搜索（無交叉驗證）")
                
                # 隨機嘗試幾組參數
                best_score = float('inf')
                best_params = None
                best_model = None
                
                from sklearn.model_selection import train_test_split
                # 分割驗證集
                X_tr, X_val, y_tr, y_val = train_test_split(X_train, y_train, test_size=0.2, random_state=42)
                
                # 嘗試不同參數
                import random
                for _ in range(n_iter):
                    params = {
                        'n_estimators': random.choice(param_grid['n_estimators']),
                        'max_depth': random.choice(param_grid['max_depth']),
                        'min_samples_split': random.choice(param_grid['min_samples_split']),
                        'min_samples_leaf': random.choice(param_grid['min_samples_leaf']),
                        'bootstrap': random.choice(param_grid['bootstrap'])
                    }
                    
                    # 創建並訓練模型
                    model = RandomForestRegressor(random_state=42, **params)
                    model.fit(X_tr, y_tr)
                    
                    # 評估模型
                    pred = model.predict(X_val)
                    score = mean_absolute_error(y_val, pred)
                    
                    # 如果更好則保存
                    if score < best_score:
                        best_score = score
                        best_params = params
                        best_model = model
                
                self.model = best_model
                self.best_params = best_params
                
            else:
                # 標準模式：使用交叉驗證
                logging.info(f"使用 {n_iter} 次迭代和 {cv_folds} 折交叉驗證進行超參數搜索")
                
                # 隨機搜索
                random_search = RandomizedSearchCV(
                    estimator=rf,
                    param_distributions=param_grid,
                    n_iter=n_iter,
                    cv=cv_folds,
                    verbose=0,
                    random_state=42,
                    n_jobs=-1
                )
                
                # 訓練模型
                random_search.fit(X_train, y_train)
                
                # 保存最佳模型
                self.model = random_search.best_estimator_
                self.best_params = random_search.best_params_
            
            # 計算特徵重要性
            if hasattr(X_train, 'columns'):
                feature_names = X_train.columns
            else:
                feature_names = [f'feature_{i}' for i in range(X_train.shape[1])]

            self.feature_importance = pd.Series(
                self.model.feature_importances_,
                index=feature_names
            ).sort_values(ascending=False)
            
            logging.info(f"隨機森林模型訓練完成，最佳參數: {self.best_params}")
            logging.info(f"前5個重要特徵: {self.feature_importance.head(5).to_dict()}")
            
            return True
            
        except Exception as e:
            logging.error(f"隨機森林模型訓練失敗: {e}")
            return False
    
    def predict(self, X_test):
        """使用模型進行預測
        
        Args:
            X_test: 測試特徵
            
        Returns:
            numpy.ndarray: 預測結果
        """
        if self.model is None:
            logging.error("模型尚未訓練")
            return None
        
        try:
            predictions = self.model.predict(X_test)
            logging.info(f"隨機森林模型預測完成，結果大小: {len(predictions)}")
            return predictions
        
        except Exception as e:
            logging.error(f"隨機森林模型預測失敗: {e}")
            return None
    
    def evaluate(self, X_test, y_test):
        """評估模型性能
        
        Args:
            X_test: 測試特徵
            y_test: 測試目標
            
        Returns:
            dict: 評估指標
        """
        if self.model is None:
            logging.error("模型尚未訓練")
            return None
        
        try:
            # 預測
            y_pred = self.predict(X_test)
            
            # 計算指標
            mae = mean_absolute_error(y_test, y_pred)
            rmse = np.sqrt(mean_squared_error(y_test, y_pred))
            r2 = r2_score(y_test, y_pred)
            
            metrics = {
                'mae': mae,
                'rmse': rmse,
                'r2': r2
            }
            
            logging.info(f"隨機森林模型評估指標: MAE={mae:.4f}, RMSE={rmse:.4f}, R²={r2:.4f}")
            return metrics
            
        except Exception as e:
            logging.error(f"隨機森林模型評估失敗: {e}")
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
