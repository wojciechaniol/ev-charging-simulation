# ⚡ EV Charging Simulation - Quick Start Guide

Bu kılavuz, projeyi **hem local (tek bilgisayar) hem de lab ortamı (3 Windows bilgisayar)** için nasıl çalıştıracağınızı gösterir.

---

## 🎯 İki Deployment Senaryosu

### Senaryo 1: Local Test (Tek Bilgisayar) ✅
**Kullanım:** Geliştirme, test, demo
- Tüm servisler tek makinede çalışır
- Docker Compose ile tek komut
- Hızlı başlatma ve durdurma
- Windows/macOS/Linux uyumlu

### Senaryo 2: Lab Deployment (3 Windows Bilgisayar) 🎓
**Kullanım:** Sınıf demosu, dağıtık sistem eğitimi
- 3 farklı bilgisayara dağıtılmış
- Gerçek ağ üzerinden iletişim
- Fault tolerance testi
- Windows lab ortamı için optimize edilmiş

---

## 🚀 Senaryo 1: Local Deployment (Tek Bilgisayar)

### Ön Gereksinimler:
- Docker Desktop kurulu ve çalışıyor
- 8 GB RAM (önerilen)
- Port 8000, 9092, 9999 boş

### Adım 1: Projeyi İndir

```bash
# Git ile
git clone https://github.com/Bariskosee/ev-charging-simulation.git
cd ev-charging-simulation

# VEYA ZIP indir ve klasöre git
```

### Adım 2: Tüm Servisleri Başlat

**macOS/Linux:**
```bash
# Tüm servisleri başlat (Kafka + Central + 5 CP + 5 Driver)
docker compose up -d

# Logları izle
docker compose logs -f

# Dashboard'u aç
open http://localhost:8000
```

**Windows PowerShell:**
```powershell
# Tüm servisleri başlat
docker compose up -d

# Logları izle
docker compose logs -f

# Dashboard'u aç
Start-Process "http://localhost:8000"
```

### Adım 3: Sistemi Doğrula

**Terminal'de:**
```bash
# Tüm servisler çalışıyor mu? (17 servis bekliyoruz)
docker ps

# CP'leri kontrol et (5 CP görmelisiniz)
curl http://localhost:8000/cp

# Driver dashboard'larını aç
# Alice: http://localhost:8100
# Bob: http://localhost:8101
# Charlie: http://localhost:8102
# David: http://localhost:8103
# Eve: http://localhost:8104
```

**PowerShell'de:**
```powershell
# Servis sayısı
(docker ps --format "{{.Names}}").Count

# CP'leri kontrol et
Invoke-WebRequest -Uri "http://localhost:8000/cp" | ConvertFrom-Json

# Tüm driver dashboard'larını aç
@(8100, 8101, 8102, 8103, 8104) | ForEach-Object { Start-Process "http://localhost:$_" }
```

### Adım 4: Servisleri Durdur

```bash
# Tüm servisleri durdur
docker compose down

# Volumes dahil tamamen temizle
docker compose down -v
```

---

## 🎓 Senaryo 2: Lab Deployment (3 Windows Bilgisayar)

### Mimari:

```
┌─────────────────────────────────┐
│ Makine 1: Kafka + Central      │  
│ IP: 192.168.1.105 (örnek)      │
│ Portlar: 9092, 8000, 9999      │
└─────────────────────────────────┘
            ↓ Network
┌─────────────────────────────────┐
│ Makine 2: 5 CP + 5 Monitor     │
│ Connects to: Makine 1          │
│ Servisler: 10 container         │
└─────────────────────────────────┘
            ↓ Network
┌─────────────────────────────────┐
│ Makine 3: 5 Drivers            │
│ Connects to: Makine 1          │
│ Servisler: 5 container          │
│ Dashboards: 8100-8104          │
└─────────────────────────────────┘
```

### Hızlı Başlangıç:

**Detaylı lab deployment kılavuzu için:**
👉 **[LAB_DEPLOYMENT_SUMMARY.md](LAB_DEPLOYMENT_SUMMARY.md)** dosyasına bakın

**Özet:**

1. **Makine 1** (Ana sunucu):
   ```powershell
   $env:KAFKA_ADVERTISED_HOST = "192.168.1.105"  # Kendi IP'niz
   docker compose up -d kafka
   Start-Sleep -Seconds 30
   docker compose up -d ev-central
   ```

2. **Makine 2** (Charging Points):
   ```powershell
   $env:KAFKA_BOOTSTRAP = "192.168.1.105:9092"
   $env:CENTRAL_HOST = "192.168.1.105"
   .\deploy-lab-cp.ps1  # Otomatik deployment
   ```

3. **Makine 3** (Drivers):
   ```powershell
   $env:KAFKA_BOOTSTRAP = "192.168.1.105:9092"
   $env:CENTRAL_HTTP_URL = "http://192.168.1.105:8000"
   .\deploy-lab-driver.ps1  # Otomatik deployment
   ```

---

## 📊 Servis Listesi

### Local Deployment (17 Servis):
| Servis | Port | Açıklama |
|--------|------|----------|
| kafka | 9092 | Message broker |
| ev-central | 8000, 9999 | Central controller + Dashboard |
| ev-cp-e-001 to 005 | 8001-8005 | 5 CP Engine |
| ev-cp-m-001 to 005 | - | 5 CP Monitor |
| ev-driver-alice | 8100 | Driver dashboard |
| ev-driver-bob | 8101 | Driver dashboard |
| ev-driver-charlie | 8102 | Driver dashboard |
| ev-driver-david | 8103 | Driver dashboard |
| ev-driver-eve | 8104 | Driver dashboard |

### Lab Deployment (17 Servis - 3 makineye dağıtılmış):
- **Makine 1**: 2 servis (Kafka + Central)
- **Makine 2**: 10 servis (5 CP Engine + 5 Monitor)
- **Makine 3**: 5 servis (5 Driver)

---

## 🔍 Monitoring & Debugging

### Central Dashboard
- **URL**: http://localhost:8000 (local) veya http://192.168.1.105:8000 (lab)
- **Özellikler**:
  - CP durumları (ACTIVATED, CHARGING, FAULTY)
  - Aktif charging sessions
  - Real-time telemetri
  - Sistem sağlık durumu

### Driver Dashboards (5 adet)
- **Alice**: http://localhost:8100
- **Bob**: http://localhost:8101
- **Charlie**: http://localhost:8102
- **David**: http://localhost:8103
- **Eve**: http://localhost:8104

### Logları İzleme

**Tüm servisleri izle:**
```bash
docker compose logs -f
```

**Belirli servisleri izle:**
```bash
# Central
docker logs -f ev-central

# CP Engine
docker logs -f ev-cp-e-001

# Driver
docker logs -f ev-driver-alice

# Kafka
docker logs -f kafka
```

---

## 🧪 Test Senaryoları

### Test 1: Normal Çalışma
```bash
# Dashboard'u aç
open http://localhost:8000  # macOS
Start-Process http://localhost:8000  # Windows

# CP'lerin ACTIVATED olduğunu doğrula
curl http://localhost:8000/cp

# Driver'ların şarj isteği gönderdiğini izle
docker logs -f ev-driver-alice
```

### Test 2: Fault Tolerance
```bash
# Bir CP'yi crash et
docker stop ev-cp-e-003

# Dashboard'dan FAULTY durumunu gözlemle (30 saniye bekle)

# CP'yi recover et
docker start ev-cp-e-003

# ACTIVATED durumuna dönüşünü izle
```

### Test 3: Load Testing
```bash
# Driver sayısını artır
docker compose up -d --scale ev-driver-alice=3

# Yükü izle
docker stats
```

---

## 🛠️ Sorun Giderme

### Problem: "Port already in use"
```bash
# Portları kontrol et
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Çözüm: Başka bir port kullan veya çakışan servisi durdur
```

### Problem: "Cannot connect to Kafka"
```bash
# Kafka'nın çalıştığını doğrula
docker ps | grep kafka

# Kafka loglarını kontrol et
docker logs kafka

# Çözüm: 30 saniye bekle, Kafka başlatma süresi gerekir
```

### Problem: "CP Dashboard'da görünmüyor"
```bash
# CP loglarını kontrol et
docker logs ev-cp-e-001

# Monitor loglarını kontrol et
docker logs ev-cp-m-001

# Çözüm: CP'yi yeniden başlat
docker restart ev-cp-e-001 ev-cp-m-001
```

---

## 📚 İleri Seviye Kullanım

### Custom Configuration
```bash
# .env dosyası oluştur
cp .env.example .env

# Ayarları düzenle
nano .env

# Değişikliklerle başlat
docker compose up -d
```

### Development Mode
```bash
# Python dependencies kur
pip install -r requirements.txt

# Local'de çalıştır (Kafka Docker'da)
python -m evcharging.apps.ev_central.main
```

### Performance Tuning
```bash
# Docker resource limitleri
docker stats

# Kafka partition sayısını artır
# docker-compose.yml'de KAFKA_NUM_PARTITIONS değiştir
```

---

## 📖 Ek Kaynaklar

- **[LAB_DEPLOYMENT_SUMMARY.md](LAB_DEPLOYMENT_SUMMARY.md)** - 3 Windows bilgisayar lab deployment
- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Kapsamlı deployment seçenekleri
- **[DRIVER_DASHBOARD_API.md](DRIVER_DASHBOARD_API.md)** - Driver API referansı
- **[TCP_FRAMING_PROTOCOL.md](TCP_FRAMING_PROTOCOL.md)** - TCP protokol detayları
- **[FAULT_TOLERANCE.md](FAULT_TOLERANCE.md)** - Fault tolerance mekanizmaları

---

## 🎯 Hızlı Komutlar Özeti

### Local (Tek Bilgisayar):
```bash
# Başlat
docker compose up -d

# İzle
docker compose logs -f

# Dashboard
open http://localhost:8000

# Durdur
docker compose down
```

### Lab (3 Bilgisayar):
```powershell
# Makine 1
$env:KAFKA_ADVERTISED_HOST = "192.168.1.105"
docker compose up -d kafka ev-central

# Makine 2
.\deploy-lab-cp.ps1

# Makine 3
.\deploy-lab-driver.ps1
```

---

**🚀 Başarılar! Projeniz hem local test hem de lab deployment için hazır!**

**Son Güncelleme:** 28 Ekim 2025  
**Versiyon:** 1.0
