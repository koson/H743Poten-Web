# CV Plotting Issues

## Issue 1: Unwanted Connecting Lines in CV Plots

### Description
มีเส้นเชื่อมแปลกๆ ที่ลากจากจุด upper potential ไปยัง lower potential ในกราฟ Cyclic Voltammetry

### Current Status
- ✅ ข้อมูลจาก STM32 มาครบถ้วน
- ✅ Backend processing ทำงานถูกต้อง  
- ✅ Frontend แสดงช่วง voltage เต็มรูปแบบแล้ว (รวม negative voltages)
- ✅ Data synchronization ระหว่าง backend-frontend แก้ไขแล้ว
- ❌ ยังคงมีเส้นเชื่อมระหว่าง forward และ reverse scans

### Attempted Solutions
1. ใช้ `connectgaps: false`
2. แยก forward และ reverse เป็น traces แยกกัน
3. เพิ่ม null separators ระหว่าง scans
4. ใช้ `mode: 'markers+lines'` กับ invisible markers
5. กำหนด `line.shape: 'linear'` อย่างชัดเจน
6. ใช้ null terminators ที่ท้าย traces

### Technical Details
- File: `static/js/cv_measurement.js`
- Function: `updatePlot()` lines ~683-745
- Library: Plotly.js
- Data structure: Separate traces for forward/reverse with explicit sorting

### Possible Root Causes
1. Plotly.js internal behavior ที่เชื่อม traces ที่มี color เดียวกัน
2. Browser rendering engine issues
3. Data point ordering หรือ timing issues
4. Plotly.js version compatibility

### Future Investigation
- ลองใช้ Plotly.js version อื่น
- ทดสอบกับ library อื่น (Chart.js, D3.js)
- ตรวจสอบ data structure และ timing ของการ update
- ลอง redraw ทั้งหมดแทนการ update

### Workaround
ปัจจุบันระบบทำงานได้ปกติ มีเพียงเส้นเชื่อมแปลกๆ ที่ไม่ส่งผลต่อการอ่านข้อมูล CV curve

---
Date: August 15, 2025
Priority: Low (Cosmetic issue)
Status: Deferred
