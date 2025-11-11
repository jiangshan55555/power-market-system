#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
LSTM神經網絡預測模型模塊
"""

import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping
from sklearn.preprocessing import MinMaxScaler, StandardScaler
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
import keras_tuner as kt
import time
import logging

class LSTMModel:
    """LSTM神經網絡電價預測模型"""
    
    def __init__(self, config=None):
        """初始化LSTM模型
        
        Args:
            config: 模型配置參數
        """
        # 默認配置
        self.config = {
            'LSTM_PARAMS': {
                'look_back_days': 7,
                'lstm_units_range': [64, 128],
                'dropout_range': [0.2, 0.4],
                'epochs': 30,
                'batch_size_range': [32, 64],
                'patience': 5,
                'T': 1
            },
            'HYPERPARAMETER_TUNING': {
                'LSTM_SEARCH_ITERATIONS': 5,
            }
        }
        
        # 使用傳入的配置覆蓋默認配置
        if config:
            if 'LSTM_PARAMS' in config:
                self.config['LSTM_PARAMS'].update(config['LSTM_PARAMS'])
            if 'HYPERPARAMETER_TUNING' in config:
                self.config['HYPERPARAMETER_TUNING'].update(config['HYPERPARAMETER_TUNING'])
        
        self.model = None
        self.X_scaler = None
        self.y_scaler = None
        self.best_params = None
    
    def _prepare_lstm_data(self, X_data, y_data):
        """準備LSTM的序列數據
        
        Args:
            X_data: 特徵數據
            y_data: 目標數據
            
        Returns:
            tuple: (X序列數據, y目標數據)
        """
        look_back_days = self.config['LSTM_PARAMS']['look_back_days']
        
        if isinstance(X_data, pd.DataFrame):
            X_data = X_data.values
        
        if isinstance(y_data, pd.Series):
            y_data = y_data.values
            
        # 將數據按時間重塑為序列
        X_sequences = []
        y_targets = []
        
        for i in range(len(X_data) - look_back_days):
            X_sequences.append(X_data[i:i + look_back_days])
            y_targets.append(y_data[i + look_back_days])
        
        return np.array(X_sequences), np.array(y_targets)
    
    def _build_lstm_model(self, input_shape, hp=None):
        """構建LSTM模型
        
        Args:
            input_shape: 輸入形狀 (look_back_days, 特徵數)
            hp: Keras調諧器超參數
            
        Returns:
            tensorflow.keras.models.Sequential: LSTM模型
        """
        # 如果未提供hp，使用默認值
        if hp is None:
            lstm_units = self.config['LSTM_PARAMS']['lstm_units_range'][0]
            dropout_rate = self.config['LSTM_PARAMS']['dropout_range'][0]
        else:
            lstm_units = hp.Int('lstm_units', 
                               min_value=self.config['LSTM_PARAMS']['lstm_units_range'][0],
                               max_value=self.config['LSTM_PARAMS']['lstm_units_range'][1],
                               step=16)
            dropout_rate = hp.Float('dropout_rate',
                                  min_value=self.config['LSTM_PARAMS']['dropout_range'][0],
                                  max_value=self.config['LSTM_PARAMS']['dropout_range'][1],
                                  step=0.1)
        
        # 建立模型
        model = Sequential()
        model.add(LSTM(units=lstm_units, input_shape=input_shape, return_sequences=True))
        model.add(Dropout(dropout_rate))
        model.add(LSTM(units=lstm_units // 2))
        model.add(Dropout(dropout_rate))
        model.add(Dense(1))
        
        # 編譯模型
        model.compile(optimizer='adam', loss='mse')
        
        return model
    
    def _model_builder(self, hp):
        """用於Keras Tuner的模型構建函數
        
        Args:
            hp: Keras調諧器超參數
            
        Returns:
            tensorflow.keras.models.Sequential: LSTM模型
        """
        input_shape = self.input_shape
        model = self._build_lstm_model(input_shape, hp)
        
        return model
    
    def train(self, X_train, y_train):
        """訓練LSTM模型
        
        Args:
            X_train: 訓練特徵
            y_train: 訓練目標
            
        Returns:
            self: 訓練好的模型實例
        """
        start_time = time.time()
        logging.info("開始LSTM模型訓練...")
        
        # 檢查數據
        if X_train is None or y_train is None:
            logging.error("訓練數據無效")
            return None
        
        try:
            # 標準化特徵
            self.X_scaler = StandardScaler()
            X_train_scaled = self.X_scaler.fit_transform(X_train)
            
            # 標準化目標
            self.y_scaler = StandardScaler()
            y_train_scaled = self.y_scaler.fit_transform(y_train.values.reshape(-1, 1)).flatten()
            
            # 準備LSTM序列
            X_train_seq, y_train_seq = self._prepare_lstm_data(X_train_scaled, y_train_scaled)
            
            if len(X_train_seq) == 0:
                logging.error("LSTM序列數據為空")
                return None
                
            # 保存輸入形狀
            self.input_shape = X_train_seq.shape[1:]
            
            # 超參數調優
            search_iterations = self.config['HYPERPARAMETER_TUNING']['LSTM_SEARCH_ITERATIONS']
            epochs = self.config['LSTM_PARAMS']['epochs']
            patience = self.config['LSTM_PARAMS']['patience']
            
            # 設置批量大小
            batch_size = self.config['LSTM_PARAMS']['batch_size_range'][0]
            
            if search_iterations > 1:
                logging.info(f"使用 {search_iterations} 次搜索進行LSTM超參數優化")
                
                # 創建調諧器
                tuner = kt.Hyperband(
                    self._model_builder,
                    objective='val_loss',
                    max_epochs=epochs,
                    factor=3,
                    directory='lstm_tuning',
                    project_name='lstm_price_prediction'
                )
                
                # 早停
                early_stopping = EarlyStopping(
                    monitor='val_loss',
                    patience=patience,
                    restore_best_weights=True
                )
                
                # 搜索超參數
                tuner.search(
                    X_train_seq, y_train_seq,
                    epochs=epochs,
                    batch_size=batch_size,
                    validation_split=0.2,
                    callbacks=[early_stopping]
                )
                
                # 獲取最佳超參數
                best_hps = tuner.get_best_hyperparameters(num_trials=1)[0]
                self.best_params = {
                    'lstm_units': best_hps.get('lstm_units'),
                    'dropout_rate': best_hps.get('dropout_rate'),
                    'batch_size': batch_size,
                    'epochs': epochs
                }
                
                # 獲取最佳模型
                self.model = tuner.hypermodel.build(best_hps)
                
                logging.info(f"最佳LSTM參數: {self.best_params}")
                
                # 使用最佳參數訓練模型
                early_stopping = EarlyStopping(
                    monitor='val_loss',
                    patience=patience,
                    restore_best_weights=True
                )
                
                self.model.fit(
                    X_train_seq, y_train_seq,
                    epochs=epochs,
                    batch_size=batch_size,
                    validation_split=0.2,
                    callbacks=[early_stopping],
                    verbose=1
                )
                
            else:
                # 直接使用默認參數訓練
                logging.info("使用默認參數訓練LSTM模型")
                
                self.model = self._build_lstm_model(self.input_shape)
                self.best_params = {
                    'lstm_units': self.config['LSTM_PARAMS']['lstm_units_range'][0],
                    'dropout_rate': self.config['LSTM_PARAMS']['dropout_range'][0],
                    'batch_size': batch_size,
                    'epochs': epochs
                }
                
                early_stopping = EarlyStopping(
                    monitor='val_loss',
                    patience=patience,
                    restore_best_weights=True
                )
                
                self.model.fit(
                    X_train_seq, y_train_seq,
                    epochs=epochs,
                    batch_size=batch_size,
                    validation_split=0.2,
                    callbacks=[early_stopping],
                    verbose=1
                )
                
            logging.info(f"LSTM模型訓練完成，耗時 {time.time() - start_time:.2f} 秒")
            
            return self
            
        except Exception as e:
            logging.error(f"LSTM模型訓練失敗: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def predict(self, X_test):
        """使用訓練好的模型進行預測
        
        Args:
            X_test: 測試特徵
            
        Returns:
            np.ndarray: 預測結果
        """
        if self.model is None or self.X_scaler is None or self.y_scaler is None:
            logging.error("模型未訓練或缺少轉換器，無法進行預測")
            return None
        
        try:
            # 標準化特徵
            X_test_scaled = self.X_scaler.transform(X_test)
            
            # 準備LSTM序列
            look_back_days = self.config['LSTM_PARAMS']['look_back_days']
            
            # 我們需要特殊處理時間序列預測
            # 如果測試集的長度小於回溯天數，我們需要使用部分訓練集數據
            if len(X_test) < look_back_days:
                logging.warning(f"測試集長度 {len(X_test)} 小於回溯天數 {look_back_days}，需要額外數據進行預測")
                return None
            
            # 我們預測測試集中的每一天
            predictions = []
            
            for i in range(len(X_test) - look_back_days + 1):
                X_sequence = X_test_scaled[i:i + look_back_days].reshape(1, look_back_days, X_test.shape[1])
                pred = self.model.predict(X_sequence, verbose=0)[0][0]
                predictions.append(pred)
            
            # 反向轉換預測結果
            predictions = np.array(predictions).reshape(-1, 1)
            predictions = self.y_scaler.inverse_transform(predictions).flatten()
            
            return predictions
            
        except Exception as e:
            logging.error(f"LSTM預測失敗: {e}")
            import traceback
            traceback.print_exc()
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
            
            # 由於預測結果可能較少（因為需要look_back_days個數據點來預測一個值）
            # 我們需要調整實際值以匹配預測結果的長度
            look_back_days = self.config['LSTM_PARAMS']['look_back_days']
            y_test_adjusted = y_test.iloc[look_back_days-1:].values[:len(y_pred)]
            
            # 計算指標
            r2 = r2_score(y_test_adjusted, y_pred)
            mae = mean_absolute_error(y_test_adjusted, y_pred)
            rmse = np.sqrt(mean_squared_error(y_test_adjusted, y_pred))
            
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
            import traceback
            traceback.print_exc()
            return None
    
    def get_params(self):
        """獲取模型參數
        
        Returns:
            dict: 模型參數
        """
        return self.best_params
