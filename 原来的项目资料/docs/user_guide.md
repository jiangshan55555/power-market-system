# 重慶電力市場預測與投標優化集成系統

本項目整合了電力市場價格預測和投標策略優化兩個模塊，專為重慶電力市場設計。系統可以對市場價格進行預測，並基於這些預測結果設計最優的投標策略。

## 系統架構

```
預測模型 → 數據轉換層 → 投標優化模型
```

- **預測模型**：使用隨機森林、XGBoost和LSTM等模型預測電力市場價格
- **數據轉換層**：將預測結果轉換為投標模型可接受的格式
- **投標優化模型**：基於價格分布和成本參數設計最優投標策略

## 目錄結構

```
電力市場預測與投標優化系統/
├── src/                          # 源代碼
│   ├── predictions/              # 預測模型
│   ├── optimization/             # 投標優化
│   ├── utils/                    # 工具模塊
│   ├── main_prediction.py        # 預測主程序
│   └── main_bidding.py          # 投標主程序
├── data/                         # 數據目錄
│   ├── rawdata_0501.xlsx         # 2025年5月數據
│   └── rawdata_0601.xlsx         # 2025年6月數據
├── config/                       # 配置文件
│   └── config.json
└── output/                       # 輸出結果目錄
    ├── predictions/              # 預測結果
    ├── bidding/                  # 投標結果
    └── logs/                     # 日誌文件
```

## 安裝依賴

本系統需要以下Python庫：

```bash
pip install pandas numpy matplotlib scikit-learn xgboost tensorflow scipy
```

## 使用方法

### 基本用法

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 运行预测
python src/main_prediction.py

# 3. 运行投标优化
python src/main_bidding.py
```

### 配置文件

系統使用 `config/config.json` 進行配置：

```json
{
    "data": {
        "input_file": "data/rawdata.xlsx",
        "target_column": "實時出清電價"
    },
    "bidding": {
        "optimization_method": "neurodynamic"
    }
}
```

### 示例

1. 僅執行價格預測：

```bash
python src/main_prediction.py
```

2. 執行投標優化：

```bash
python src/main_bidding.py
```

## 輸出結果

1. **預測模塊輸出**：
   - `predictions.csv`：預測結果
   - `evaluation_report.md`：預測模型評估報告
   - `prediction_plot.png`：預測可視化圖表

2. **投標優化模塊輸出**：
   - `bidding_optimization_results.xlsx`：投標優化結果
   - `bidding_strategy_report.md`：投標策略報告
   - `price_quantity_curve.png`：價格-投標量曲線
   - `rt_response_3d.png`：實時響應曲面
   - `scenario_comparison.png`：不同成本情境比較

## 模型特點

### 預測模型

- 支持多種機器學習算法：隨機森林、XGBoost和LSTM
- 遵循GAP規則，保證預測的實用性
- 自動特徵工程，捕捉時間序列特性
- 模型集成，提高預測準確性

### 投標優化模型

- **多算法支持**：神經動力學自適應網格優化 + SciPy約束優化
- **創新技術**：
  - 自適應網格細化：自動檢測門檻區域並細化優化
  - 智能學習率調整：根據優化進程動態調整
  - 早停機制：避免過度迭代，提高效率
- 基於價格概率分布的兩階段優化
- 自動從預測價格估算成本參數
- 多情境分析，提供穩健策略
- **增強的可視化**：光滑三維曲面、細化網格標記
- 完整的報告生成和性能統計

## 注意事項

1. 首次運行時需要將數據文件放置在`input`目錄下
2. 系統將自動估算成本參數，無需手動輸入發電機組參數
3. LSTM模型訓練可能需要較長時間，可使用`--run_lstm`明確指定是否運行
4. 完整的分析報告和可視化結果將保存在`output`目錄下
