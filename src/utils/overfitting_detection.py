#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
過擬合檢測模塊，用於簡單判斷預測模型是否過擬合
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
import logging
from sklearn.metrics import mean_absolute_error, r2_score

class OverfittingDetection:
    """過擬合檢測類，提供簡單的過擬合檢測方法"""
    
    def __init__(self, output_dir='../output/prediction_results/overfitting_analysis', 
                r2_threshold=0.9, error_ratio_threshold=1.5):
        """初始化過擬合檢測器
        
        Args:
            output_dir: 輸出目錄
            r2_threshold: R²閾值，判斷過擬合的參考值
            error_ratio_threshold: 誤差比例閾值，訓練誤差和測試誤差比例超過此值視為過擬合
        """
        self.output_dir = output_dir
        self.r2_threshold = r2_threshold
        self.error_ratio_threshold = error_ratio_threshold
        
        # 創建輸出目錄
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
    
    def detect(self, predictions, actual_values, train_predictions=None, train_actual_values=None):
        """檢測模型是否過擬合
        
        Args:
            predictions: 測試集預測值
            actual_values: 測試集實際值
            train_predictions: 訓練集預測值，如果提供則進行訓練-測試集對比
            train_actual_values: 訓練集實際值，如果提供則進行訓練-測試集對比
            
        Returns:
            dict: 包含過擬合判斷結果和簡要分析
        """
        # 確保輸入為 numpy 數組
        predictions = np.array(predictions) if not isinstance(predictions, np.ndarray) else predictions
        actual_values = np.array(actual_values) if not isinstance(actual_values, np.ndarray) else actual_values
        
        # 計算測試集指標
        test_mae = mean_absolute_error(actual_values, predictions)
        test_r2 = r2_score(actual_values, predictions)
        
        # 初始化結果
        result = {
            'is_overfitting': False,
            'reason': '',
            'test_metrics': {
                'mae': test_mae,
                'r2': test_r2
            }
        }
        
        # 如果提供了訓練集數據，進行訓練-測試集對比
        if train_predictions is not None and train_actual_values is not None:
            train_predictions = np.array(train_predictions) if not isinstance(train_predictions, np.ndarray) else train_predictions
            train_actual_values = np.array(train_actual_values) if not isinstance(train_actual_values, np.ndarray) else train_actual_values
            
            train_mae = mean_absolute_error(train_actual_values, train_predictions)
            train_r2 = r2_score(train_actual_values, train_predictions)
            
            result['train_metrics'] = {
                'mae': train_mae,
                'r2': train_r2
            }
            
            # 檢測過擬合：訓練集表現明顯優於測試集
            if train_r2 > self.r2_threshold and train_r2 - test_r2 > 0.2:
                result['is_overfitting'] = True
                result['reason'] = f"訓練集R²({train_r2:.3f})明顯高於測試集R²({test_r2:.3f})"
                
            # 檢測過擬合：訓練集誤差明顯低於測試集誤差
            if train_mae > 0 and test_mae / train_mae > self.error_ratio_threshold:
                result['is_overfitting'] = True
                result['reason'] = f"測試集MAE({test_mae:.3f})與訓練集MAE({train_mae:.3f})比值過大({test_mae/train_mae:.2f})"
        else:
            # 簡單檢測：預測值變化範圍與實際值相比
            pred_range = np.max(predictions) - np.min(predictions)
            actual_range = np.max(actual_values) - np.min(actual_values)
            range_ratio = pred_range / actual_range if actual_range > 0 else 1.0
            
            if range_ratio < 0.7:
                result['is_overfitting'] = True
                result['reason'] = f"預測值變化範圍({pred_range:.3f})明顯小於實際值範圍({actual_range:.3f})"
                
            # 簡單檢測：R²異常
            if test_r2 < 0:
                result['is_overfitting'] = True
                result['reason'] = f"測試集R²值異常({test_r2:.3f})"
        
        # 如果檢測到過擬合，生成簡單的分析圖
        if result['is_overfitting']:
            self._generate_simple_plot(predictions, actual_values, train_predictions, train_actual_values)
            logging.warning(f"檢測到過擬合：{result['reason']}")
        
        return result
    
    def _generate_simple_plot(self, test_pred, test_actual, train_pred=None, train_actual=None):
        """生成簡單的過擬合分析圖
        
        Args:
            test_pred: 測試集預測值
            test_actual: 測試集實際值
            train_pred: 訓練集預測值
            train_actual: 訓練集實際值
        """
        try:
            plt.figure(figsize=(10, 6))
            
            # 測試集預測與實際值對比散點圖
            plt.scatter(test_actual, test_pred, alpha=0.7, label='測試集', color='blue')
            
            # 如果有訓練集數據，也繪製訓練集散點圖
            if train_pred is not None and train_actual is not None:
                plt.scatter(train_actual, train_pred, alpha=0.5, label='訓練集', color='red')
            
            # 繪製對角線（完美預測線）
            min_val = min(np.min(test_actual), np.min(test_pred))
            max_val = max(np.max(test_actual), np.max(test_pred))
            if train_pred is not None and train_actual is not None:
                min_val = min(min_val, np.min(train_actual), np.min(train_pred))
                max_val = max(max_val, np.max(train_actual), np.max(train_pred))
            
            plt.plot([min_val, max_val], [min_val, max_val], 'k--', label='完美預測')
            
            plt.title('過擬合分析：預測值與實際值對比')
            plt.xlabel('實際值')
            plt.ylabel('預測值')
            plt.legend()
            plt.grid(True)
            
            # 保存圖表
            import datetime
            timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
            filepath = os.path.join(self.output_dir, f'overfitting_{timestamp}.png')
            plt.savefig(filepath, dpi=300)
            plt.close()
            
            logging.info(f"過擬合分析圖已保存至 {filepath}")
            
        except Exception as e:
            logging.error(f"生成過擬合分析圖時出錯: {str(e)}")
            
    def create_report(self, model_results):
        """根據各模型結果創建過擬合報告
        
        Args:
            model_results: 各模型結果字典，格式為 {模型名: {訓練和測試結果}}
            
        Returns:
            str: 報告文件路徑
        """
        try:
            import datetime
            timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
            report_path = os.path.join(self.output_dir, f'overfitting_report_{timestamp}.md')
            
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write("# 模型過擬合分析報告\n\n")
                f.write(f"生成時間: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                f.write("## 各模型過擬合分析結果\n\n")
                f.write("| 模型 | 過擬合判斷 | 原因 | 訓練集MAE | 測試集MAE | 訓練集R² | 測試集R² |\n")
                f.write("|------|------------|------|-----------|----------|---------|--------|\n")
                
                # 對每個模型進行過擬合檢測
                for model_name, model_data in model_results.items():
                    # 跳過集成模型
                    if model_name == 'ensemble':
                        continue
                    
                    # 獲取訓練和測試數據
                    train_pred = model_data.get('train_predictions')
                    train_actual = model_data.get('train_actual')
                    test_pred = model_data.get('predictions')
                    test_actual = model_data.get('test_actual')

                    # 增加健壯性檢查：如果測試數據為空，則跳過
                    if test_pred is None or test_actual is None or len(test_pred) == 0:
                        logging.warning(f"模型 '{model_name}' 缺少有效的測試預測或實際值，跳過過擬合檢測。")
                        f.write(f"| {model_name} | 無法檢測 | 缺少測試數據 | N/A | N/A | N/A | N/A |\n")
                        continue
                    
                    # 如果沒有訓練數據，只使用測試數據
                    if train_pred is None or train_actual is None:
                        result = self.detect(test_pred, test_actual)
                        train_mae = "N/A"
                        train_r2 = "N/A"
                    else:
                        result = self.detect(test_pred, test_actual, train_pred, train_actual)
                        train_mae = f"{result['train_metrics']['mae']:.3f}"
                        train_r2 = f"{result['train_metrics']['r2']:.3f}"
                    
                    # 格式化測試指標
                    test_mae = f"{result['test_metrics']['mae']:.3f}"
                    test_r2 = f"{result['test_metrics']['r2']:.3f}"
                    
                    # 寫入報告
                    f.write(f"| {model_name} | {'是' if result['is_overfitting'] else '否'} | {result['reason']} | {train_mae} | {test_mae} | {train_r2} | {test_r2} |\n")
                
                f.write("\n## 建議\n\n")
                f.write("如檢測到過擬合，可嘗試以下方法：\n\n")
                f.write("1. 增加訓練數據\n")
                f.write("2. 減少模型複雜度\n")
                f.write("3. 增加正則化\n")
                f.write("4. 使用集成方法\n")
                f.write("5. 調整模型超參數\n")
            
            logging.info(f"過擬合報告已保存至 {report_path}")
            return report_path
            
        except Exception as e:
            logging.error(f"創建過擬合報告時出錯: {str(e)}")
            import traceback
            logging.error(traceback.format_exc())
            return None
