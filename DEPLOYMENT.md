# 电力市场预测系统 - Vercel 部署指南

## 📦 项目结构

```
power-prediction-system/
├── api/                          # Flask API 后端
│   ├── app.py                   # 主应用入口
│   ├── run_original_prediction.py  # 预测模块
│   ├── run_bidding_optimization.py # 投标优化模块
│   └── requirements.txt         # Python 依赖
├── src/                         # 核心算法模块
│   ├── predictions/             # 预测模型
│   ├── optimization/            # 优化算法
│   └── utils/                   # 工具函数
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
└── README.md                    # 项目说明
```

## 🚀 Vercel 部署步骤

### 1. 准备工作

确保你已经：
- 安装了 Git
- 有 GitHub 账号
- 有 Vercel 账号（可以用 GitHub 登录）

### 2. 推送到 GitHub

```bash
cd power-prediction-system
git init
git add .
git commit -m "Initial commit: 电力市场预测系统"
git branch -M main
git remote add origin <你的GitHub仓库地址>
git push -u origin main
```

### 3. 在 Vercel 上部署

1. 访问 https://vercel.com
2. 点击 "Import Project"
3. 选择你的 GitHub 仓库
4. Vercel 会自动检测到 `vercel.json` 配置
5. 点击 "Deploy"

### 4. 环境变量配置（可选）

在 Vercel 项目设置中添加环境变量：
- `FLASK_ENV`: production
- `PYTHONPATH`: /var/task

## ⚠️ 注意事项

### Vercel 限制

1. **无服务器函数超时限制**：
   - 免费版：10秒
   - Pro版：60秒
   - 预测和优化可能需要较长时间，建议升级到 Pro 版本

2. **文件大小限制**：
   - 单个文件最大 50MB
   - 总部署大小最大 100MB（免费版）

3. **内存限制**：
   - 免费版：1024MB
   - Pro版：3008MB

### 替代方案

如果 Vercel 限制太多，可以考虑：

1. **Railway.app**：
   - 支持长时间运行的进程
   - 更适合机器学习应用
   - 有免费额度

2. **Render.com**：
   - 支持 Docker 部署
   - 无超时限制
   - 有免费层级

3. **Heroku**：
   - 传统 PaaS 平台
   - 支持后台任务
   - 需要付费

## 🔧 本地测试

部署前先在本地测试：

```bash
# 安装依赖
pip install -r requirements.txt

# 运行服务器
python api/app.py

# 访问
http://localhost:5000
```

## 📝 部署检查清单

- [x] 所有源代码文件已复制
- [x] 配置文件已复制（config.json）
- [x] 数据文件已复制（rawdata_*.xlsx）
- [x] 依赖文件已创建（requirements.txt）
- [x] Vercel 配置已创建（vercel.json）
- [x] .gitignore 已创建
- [x] README.md 已更新
- [ ] 测试所有功能正常
- [ ] 推送到 GitHub
- [ ] 在 Vercel 上部署

## 🐛 常见问题

### 1. 部署后 API 超时

**原因**：预测和优化计算时间过长
**解决**：
- 升级到 Vercel Pro
- 或使用 Railway/Render 等平台

### 2. 文件上传失败

**原因**：Vercel 无服务器函数不支持持久化存储
**解决**：
- 使用云存储（S3, Cloudinary）
- 或使用有状态的托管平台

### 3. 模块导入错误

**原因**：Python 路径配置问题
**解决**：
- 检查 `sys.path` 设置
- 确保所有模块都在正确的目录

## 📞 支持

如有问题，请查看：
- Vercel 文档：https://vercel.com/docs
- Flask 文档：https://flask.palletsprojects.com/

