#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
线性回归电价预测模型
基于sklearn的LinearRegression实现，支持多种正则化方法
"""

import pandas as pd
import numpy as np
import logging
import time
import traceback
from sklearn.linear_model import LinearRegression, Ridge, Lasso, ElasticNet
from sklearn.model_selection import RandomizedSearchCV
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler

class LinearRegressionModel:
    """线性回归电价预测模型"""
    
    def __init__(self, config=None):
        """初始化线性回归模型
        
        Args:
            config: 模型配置参数
        """
        # 默认配置
        self.config = {
            'LINEAR_SEARCH_SPACE': {
                'model_type': ['linear', 'ridge', 'lasso', 'elastic_net'],
                'ridge_alpha': [0.1, 1.0, 10.0, 100.0],
                'lasso_alpha': [0.01, 0.1, 1.0, 10.0],
                'elastic_alpha': [0.01, 0.1, 1.0, 10.0],
                'elastic_l1_ratio': [0.1, 0.3, 0.5, 0.7, 0.9]
            },
            'HYPERPARAMETER_TUNING': {
                'LINEAR_SEARCH_ITERATIONS': 10,
                'CV_FOLDS': 3,
                'USE_SCALING': True
            }
        }
        
        # 使用传入的配置覆盖默认配置
        if config:
            if 'LINEAR_PARAMS' in config:
                self.config['LINEAR_SEARCH_SPACE'] = config['LINEAR_PARAMS']
            if 'HYPERPARAMETER_TUNING' in config:
                self.config['HYPERPARAMETER_TUNING'].update(config['HYPERPARAMETER_TUNING'])
        
        self.model = None
        self.scaler = None
        self.best_params = None
        self.model_type = 'linear'
    
    def train(self, X_train, y_train, hyperparameter_tuning=True):
        """训练线性回归模型
        
        Args:
            X_train: 训练特征
            y_train: 训练目标
            hyperparameter_tuning: 是否进行超参数调优
            
        Returns:
            self: 训练后的模型实例
        """
        start_time = time.time()
        logging.info("开始训练线性回归模型...")
        
        try:
            # 数据标准化
            use_scaling = self.config['HYPERPARAMETER_TUNING'].get('USE_SCALING', True)
            if use_scaling:
                self.scaler = StandardScaler()
                X_train_scaled = self.scaler.fit_transform(X_train)
            else:
                X_train_scaled = X_train
            
            if hyperparameter_tuning:
                # 超参数调优模式
                search_iter = self.config['HYPERPARAMETER_TUNING']['LINEAR_SEARCH_ITERATIONS']
                cv_folds = self.config['HYPERPARAMETER_TUNING']['CV_FOLDS']
                
                logging.info(f"使用 {search_iter} 次迭代和 {cv_folds} 折交叉验证进行模型选择")
                
                best_score = float('inf')
                best_model = None
                best_params = None
                
                # 尝试不同的线性模型
                model_types = self.config['LINEAR_SEARCH_SPACE']['model_type']
                
                for model_type in model_types:
                    if model_type == 'linear':
                        # 普通线性回归
                        model = LinearRegression()
                        param_grid = {}
                        
                    elif model_type == 'ridge':
                        # Ridge回归
                        model = Ridge(random_state=42)
                        param_grid = {
                            'alpha': self.config['LINEAR_SEARCH_SPACE']['ridge_alpha']
                        }
                        
                    elif model_type == 'lasso':
                        # Lasso回归
                        model = Lasso(random_state=42, max_iter=2000)
                        param_grid = {
                            'alpha': self.config['LINEAR_SEARCH_SPACE']['lasso_alpha']
                        }
                        
                    elif model_type == 'elastic_net':
                        # ElasticNet回归
                        model = ElasticNet(random_state=42, max_iter=2000)
                        param_grid = {
                            'alpha': self.config['LINEAR_SEARCH_SPACE']['elastic_alpha'],
                            'l1_ratio': self.config['LINEAR_SEARCH_SPACE']['elastic_l1_ratio']
                        }
                    
                    # 如果有参数需要调优
                    if param_grid:
                        search = RandomizedSearchCV(
                            estimator=model,
                            param_distributions=param_grid,
                            n_iter=min(search_iter, len(param_grid.get('alpha', [1]))),
                            cv=cv_folds,
                            random_state=42,
                            n_jobs=-1,
                            verbose=0,
                            scoring='neg_mean_absolute_error'
                        )
                        search.fit(X_train_scaled, y_train)
                        current_model = search.best_estimator_
                        current_score = -search.best_score_
                        current_params = {'model_type': model_type, **search.best_params_}
                    else:
                        # 普通线性回归，无需调参
                        model.fit(X_train_scaled, y_train)
                        pred = model.predict(X_train_scaled)
                        current_score = mean_absolute_error(y_train, pred)
                        current_model = model
                        current_params = {'model_type': model_type}
                    
                    # 更新最佳模型
                    if current_score < best_score:
                        best_score = current_score
                        best_model = current_model
                        best_params = current_params
                        self.model_type = model_type
                
                self.model = best_model
                self.best_params = best_params
                
            else:
                # 快速模式：使用普通线性回归
                logging.info("快速模式：使用普通线性回归")
                self.model = LinearRegression()
                self.model.fit(X_train_scaled, y_train)
                self.best_params = {'model_type': 'linear'}
                self.model_type = 'linear'
            
            logging.info(f"线性回归模型训练完成，耗时 {time.time() - start_time:.2f} 秒")
            logging.info(f"选择的模型类型: {self.model_type}")
            if self.best_params:
                logging.info(f"最佳参数: {self.best_params}")
            
            return self
            
        except Exception as e:
            logging.error(f"线性回归模型训练失败: {e}")
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
            # 应用相同的标准化
            if self.scaler is not None:
                X_test_scaled = self.scaler.transform(X_test)
            else:
                X_test_scaled = X_test
                
            predictions = self.model.predict(X_test_scaled)
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
            
            logging.info(f"线性回归评估指标: R² = {r2:.4f}, MAE = {mae:.4f}, RMSE = {rmse:.4f}")
            
            return metrics
            
        except Exception as e:
            logging.error(f"评估失败: {e}")
            return None
    
    def get_coefficients(self):
        """获取模型系数
        
        Returns:
            dict: 模型系数信息
        """
        if self.model is None:
            return None
            
        try:
            coef_info = {
                'model_type': self.model_type,
                'coefficients': self.model.coef_.tolist() if hasattr(self.model, 'coef_') else None,
                'intercept': float(self.model.intercept_) if hasattr(self.model, 'intercept_') else None
            }
            return coef_info
        except Exception as e:
            logging.error(f"获取系数失败: {e}")
            return None
    
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
            model_data = {
                'model': self.model,
                'scaler': self.scaler,
                'model_type': self.model_type,
                'best_params': self.best_params
            }
            joblib.dump(model_data, filepath)
            logging.info(f"线性回归模型已保存到: {filepath}")
        except Exception as e:
            logging.error(f"保存模型失败: {e}")
    
    def load_model(self, filepath):
        """加载模型
        
        Args:
            filepath: 模型文件路径
        """
        try:
            import joblib
            model_data = joblib.load(filepath)
            self.model = model_data['model']
            self.scaler = model_data.get('scaler')
            self.model_type = model_data.get('model_type', 'linear')
            self.best_params = model_data.get('best_params')
            logging.info(f"线性回归模型已从 {filepath} 加载")
            return self
        except Exception as e:
            logging.error(f"加载模型失败: {e}")
            return None
