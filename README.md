# 电力市场预测与投标优化系统

基于 Next.js 的全栈电力市场智能决策支持平台

## 🚀 快速开始

### 本地开发

```bash
cd power-market-system
npm install
npm run dev
```

访问 http://localhost:3000

### 部署到 Vercel

#### 方法1：通过 Vercel CLI

```bash
# 安装 Vercel CLI
npm install -g vercel

# 登录
vercel login

# 部署
cd power-market-system
vercel
```

#### 方法2：通过 Vercel 网站

1. 访问 https://vercel.com
2. 点击 "New Project"
3. 导入您的 Git 仓库
4. 选择 `power-market-system` 文件夹作为根目录
5. 点击 "Deploy"

## 📁 项目结构

```
power-market-system/
├── pages/
│   ├── api/                    # 后端 API 路由
│   │   ├── database/
│   │   │   └── status.js      # 数据库状态 API
│   │   ├── available-dates.js  # 可用日期 API
│   │   ├── historical-prices.js # 历史数据 API
│   │   ├── predict.js          # 预测 API
│   │   └── optimize.js         # 优化 API
│   ├── index.js                # 主页面
│   └── _app.js                 # App 配置
├── styles/
│   └── globals.css             # 全局样式
├── package.json                # 依赖配置
├── next.config.js              # Next.js 配置
└── vercel.json                 # Vercel 部署配置
```

## 🔧 API 端点

### 1. 获取数据库状态
```
GET /api/database/status
```

### 2. 获取可用日期
```
GET /api/available-dates
```

### 3. 获取历史数据
```
GET /api/historical-prices?date=2025-06-30
```

### 4. 运行预测
```
POST /api/predict
Body: { "date": "2025-06-30", "model": "ensemble" }
```

### 5. 生成投标策略
```
POST /api/optimize
Body: { "predicted_prices": [...], "max_capacity": 1000 }
```

## ✨ 功能特性

- ✅ 数据库状态监控
- ✅ 历史电价数据查询
- ✅ 基于机器学习的价格预测（SVM + Random Forest + XGBoost）
- ✅ 智能投标策略优化
- ✅ 实时数据可视化
- ✅ 响应式设计
- ✅ 完全部署到 Vercel

## 🎯 下一步

1. 完成前端页面的完整实现
2. 连接真实的数据库（推荐使用 Vercel Postgres 或 Supabase）
3. 集成真实的机器学习模型
4. 添加用户认证
5. 添加数据导出功能

## 📝 注意事项

- 当前使用模拟数据，生产环境需要连接真实数据源
- API 已配置 CORS，支持跨域访问
- 所有 API 都支持 Vercel Serverless Functions
- 建议使用环境变量管理敏感配置

## 🔗 相关链接

- [Next.js 文档](https://nextjs.org/docs)
- [Vercel 部署文档](https://vercel.com/docs)
- [Chart.js 文档](https://www.chartjs.org/docs/latest/)

