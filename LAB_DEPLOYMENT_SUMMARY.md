# 🎓 EV Charging Simulation - 3 Windows Bilgisayar Laboratuvar Dağıtım Kılavuzu

Bu kılavuz, EV Charging Simulation sistemini laboratuvardaki 3 farklı Windows bilgisayara (okul kablolu ağı üzerinden) nasıl dağıtacağınızı adım adım gösterir.

> **💡 Not:** Tek bilgisayarda test etmek için **[QUICKSTART.md](QUICKSTART.md)** dosyasına bakın.  
> Bu kılavuz sadece **lab ortamı (3 Windows bilgisayar)** için geçerlidir.

---

## 📊 Sistem Yapısı

### Toplam Servis Sayısı: **17 Servis**

```
┌─────────────────────────────────────────────────────────┐
│  Makine 1 (Ana Sunucu)                                  │
│  - 1 Kafka Broker                                       │
│  - 1 Central Controller (Dashboard + TCP)              │
│  Toplam: 2 servis                                       │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  Makine 2 (Lab PC 1 - Şarj İstasyonları)               │
│  - 5 CP Engine (CP-001 to CP-005)                      │
│  - 5 CP Monitor (Health Checking)                      │
│  Toplam: 10 servis                                      │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  Makine 3 (Lab PC 2 - Sürücüler)                       │
│  - 5 Driver İstemcisi (Alice, Bob, Charlie, David, Eve)│
│  Toplam: 5 servis                                       │
└─────────────────────────────────────────────────────────┘
```

---

## ⚡ Şarj İstasyonu Detayları (5 CP)

| CP ID  | Güç (kW) | Fiyat (€/kWh) | Port | Açıklama        |
|--------|----------|---------------|------|-----------------|
| CP-001 | 22.0     | 0.30          | 8001 | Standart AC     |
| CP-002 | 50.0     | 0.35          | 8002 | Hızlı DC        |
| CP-003 | 43.0     | 0.32          | 8003 | Orta Seviye     |
| CP-004 | 150.0    | 0.40          | 8004 | Ultra Hızlı DC  |
| CP-005 | 7.2      | 0.28          | 8005 | Yavaş AC (Gece) |

---

## 🚗 Sürücü Detayları (5 Driver)

| Sürücü ID      | Dashboard Port | İstek Aralığı | Davranış Profili      |
|----------------|----------------|---------------|-----------------------|
| driver-alice   | 8100           | 5.0 saniye    | Dengeli kullanım      |
| driver-bob     | 8101           | 6.0 saniye    | Sakin kullanıcı       |
| driver-charlie | 8102           | 7.0 saniye    | Ara sıra kullanım     |
| driver-david   | 8103           | 8.0 saniye    | Hafta sonu kullanıcı  |
| driver-eve     | 8104           | 4.5 saniye    | Yoğun kullanım (Taksi)|

---

## � Ağ Gereksinimleri

### Tüm 3 Bilgisayar İçin:
1. ✅ Aynı yerel ağda (LAN) olmalı (örn: 192.168.1.x)
2. ✅ Firewall izinleri gerekli portlar için açık olmalı
3. ✅ Docker/Docker Desktop kurulu ve çalışıyor olmalı
4. ✅ Terminal/PowerShell erişimi

### Gerekli Portlar:
- **Makine 1**: 9092 (Kafka), 8000 (Dashboard), 9999 (TCP)
- **Makine 2**: Dış bağlantı yok (sadece outbound) - 5 CP Engine + 5 Monitor
- **Makine 3**: 8100-8104 (5 Driver dashboards - Alice, Bob, Charlie, David, Eve)

---

## �🚀 Kurulum Adımları

### 0️⃣ Ön Hazırlık (Tüm Windows Bilgisayarlarda)

#### Docker Desktop Kurulumu:

**Tüm 3 makinede aşağıdaki adımları takip edin:**

1. [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/) indir
2. İndir ve bilgisayarı yeniden başlat
3. Docker Desktop'ı aç ve **WSL 2 backend'i etkinleştir** (daha performanslı)
4. Docker Desktop'ın sistem tray'de çalıştığından emin olun

**Docker kurulumunu doğrula:**
```powershell
# PowerShell'de test et
docker --version
docker compose version
```

#### Proje Dosyalarını Kopyala (Tüm Makinelerde):

```powershell
# Git kullanarak (önerilir)
git clone https://github.com/Bariskosee/ev-charging-simulation.git
cd ev-charging-simulation

# VEYA ZIP olarak indir ve çıkar
# 1. https://github.com/Bariskosee/ev-charging-simulation/archive/refs/heads/main.zip
# 2. ZIP'i çıkar
# 3. PowerShell'de klasöre git
```

---

### 1️⃣ Makine 1 Kurulumu (Ana Bilgisayar)

#### Adım 1.1: IPv4 Adresini Bul

**PowerShell'de (ÖNERİLİR):**
```powershell
# Ethernet bağlantısının IPv4 adresini bul
(Get-NetIPAddress -AddressFamily IPv4 -InterfaceAlias "Ethernet*" | Where-Object {$_.IPAddress -like "192.168.*" -or $_.IPAddress -like "10.*"}).IPAddress
```

**Command Prompt'ta (Alternatif):**
```cmd
ipconfig | findstr /i "IPv4"
```

**Örnek Çıktı:**
```
192.168.1.105
```

**⚠️ ÖNEMLİ:** 
- Bu IP adresini **NOT EDİN** - diğer 2 makinede kullanacaksınız! 📝
- Okul ağı 10.x.x.x kullanıyorsa ona göre not edin
- Öğretmen/yönetici IP aralığını onaylasın

---

#### Adım 1.2: docker-compose.yml Dosyasını Kontrol Et

Projenizin ana dizininde `docker-compose.yml` dosyası zaten yapılandırılmış durumda:

```yaml
kafka:
  image: apache/kafka:3.7.0
  container_name: ev-kafka
  ports:
    - "9092:9092"
  environment:
    KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://${KAFKA_ADVERTISED_HOST:-localhost}:9092
    KAFKA_CONTROLLER_QUORUM_VOTERS: 1@localhost:9093
    # ... diğer ayarlar
```

**Not:** `KAFKA_ADVERTISED_HOST` environment variable ile dış IP kullanımı destekleniyor.

---

#### Adım 1.3: Windows Firewall Yapılandırması

**PowerShell'i Yönetici Olarak Aç:**
1. Başlat menüsünde "PowerShell" ara
2. Sağ tık → "Run as Administrator"

**Gerekli portları aç:**
```powershell
# Kafka için port 9092'yi aç
New-NetFirewallRule -DisplayName "EV Charging - Kafka Port 9092" -Direction Inbound -LocalPort 9092 -Protocol TCP -Action Allow

# Central Dashboard için port 8000'i aç
New-NetFirewallRule -DisplayName "EV Charging - Central Dashboard 8000" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow

# TCP Server için port 9999'u aç
New-NetFirewallRule -DisplayName "EV Charging - TCP Server 9999" -Direction Inbound -LocalPort 9999 -Protocol TCP -Action Allow
```

**Firewall kurallarını doğrula:**
```powershell
# Kuralların eklendiğini kontrol et
Get-NetFirewallRule -DisplayName "EV Charging*" | Select-Object DisplayName, Enabled, Direction
```

**Alternatif: Windows GUI İle:**
1. `Control Panel` → `Windows Defender Firewall` → `Advanced Settings`
2. `Inbound Rules` → `New Rule`
3. `Port` seç → `TCP` → `9092, 8000, 9999` portlarını ekle
4. `Allow the connection` → `Apply`

---

#### Adım 1.4: Servisleri Başlat

**PowerShell'de (Normal kullanıcı - yönetici değil):**

```powershell
# IPv4 adresini environment variable olarak ayarla
$env:KAFKA_ADVERTISED_HOST = "192.168.1.105"  # ⬅️ KENDİ IP'NİZİ YAZIN!

# Kafka'yı başlat
docker compose up -d kafka

# Kafka'nın hazır olmasını bekle (30 saniye)
Start-Sleep -Seconds 30

# Kafka'nın başarıyla başladığını kontrol et
docker logs ev-kafka | Select-String "started (kafka.server.KafkaRaftServer)"

# Central Controller'ı başlat
docker compose up -d ev-central

# Servislerin durumunu kontrol et
docker compose ps
```

**Beklenen Çıktı:**
```
NAME          IMAGE                     STATUS         PORTS
ev-kafka      apache/kafka:3.7.0        Up (healthy)   0.0.0.0:9092->9092/tcp
ev-central    ev-charging-...-central   Up             0.0.0.0:8000->8000/tcp, 0.0.0.0:9999->9999/tcp
```

---

#### Adım 1.5: Sistem Sağlığını Doğrula

**PowerShell'de:**
```powershell
# Central Dashboard'u kontrol et
Invoke-WebRequest -Uri "http://localhost:8000/health" | Select-Object -ExpandProperty Content

# Kafka bağlantısını test et
docker exec ev-kafka kafka-broker-api-versions.sh --bootstrap-server localhost:9092
```

**Beklenen Sağlık Durumu:**
```json
{
  "status": "healthy",
  "service": "ev-central",
  "kafka_producer": "connected",
  "kafka_consumer": "connected",
  "timestamp": "2025-10-28T..."
}
```

---

#### Adım 1.6: IP Adresini Paylaş

**PowerShell'de:**
```powershell
Write-Host "==================================="
Write-Host "Kafka ve Central IP: $env:KAFKA_ADVERTISED_HOST"
Write-Host "Dashboard URL: http://$env:KAFKA_ADVERTISED_HOST:8000"
Write-Host "==================================="
Write-Host "Bu IP'yi diğer 2 makineye verin!"
```

**Bu bilgileri diğer 2 lab bilgisayarına gönderin! 📤**

**İpucu:** IP'yi not kağıdına yazın veya WhatsApp/Teams'te paylaşın

---

### 2️⃣ Makine 2 Kurulumu (Charging Points)

#### Adım 2.1: Environment Variables Ayarla

**Makine 1'den aldığınız IP adresini kullanın:**

```powershell
# Makine 1'in IP adresi (arkadaşınızdan/öğretmenden aldığınız)
$env:KAFKA_BOOTSTRAP = "192.168.1.105:9092"      # ⬅️ Makine 1 IP
$env:CENTRAL_HOST = "192.168.1.105"              # ⬅️ Makine 1 IP
$env:CENTRAL_PORT = "8000"
```

---

#### Adım 2.2: Bağlantıyı Test Et

**PowerShell'de:**
```powershell
# Kafka'ya erişimi test et
docker run --rm confluentinc/cp-kafka:latest `
  kafka-broker-api-versions --bootstrap-server $env:KAFKA_BOOTSTRAP

# Central Dashboard'a erişimi test et
Invoke-WebRequest -Uri "http://$($env:CENTRAL_HOST):8000/health"
```

**Eğer hata alırsanız:**
- ✅ Makine 1'in firewall ayarlarını kontrol edin
- ✅ IP adresinin doğru olduğunu onaylayın
- ✅ İki bilgisayarın aynı kablolu ağda olduğunu doğrulayın (öğretmen/network admin'e sorun)

---

#### Adım 2.3: Network Oluşturma (ÖNEMLİ!)

**İlk önce Docker network'ü oluşturun:**
```powershell
# Makine 2'de (CP bilgisayarında)
# Network'ün var olup olmadığını kontrol et
docker network ls | Select-String "evcharging-network"

# Eğer yoksa oluştur (Makine 1'deki ile aynı isimde olmalı)
docker network create ev-charging-simulation-1_evcharging-network

# Network'ü doğrula
docker network inspect ev-charging-simulation-1_evcharging-network
```

**⚠️ ÖNEMLİ:** Bu network Makine 1'de otomatik oluşur ama Makine 2 ve 3'te manuel oluşturulmalı!

---

#### Adım 2.4: Charging Point Servislerini Başlat

**PowerShell Script ile (ÖNERİLİR):**
```powershell
# Quick deployment script kullan (otomatik bağlantı testi dahil)
.\deploy-lab-cp.ps1
```

**Manuel PowerShell:**
```powershell
# Environment variables'ların ayarlandığından emin olun
Write-Host "KAFKA_BOOTSTRAP: $env:KAFKA_BOOTSTRAP"
Write-Host "CENTRAL_HOST: $env:CENTRAL_HOST"

# 5 CP Engine ve 5 Monitor servisini başlat (toplamda 10 servis)
docker compose -f docker/docker-compose.remote-kafka.yml up -d `
  ev-cp-e-001 ev-cp-e-002 ev-cp-e-003 ev-cp-e-004 ev-cp-e-005 `
  ev-cp-m-001 ev-cp-m-002 ev-cp-m-003 ev-cp-m-004 ev-cp-m-005

# Servislerin durumunu kontrol et (10 servis görmelisiniz)
docker compose -f docker/docker-compose.remote-kafka.yml ps

# Tüm CP'lerin çalıştığını doğrula
docker ps --filter "name=ev-cp" --format "table {{.Names}}\t{{.Status}}"
```

**Beklenen Çıktı:** 10 container (5 engine + 5 monitor) "Up" durumda olmalı

---

#### Adım 2.4: CP Loglarını Kontrol Et

**PowerShell'de:**
```powershell
# CP Engine başarıyla başladı mı?
docker logs ev-cp-e-1 | Select-String "started successfully|ACTIVATED"

# CP Monitor çalışıyor mu?
docker logs ev-cp-m-1 | Select-String "heartbeat|Monitoring CP-001"
```

**Beklenen CP Engine Logları:**
```
✅ Kafka producer started: 192.168.1.105:9092
✅ Kafka consumer started: topics=['central.commands']
✅ CP CP-001: CPState.DISCONNECTED + CPEvent.CONNECT -> CPState.ACTIVATED
✅ CP Engine CP-001 started successfully
```

**Beklenen Monitor Logları:**
```
✅ Monitoring CP-001 at ev-cp-e-1:8001
✅ Central heartbeat sent successfully
✅ Health check: CP-001 is HEALTHY
```

---

#### Adım 2.5: Makine 1'den CP'leri Doğrula

**Makine 1'de (Ana Bilgisayar) PowerShell:**
```powershell
# Dashboard'dan CP'leri kontrol et
Invoke-WebRequest -Uri "http://localhost:8000/cp" | ConvertFrom-Json | Select-Object -ExpandProperty charging_points
```

**CP-001 to CP-005 görmelisiniz! (Toplamda 5 CP + 5 Monitor = 10 servis)** 🎉

---

### 3️⃣ Makine 3 Kurulumu (Drivers)

#### Adım 3.1: Environment Variables Ayarla

**PowerShell'de:**
```powershell
# Makine 1'in IP adresi (arkadaşınızdan/öğretmenden aldığınız)
$env:KAFKA_BOOTSTRAP = "192.168.1.105:9092"                    # ⬅️ Makine 1 IP
$env:CENTRAL_HTTP_URL = "http://192.168.1.105:8000"            # ⬅️ Makine 1 IP
```

---

#### Adım 3.2: Bağlantıyı Test Et

**PowerShell'de:**
```powershell
# Central Dashboard'a erişimi test et
Invoke-WebRequest -Uri "$env:CENTRAL_HTTP_URL/health"

# Mevcut CP'leri görüntüle
Invoke-WebRequest -Uri "$env:CENTRAL_HTTP_URL/cp" | ConvertFrom-Json | Select-Object -ExpandProperty charging_points | Select-Object cp_id, state, engine_state
```

---

#### Adım 3.3: Driver Servislerini Başlat

**PowerShell Script ile (ÖNERİLİR):**
```powershell
# Quick deployment script kullan (otomatik bağlantı testi dahil)
.\deploy-lab-driver.ps1
```

**Manuel PowerShell:**
```powershell
# 5 Driver servisini başlat (Alice, Bob, Charlie, David, Eve)
docker compose -f docker/docker-compose.remote-kafka.yml up -d `
  ev-driver-alice ev-driver-bob ev-driver-charlie ev-driver-david ev-driver-eve

# Servislerin durumunu kontrol et (5 driver görmelisiniz)
docker compose -f docker/docker-compose.remote-kafka.yml ps

# Tüm driver'ların çalıştığını doğrula
docker ps --filter "name=ev-driver" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

**Beklenen Çıktı:** 5 container "Up" durumda, portlar 8100-8104 mapped olmalı

---

#### Adım 3.4: Windows Firewall (Driver Dashboards için - Opsiyonel)

Eğer driver dashboard'larına diğer bilgisayarlardan erişmek isterseniz (örneğin öğretmen herkesi izlemek istiyorsa):

**PowerShell (Yönetici olarak):**
```powershell
# Driver dashboard portlarını aç (8100-8104)
New-NetFirewallRule -DisplayName "EV Charging - Driver Dashboards" -Direction Inbound -LocalPort 8100-8104 -Protocol TCP -Action Allow
```

**Not:** Genellikle gerekli değildir - sadece localhost'tan erişilir.

---

#### Adım 3.5: Driver Loglarını Kontrol Et

**PowerShell'de:**
```powershell
# Driver başarıyla başladı mı?
docker logs ev-driver-alice | Select-String "started|requested charging|ACCEPTED"
```

**Beklenen Driver Logları:**
```
✅ Starting Driver client: driver-alice
✅ Kafka producer started: 192.168.1.105:9092
✅ Kafka consumer started: topics=['driver.updates']
✅ Driver driver-alice started successfully
✅ 📤 Driver driver-alice requested charging at CP-001
✅ ✅ ACCEPTED | Request accepted, starting charging
✅ 🔋 IN_PROGRESS | Charging: 22.0 kW, €0.02
```

---

#### Adım 3.6: Driver Dashboard'lara Erişim

**PowerShell'de:**
```powershell
# Tüm driver dashboard'larını browser'da aç
Start-Process "http://localhost:8100"  # Alice
Start-Process "http://localhost:8101"  # Bob
Start-Process "http://localhost:8102"  # Charlie
Start-Process "http://localhost:8103"  # David
Start-Process "http://localhost:8104"  # Eve

# Veya API üzerinden hepsini kontrol et
@(8100, 8101, 8102, 8103, 8104) | ForEach-Object {
    Write-Host "`nDriver Dashboard Port $_:"
    Invoke-WebRequest -Uri "http://localhost:$_/health" | ConvertFrom-Json
}
```

---

## ✅ Doğrulama Kontrol Listesi

### Makine 1 Kontrolleri:

**PowerShell:**
```powershell
# ✅ Kafka çalışıyor mu?
docker ps --filter "name=ev-kafka"

# ✅ Central çalışıyor mu?
docker ps --filter "name=ev-central"

# ✅ Kafka external'den erişilebilir mi?
docker exec ev-kafka kafka-broker-api-versions.sh --bootstrap-server localhost:9092

# ✅ CP'ler kaydedildi mi? (5 adet olmalı)
$cps = Invoke-WebRequest -Uri "http://localhost:8000/cp" | ConvertFrom-Json | Select-Object -ExpandProperty charging_points
Write-Host "Toplam CP Sayısı: $($cps.Count)"
$cps | Select-Object cp_id, state, engine_state, kw_rate | Format-Table
```

---

### Makine 2 Kontrolleri:

**PowerShell:**
```powershell
# ✅ CP Engine'ler çalışıyor mu?
docker ps --filter "name=ev-cp-e"

# ✅ CP Monitor'ler çalışıyor mu?
docker ps --filter "name=ev-cp-m"

# ✅ Kafka'ya bağlandılar mı?
docker logs ev-cp-e-001 | Select-String "Kafka producer started"
docker logs ev-cp-m-001 | Select-String "heartbeat sent successfully"
```

---

### Makine 3 Kontrolleri:

**PowerShell:**
```powershell
# ✅ Driver'lar çalışıyor mu?
docker ps --filter "name=ev-driver"

# ✅ Alice Kafka'ya bağlandı mı?
docker logs ev-driver-alice | Select-String "Kafka producer started"

# ✅ Alice şarj isteği gönderiyor mu?
docker logs ev-driver-alice | Select-String "requested charging"

# ✅ Dashboard'lar erişilebilir mi?
@(8100, 8101, 8102, 8103, 8104) | ForEach-Object {
    Write-Host "`nPort $_:"
    (Invoke-WebRequest -Uri "http://localhost:$_/health" | ConvertFrom-Json).status
}
```

# ✅ Kafka'ya bağlandılar mı?
docker logs ev-driver-alice | Select-String "Kafka producer started"

# ✅ Charging request gönderebildiler mi?
docker logs ev-driver-alice | Select-String "requested charging"

# ✅ Dashboard'lar erişilebilir mi?
@(8100, 8101, 8102, 8103, 8104) | ForEach-Object {
    $port = $_
    Write-Host "Port ${port}:"
    curl -s "http://localhost:${port}/health" | ConvertFrom-Json | Select-Object status
}
```

---

## 🎯 Test Senaryoları

### Senaryo 1: Normal İşleyiş (Gözlem)
**Amaç:** Sistemin otonom çalıştığını doğrula

1. **Makine 1**: Dashboard'u aç → `http://localhost:8000`
2. **Makine 2**: CP loglarını izle → `docker logs -f ev-cp-e-1`
3. **Makine 3**: Driver loglarını izle → `docker logs -f ev-driver-alice`

**Beklenen Sonuç:**
- Dashboard'da 5 CP ACTIVATED durumda
- Driver'lar sürekli şarj isteği gönderiyor
- CP'ler şarj session'larını başlatıyor ve telemetri gönderiyor

---

### Senaryo 2: CP Fault Injection
**Amaç:** Fault tolerance mekanizmalarını test et

**PowerShell:**
```powershell
# Makine 2'de bir CP'yi crash et
docker stop ev-cp-e-003

# Bekle: 30 saniye
Start-Sleep -Seconds 30

# Makine 1'de Dashboard'dan gözlemle:
# CP-003 durumu: ACTIVATED → FAULTY

# Makine 2'de recover et:
docker start ev-cp-e-003

# Bekle: 10 saniye
Start-Sleep -Seconds 10

# Makine 1'de Dashboard'dan gözlemle:
# CP-003 durumu: FAULTY → ACTIVATED
```

# Makine 1'de dashboard'dan gözlemle
# CP-003 durumu FAULTY olacak

# 30 saniye bekle, sonra recover et
Start-Sleep -Seconds 30
docker start ev-cp-e-3
```

---

### Senaryo 3: Eşzamanlı Şarj Testleri
**Amaç:** 5 driver'ın aynı anda farklı CP'lerde şarj yapabildiğini göster

**PowerShell:**
```powershell
# Makine 3'te tüm driver'ların loglarını izle (ayrı terminal pencerelerinde):
docker logs -f ev-driver-alice
docker logs -f ev-driver-bob
docker logs -f ev-driver-charlie
docker logs -f ev-driver-david
docker logs -f ev-driver-eve

# Veya hepsini birden görmek için:
Get-Process | Where-Object {$_.Name -eq "powershell"} | ForEach-Object {
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "docker logs -f ev-driver-alice"
}

# Makine 1'de Dashboard'dan gözlemle:
# - 5 aktif session aynı anda
# - Farklı CP'ler farklı güç seviyeleri gösteriyor
# - Her driver kendi dashboard'unda charging progress gösteriyor
```

---

### Senaryo 4: Load Testing
**Amaç:** Sistemi yük altında test et

**PowerShell:**
```powershell
# Makine 3'te driver'ları daha agresif yapabilirsin:
# docker-compose.remote-kafka.yml'de interval'ları düşür (örn: 2.0 saniye)

# Veya daha fazla driver ekle:
docker compose -f docker/docker-compose.remote-kafka.yml up -d --scale ev-driver-alice=3
```

---

## 🔧 Sorun Giderme

### Problem: "Connection refused to Kafka"

**Belirtiler:**
```
ERROR: Failed to connect to Kafka at 192.168.1.105:9092
```

**Çözüm (Makine 1'de) - Windows PowerShell:**
```powershell
# Firewall kuralını kontrol et
Get-NetFirewallRule -DisplayName "Kafka Port 9092"

# Eğer yoksa ekle
New-NetFirewallRule -DisplayName "Kafka Port 9092" -Direction Inbound -LocalPort 9092 -Protocol TCP -Action Allow

# Kafka'nın 0.0.0.0'da dinlediğini doğrula
docker exec ev-kafka netstat -tuln | Select-String "9092"
# Görmeli: 0.0.0.0:9092 (127.0.0.1:9092 DEĞİL!)

# Network connectivity test et (Makine 2 veya 3'ten)
Test-NetConnection -ComputerName 192.168.1.105 -Port 9092
# Beklenen: TcpTestSucceeded : True
```

---

### Problem: "CP Dashboard'da görünmüyor"

> **📚 Detaylı troubleshooting için:** [TROUBLESHOOTING_GUIDE.md](TROUBLESHOOTING_GUIDE.md)  
> Bu guide tüm yaygın problemleri, sebeplerini ve çözümlerini içerir.

**Belirtiler:**
- Makine 2'de CP container'ları çalışıyor (`docker ps` ile görünüyor)
- Ama Makine 1'de Central dashboard'da CP listesi boş

**Hızlı Kontrol - Yeni deploy scriptleri otomatik diagnose yapar:**

```powershell
# Güncellenmiş script ile deploy et
.\deploy-lab-cp.ps1

# Script şunları otomatik kontrol eder:
# ✅ Docker network var mı?
# ✅ CP Monitor kayıt başarılı mı?
# ✅ Central'a erişilebiliyor mu?
# ❌ Problemler varsa diagnostic komutlar gösterir
```

**Manuel Troubleshooting:**

**Sebep 1: Network Connectivity**

**Çözüm (Makine 2'de) - Windows PowerShell:**
```powershell
# ADIM 1: Environment variables kontrol
Write-Host "KAFKA_BOOTSTRAP: $env:KAFKA_BOOTSTRAP"
Write-Host "CENTRAL_HOST: $env:CENTRAL_HOST"
Write-Host "CENTRAL_PORT: $env:CENTRAL_PORT"

# Eğer boşsa tekrar ayarla (Makine 1'in IP'si)
$env:KAFKA_BOOTSTRAP = "192.168.1.105:9092"      # ⬅️ DEĞİŞTİR
$env:CENTRAL_HOST = "192.168.1.105"              # ⬅️ DEĞİŞTİR
$env:CENTRAL_PORT = "8000"

# ADIM 2: Network bağlantısını test et
Test-NetConnection -ComputerName $env:CENTRAL_HOST -Port 8000
# Beklenen: TcpTestSucceeded : True

# ADIM 3: Central'a HTTP request gönder
Invoke-WebRequest -Uri "http://$($env:CENTRAL_HOST):8000/health" -UseBasicParsing

# ADIM 4: CP Monitor loglarını kontrol et
docker logs ev-cp-m-001 --tail 30

# Aranacak mesajlar:
# ✅ "CP CP-001 registered with Central successfully"
# ✅ "Central heartbeat sent successfully"
# ❌ "Failed to register" veya "Connection refused" → Problem var!
```

**Sebep 2: Firewall Engelleme**

**Çözüm (Makine 1'de) - PowerShell (Yönetici):**
```powershell
# Port 8000 için inbound rule ekle
New-NetFirewallRule -DisplayName "EV Charging - Central HTTP 8000" `
    -Direction Inbound `
    -LocalPort 8000 `
    -Protocol TCP `
    -Action Allow

# Kuralın eklendiğini doğrula
Get-NetFirewallRule -DisplayName "EV Charging - Central HTTP 8000"

# Test: Makine 2'den Makine 1'e erişim
# Makine 2'de çalıştır:
Invoke-WebRequest -Uri "http://192.168.1.105:8000/health"
```

**Sebep 3: Container'lar Yanlış Environment Variables Kullanıyor**

**Çözüm (Makine 2'de):**
```powershell
# Container'ların environment variables'larını kontrol et
docker inspect ev-cp-m-001 | Select-String "CP_MONITOR_CENTRAL_HOST|CENTRAL_HOST"

# Yanlış IP görürseniz container'ları yeniden başlatın
docker compose -f docker/docker-compose.remote-kafka.yml down
docker compose -f docker/docker-compose.remote-kafka.yml up -d ev-cp-e-001 ev-cp-m-001

# 10 saniye bekleyin
Start-Sleep -Seconds 10

# Monitor loglarını kontrol edin
docker logs ev-cp-m-001 --tail 20
```

**Sebep 4: Docker Network Problemi**

**Çözüm (Makine 2'de):**
```powershell
# Network'ün mevcut olduğunu kontrol et
docker network ls | Select-String "evcharging"

# Eğer network yoksa oluştur
docker network create ev-charging-simulation-1_evcharging-network

# Container'ları network'e bağla
docker network connect ev-charging-simulation-1_evcharging-network ev-cp-e-001
docker network connect ev-charging-simulation-1_evcharging-network ev-cp-m-001

# Container'ları restart et
docker restart ev-cp-e-001 ev-cp-m-001
```

**HIZLI TEST (Makine 2'de):**
```powershell
# CP Monitor'ün Central'a ulaşabildiğini container içinden test et
docker exec ev-cp-m-001 curl -v http://$env:CENTRAL_HOST:8000/health

# Başarılı olursa göreceksiniz:
# < HTTP/1.1 200 OK
# {"status":"healthy",...}
```

**Son Kontrol (Makine 1'de):**
```powershell
# Dashboard'dan CP'leri kontrol et
Invoke-WebRequest -Uri "http://localhost:8000/cp" | ConvertFrom-Json | 
    Select-Object -ExpandProperty charging_points | 
    Format-Table cp_id, state, engine_state, monitor_status

# Eğer hala boşsa, Central loglarını kontrol et:
docker logs ev-central --tail 50 | Select-String "CP-001|registered|heartbeat"
```

---

### Problem: "Driver şarj isteği gönderemiyor"

**Çözüm (Makine 3'te) - Windows PowerShell:**
```powershell
# Central'a erişebiliyor mu?
Invoke-WebRequest -Uri "$env:CENTRAL_HTTP_URL/health"

# CP'lerin ACTIVATED durumda olduğunu doğrula
Invoke-WebRequest -Uri "$env:CENTRAL_HTTP_URL/cp" | ConvertFrom-Json | Select-Object -ExpandProperty charging_points | Where-Object {$_.engine_state -ne "ACTIVATED"}

# Driver loglarını kontrol et
docker logs ev-driver-alice -n 50

# Yeniden başlat
docker restart ev-driver-alice

# Manuel şarj isteği gönder
Invoke-WebRequest -Uri "http://localhost:8100/drivers/driver-alice/requests" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"cp_id": "CP-001", "vehicle_id": "VEH-001"}'
```

---

### Problem: "IP Adresi Değişti"

**Windows'ta IP sabitlemek için:**
1. `Control Panel` → `Network and Sharing Center`
2. `Change adapter settings`
3. Ethernet'e sağ tık → `Properties`
4. `Internet Protocol Version 4 (TCP/IPv4)` → `Properties`
5. `Use the following IP address:` seç
6. IP: `192.168.1.105` (veya istediğiniz IP)
7. Subnet: `255.255.255.0`
8. Gateway: `192.168.1.1` (router IP'si)
9. DNS: `8.8.8.8` ve `8.8.4.4` (Google DNS)

**Not:** Okul ağında IP değişikliği yapmak için sistem yöneticisine danışın!

---

## 📊 Performans Metrikleri

### Beklenen Değerler:
- **Kafka throughput**: 1000+ messages/sec
- **CP response time**: < 100ms
- **Monitor health check**: 2 saniyede bir
- **Driver request interval**: 4.5 - 8 saniye arası
- **Session başlatma süresi**: < 2 saniye
- **Telemetry publish rate**: 1 saniyede bir

---

## 🎓 Eğitmen İçin Notlar

### Sunum Öncesi Kontrol:
1. ✅ Her 3 makinede Docker Desktop çalışıyor
2. ✅ Network bağlantısı stabil
3. ✅ IP adresleri doğru ayarlanmış
4. ✅ Firewall kuralları uygulanmış
5. ✅ Test scriptleri çalıştırılmış

### Sunum Sırasında Gösterilecekler:
1. **Otonom Başlatma** (5 dk)
   - Makine 1 → 2 → 3 sırasıyla başlat
   - Terminal loglarını göster
   - Dashboard'u projeksiyonda aç

2. **Normal İşleyiş** (5 dk)
   - Dashboard'da CP durumları
   - Session'lar ve telemetri
   - Driver dashboard'ları

3. **Fault Injection** (5 dk)
   - CP-003'ü crash et
   - FAULTY durumuna geçişi göster
   - Recover işlemi
   - ACTIVATED'a geri dönüş

4. **Eşzamanlı Test** (5 dk)
   - 5 driver + 5 CP aynı anda
   - Log akışlarını göster
   - Dashboard'da real-time updates

### Öğrenci Çalışması İçin:
- Öğrenciler kendi laptop'larında **tek makine** deployment yapabilir
- `docker compose up -d` ile tüm sistem local'de çalışır
- 3 makine senaryosu laboratuvar ortamı için özel
- **Detaylar için:** [QUICKSTART.md](QUICKSTART.md) dosyasına bakın

---

## 📝 Sık Kullanılan Komutlar

**Windows PowerShell:**
```powershell
# Tüm logları izle
docker compose logs -f

# Belirli servisleri izle (ayrı terminal pencereleri önerilir)
docker logs -f ev-cp-e-001
docker logs -f ev-driver-alice

# Servis sayısını kontrol et
(docker ps --format "{{.Names}}").Count

# Kafka topic'lerini listele (sadece Makine 1'de)
docker exec kafka kafka-topics.sh --bootstrap-server localhost:9092 --list

# Tüm servisleri durdur
docker compose down

# Tüm servisleri temizle (volumes dahil)
docker compose down -v
docker system prune -a --volumes -f
```

---

## 🎯 Hızlı Başlatma Özeti

### Makine 1 (Ana Sunucu) - Windows PowerShell:
```powershell
$env:KAFKA_ADVERTISED_HOST = "192.168.1.105"  # ⬅️ KENDİ IP'NİZ
docker compose up -d kafka
Start-Sleep -Seconds 30
docker compose up -d ev-central
```

### Makine 2 (Charging Points) - Windows PowerShell:
```powershell
$env:KAFKA_BOOTSTRAP = "192.168.1.105:9092"
$env:CENTRAL_HOST = "192.168.1.105"
$env:CENTRAL_PORT = "8000"

# Script ile (önerilir - otomatik bağlantı testi dahil)
.\deploy-lab-cp.ps1

# VEYA manuel docker compose komutları
docker compose -f docker/docker-compose.remote-kafka.yml up -d `
  ev-cp-e-001 ev-cp-e-002 ev-cp-e-003 ev-cp-e-004 ev-cp-e-005 `
  ev-cp-m-001 ev-cp-m-002 ev-cp-m-003 ev-cp-m-004 ev-cp-m-005
```

### Makine 3 (Drivers) - Windows PowerShell:
```powershell
$env:KAFKA_BOOTSTRAP = "192.168.1.105:9092"
$env:CENTRAL_HTTP_URL = "http://192.168.1.105:8000"

# Script ile (önerilir - otomatik bağlantı testi dahil)
.\deploy-lab-driver.ps1

# VEYA manuel docker compose komutları
docker compose -f docker/docker-compose.remote-kafka.yml up -d `
  ev-driver-alice ev-driver-bob ev-driver-charlie ev-driver-david ev-driver-eve
```

---

## 📌 Windows Lab Ortamı Notları

### Deployment Scripts:
Lab ortamı için özel PowerShell script'leri hazırlandı:
- **deploy-lab-cp.ps1**: Makine 2'de 5 CP + 5 Monitor başlatır (otomatik bağlantı testi dahil)
- **deploy-lab-driver.ps1**: Makine 3'te 5 Driver başlatır (otomatik bağlantı testi dahil)

Bu script'ler:
- ✅ Environment variable kontrolü yapar
- ✅ Kafka ve Central'a bağlantıyı test eder
- ✅ Firewall problemlerini erken tespit eder
- ✅ Detaylı log çıktıları verir

### Windows Defender Firewall:
Lab ortamında Windows Defender Firewall özellikle aşağıdaki portları engelleyebilir:
- **9092** (Kafka)
- **8000** (Central Dashboard)
- **9999** (Central TCP Server)

**Çözüm:** Gerekli portlar için inbound rules eklenmeli (yukarıda detaylandırılmıştır).

### PowerShell 7+ Önerilir:
- Daha iyi performans ve cross-platform uyumluluk
- `Invoke-WebRequest` komutları daha güvenilir
- JSON parsing `ConvertFrom-Json` ile kolay

### Docker Desktop WSL 2:
- WSL 2 backend mutlaka kullanılmalı (Settings → General → Use WSL 2)
- Daha performanslı ve Windows için optimize edilmiş

### Okul Ağı (Wired LAN):
- Tüm lab bilgisayarları kablolu ethernet ile okul ağına bağlı
- DHCP kullanılıyorsa IP adreslerinin değişme ihtimaline karşı dikkatli olun
- Statik IP ataması için sistem yöneticisine danışın
- Bazı okul ağlarında firewall/proxy ayarları Docker trafiğini etkileyebilir

---

**Güncellenme:** 28 Ekim 2025  
**Versiyon:** 4.0 (Windows Lab Environment Only)  
**Toplam Servis:** 17 (2 infra + 10 CP + 5 driver)  
**Kaynak:** [GitHub - ev-charging-simulation](https://github.com/Bariskosee/ev-charging-simulation)

---

**🚀 Başarılar! Windows lab ortamınızda sistem artık 3 makine üzerinde kesintisiz çalışmaya hazır!**
