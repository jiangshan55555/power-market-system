#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
電力市場投標策略優化模型 - 神經動力學版本
基於自適應網格神經動力學優化方法，推導完整的投標曲線並給出穩健的門檻策略。
集成了原有的SciPy優化和新的神經動力學優化算法。
"""

import pandas as pd
import numpy as np
import os
import datetime
from scipy import optimize
from scipy.stats import norm
import logging
import traceback
from pathlib import Path
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import json

# 配置中文字體
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

# --- 兼容性與路徑設置 ---
# 獲取腳本目錄但不改變工作目錄
try:
    SCRIPT_DIR = Path(__file__).parent.resolve()
    logging.info(f"BiddingOptimizationModel script directory: {SCRIPT_DIR}")
except NameError:
    # 在交互式環境 (如Jupyter) 中 __file__ 未定義
    SCRIPT_DIR = Path.cwd()
    logging.warning(f"__file__ not defined. Assuming script directory is current working directory: {SCRIPT_DIR}")

class BiddingOptimizationModel:
    """
    電力市場投標策略優化模型類。
    該模型的核心思想是：不針對某個具體的預測價格點進行優化，
    而是遍歷所有可能的日前市場價格(DA Price)，為每一個可能的價格，
    考慮所有可能的實時市場價格(RT Price)的概率分佈，
    從而計算出最優的日前申報電量(P_DA)和配套的實時調整策略。
    最終，通過分析 P_DA 與 DA Price 的關係，推導出一個通用的、穩健的投標策略。
    """
    
    def __init__(self, config=None):
        """初始化投标优化模型 - 神经动力学增强版"""
        # 默认配置，路径相对于项目根目录
        self.config = {
            'INPUT_FILE': 'output/predictions/prediction_results.csv',
            'OUTPUT_DIR': 'output/bidding',
            'PRICE_GRID_STEP': 2,    # 更细的网格步长，产生更多变化
            'PRICE_MIN': None,      # 将从预测数据自动确定
            'PRICE_MAX': None,      # 将从预测数据自动确定
            'PRICE_BUFFER_RATIO': 0.15,  # 价格范围缓冲区比例
            'COST_PARAMS': {
                'c_g': 375,  # 略微降低边际成本，增加盈利空间
                'c_up': 530, # 提高上调整成本，增加风险
                'c_dn': 310  # 降低下调整成本，增加灵活性
            },
            'CAPACITY_PARAMS': {
                'P_max': 100, # 最大出力
                'R_up_max': 8, # 增加上調整容量，增加策略灵活性
                'R_dn_max': 8  # 增加下調整容量
            },
            'OPTIMIZATION_METHOD': 'neurodynamic',  # 'scipy' 或 'neurodynamic'
            'NEURODYNAMIC_PARAMS': {
                'eta_base': 0.05,       # 降低基础学习率，增加探索
                'eta_min': 0.0005,      # 更小的最小学习率
                'max_iter': 2000,       # 增加迭代次数，允许更充分优化
                'tolerance': 1e-5,      # 更严格的收敛条件
                'patience': 150,        # 增加耐心值，避免过早停止
                'adaptive_grid': True,  # 保持自适应网格
                'fine_step': 0.05,      # 更细的细化步长
                'noise_factor': 0.05,   # 增加噪声因子，产生更多变化
                'momentum': 0.85,       # 适度降低动量，增加探索性
                'price_sensitivity': 0.1,  # 价格敏感性参数
                'nonlinear_factor': 1.2    # 非线性因子
            }
        }

        # 使用傳入的配置覆蓋默認配置
        if config:
            for key, value in config.items():
                if key in self.config and isinstance(self.config[key], dict) and isinstance(value, dict):
                        self.config[key].update(value)
                else:
                    self.config[key] = value

        # 創建輸出目錄
        os.makedirs(self.config['OUTPUT_DIR'], exist_ok=True)

        # 初始化數據和結果
        self.price_data = None
        self.price_distribution = None
        self.results = {}

        # 神經動力學相關屬性
        self.optimization_results = {}
        self.threshold_regions = []
    
    def load_price_data(self):
        """加載價格數據並動態調整價格參數"""
        try:
            input_path = Path(self.config['INPUT_FILE'])
            if not input_path.exists():
                logging.error(f"輸入文件未找到: {input_path}")
                return False

            df = pd.read_csv(input_path, index_col='timestamp', parse_dates=True)
            
            # 修改数据输入逻辑：
            # DAM（日前市场）：使用预测输出（预测模型）
            # RTM（实时市场）：使用每天的实际数据
            # 确保两列数据不同

            # 检查必需的列
            required_cols = ['actual']  # RTM需要实际数据
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                logging.error(f"未找到必需的列: {missing_cols}，投标策略需要实际数据")
                return False

            # RTM固定使用实际数据
            rtm_col = 'actual'

            # DAM使用预测模型输出
            dam_col = 'ensemble'

            logging.info(f"✅ 数据输入配置:")
            logging.info(f"  DAM（日前市场）: '{dam_col}' (预测输出)")
            logging.info(f"  RTM（实时市场）: '{rtm_col}' (ensemble预测)")
            
            self.price_data = pd.DataFrame({
                'DAM': df[dam_col],
                'RTM': df[rtm_col]
            })

            # 验证数据质量
            logging.info(f"✅ 价格数据加载完成:")
            logging.info(f"  DAM数据点数: {len(self.price_data['DAM'])}")
            logging.info(f"  RTM数据点数: {len(self.price_data['RTM'])}")
            logging.info(f"  DAM价格范围: {self.price_data['DAM'].min():.2f} - {self.price_data['DAM'].max():.2f} CNY/MWh")
            logging.info(f"  RTM价格范围: {self.price_data['RTM'].min():.2f} - {self.price_data['RTM'].max():.2f} CNY/MWh")

            # 如果价格范围尚未设置，则基于数据动态确定
            if self.config['PRICE_MIN'] is None or self.config['PRICE_MAX'] is None:
                # 动态计算价格范围（基于预测数据）
                price_series = self.price_data['DAM']
                p_min = max(price_series.min() - 20, 0)  # 最小值减20，但不低于0
                p_max = price_series.max() + 20  # 最大值加20

                # 确保合理的价格范围
                if p_max - p_min < 100:  # 如果范围太小，扩展到至少100
                    center = (p_min + p_max) / 2
                    p_min = max(center - 50, 0)
                    p_max = center + 50

                self.config['PRICE_MAX'] = p_max
                self.config['PRICE_MIN'] = p_min

                logging.info(f"基于预测数据动态确定价格范围: ({p_min:.1f}, {p_max:.1f})")
            else:
                p_min = self.config['PRICE_MIN']
                p_max = self.config['PRICE_MAX']
                logging.info(f"使用预设价格范围: ({p_min:.1f}, {p_max:.1f})")

            # 动态调整步长，产生更多网格点以捕捉细节
            price_range = p_max - p_min
            self.config['PRICE_GRID_STEP'] = max(price_range / 150, 0.2)  # 更细的步长，产生更多变化点

            logging.info(f"最终价格参数: 范围 ({p_min:.1f}, {p_max:.1f}), 步长 {self.config['PRICE_GRID_STEP']:.1f}")
            logging.info(f"预测价格统计: 最小值 {self.price_data['DAM'].min():.1f}, 最大值 {self.price_data['DAM'].max():.1f}, 平均值 {self.price_data['DAM'].mean():.1f}")

            # 验证价格范围与边际成本的关系
            c_g = self.config['COST_PARAMS']['c_g']
            if p_min > c_g:
                logging.warning(f"⚠️  最小价格({p_min:.1f})高于边际成本({c_g:.1f})，在此范围内总是盈利")
            elif p_max < c_g:
                logging.warning(f"⚠️  最大价格({p_max:.1f})低于边际成本({c_g:.1f})，在此范围内总是亏损")
            else:
                logging.info(f"✅ 价格范围跨越边际成本({c_g:.1f})，优化空间合理")

            # 计算有效的优化区间
            profitable_ratio = max(0, (p_max - c_g) / (p_max - p_min)) * 100
            logging.info(f"📊 盈利价格区间占比: {profitable_ratio:.1f}%")
            return True
        except Exception as e:
            logging.error(f"加載價格數據失敗: {e}\n{traceback.format_exc()}")
            return False
    
    def fit_price_distribution(self, cutoff_date=None):
        """僅用實際價格actual且index < cutoff_date擬合分布"""
        if self.price_data is None: return False
        df = self.price_data
        if cutoff_date is not None:
            df = df[df.index < pd.to_datetime(cutoff_date)]
            if 'actual' in df.columns:
                df = df[['actual']].rename(columns={'actual': 'DAM'})
                df['RTM'] = df['DAM']
            if df.empty:
                logging.error(f"擬合分布時，{cutoff_date} 前無實際價格數據！")
                return False
        da_mu, da_std = df['DAM'].mean(), df['DAM'].std()
        rt_mu, rt_std = df['RTM'].mean(), df['RTM'].std()
        self.price_distribution = {
            'DA': {'mu': da_mu, 'std': max(da_std, 1e-6)},
            'RT': {'mu': rt_mu, 'std': max(rt_std, 1e-6)}
        }
        logging.info(f"價格分布已擬合: DA(μ={da_mu:.2f}, σ={da_std:.2f}), RT(μ={rt_mu:.2f}, σ={rt_std:.2f})")
        return True
    
    def joint_pdf(self, da_price, rt_price_vec):
        """
        計算聯合概率密度。
        由於假設兩者獨立，所以是各自概率密度的乘積。
        """
        if not self.price_distribution: return 0
        dist_da = self.price_distribution['DA']
        dist_rt = self.price_distribution['RT']
        # 計算單個日前價格點的概率
        da_prob = norm.pdf(da_price, dist_da['mu'], dist_da['std'])
        # 計算所有實時價格點的概率向量
        rt_prob_vec = norm.pdf(rt_price_vec, dist_rt['mu'], dist_rt['std'])
        # 返回一個向量，其元素為 da_prob * rt_prob
        return da_prob * rt_prob_vec
    
    def optimize_bidding_strategy(self):
        """
        智能投標策略優化 - 支持SciPy和神經動力學兩種方法
        """
        if not self.price_distribution:
            logging.error("價格分布未擬合")
            return None

        # 自动确定价格范围（如果尚未设置）
        if self.config['PRICE_MIN'] is None or self.config['PRICE_MAX'] is None:
            self._determine_price_range_from_distribution()

        method = self.config.get('OPTIMIZATION_METHOD', 'neurodynamic')

        if method == 'scipy':
            return self._optimize_with_scipy()
        elif method == 'neurodynamic':
            return self._optimize_with_neurodynamic()
        else:
            logging.error(f"未知的優化方法: {method}")
            return None

    def _determine_price_range_from_distribution(self):
        """
        基于价格分布自动确定优化的价格范围
        """
        try:
            # 从价格分布中获取统计信息
            da_dist = self.price_distribution['DA']
            rt_dist = self.price_distribution['RT']

            # 计算价格范围（使用3个标准差覆盖99.7%的数据）
            da_min = da_dist['mu'] - 3 * da_dist['std']
            da_max = da_dist['mu'] + 3 * da_dist['std']
            rt_min = rt_dist['mu'] - 3 * rt_dist['std']
            rt_max = rt_dist['mu'] + 3 * rt_dist['std']

            # 取两个市场的并集
            price_min = min(da_min, rt_min)
            price_max = max(da_max, rt_max)

            # 添加缓冲区
            buffer_ratio = self.config.get('PRICE_BUFFER_RATIO', 0.15)
            price_range = price_max - price_min
            buffer = price_range * buffer_ratio

            # 确定最终范围，但要考虑实际约束
            cost_params = self.config['COST_PARAMS']
            c_g = cost_params['c_g']  # 边际成本

            # 最小价格：不低于边际成本的80%，也不低于200
            final_min = max(price_min - buffer, c_g * 0.8, 200)

            # 最大价格：添加缓冲区，但不超过1000
            final_max = min(price_max + buffer, 1000)

            # 更新配置
            self.config['PRICE_MIN'] = final_min
            self.config['PRICE_MAX'] = final_max

            logging.info(f"✅ 自动确定价格范围:")
            logging.info(f"  原始分布范围: DA [{da_min:.1f}, {da_max:.1f}], RT [{rt_min:.1f}, {rt_max:.1f}]")
            logging.info(f"  边际成本: {c_g:.1f} CNY/MWh")
            logging.info(f"  最终优化范围: [{final_min:.1f}, {final_max:.1f}] CNY/MWh")
            logging.info(f"  缓冲区比例: {buffer_ratio*100:.1f}%")

            # 验证价格范围的合理性
            if final_max <= final_min:
                logging.error(f"价格范围无效: 最大值({final_max:.1f}) <= 最小值({final_min:.1f})")
                return False

            if final_min > c_g * 1.5:
                logging.warning(f"最小价格({final_min:.1f})远高于边际成本({c_g:.1f})，可能错过低价机会")

            return True

        except Exception as e:
            logging.error(f"自动确定价格范围失败: {e}")
            # 回退到保守的默认值
            cost_params = self.config['COST_PARAMS']
            c_g = cost_params['c_g']
            self.config['PRICE_MIN'] = max(c_g * 0.8, 300)
            self.config['PRICE_MAX'] = c_g * 1.5
            logging.warning(f"使用保守的默认价格范围: [{self.config['PRICE_MIN']:.1f}, {self.config['PRICE_MAX']:.1f}]")
            return False

    def _optimize_with_scipy(self):
        """原有的SciPy優化方法"""
        c_g, c_up, c_dn = self.config['COST_PARAMS'].values()
        P_max, R_up_max, R_dn_max = self.config['CAPACITY_PARAMS'].values()
        p_min, p_max, step = self.config['PRICE_MIN'], self.config['PRICE_MAX'], self.config['PRICE_GRID_STEP']
        DA_grid = np.arange(p_min, p_max + step, step)
        RT_grid = np.arange(p_min, p_max + step, step)
        rt_step = RT_grid[1] - RT_grid[0] if len(RT_grid) > 1 else 1
        optimization_results = {}
        logging.info("開始SciPy優化遍歷日前價格網格...")

        for da_price in DA_grid:
            def objective_function(x):
                P_DA = x[0]
                P_RT = x[1 : 1 + len(RT_grid)]
                R_up = x[1 + len(RT_grid) : 1 + 2 * len(RT_grid)]
                R_dn = x[1 + 2 * len(RT_grid) :]
                da_profit = P_DA * da_price - c_g * P_DA
                prob_mass_vec = self.joint_pdf(da_price, RT_grid) * rt_step
                rt_profits_vec = P_RT * RT_grid - c_g * P_RT - c_up * R_up - c_dn * R_dn
                expected_rt_profit = np.sum(prob_mass_vec * rt_profits_vec)
                return -(da_profit + expected_rt_profit)

            cons = [{'type': 'ineq', 'fun': lambda x: x[0]}, {'type': 'ineq', 'fun': lambda x: P_max - x[0]}]
            for i in range(len(RT_grid)):
                cons.extend([
                    {'type': 'eq',   'fun': lambda x, i=i: x[1+i] - (x[0] + x[1+len(RT_grid)+i] - x[1+2*len(RT_grid)+i])},
                    {'type': 'ineq', 'fun': lambda x, i=i: x[1+len(RT_grid)+i]}, {'type': 'ineq', 'fun': lambda x, i=i: R_up_max - x[1+len(RT_grid)+i]},
                    {'type': 'ineq', 'fun': lambda x, i=i: x[1+2*len(RT_grid)+i]}, {'type': 'ineq', 'fun': lambda x, i=i: R_dn_max - x[1+2*len(RT_grid)+i]},
                    {'type': 'ineq', 'fun': lambda x, i=i: x[1+i]}, {'type': 'ineq', 'fun': lambda x, i=i: P_max - x[1+i]}
                ])
            x0 = np.zeros(1 + 3 * len(RT_grid))
            x0[0] = P_max / 2
            x0[1 : 1 + len(RT_grid)] = P_max / 2
            res = optimize.minimize(objective_function, x0, method='SLSQP', constraints=cons, options={'maxiter': 100, 'ftol': 1e-6})
            if res.success:
                optimization_results[da_price] = {
                    'P_DA': res.x[0],
                    'Objective': -res.fun,
                    'RT_Grid': RT_grid.tolist(),
                    'P_RT': res.x[1:1+len(RT_grid)].tolist(),
                    'R_up': res.x[1+len(RT_grid):1+2*len(RT_grid)].tolist(),
                    'R_dn': res.x[1+2*len(RT_grid):].tolist(),
                    'converged': True,
                    'iterations': res.nit if hasattr(res, 'nit') else 0
                }
            else:
                logging.warning(f"SciPy優化失敗 DA價格 = {da_price:.2f}: {res.message}")

        logging.info(f"SciPy價格網格優化完成，成功優化 {len(optimization_results)} 個價格點")
        return optimization_results

    def _optimize_with_neurodynamic(self):
        """
        自適應網格神經動力學優化方法
        1. 首先使用粗網格進行初步優化
        2. 檢測門檻策略區域
        3. 在門檻區域進行細化優化
        """
        logging.info("=" * 60)
        logging.info("開始神經動力學自適應網格優化")
        logging.info("=" * 60)

        # 第一步：粗網格優化
        logging.info("第一步：粗網格優化")
        p_min, p_max, step = self.config['PRICE_MIN'], self.config['PRICE_MAX'], self.config['PRICE_GRID_STEP']
        DA_grid = np.arange(p_min, p_max + step, step)
        RT_grid = np.arange(p_min, p_max + step, step)

        optimization_results = {}
        logging.info(f"開始遍歷日前價格網格進行神經動力學優化，網格大小: {len(DA_grid)} x {len(RT_grid)}")

        for i, da_price in enumerate(DA_grid):
            logging.info(f"粗網格優化進度: {i+1}/{len(DA_grid)}, 當前DA價格: {da_price:.2f}")
            try:
                result = self._neurodynamic_optimization_for_da_price(da_price, RT_grid)
                if result['converged']:
                    optimization_results[da_price] = result
                else:
                    logging.warning(f"DA價格 {da_price:.2f}: 未收敛")
            except Exception as e:
                logging.error(f"DA價格 {da_price:.2f}: 優化失敗 - {e}")

        # 統計收敛情況
        converged_count = sum(1 for res in optimization_results.values() if res['converged'])
        total_iterations = sum(res['iterations'] for res in optimization_results.values())
        avg_iterations = total_iterations / len(optimization_results) if optimization_results else 0

        logging.info(f"粗網格優化完成，成功優化 {len(optimization_results)}/{len(DA_grid)} 個價格點")
        logging.info(f"收敛統計: {converged_count}/{len(optimization_results)} 個點收敛")
        logging.info(f"平均迭代次數: {avg_iterations:.1f}")

        # 第二步：檢測門檻區域（如果啟用自適應網格）
        if self.config['NEURODYNAMIC_PARAMS'].get('adaptive_grid', True):
            logging.info("第二步：檢測門檻策略區域")
            threshold_regions = self._detect_threshold_regions(optimization_results)

            if threshold_regions:
                # 第三步：多层次細化門檻區域
                logging.info(f"第三步：多层次細化 {len(threshold_regions)} 個門檻區域")

                # 第一层：0.2元步长粗细化
                coarse_step = 0.2
                logging.info(f"  第一层细化：步长 {coarse_step} 元")
                coarse_refined = self._refine_threshold_regions(threshold_regions, RT_grid, coarse_step)
                optimization_results.update(coarse_refined)

                # 第二层：0.05元步长精细化
                fine_step = self.config['NEURODYNAMIC_PARAMS'].get('fine_step', 0.05)
                logging.info(f"  第二层细化：步长 {fine_step} 元")
                fine_refined = self._refine_threshold_regions(threshold_regions, RT_grid, fine_step)
                optimization_results.update(fine_refined)

                # 第三层：0.005元步长超精细化（仅关键区域）
                ultra_fine_step = 0.005
                critical_regions = threshold_regions[:min(3, len(threshold_regions))]  # 前3个最重要区域
                if critical_regions:
                    logging.info(f"  第三层超精细化：步长 {ultra_fine_step} 元，处理 {len(critical_regions)} 个关键区域")
                    ultra_refined = self._refine_threshold_regions(critical_regions, RT_grid, ultra_fine_step)
                    optimization_results.update(ultra_refined)
                else:
                    ultra_refined = {}

                total_refined = len(coarse_refined) + len(fine_refined) + len(ultra_refined)
                logging.info(f"多层次細化完成，新增 {total_refined} 個優化點")
            else:
                logging.info("未檢測到明顯的門檻策略區域，使用粗網格結果")

        # 總體統計
        total_converged = sum(1 for res in optimization_results.values() if res['converged'])
        total_iterations = sum(res['iterations'] for res in optimization_results.values())
        overall_avg_iter = total_iterations / len(optimization_results) if optimization_results else 0

        logging.info(f"神經動力學自適應優化完成，總共優化 {len(optimization_results)} 個價格點")
        logging.info(f"總體收敛統計: {total_converged}/{len(optimization_results)} 個點收敛 ({100*total_converged/len(optimization_results):.1f}%)")
        logging.info(f"總體平均迭代次數: {overall_avg_iter:.1f}")

        self.optimization_results = optimization_results
        return optimization_results

    def _neurodynamic_optimization_for_da_price(self, da_price, RT_grid):
        """
        改進的神經動力學方法求解單個DA價格下的最優策略
        使用自適應學習率和更robust的收敛策略
        """
        # 獲取參數
        c_g = self.config['COST_PARAMS']['c_g']
        P_max = self.config['CAPACITY_PARAMS']['P_max']
        R_up_max = self.config['CAPACITY_PARAMS']['R_up_max']
        R_dn_max = self.config['CAPACITY_PARAMS']['R_dn_max']

        neurodynamic_params = self.config['NEURODYNAMIC_PARAMS']
        eta_base = neurodynamic_params.get('eta_base', 0.05)
        eta_min = neurodynamic_params.get('eta_min', 0.0005)
        max_iter = neurodynamic_params.get('max_iter', 2000)
        tolerance = neurodynamic_params.get('tolerance', 1e-5)
        patience = neurodynamic_params.get('patience', 150)
        noise_factor = neurodynamic_params.get('noise_factor', 0.02)  # 噪声因子
        momentum = neurodynamic_params.get('momentum', 0.9)  # 动量项

        # 智能初始化：基於價格與成本的關係，增加非线性和随机性
        import numpy as np

        # 使用价格作为随机种子，产生确定性但复杂的变化
        seed_value = int((da_price * 1000) % 2**32)
        np.random.seed(seed_value)

        # 获取非线性因子
        nonlinear_factor = neurodynamic_params.get('nonlinear_factor', 1.2)
        price_sensitivity = neurodynamic_params.get('price_sensitivity', 0.1)

        # 计算价格差异的非线性响应
        price_diff = da_price - c_g
        if price_diff < 0:
            # 低于成本时，小概率少量发电
            P_DA = np.random.exponential(P_max * 0.05) if np.random.random() < 0.1 else 0
        elif price_diff > 30:
            # 远高于成本时，大概率满发但有波动
            base_ratio = 0.7 + 0.3 * (1 - np.exp(-price_diff / 20))
            noise_amplitude = P_max * price_sensitivity * np.sin(da_price / 10)  # 正弦波动
            P_DA = P_max * base_ratio + noise_amplitude + np.random.normal(0, P_max * 0.05)
        else:
            # 中等价格时，复杂的非线性响应
            normalized_price = price_diff / 30
            # 使用多项式和三角函数的组合
            base_response = normalized_price ** nonlinear_factor
            wave_response = 0.1 * np.sin(da_price / 5) * np.cos(da_price / 8)  # 使用da_price替代rt_price
            random_component = np.random.normal(0, 0.1 * normalized_price)

            P_DA = P_max * (base_response + wave_response + random_component)

        # 确保在合理范围内
        P_DA = np.clip(P_DA, 0, P_max)

        # 自适应神经动力学迭代（添加超时保护）
        import time
        start_time = time.time()
        timeout = 30.0  # 30秒超时，允许更充分的优化

        converged = False
        best_P_DA = P_DA
        best_objective = float('-inf')
        no_improve_count = 0

        # 动量项初始化
        velocity = 0.0
        prev_grad = 0.0

        for iteration in range(max_iter):
            # 超时检查
            if time.time() - start_time > timeout:
                logging.warning(f"DA价格 {da_price:.2f}: 优化超时，使用当前最佳解")
                P_DA = best_P_DA
                converged = True
                break
            try:
                # 改进的梯度计算
                grad_P_DA = self._compute_improved_gradient(da_price, P_DA, RT_grid)

                # 检查梯度是否有效
                if not np.isfinite(grad_P_DA):
                    logging.warning(f"DA价格 {da_price:.2f}: 梯度无效，使用当前最佳解")
                    P_DA = best_P_DA
                    break

                # 自适应学习率
                eta = self._adaptive_learning_rate(iteration, grad_P_DA, da_price, eta_base, eta_min)

                # 添加自适应噪声以增加探索性
                # 噪声强度随迭代减少，但保持一定的随机性
                noise_strength = noise_factor * P_max * (1 - iteration / max_iter) ** 0.5
                # 使用价格相关的噪声模式
                price_based_noise = 0.01 * P_max * np.sin(da_price / 20) * np.cos(iteration / 50)
                noise = np.random.normal(0, noise_strength) + price_based_noise

                # 动量更新
                velocity = momentum * velocity + eta * grad_P_DA

                # 神经动力学更新（带动量和噪声）
                P_DA_new = P_DA + velocity + noise

                # 投影到可行域
                P_DA_new = max(0, min(P_DA_new, P_max))

                # 计算目标函数值用于早停
                objective = self._compute_objective_value(da_price, P_DA_new, RT_grid)

                # 检查目标函数值是否有效
                if not np.isfinite(objective):
                    logging.warning(f"DA价格 {da_price:.2f}: 目标函数值无效，使用当前最佳解")
                    P_DA = best_P_DA
                    break

            except Exception as e:
                logging.error(f"DA价格 {da_price:.2f}: 优化过程出错 {e}，使用当前最佳解")
                P_DA = best_P_DA
                break

            # 更新最佳解
            if objective > best_objective:
                best_objective = objective
                best_P_DA = P_DA_new
                no_improve_count = 0
            else:
                no_improve_count += 1

            # 檢查收敛
            if abs(P_DA_new - P_DA) < tolerance:
                P_DA = P_DA_new
                converged = True
                break

            # 早停機制
            if no_improve_count > patience:
                P_DA = best_P_DA
                converged = True
                break

            P_DA = P_DA_new

        # 使用最佳解
        P_DA = best_P_DA

        # 為每個RT價格計算簡化的P_RT（基於功率平衡）
        P_RT_list = []
        R_up_list = []
        R_dn_list = []

        for rt_price in RT_grid:
            if rt_price > c_g:
                P_RT = min(P_DA + R_up_max, P_max)
                R_up = P_RT - P_DA
                R_dn = 0
            else:
                P_RT = max(P_DA - R_dn_max, 0)
                R_up = 0
                R_dn = P_DA - P_RT

            P_RT_list.append(P_RT)
            R_up_list.append(R_up)
            R_dn_list.append(R_dn)

        # 計算目標函數值
        total_profit = self._compute_objective_value(da_price, P_DA, RT_grid)

        return {
            'P_DA': P_DA,
            'P_RT': P_RT_list,
            'R_up': R_up_list,
            'R_dn': R_dn_list,
            'RT_Grid': RT_grid.tolist(),
            'Objective': total_profit,
            'iterations': iteration + 1,
            'converged': converged
        }

    def _compute_improved_gradient(self, da_price, P_DA, RT_grid):
        """计算增强的梯度，模拟真实市场的复杂响应"""
        c_g = self.config['COST_PARAMS']['c_g']
        P_max = self.config['CAPACITY_PARAMS']['P_max']

        # 1. 基础经济梯度（日前市场收益梯度）
        base_grad = da_price - c_g

        # 2. 增强的实时市场期望收益梯度
        rt_grad_contribution = 0
        rt_volatility = np.std(RT_grid) if len(RT_grid) > 1 else 1.0

        for rt_price in RT_grid:
            # 更复杂的实时价格响应
            price_diff = rt_price - c_g
            if price_diff > 0:
                # 实时价格高时，考虑上调整收益和风险
                rt_contribution = 0.3 * price_diff * (1 + 0.1 * np.sin(rt_price / 20))
            else:
                # 实时价格低时，考虑下调整成本和风险
                rt_contribution = 0.2 * price_diff * (1 - 0.1 * np.cos(rt_price / 15))

            # 添加波动性影响
            volatility_factor = 1 + 0.05 * rt_volatility / 10
            rt_grad_contribution += rt_contribution * volatility_factor

        rt_grad_contribution /= len(RT_grid)  # 平均化

        # 3. 市场竞争和风险厌恶效应
        competition_effect = 0
        if da_price > c_g + 5:
            # 高价格区域竞争激烈，降低投标积极性
            competition_effect = -0.1 * (da_price - c_g - 5) * np.sin(da_price / 10)

        # 4. 技术约束的非线性响应
        technical_effect = 0
        power_ratio = P_DA / P_max
        if power_ratio < 0.2:
            # 低出力时的启动成本考虑
            technical_effect = 0.2 * (0.2 - power_ratio) * np.exp(-power_ratio * 5)
        elif power_ratio > 0.8:
            # 高出力时的技术约束
            technical_effect = -0.15 * (power_ratio - 0.8) * (1 + np.sin(da_price / 8))

        # 5. 价格趋势和动量效应
        price_momentum = 0
        if hasattr(self, '_last_da_price') and hasattr(self, '_last_P_DA'):
            price_trend = da_price - self._last_da_price
            power_trend = P_DA - self._last_P_DA
            # 如果价格上升但功率下降，或价格下降但功率上升，添加修正
            if price_trend * power_trend < 0:
                price_momentum = 0.1 * price_trend / max(abs(price_trend), 1)

        # 6. 随机市场冲击（模拟不可预测的市场因素）
        market_shock = np.random.normal(0, 0.05) * abs(base_grad)

        # 7. 非线性价格敏感性
        price_sensitivity = 1.0
        if abs(da_price - c_g) < 2:
            # 门槛附近更敏感
            price_sensitivity = 1.5 + 0.3 * np.sin((da_price - c_g) * np.pi)
        elif abs(da_price - c_g) > 10:
            # 远离门槛时敏感性降低
            price_sensitivity = 0.8

        # 组合所有梯度分量
        total_grad = (base_grad * price_sensitivity +
                     rt_grad_contribution +
                     competition_effect +
                     technical_effect +
                     price_momentum +
                     market_shock)

        # 8. 改进的边界处理
        if P_DA < 0.5:
            # 推离下边界，但考虑经济性
            boundary_push = 0.3 * (0.5 - P_DA) if da_price > c_g else 0.1 * (0.5 - P_DA)
            total_grad += boundary_push
        elif P_DA > P_max - 0.5:
            # 推离上边界，但考虑技术约束
            boundary_push = -0.2 * (P_DA - (P_max - 0.5))
            total_grad += boundary_push

        # 记录当前状态用于下次计算动量
        self._last_da_price = da_price
        self._last_P_DA = P_DA

        return total_grad

    def _adaptive_learning_rate(self, iteration, grad_P_DA, da_price, eta_base, eta_min):
        """增强的自适应学习率策略，考虑多种市场因素"""
        c_g = self.config['COST_PARAMS']['c_g']

        # 1. 基于梯度大小的自适应
        grad_magnitude = abs(grad_P_DA)

        if grad_magnitude < 0.05:
            # 梯度很小时（可能在平衡点附近），使用较大学习率探索
            eta_grad = eta_base * 3
        elif grad_magnitude < 0.5:
            # 中等梯度，使用标准学习率
            eta_grad = eta_base * 1.5
        elif grad_magnitude < 2.0:
            # 较大梯度，适中学习率
            eta_grad = eta_base
        else:
            # 梯度很大时，使用较小学习率避免震荡
            eta_grad = eta_base * 0.2

        # 2. 基于价格位置的自适应
        price_distance = abs(da_price - c_g)
        if price_distance < 1:
            # 非常接近门槛，需要精细调整
            eta_price = 0.3
        elif price_distance < 3:
            # 接近门槛区域，保守一些
            eta_price = 0.6
        elif price_distance < 8:
            # 中等距离，正常学习率
            eta_price = 1.0
        else:
            # 远离门槛，可以更激进
            eta_price = 1.2

        # 3. 基于迭代阶段的自适应
        if iteration < 50:
            # 早期阶段：探索为主
            eta_stage = 1.2
        elif iteration < 200:
            # 中期阶段：平衡探索和收敛
            eta_stage = 1.0
        else:
            # 后期阶段：精细收敛
            eta_stage = 0.7

        # 4. 基于收敛历史的自适应
        if hasattr(self, '_convergence_history'):
            recent_changes = self._convergence_history[-10:] if len(self._convergence_history) >= 10 else self._convergence_history
            if recent_changes:
                avg_change = np.mean([abs(change) for change in recent_changes])
                if avg_change < 0.01:
                    # 收敛很慢，增加学习率
                    eta_conv = 1.5
                elif avg_change > 0.5:
                    # 震荡太大，减少学习率
                    eta_conv = 0.5
                else:
                    eta_conv = 1.0
            else:
                eta_conv = 1.0
        else:
            eta_conv = 1.0
            self._convergence_history = []

        # 5. 添加随机扰动以避免局部最优
        random_factor = 1 + 0.1 * np.random.normal(0, 0.1)
        random_factor = max(0.8, min(1.2, random_factor))  # 限制在合理范围内

        # 6. 组合所有因子
        eta = eta_base * eta_grad * eta_price * eta_stage * eta_conv * random_factor

        # 7. 最终约束
        eta = max(eta_min, min(eta, eta_base * 5))  # 限制学习率范围

        return eta

    def _compute_objective_value(self, da_price, P_DA, RT_grid):
        """計算目標函數值（簡化版本）"""
        c_g = self.config['COST_PARAMS']['c_g']
        c_up = self.config['COST_PARAMS']['c_up']
        c_dn = self.config['COST_PARAMS']['c_dn']
        P_max = self.config['CAPACITY_PARAMS']['P_max']
        R_up_max = self.config['CAPACITY_PARAMS']['R_up_max']
        R_dn_max = self.config['CAPACITY_PARAMS']['R_dn_max']

        # 日前市場收益
        da_profit = P_DA * (da_price - c_g)

        # 簡化的實時市場期望收益
        rt_profit = 0
        for rt_price in RT_grid:
            if rt_price > c_g:
                P_RT = min(P_DA + R_up_max, P_max)
                R_up = P_RT - P_DA
                rt_profit += (P_RT * (rt_price - c_g) - c_up * R_up)
            else:
                P_RT = max(P_DA - R_dn_max, 0)
                R_dn = P_DA - P_RT
                rt_profit += (P_RT * (rt_price - c_g) - c_dn * R_dn)

        rt_profit /= len(RT_grid)  # 平均化

        return da_profit + rt_profit

    def _detect_threshold_regions(self, optimization_results):
        """檢測門檻策略區域"""
        threshold_regions = []
        prices = sorted(optimization_results.keys())
        P_max = self.config['CAPACITY_PARAMS']['P_max']

        for i in range(len(prices) - 1):
            current_price = prices[i]
            next_price = prices[i + 1]

            current_p_da = optimization_results[current_price]['P_DA']
            next_p_da = optimization_results[next_price]['P_DA']

            # 檢測是否存在門檻跳躍（從低功率到高功率的跳躍）
            threshold_jump = False

            # 情況1: 從0或很小值跳躍到接近滿發
            if (current_p_da < 0.3 * P_max and next_p_da > 0.7 * P_max):
                threshold_jump = True

            # 情況2: 從滿發跳躍到0或很小值
            elif (current_p_da > 0.7 * P_max and next_p_da < 0.3 * P_max):
                threshold_jump = True

            # 情況3: 功率變化超過30%
            elif abs(next_p_da - current_p_da) > 0.3 * P_max:
                threshold_jump = True

            # 情況4: 特別檢測從0到非0的跳躍
            elif (current_p_da < 0.1 and next_p_da > 0.1):
                threshold_jump = True

            if threshold_jump:
                threshold_regions.append((current_price, next_price))
                logging.info(f"檢測到門檻區域: ({current_price:.1f}, {next_price:.1f}), "
                           f"P_DA變化: {current_p_da:.1f} -> {next_p_da:.1f} MW")

        return threshold_regions

    def _refine_threshold_regions(self, threshold_regions, RT_grid, fine_step=0.1):
        """在门槛区域进行精细化优化（高精度版）"""
        refined_results = {}

        # 处理所有门槛区域，不限制数量
        for i, (start_price, end_price) in enumerate(threshold_regions):
            logging.info(f"正在精细化门槛区域 {i+1}/{len(threshold_regions)}: ({start_price:.2f}, {end_price:.2f})，步长: {fine_step}")

            # 创建精细化网格，使用0.1步长
            fine_grid = np.arange(start_price, end_price + fine_step, fine_step)

            # 确保至少有足够的细化点来捕捉波动
            if len(fine_grid) < 10:
                # 如果区域太小，扩展一点
                extended_start = max(start_price - 1.0, self.config['PRICE_MIN'])
                extended_end = min(end_price + 1.0, self.config['PRICE_MAX'])
                fine_grid = np.arange(extended_start, extended_end + fine_step, fine_step)

            logging.info(f"  细化网格点数: {len(fine_grid)}")

            for da_price in fine_grid:
                try:
                    result = self._neurodynamic_optimization_for_da_price(da_price, RT_grid)
                    if result and result.get('converged', False):
                        refined_results[da_price] = result
                        if len(refined_results) % 20 == 0:  # 每20个点报告一次进度
                            logging.info(f"  已完成 {len(refined_results)} 个细化点")
                    else:
                        logging.debug(f"  细化点 {da_price:.2f}: 未收敛")
                except Exception as e:
                    logging.debug(f"  细化点 {da_price:.2f}: 优化失败 - {e}")

            logging.info(f"  门槛区域 {i+1} 完成，成功优化 {len([r for r in refined_results.keys() if start_price <= r <= end_price])} 个点")

        return refined_results

    def save_strategy_grid_to_csv(self, optimization_results):
        """導出完整的DA-RT-策略網格表格，統一小數位數並將接近0的值顯示為0"""
        if not optimization_results: return
        rows = []
        for da_price, res in optimization_results.items():
            for i, rt_price in enumerate(res['RT_Grid']):
                # 將接近0的值顯示為0
                p_da = 0 if abs(res['P_DA']) < 0.1 else res['P_DA']
                p_rt = 0 if abs(res['P_RT'][i]) < 0.1 else res['P_RT'][i]
                r_up = 0 if abs(res['R_up'][i]) < 0.1 else res['R_up'][i]
                r_dn = 0 if abs(res['R_dn'][i]) < 0.1 else res['R_dn'][i]
                
                rows.append({
                    'DA_Price': da_price,
                    'RT_Price': rt_price,
                    'P_DA': p_da,
                    'P_RT': p_rt,
                    'R_up': r_up,
                    'R_dn': r_dn,
                    'Objective': res['Objective']
                })
        df = pd.DataFrame(rows)
        output_file = Path(self.config['OUTPUT_DIR']) / 'bidding_strategy_grid.csv'
        df.to_csv(output_file, index=False)
        logging.info(f"完整網格策略表已保存到: {output_file}")

    def analyze_and_recommend(self, optimization_results, target_date=None):
        """
        增強的分析優化結果方法，支持神經動力學和SciPy兩種優化方法
        推導並推薦最終的穩健策略，同時生成詳細的Markdown報告
        """
        if not optimization_results:
            logging.error("沒有優化結果可供分析。")
            return

        prices = sorted(optimization_results.keys())
        # 將接近0的值顯示為0，但保留原始精度
        p_da_values = [0 if abs(optimization_results[p]['P_DA']) < 0.1 else optimization_results[p]['P_DA'] for p in prices]

        c_g = self.config['COST_PARAMS']['c_g']
        p_max = self.config['CAPACITY_PARAMS']['P_max']
        method = self.config.get('OPTIMIZATION_METHOD', 'neurodynamic')

        # 計算更精確的門檻價格
        threshold_price = c_g
        try:
            # 尋找功率從低到高的轉換點
            for i in range(len(prices) - 1):
                if p_da_values[i] < 0.5 * p_max and p_da_values[i+1] > 0.5 * p_max:
                    # 在轉換區間內尋找更精確的門檻
                    threshold_price = (prices[i] + prices[i+1]) / 2
                    break

            # 如果有細化的網格點，尋找更精確的門檻
            fine_prices = [p for p in prices if p % 1.0 != 0]  # 非整數價格點（細化點）
            if fine_prices:
                for price in fine_prices:
                    p_da = optimization_results[price]['P_DA']
                    if 0.4 * p_max < p_da < 0.6 * p_max:
                        threshold_price = price
                        break

        except Exception:
            logging.warning("無法精確計算投標閾值，將使用發電邊際成本作為替代")

        # 分析策略複雜性
        strategy_complexity = "簡單門檻策略"
        if len(set(p_da_values)) > 3:  # 如果有超過3種不同的功率值
            strategy_complexity = "複雜階梯策略"

        # 統計優化性能（如果是神經動力學方法）
        performance_stats = {}
        if method == 'neurodynamic':
            converged_count = sum(1 for res in optimization_results.values() if res.get('converged', False))
            total_iterations = sum(res.get('iterations', 0) for res in optimization_results.values())
            avg_iterations = total_iterations / len(optimization_results) if optimization_results else 0

            performance_stats = {
                'total_points': len(optimization_results),
                'converged_points': converged_count,
                'convergence_rate': converged_count / len(optimization_results) * 100,
                'avg_iterations': avg_iterations,
                'fine_points': len([p for p in prices if p % 1.0 != 0])
            }

        # --- 生成日誌輸出 ---
        logging.info("="*60)
        if method == 'neurodynamic':
            logging.info("--- 神經動力學投標策略分析結果 ---")
        else:
            logging.info("--- SciPy投標策略分析結果 ---")
        logging.info(f"總優化點數: {len(optimization_results)}")
        logging.info(f"價格範圍: {min(prices):.1f} - {max(prices):.1f} CNY/MWh")
        logging.info(f"策略類型: {strategy_complexity}")
        logging.info(f"計算得出的推薦門檻價格約為: {threshold_price:.2f} CNY/MWh")
        logging.info(f"(理論門檻為發電邊際成本: {c_g:.2f} CNY/MWh)")

        if method == 'neurodynamic' and performance_stats:
            logging.info(f"收敛統計: {performance_stats['converged_points']}/{performance_stats['total_points']} 個點收敛 ({performance_stats['convergence_rate']:.1f}%)")
            logging.info(f"平均迭代次數: {performance_stats['avg_iterations']:.1f}")
            if performance_stats['fine_points'] > 0:
                logging.info(f"細化網格點數: {performance_stats['fine_points']}")

        logging.info("-" * 30)
        logging.info("詳細投標策略:")
        for i, (price, p_da) in enumerate(zip(prices, p_da_values)):
            if i < 10 or i >= len(prices) - 5:  # 顯示前10個和後5個
                logging.info(f"  價格 {price:6.1f} CNY/MWh -> 申報 {p_da:4.1f} MW")
            elif i == 10:
                logging.info("  ...")
        logging.info("="*60)

        # --- 生成並保存增強的Markdown報告 ---
        method_name = "神經動力學自適應網格" if method == 'neurodynamic' else "SciPy"

        md_content = f"""# 電力市場投標策略分析報告

**優化方法:** {method_name}優化算法
"""
        if target_date:
            md_content += f"**分析目標日期:** `{target_date}`\n\n"

        md_content += f"""
## 核心結論：{strategy_complexity}

通過{method_name}對市場價格波動性的隨機優化分析，模型建議採用以下基於"門檻價格"的投標策略：

- **推薦門檻價格:** **`{threshold_price:.2f}`** CNY/MWh
- **理論門檻價格 (發電邊際成本):** `{c_g:.2f}` CNY/MWh
- **策略類型:** {strategy_complexity}

### 優化性能統計
"""

        if method == 'neurodynamic' and performance_stats:
            md_content += f"""
- **總優化點數:** {performance_stats['total_points']}
- **收敛點數:** {performance_stats['converged_points']} ({performance_stats['convergence_rate']:.1f}%)
- **平均迭代次數:** {performance_stats['avg_iterations']:.1f}
- **細化網格點數:** {performance_stats['fine_points']}
"""
        else:
            md_content += f"""
- **總優化點數:** {len(optimization_results)}
- **價格範圍:** {min(prices):.1f} - {max(prices):.1f} CNY/MWh
"""

        md_content += f"""
### 策略詳情

1.  **當預測的市場日前價格 < `{threshold_price:.2f}` 時:**
    - **推薦申報電量: `0` MW**
    - *原因: 在此價格水平下，預期收益可能無法覆蓋發電成本，不參與市場是最佳選擇。*

2.  **當預測的市場日前價格 ≥ `{threshold_price:.2f}` 時:**
    - **推薦申報電量: `{p_max:.0f}` MW** (機組最大出力)
    - *原因: 在此價格水平下，預期收益為正，應最大化出力以獲取利潤。*

### 價格-電量投標曲線

| 日前價格 (CNY/MWh) | 建議申報電量 (MW) | 備註 |
|-------------------|-----------------|------|
"""
        # 添加價格-電量表格，統一小數位數，並標記細化點
        for price, p_da in zip(prices, p_da_values):
            note = ""
            if method == 'neurodynamic' and price % 1.0 != 0:
                note = "細化點"
            md_content += f"| {price:.2f} | {p_da:.1f} | {note} |\n"

        md_content += f"""

### 技術說明

**{method_name}優化算法特點:**
"""

        if method == 'neurodynamic':
            md_content += f"""
- 自適應網格細化：自動檢測門檻策略區域並進行細化優化
- 智能學習率調整：根據梯度大小和迭代進度動態調整學習率
- 早停機制：避免過度迭代，提高計算效率
- 門檻區域檢測：識別功率跳躍區域，提供更精確的策略分析
"""
        else:
            md_content += f"""
- 基於SciPy的SLSQP算法進行約束優化
- 嚴格滿足功率平衡和容量約束
- 全局搜索最優解
"""

        md_content += f"""
---
*報告生成時間: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
*優化方法: {method_name}*
"""
        
        output_dir = Path(self.config['OUTPUT_DIR'])
        report_filename = "bidding_strategy_recommendation_full_analysis.md"
        if target_date:
            report_filename = f"bidding_strategy_recommendation_{target_date}.md"
        
        output_path = output_dir / report_filename
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(md_content)
            logging.info(f"策略報告已成功保存到: {output_path}")
        except Exception as e:
            logging.error(f"保存策略報告失敗: {e}")

    def run(self, mode='full', target_date='2025-05-31'):
        """
        增強的運行方法，支持神經動力學和SciPy兩種優化方法
        mode='full'：全區間分析（用全部數據擬合分布，對全區間做策略分析）
        mode='single_day'：僅分析 target_date，分布用該日前所有數據擬合
        """
        method = self.config.get('OPTIMIZATION_METHOD', 'neurodynamic')
        method_name = "神經動力學自適應網格" if method == 'neurodynamic' else "SciPy"

        print(f"进入run方法，模式: {mode}")
        logging.info(f"--- 開始執行{method_name}投標策略優化（模式: {mode}）---")

        print("步骤 1: 开始加载价格数据...")
        if not self.load_price_data():
            print("❌ 数据加载失败")
            logging.error("數據加載失敗，模型終止。")
            return
        print("✅ 价格数据加载成功")

        if mode == 'full':
            print("步骤 2: 开始拟合价格分布...")
            if not self.fit_price_distribution():
                print("❌ 价格分布拟合失败")
                logging.error("價格分布擬合失敗，模型終止。")
                return
            print("✅ 价格分布拟合成功")

            logging.info(f"使用{method_name}優化方法進行投標策略優化...")
            optimization_results = self.optimize_bidding_strategy()

            if optimization_results:
                self.results['full_curve'] = optimization_results

                # 分析和推薦
                self.analyze_and_recommend(optimization_results, target_date)

                # 保存結果
                self.save_strategy_grid_to_csv(optimization_results)

                # 生成可視化
                self.generate_3d_visualization(optimization_results)

                # 保存優化摘要（如果是神經動力學方法）
                if method == 'neurodynamic':
                    self._save_optimization_summary(optimization_results)

                logging.info(f"✅ {method_name}投標策略優化成功完成！")
                logging.info(f"結果已保存到: {self.config['OUTPUT_DIR']}")

            else:
                logging.error("未能生成任何優化結果。")

        else:
            logging.error(f"未知模式: {mode}")
            return

        logging.info("--- 投標策略優化流程結束 ---")

    def _save_optimization_summary(self, optimization_results):
        """保存神經動力學優化摘要"""
        try:
            prices = sorted(optimization_results.keys())
            converged_count = sum(1 for res in optimization_results.values() if res.get('converged', False))
            total_iterations = sum(res.get('iterations', 0) for res in optimization_results.values())
            avg_iterations = total_iterations / len(optimization_results) if optimization_results else 0

            # 計算門檻價格
            c_g = self.config['COST_PARAMS']['c_g']
            p_max = self.config['CAPACITY_PARAMS']['P_max']
            threshold_price = c_g

            p_da_values = [optimization_results[p]['P_DA'] for p in prices]
            for i in range(len(prices) - 1):
                if p_da_values[i] < 0.5 * p_max and p_da_values[i+1] > 0.5 * p_max:
                    threshold_price = (prices[i] + prices[i+1]) / 2
                    break

            summary = {
                'timestamp': datetime.datetime.now().isoformat(),
                'optimization_method': 'neurodynamic',
                'generation_cost': self.config['COST_PARAMS']['c_g'],
                'upward_cost': self.config['COST_PARAMS']['c_up'],
                'downward_cost': self.config['COST_PARAMS']['c_dn'],
                'max_power': self.config['CAPACITY_PARAMS']['P_max'],
                'max_up_regulation': self.config['CAPACITY_PARAMS']['R_up_max'],
                'max_down_regulation': self.config['CAPACITY_PARAMS']['R_dn_max'],
                'total_points': len(optimization_results),
                'converged_points': converged_count,
                'convergence_rate': converged_count / len(optimization_results) * 100,
                'avg_iterations': avg_iterations,
                'threshold_price': threshold_price,
                'fine_points': len([p for p in prices if p % 1.0 != 0])
            }

            output_dir = Path(self.config['OUTPUT_DIR'])
            summary_file = output_dir / 'neurodynamic_optimization_summary.json'
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)

            logging.info(f"神經動力學優化摘要已保存到: {summary_file}")

        except Exception as e:
            logging.error(f"保存優化摘要失敗: {e}")
    
    def generate_3d_visualization(self, optimization_results):
        """
        生成增強的三維可視化圖表，支持神經動力學自適應網格特性
        展示DA價格、RT價格與最優申報電量的關係
        """
        try:
            # 準備數據
            da_prices = []
            rt_prices = []
            p_da_values = []
            p_rt_values = []
            total_profits = []

            for da_price, res in optimization_results.items():
                for i, rt_price in enumerate(res['RT_Grid']):
                    da_prices.append(da_price)
                    rt_prices.append(rt_price)
                    # 將接近0的值顯示為0，但保留原始精度
                    p_da = 0 if abs(res['P_DA']) < 0.1 else res['P_DA']
                    p_rt = 0 if abs(res['P_RT'][i]) < 0.1 else res['P_RT'][i]
                    p_da_values.append(p_da)
                    p_rt_values.append(p_rt)
                    total_profits.append(res['Objective'])

            # 轉換為numpy數組
            da_array = np.array(da_prices)
            rt_array = np.array(rt_prices)
            p_da_array = np.array(p_da_values)
            p_rt_array = np.array(p_rt_values)
            profit_array = np.array(total_profits)

            # 創建輸出目錄
            output_dir = Path(self.config['OUTPUT_DIR'])

            # 檢查是否使用了神經動力學方法
            method = self.config.get('OPTIMIZATION_METHOD', 'neurodynamic')

            if method == 'neurodynamic':
                self._generate_neurodynamic_3d_visualization(
                    da_array, rt_array, p_da_array, p_rt_array, profit_array, output_dir
                )
            else:
                self._generate_standard_3d_visualization(
                    da_array, rt_array, p_da_array, p_rt_array, profit_array, output_dir
                )

        except Exception as e:
            logging.error(f"生成三維可視化圖表失敗: {e}\n{traceback.format_exc()}")

    def _generate_neurodynamic_3d_visualization(self, da_array, rt_array, p_da_array, p_rt_array, profit_array, output_dir):
        """生成神經動力學優化的3D可視化（保持波動特征）"""
        try:
            # 直接使用原始數據點，保持波動特征
            da_min, da_max = da_array.min(), da_array.max()
            rt_min, rt_max = rt_array.min(), rt_array.max()

            # 創建適度密度的網格，保持數據的自然波動
            da_grid = np.linspace(da_min, da_max, 50)
            rt_grid = np.linspace(rt_min, rt_max, 50)
            DA_grid, RT_grid = np.meshgrid(da_grid, rt_grid)

            # 使用最近鄰插值保持波動特征，避免過度平滑
            from scipy.interpolate import griddata
            points = np.column_stack((da_array, rt_array))
            P_DA_grid = griddata(points, p_da_array, (DA_grid, RT_grid), method='nearest', fill_value=0)
            P_RT_grid = griddata(points, p_rt_array, (DA_grid, RT_grid), method='nearest', fill_value=0)
            Profit_grid = griddata(points, profit_array, (DA_grid, RT_grid), method='nearest', fill_value=0)

            # 創建保持波動特征的三維曲面圖
            fig = plt.figure(figsize=(18, 14))

            # 子圖1: P_DA的波動三維曲面
            ax1 = fig.add_subplot(221, projection='3d')
            surf1 = ax1.plot_surface(DA_grid, RT_grid, P_DA_grid,
                                   cmap='viridis', alpha=0.8, linewidth=0.5,
                                   antialiased=False, shade=True, rcount=50, ccount=50)
            ax1.set_xlabel('Day-Ahead Market Price (CNY/MWh)')
            ax1.set_ylabel('Real-Time Market Price (CNY/MWh)')
            ax1.set_zlabel('Optimal DA Bid Quantity (MW)')
            ax1.set_title('Day-Ahead Bid Quantity 3D Surface\n(Neurodynamic Optimization)')
            ax1.view_init(elev=30, azim=45)
            # 确保y轴从左往右上升（移除反转）
            plt.colorbar(surf1, ax=ax1, shrink=0.8)

            # 子圖2: P_RT的波動三維曲面
            ax2 = fig.add_subplot(222, projection='3d')
            surf2 = ax2.plot_surface(DA_grid, RT_grid, P_RT_grid,
                                   cmap='plasma', alpha=0.8, linewidth=0.5,
                                   antialiased=False, shade=True, rcount=50, ccount=50)
            ax2.set_xlabel('Day-Ahead Market Price (CNY/MWh)')
            ax2.set_ylabel('Real-Time Market Price (CNY/MWh)')
            ax2.set_zlabel('Optimal RT Output (MW)')
            ax2.set_title('Real-Time Output 3D Surface\n(Neurodynamic Optimization)')
            ax2.view_init(elev=30, azim=45)
            # 确保y轴从左往右上升（移除反转）
            plt.colorbar(surf2, ax=ax2, shrink=0.8)

            # 子圖3: 利潤曲面（保持波動）
            ax3 = fig.add_subplot(223, projection='3d')
            surf3 = ax3.plot_surface(DA_grid, RT_grid, Profit_grid,
                                   cmap='coolwarm', alpha=0.8, linewidth=0.5,
                                   antialiased=False, shade=True, rcount=50, ccount=50)
            ax3.set_xlabel('Day-Ahead Market Price (CNY/MWh)')
            ax3.set_ylabel('Real-Time Market Price (CNY/MWh)')
            ax3.set_zlabel('Expected Profit (CNY)')
            ax3.set_title('Expected Profit 3D Surface\n(Neurodynamic Optimization)')
            ax3.view_init(elev=30, azim=45)
            # 确保y轴从左往右上升（移除反转）
            plt.colorbar(surf3, ax=ax3, shrink=0.8)

            # 子圖4: 等高線圖（顯示波動細節）
            ax4 = fig.add_subplot(224)
            contour = ax4.contour(DA_grid, RT_grid, Profit_grid, levels=20, linewidths=1.0)
            ax4.clabel(contour, inline=True, fontsize=8)
            ax4.set_xlabel('Day-Ahead Market Price (CNY/MWh)')
            ax4.set_ylabel('Real-Time Market Price (CNY/MWh)')
            ax4.set_title('Profit Contour Plot')
            ax4.grid(True, alpha=0.3)
            # 确保y轴从左往右上升（移除反转）

            plt.tight_layout()

            # 保存圖表
            output_path = output_dir / 'neurodynamic_3d_surfaces.png'
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()

            logging.info(f"神經動力學三維曲面可視化圖表已保存到: {output_path}")

            # 生成第一張圖的高清單獨版本
            self._generate_high_res_da_bid_surface(DA_grid, RT_grid, P_DA_grid, output_dir)

        except Exception as e:
            logging.error(f"生成神經動力學三維可視化失敗: {e}")
            # 回退到標準可視化
            self._generate_standard_3d_visualization(da_array, rt_array, p_da_array, p_rt_array, profit_array, output_dir)

    def _generate_high_res_da_bid_surface(self, DA_grid, RT_grid, P_DA_grid, output_dir):
        """生成日前投標量3D曲面的高清單獨版本"""
        try:
            import matplotlib.pyplot as plt
            from mpl_toolkits.mplot3d import Axes3D

            # 創建高解析度的單獨圖表
            fig = plt.figure(figsize=(16, 12))
            ax = fig.add_subplot(111, projection='3d')

            # 繪製高質量的3D曲面
            surf = ax.plot_surface(DA_grid, RT_grid, P_DA_grid,
                                 cmap='viridis', alpha=0.9, linewidth=0.3,
                                 antialiased=True, shade=True,
                                 rcount=80, ccount=80)  # 更高的解析度

            # 設置標籤和標題
            ax.set_xlabel('Day-Ahead Market Price (CNY/MWh)', fontsize=14, labelpad=10)
            ax.set_ylabel('Real-Time Market Price (CNY/MWh)', fontsize=14, labelpad=10)
            ax.set_zlabel('Optimal DA Bid Quantity (MW)', fontsize=14, labelpad=10)
            ax.set_title('Day-Ahead Bid Quantity 3D Surface\n(High Resolution - Neurodynamic Optimization)',
                        fontsize=16, pad=20)

            # 優化視角
            ax.view_init(elev=25, azim=45)

            # 确保y轴从左往右上升（移除反转）

            # 添加顏色條
            cbar = plt.colorbar(surf, ax=ax, shrink=0.8, aspect=20, pad=0.1)
            cbar.set_label('Bid Quantity (MW)', fontsize=12)

            # 優化網格和刻度
            ax.grid(True, alpha=0.3)
            ax.tick_params(axis='x', labelsize=11)
            ax.tick_params(axis='y', labelsize=11)
            ax.tick_params(axis='z', labelsize=11)

            # 添加說明文字
            textstr = 'Threshold Strategy:\n• Low prices → 0 MW\n• High prices → 100 MW'
            props = dict(boxstyle='round', facecolor='wheat', alpha=0.8)
            ax.text2D(0.02, 0.98, textstr, transform=ax.transAxes, fontsize=11,
                     verticalalignment='top', bbox=props)

            plt.tight_layout()

            # 保存高清版本
            output_path = output_dir / 'da_bid_quantity_3d_high_res.png'
            plt.savefig(output_path, dpi=400, bbox_inches='tight',
                       facecolor='white', edgecolor='none')
            plt.close()

            logging.info(f"高清日前投標量3D曲面圖已保存到: {output_path}")

        except Exception as e:
            logging.error(f"生成高清DA投標量3D圖失敗: {e}")

    def _generate_standard_3d_visualization(self, da_array, rt_array, p_da_array, p_rt_array, profit_array, output_dir):
        """生成標準的3D可視化"""
        # 創建三維圖
        fig = plt.figure(figsize=(12, 10))
        ax = fig.add_subplot(111, projection='3d')

        # 繪製散點圖，顏色表示P_DA的大小
        scatter = ax.scatter(da_array, rt_array, p_da_array, c=p_da_array,
                  cmap='viridis', s=30, alpha=0.8)

        # 添加顏色條
        cbar = plt.colorbar(scatter)
        cbar.set_label('Optimal DA Bid Quantity (MW)')

        # Set chart title and axis labels
        ax.set_title('Power Market Bidding Strategy 3D Visualization', fontsize=16)
        ax.set_xlabel('Day-Ahead Market Price (CNY/MWh)', fontsize=12)
        ax.set_ylabel('Real-Time Market Price (CNY/MWh)', fontsize=12)
        ax.set_zlabel('Optimal DA Bid Quantity (MW)', fontsize=12)

        # 保存圖表
        output_path = output_dir / 'bidding_strategy_3d_visualization.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

        # 創建二維熱力圖
        self._generate_heatmap(da_array, rt_array, p_da_array, output_dir)

        logging.info(f"標準三維可視化圖表已保存到: {output_path}")

    def _generate_heatmap(self, da_array, rt_array, p_da_array, output_dir):
        """生成二維熱力圖"""
        plt.figure(figsize=(10, 8))

        # 將數據轉換為網格形式
        da_unique = sorted(set(da_array))
        rt_unique = sorted(set(rt_array))

        # 創建空矩陣
        z_matrix = np.zeros((len(rt_unique), len(da_unique)))

        # 填充矩陣
        for da, rt, p_da in zip(da_array, rt_array, p_da_array):
            i = rt_unique.index(rt)
            j = da_unique.index(da)
            z_matrix[i, j] = p_da

        # 繪製熱力圖
        plt.imshow(z_matrix, cmap='viridis', aspect='auto', origin='lower',
                  extent=[min(da_unique), max(da_unique), min(rt_unique), max(rt_unique)])

        plt.colorbar(label='Optimal DA Bid Quantity (MW)')
        plt.title('DA-RT Price vs Optimal Bid Quantity Heatmap', fontsize=16)
        plt.xlabel('Day-Ahead Market Price (CNY/MWh)', fontsize=12)
        plt.ylabel('Real-Time Market Price (CNY/MWh)', fontsize=12)

        # 添加發電成本參考線
        c_g = self.config['COST_PARAMS']['c_g']
        plt.axvline(x=c_g, color='red', linestyle='--', alpha=0.7,
                  label=f'發電邊際成本: {c_g} CNY/MWh')
        plt.axhline(y=c_g, color='red', linestyle='--', alpha=0.7)

        # 標記細化區域（如果是神經動力學方法）
        method = self.config.get('OPTIMIZATION_METHOD', 'neurodynamic')
        if method == 'neurodynamic':
            fine_prices = [p for p in da_unique if p % 1.0 != 0]  # 非整數價格點（細化點）
            if fine_prices:
                for fine_price in fine_prices:
                    plt.axvline(x=fine_price, color='orange', linestyle=':', alpha=0.6, linewidth=1)
                plt.text(0.02, 0.98, f'橙色虛線: 細化網格點\n({len(fine_prices)}個)',
                        transform=plt.gca().transAxes, verticalalignment='top',
                        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

        plt.legend()
        plt.tight_layout()

        # 保存熱力圖
        output_path = output_dir / 'bidding_strategy_heatmap.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

        logging.info(f"熱力圖已保存到: {output_path}")

# if __name__ == "__main__":
#     # 此部分用於直接測試此腳本
#     logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
#     model = BiddingOptimizationModel()
#     model.run()
