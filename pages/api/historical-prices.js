// API: 获取历史电价数据
export default function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }

  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { date } = req.query;

  if (!date) {
    return res.status(400).json({ 
      success: false, 
      error: 'Date parameter is required' 
    });
  }

  // 生成指定日期的96个时间点数据（每15分钟一个）
  const data = [];
  const baseDate = new Date(date);
  
  for (let i = 0; i < 96; i++) {
    const hour = Math.floor(i / 4);
    const minute = (i % 4) * 15;
    const timestamp = new Date(baseDate);
    timestamp.setHours(hour, minute, 0, 0);
    
    // 生成模拟价格数据（基于时间段的波动）
    let basePrice = 400;
    
    // 早高峰 (7-9点)
    if (hour >= 7 && hour < 9) {
      basePrice = 550 + Math.random() * 100;
    }
    // 晚高峰 (18-21点)
    else if (hour >= 18 && hour < 21) {
      basePrice = 600 + Math.random() * 150;
    }
    // 深夜低谷 (0-6点)
    else if (hour >= 0 && hour < 6) {
      basePrice = 250 + Math.random() * 50;
    }
    // 其他时段
    else {
      basePrice = 400 + Math.random() * 100;
    }
    
    data.push({
      timestamp: timestamp.toISOString(),
      price: Math.round(basePrice * 100) / 100,
      load: Math.round((800 + Math.random() * 400) * 10) / 10
    });
  }

  // 计算统计信息
  const prices = data.map(d => d.price);
  const avgPrice = prices.reduce((a, b) => a + b, 0) / prices.length;
  const minPrice = Math.min(...prices);
  const maxPrice = Math.max(...prices);

  res.status(200).json({
    success: true,
    date: date,
    data: data,
    statistics: {
      count: data.length,
      average_price: Math.round(avgPrice * 100) / 100,
      min_price: Math.round(minPrice * 100) / 100,
      max_price: Math.round(maxPrice * 100) / 100
    }
  });
}

