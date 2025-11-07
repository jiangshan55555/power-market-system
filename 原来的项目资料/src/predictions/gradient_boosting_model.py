#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
梯度提升决策树(GBDT)电价预测模型
基于sklearn的GradientBoostingRegressor实现
"""

import pandas as pd
import numpy as np
import logging
import time
import traceback
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import RandomizedSearchCV
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

class GradientBoostingModel:
    """梯度提升决策树(GBDT)电价预测模型"""
    
    def __init__(self, config=None):
        """初始化GBDT模型
        
        Args:
            config: 模型配置参数
        """
        # 默认配置
        self.config = {
            'GBDT_SEARCH_SPACE': {
                'n_estimators': [50, 100, 200, 300],
                'learning_rate': [0.01, 0.05, 0.1, 0.2],
                'max_depth': [3, 5, 7, 9],
                'min_samples_split': [2, 5, 10],
                'min_samples_leaf': [1, 2, 4],
                'subsample': [0.8, 0.9, 1.0],
                'max_features': ['sqrt', 'log2', None]
            },
            'HYPERPARAMETER_TUNING': {
                'GBDT_SEARCH_ITERATIONS': 20,
                'CV_FOLDS': 3
            }
        }
        
        # 使用传入的配置覆盖默认配置
        if config:
            if 'GBDT_PARAMS' in config:
                self.config['GBDT_SEARCH_SPACE'] = config['GBDT_PARAMS']
            if 'HYPERPARAMETER_TUNING' in config:
                self.config['HYPERPARAMETER_TUNING'].update(config['HYPERPARAMETER_TUNING'])
        
        self.model = None
        self.feature_importance = None
        self.best_params = None
    
    def train(self, X_train, y_train, hyperparameter_tuning=True):
        """训练GBDT模型
        
        Args:
            X_train: 训练特征
            y_train: 训练目标
            hyperparameter_tuning: 是否进行超参数调优
            
        Returns:
            self: 训练后的模型实例
        """
        start_time = time.time()
        logging.info("开始训练梯度提升决策树(GBDT)模型...")
        
        try:
            if hyperparameter_tuning:
                # 超参数调优模式
                search_space = self.config['GBDT_SEARCH_SPACE']
                search_iter = self.config['HYPERPARAMETER_TUNING']['GBDT_SEARCH_ITERATIONS']
                cv_folds = self.config['HYPERPARAMETER_TUNING']['CV_FOLDS']
                
                logging.info(f"使用 {search_iter} 次迭代和 {cv_folds} 折交叉验证进行超参数搜索")
                
                gbdt_model = GradientBoostingRegressor(random_state=42)
                random_search = RandomizedSearchCV(
                    estimator=gbdt_model,
                    param_distributions=search_space,
                    n_iter=search_iter,
                    cv=cv_folds,
                    random_state=42,
                    n_jobs=-1,
                    verbose=0,
                    scoring='neg_mean_absolute_error'
                )
                
                # 拟合模型
                random_search.fit(X_train, y_train)
                
                # 保存最佳模型和参数
                self.model = random_search.best_estimator_
                self.best_params = random_search.best_params_
                
            else:
                # 快速模式：使用默认参数
                logging.info("快速模式：使用默认参数训练GBDT模型")
                self.model = GradientBoostingRegressor(
                    n_estimators=100,
                    learning_rate=0.1,
                    max_depth=5,
                    random_state=42
                )
                self.model.fit(X_train, y_train)
                self.best_params = self.model.get_params()
            
            # 特征重要性
            self.feature_importance = pd.Series(
                self.model.feature_importances_, 
                index=X_train.columns if hasattr(X_train, 'columns') else range(X_train.shape[1])
            ).sort_values(ascending=False)
            
            logging.info(f"GBDT模型训练完成，耗时 {time.time() - start_time:.2f} 秒")
            if self.best_params:
                logging.info(f"最佳参数: {self.best_params}")
            logging.info(f"前5个重要特征: {self.feature_importance.head(5).to_dict()}")
            
            return self
            
        except Exception as e:
            logging.error(f"GBDT模型训练失败: {e}")
            logging.error(traceback.format_exc())
            return None
    
    def predict(self, X_test):
        """进行预测
        
        Args:
            X_test: 测试特征
            
        Returns:
            np.array: 预测结果
        """
        if self.model is None:
            logging.error("模型未训练，无法进行预测")
            return None
        
        try:
            predictions = self.model.predict(X_test)
            return predictions
        except Exception as e:
            logging.error(f"预测失败: {e}")
            return None
    
    def evaluate(self, X_test, y_test):
        """评估模型性能
        
        Args:
            X_test: 测试特征
            y_test: 测试目标
            
        Returns:
            dict: 包含评估指标的字典
        """
        if self.model is None:
            logging.error("模型未训练，无法进行评估")
            return None
        
        try:
            # 获取预测
            y_pred = self.predict(X_test)
            
            # 计算指标
            r2 = r2_score(y_test, y_pred)
            mae = mean_absolute_error(y_test, y_pred)
            rmse = np.sqrt(mean_squared_error(y_test, y_pred))
            
            # 返回评估结果
            metrics = {
                'r2': r2,
                'mae': mae,
                'rmse': rmse,
            }
            
            logging.info(f"GBDT评估指标: R² = {r2:.4f}, MAE = {mae:.4f}, RMSE = {rmse:.4f}")
            
            return metrics
            
        except Exception as e:
            logging.error(f"评估失败: {e}")
            return None
    
    def get_feature_importance(self):
        """获取特征重要性
        
        Returns:
            pd.Series: 特征重要性
        """
        return self.feature_importance
    
    def get_params(self):
        """获取模型参数
        
        Returns:
            dict: 模型参数
        """
        return self.best_params
    
    def save_model(self, filepath):
        """保存模型
        
        Args:
            filepath: 保存路径
        """
        try:
            import joblib
            joblib.dump(self.model, filepath)
            logging.info(f"GBDT模型已保存到: {filepath}")
        except Exception as e:
            logging.error(f"保存模型失败: {e}")
    
    def load_model(self, filepath):
        """加载模型
        
        Args:
            filepath: 模型文件路径
        """
        try:
            import joblib
            self.model = joblib.load(filepath)
            logging.info(f"GBDT模型已从 {filepath} 加载")
            return self
        except Exception as e:
            logging.error(f"加载模型失败: {e}")
            return None
