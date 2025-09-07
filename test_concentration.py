import re

def extract_concentration_from_filename(filename):
    # Pattern ที่ตรงกับตัวเลขตามด้วย mM (รวมจุดทศนียม)
    pattern = r'(\d+(?:\.\d+)?)mM'
    match = re.search(pattern, filename)
    return float(match.group(1)) if match else None

# ทดสอบกับไฟล์ต่างๆ
test_files = [
    'Pipot_Ferro_0.5mM_100mVpS_E1_scan_01.csv',
    'Palmsens_0.5mM_CV_100mVpS_E1_scan_01.csv', 
    'Palmsens_5mM_CV_100mVpS_E1_scan_01.csv',
    'Palmsens_1.0mM_CV_100mVpS_E1_scan_01.csv',
    'Palmsens_10mM_CV_100mVpS_E1_scan_01.csv'
]

print("Testing concentration extraction after file renaming:")
print("=" * 60)
for filename in test_files:
    concentration = extract_concentration_from_filename(filename)
    print(f"{filename:<50} -> {concentration} mM")
