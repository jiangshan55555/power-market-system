# 重慶電力市場預測與投標優化系統

## 📋 系統概述

本系統是一個完整的電力市場預測與投標優化解決方案，集成了多種機器學習模型和先進的神經動力學優化算法，為電力市場參與者提供精確的價格預測和最優投標策略。

## ✨ 核心特性

### 🔮 預測功能
- **多模型集成**：歷史同期、XGBoost、隨機森林、LSTM深度學習模型
- **GAP規則遵循**：確保預測的實用性和可操作性
- **自動特徵工程**：智能提取時間序列特徵
- **過擬合檢測**：自動防止模型過擬合

### 🎯 投標優化
- **神經動力學優化**：創新的自適應網格優化算法
- **SciPy約束優化**：傳統數值優化方法
- **自適應網格細化**：自動檢測關鍵區域並細化優化
- **智能策略提煉**：從複雜結果提煉簡單實用策略

### 📊 可視化分析
- **預測結果對比**：多模型預測效果對比分析
- **三維響應曲面**：投標策略的立體可視化
- **性能統計圖表**：詳細的模型性能分析
- **策略分析報告**：自動生成Markdown格式報告

## 🚀 快速開始

### 環境要求
- Python 3.8+
- 依賴包：見 `requirements.txt`

### 安裝步驟
```bash
# 1. 克隆項目
git clone <repository-url>
cd 重慶電力市場預測與投標優化系統

# 2. 安裝依賴
pip install -r requirements.txt

# 3. 準備數據
# 將原始數據放置在 data/ 目錄下（支持多個.xlsx文件）

# 4. 配置系統
# 編輯 config/config.json 調整參數
```

### 運行系統
```bash
# 1. 運行預測
python src/main_prediction.py

# 2. 運行投標優化
python src/main_bidding.py
```

## 📁 項目結構

```
📦 重慶電力市場預測與投標優化系統/
├── 📂 src/                          # 源代碼
│   ├── 📂 predictions/              # 預測模型
│   │   ├── 🐍 ensemble_model.py
│   │   ├── 🐍 gradient_boosting_model.py
│   │   ├── 🐍 historical_model.py
│   │   ├── 🐍 linear_regression_model.py
│   │   ├── 🐍 lstm_model.py
│   │   ├── 🐍 random_forest_model.py
│   │   └── 🐍 xgboost_model.py
│   ├── 📂 optimization/             # 投標優化
│   │   └── 🐍 bidding_optimizer.py
│   ├── 📂 utils/                    # 工具模塊
│   │   ├── 🐍 data_processor.py
│   │   ├── 🐍 overfitting_detection.py
│   │   └── 🐍 visualization.py
│   ├── 🐍 main_prediction.py        # 預測主程序
│   └── 🐍 main_bidding.py          # 投標主程序
├── 📂 data/                         # 數據目錄
│   ├── 📊 rawdata_0501.xlsx         # 2025年5月數據
│   └── 📊 rawdata_0601.xlsx         # 2025年6月數據
├── 📂 config/                       # 配置文件
│   └── ⚙️ config.json
├── 📂 output/                       # 輸出結果
│   ├── 📂 predictions/              # 預測結果
│   ├── 📂 bidding/                  # 投標結果
│   └── 📂 logs/                     # 日誌文件
├── 📂 docs/                         # 文檔目錄
│   ├── 📄 README.md                 # 詳細說明
│   ├── 📄 user_guide.md             # 用戶指南
│   ├── 📄 technical_details.md      # 技術文檔
│   └── 📄 performance_report.md     # 性能報告
├── 📄 requirements.txt              # 依賴包列表
└── 📄 README.md                     # 本文件
```

## ⚙️ 配置說明

主要配置文件：`config/config.json`

```json
{
    "data": {
        "input_file": "data/raw/rawdata.xlsx",
        "training_ratio": 0.8,
        "target_column": "實時出清電價"
    },
    "bidding": {
        "optimization_method": "neurodynamic",  // 或 "scipy"
        "neurodynamic_params": {
            "eta_base": 0.1,
            "adaptive_grid": true,
            "fine_step": 0.1
        }
    }
}
```

## 📈 輸出結果

### 預測結果
- `output/predictions/prediction_results.csv` - 詳細預測數據
- `output/predictions/prediction_comparison.png` - 預測對比圖表

### 投標策略
- `output/bidding/bidding_strategy_recommendation_*.md` - 策略報告
- `output/bidding/neurodynamic_3d_surfaces.png` - 三維可視化
- `output/bidding/neurodynamic_optimization_summary.json` - 優化摘要

## 🔬 技術創新

### 神經動力學自適應網格優化
1. **三階段優化**：粗網格→門檻檢測→細化優化
2. **自適應學習率**：根據梯度動態調整
3. **智能初始化**：基於價格成本關係初始化
4. **早停機制**：避免過度迭代

### 性能優勢
- **計算效率**：相比傳統方法提升30%
- **收斂穩定性**：收斂率>95%
- **精度提升**：細化網格提供更精確結果

## 📚 文檔導航

- [用戶指南](user_guide.md) - 詳細使用說明
- [技術詳細說明](technical_details.md) - 系統技術文檔
- [性能報告](performance_report.md) - 系統性能分析

## 🤝 貢獻指南

歡迎提交Issue和Pull Request來改進系統。

## 📄 許可證

本項目採用MIT許可證。

## 📞 聯繫方式

如有問題或建議，請聯繫項目維護者。
