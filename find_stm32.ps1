# STM32 COM Port Detection Script
# Run this in PowerShell to find STM32 device

Write-Host "🔍 Scanning for STM32 devices..." -ForegroundColor Green

# Get all COM ports
$comPorts = Get-WmiObject -Class Win32_PnPEntity | Where-Object { $_.Caption -match "COM\d+" }

if ($comPorts) {
    Write-Host "`n📡 Found COM Ports:" -ForegroundColor Yellow
    Write-Host "-" * 50
    
    foreach ($port in $comPorts) {
        $comNumber = [regex]::Match($port.Caption, "COM(\d+)").Groups[1].Value
        Write-Host "COM$comNumber : $($port.Caption)" -ForegroundColor Cyan
        
        # Check if it looks like STM32
        if ($port.Caption -match "STM32|USB|Serial") {
            Write-Host "  ✅ Possible STM32 device!" -ForegroundColor Green
        }
    }
    
    Write-Host "`n🔧 To test SCPI commands, use one of these COM ports:"
    Write-Host "   python test_stm32_scpi.py" -ForegroundColor Yellow
    
} else {
    Write-Host "❌ No COM ports found!" -ForegroundColor Red
    Write-Host "Please check:" -ForegroundColor Yellow
    Write-Host "  1. STM32 is connected via USB" 
    Write-Host "  2. STM32 drivers are installed"
    Write-Host "  3. Device Manager shows the device"
}

Write-Host "`n📋 Device Manager Check:" -ForegroundColor Yellow
Write-Host "Press Win+X, select Device Manager, look under 'Ports (COM & LPT)'"