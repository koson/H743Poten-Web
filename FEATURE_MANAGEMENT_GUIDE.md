# H743Poten Feature Management System

## Overview

ระบบ Feature Management สำหรับ H743Poten Web Interface ช่วยให้คุณสามารถจัดการ features และ permissions สำหรับ users แต่ละกลุ่มได้อย่างละเอียด

## User Groups และ Permissions

### 1. Administrators (admin/admin123)
- **Features**: ทุก features รวมถึง AI Dashboard และ Hardware Diagnostics
- **Permissions**: read, write, delete, admin, configure
- **สามารถทำได้**:
  - จัดการ users และ groups
  - เปิด/ปิด features แบบ real-time
  - เข้าถึงการตั้งค่าระบบทั้งหมด
  - ควบคุมอุปกรณ์โดยตรง

### 2. Operators (operator/operator123)
- **Features**: การวัด, การวิเคราะห์, calibration, peak detection
- **Permissions**: read, write, configure
- **สามารถทำได้**:
  - ใช้งานระบบวัดทั้งหมด
  - วิเคราะห์ข้อมูลขั้นสูง
  - export ข้อมูล
  - ควบคุมอุปกรณ์

### 3. Researchers (researcher/research123)
- **Features**: การวิเคราะห์, AI Dashboard, peak detection
- **Permissions**: read, write
- **สามารถทำได้**:
  - วิเคราะห์ข้อมูลด้วย AI
  - ใช้เครื่องมือวิจัยขั้นสูง
  - export ข้อมูล
  - ไม่สามารถควบคุมอุปกรณ์

### 4. Viewers (viewer/viewer123)
- **Features**: ดูข้อมูลและ peak detection เบื้องต้น
- **Permissions**: read
- **สามารถทำได้**:
  - ดูข้อมูลที่มีอยู่
  - ใช้เครื่องมือวิเคราะห์พื้นฐาน

## วิธีการใช้งาน

### 1. การ Login
1. เข้าไปที่หน้า login: `http://localhost:8080/auth/login-page`
2. เลือก demo account หรือกรอก username/password
3. ระบบจะแสดงเมนูตาม role ของ user

### 2. การจัดการ Users (Admin เท่านั้น)
1. Login ด้วย admin account
2. ไปที่ User Management ในเมนู user
3. สามารถ:
   - สร้าง user ใหม่
   - แก้ไข groups ของ user
   - ดู active sessions

### 3. การจัดการ Features (Admin เท่านั้น)
1. Login ด้วย admin account
2. ไปที่ Feature Management
3. สามารถ:
   - เปิด/ปิด features แบบ real-time
   - ดูการกำหนดค่าของแต่ละ group
   - สร้าง deployment configuration

### 4. การ Deploy แบบเลือก Features

#### วิธีที่ 1: ใช้ Group-based Deployment
```javascript
// เปลี่ยน features ของ group แบบ dynamic
const response = await fetch('/admin/features/measurements', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        enabled: false,  // ปิด feature measurements
        target_groups: ['viewers']  // เฉพาะ group viewers
    })
});
```

#### วิธีที่ 2: ใช้ Feature Override
```javascript
// Override feature แบบชั่วคราว
const response = await fetch('/api/features/toggle/ai_dashboard', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        enabled: true  // เปิด AI Dashboard ชั่วคราว
    })
});
```

#### วิธีที่ 3: สร้าง Custom Deployment
```javascript
// สร้าง deployment configuration
const response = await fetch('/api/features/create-deployment', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        name: 'Research Lab Setup',
        features: ['measurements', 'analysis_workflow', 'ai_dashboard'],
        groups: ['researchers', 'operators']
    })
});
```

## API Endpoints

### Authentication
- `POST /auth/login` - Login
- `POST /auth/logout` - Logout
- `GET /auth/check-session` - ตรวจสอบ session

### User Management (Admin only)
- `GET /admin/users` - ดู users ทั้งหมด
- `POST /admin/users` - สร้าง user ใหม่
- `PUT /admin/users/{username}/groups` - แก้ไข groups

### Feature Management
- `GET /api/features/user` - ดู features ของ user ปัจจุบัน
- `POST /api/features/toggle/{feature_name}` - เปิด/ปิด feature
- `GET /api/features/deployment-config` - ดู deployment configuration
- `POST /api/features/create-deployment` - สร้าง deployment ใหม่
- `GET /api/features/simulate-user/{username}` - จำลองมุมมองของ user

## การกำหนดค่าใน HTML

### 1. ซ่อน/แสดง elements ตาม features
```html
<!-- จะแสดงเมื่อ user มี feature 'measurements' -->
<div data-feature="measurements">
    <button>Start Measurement</button>
</div>

<!-- จะแสดงเมื่อ user มี permission 'admin' -->
<div data-requires-permission="admin">
    <button>Admin Panel</button>
</div>
```

### 2. ใช้ JavaScript เช็ค features
```javascript
// เช็คว่า user มี feature หรือไม่
if (authManager.hasFeature('ai_dashboard')) {
    // แสดง AI Dashboard
}

// เช็คว่า user มี permission หรือไม่
if (authManager.hasPermission('admin')) {
    // แสดง admin controls
}
```

## การปรับแต่งสำหรับ Production

### 1. การตั้งค่า Security
```python
# ใน app.py
app.config['SECRET_KEY'] = 'your-secure-secret-key'

# ใน middleware/auth.py
response.set_cookie(
    'session_id',
    session_id,
    secure=True,      # ใช้ HTTPS
    httponly=True,    # ป้องกัน XSS
    samesite='Strict' # ป้องกัน CSRF
)
```

### 2. การสร้าง Custom User Groups
```python
# เพิ่มใน services/user_service.py
custom_groups = {
    "lab_managers": {
        "name": "Lab Managers",
        "description": "Laboratory management team",
        "features": {
            "measurements": True,
            "analysis_workflow": True,
            "calibration": True,
            "data_logging": True,
            "user_management": True  # จัดการ users ในแลป
        },
        "permissions": ["read", "write", "configure"]
    }
}
```

### 3. การสร้าง Custom Features
```python
# เพิ่มใน services/feature_service.py
custom_features = {
    "custom_analysis": {
        "name": "Custom Analysis Module",
        "description": "Laboratory-specific analysis tools",
        "category": "analysis",
        "enabled": True,
        "requires_permissions": ["read", "write"],
        "routes": ["/custom-analysis", "/api/custom/*"],
        "menu_item": {
            "label": "Custom Analysis",
            "icon": "fas fa-flask",
            "order": 6
        }
    }
}
```

## ตัวอย่างการใช้งานจริง

### Scenario 1: ระบบสำหรับนักเรียน
```python
# กำหนด features เฉพาะการดูข้อมูล
student_features = {
    "measurements": False,      # ไม่ให้วัด
    "analysis_workflow": True,  # ให้วิเคราะห์ข้อมูลที่มี
    "peak_detection": True,     # ให้ใช้ peak detection
    "data_export": False,       # ไม่ให้ export
    "device_control": False     # ไม่ให้ควบคุมเครื่อง
}
```

### Scenario 2: ระบบสำหรับลูกค้า Demo
```python
# กำหนด features สำหรับ demo
demo_features = {
    "measurements": True,       # ให้วัดได้ แต่จำกัด
    "csv_emulation": True,      # ใช้ข้อมูล demo
    "ai_dashboard": True,       # แสดงความสามารถ AI
    "hardware_diagnostics": False,  # ไม่ให้เข้าถึงระบบจริง
    "data_export": False        # ไม่ให้ export ข้อมูลจริง
}
```

### Scenario 3: ระบบสำหรับ Remote Access
```python
# กำหนด features สำหรับการเข้าถึงระยะไกล
remote_features = {
    "measurements": False,      # ไม่ให้ควบคุมเครื่องระยะไกล
    "analysis_workflow": True,  # ให้วิเคราะห์ข้อมูล
    "data_logging": True,       # ให้ดูข้อมูลที่บันทึก
    "peak_detection": True,     # ให้ใช้เครื่องมือวิเคราะห์
    "device_control": False     # ห้ามควบคุมเครื่อง
}
```

## สรุป

ระบบ Feature Management ของ H743Poten ให้ความยืดหยุ่นในการจัดการสิทธิ์และ features ที่สูง สามารถปรับแต่งได้ตามความต้องการของแต่ละองค์กร ช่วยให้สามารถ deploy ระบบเดียวกันให้กับ user groups ที่แตกต่างกันได้อย่างมีประสิทธิภาพ