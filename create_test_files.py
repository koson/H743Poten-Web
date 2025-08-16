import pandas as pd
import numpy as np
import os

# สร้างไฟล์ CV data ขนาดใหญ่สำหรับทดสอบ 
print("Creating large test CV file...")

data_points = 800000  # 800k points for ~25MB file

potential = np.linspace(-1.0, 1.0, data_points)
current = np.sin(potential * 5) * 1e-6 + np.random.normal(0, 1e-7, data_points)
time_points = np.linspace(0, 100, data_points)

df = pd.DataFrame({
    'Potential (V)': potential,
    'Current (A)': current,
    'Time (s)': time_points
})

# สร้าง directory ถ้าไม่มี
os.makedirs('test_files', exist_ok=True)

# Save large file
df.to_csv('test_files/test_cv_large.csv', index=False)
print(f'Created large test file with {len(df)} rows')

# สร้างไฟล์ขนาดใหญ่มากสำหรับทดสอบ error
data_points_xl = 2000000  # 2M points for ~60MB file

potential_xl = np.linspace(-1.0, 1.0, data_points_xl)
current_xl = np.sin(potential_xl * 5) * 1e-6 + np.random.normal(0, 1e-7, data_points_xl)
time_points_xl = np.linspace(0, 200, data_points_xl)

df_xl = pd.DataFrame({
    'Potential (V)': potential_xl,
    'Current (A)': current_xl,
    'Time (s)': time_points_xl
})

df_xl.to_csv('test_files/test_cv_extra_large.csv', index=False)
print(f'Created extra large test file with {len(df_xl)} rows')

# แสดงขนาดไฟล์
import os
if os.path.exists('test_files/test_cv_large.csv'):
    size = os.path.getsize('test_files/test_cv_large.csv') / (1024*1024)
    print(f'Large file size: {size:.2f} MB')

if os.path.exists('test_files/test_cv_extra_large.csv'):
    size_xl = os.path.getsize('test_files/test_cv_extra_large.csv') / (1024*1024)
    print(f'Extra large file size: {size_xl:.2f} MB')
