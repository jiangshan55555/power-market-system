import pandas as pd
import os

# 检查上传的文件
upload_dir = 'uploads'
if os.path.exists(upload_dir):
    files = os.listdir(upload_dir)
    print(f'上传的文件: {files}')
    
    if files:
        filepath = os.path.join(upload_dir, files[0])
        df = pd.read_excel(filepath)
        
        print(f'\n文件: {files[0]}')
        print(f'形状: {df.shape}')
        print(f'\n列名: {df.columns.tolist()}')
        print(f'\n前5行数据:')
        print(df.head())
        
        # 检查日期和时刻列
        if '日期' in df.columns:
            print(f'\n日期列示例:')
            print(df['日期'].head())
            print(f'日期列数据类型: {df["日期"].dtype}')
        
        if '时刻' in df.columns:
            print(f'\n时刻列示例:')
            print(df['时刻'].head())
            print(f'时刻列数据类型: {df["时刻"].dtype}')
        
        if '时间' in df.columns:
            print(f'\n时间列示例:')
            print(df['时间'].head())
            print(f'时间列数据类型: {df["时间"].dtype}')

