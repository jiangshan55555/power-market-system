# 创建 index.js 文件

## 📝 操作步骤

### 步骤1：创建文件

在 `power-market-system/pages/` 目录下创建一个新文件，命名为 `index.js`

### 步骤2：复制以下完整代码

将下面的代码完整复制到 `index.js` 文件中：

```javascript
import { useState, useEffect } from 'react';
import Head from 'next/head';

export default function PowerMarketDashboard() {
  const [activeTab, setActiveTab] = useState('database');
  const [databaseStatus, setDatabaseStatus] = useState(null);
  const [historicalData, setHistoricalData] = useState(null);
  const [predictionResults, setPredictionResults] = useState(null);
  const [optimizationResults, setOptimizationResults] = useState(null);
  const [availableDates, setAvailableDates] = useState([]);
  const [selectedDate, setSelectedDate] = useState('');
  const [selectedPredictionDate, setSelectedPredictionDate] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const getSafeDbStats = () => {
    if (!databaseStatus) return { recordCount: 'N/A', dataSource: 'N/A', avgPrice: 'N/A', minPrice: 'N/A', maxPrice: 'N/A' };
    const recordCount = databaseStatus.database?.recordCount || 'N/A';
    const dataSource = databaseStatus.database?.dataSource || '未知';
    const avgPrice = databaseStatus.statistics?.price_stats?.avg;
    const minPrice = databaseStatus.statistics?.price_stats?.min;
    const maxPrice = databaseStatus.statistics?.price_stats?.max;
    return {
      recordCount,
      dataSource,
      avgPrice: avgPrice != null ? avgPrice.toFixed(2) : 'N/A',
      minPrice: minPrice != null ? minPrice.toFixed(0) : 'N/A',
      maxPrice: maxPrice != null ? maxPrice.toFixed(0) : 'N/A'
    };
  };

  const getSafeHistStats = () => {
    if (!historicalData) return { count: 'N/A', avgPrice: 'N/A' };
    return {
      count: historicalData.data?.length || 0,
      avgPrice: historicalData.statistics?.average_price?.toFixed(2) || 'N/A'
    };
  };

  const getSafePredStats = () => {
    if (!predictionResults) return { count: 'N/A', avgPrice: 'N/A', modelSource: 'N/A' };
    return {
      count: predictionResults.predictions?.length || 0,
      avgPrice: predictionResults.statistics?.average_price?.toFixed(2) || 'N/A',
      modelSource: predictionResults.model_info?.source || '未知'
    };
  };

  const getSafeOptStats = () => {
    if (!optimizationResults) return { expectedProfit: 'N/A', totalCapacity: 'N/A', avgWinProb: 'N/A', bidPrice: 'N/A' };
    const expectedProfit = optimizationResults.summary?.expected_profit;
    const totalCapacity = optimizationResults.summary?.total_capacity;
    const avgWinProb = optimizationResults.summary?.average_win_probability;
    const bidPrice = optimizationResults.optimized_bids?.[0]?.bid_price;
    return {
      expectedProfit: expectedProfit != null ? expectedProfit.toFixed(0) : 'N/A',
      totalCapacity: totalCapacity != null ? totalCapacity.toFixed(0) : 'N/A',
      avgWinProb: avgWinProb != null ? (avgWinProb * 100).toFixed(1) : 'N/A',
      bidPrice: bidPrice != null ? bidPrice.toFixed(2) : 'N/A'
    };
  };

  const fetchDatabaseStatus = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('/api/database/status');
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      setDatabaseStatus(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchAvailableDates = async () => {
    try {
      const response = await fetch('/api/available-dates');
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      setAvailableDates(data.dates || []);
      if (data.dates && data.dates.length > 0) {
        setSelectedDate(data.dates[data.dates.length - 1]);
        setSelectedPredictionDate(data.dates[data.dates.length - 1]);
      }
    } catch (err) {
      console.error('获取日期失败:', err);
    }
  };

  const fetchHistoricalData = async (date) => {
    if (!date) return;
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`/api/historical-prices?date=${date}`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      setHistoricalData(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const runPrediction = async () => {
    if (!selectedPredictionDate) {
      alert('请选择预测日期');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('/api/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ date: selectedPredictionDate, model: 'ensemble' })
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      setPredictionResults(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const runOptimization = async () => {
    if (!predictionResults?.predictions) {
      alert('请先运行预测分析');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const prices = predictionResults.predictions.map(p => p.predicted_price);
      const response = await fetch('/api/optimize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ predicted_prices: prices, max_capacity: 1000 })
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      setOptimizationResults(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchAvailableDates(); }, []);
  useEffect(() => { if (selectedDate) fetchHistoricalData(selectedDate); }, [selectedDate]);

  // 继续下一部分...
```

### 步骤3：继续添加 UI 部分

由于代码较长，请查看下一个文件 `INDEX_UI_PART.md` 获取完整的 UI 代码。

## ⚠️ 重要提示

- 确保代码完整复制，不要遗漏任何部分
- 保存文件时使用 UTF-8 编码
- 检查文件路径是否正确：`power-market-system/pages/index.js`

