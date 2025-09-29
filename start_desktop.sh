
echo "🚀 H743 Potentiostat Desktop Launcher"
echo "======================================"

# ตรวจสอบ Python version
echo "📍 ตรวจสอบ Python version..."

PYTHON_CMD=""
PYTHON_VERSION=""

# ลองหา Python ที่เหมาะสม
for cmd in python3.11 python3.10 python3.9 python3.8 python3 python; do
    if command -v $cmd &> /dev/null; then
        VERSION=$($cmd --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
        MAJOR=$(echo $VERSION | cut -d. -f1)
        MINOR=$(echo $VERSION | cut -d. -f2)
        
        if [ "$MAJOR" -eq 3 ] && [ "$MINOR" -ge 8 ]; then
            PYTHON_CMD=$cmd
            PYTHON_VERSION=$VERSION
            break
        fi
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    echo "❌ ไม่พบ Python 3.8 หรือสูงกว่า"
    echo "📦 กรุณาติดตั้ง Python 3.8+ ก่อน:"
    echo "   sudo apt-get update"
    echo "   sudo apt-get install python3.8 python3.8-venv python3.8-pip"
    exit 1
fi

echo "✅ พบ Python $PYTHON_VERSION ที่ $PYTHON_CMD"

# Virtual environment
if [ ! -d "poten-env" ]; then
    echo "📦 สร้าง virtual environment ด้วย Python $PYTHON_VERSION..."
    $PYTHON_CMD -m venv poten-env
    if [ $? -ne 0 ]; then
        echo "❌ ไม่สามารถสร้าง virtual environment ได้"
        echo "📦 ลองติดตั้ง: sudo apt-get install python3-venv"
        exit 1
    fi
fi

# Activate virtual environment
echo "🔄 เปิดใช้ virtual environment..."
source poten-env/bin/activate

# ตรวจสอบ Python ใน venv
VENV_VERSION=$(python --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
echo "✅ Virtual environment Python: $VENV_VERSION"

# Install dependencies
echo "📦 ติดตั้ง Python dependencies..."
DEPENDENCIES=("flask" "requests" "pyserial" "flask-cors" "pywebview")

for dep in "${DEPENDENCIES[@]}"; do
    echo "📦 ตรวจสอบ $dep..."
    if ! python -c "import $dep" 2>/dev/null; then
        echo "📥 ติดตั้ง $dep..."
        pip install $dep
        if [ $? -ne 0 ]; then
            echo "❌ ไม่สามารถติดตั้ง $dep ได้"
            exit 1
        fi
        echo "✅ ติดตั้ง $dep สำเร็จ"
    else
        echo "✅ $dep พร้อมใช้งาน"
    fi
done

# ตรวจสอบ GUI dependencies
echo "📦 ตรวจสอบ GUI dependencies..."

# ตรวจสอบว่าเป็น headless server หรือไม่
if [ -z "$DISPLAY" ] && [ -z "$WAYLAND_DISPLAY" ]; then
    echo "⚠️  ไม่พบ GUI display - อาจเป็น headless server"
    echo "💡 หากต้องการใช้ GUI บน remote server:"
    echo "   ssh -X koson@192.168.9.76"
    echo "   หรือติดตั้ง VNC/Remote Desktop"
    echo ""
    echo "🔄 กำลังลองรันแบบ headless..."
else
    echo "✅ พบ GUI display: $DISPLAY$WAYLAND_DISPLAY"
    
    # ติดตั้ง GUI dependencies ถ้าจำเป็น
    if ! dpkg -l | grep -q python3-gi 2>/dev/null; then
        echo "📥 ติดตั้ง GUI dependencies..."
        echo "💡 อาจต้องใส่รหัสผ่าน sudo:"
        sudo apt-get update && sudo apt-get install -y python3-gi python3-gi-cairo gir1.2-gtk-3.0 gir1.2-webkit2-4.0 python3-tk
    fi
fi

echo "🖥️  เริ่มแอปพลิเคชัน..."
echo "======================================"

# รัน desktop app
python desktop_app.py
