# Quick Start: Feature Management System

## การติดตั้งและเริ่มใช้งาน

### 1. เริ่มต้นระบบ
```bash
# เปิดเซิร์ฟเวอร์
python main.py

# หรือใช้ development server
python main_dev.py
```

### 2. เข้าสู่ระบบ
เปิดเบราว์เซอร์และไปที่: `http://localhost:8080/auth/login-page`

**Demo Accounts:**
- **admin/admin123** - ควบคุมทุกอย่าง
- **operator/operator123** - ใช้งานระบบวัด
- **researcher/research123** - วิเคราะห์ข้อมูล + AI
- **viewer/viewer123** - ดูข้อมูลเท่านั้น

### 3. ทดสอบ Feature Management

#### 3.1 ทดสอบกับ Admin Account
1. Login ด้วย admin/admin123
2. ไปที่เมนู User ตรงมุมขวาบน → User Management
3. ดู users และ groups ทั้งหมด
4. ไปที่ Feature Management
5. ลองเปิด/ปิด features

#### 3.2 ทดสอบกับ User ธรรมดา
1. Login ด้วย viewer/viewer123
2. สังเกตว่าเมนูมีน้อยกว่า admin
3. ลองเข้า `/measurements` จะเห็นว่าบาง controls ถูกซ่อน
4. ลอง `/settings` จะเข้าไม่ได้

### 4. การจัด Deploy แบบเลือก Features

#### สถานการณ์: ระบบสำหรับนักเรียน
```bash
# 1. Login ด้วย admin
# 2. สร้าง user group ใหม่สำหรับนักเรียน
curl -X POST http://localhost:8080/admin/users \
  -H "Content-Type: application/json" \
  -d '{
    "username": "student01",
    "password": "student123",
    "email": "student01@school.edu",
    "full_name": "Student One",
    "groups": ["viewers"]
  }'
```

#### สถานการณ์: ระบบ Demo สำหรับลูกค้า
```javascript
// ปิด features ที่ไม่ต้องการแสดงในการ demo
const demoSetup = async () => {
    // ปิด hardware diagnostics
    await fetch('/api/features/toggle/hardware_diagnostics', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled: false })
    });
    
    // เปิด AI dashboard เพื่อโชว์ความสามารถ
    await fetch('/api/features/toggle/ai_dashboard', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled: true })
    });
};
```

#### สถานการณ์: ระบบแลปวิจัย
```javascript
// เปิดเฉพาะ features ที่จำเป็นสำหรับการวิจัย
const researchSetup = async () => {
    const features = [
        'measurements',
        'analysis_workflow', 
        'ai_dashboard',
        'peak_detection',
        'data_export'
    ];
    
    // เปิด features ที่เลือก
    for (const feature of features) {
        await fetch(`/api/features/toggle/${feature}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ enabled: true })
        });
    }
};
```

## การใช้งานขั้นสูง

### 1. สร้าง Custom User Group
```python
# ใน config/user_groups.json เพิ่ม:
{
    "technicians": {
        "name": "Technicians",
        "description": "Equipment maintenance team",
        "features": {
            "measurements": true,
            "hardware_diagnostics": true,
            "device_control": true,
            "data_logging": true,
            "calibration": true,
            "ai_dashboard": false,
            "analysis_workflow": false
        },
        "permissions": ["read", "write", "configure"]
    }
}
```

### 2. สร้าง Custom Feature
```python
# ใน config/features.json เพิ่ม:
{
    "quality_control": {
        "name": "Quality Control",
        "description": "Quality control and validation tools",
        "category": "analysis",
        "enabled": true,
        "requires_permissions": ["read", "write"],
        "routes": ["/qc", "/api/qc/*"],
        "menu_item": {
            "label": "Quality Control",
            "icon": "fas fa-check-circle",
            "order": 7
        }
    }
}
```

### 3. Dynamic Feature Control
```javascript
// ติดตาม feature status แบบ real-time
const featureMonitor = {
    async checkFeatureStatus(featureName) {
        const response = await fetch(`/api/features/test-access/${featureName}`);
        const data = await response.json();
        return data.has_access;
    },

    async updateUI() {
        const features = ['measurements', 'ai_dashboard', 'calibration'];
        
        for (const feature of features) {
            const hasAccess = await this.checkFeatureStatus(feature);
            const elements = document.querySelectorAll(`[data-feature="${feature}"]`);
            
            elements.forEach(el => {
                if (hasAccess) {
                    el.style.display = '';
                    el.classList.remove('feature-disabled');
                } else {
                    el.style.display = 'none';
                    el.classList.add('feature-disabled');
                }
            });
        }
    }
};

// อัพเดท UI ทุก 30 วินาที
setInterval(() => featureMonitor.updateUI(), 30000);
```

## การแก้ปัญหา

### ปัญหา: Login ไม่ได้
```bash
# ตรวจสอบ log
tail -f logs/h743poten.log

# ตรวจสอบ session files
ls -la config/sessions.json

# รีเซ็ต users (ระวัง: จะลบ users ทั้งหมด)
rm config/users.json
# เริ่มเซิร์ฟเวอร์ใหม่เพื่อสร้าง default users
```

### ปัญหา: Features ไม่แสดง
```javascript
// ตรวจสอบใน browser console
console.log('Current user:', authManager.currentUser);
console.log('User features:', authManager.userFeatures);
console.log('Authentication status:', authManager.isAuthenticated);

// ตรวจสอบ API
fetch('/auth/check-session')
    .then(r => r.json())
    .then(console.log);
```

### ปัญหา: Permission Denied
```bash
# ตรวจสอบ user groups
curl http://localhost:8080/admin/users \
  -H "Cookie: session_id=YOUR_SESSION_ID"

# ตรวจสอบ feature config
curl http://localhost:8080/api/features/user \
  -H "Cookie: session_id=YOUR_SESSION_ID"
```

## Tips & Best Practices

### 1. การจัด Deploy แบบ Progressive
```javascript
// เริ่มด้วย features พื้นฐาน
const basicFeatures = ['measurements', 'data_logging'];

// ค่อยๆ เปิด features ขั้นสูง
const advancedFeatures = ['analysis_workflow', 'ai_dashboard'];

// สุดท้ายเปิด admin features
const adminFeatures = ['user_management', 'hardware_diagnostics'];
```

### 2. การทดสอบ Features
```javascript
// ทดสอบแต่ละ feature ก่อน deploy
const testFeature = async (featureName) => {
    try {
        const response = await fetch(`/api/features/test-access/${featureName}`);
        const data = await response.json();
        console.log(`Feature ${featureName}:`, data.has_access ? '✅' : '❌');
    } catch (error) {
        console.error(`Error testing ${featureName}:`, error);
    }
};

// ทดสอบทุก features
['measurements', 'ai_dashboard', 'calibration'].forEach(testFeature);
```

### 3. การสำรองข้อมูล
```bash
# สำรอง config files
cp -r config config_backup_$(date +%Y%m%d)

# กู้คืน config
cp -r config_backup_20250101/* config/
```

## สรุป

ระบบ Feature Management ช่วยให้สามารถ:
- ✅ จัดการสิทธิ์ user แบบละเอียด
- ✅ เปิด/ปิด features แบบ real-time
- ✅ Deploy ระบบเดียวกันให้ user groups ต่างๆ
- ✅ ปรับแต่งได้ตามความต้องการ
- ✅ รักษาความปลอดภัยของระบบ

**เริ่มต้นใช้งานได้ทันทีด้วย demo accounts!**