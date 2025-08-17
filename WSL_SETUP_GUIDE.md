# WSL Setup Guide for H743Poten Development

## 🐧 WSL Environment Setup

### วิธีแก้ปัญหา "/bin/sh not found"

#### 1. ตรวจสอบสถานะ WSL
```cmd
wsl --list --verbose
```

#### 2. ถ้า WSL ยังไม่ติดตั้ง
```powershell
# เปิด PowerShell as Administrator
wsl --install
# รีสตาร์ทเครื่อง
```

#### 3. ถ้า Ubuntu หยุดทำงาน
```cmd
wsl --distribution Ubuntu
# หรือ
wsl -d Ubuntu
```

#### 4. เริ่ม Ubuntu distribution
```cmd
wsl --set-default Ubuntu
wsl
```

### 🚀 การใช้งาน Environment Switcher

#### ใน VS Code Terminal:
1. **กด Ctrl+Shift+E** - เปิด Environment Switcher
2. **กด Ctrl+Shift+W** - เปิด WSL โดยตรง
3. **เลือก environment:**
   - `1` - Windows CMD (แนะนำ)
   - `2` - WSL/Linux 
   - `3` - Auto-detect

#### คำสั่งที่ใช้ได้:
```cmd
env_switcher.bat     # เลือก environment
wsl.bat              # เปิด WSL โดยตรง
simple_wsl.bat       # WSL launcher
dev                  # Windows environment
./dev.sh             # WSL environment (ใน WSL)
```

### 🔧 Terminal Profiles ใน VS Code

**H743Poten-Auto** (Default):
- แสดงตัวเลือก environment

**H743Poten-CMD**: 
- Windows Command Prompt พร้อม dev tools

**H743Poten-WSL**:
- ตรวจสอบและเปิด WSL environment

### ⌨️ Keyboard Shortcuts

- **Ctrl+Shift+D** - เปิด terminal ใหม่
- **Ctrl+Shift+E** - Environment Switcher (ใน terminal)
- **Ctrl+Shift+W** - เปิด WSL โดยตรง (ใน terminal)
- **Ctrl+Shift+S** - Start Server
- **Ctrl+Shift+X** - Stop Server
- **Ctrl+Shift+Q** - Check Status

### 🛠️ การติดตั้ง Python ใน WSL

```bash
# ใน WSL/Ubuntu terminal
sudo apt update
sudo apt install python3 python3-pip python3-venv

# ตรวจสอบการติดตั้ง
python3 --version
```

### 📁 การเข้าถึงไฟล์ Windows จาก WSL

```bash
# Windows D:\ drive จะอยู่ที่
cd /mnt/d/GitHubRepos/__Potentiostat/poten-2025/H743Poten/H743Poten-Web

# ทำให้ script executable
chmod +x dev.sh setup_wsl.sh

# รัน development tools
./dev.sh
```

### 🔍 Troubleshooting

#### ปัญหา: "Permission denied"
```bash
chmod +x dev.sh
```

#### ปัญหา: "Python not found"
```bash
./setup_wsl.sh  # auto-install Python
```

#### ปัญหา: "Command not found"
```bash
# ตรวจสอบว่าอยู่ใน directory ที่ถูกต้อง
pwd
ls -la dev.sh
```

#### ปัญหา: WSL ไม่เริ่มต้น
```cmd
# Reset WSL
wsl --shutdown
wsl --distribution Ubuntu
```

### 💡 Tips

1. **ใช้ Windows CMD** ถ้าเพิ่งเริ่มต้น
2. **ใช้ WSL** ถ้าต้องการ Docker หรือ Linux tools
3. **Auto-detect** จะเลือก environment ที่เหมาะสมให้อัตโนมัติ

### 🎯 Quick Commands

```cmd
# Windows
dev                    # Show help
dev start             # Start server
dev status            # Check status

# WSL  
./dev.sh              # Show help
./dev.sh start        # Start server
./dev.sh status       # Check status
```
