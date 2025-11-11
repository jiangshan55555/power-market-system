# ⚡ 电力市场智能预测与投标优化系统

基于神经动力学优化和机器学习集成的电力市场价格预测与投标策略优化系统。

## 🎯 系统概述

本系统是一个完整的电力市场决策支持工具，集成了：
- **价格预测模块**：使用多模型智能集成预测电力市场实时出清价格
- **投标优化模块**：基于神经动力学自适应网格算法优化投标策略
- **数据管理模块**：支持数据上传、查询和可视化
- **Web界面**：直观的用户界面，实时显示预测和优化结果

## ✨ 核心功能

### 1. 📊 数据库状态
- 实时显示数据库连接状态
- 数据统计信息
- 数据质量检查

### 2. 📈 历史数据查询
- 上传Excel数据文件
- 按日期范围查询历史数据
- 数据可视化展示

### 3. 🔮 价格预测
- **多模型集成**：
  - 历史同期模型
  - 随机森林（Random Forest）
  - 线性回归（Linear Regression）
  - 梯度提升（Gradient Boosting）
  - XGBoost
  - 智能集成模型
- **性能指标**：MAE, RMSE, R²
- **结果可视化**：预测曲线、误差分析

### 4. ⚙️ 投标优化
- **神经动力学优化算法**：
  - 自适应学习率
  - 动态网格细化
  - 收敛性保证
- **优化目标**：最大化预期收益
- **约束条件**：
  - 发电容量限制
  - 调整容量限制
  - 成本约束
- **输出结果**：
  - 门槛价格策略
  - 价格-电量投标曲线
  - 预期收益分析

## 🚀 快速开始

### 本地运行

1. **安装依赖**：
```bash
pip install -r requirements.txt
```

2. **启动服务**：
```bash
# Windows
启动系统.bat

# 或手动启动
python api/app.py
```

3. **访问系统**：
打开浏览器访问 http://localhost:5000

### Vercel 部署

详见 [DEPLOYMENT.md](DEPLOYMENT.md)

## 📁 项目结构

```
power-prediction-system/
├── api/                          # Flask API 后端
│   ├── app.py                   # 主应用入口
│   ├── run_original_prediction.py  # 预测模块封装
│   ├── run_bidding_optimization.py # 优化模块封装
│   └── requirements.txt         # API 依赖
├── src/                         # 核心算法模块
│   ├── predictions/             # 预测模型实现
│   ├── optimization/            # 优化算法实现
│   ├── utils/                   # 工具函数
│   ├── main_prediction.py       # 预测主程序
│   └── main_bidding.py          # 优化主程序
├── config/                      # 配置文件
│   └── config.json             # 系统配置
├── data/                        # 原始数据
│   ├── rawdata_0501.xlsx       # 5月数据
│   └── rawdata_0601.xlsx       # 6月数据
├── output/                      # 输出结果
│   ├── predictions/            # 预测结果
│   ├── bidding/                # 投标策略
│   └── logs/                   # 日志文件
├── index.html                   # 前端页面
├── vercel.json                  # Vercel 配置
├── requirements.txt             # 项目依赖
├── DEPLOYMENT.md                # 部署指南
└── README.md                    # 项目说明
```

## 🛠️ 技术栈

### 后端
- **框架**：Flask 3.0
- **数据处理**：pandas, numpy
- **机器学习**：
  - scikit-learn（随机森林、梯度提升、线性回归）
  - XGBoost（极端梯度提升）
- **优化算法**：神经动力学自适应网格优化
- **可视化**：matplotlib, seaborn

### 前端
- **框架**：Bootstrap 5
- **图表**：Chart.js
- **UI组件**：原生 JavaScript

### 部署
- **平台**：Vercel / Railway / Render
- **容器**：支持 Docker 部署

## 📊 算法说明

### 价格预测算法

1. **历史同期模型**：基于历史同期数据的简单预测
2. **随机森林**：集成学习，抗过拟合能力强
3. **线性回归**：快速基准模型
4. **梯度提升**：逐步优化的集成方法
5. **XGBoost**：高性能梯度提升实现
6. **智能集成**：Top-K 模型筛选 + 加权平均

### 投标优化算法

**神经动力学自适应网格优化**：
- **目标函数**：最大化预期收益
- **约束条件**：容量限制、成本约束
- **优化方法**：自适应学习率 + 动态网格细化

## 📈 性能指标

### 预测性能（测试集）
- **MAE**：21.80 CNY/MWh
- **RMSE**：52.89 CNY/MWh
- **R²**：0.1893

### 优化性能
- **收敛率**：> 95%
- **平均迭代次数**：< 200
- **计算时间**：2-5分钟（全量优化）

