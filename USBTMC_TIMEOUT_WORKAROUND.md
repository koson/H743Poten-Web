# ⚠️ USBTMC Timeout Issue - Workaround

## ปัญหา:
DMM 34461A เกิด "Connection timed out" บ่อยครั้งหลังจาก:
- ส่งคำสั่ง `*RST`
- ใช้งานไประยะหนึ่ง
- มีการ error ใน SCPI command

## สาเหตุ:
- USBTMC device driver ใน Linux มี bug เรื่อง timeout
- DMM hang ใน remote mode
- USB communication buffer ค้าง

## วิธีแก้ไขชั่วคราว:

### วิธีที่ 1: Reset USB Module (Fastest)
```bash
ssh ben@192.168.9.75 "sudo rmmod usbtmc && sudo modprobe usbtmc && sudo chmod 666 /dev/usbtmc0"
```

### วิธีที่ 2: Unplug-Replug USB Cable (Most Reliable)
```
1. ถอดสาย USB ออกจาก DMM
2. รอ 5 วินาที
3. เสียบสาย USB กลับเข้าไป
4. รอ 10 วินาที ให้ Pi detect device
```

### วิธีที่ 3: Power Cycle DMM
```
1. กดปุ่ม Power บน DMM (ปิด)
2. รอ 10 วินาที
3. กดปุ่ม Power อีกครั้ง (เปิด)
4. รอให้ DMM boot up เสร็จ (~30 วินาที)
```

## วิธีป้องกัน:

### 1. ใช้ SCPI Commands อย่างระมัดระวัง
```bash
# ❌ Don't
*RST              # อาจทำให้ timeout

# ✅ Do
*CLS              # Clear errors first  
*RST              # Then reset
*CLS              # Clear again
```

### 2. ตรวจสอบ Error Queue เสมอ
```bash
SYST:ERR?         # Check for errors
```

### 3. Return to Local Mode หลังใช้งาน
```bash
QUIT              # Server will auto SYST:LOC
# หรือ
LOCAL             # Manual local mode return
```

## Long-term Solution:

### สำหรับ STM32 H743 Potentiostat:
ใช้ **Serial Communication (UART)** แทน USBTMC:

**ข้อดี:**
- ✅ ไม่มี timeout issues
- ✅ Faster recovery
- ✅ More reliable
- ✅ Simpler protocol
- ✅ Better control

**Architecture:**
```
PC/Pi → TCP/USB → Serial Port → STM32 H743
```

**Benefits:**
- Serial port สามารถ close/open ได้รวดเร็ว
- ไม่มี USB TMC Class complexity
- Custom protocol ที่เหมาะกับ application
- Better error handling

## Current Workaround Script:

```bash
#!/bin/bash
# reset_usbtmc.sh

echo "🔄 Resetting USBTMC device..."
ssh ben@192.168.9.75 "
  sudo rmmod usbtmc
  sleep 2
  sudo modprobe usbtmc
  sleep 2
  sudo chmod 666 /dev/usbtmc0
  echo '✅ USBTMC reset complete'
  ls -la /dev/usbtmc*
"

echo "🔄 Restarting SCPI server..."
bash deploy_pure_scpi.sh
```

## Monitoring Script:

```bash
#!/bin/bash
# monitor_scpi.sh

while true; do
  RESPONSE=$(echo "*IDN?" | timeout 3 nc 192.168.9.75 5025 2>/dev/null)
  if [ -z "$RESPONSE" ]; then
    echo "❌ Server timeout - resetting..."
    ./reset_usbtmc.sh
  else
    echo "✅ Server OK: $RESPONSE"
  fi
  sleep 10
done
```

## สรุป:
- USBTMC มีข้อจำกัดเรื่อง stability
- ต้องมี recovery mechanism
- สำหรับ production ควรใช้ Serial แทน
- STM32 H743 จะใช้ Serial = ปัญหานี้หายไป! 🎉

---
*แนะนำ: Unplug-replug USB cable เป็นวิธีที่ reliable ที่สุดตอนนี้*