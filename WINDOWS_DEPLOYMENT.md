# Windows PowerShell Deployment Guide

Bu kılavuz, EV Charging Simulation sistemini Windows lab ortamında 3 farklı PowerShell penceresinde çalıştırmak için hazırlanmıştır.

## 📋 Gereksinimler

- Windows 10/11
- Docker Desktop for Windows (WSL2 backend)
- PowerShell 5.1 veya üzeri
- Git for Windows (opsiyonel)

## 🚀 Hızlı Başlangıç

### PowerShell Script'lerini Çalıştırma İzni

PowerShell script'lerini ilk defa çalıştırmadan önce, execution policy'yi ayarlamanız gerekebilir:

```powershell
# PowerShell'i Administrator olarak açın ve şu komutu çalıştırın:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## 🔌 Senaryo 1: Yeni CP Ekleme (Runtime'da)

### PowerShell Penceresi #1: Ana Sistem

```powershell
# Sistemin çalıştığından emin olun
docker compose up -d

# Sistem durumunu kontrol edin
docker ps --filter "name=ev-" --format "table {{.Names}}`t{{.Status}}"

# Central dashboard'u kontrol edin
curl http://localhost:8000/cp
```

### PowerShell Penceresi #2: Yeni CP Ekleme

```powershell
# CP-011 ekle (150kW, €0.40/kWh)
.\add-cp.ps1 11 150.0 0.40

# CP-012 ekle (75kW, €0.35/kWh)
.\add-cp.ps1 12 75.0 0.35

# CP-015 ekle (default: 22kW, €0.30/kWh)
.\add-cp.ps1 15

# Eklenen CP'leri kontrol et
curl http://localhost:8000/cp | ConvertFrom-Json | 
    Select-Object -ExpandProperty charging_points | 
    Where-Object { $_.cp_id -match "CP-01[1-5]" }
```

### PowerShell Penceresi #3: CP Loglarını İzleme

```powershell
# CP-011 engine loglarını izle
docker logs -f ev-cp-e-11

# Veya monitor loglarını izle
docker logs -f ev-cp-m-11

# Veya Central loglarını izle
docker logs -f ev-central
```

## 🚗 Senaryo 2: Yeni Driver Ekleme (Runtime'da)

### PowerShell Penceresi #1: Ana Sistem

```powershell
# Mevcut driver'ları listele
docker ps --filter "name=ev-driver" --format "{{.Names}}"
```

### PowerShell Penceresi #2: Yeni Driver Ekleme

```powershell
# Driver Frank ekle (Dashboard: 8105)
.\add-driver.ps1 frank 8105

# Driver Grace ekle (Dashboard: 8106)
.\add-driver.ps1 grace 8106

# Driver Henry ekle (Dashboard: 8107)
.\add-driver.ps1 henry 8107

# Driver dashboard'larını aç
Start-Process "http://localhost:8105"
Start-Process "http://localhost:8106"
```

### PowerShell Penceresi #3: Driver Loglarını İzleme

```powershell
# Frank'in loglarını izle
docker logs -f ev-driver-frank

# Veya tüm driver'ların son loglarını göster
docker ps --filter "name=ev-driver" --format "{{.Names}}" | ForEach-Object {
    Write-Host "`n=== $_ ===" -ForegroundColor Cyan
    docker logs $_ --tail 5
}
```

## 💥 Senaryo 3: CP Çökmesi Simülasyonu

### PowerShell Penceresi #1: Sistem İzleme

```powershell
# Central dashboard'u sürekli izle
while ($true) {
    Clear-Host
    Write-Host "=== EV Charging System Status ===" -ForegroundColor Cyan
    Write-Host "Time: $(Get-Date -Format 'HH:mm:ss')" -ForegroundColor Yellow
    
    $status = curl -s http://localhost:8000/cp | ConvertFrom-Json
    Write-Host "`nTotal CPs: $($status.charging_points.Count)"
    Write-Host "Active Requests: $($status.active_requests)"
    
    $status.charging_points | Format-Table cp_id, state, monitor_status, current_driver -AutoSize
    
    Start-Sleep -Seconds 2
}
```

### PowerShell Penceresi #2: Çökme Simülasyonu

```powershell
# Belirli bir CP'yi çökert
.\simulate-crash.ps1 ev-cp-e-5

# Veya rastgele bir CP'yi çökert
.\simulate-crash.ps1

# 10 saniye bekle (monitor detection)
Start-Sleep -Seconds 10

# Central'ın hala çalıştığını kontrol et
docker ps --filter "name=ev-central"

# CP durumunu kontrol et
curl http://localhost:8000/cp | ConvertFrom-Json | 
    Select-Object -ExpandProperty charging_points | 
    Where-Object { $_.cp_id -eq "CP-005" } | 
    Format-List

# CP'yi yeniden başlat
docker start ev-cp-e-5
```

### PowerShell Penceresi #3: Log İzleme

```powershell
# Central loglarını canlı izle
docker logs -f ev-central | Select-String -Pattern "FAULT|ERROR|crash"

# Veya CP Monitor loglarını izle
docker logs -f ev-cp-m-5
```

## 🧪 Senaryo 4: Kapsamlı Test

### PowerShell Penceresi #1: Test Çalıştırma

```powershell
# Otomatik test script'ini çalıştır
.\test-cp-crash.ps1

# Veya belirli bir CP için test et
.\test-cp-crash.ps1 -TestCp "ev-cp-e-3" -TestCpId "CP-003"
```

### PowerShell Penceresi #2: Dashboard İzleme

```powershell
# Web tarayıcıda dashboard'u aç
Start-Process "http://localhost:8000"

# Veya JSON formatında sürekli izle
while ($true) {
    $status = curl -s http://localhost:8000/cp | ConvertFrom-Json
    Clear-Host
    Write-Host "=== Charging Points Status ===" -ForegroundColor Cyan
    $status.charging_points | 
        Select-Object cp_id, state, engine_state, monitor_status | 
        Format-Table -AutoSize
    Start-Sleep -Seconds 3
}
```

### PowerShell Penceresi #3: Container İzleme

```powershell
# Container durumlarını sürekli izle
while ($true) {
    Clear-Host
    docker ps --filter "name=ev-" --format "table {{.Names}}`t{{.Status}}`t{{.Ports}}"
    Start-Sleep -Seconds 5
}
```

## 🗑️ Temizlik İşlemleri

### Eklenen CP'leri Kaldırma

```powershell
# Belirli bir CP'yi kaldır
docker compose -f docker-compose.cp-11.yml down
Remove-Item docker-compose.cp-11.yml

# Tüm dinamik CP'leri kaldır
Get-ChildItem -Filter "docker-compose.cp-*.yml" | ForEach-Object {
    docker compose -f $_.Name down
    Remove-Item $_.Name
}
```

### Eklenen Driver'ları Kaldırma

```powershell
# Belirli bir driver'ı kaldır
docker compose -f docker-compose.driver-frank.yml down
Remove-Item docker-compose.driver-frank.yml

# Tüm dinamik driver'ları kaldır
Get-ChildItem -Filter "docker-compose.driver-*.yml" | ForEach-Object {
    docker compose -f $_.Name down
    Remove-Item $_.Name
}
```

### Tüm Sistemi Durdurma

```powershell
# Ana sistemi durdur
docker compose down

# Tüm container'ları temizle
docker ps -a --filter "name=ev-" --format "{{.Names}}" | ForEach-Object {
    docker rm -f $_
}

# Volume'ları temizle (opsiyonel)
docker volume prune -f
```

## 📊 Yararlı PowerShell Komutları

### Sistem Durumu Kontrolü

```powershell
# Çalışan container sayısı
$count = (docker ps --filter "name=ev-" --format "{{.Names}}").Count
Write-Host "Running EV containers: $count"

# CP'lerin durumu
$status = curl -s http://localhost:8000/cp | ConvertFrom-Json
Write-Host "Total CPs: $($status.charging_points.Count)"
Write-Host "Active Requests: $($status.active_requests)"

# ON durumundaki CP'ler
$onCps = $status.charging_points | Where-Object { $_.state -eq "ON" }
Write-Host "Available CPs: $($onCps.Count)"
```

### Log Analizi

```powershell
# Hataları ara
docker logs ev-central --tail 100 | Select-String -Pattern "ERROR|FAULT"

# Son 10 charging session'ı
docker logs ev-central --tail 200 | 
    Select-String -Pattern "Session.*started|completed" | 
    Select-Object -Last 10

# Monitor detection mesajları
docker logs ev-cp-m-5 --tail 50 | 
    Select-String -Pattern "FAULT|Health check"
```

### Performans Monitoring

```powershell
# Container resource kullanımı
docker stats --no-stream --filter "name=ev-" --format "table {{.Name}}`t{{.CPUPerc}}`t{{.MemUsage}}"

# Kafka mesaj sayısı
docker exec ev-kafka kafka-topics.sh --list --bootstrap-server localhost:9092
```

## 🔧 Troubleshooting

### Script Çalışmıyor

```powershell
# Execution policy'yi kontrol et
Get-ExecutionPolicy

# Eğer Restricted ise, değiştir:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Docker Connection Hatası

```powershell
# Docker Desktop'un çalıştığını kontrol et
docker version

# Docker service'i restart et (gerekirse)
Restart-Service docker
```

### Port Çakışması

```powershell
# Belirli bir portu kullanan process'i bul
Get-NetTCPConnection -LocalPort 8000 -State Listen

# Process'i kapat
Stop-Process -Id <PID>
```

### Network Hatası

```powershell
# Docker network'ü kontrol et
docker network ls

# Network'ü yeniden oluştur
docker network rm ev-charging-simulation-1_evcharging-network
docker compose up -d
```

## 📝 Lab Ortamı için İpuçları

### 3 PowerShell Penceresinde Çalışma

**Pencere 1 (Üst Sol) - Komut Merkezi:**
- Yeni CP/Driver ekleme
- Çökme simülasyonu
- Test script'leri çalıştırma

**Pencere 2 (Üst Sağ) - Monitoring:**
- Dashboard izleme
- Container durumu
- Sistem metrikleri

**Pencere 3 (Alt) - Log İzleme:**
- Central logs
- CP/Driver logs
- Hata mesajları

### Hızlı Test Senaryosu

```powershell
# Pencere 1: Sistem başlat
docker compose up -d

# Pencere 2: Dashboard izle
Start-Process "http://localhost:8000"

# Pencere 3: Logs izle
docker logs -f ev-central

# Pencere 1: Yeni CP ekle
.\add-cp.ps1 11 150.0 0.40

# Pencere 1: CP'yi çökert (10 saniye sonra)
Start-Sleep -Seconds 10
.\simulate-crash.ps1 ev-cp-e-11

# Tüm pencerelerde değişiklikleri gözlemle!
```

## 🎯 Grading Senaryoları

### Senaryo A: Dynamic Scaling
1. Sistem 10 CP ile başlasın
2. 3 yeni CP ekle (runtime)
3. 2 yeni driver ekle
4. Tüm CP'lerin Central'a kayıtlı olduğunu doğrula

### Senaryo B: Fault Tolerance
1. 1 CP çökert
2. Central'ın ayakta kaldığını doğrula
3. Diğer CP'lerin çalıştığını kontrol et
4. Çöken CP'yi restart et
5. Recovery'yi gözlemle

### Senaryo C: Multiple Failures
1. 3 CP'yi aynı anda çökert
2. Sistem stability'sini kontrol et
3. 1 driver'ı çökert
4. Tüm komponenti restart et

## 📚 Ek Kaynaklar

- Ana README: `README.md`
- Docker deployment: `QUICKSTART.md`
- Multi-machine setup: `MULTI_MACHINE_DEPLOYMENT_ANALYSIS.md`
- Crash resilience: `CRASH_RESILIENCE.md`
- Dynamic deployment: `DYNAMIC_DEPLOYMENT.md`

---

**Not:** Tüm PowerShell script'leri (`.ps1`) bash script'lerinin (`.sh`) tam karşılıkları olup, Windows ortamında sorunsuz çalışmaktadır.
