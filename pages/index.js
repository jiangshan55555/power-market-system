import { useState, useEffect } from 'react';
import Head from 'next/head';

export default function PowerMarketDashboard() {
  // 状态管理
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

  // 侧边栏状态
  const [operationLogs, setOperationLogs] = useState([]);
  const [currentPrice, setCurrentPrice] = useState(450.25);
  const [priceTrend, setPriceTrend] = useState({ value: 2.3, direction: 'up' });

  // 安全获取数据库统计信息
  const getSafeDbStats = () => {
    if (!databaseStatus) return { recordCount: 'N/A', dataSource: 'N/A', avgPrice: 'N/A', minPrice: 'N/A', maxPrice: 'N/A' };
    
    const recordCount = 
      databaseStatus.database?.recordCount || 
      databaseStatus.database?.record_count ||
      databaseStatus.recordCount ||
      databaseStatus.count ||
      'N/A';
    
    const dataSource = 
      databaseStatus.database?.dataSource || 
      databaseStatus.database?.data_source ||
      databaseStatus.dataSource ||
      databaseStatus.source ||
      '未知';
    
    const avgPrice = 
      databaseStatus.statistics?.price_stats?.avg ||
      databaseStatus.statistics?.average_price ||
      databaseStatus.statistics?.avg_price ||
      databaseStatus.avgPrice ||
      databaseStatus.average_price;
    
    const minPrice = 
      databaseStatus.statistics?.price_stats?.min ||
      databaseStatus.statistics?.min_price ||
      databaseStatus.minPrice ||
      databaseStatus.min_price;
    
    const maxPrice = 
      databaseStatus.statistics?.price_stats?.max ||
      databaseStatus.statistics?.max_price ||
      databaseStatus.maxPrice ||
      databaseStatus.max_price;
    
    return {
      recordCount,
      dataSource,
      avgPrice: avgPrice !== null && avgPrice !== undefined ? avgPrice.toFixed(2) : 'N/A',
      minPrice: minPrice !== null && minPrice !== undefined ? minPrice.toFixed(0) : 'N/A',
      maxPrice: maxPrice !== null && maxPrice !== undefined ? maxPrice.toFixed(0) : 'N/A'
    };
  };

  // 安全获取历史数据统计信息
  const getSafeHistStats = () => {
    if (!historicalData) return { count: 'N/A', avgPrice: 'N/A', minPrice: 'N/A', maxPrice: 'N/A' };
    
    const count = historicalData.data?.length || historicalData.statistics?.count || 0;
    const avgPrice = historicalData.statistics?.average_price || historicalData.statistics?.avg_price;
    const minPrice = historicalData.statistics?.min_price || historicalData.statistics?.minPrice;
    const maxPrice = historicalData.statistics?.max_price || historicalData.statistics?.maxPrice;
    
    return {
      count,
      avgPrice: avgPrice !== null && avgPrice !== undefined ? avgPrice.toFixed(2) : 'N/A',
      minPrice: minPrice !== null && minPrice !== undefined ? minPrice.toFixed(2) : 'N/A',
      maxPrice: maxPrice !== null && maxPrice !== undefined ? maxPrice.toFixed(2) : 'N/A'
    };
  };

  // 安全获取预测结果统计信息
  const getSafePredStats = () => {
    if (!predictionResults) return { count: 'N/A', avgPrice: 'N/A', modelSource: 'N/A' };
    
    const count = predictionResults.predictions?.length || 0;
    const avgPrice = predictionResults.statistics?.average_price || predictionResults.statistics?.avg_price;
    const modelSource = predictionResults.model_info?.source || predictionResults.modelInfo?.source || '未知';
    
    return {
      count,
      avgPrice: avgPrice !== null && avgPrice !== undefined ? avgPrice.toFixed(2) : 'N/A',
      modelSource
    };
  };

  // 安全获取优化结果统计信息
  const getSafeOptStats = () => {
    if (!optimizationResults) return { expectedProfit: 'N/A', totalCapacity: 'N/A', avgWinProb: 'N/A', bidPrice: 'N/A' };
    
    const expectedProfit = optimizationResults.summary?.expected_profit || optimizationResults.summary?.expectedProfit;
    const totalCapacity = optimizationResults.summary?.total_capacity || optimizationResults.summary?.totalCapacity;
    const avgWinProb = optimizationResults.summary?.average_win_probability || optimizationResults.summary?.averageWinProbability;
    const bidPrice = optimizationResults.optimized_bids?.[0]?.bid_price || optimizationResults.optimized_bids?.[0]?.bidPrice;
    
    return {
      expectedProfit: expectedProfit !== null && expectedProfit !== undefined ? expectedProfit.toFixed(0) : 'N/A',
      totalCapacity: totalCapacity !== null && totalCapacity !== undefined ? totalCapacity.toFixed(0) : 'N/A',
      avgWinProb: avgWinProb !== null && avgWinProb !== undefined ? (avgWinProb * 100).toFixed(1) : 'N/A',
      bidPrice: bidPrice !== null && bidPrice !== undefined ? bidPrice.toFixed(2) : 'N/A'
    };
  };

  // API 调用函数
  const fetchDatabaseStatus = async () => {
    setLoading(true);
    setError(null);
    addLog('获取数据库状态');
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

  // 添加操作日志
  const addLog = (action) => {
    const now = new Date();
    const timeStr = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`;
    const newLog = {
      time: timeStr,
      action: action,
      id: Date.now()
    };
    setOperationLogs(prev => [newLog, ...prev].slice(0, 5)); // 只保留最近5条
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
      console.error('Failed to fetch dates:', err);
    }
  };

  const fetchHistoricalData = async (date) => {
    setLoading(true);
    setError(null);
    addLog(`查询历史数据: ${date}`);
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
    addLog(`运行预测分析: ${selectedPredictionDate}`);
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
    addLog('生成投标策略');
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

  // 生命周期
  useEffect(() => { fetchAvailableDates(); }, []);
  useEffect(() => { if (selectedDate) fetchHistoricalData(selectedDate); }, [selectedDate]);

  const dbStats = getSafeDbStats();
  const histStats = getSafeHistStats();
  const predStats = getSafePredStats();
  const optStats = getSafeOptStats();

  return (
    <>
      <Head>
        <title>电力市场预测与投标优化系统</title>
        <meta name="description" content="基于机器学习的电力市场智能决策支持平台" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="preconnect" href="https://fonts.googleapis.com" />
      </Head>

      <div className="dashboard-container">
        {/* 头部 */}
        <header className="dashboard-header" role="banner">
          <h1>⚡ 电力市场预测与投标优化系统</h1>
        </header>

        {/* 标签导航 */}
        <nav className="tab-navigation" role="navigation" aria-label="主导航">
          <button
            className={`tab-button ${activeTab === 'database' ? 'active' : ''}`}
            onClick={() => setActiveTab('database')}
            role="tab"
            aria-selected={activeTab === 'database'}
            aria-controls="database-panel"
          >
            📊 数据库状态
          </button>
          <button
            className={`tab-button ${activeTab === 'historical' ? 'active' : ''}`}
            onClick={() => setActiveTab('historical')}
            role="tab"
            aria-selected={activeTab === 'historical'}
            aria-controls="historical-panel"
          >
            📈 历史数据
          </button>
          <button
            className={`tab-button ${activeTab === 'prediction' ? 'active' : ''}`}
            onClick={() => setActiveTab('prediction')}
            role="tab"
            aria-selected={activeTab === 'prediction'}
            aria-controls="prediction-panel"
          >
            🔮 预测分析
          </button>
          <button
            className={`tab-button ${activeTab === 'optimization' ? 'active' : ''}`}
            onClick={() => setActiveTab('optimization')}
            role="tab"
            aria-selected={activeTab === 'optimization'}
            aria-controls="optimization-panel"
          >
            🎯 投标优化
          </button>
        </nav>

        {/* 主布局：左侧主内容 + 右侧边栏 */}
        <div className="main-layout">
          {/* 主内容区域 */}
          <main className="main-content tab-content" role="main">
          {/* 进度条 */}
          {loading && <div className="progress-bar" role="progressbar" aria-label="加载中"></div>}

          {/* 错误提示 */}
          {error && (
            <div className="error-message" role="alert" aria-live="assertive">
              <span aria-hidden="true">❌</span>
              <span>错误: {error}</span>
            </div>
          )}

          {/* 加载提示 */}
          {loading && (
            <div className="loading-message" role="status" aria-live="polite">
              <span aria-hidden="true">⏳</span> 加载中...
            </div>
          )}

          {/* 数据库状态页面 */}
          {activeTab === 'database' && (
            <section className="tab-panel" id="database-panel" role="tabpanel" aria-labelledby="database-tab">
              <h2>数据库状态监控</h2>
              <button
                className="action-button"
                onClick={fetchDatabaseStatus}
                disabled={loading}
                aria-label="获取数据库状态"
              >
                获取数据库状态
              </button>

              {databaseStatus && (
                <div className="results-container fade-in">
                  <div className="metrics-grid">
                    <div className="metric-card metric-primary">
                      <div className="metric-icon">📊</div>
                      <div className="metric-content">
                        <span className="metric-label">记录数</span>
                        <span className="metric-value">{dbStats.recordCount}</span>
                      </div>
                    </div>
                    <div className="metric-card metric-success">
                      <div className="metric-icon">💰</div>
                      <div className="metric-content">
                        <span className="metric-label">平均电价</span>
                        <span className="metric-value">
                          {dbStats.avgPrice !== 'N/A' ? `${dbStats.avgPrice}` : 'N/A'}
                        </span>
                        {dbStats.avgPrice !== 'N/A' && <span className="metric-unit">元/MWh</span>}
                      </div>
                    </div>
                    <div className="metric-card metric-info">
                      <div className="metric-icon">📉</div>
                      <div className="metric-content">
                        <span className="metric-label">最低电价</span>
                        <span className="metric-value">
                          {dbStats.minPrice !== 'N/A' ? `${dbStats.minPrice}` : 'N/A'}
                        </span>
                        {dbStats.minPrice !== 'N/A' && <span className="metric-unit">元/MWh</span>}
                      </div>
                    </div>
                    <div className="metric-card metric-warning">
                      <div className="metric-icon">📈</div>
                      <div className="metric-content">
                        <span className="metric-label">最高电价</span>
                        <span className="metric-value">
                          {dbStats.maxPrice !== 'N/A' ? `${dbStats.maxPrice}` : 'N/A'}
                        </span>
                        {dbStats.maxPrice !== 'N/A' && <span className="metric-unit">元/MWh</span>}
                      </div>
                    </div>
                    <div className="metric-card metric-secondary">
                      <div className="metric-icon">🗄️</div>
                      <div className="metric-content">
                        <span className="metric-label">数据来源</span>
                        <span className="metric-value metric-value-small">{dbStats.dataSource}</span>
                      </div>
                    </div>
                    <div className="metric-card metric-dark">
                      <div className="metric-icon">🕐</div>
                      <div className="metric-content">
                        <span className="metric-label">最后更新</span>
                        <span className="metric-value metric-value-small">
                          {databaseStatus.database?.lastUpdate || 'N/A'}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </section>
          )}

          {/* 历史数据页面 */}
          {activeTab === 'historical' && (
            <section className="tab-panel" id="historical-panel" role="tabpanel" aria-labelledby="historical-tab">
              <h2>历史电价数据查询</h2>
              <div className="form-group">
                <label htmlFor="historical-date-select">选择日期：</label>
                <select
                  id="historical-date-select"
                  value={selectedDate}
                  onChange={(e) => setSelectedDate(e.target.value)}
                  disabled={loading}
                  aria-label="选择历史数据日期"
                >
                  <option value="">请选择日期</option>
                  {availableDates.map(date => (
                    <option key={date} value={date}>{date}</option>
                  ))}
                </select>
              </div>

              {historicalData && (
                <div className="results-container fade-in">
                  <div className="metrics-grid metrics-grid-4">
                    <div className="metric-card metric-primary">
                      <div className="metric-icon">📍</div>
                      <div className="metric-content">
                        <span className="metric-label">数据点数</span>
                        <span className="metric-value">{histStats.count}</span>
                        <span className="metric-unit">个时间点</span>
                      </div>
                    </div>
                    <div className="metric-card metric-success">
                      <div className="metric-icon">📊</div>
                      <div className="metric-content">
                        <span className="metric-label">平均价格</span>
                        <span className="metric-value">
                          {histStats.avgPrice !== 'N/A' ? `${histStats.avgPrice}` : 'N/A'}
                        </span>
                        {histStats.avgPrice !== 'N/A' && <span className="metric-unit">元/MWh</span>}
                      </div>
                    </div>
                    <div className="metric-card metric-info">
                      <div className="metric-icon">⬇️</div>
                      <div className="metric-content">
                        <span className="metric-label">最低价格</span>
                        <span className="metric-value">
                          {histStats.minPrice !== 'N/A' ? `${histStats.minPrice}` : 'N/A'}
                        </span>
                        {histStats.minPrice !== 'N/A' && <span className="metric-unit">元/MWh</span>}
                      </div>
                    </div>
                    <div className="metric-card metric-warning">
                      <div className="metric-icon">⬆️</div>
                      <div className="metric-content">
                        <span className="metric-label">最高价格</span>
                        <span className="metric-value">
                          {histStats.maxPrice !== 'N/A' ? `${histStats.maxPrice}` : 'N/A'}
                        </span>
                        {histStats.maxPrice !== 'N/A' && <span className="metric-unit">元/MWh</span>}
                      </div>
                    </div>
                  </div>

                  <div className="data-table-container">
                    <h3>详细数据（前10条）</h3>
                    <table className="data-table">
                      <thead>
                        <tr>
                          <th>时间</th>
                          <th>电价 (元/MWh)</th>
                          <th>负荷 (MW)</th>
                        </tr>
                      </thead>
                      <tbody>
                        {historicalData.data?.slice(0, 10).map((item, index) => (
                          <tr key={index}>
                            <td>{item.timestamp}</td>
                            <td>{item.price.toFixed(2)}</td>
                            <td>{item.load.toFixed(0)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </section>
          )}

          {/* 预测分析页面 */}
          {activeTab === 'prediction' && (
            <section className="tab-panel" id="prediction-panel" role="tabpanel" aria-labelledby="prediction-tab">
              <h2>电价预测分析</h2>
              <div className="form-group">
                <label htmlFor="prediction-date-select">选择预测日期：</label>
                <select
                  id="prediction-date-select"
                  value={selectedPredictionDate}
                  onChange={(e) => setSelectedPredictionDate(e.target.value)}
                  disabled={loading}
                  aria-label="选择预测日期"
                >
                  <option value="">请选择日期</option>
                  {availableDates.map(date => (
                    <option key={date} value={date}>{date}</option>
                  ))}
                </select>
              </div>
              <button
                className="action-button"
                onClick={runPrediction}
                disabled={loading || !selectedPredictionDate}
                aria-label="运行电价预测分析"
              >
                运行预测分析
              </button>

              {predictionResults && (
                <div className="results-container fade-in">
                  <div className="metrics-grid metrics-grid-4">
                    <div className="metric-card metric-primary">
                      <div className="metric-icon">📊</div>
                      <div className="metric-content">
                        <span className="metric-label">预测数据点</span>
                        <span className="metric-value">{predStats.count}</span>
                        <span className="metric-unit">个时间点</span>
                      </div>
                    </div>
                    <div className="metric-card metric-success">
                      <div className="metric-icon">💹</div>
                      <div className="metric-content">
                        <span className="metric-label">平均预测价格</span>
                        <span className="metric-value">
                          {predStats.avgPrice !== 'N/A' ? `${predStats.avgPrice}` : 'N/A'}
                        </span>
                        {predStats.avgPrice !== 'N/A' && <span className="metric-unit">元/MWh</span>}
                      </div>
                    </div>
                  </div>

                  <div className="data-table-container">
                    <h3>预测结果（前10条）</h3>
                    <table className="data-table">
                      <thead>
                        <tr>
                          <th>时间</th>
                          <th>预测价格 (元/MWh)</th>
                          <th>置信度</th>
                        </tr>
                      </thead>
                      <tbody>
                        {predictionResults.predictions?.slice(0, 10).map((item, index) => (
                          <tr key={index}>
                            <td>{item.timestamp}</td>
                            <td>{item.predicted_price.toFixed(2)}</td>
                            <td>{(item.confidence * 100).toFixed(1)}%</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </section>
          )}

          {/* 投标优化页面 */}
          {activeTab === 'optimization' && (
            <section className="tab-panel" id="optimization-panel" role="tabpanel" aria-labelledby="optimization-tab">
              <h2>投标策略优化</h2>
              <p className="info-text">
                基于预测结果生成最优投标策略
              </p>
              <button
                className="action-button"
                onClick={runOptimization}
                disabled={loading || !predictionResults}
                aria-label="生成投标策略"
              >
                生成投标策略
              </button>

              {optimizationResults && (
                <div className="results-container fade-in">
                  <div className="metrics-grid metrics-grid-4">
                    <div className="metric-card metric-warning">
                      <div className="metric-icon">💰</div>
                      <div className="metric-content">
                        <span className="metric-label">预期收益</span>
                        <span className="metric-value">
                          {optStats.expectedProfit !== 'N/A' ? `¥${optStats.expectedProfit}` : 'N/A'}
                        </span>
                      </div>
                    </div>
                    <div className="metric-card metric-primary">
                      <div className="metric-icon">⚡</div>
                      <div className="metric-content">
                        <span className="metric-label">建议投标量</span>
                        <span className="metric-value">
                          {optStats.totalCapacity !== 'N/A' ? `${optStats.totalCapacity}` : 'N/A'}
                        </span>
                        {optStats.totalCapacity !== 'N/A' && <span className="metric-unit">MW</span>}
                      </div>
                    </div>
                    <div className="metric-card metric-success">
                      <div className="metric-icon">🎯</div>
                      <div className="metric-content">
                        <span className="metric-label">平均成功概率</span>
                        <span className="metric-value">
                          {optStats.avgWinProb !== 'N/A' ? `${optStats.avgWinProb}` : 'N/A'}
                        </span>
                        {optStats.avgWinProb !== 'N/A' && <span className="metric-unit">%</span>}
                      </div>
                    </div>
                    <div className="metric-card metric-info">
                      <div className="metric-icon">💵</div>
                      <div className="metric-content">
                        <span className="metric-label">建议价格</span>
                        <span className="metric-value">
                          {optStats.bidPrice !== 'N/A' ? `${optStats.bidPrice}` : 'N/A'}
                        </span>
                        {optStats.bidPrice !== 'N/A' && <span className="metric-unit">元/MWh</span>}
                      </div>
                    </div>
                  </div>

                  <div className="data-table-container">
                    <h3>优化投标策略（前10条）</h3>
                    <table className="data-table">
                      <thead>
                        <tr>
                          <th>时间段</th>
                          <th>投标价格 (元/MWh)</th>
                          <th>投标量 (MW)</th>
                          <th>成功概率</th>
                          <th>预期收益 (元)</th>
                        </tr>
                      </thead>
                      <tbody>
                        {optimizationResults.optimized_bids?.slice(0, 10).map((bid, index) => (
                          <tr key={index}>
                            <td>{bid.time_period}</td>
                            <td>{bid.bid_price.toFixed(2)}</td>
                            <td>{bid.bid_quantity.toFixed(0)}</td>
                            <td>{(bid.win_probability * 100).toFixed(1)}%</td>
                            <td>¥{bid.expected_profit.toFixed(0)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </section>
          )}
          </main>

          {/* 右侧边栏 */}
          <aside className="sidebar-right" role="complementary" aria-label="辅助信息">
            {/* 实时监控卡片 */}
            <div className="sidebar-card realtime-monitor">
              <div className="sidebar-card-title">
                <span className="icon">⚡</span>
                实时电价监控
              </div>
              <div className="sidebar-card-content">
                <div className="realtime-price">¥{currentPrice.toFixed(2)}</div>
                <div className={`realtime-trend ${priceTrend.direction}`}>
                  {priceTrend.direction === 'up' ? '↑' : '↓'} {priceTrend.value}%
                </div>
                <div style={{ marginTop: '12px', fontSize: '0.8rem', color: 'var(--color-text-tertiary)' }}>
                  更新时间: {new Date().toLocaleTimeString('zh-CN')}
                </div>
              </div>
            </div>

            {/* 数据统计卡片 */}
            <div className="sidebar-card">
              <div className="sidebar-card-title">
                <span className="icon">📊</span>
                数据统计
              </div>
              <div className="sidebar-card-content">
                <div className="stat-item">
                  <span className="stat-label">数据库记录</span>
                  <span className="stat-value">{getSafeDbStats().recordCount}</span>
                </div>
                <div className="stat-item">
                  <span className="stat-label">本周均价</span>
                  <span className="stat-value">¥{getSafeDbStats().avgPrice}</span>
                </div>
                <div className="stat-item">
                  <span className="stat-label">最高电价</span>
                  <span className="stat-value">¥{getSafeDbStats().maxPrice}</span>
                </div>
                <div className="stat-item">
                  <span className="stat-label">最低电价</span>
                  <span className="stat-value">¥{getSafeDbStats().minPrice}</span>
                </div>
                <div className="stat-item">
                  <span className="stat-label">预测准确率</span>
                  <span className="stat-value">
                    {predictionResults?.model_info?.accuracy
                      ? `${(predictionResults.model_info.accuracy * 100).toFixed(1)}%`
                      : 'N/A'}
                  </span>
                </div>
              </div>
            </div>

            {/* 操作日志卡片 */}
            <div className="sidebar-card">
              <div className="sidebar-card-title">
                <span className="icon">📝</span>
                操作日志
              </div>
              <div className="sidebar-card-content">
                {operationLogs.length === 0 ? (
                  <div style={{ color: 'var(--color-text-tertiary)', fontSize: '0.85rem', textAlign: 'center', padding: '12px 0' }}>
                    暂无操作记录
                  </div>
                ) : (
                  operationLogs.map(log => (
                    <div key={log.id} className="log-item">
                      <div className="log-time">{log.time}</div>
                      <div className="log-action">{log.action}</div>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* 帮助提示卡片 */}
            <div className="sidebar-card">
              <div className="sidebar-card-title">
                <span className="icon">💡</span>
                使用提示
              </div>
              <div className="sidebar-card-content">
                <div className="help-tip">
                  {activeTab === 'database' && '点击"获取数据库状态"查看系统数据概况'}
                  {activeTab === 'historical' && '选择日期后可查看该日的96个时间点电价数据'}
                  {activeTab === 'prediction' && '基于历史数据使用机器学习模型预测未来电价'}
                  {activeTab === 'optimization' && '根据预测结果生成最优投标策略，最大化收益'}
                </div>
              </div>
            </div>
          </aside>
        </div>

        {/* 页脚 */}
        <footer className="dashboard-footer" role="contentinfo">
          <p>© 2025 电力市场预测与投标优化系统 | 基于 Next.js + Vercel 部署</p>
        </footer>
      </div>
    </>
  );
}
