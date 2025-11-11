from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
import pandas as pd
import numpy as np
from datetime import datetime
import os
import json
import sys
from pathlib import Path
from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVR
from sklearn.ensemble import RandomForestRegressor, VotingRegressor
from xgboost import XGBRegressor
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import warnings
warnings.filterwarnings('ignore')

# 自定义 JSON 编码器，处理 NaN 和 Infinity
class SafeJSONEncoder(json.JSONEncoder):
    def encode(self, o):
        if isinstance(o, float):
            if np.isnan(o) or np.isinf(o):
                return 'null'
        return super().encode(o)

    def iterencode(self, o, _one_shot=False):
        """Encode the given object and yield each string representation as available."""
        for chunk in super().iterencode(o, _one_shot):
            # Replace NaN and Infinity with null in the JSON string
            chunk = chunk.replace('NaN', 'null').replace('Infinity', 'null').replace('-Infinity', 'null')
            yield chunk

# 导入特征工程模块
from feature_engineering import create_all_features
from predict_all_models import run_all_models
from run_original_prediction import run_original_prediction
from run_bidding_optimization import run_bidding_optimization

# 添加原来项目的路径以导入模型类
ORIGINAL_PROJECT_PATH = Path(__file__).parent.parent.parent / 'power-market-system' / '原来的项目资料'
sys.path.insert(0, str(ORIGINAL_PROJECT_PATH))

try:
    from src.predictions.random_forest_model import RandomForestModel
    from src.predictions.xgboost_model import XGBoostModel
    from src.predictions.gradient_boosting_model import GradientBoostingModel
    from src.predictions.ensemble_model import EnsembleModel
    USE_ORIGINAL_MODELS = True
    print("✅ 成功导入原项目的模型类")
    print("   - RandomForestModel")
    print("   - XGBoostModel")
    print("   - GradientBoostingModel")
    print("   - EnsembleModel")
except ImportError as e:
    print(f"⚠️ 无法导入原项目模型类: {e}")
    print("将使用简化版本的模型")
    USE_ORIGINAL_MODELS = False

app = Flask(__name__)
CORS(app)

# 配置 Flask 使用自定义 JSON 编码器
app.json_encoder = SafeJSONEncoder
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 全局变量存储数据和模型
current_data = None
trained_models = None
scaler = None
feature_columns = None

@app.route('/')
def index():
    """提供前端页面"""
    return send_from_directory('..', 'index.html')

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'message': '电力市场预测系统运行正常',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/upload', methods=['POST'])
def upload_file():
    global current_data

    try:
        if 'file' not in request.files:
            return jsonify({'error': '没有文件上传'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '文件名为空'}), 400

        # 保存文件
        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)

        print(f"✅ 文件已保存到: {filepath}")

        # 读取数据（使用双层表头）
        if file.filename.endswith('.xlsx') or file.filename.endswith('.xls'):
            # 尝试读取双层表头
            try:
                current_data = pd.read_excel(filepath, header=[0, 1])
                print(f"✅ 使用双层表头读取数据")

                # 处理多层表头，合并为单层
                new_columns = []
                for col in current_data.columns.values:
                    feature_name = str(col[0]).strip()
                    # 对于时间列，只保留第一层的列名
                    if feature_name in ['时间', '日期', '时刻']:
                        new_columns.append(feature_name)
                    else:
                        # 对于其他列，如果第二层有值且不是数字，则合并
                        if pd.notna(col[1]) and not isinstance(col[1], (int, float)):
                            second_part = str(col[1]).strip()
                            if second_part and second_part != feature_name:
                                feature_name = f"{feature_name}_{second_part}"
                        new_columns.append(feature_name)
                current_data.columns = new_columns
                print(f"   合并后的列名: {current_data.columns.tolist()[:10]}...")
            except:
                # 如果双层表头失败，尝试单层表头
                print(f"   双层表头读取失败，尝试单层表头")
                current_data = pd.read_excel(filepath)
        elif file.filename.endswith('.csv'):
            current_data = pd.read_csv(filepath)
        else:
            return jsonify({'error': '不支持的文件格式，请上传 Excel 或 CSV 文件'}), 400

        print(f"✅ 数据读取成功，形状: {current_data.shape}")
        print(f"   前10列: {current_data.columns.tolist()[:10]}")

        # 自动识别并解析时间列
        time_column = None
        for col in current_data.columns:
            col_lower = str(col).lower()
            # 优先查找"时间"列（而不是"日期"或"时刻"）
            if col_lower == '时间' or col_lower == 'datetime':
                time_column = col
                break

        # 如果没找到"时间"列，再查找其他可能的时间列（但排除"日期"列）
        if not time_column:
            for col in current_data.columns:
                col_lower = str(col).lower()
                # 排除"日期"和"时刻"列，只查找包含 time 或 date 的列
                if any(keyword in col_lower for keyword in ['time', 'date']) and '日期' not in col_lower and '时刻' not in col_lower:
                    time_column = col
                    break

        if time_column:
            print(f"   找到时间列: {time_column}")
            print(f"   时间列数据类型: {current_data[time_column].dtype}")
            print(f"   时间列示例值: {current_data[time_column].head(3).tolist()}")

            # 解析时间列
            try:
                # 如果是字符串类型，尝试解析
                if current_data[time_column].dtype == 'object':
                    # 先修复24:00的问题（24:00应该是次日00:00）
                    def fix_24_hour(time_str):
                        if pd.isna(time_str):
                            return time_str
                        time_str = str(time_str).strip()
                        # 检查是否包含24:00
                        if ' 24:00' in time_str:
                            # 将24:00替换为00:00，并将日期加1天
                            date_part, time_part = time_str.split(' ')
                            date_obj = pd.to_datetime(date_part)
                            next_day = date_obj + pd.Timedelta(days=1)
                            return next_day.strftime('%Y-%m-%d') + ' 00:00'
                        return time_str

                    print(f"   修复24:00时间格式...")
                    current_data[time_column] = current_data[time_column].apply(fix_24_hour)
                    current_data[time_column] = pd.to_datetime(current_data[time_column], format='%Y-%m-%d %H:%M', errors='coerce')
                elif not pd.api.types.is_datetime64_any_dtype(current_data[time_column]):
                    current_data[time_column] = pd.to_datetime(current_data[time_column], errors='coerce')

                print(f"   ✅ 时间列已解析为 datetime 类型")
                print(f"   时间范围: {current_data[time_column].min()} 到 {current_data[time_column].max()}")
            except Exception as e:
                print(f"   ⚠️ 时间列解析失败: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"   ⚠️ 未找到时间列")

        # 转换数据预览为 JSON 可序列化格式
        preview_data = current_data.head(20).copy()

        # 将所有 numpy/pandas 类型转换为 Python 原生类型
        preview_dict = []
        for _, row in preview_data.iterrows():
            row_dict = {}
            for col in preview_data.columns:
                val = row[col]
                # 转换为 Python 原生类型
                if pd.isna(val):
                    row_dict[col] = None
                elif isinstance(val, (np.integer, np.int64, np.int32)):
                    row_dict[col] = int(val)
                elif isinstance(val, (np.floating, np.float64, np.float32)):
                    row_dict[col] = float(val)
                elif isinstance(val, (pd.Timestamp, np.datetime64)):
                    row_dict[col] = str(val)
                else:
                    row_dict[col] = str(val)
            preview_dict.append(row_dict)

        # 数据基本信息
        info = {
            'filename': file.filename,
            'rows': int(len(current_data)),
            'columns': int(len(current_data.columns)),
            'column_names': [str(col) for col in current_data.columns.tolist()],
            'preview': preview_dict,
            'upload_time': datetime.now().isoformat()
        }

        print("数据信息准备完成，准备返回...")

        return jsonify({
            'message': '文件上传成功',
            'data': info
        })

    except Exception as e:
        import traceback
        error_msg = f'上传失败: {str(e)}'
        print(error_msg)
        print(traceback.format_exc())
        return jsonify({'error': error_msg}), 500

@app.route('/api/available-dates', methods=['GET'])
def get_available_dates():
    """获取数据中所有可用的日期列表"""
    global current_data

    try:
        if current_data is None:
            return jsonify({'error': '请先上传数据文件'}), 400

        # 找到时间列（优先查找"时间"列）
        time_column = None
        for col in current_data.columns:
            col_lower = str(col).lower()
            if col_lower == '时间' or col_lower == 'datetime':
                time_column = col
                break

        # 如果没找到"时间"列，再查找其他可能的时间列
        if not time_column:
            for col in current_data.columns:
                col_lower = str(col).lower()
                if any(keyword in col_lower for keyword in ['time', 'date']):
                    time_column = col
                    break

        if time_column is None:
            return jsonify({'error': '数据中未找到时间列'}), 400

        print(f"📅 获取可用日期列表...")
        print(f"   使用时间列: {time_column}")
        print(f"   时间列数据类型: {current_data[time_column].dtype}")
        print(f"   时间列示例值: {current_data[time_column].head(3).tolist()}")

        # 确保时间列是datetime类型
        if not pd.api.types.is_datetime64_any_dtype(current_data[time_column]):
            print(f"   ⚠️ 时间列不是 datetime 类型，尝试转换...")
            try:
                # 尝试使用指定格式解析
                current_data[time_column] = pd.to_datetime(current_data[time_column], format='%Y-%m-%d %H:%M', errors='coerce')
                print(f"   ✅ 时间列已转换为 datetime 类型")
            except Exception as e:
                print(f"   ❌ 时间列转换失败: {e}")
                return jsonify({'error': f'时间列转换失败: {str(e)}'}), 400

        # 获取所有唯一的日期（排除 NaT）
        valid_times = current_data[time_column].dropna()
        unique_dates = valid_times.dt.date.unique()
        unique_dates = sorted(unique_dates, reverse=True)  # 降序排列，最新的在前

        print(f"   ✅ 找到 {len(unique_dates)} 个唯一日期")
        if len(unique_dates) > 0:
            print(f"   日期范围: {unique_dates[-1]} 到 {unique_dates[0]}")

        # 转换为字符串列表
        date_list = [str(date) for date in unique_dates]

        return jsonify({
            'dates': date_list,
            'count': len(date_list)
        })

    except Exception as e:
        import traceback
        error_msg = f'获取日期列表失败: {str(e)}'
        print(error_msg)
        print(traceback.format_exc())
        return jsonify({'error': error_msg}), 500

@app.route('/api/query-price', methods=['POST'])
def query_price():
    """查询历史电价数据"""
    global current_data

    try:
        print("\n" + "="*60)
        print("📊 查询历史电价数据...")

        if current_data is None:
            return jsonify({'error': '请先上传数据文件'}), 400

        # 获取查询日期和时刻
        data = request.get_json()
        query_date = data.get('date')
        query_time = data.get('time')  # 可选参数，如果提供则查询特定时刻

        print(f"   收到查询请求:")
        print(f"   - 日期: {query_date} (类型: {type(query_date)})")
        print(f"   - 时刻: {query_time}")

        if not query_date:
            return jsonify({'error': '请提供查询日期'}), 400

        # 确保数据中有时间列
        # 优先查找 "时间" 列（包含完整的日期和时间信息）
        time_column = None

        # 第一优先级：查找 "时间" 列
        for col in current_data.columns:
            if str(col).lower() == '时间' or str(col).lower() == 'datetime':
                time_column = col
                print(f"   ✅ 找到时间列: {time_column}")
                break

        # 第二优先级：如果没找到 "时间" 列，再查找其他包含 time 或 date 的列（但排除 "日期" 和 "时刻"）
        if not time_column:
            for col in current_data.columns:
                col_lower = str(col).lower()
                if any(keyword in col_lower for keyword in ['time', 'date']) and '日期' not in col_lower and '时刻' not in col_lower:
                    time_column = col
                    print(f"   ✅ 找到时间列: {time_column}")
                    break

        if time_column is None:
            print(f"   ❌ 未找到时间列，可用列: {current_data.columns.tolist()}")
            return jsonify({'error': '数据中未找到时间列'}), 400

        # 打印时间列的当前状态（在任何转换之前）
        print(f"   时间列 '{time_column}' 当前类型: {current_data[time_column].dtype}")
        print(f"   时间列前3个值: {current_data[time_column].head(3).tolist()}")

        # 确保时间列是datetime类型（如果已经是 datetime 类型，就不要再转换了）
        if not pd.api.types.is_datetime64_any_dtype(current_data[time_column]):
            print(f"   ⚠️  时间列不是 datetime 类型，正在转换...")
            current_data[time_column] = pd.to_datetime(current_data[time_column])
            print(f"   ✅ 时间列已转换为 datetime 类型")
            print(f"   转换后前3个值: {current_data[time_column].head(3).tolist()}")
        else:
            print(f"   ✅ 时间列已经是 datetime 类型，无需转换")

        # 找到电价列（优先使用"实时出清电价"）
        price_column = None

        # 优先查找"实时出清电价"
        if '实时出清电价' in current_data.columns:
            price_column = '实时出清电价'
            print(f"   ✅ 找到电价列: {price_column}")
        else:
            # 如果没有，再查找其他可能的电价列
            for col in current_data.columns:
                col_lower = str(col).lower()
                if any(keyword in col_lower for keyword in ['电价', 'price', '价格', '出清价']):
                    price_column = col
                    print(f"   ✅ 找到电价列: {price_column}")
                    break

        if price_column is None:
            print(f"   ❌ 未找到电价列，可用列: {current_data.columns.tolist()}")
            return jsonify({'error': '数据中未找到电价列'}), 400

        # 筛选指定日期的数据
        query_date_obj = pd.to_datetime(query_date)
        print(f"   📅 查询日期: {query_date} -> {query_date_obj.date()}")
        print(f"   时间列数据类型: {current_data[time_column].dtype}")
        print(f"   时间列示例: {current_data[time_column].head(3).tolist()}")

        filtered_data = current_data[current_data[time_column].dt.date == query_date_obj.date()].copy()

        print(f"   筛选后数据量: {len(filtered_data)}")

        if len(filtered_data) == 0:
            # 显示可用的日期范围
            available_dates = current_data[time_column].dt.date.unique()
            print(f"   ❌ 未找到数据，可用日期: {sorted(available_dates)[:5]}...")
            return jsonify({'error': f'未找到 {query_date} 的数据，请检查日期格式'}), 404

        # 如果提供了时刻，进一步筛选特定时刻的数据
        if query_time:
            query_datetime = pd.to_datetime(query_time)
            filtered_data = filtered_data[filtered_data[time_column] == query_datetime].copy()

            if len(filtered_data) == 0:
                return jsonify({'error': f'未找到 {query_time} 的数据'}), 404

        # 计算统计信息
        price_values = filtered_data[price_column].dropna()

        stats = {
            'count': int(len(price_values)),
            'max': float(price_values.max()),
            'min': float(price_values.min()),
            'mean': float(price_values.mean())
        }

        # 获取详细数据（所有数据，按时间排序）
        filtered_data = filtered_data.sort_values(by=time_column)
        detail_data = []
        for _, row in filtered_data.iterrows():
            detail_row = {
                'time': str(row[time_column]),
                'price': float(row[price_column]) if not pd.isna(row[price_column]) else None
            }

            # 如果有负荷列，也添加进去
            for col in current_data.columns:
                col_lower = str(col).lower()
                if any(keyword in col_lower for keyword in ['负荷', 'load', '功率', 'power']):
                    detail_row['load'] = float(row[col]) if not pd.isna(row[col]) else None
                    break

            detail_data.append(detail_row)

        return jsonify({
            'date': query_date,
            'stats': stats,
            'detail': detail_data,
            'columns': {
                'time': time_column,
                'price': price_column
            }
        })

    except Exception as e:
        import traceback
        error_msg = f'查询失败: {str(e)}'
        print(error_msg)
        print(traceback.format_exc())
        return jsonify({'error': error_msg}), 500

@app.route('/api/data-status', methods=['GET'])
def get_data_status():
    """获取数据状态详细信息"""
    global current_data

    try:
        if current_data is None:
            return jsonify({'error': '请先上传数据文件'}), 400

        # 基本信息
        basic_info = {
            'rows': int(len(current_data)),
            'columns': int(len(current_data.columns)),
            'memory_usage': f"{current_data.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB"
        }

        # 列信息（数据类型、缺失值、唯一值）
        column_info = []
        for col in current_data.columns:
            col_data = current_data[col]
            missing_count = int(col_data.isna().sum())
            missing_percent = float(missing_count / len(current_data) * 100)

            col_info = {
                'name': str(col),
                'dtype': str(col_data.dtype),
                'missing_count': missing_count,
                'missing_percent': round(missing_percent, 2),
                'unique_count': int(col_data.nunique()),
                'non_null_count': int(col_data.count())
            }

            # 如果是数值类型，添加统计信息
            if pd.api.types.is_numeric_dtype(col_data):
                stats = col_data.describe()
                col_info['statistics'] = {
                    'mean': float(stats['mean']) if not pd.isna(stats['mean']) else None,
                    'std': float(stats['std']) if not pd.isna(stats['std']) else None,
                    'min': float(stats['min']) if not pd.isna(stats['min']) else None,
                    'max': float(stats['max']) if not pd.isna(stats['max']) else None,
                    'median': float(col_data.median()) if not pd.isna(col_data.median()) else None
                }

            column_info.append(col_info)

        # 数据质量评分
        total_cells = len(current_data) * len(current_data.columns)
        missing_cells = current_data.isna().sum().sum()
        data_quality_score = float((total_cells - missing_cells) / total_cells * 100)

        # 数据预览（前20行）
        preview_data = current_data.head(20).copy()
        preview_dict = []
        for _, row in preview_data.iterrows():
            row_dict = {}
            for col in preview_data.columns:
                val = row[col]
                if pd.isna(val):
                    row_dict[col] = None
                elif isinstance(val, (np.integer, np.int64, np.int32)):
                    row_dict[col] = int(val)
                elif isinstance(val, (np.floating, np.float64, np.float32)):
                    row_dict[col] = float(val)
                elif isinstance(val, (pd.Timestamp, np.datetime64)):
                    row_dict[col] = str(val)
                else:
                    row_dict[col] = str(val)
            preview_dict.append(row_dict)

        result = {
            'basic_info': basic_info,
            'column_info': column_info,
            'data_quality_score': round(data_quality_score, 2),
            'preview': preview_dict
        }

        print(f"✅ 数据状态检查完成")
        print(f"   数据质量评分: {data_quality_score:.2f}%")
        print(f"   总缺失值: {int(missing_cells)} / {total_cells}")

        return jsonify(result)

    except Exception as e:
        import traceback
        error_msg = f'获取数据状态失败: {str(e)}'
        print(error_msg)
        print(traceback.format_exc())
        return jsonify({'error': error_msg}), 500

@app.route('/api/train', methods=['POST'])
def train_model():
    global current_data, trained_models, scaler, feature_columns

    try:
        if current_data is None:
            return jsonify({'error': '请先上传数据'}), 400

        params = request.json
        target_column = params.get('target_column', '电价')

        if target_column not in current_data.columns:
            return jsonify({'error': f'目标列 "{target_column}" 不存在'}), 400

        # 准备数据
        df = current_data.copy()

        # 选择数值型特征
        numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
        if target_column not in numeric_columns:
            return jsonify({'error': f'目标列 "{target_column}" 不是数值型'}), 400

        feature_columns = [col for col in numeric_columns if col != target_column]

        if len(feature_columns) == 0:
            return jsonify({'error': '没有可用的特征列'}), 400

        X = df[feature_columns].fillna(df[feature_columns].mean())
        y = df[target_column].fillna(df[target_column].mean())

        # 划分训练集和测试集
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # 标准化
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        print("=" * 60)
        print("开始训练模型（使用原项目的模型实现）...")
        print("=" * 60)

        trained_models = {}

        # 1. Random Forest 模型（使用原项目的实现）
        print("训练 Random Forest 模型...")
        if USE_ORIGINAL_MODELS:
            try:
                rf_model = RandomForestModel()
                if rf_model.train(X_train_scaled, y_train):
                    trained_models['random_forest'] = rf_model
                    print("✅ Random Forest 模型训练完成（使用原项目实现）")
                else:
                    raise Exception("原项目模型训练失败")
            except Exception as e:
                print(f"⚠️ 原项目 RF 模型失败，使用简化版本: {e}")
                import traceback
                traceback.print_exc()
                rf_model = RandomForestRegressor(n_estimators=100, random_state=42, max_depth=10)
                rf_model.fit(X_train_scaled, y_train)
                trained_models['random_forest'] = rf_model
                print("✅ Random Forest 模型训练完成（简化版本）")
        else:
            rf_model = RandomForestRegressor(n_estimators=100, random_state=42, max_depth=10)
            rf_model.fit(X_train_scaled, y_train)
            trained_models['random_forest'] = rf_model
            print("✅ Random Forest 模型训练完成")

        # 2. XGBoost 模型（使用原项目的实现）
        print("训练 XGBoost 模型...")
        if USE_ORIGINAL_MODELS:
            try:
                xgb_model = XGBoostModel()
                if xgb_model.train(X_train_scaled, y_train):
                    trained_models['xgboost'] = xgb_model
                    print("✅ XGBoost 模型训练完成（使用原项目实现）")
                else:
                    raise Exception("原项目模型训练失败")
            except Exception as e:
                print(f"⚠️ 原项目 XGBoost 模型失败，使用简化版本: {e}")
                import traceback
                traceback.print_exc()
                xgb_model = XGBRegressor(n_estimators=100, random_state=42, max_depth=6, learning_rate=0.1)
                xgb_model.fit(X_train_scaled, y_train)
                trained_models['xgboost'] = xgb_model
                print("✅ XGBoost 模型训练完成（简化版本）")
        else:
            xgb_model = XGBRegressor(n_estimators=100, random_state=42, max_depth=6, learning_rate=0.1)
            xgb_model.fit(X_train_scaled, y_train)
            trained_models['xgboost'] = xgb_model
            print("✅ XGBoost 模型训练完成")

        # 3. Gradient Boosting 模型（使用原项目的实现）
        print("训练 Gradient Boosting 模型...")
        if USE_ORIGINAL_MODELS:
            try:
                gb_model = GradientBoostingModel()
                if gb_model.train(X_train_scaled, y_train, hyperparameter_tuning=False):
                    trained_models['gradient_boosting'] = gb_model
                    print("✅ Gradient Boosting 模型训练完成（使用原项目实现）")
                else:
                    raise Exception("原项目模型训练失败")
            except Exception as e:
                print(f"⚠️ 原项目 GB 模型失败，使用简化版本: {e}")
                import traceback
                traceback.print_exc()
                from sklearn.ensemble import GradientBoostingRegressor
                gb_model = GradientBoostingRegressor(n_estimators=100, random_state=42, max_depth=5)
                gb_model.fit(X_train_scaled, y_train)
                trained_models['gradient_boosting'] = gb_model
                print("✅ Gradient Boosting 模型训练完成（简化版本）")
        else:
            from sklearn.ensemble import GradientBoostingRegressor
            gb_model = GradientBoostingRegressor(n_estimators=100, random_state=42, max_depth=5)
            gb_model.fit(X_train_scaled, y_train)
            trained_models['gradient_boosting'] = gb_model
            print("✅ Gradient Boosting 模型训练完成")

        # 4. 集成模型（使用原项目的智能集成）
        print("创建集成模型...")
        predictions_for_ensemble = {}
        for name, model in trained_models.items():
            try:
                predictions_for_ensemble[name] = model.predict(X_test_scaled)
            except Exception as e:
                print(f"⚠️ 获取 {name} 预测失败: {e}")

        if USE_ORIGINAL_MODELS and len(predictions_for_ensemble) >= 2:
            try:
                ensemble_config = {
                    'selection_method': 'all',
                    'ensemble_method': 'weighted_average',
                    'exclude_models': [],
                    'min_models': 2,
                }
                ensemble_model = EnsembleModel(config=ensemble_config)
                ensemble_model.train(predictions_for_ensemble, y_test)
                trained_models['ensemble'] = ensemble_model
                print("✅ 集成模型创建完成（使用原项目智能集成）")
            except Exception as e:
                print(f"⚠️ 原项目集成模型失败: {e}")
                import traceback
                traceback.print_exc()
                print("跳过集成模型")

        print("=" * 60)

        # 评估模型
        results = {}
        for name, model in trained_models.items():
            try:
                y_pred = model.predict(X_test_scaled)
                results[name] = {
                    'mse': float(mean_squared_error(y_test, y_pred)),
                    'rmse': float(np.sqrt(mean_squared_error(y_test, y_pred))),
                    'mae': float(mean_absolute_error(y_test, y_pred)),
                    'r2': float(r2_score(y_test, y_pred))
                }
                print(f"  {name}: MAE={results[name]['mae']:.2f}, RMSE={results[name]['rmse']:.2f}, R²={results[name]['r2']:.4f}")
            except Exception as e:
                print(f"⚠️ 评估 {name} 模型失败: {e}")

        print("=" * 60)

        return jsonify({
            'message': '模型训练成功',
            'target_column': target_column,
            'features': feature_columns,
            'train_size': len(X_train),
            'test_size': len(X_test),
            'results': results,
            'using_original_models': USE_ORIGINAL_MODELS
        })

    except Exception as e:
        import traceback
        print(f"训练失败: {e}")
        print(traceback.format_exc())
        return jsonify({'error': f'训练失败: {str(e)}'}), 500

@app.route('/api/batch_predict', methods=['POST'])
def batch_predict():
    global current_data, trained_models, scaler, feature_columns

    try:
        if trained_models is None:
            return jsonify({'error': '请先训练模型'}), 400

        if current_data is None:
            return jsonify({'error': '请先上传数据'}), 400

        params = request.json
        model_type = params.get('model', 'ensemble')

        if model_type not in trained_models:
            available_models = list(trained_models.keys())
            return jsonify({
                'error': f'模型类型 "{model_type}" 不存在',
                'available_models': available_models
            }), 400

        # 准备数据
        df = current_data.copy()
        X = df[feature_columns].fillna(df[feature_columns].mean())
        X_scaled = scaler.transform(X)

        # 批量预测
        model = trained_models[model_type]
        print(f"使用模型 {model_type} 进行批量预测...")
        print(f"模型类型: {type(model)}")

        # 特殊处理集成模型
        if model_type == 'ensemble' and USE_ORIGINAL_MODELS:
            print("集成模型需要各个子模型的预测结果...")
            # 获取所有子模型的预测
            new_predictions = {}
            for name, sub_model in trained_models.items():
                if name != 'ensemble':
                    try:
                        new_predictions[name] = sub_model.predict(X_scaled)
                        print(f"  ✅ {name} 预测完成")
                    except Exception as e:
                        print(f"  ⚠️ {name} 预测失败: {e}")

            if len(new_predictions) < 2:
                return jsonify({'error': '集成模型需要至少2个子模型的预测结果'}), 500

            # 调用集成模型的 predict 方法
            predictions = model.predict(new_predictions)
            print(f"集成预测完成，结果长度: {len(predictions) if predictions is not None else 0}")
        else:
            # 普通模型直接预测
            if hasattr(model, 'predict'):
                predictions = model.predict(X_scaled)
                print(f"预测结果类型: {type(predictions)}")
                print(f"预测结果前5个: {predictions[:5] if predictions is not None else None}")
            else:
                return jsonify({'error': f'模型 {model_type} 没有 predict 方法'}), 500

        if predictions is None:
            return jsonify({'error': f'模型 {model_type} 预测返回 None'}), 500

        # 添加预测结果到数据框
        df['预测电价'] = predictions

        # 转换为 JSON 可序列化的格式
        results = df.head(50).copy()
        for col in results.columns:
            if results[col].dtype == 'object':
                results[col] = results[col].astype(str)
            elif pd.api.types.is_datetime64_any_dtype(results[col]):
                results[col] = results[col].astype(str)
            else:
                results[col] = results[col].apply(lambda x: float(x) if pd.notna(x) else None)

        return jsonify({
            'message': '批量预测完成',
            'model': model_type,
            'count': int(len(predictions)),
            'results': results.to_dict('records')
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'批量预测失败: {str(e)}'}), 500

@app.route('/api/predict', methods=['POST'])
def predict_price():
    """预测整个月的电价"""
    global current_data

    try:
        print("\n" + "="*60)
        print("📥 收到预测请求")
        print("="*60)

        if current_data is None:
            print("❌ 错误: 未上传数据文件")
            return jsonify({'success': False, 'error': '请先上传数据文件'}), 400

        data = request.get_json()
        print(f"📦 请求数据: {data}")

        model_type = data.get('model', 'ensemble')
        print(f"🤖 模型类型: {model_type}")

        print(f"\n{'='*60}")
        print(f"📊 开始预测整月电价 - 模型: {model_type}")
        print(f"{'='*60}")

        # 找到时间列
        time_column = None
        for col in current_data.columns:
            if str(col).lower() == '时间' or str(col).lower() == 'datetime':
                time_column = col
                break

        if not time_column:
            for col in current_data.columns:
                col_lower = str(col).lower()
                if any(keyword in col_lower for keyword in ['time', 'date']) and '日期' not in col_lower and '时刻' not in col_lower:
                    time_column = col
                    break

        if not time_column:
            error_msg = '未找到时间列'
            print(f"❌ {error_msg}")
            return jsonify({'success': False, 'error': error_msg}), 400

        print(f"✅ 找到时间列: {time_column}")

        # 确保时间列是 datetime 类型
        if not pd.api.types.is_datetime64_any_dtype(current_data[time_column]):
            current_data[time_column] = pd.to_datetime(current_data[time_column])

        # 按时间排序
        data_sorted = current_data.sort_values(by=time_column).copy()

        # 获取日期范围
        min_date = data_sorted[time_column].min().strftime('%Y-%m-%d')
        max_date = data_sorted[time_column].max().strftime('%Y-%m-%d')
        print(f"📅 数据日期范围: {min_date} 到 {max_date}")

        # 找到电价列
        price_column = None
        for col in current_data.columns:
            if '实时出清电价' in str(col):
                price_column = col
                break

        # 如果没找到"实时出清电价"，再找其他电价列
        if not price_column:
            for col in current_data.columns:
                if '电价' in str(col):
                    price_column = col
                    break

        if not price_column:
            error_msg = f'未找到电价列。可用列: {list(current_data.columns)}'
            print(f"❌ {error_msg}")
            return jsonify({'success': False, 'error': '未找到电价列'}), 400

        print(f"✅ 电价列: {price_column}")

        # 🔧 特征工程：创建所有特征（包括GAP规则）
        print(f"\n{'='*60}")
        print(f"🔧 开始特征工程...")
        print(f"{'='*60}")

        # GAP天数设置为1（T=1）
        gap_days = 1
        data_with_features = create_all_features(data_sorted, price_column, time_column, gap_days=gap_days)

        print(f"\n{'='*60}")
        print(f"✅ 特征工程完成")
        print(f"{'='*60}\n")

        # 按时间顺序分割：前80%训练，后20%测试
        split_idx = int(len(data_with_features) * 0.8)
        train_data = data_with_features.iloc[:split_idx].copy().reset_index(drop=True)
        test_data = data_with_features.iloc[split_idx:].copy().reset_index(drop=True)

        print(f"✅ 训练集大小: {len(train_data)}, 测试集大小: {len(test_data)}")
        print(f"   训练集时间范围: {train_data[time_column].min()} 到 {train_data[time_column].max()}")
        print(f"   测试集时间范围: {test_data[time_column].min()} 到 {test_data[time_column].max()}")

        # 准备特征和目标
        # 只使用原项目的5个核心特征
        feature_cols = ['hour', 'dayofweek', 'day', 'price_lag1', 'price_lag4']

        # 检查特征是否存在
        missing_features = [f for f in feature_cols if f not in train_data.columns]
        if missing_features:
            error_msg = f'缺少特征列: {missing_features}'
            print(f"❌ {error_msg}")
            return jsonify({'success': False, 'error': error_msg}), 400

        print(f"✅ 使用原项目的5个核心特征:")
        print(f"   1. hour - 小时")
        print(f"   2. dayofweek - 星期几")
        print(f"   3. day - 日期")
        print(f"   4. price_lag1 - 前1个时间点的价格")
        print(f"   5. price_lag4 - 前4个时间点的价格")

        # 处理缺失值（使用SimpleImputer，原项目方式）
        print(f"\n🔧 处理缺失值...")
        print(f"   训练集缺失值数量: {train_data[feature_cols].isna().sum().sum()}")
        print(f"   测试集缺失值数量: {test_data[feature_cols].isna().sum().sum()}")

        X_train = train_data[feature_cols].values
        y_train = train_data[price_column].values
        X_test = test_data[feature_cols].values
        y_test = test_data[price_column].values

        # 使用SimpleImputer处理缺失值（原项目方式）
        from sklearn.impute import SimpleImputer
        imputer = SimpleImputer(strategy='mean')
        X_train = imputer.fit_transform(X_train)
        X_test = imputer.transform(X_test)

        print(f"   ✅ 缺失值处理完成")
        print(f"   ⚠️  注意：不使用StandardScaler，直接使用原始特征值（原项目方式）")

        # 根据选择的模型类型进行训练和预测
        model_name_map = {
            'random_forest': '随机森林',
            'xgboost': 'XGBoost',
            'gradient_boosting': '梯度提升',
            'linear_regression': '线性回归',
            'lstm': 'LSTM神经网络',
            'historical': '历史同期模型',
            'ensemble': '集成模型'
        }

        print(f"🤖 开始训练 {model_name_map.get(model_type, model_type)} 模型...")

        # 导入模型
        sys.path.insert(0, str(Path(__file__).parent.parent))

        if model_type == 'random_forest':
            from src.predictions.random_forest_model import RandomForestModel
            model = RandomForestModel(config={'HYPERPARAMETER_TUNING': {'CV_FOLDS': 3, 'RF_SEARCH_ITERATIONS': 5}})
            model.train(X_train, y_train)
            y_pred = model.predict(X_test)

        elif model_type == 'xgboost':
            from src.predictions.xgboost_model import XGBoostModel
            model = XGBoostModel(config={'HYPERPARAMETER_TUNING': {'CV_FOLDS': 3, 'XGB_SEARCH_ITERATIONS': 5}})
            model.train(X_train, y_train)
            y_pred = model.predict(X_test)

        elif model_type == 'gradient_boosting':
            from src.predictions.gradient_boosting_model import GradientBoostingModel
            model = GradientBoostingModel(config={'HYPERPARAMETER_TUNING': {'CV_FOLDS': 3, 'GB_SEARCH_ITERATIONS': 5}})
            model.train(X_train, y_train)
            y_pred = model.predict(X_test)

        elif model_type == 'linear_regression':
            from src.predictions.linear_regression_model import LinearRegressionModel
            model = LinearRegressionModel(config={'HYPERPARAMETER_TUNING': {'CV_FOLDS': 3, 'LINEAR_SEARCH_ITERATIONS': 5}})
            model.train(X_train, y_train)
            y_pred = model.predict(X_test)

        elif model_type == 'lstm':
            from src.predictions.lstm_model import LSTMModel
            # LSTM需要特殊处理，因为它需要序列数据
            # 为了简化，我们使用较少的epochs
            model = LSTMModel(config={
                'LSTM_PARAMS': {'epochs': 10, 'look_back_days': 3},
                'HYPERPARAMETER_TUNING': {'LSTM_SEARCH_ITERATIONS': 2}
            })
            model.train(X_train, y_train)
            y_pred = model.predict(X_test)

        elif model_type == 'historical':
            from src.predictions.historical_model import HistoricalModel
            # 历史同期模型需要带时间索引的数据
            # 创建带时间索引的训练数据
            train_data_indexed = train_data.copy()
            train_data_indexed.index = pd.to_datetime(train_data[time_column])
            test_data_indexed = test_data.copy()
            test_data_indexed.index = pd.to_datetime(test_data[time_column])

            # 准备训练数据
            X_train_df = train_data_indexed[feature_cols]
            y_train_series = train_data_indexed[price_column]
            y_train_series.name = price_column

            X_test_df = test_data_indexed[feature_cols]

            model = HistoricalModel()
            model.train(X_train_df, y_train_series)
            y_pred = model.predict(X_test_df)

        elif model_type == 'ensemble':
            from src.predictions.random_forest_model import RandomForestModel
            from src.predictions.xgboost_model import XGBoostModel
            from src.predictions.gradient_boosting_model import GradientBoostingModel
            from src.predictions.linear_regression_model import LinearRegressionModel
            from src.predictions.ensemble_model import EnsembleModel

            # 训练各个子模型
            print("   训练随机森林...")
            rf_model = RandomForestModel(config={'HYPERPARAMETER_TUNING': {'CV_FOLDS': 3, 'RF_SEARCH_ITERATIONS': 3}})
            rf_model.train(X_train, y_train)
            rf_pred = rf_model.predict(X_test)

            print("   训练XGBoost...")
            xgb_model = XGBoostModel(config={'HYPERPARAMETER_TUNING': {'CV_FOLDS': 3, 'XGB_SEARCH_ITERATIONS': 3}})
            xgb_model.train(X_train, y_train)
            xgb_pred = xgb_model.predict(X_test)

            print("   训练梯度提升...")
            gb_model = GradientBoostingModel(config={'HYPERPARAMETER_TUNING': {'CV_FOLDS': 3, 'GB_SEARCH_ITERATIONS': 3}})
            gb_model.train(X_train, y_train)
            gb_pred = gb_model.predict(X_test)

            print("   训练线性回归...")
            lr_model = LinearRegressionModel(config={'HYPERPARAMETER_TUNING': {'CV_FOLDS': 3, 'LINEAR_SEARCH_ITERATIONS': 3}})
            lr_model.train(X_train, y_train)
            lr_pred = lr_model.predict(X_test)

            # 集成预测
            print("   集成模型...")
            ensemble = EnsembleModel(config={'ensemble_method': 'weighted_average', 'selection_method': 'all'})
            predictions_dict = {
                'random_forest': rf_pred,
                'xgboost': xgb_pred,
                'gradient_boosting': gb_pred,
                'linear_regression': lr_pred
            }
            ensemble.train(predictions_dict, y_test)
            y_pred = ensemble.predict(predictions_dict)

        else:
            return jsonify({'success': False, 'error': f'不支持的模型类型: {model_type}'}), 400

        print(f"✅ 预测完成")

        # 计算性能指标
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        r2 = r2_score(y_test, y_pred)

        # 计算MAPE，处理可能的NaN值
        mape_values = np.abs((y_test - y_pred) / np.where(y_test != 0, y_test, 1)) * 100
        mape = np.mean(mape_values[~np.isnan(mape_values)])

        # 如果所有值都是NaN，设置为0
        if np.isnan(mape):
            mape = 0.0

        print(f"📊 性能指标:")
        print(f"   MAE: {mae:.2f}")
        print(f"   RMSE: {rmse:.2f}")
        print(f"   R²: {r2:.4f}")
        print(f"   MAPE: {mape:.2f}%")

        # 准备返回结果
        predictions = []
        # 获取时间列的值（作为列表）
        time_values = test_data[time_column].tolist()

        print(f"📊 准备返回结果...")
        print(f"   测试集长度: {len(test_data)}")
        print(f"   预测值长度: {len(y_pred)}")
        print(f"   实际值长度: {len(y_test)}")
        print(f"   时间值长度: {len(time_values)}")
        print(f"   前3个时间值: {time_values[:3]}")

        for i in range(len(test_data)):
            pred_val = float(y_pred[i]) if not np.isnan(y_pred[i]) and not np.isinf(y_pred[i]) else 0.0
            actual_val = float(y_test[i]) if not np.isnan(y_test[i]) and not np.isinf(y_test[i]) else 0.0
            time_val = time_values[i]

            # 确保时间值是有效的
            if pd.isna(time_val):
                print(f"⚠️ 警告: 索引 {i} 的时间值为 NaT")
                time_str = 'NaT'
            else:
                time_str = str(time_val)

            predictions.append({
                'time': time_str,
                'predicted': pred_val,
                'actual': actual_val
            })

        # 获取测试集的日期范围
        test_min_date = test_data[time_column].min().strftime('%Y-%m-%d')
        test_max_date = test_data[time_column].max().strftime('%Y-%m-%d')
        date_range = f"{test_min_date} 到 {test_max_date}"

        # 确保所有指标都是有效的数值
        def safe_float(val):
            if np.isnan(val) or np.isinf(val):
                return 0.0
            return float(val)

        return jsonify({
            'success': True,
            'date_range': date_range,
            'model': model_type,
            'model_name': model_name_map.get(model_type, model_type),
            'train_size': len(train_data),
            'predictions': predictions,
            'metrics': {
                'mae': safe_float(mae),
                'rmse': safe_float(rmse),
                'r2': safe_float(r2),
                'mape': safe_float(mape)
            }
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'预测失败: {str(e)}'}), 500

@app.route('/api/predict-original-file', methods=['POST'])
def predict_original_file_endpoint():
    """直接调用原项目 main_prediction.py 的 main() 函数"""
    try:
        print("\n" + "="*60)
        print("📥 收到预测请求 - 直接调用原项目 main_prediction.py")
        print("="*60)

        # 调用原项目的预测函数（直接运行main()）
        result = run_original_prediction()

        if not result['success']:
            return jsonify(result), 500

        # 准备返回数据（格式化为前端需要的格式）
        predictions_list = []
        y_test = result['y_test']
        timestamps = result['timestamps']

        # 辅助函数：安全转换为浮点数
        def safe_float(value):
            """安全地将值转换为浮点数，处理 None 值"""
            if value is None:
                return None
            try:
                return float(value)
            except (ValueError, TypeError):
                return None

        for i in range(len(y_test)):
            pred_item = {
                'time': timestamps[i],
                'actual': safe_float(y_test[i])
            }

            # 添加所有模型的预测值
            for model_name, pred_values in result['predictions'].items():
                if i < len(pred_values):
                    pred_item[model_name] = safe_float(pred_values[i])

            predictions_list.append(pred_item)

        print(f"\n✅ 原项目预测完成！")
        print(f"   返回 {len(predictions_list)} 条预测结果")
        print(f"   包含 {len(result['metrics'])} 个模型的性能指标")
        print(f"   时间戳示例: {predictions_list[0]['time'] if predictions_list else 'N/A'}")

        # 构建响应数据
        response_data = {
            'success': True,
            'predictions': predictions_list,
            'metrics': result['metrics'],
            'model_names': list(result['predictions'].keys()),
            'train_size': result['train_size'],
            'test_size': result['test_size'],
            'feature_names': result['feature_names']
        }

        # 手动序列化为 JSON，确保 NaN 和 Infinity 被正确处理
        json_str = json.dumps(response_data, cls=SafeJSONEncoder, ensure_ascii=False)

        # 返回 Response 对象而不是 jsonify
        return Response(json_str, mimetype='application/json')

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'预测失败: {str(e)}'}), 500

@app.route('/api/predict-original', methods=['POST'])
def predict_original_endpoint():
    """运行原项目的预测逻辑（使用上传的数据）"""
    global current_data

    try:
        print("\n" + "="*60)
        print("📥 收到预测请求 - 运行原项目预测逻辑（使用上传数据）")
        print("="*60)

        if current_data is None:
            print("❌ 错误: 未上传数据文件")
            return jsonify({'success': False, 'error': '请先上传数据文件'}), 400

        # 获取上传的文件路径
        uploaded_file_path = os.path.join(UPLOAD_FOLDER, 'current_data.xlsx')

        # 保存当前数据到临时文件
        current_data.to_excel(uploaded_file_path, index=False)
        print(f"✅ 数据已保存到: {uploaded_file_path}")

        # 调用原项目的预测函数
        result = run_original_prediction(uploaded_file_path)

        if not result['success']:
            return jsonify(result), 500

        # 准备返回数据（格式化为前端需要的格式）
        predictions_list = []
        y_test = result['y_test']
        timestamps = result['timestamps']

        for i in range(len(y_test)):
            pred_item = {
                'time': timestamps[i],
                'actual': float(y_test[i])
            }

            # 添加所有模型的预测值
            for model_name, pred_values in result['predictions'].items():
                if i < len(pred_values):
                    pred_item[model_name] = float(pred_values[i])

            predictions_list.append(pred_item)

        print(f"\n✅ 原项目预测完成！")
        print(f"   返回 {len(predictions_list)} 条预测结果")
        print(f"   包含 {len(result['metrics'])} 个模型的性能指标")

        # 构建响应数据
        response_data = {
            'success': True,
            'predictions': predictions_list,
            'metrics': result['metrics'],
            'model_names': list(result['predictions'].keys()),
            'train_size': result['train_size'],
            'test_size': result['test_size'],
            'feature_names': result['feature_names']
        }

        # 手动序列化为 JSON，确保 NaN 和 Infinity 被正确处理
        json_str = json.dumps(response_data, cls=SafeJSONEncoder, ensure_ascii=False)

        # 返回 Response 对象而不是 jsonify
        return Response(json_str, mimetype='application/json')

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'预测失败: {str(e)}'}), 500

@app.route('/api/predict-all-models', methods=['POST'])
def predict_all_models_endpoint():
    """运行所有预测模型并返回结果"""
    global current_data

    try:
        print("\n" + "="*60)
        print("📥 收到预测请求 - 运行所有模型")
        print("="*60)

        if current_data is None:
            print("❌ 错误: 未上传数据文件")
            return jsonify({'success': False, 'error': '请先上传数据文件'}), 400

        # 找到时间列
        time_column = None
        for col in current_data.columns:
            if str(col).lower() == '时间' or str(col).lower() == 'datetime':
                time_column = col
                break

        if not time_column:
            for col in current_data.columns:
                col_lower = str(col).lower()
                if any(keyword in col_lower for keyword in ['time', 'date']) and '日期' not in col_lower and '时刻' not in col_lower:
                    time_column = col
                    break

        if not time_column:
            error_msg = '未找到时间列'
            print(f"❌ {error_msg}")
            return jsonify({'success': False, 'error': error_msg}), 400

        print(f"✅ 找到时间列: {time_column}")

        # 确保时间列是 datetime 类型
        if not pd.api.types.is_datetime64_any_dtype(current_data[time_column]):
            current_data[time_column] = pd.to_datetime(current_data[time_column])

        # 按时间排序
        data_sorted = current_data.sort_values(by=time_column).copy()

        # 找到电价列
        price_column = None
        for col in current_data.columns:
            if '实时出清电价' in str(col):
                price_column = col
                break

        if not price_column:
            for col in current_data.columns:
                if '电价' in str(col):
                    price_column = col
                    break

        if not price_column:
            error_msg = f'未找到电价列。可用列: {list(current_data.columns)}'
            print(f"❌ {error_msg}")
            return jsonify({'success': False, 'error': '未找到电价列'}), 400

        print(f"✅ 电价列: {price_column}")

        # 特征工程
        gap_days = 1
        data_with_features = create_all_features(data_sorted, price_column, time_column, gap_days=gap_days)

        # 只使用原项目的5个核心特征
        feature_cols = ['hour', 'dayofweek', 'day', 'price_lag1', 'price_lag4']

        # 检查特征是否存在
        missing_features = [f for f in feature_cols if f not in data_with_features.columns]
        if missing_features:
            error_msg = f'缺少特征列: {missing_features}'
            print(f"❌ {error_msg}")
            return jsonify({'success': False, 'error': error_msg}), 400

        print(f"✅ 使用原项目的5个核心特征:")
        print(f"   1. hour - 小时")
        print(f"   2. dayofweek - 星期几")
        print(f"   3. day - 日期")
        print(f"   4. price_lag1 - 前1个时间点的价格")
        print(f"   5. price_lag4 - 前4个时间点的价格")

        # 运行所有模型
        results = run_all_models(data_with_features, price_column, time_column, feature_cols)

        # 准备返回数据
        predictions_list = []
        time_values = results['timestamps'].tolist()
        y_test = results['y_test']

        for i in range(len(y_test)):
            pred_item = {
                'time': str(time_values[i]),
                'actual': float(y_test[i]) if not np.isnan(y_test[i]) else 0.0
            }

            # 添加所有模型的预测值
            for model_name, pred_values in results['predictions'].items():
                if i < len(pred_values):
                    pred_val = float(pred_values[i]) if not np.isnan(pred_values[i]) else 0.0
                    pred_item[model_name] = pred_val

            predictions_list.append(pred_item)

        # 准备性能指标
        metrics_dict = {}
        for model_name, metrics in results['metrics'].items():
            metrics_dict[model_name] = {
                'mae': float(metrics['mae']),
                'rmse': float(metrics['rmse']),
                'r2': float(metrics['r2']),
                'mape': float(metrics['mape']),
                'direction_accuracy': float(metrics['direction_accuracy'])
            }

        print(f"\n✅ 所有模型预测完成！")
        print(f"   返回 {len(predictions_list)} 条预测结果")
        print(f"   包含 {len(metrics_dict)} 个模型的性能指标")

        return jsonify({
            'success': True,
            'predictions': predictions_list,
            'metrics': metrics_dict,
            'model_names': list(results['predictions'].keys())
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'预测失败: {str(e)}'}), 500

@app.route('/api/bidding/optimize', methods=['POST'])
def optimize_bidding():
    """
    运行投标优化
    """
    try:
        print("\n" + "="*60)
        print("🎯 收到投标优化请求")
        print("="*60)

        # 运行投标优化
        results = run_bidding_optimization()

        if not results.get('success', False):
            return jsonify(results), 500

        print("\n✅ 投标优化成功完成")
        return jsonify(results)

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"\n❌ 投标优化失败: {str(e)}")
        print(error_trace)
        return jsonify({
            'success': False,
            'error': f'投标优化失败: {str(e)}',
            'traceback': error_trace
        }), 500

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 电力市场预测系统启动中...")
    print("=" * 60)
    print(f"📍 API 地址: http://localhost:5000")
    print(f"📊 健康检查: http://localhost:5000/health")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5000, debug=True)

