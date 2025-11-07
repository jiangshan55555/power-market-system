#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
可視化工具模塊
提供預測結果和投標策略的可視化功能
"""

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import seaborn as sns
from pathlib import Path
import logging

# 配置中文字體
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

class PredictionVisualizer:
    """預測結果可視化器"""
    
    def __init__(self, output_dir='output/predictions'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def plot_prediction_comparison(self, results_df, save_path=None):
        """繪製預測結果對比圖"""
        try:
            fig, axes = plt.subplots(2, 2, figsize=(15, 10))
            fig.suptitle('電力價格預測結果對比', fontsize=16)
            
            # 獲取預測列
            pred_columns = [col for col in results_df.columns if col.endswith('_prediction')]
            
            # 子圖1: 時間序列對比
            ax1 = axes[0, 0]
            ax1.plot(results_df['date'], results_df['actual'], label='實際價格', linewidth=2, color='black')
            
            colors = ['red', 'blue', 'green', 'orange', 'purple']
            for i, col in enumerate(pred_columns):
                model_name = col.replace('_prediction', '').upper()
                ax1.plot(results_df['date'], results_df[col], 
                        label=f'{model_name}預測', alpha=0.7, color=colors[i % len(colors)])
            
            ax1.set_title('預測vs實際價格時間序列')
            ax1.set_xlabel('日期')
            ax1.set_ylabel('價格 (CNY/MWh)')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # 子圖2: 散點圖
            ax2 = axes[0, 1]
            for i, col in enumerate(pred_columns):
                model_name = col.replace('_prediction', '').upper()
                ax2.scatter(results_df['actual'], results_df[col], 
                           alpha=0.6, label=model_name, color=colors[i % len(colors)])
            
            # 添加理想線
            min_val = min(results_df['actual'].min(), min([results_df[col].min() for col in pred_columns]))
            max_val = max(results_df['actual'].max(), max([results_df[col].max() for col in pred_columns]))
            ax2.plot([min_val, max_val], [min_val, max_val], 'k--', alpha=0.5, label='理想線')
            
            ax2.set_title('預測vs實際價格散點圖')
            ax2.set_xlabel('實際價格 (CNY/MWh)')
            ax2.set_ylabel('預測價格 (CNY/MWh)')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            
            # 子圖3: 誤差分布
            ax3 = axes[1, 0]
            errors = {}
            for col in pred_columns:
                model_name = col.replace('_prediction', '').upper()
                errors[model_name] = results_df['actual'] - results_df[col]
            
            error_df = pd.DataFrame(errors)
            error_df.boxplot(ax=ax3)
            ax3.set_title('預測誤差分布')
            ax3.set_ylabel('誤差 (CNY/MWh)')
            ax3.grid(True, alpha=0.3)
            
            # 子圖4: 性能指標
            ax4 = axes[1, 1]
            from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
            
            metrics = {'MAE': [], 'RMSE': [], 'R²': []}
            model_names = []
            
            for col in pred_columns:
                model_name = col.replace('_prediction', '').upper()
                model_names.append(model_name)
                
                mae = mean_absolute_error(results_df['actual'], results_df[col])
                rmse = np.sqrt(mean_squared_error(results_df['actual'], results_df[col]))
                r2 = r2_score(results_df['actual'], results_df[col])
                
                metrics['MAE'].append(mae)
                metrics['RMSE'].append(rmse)
                metrics['R²'].append(r2)
            
            x = np.arange(len(model_names))
            width = 0.25
            
            ax4.bar(x - width, metrics['MAE'], width, label='MAE', alpha=0.8)
            ax4.bar(x, metrics['RMSE'], width, label='RMSE', alpha=0.8)
            ax4_twin = ax4.twinx()
            ax4_twin.bar(x + width, metrics['R²'], width, label='R²', alpha=0.8, color='green')
            
            ax4.set_title('模型性能指標對比')
            ax4.set_xlabel('模型')
            ax4.set_ylabel('MAE / RMSE')
            ax4_twin.set_ylabel('R²')
            ax4.set_xticks(x)
            ax4.set_xticklabels(model_names, rotation=45)
            ax4.legend(loc='upper left')
            ax4_twin.legend(loc='upper right')
            
            plt.tight_layout()
            
            if save_path is None:
                save_path = self.output_dir / 'prediction_comparison.png'
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            logging.info(f"預測對比圖已保存到: {save_path}")
            
        except Exception as e:
            logging.error(f"生成預測對比圖失敗: {e}")

class BiddingVisualizer:
    """投標策略可視化器"""
    
    def __init__(self, output_dir='output/bidding'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def plot_bidding_curve(self, strategy_df, save_path=None):
        """繪製投標曲線"""
        try:
            plt.figure(figsize=(12, 8))
            
            # 繪製投標曲線
            plt.plot(strategy_df['DA_Price'], strategy_df['P_DA'], 
                    linewidth=3, marker='o', markersize=4, label='投標曲線')
            
            # 添加門檻線
            threshold_price = 380  # 發電邊際成本
            plt.axvline(x=threshold_price, color='red', linestyle='--', 
                       alpha=0.7, label=f'發電邊際成本: {threshold_price} CNY/MWh')
            
            plt.title('電力市場投標策略曲線', fontsize=16)
            plt.xlabel('日前市場價格 (CNY/MWh)', fontsize=12)
            plt.ylabel('投標電量 (MW)', fontsize=12)
            plt.grid(True, alpha=0.3)
            plt.legend()
            
            # 添加註釋
            plt.text(0.02, 0.98, '策略說明:\n• 價格低於成本時不參與市場\n• 價格高於成本時滿發運行',
                    transform=plt.gca().transAxes, verticalalignment='top',
                    bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
            
            plt.tight_layout()
            
            if save_path is None:
                save_path = self.output_dir / 'bidding_curve.png'
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            logging.info(f"投標曲線圖已保存到: {save_path}")
            
        except Exception as e:
            logging.error(f"生成投標曲線圖失敗: {e}")
