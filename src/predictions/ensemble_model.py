#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
智能集成預測模型
支持基于性能的模型筛选和多种集成策略
"""

import numpy as np
import pandas as pd
import logging
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

class EnsembleModel:
    """智能集成模型，支持性能筛选和多种集成策略"""

    def __init__(self, config=None):
        """初始化集成模型

        Args:
            config: 集成配置参数
        """
        # 默认配置
        self.config = {
            'selection_method': 'top_k',  # 'top_k', 'threshold', 'all'
            'top_k': 3,  # 选择前k个最好的模型
            'mae_threshold': 30.0,  # MAE阈值，超过此值的模型不参与集成
            'rmse_threshold': 60.0,  # RMSE阈值
            'r2_threshold': 0.0,  # R²阈值，低于此值的模型不参与集成
            'ensemble_method': 'weighted_average',  # 'simple_average', 'weighted_average', 'voting'
            'exclude_models': ['historical'],  # 默认排除的模型
            'min_models': 2,  # 最少需要的模型数量
        }

        # 使用传入的配置覆盖默认配置
        if config:
            self.config.update(config)

        self.weights = {}
        self.predictions = {}
        self.model_names = []
        self.selected_models = []
        self.model_performance = {}
        self.final_predictions = None
    
    def train(self, predictions, y_true):
        """
        智能训练集成模型，包含模型筛选和权重计算

        Args:
            predictions (dict): 各模型的预测结果字典，如 {'rf': [1, 2, 3], 'xgb': [1.1, 2.1, 3.1]}
            y_true (pd.Series or np.ndarray): 对应的真实值
        """
        self.predictions = predictions
        self.model_names = list(predictions.keys())

        # 确保 y_true 是 numpy 数组
        if isinstance(y_true, pd.Series):
            y_true = y_true.values

        logging.info(f"开始智能集成模型训练，候选模型: {self.model_names}")

        # 步骤1: 计算所有模型的性能指标
        self._evaluate_all_models(y_true)

        # 步骤2: 根据配置筛选模型
        self._select_models()

        # 步骤3: 计算集成权重
        self._calculate_weights(y_true)

        # 步骤4: 生成最终预测
        self._generate_ensemble_predictions()

        logging.info(f"✅ 智能集成完成，选择了 {len(self.selected_models)} 个模型: {self.selected_models}")

    def _evaluate_all_models(self, y_true):
        """评估所有模型的性能"""
        self.model_performance = {}

        for model_name in self.model_names:
            pred = self.predictions[model_name]

            # 确保预测是数组
            if isinstance(pred, pd.Series):
                pred = pred.values
            elif isinstance(pred, list):
                pred = np.array(pred)

            # 计算性能指标
            mae = mean_absolute_error(y_true, pred)
            mse = mean_squared_error(y_true, pred)
            rmse = np.sqrt(mse)
            r2 = r2_score(y_true, pred)

            # 计算MAPE (处理零值)
            mape = np.mean(np.abs((y_true - pred) / np.where(y_true != 0, y_true, 1))) * 100

            # 计算方向准确率
            if len(y_true) > 1:
                actual_diff = np.diff(y_true)
                pred_diff = np.diff(pred)
                direction_accuracy = np.mean((actual_diff * pred_diff) > 0) * 100
            else:
                direction_accuracy = 0.0

            self.model_performance[model_name] = {
                'MAE': mae,
                'RMSE': rmse,
                'R2': r2,
                'MAPE': mape,
                'Direction_Accuracy': direction_accuracy
            }

            logging.info(f"模型 {model_name}: MAE={mae:.2f}, RMSE={rmse:.2f}, R²={r2:.4f}")

    def _select_models(self):
        """根据配置筛选模型"""
        # 排除指定的模型
        candidate_models = [name for name in self.model_names
                          if name not in self.config['exclude_models']]

        if self.config['selection_method'] == 'all':
            # 使用所有候选模型
            self.selected_models = candidate_models

        elif self.config['selection_method'] == 'threshold':
            # 基于阈值筛选
            self.selected_models = []
            for model_name in candidate_models:
                perf = self.model_performance[model_name]
                if (perf['MAE'] <= self.config['mae_threshold'] and
                    perf['RMSE'] <= self.config['rmse_threshold'] and
                    perf['R2'] >= self.config['r2_threshold']):
                    self.selected_models.append(model_name)

            logging.info(f"阈值筛选: MAE≤{self.config['mae_threshold']}, "
                        f"RMSE≤{self.config['rmse_threshold']}, "
                        f"R²≥{self.config['r2_threshold']}")

        elif self.config['selection_method'] == 'top_k':
            # 选择前k个最好的模型（按MAE排序）
            sorted_models = sorted(candidate_models,
                                 key=lambda x: self.model_performance[x]['MAE'])
            self.selected_models = sorted_models[:self.config['top_k']]

            logging.info(f"Top-K筛选: 选择前{self.config['top_k']}个最佳模型")

        # 确保至少有最少数量的模型
        if len(self.selected_models) < self.config['min_models']:
            logging.warning(f"筛选后模型数量({len(self.selected_models)})少于最小要求"
                          f"({self.config['min_models']})，使用所有候选模型")
            self.selected_models = candidate_models

        logging.info(f"最终选择的模型: {self.selected_models}")

        # 显示被排除的模型
        excluded = set(self.model_names) - set(self.selected_models)
        if excluded:
            logging.info(f"被排除的模型: {list(excluded)}")
            for model_name in excluded:
                perf = self.model_performance[model_name]
                logging.info(f"  {model_name}: MAE={perf['MAE']:.2f}, "
                           f"RMSE={perf['RMSE']:.2f}, R²={perf['R2']:.4f}")

    def _calculate_weights(self, y_true):
        """计算集成权重"""
        if self.config['ensemble_method'] == 'simple_average':
            # 简单平均
            self.weights = {name: 1.0/len(self.selected_models)
                          for name in self.selected_models}

        elif self.config['ensemble_method'] == 'weighted_average':
            # 基于性能的加权平均（MAE越小权重越大）
            mae_scores = [self.model_performance[name]['MAE'] for name in self.selected_models]

            # 计算倒数权重（MAE越小权重越大）
            inverse_mae = [1.0 / (mae + 1e-8) for mae in mae_scores]
            total_weight = sum(inverse_mae)

            self.weights = {name: weight/total_weight
                          for name, weight in zip(self.selected_models, inverse_mae)}

        elif self.config['ensemble_method'] == 'voting':
            # 投票机制
            self._calculate_voting_weights(y_true)

        # 显示权重信息
        logging.info("集成权重分配:")
        for name in self.selected_models:
            logging.info(f"  {name}: {self.weights[name]:.4f}")

    def _calculate_voting_weights(self, y_true):
        """计算投票权重"""
        votes = {name: 0 for name in self.selected_models}
        num_points = len(y_true)

        # 遍历每个预测点
        for i in range(num_points):
            best_model = None
            min_error = float('inf')

            # 找出这一点上哪个模型的预测最准确
            for name in self.selected_models:
                pred = self.predictions[name]
                if isinstance(pred, pd.Series):
                    pred = pred.values
                elif isinstance(pred, list):
                    pred = np.array(pred)

                error = abs(pred[i] - y_true[i])
                if error < min_error:
                    min_error = error
                    best_model = name

            # 给最佳模型投票
            if best_model:
                votes[best_model] += 1

        # 计算权重（得票率）
        total_votes = sum(votes.values())
        if total_votes > 0:
            self.weights = {name: votes[name] / total_votes for name in self.selected_models}
        else:
            # 如果没有投票，使用平均权重
            self.weights = {name: 1.0/len(self.selected_models) for name in self.selected_models}

    def _generate_ensemble_predictions(self):
        """生成集成预测"""
        if not self.selected_models:
            logging.error("没有选择的模型，无法生成集成预测")
            return None

        # 获取第一个模型的预测长度
        first_model = self.selected_models[0]
        pred_length = len(self.predictions[first_model])

        # 初始化集成预测
        self.final_predictions = np.zeros(pred_length)

        # 加权平均
        for model_name in self.selected_models:
            pred = self.predictions[model_name]
            if isinstance(pred, pd.Series):
                pred = pred.values
            elif isinstance(pred, list):
                pred = np.array(pred)

            weight = self.weights[model_name]
            self.final_predictions += weight * pred

        logging.info(f"集成预测生成完成，预测长度: {len(self.final_predictions)}")

        return self.final_predictions

    def predict(self, new_predictions=None):
        """
        进行集成预测

        Args:
            new_predictions (dict, optional): 新的预测结果，如果为None则使用训练时的预测

        Returns:
            np.array: 集成预测结果
        """
        if new_predictions is not None:
            # 使用新的预测数据
            if not self.selected_models or not self.weights:
                logging.error("模型未训练，无法进行预测")
                return None

            # 获取预测长度
            first_model = self.selected_models[0]
            if first_model not in new_predictions:
                logging.error(f"新预测数据中缺少模型: {first_model}")
                return None

            pred_length = len(new_predictions[first_model])
            ensemble_pred = np.zeros(pred_length)

            # 加权平均
            for model_name in self.selected_models:
                if model_name not in new_predictions:
                    logging.warning(f"新预测数据中缺少模型: {model_name}，跳过")
                    continue

                pred = new_predictions[model_name]
                if isinstance(pred, pd.Series):
                    pred = pred.values
                elif isinstance(pred, list):
                    pred = np.array(pred)

                weight = self.weights[model_name]
                ensemble_pred += weight * pred

            return ensemble_pred
        else:
            # 使用训练时的预测
            return self.final_predictions

    def get_model_performance(self):
        """获取所有模型的性能指标"""
        return self.model_performance

    def get_selected_models(self):
        """获取被选择的模型列表"""
        return self.selected_models

    def get_weights(self):
        """获取模型权重"""
        return self.weights

    def get_ensemble_summary(self):
        """获取集成模型摘要信息"""
        summary = {
            'config': self.config,
            'total_models': len(self.model_names),
            'selected_models': self.selected_models,
            'excluded_models': list(set(self.model_names) - set(self.selected_models)),
            'weights': self.weights,
            'performance': {name: self.model_performance[name]
                          for name in self.selected_models}
        }
        return summary

    def print_summary(self):
        """打印集成模型摘要"""
        print("\n" + "="*60)
        print("智能集成模型摘要")
        print("="*60)
        print(f"筛选方法: {self.config['selection_method']}")
        print(f"集成方法: {self.config['ensemble_method']}")
        print(f"候选模型数: {len(self.model_names)}")
        print(f"选择模型数: {len(self.selected_models)}")

        print(f"\n选择的模型及权重:")
        for name in self.selected_models:
            perf = self.model_performance[name]
            weight = self.weights[name]
            print(f"  {name}: 权重={weight:.4f}, MAE={perf['MAE']:.2f}, "
                  f"RMSE={perf['RMSE']:.2f}, R²={perf['R2']:.4f}")

        excluded = set(self.model_names) - set(self.selected_models)
        if excluded:
            print(f"\n被排除的模型:")
            for name in excluded:
                perf = self.model_performance[name]
                print(f"  {name}: MAE={perf['MAE']:.2f}, "
                      f"RMSE={perf['RMSE']:.2f}, R²={perf['R2']:.4f}")

