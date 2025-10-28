# 🪟 Windows 3 Makine Dağıtım Kılavuzu

## 🎯 Senaryo: 3 Windows Bilgisayarda Dağıtım

Bu kılavuz, EV Charging Simulation sistemini 3 farklı Windows bilgisayara nasıl dağıtacağınızı gösterir.

---

## 🖥️ Makine Yapılandırması

### **Makine 1 (Ana Bilgisayar)** - Kafka + Central Controller
- **Rol**: Mesaj broker (Kafka) ve merkezi kontrol sistemi
- **Servisler**: 
  - `ev-kafka` (Port 9092)
  - `ev-central` (Port 8000 - Dashboard, Port 9999 - TCP)
- **Gereksinimler**: Docker Desktop for Windows

### **Makine 2 (Lab PC 1)** - Şarj İstasyonları
- **Rol**: Charging Point Engine + Monitor
- **Servisler**: 
  - `ev-cp-e-1` to `ev-cp-e-5` (Engine)
  - `ev-cp-m-1` to `ev-cp-m-5` (Monitor)
- **Gereksinimler**: Docker Desktop for Windows

### **Makine 3 (Lab PC 2)** - Sürücüler
- **Rol**: Driver istemcileri
- **Servisler**: 
  - `ev-driver-alice` (Port 8100)
  - `ev-driver-bob` (Port 8101)
  - `ev-driver-charlie` (Port 8102)
- **Gereksinimler**: Docker Desktop for Windows

---

## 📡 Ağ Yapılandırması Gereksinimleri

### Tüm 3 Bilgisayar:
1. ✅ Aynı yerel ağda (LAN) olmalı (örn: 192.168.1.x)
2. ✅ Firewall izinleri gerekli portlar için açık olmalı
3. ✅ Docker Desktop kurulu ve çalışıyor olmalı
4. ✅ Windows PowerShell veya Command Prompt erişimi

### Gerekli Portlar:
- **Makine 1**: 9092 (Kafka), 8000 (Dashboard), 9999 (TCP)
- **Makine 2**: Dış bağlantı yok (sadece outbound)
- **Makine 3**: 8100-8104 (Driver dashboards)

---

## 🚀 Kurulum Adımları

### 0️⃣ Ön Hazırlık (Tüm Makinelerde)

#### Windows'ta Docker Desktop Kurulumu:
1. [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/) indir
2. Kur ve bilgisayarı yeniden başlat
3. Docker Desktop'ı aç ve WSL 2 backend'i etkinleştir

#### Proje Dosyalarını Kopyala:
```powershell
# Git kullanarak (önerilir)
git clone https://github.com/Bariskosee/ev-charging-simulation.git
cd ev-charging-simulation

# Veya ZIP olarak indir ve çıkar
```

---

### 1️⃣ Makine 1 Kurulumu (Ana Bilgisayar)

#### Adım 1.1: IPv4 Adresini Bul

**PowerShell'de:**
```powershell
# IPv4 adresini bul
(Get-NetIPAddress -AddressFamily IPv4 -InterfaceAlias "Ethernet*" | Where-Object {$_.IPAddress -like "192.168.*"}).IPAddress
```

**Veya Command Prompt'ta:**
```cmd
ipconfig | findstr /i "IPv4"
```

**Örnek Çıktı:**
```
192.168.1.105
```

Bu IP adresini **NOT EDİN** - diğer makinelerde kullanacaksınız! 📝

---

#### Adım 1.2: docker-compose.yml Dosyasını Düzenle

Projenizin ana dizininde `docker-compose.yml` dosyasını açın ve Kafka yapılandırmasını düzenleyin:

**Değiştirilmesi Gereken Satırlar (27-30):**

```yaml
# docker-compose.yml - Kafka servis yapılandırması

kafka:
  image: apache/kafka:3.7.0
  container_name: ev-kafka
  ports:
    - "9092:9092"
  environment:
    KAFKA_NODE_ID: 1
    KAFKA_PROCESS_ROLES: broker,controller
    KAFKA_LISTENERS: PLAINTEXT://0.0.0.0:9092,CONTROLLER://0.0.0.0:9093
    # ⬇️ BU SATIRI DEĞİŞTİRİN:
    KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://${KAFKA_ADVERTISED_HOST:-localhost}:9092
    # ESKİ: PLAINTEXT://kafka:9092
    # YENİ: PLAINTEXT://${KAFKA_ADVERTISED_HOST:-localhost}:9092
    
    KAFKA_CONTROLLER_LISTENER_NAMES: CONTROLLER
    KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT
    # ⬇️ BU SATIRI DA DEĞİŞTİRİN:
    KAFKA_CONTROLLER_QUORUM_VOTERS: 1@localhost:9093
    # ESKİ: 1@kafka:9093
    # YENİ: 1@localhost:9093
```

---

#### Adım 1.3: Windows Firewall'u Yapılandır

**PowerShell'i Yönetici Olarak Aç ve:**

```powershell
# Kafka için port 9092'yi aç
New-NetFirewallRule -DisplayName "Kafka Port 9092" -Direction Inbound -LocalPort 9092 -Protocol TCP -Action Allow

# Central Dashboard için port 8000'i aç
New-NetFirewallRule -DisplayName "Central Dashboard Port 8000" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow

# TCP Server için port 9999'u aç
New-NetFirewallRule -DisplayName "Central TCP Port 9999" -Direction Inbound -LocalPort 9999 -Protocol TCP -Action Allow
```

**Veya Windows Defender Firewall GUI'den:**
1. `Control Panel` → `Windows Defender Firewall` → `Advanced Settings`
2. `Inbound Rules` → `New Rule`
3. Port seç → TCP → 9092, 8000, 9999 portlarını ekle
4. Allow the connection → Apply

---

#### Adım 1.4: Servisleri Başlat

**PowerShell veya Command Prompt'ta:**

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
  "timestamp": "2025-10-27T..."
}
```

---

#### Adım 1.6: IP Adresini Paylaş

```powershell
# IP adresini göster
Write-Host "==================================="
Write-Host "Kafka ve Central IP: $env:KAFKA_ADVERTISED_HOST"
Write-Host "Dashboard URL: http://$env:KAFKA_ADVERTISED_HOST:8000"
Write-Host "==================================="
Write-Host "Bu IP'yi diğer makinelere verin!"
```

**Bu bilgileri diğer 2 makineye gönderin! 📤**

---

### 2️⃣ Makine 2 Kurulumu (Charging Points)

#### Adım 2.1: Environment Variables Ayarla

**Makine 1'den aldığınız IP adresini kullanın:**

```powershell
# Makine 1'in IP adresi (örnek: 192.168.1.105)
$env:KAFKA_BOOTSTRAP = "192.168.1.105:9092"      # ⬅️ Makine 1 IP
$env:CENTRAL_HOST = "192.168.1.105"              # ⬅️ Makine 1 IP
$env:CENTRAL_PORT = "8000"
```

---

#### Adım 2.2: Bağlantıyı Test Et

```powershell
# Kafka'ya erişimi test et
docker run --rm confluentinc/cp-kafka:latest `
  kafka-broker-api-versions --bootstrap-server $env:KAFKA_BOOTSTRAP

# Central Dashboard'a erişimi test et
Invoke-WebRequest -Uri "http://$($env:CENTRAL_HOST):8000/health"
```

**Eğer hata alırsanız:**
- Makine 1'in firewall ayarlarını kontrol edin
- IP adresinin doğru olduğunu onaylayın
- İki bilgisayarın aynı ağda olduğunu doğrulayın

---

#### Adım 2.3: Charging Point Servislerini Başlat

```powershell
# CP Engine ve Monitor servislerini başlat
docker compose -f docker/docker-compose.remote-kafka.yml up -d `
  ev-cp-e-1 ev-cp-e-2 ev-cp-e-3 ev-cp-e-4 ev-cp-e-5 `
  ev-cp-m-1 ev-cp-m-2 ev-cp-m-3 ev-cp-m-4 ev-cp-m-5

# Servislerin durumunu kontrol et
docker compose -f docker/docker-compose.remote-kafka.yml ps
```

---

#### Adım 2.4: CP Loglarını Kontrol Et

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

**Makine 1'de (Ana Bilgisayar):**

```powershell
# Dashboard'dan CP'leri kontrol et
Invoke-WebRequest -Uri "http://localhost:8000/cp" | ConvertFrom-Json | Select-Object -ExpandProperty charging_points
```

**CP-001 to CP-005 görmelisiniz!** 🎉

---

### 3️⃣ Makine 3 Kurulumu (Drivers)

#### Adım 3.1: Environment Variables Ayarla

```powershell
# Makine 1'in IP adresi
$env:KAFKA_BOOTSTRAP = "192.168.1.105:9092"                    # ⬅️ Makine 1 IP
$env:CENTRAL_HTTP_URL = "http://192.168.1.105:8000"            # ⬅️ Makine 1 IP
```

---

#### Adım 3.2: Bağlantıyı Test Et

```powershell
# Central Dashboard'a erişimi test et
Invoke-WebRequest -Uri "$env:CENTRAL_HTTP_URL/health"

# Mevcut CP'leri görüntüle
Invoke-WebRequest -Uri "$env:CENTRAL_HTTP_URL/cp" | ConvertFrom-Json | Select-Object -ExpandProperty charging_points | Select-Object cp_id, state, engine_state
```

---

#### Adım 3.3: Driver Servislerini Başlat

```powershell
# Driver servislerini başlat
docker compose -f docker/docker-compose.remote-kafka.yml up -d `
  ev-driver-alice ev-driver-bob ev-driver-charlie

# Servislerin durumunu kontrol et
docker compose -f docker/docker-compose.remote-kafka.yml ps
```

---

#### Adım 3.4: Windows Firewall (Driver Dashboards için - Opsiyonel)

Eğer driver dashboard'larına dışarıdan erişmek isterseniz:

```powershell
# Driver dashboard portlarını aç (8100-8104)
New-NetFirewallRule -DisplayName "Driver Dashboards" -Direction Inbound -LocalPort 8100-8104 -Protocol TCP -Action Allow
```

---

#### Adım 3.5: Driver Loglarını Kontrol Et

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

#### Adım 3.6: Driver Dashboard'a Erişim

```powershell
# Browser'da aç
Start-Process "http://localhost:8100"

# Veya API üzerinden
Invoke-WebRequest -Uri "http://localhost:8100/charging-points" | ConvertFrom-Json
```

---

## ✅ Doğrulama Kontrol Listesi

### Makine 1 (Ana Bilgisayar) Kontrolleri:

```powershell
# ✅ Kafka çalışıyor mu?
docker ps --filter "name=ev-kafka"

# ✅ Central çalışıyor mu?
docker ps --filter "name=ev-central"

# ✅ Kafka external'den erişilebilir mi?
docker exec ev-kafka kafka-broker-api-versions.sh --bootstrap-server localhost:9092

# ✅ CP'ler kaydedildi mi?
Invoke-WebRequest -Uri "http://localhost:8000/cp" | ConvertFrom-Json | Select-Object -ExpandProperty charging_points | Measure-Object
# Sonuç: 5 CP görmelisiniz
```

---

### Makine 2 (CP'ler) Kontrolleri:

```powershell
# ✅ CP Engine'ler çalışıyor mu?
docker ps --filter "name=ev-cp-e"

# ✅ CP Monitor'ler çalışıyor mu?
docker ps --filter "name=ev-cp-m"

# ✅ Kafka'ya bağlandılar mı?
docker logs ev-cp-e-1 | Select-String "Kafka producer started"
docker logs ev-cp-m-1 | Select-String "heartbeat sent successfully"
```

---

### Makine 3 (Driver'lar) Kontrolleri:

```powershell
# ✅ Driver'lar çalışıyor mu?
docker ps --filter "name=ev-driver"

# ✅ Kafka'ya bağlandılar mı?
docker logs ev-driver-alice | Select-String "Kafka producer started"

# ✅ Charging request gönderebildiler mi?
docker logs ev-driver-alice | Select-String "requested charging"
```

---

## 🔧 Sorun Giderme

### Sorun 1: "Connection refused to Kafka"

**Belirtiler:**
```
ERROR: Failed to connect to Kafka at 192.168.1.105:9092
```

**Çözümler:**

1. **Makine 1'de Firewall kontrolü:**
```powershell
# Firewall kuralını kontrol et
Get-NetFirewallRule -DisplayName "Kafka Port 9092"

# Eğer yoksa ekle
New-NetFirewallRule -DisplayName "Kafka Port 9092" -Direction Inbound -LocalPort 9092 -Protocol TCP -Action Allow
```

2. **Kafka'nın 0.0.0.0'da dinlediğini doğrula:**
```powershell
docker exec ev-kafka netstat -tuln | Select-String "9092"
# Görmeli: 0.0.0.0:9092 (127.0.0.1:9092 DEĞİL!)
```

3. **Network connectivity test et (Makine 2 veya 3'ten):**
```powershell
Test-NetConnection -ComputerName 192.168.1.105 -Port 9092
```

**Beklenen Sonuç:**
```
TcpTestSucceeded : True
```

---

### Sorun 2: "CP Dashboard'da Görünmüyor"

**Sebep:** CP Engine başlamadı veya Central'a bağlanamadı

**Çözüm:**

```powershell
# CP Engine loglarını kontrol et
docker logs ev-cp-e-1 --tail 50

# CP'yi yeniden başlat
docker restart ev-cp-e-1 ev-cp-m-1

# 10 saniye bekle
Start-Sleep -Seconds 10

# Dashboard'dan tekrar kontrol et
Invoke-WebRequest -Uri "http://192.168.1.105:8000/cp" | ConvertFrom-Json
```

---

### Sorun 3: "Driver Şarj İsteği Gönderemiyor"

**Çözüm:**

```powershell
# CP'lerin ACTIVATED durumda olduğunu doğrula
Invoke-WebRequest -Uri "$env:CENTRAL_HTTP_URL/cp" | ConvertFrom-Json | Select-Object -ExpandProperty charging_points | Where-Object {$_.engine_state -ne "ACTIVATED"}

# Manuel şarj isteği gönder
Invoke-WebRequest -Uri "http://localhost:8100/drivers/driver-alice/requests" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"cp_id": "CP-001", "vehicle_id": "VEH-001"}'
```

---

### Sorun 4: "IP Adresi Değişti"

**Windows'ta IP sabitlemek için:**

1. `Control Panel` → `Network and Sharing Center`
2. `Change adapter settings`
3. Ethernet'e sağ tık → `Properties`
4. `Internet Protocol Version 4 (TCP/IPv4)` → `Properties`
5. `Use the following IP address:` seç
6. IP: `192.168.1.105` (veya istediğiniz IP)
7. Subnet: `255.255.255.0`
8. Gateway: `192.168.1.1` (router IP'si)

---

## 🎯 Hızlı Başlatma Komutları

### Makine 1 (Bir Kez Çalıştır):

```powershell
# Ortam değişkenini ayarla
$env:KAFKA_ADVERTISED_HOST = "192.168.1.105"  # ⬅️ KENDİ IP'NİZ

# Servisleri başlat
docker compose up -d kafka
Start-Sleep -Seconds 30
docker compose up -d ev-central

# IP'yi göster
Write-Host "Sistem IP: $env:KAFKA_ADVERTISED_HOST"
```

---

### Makine 2 (Bir Kez Çalıştır):

```powershell
# Ortam değişkenlerini ayarla
$env:KAFKA_BOOTSTRAP = "192.168.1.105:9092"     # ⬅️ Makine 1 IP
$env:CENTRAL_HOST = "192.168.1.105"              # ⬅️ Makine 1 IP
$env:CENTRAL_PORT = "8000"

# CP'leri başlat
docker compose -f docker/docker-compose.remote-kafka.yml up -d `
  ev-cp-e-1 ev-cp-e-2 ev-cp-e-3 ev-cp-e-4 ev-cp-e-5 `
  ev-cp-m-1 ev-cp-m-2 ev-cp-m-3 ev-cp-m-4 ev-cp-m-5
```

---

### Makine 3 (Bir Kez Çalıştır):

```powershell
# Ortam değişkenlerini ayarla
$env:KAFKA_BOOTSTRAP = "192.168.1.105:9092"            # ⬅️ Makine 1 IP
$env:CENTRAL_HTTP_URL = "http://192.168.1.105:8000"    # ⬅️ Makine 1 IP

# Driver'ları başlat
docker compose -f docker/docker-compose.remote-kafka.yml up -d `
  ev-driver-alice ev-driver-bob ev-driver-charlie
```

---

## 📊 Demo İçin Öneriler

### Senaryo 1: Canlı İzleme

**Makine 1'de (Sunum Ekranı):**
- Browser'da aç: `http://localhost:8000`
- Canlı CP durumlarını göster
- Charging session'ları izle

**Makine 2'de (Arka Planda):**
- CP loglarını göster: `docker logs -f ev-cp-e-1`

**Makine 3'te (Arka Planda):**
- Driver loglarını göster: `docker logs -f ev-driver-alice`

---

### Senaryo 2: Fault Injection

```powershell
# Makine 2'de bir CP'yi crash et
docker stop ev-cp-e-3

# Makine 1'de dashboard'dan gözlemle
# CP-003 durumu FAULTY olacak

# 30 saniye bekle, sonra recover et
Start-Sleep -Seconds 30
docker start ev-cp-e-3
```

---

## 📝 Notlar

1. **IP Adresleri:** Tüm örneklerde `192.168.1.105` yerine kendi IP'nizi kullanın
2. **Firewall:** Windows Defender özellikle 9092, 8000, 9999 portlarını engelleyebilir
3. **Docker Desktop:** Mutlaka WSL 2 backend kullanın (daha performanslı)
4. **Network:** Tüm 3 bilgisayar aynı subnet'te olmalı (örn: 192.168.1.x)
5. **PowerShell:** Komutları PowerShell 7+ ile çalıştırmanız önerilir

---

## 🎓 Sunum İçin Hazırlık

### Önceden Yap:
1. ✅ Her 3 makinede Docker Desktop kur
2. ✅ Her makinede projeyi klonla
3. ✅ IP adreslerini not et
4. ✅ Firewall kurallarını ekle
5. ✅ Test et: Makine 1 → 2 → 3 sırasıyla başlat

### Sunum Sırasında:
1. Terminal'leri aç (her makinede 1 tane)
2. Makine 1: Dashboard'u tarayıcıda göster
3. Makine 2/3: Log takibini göster
4. Fault injection demo yap
5. Recovery'yi göster

---

**Başarılar! 🚀**
