// API: 获取可用日期列表
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

  // 生成 2025年5月1日 到 6月30日 的日期列表
  const dates = [];
  const startDate = new Date('2025-05-01');
  const endDate = new Date('2025-06-30');
  
  for (let d = new Date(startDate); d <= endDate; d.setDate(d.getDate() + 1)) {
    dates.push(d.toISOString().split('T')[0]);
  }

  res.status(200).json({
    success: true,
    dates: dates,
    count: dates.length,
    range: {
      start: '2025-05-01',
      end: '2025-06-30'
    }
  });
}

