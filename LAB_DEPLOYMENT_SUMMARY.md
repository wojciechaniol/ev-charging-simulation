# 🎓 EV Charging Simulation - 3 Windows Bilgisayar Laboratuvar Dağıtım Kılavuzu

Bu kılavuz, EV Charging Simulation sistemini laboratuvardaki **3 farklı Windows bilgisayara** (okul kablolu ağı üzerinden) nasıl dağıtacağınızı **adım adım** gösterir.

> **💡 Not:** Tek bilgisayarda test etmek için **[QUICKSTART.md](QUICKSTART.md)** dosyasına bakın.  
> Bu kılavuz sadece **lab ortamı (3 Windows bilgisayar)** için geçerlidir.

---

## 🎯 Bu Kılavuzun Amacı

**Senaryo:** Okul laboratuvarında 3 ayrı Windows bilgisayar var ve bu bilgisayarlar kablolu ağ (LAN) ile bağlı. Sistemi şu şekilde dağıtacağız:

1. **Makine 1 (Öğretmen/Ana Bilgisayar)**: Kafka + Central Controller - Merkezi yönetim
2. **Makine 2 (Lab PC 1)**: 5 Şarj İstasyonu (CP) - Şarj noktaları
3. **Makine 3 (Lab PC 2)**: 5 Sürücü İstemcisi - Araç kullanıcıları

**Ne Yapacağız:**
- ✅ Her makinede Docker kurulumu
- ✅ Proje dosyalarını her makineye kopyalama
- ✅ Ağ bağlantılarını test etme
- ✅ Firewall ayarlarını yapılandırma
- ✅ Servisleri sırasıyla başlatma
- ✅ Sistemin çalıştığını doğrulama

**Toplam Süre:** ~45-60 dakika (ilk kurulum için)

---

## 📅 Hızlı Başlangıç Zaman Çizelgesi

Tüm ekip için tahmini zaman çizelgesi:

```
⏰ 0-20 dk:  [0️⃣ Ön Hazırlık]     Her 3 makinede Docker + Proje dosyaları
⏰ 20-35 dk: [1️⃣ Makine 1]        Öğretmen: Kafka + Central başlatma
⏰ 35-45 dk: [2️⃣ Makine 2]        Grup 1: 10 CP servisi başlatma
⏰ 45-55 dk: [3️⃣ Makine 3]        Grup 2: 5 Driver servisi başlatma
⏰ 55-60 dk: [4️⃣ Doğrulama]       Herkes: Test ve gözlem

✅ Toplam: ~60 dakika (deneyimliyseniz 45 dakika)
```

### Paralel Çalışma İpucu 💡
Zaman kazanmak için:
- **0-20 dk:** Her 3 makine **aynı anda** Docker kurabilir
- **20-35 dk:** Makine 1 hazırlanırken, Grup 1 ve 2 bekleyebilir veya bağlantı testleri yapabilir
- **35-55 dk:** Makine 2 ve 3 **sırayla** başlatılmalı (Makine 3, Makine 2'ye bağımlı)

---

## ✅ Ön Gereksinimler Kontrol Listesi

Başlamadan önce aşağıdakilerin hazır olduğundan emin olun:

### Donanım Gereksinimleri (Her Makine İçin):
- [ ] Windows 10/11 (64-bit)
- [ ] En az 8 GB RAM (16 GB önerilir)
- [ ] En az 20 GB boş disk alanı
- [ ] İnternet bağlantısı (ilk kurulum için)
- [ ] Ethernet kablosu ile ağa bağlı

### Yazılım Gereksinimleri (Her Makine İçin):
- [ ] Docker Desktop for Windows kurulacak
- [ ] PowerShell erişimi (Windows'ta varsayılan)
- [ ] Git (opsiyonel ama önerilir)
- [ ] Web tarayıcısı (Chrome/Edge/Firefox)

### Ağ Gereksinimleri:
- [ ] 3 bilgisayar aynı yerel ağda (LAN)
- [ ] Her bilgisayarın sabit veya öngörülebilir IP adresi var
- [ ] Bilgisayarlar arası ping yapılabiliyor
- [ ] IT departmanından gerekli izinler alınmış (firewall kuralları için)

### İdari Gereksinimler:
- [ ] Yönetici (Administrator) erişimi var
- [ ] Firewall ayarları değiştirilebilir
- [ ] Port yönlendirme yapılabilir (9092, 8000, 9999)

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

## 📋 Kurulum İş Akışı (Genel Bakış)

Bu rehber 5 ana aşamadan oluşur:

### Aşama 0️⃣: Ön Hazırlık (Tüm Makinelerde - ~20 dakika)
```
[Makine 1] → Docker kurulumu + Proje dosyaları
[Makine 2] → Docker kurulumu + Proje dosyaları  
[Makine 3] → Docker kurulumu + Proje dosyaları
```
**Hedef:** Her makineye Docker ve proje dosyalarını kurmak

### Aşama 1️⃣: Makine 1 Kurulumu (Ana Sunucu - ~10 dakika)
```
IP Bul → Firewall Aç → Kafka Başlat → Central Başlat → IP Paylaş
```
**Hedef:** Kafka ve Central Controller'ı çalıştırıp IP adresini diğer makinelere vermek

### Aşama 2️⃣: Makine 2 Kurulumu (Şarj İstasyonları - ~10 dakika)
```
IP Al → Bağlantı Test → Network Oluştur → 5 CP + 5 Monitor Başlat → Doğrula
```
**Hedef:** 10 CP servisi (5 engine + 5 monitor) başlatmak ve Central'a kayıt olmalarını sağlamak

### Aşama 3️⃣: Makine 3 Kurulumu (Sürücüler - ~5 dakika)
```
IP Al → Bağlantı Test → 5 Driver Başlat → Dashboard Erişim → Doğrula
```
**Hedef:** 5 sürücü istemcisi başlatmak ve şarj istekleri göndermelerini sağlamak

### Aşama 4️⃣: Doğrulama ve Test (~5 dakika)
```
Makine 1: CP'leri Dashboard'da Gör
Makine 2: Log Kontrolü
Makine 3: Şarj Sessionları Gözlemle
```
**Hedef:** Tüm sistemin birlikte çalıştığını doğrulamak

---

## 🎓 Kimin Ne Yapacağı (Rol Dağılımı)

### Öğretmen/Lab Sorumlusu:
- ✅ Makine 1'i kurar ve yönetir (Kafka + Central)
- ✅ IP adresini not edip öğrencilere dağıtır
- ✅ Firewall kurallarını ayarlar (IT yardımı ile)
- ✅ Dashboard'dan tüm sistemi izler

### Öğrenci Grubu 1 (Makine 2):
- ✅ Öğretmenden IP adresini alır
- ✅ CP servislerini başlatır (script ile)
- ✅ CP'lerin Central'a kayıt olduğunu doğrular

### Öğrenci Grubu 2 (Makine 3):
- ✅ Öğretmenden IP adresini alır
- ✅ Driver servislerini başlatır (script ile)
- ✅ Driver dashboard'larından şarj sessionlarını izler

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

## 🚀 Kurulum Adımları

### 0️⃣ Ön Hazırlık (Tüm Windows Bilgisayarlarda)

> **⏱️ Tahmini Süre:** 15-20 dakika (her makine için)  
> **👥 Kim Yapacak:** Öğretmen + Her iki öğrenci grubu kendi makinelerinde

#### Adım 0.1: Docker Desktop Kurulumu

**Tüm 3 makinede aşağıdaki adımları takip edin:**

**1. Docker Desktop İndirme:**
- Web tarayıcısında https://www.docker.com/products/docker-desktop/ adresine gidin
- **"Download for Windows"** butonuna tıklayın
- `Docker Desktop Installer.exe` dosyasını indirin (~500 MB)

**2. Docker Desktop Kurulumu:**
```powershell
# İndirilen installer'ı çalıştırın (çift tıklama)
# Kurulum sırasında:
✅ "Use WSL 2 instead of Hyper-V" seçeneğini işaretleyin (önerilir)
✅ "Add shortcut to desktop" seçeneğini işaretleyin
❌ "Use Windows containers" seçeneğini işaretLEMEyin (Linux containers kullanacağız)
```

**3. Bilgisayarı Yeniden Başlatma:**
- Kurulum tamamlandıktan sonra **bilgisayarı mutlaka yeniden başlatın**
- Yeniden başladıktan sonra Docker Desktop otomatik başlayacak

**4. Docker Desktop'ı Başlatma ve Yapılandırma:**
- Masaüstünden "Docker Desktop" ikonuna çift tıklayın
- İlk açılışta Docker hizmet sözleşmesini kabul edin
- Sistem tray'de (sağ alt köşede) Docker balina ikonu görünmeli
- İkon yeşil oldığında Docker hazır demektir

**5. WSL 2 Kurulumu (Eğer İsterse):**
```powershell
# Eğer Docker "WSL 2 installation is incomplete" hatası verirse:
# PowerShell'i Yönetici olarak açın ve şunu çalıştırın:

wsl --install

# Bilgisayarı tekrar başlatın
```

**6. Docker Kurulumunu Doğrulama:**

**PowerShell'i açın** (Başlat → "PowerShell" yazın → Enter):
```powershell
# Docker versiyonunu kontrol et
docker --version
# Beklenen çıktı: Docker version 24.x.x, build xxxxx

# Docker Compose versiyonunu kontrol et
docker compose version
# Beklenen çıktı: Docker Compose version v2.x.x

# Docker'ın çalıştığını test et
docker run hello-world
# Beklenen: "Hello from Docker!" mesajı görülmeli
```

**✅ Başarılı Kurulum İşaretleri:**
- Docker Desktop açık ve sistem tray'de yeşil ikon var
- `docker --version` komutu versiyon numarası döndürüyor
- `docker run hello-world` başarıyla çalışıyor

**❌ Sorun Giderme:**
- **"Docker Desktop starting..." takılı kalıyorsa:** 2-3 dakika bekleyin
- **"WSL 2 hatası" alıyorsanız:** `wsl --install` komutunu çalıştırın ve restart edin
- **"Access denied" hatası:** PowerShell'i "Run as Administrator" ile açın

---

#### Adım 0.2: Proje Dosyalarını İndirme

**Tüm 3 makinede aynı adımları takip edin:**

**Seçenek 1: Git ile (ÖNERİLİR):**

```powershell
# PowerShell'de (Normal kullanıcı - yönetici değil)

# 1. Git kurulu mu kontrol et
git --version
# Eğer "command not found" hatası alırsanız Git kurun:
# https://git-scm.com/download/win

# 2. Projeyi klonlayın
cd C:\Users\$env:USERNAME\Desktop
git clone https://github.com/Bariskosee/ev-charging-simulation.git

# 3. Proje klasörüne girin
cd ev-charging-simulation

# 4. Dosyaların indiğini doğrulayın
ls
# Göreceksiniz: docker/, evcharging/, docker-compose.yml, README.md, vb.
```

**Seçenek 2: ZIP ile (Git yoksa):**

```powershell
# 1. Web tarayıcısında bu adresi açın:
# https://github.com/Bariskosee/ev-charging-simulation/archive/refs/heads/main.zip

# 2. ZIP dosyasını indirin (Downloads klasörüne)

# 3. ZIP'i masaüstüne çıkarın:
# Downloads klasöründe ev-charging-simulation-main.zip'e sağ tık
# "Extract All" → Destination: Desktop → Extract

# 4. PowerShell'de klasöre gidin
cd C:\Users\$env:USERNAME\Desktop\ev-charging-simulation-main

# 5. Dosyaların varlığını doğrulayın
ls
```

**✅ Başarılı İndirme İşaretleri:**
- Masaüstünde `ev-charging-simulation` klasörü var
- İçinde `docker/`, `evcharging/`, `docker-compose.yml` var
- PowerShell'de `cd ev-charging-simulation` komutu çalışıyor

---

#### Adım 0.3: Ağ Bağlantısını Test Etme

**Her makinede ağ bağlantısını test edin:**

**PowerShell'de:**
```powershell
# 1. Kendi IP adresinizi öğrenin
(Get-NetIPAddress -AddressFamily IPv4 -InterfaceAlias "Ethernet*" | Where-Object {$_.IPAddress -like "192.168.*" -or $_.IPAddress -like "10.*"}).IPAddress

# Örnek çıktı:
# 192.168.1.101  (Makine 1)
# 192.168.1.102  (Makine 2)
# 192.168.1.103  (Makine 3)

# 2. IP'yi not edin (kağıda yazın veya WhatsApp'ta paylaşın)
```

**Ağ testi (Tüm makineler hazır olduktan sonra):**
```powershell
# Her makineden diğer makinelere ping atın:

# Örnek: Makine 2'den Makine 1'e ping
ping 192.168.1.101

# Beklenen:
# Reply from 192.168.1.101: bytes=32 time<1ms TTL=128
# (4 başarılı paket)

# Eğer "Request timed out" alırsanız:
# - Windows Firewall ICMPv4 engelliyor olabilir
# - Makineler farklı subnet'lerde olabilir
# - IT departmanına danışın
```

**✅ Ağ Hazır İşaretleri:**
- Her makine kendi IP adresini biliyor
- Makineler arası ping başarılı
- Tüm IP'ler aynı subnet'te (örn: 192.168.1.x)

---

### 1️⃣ Makine 1 Kurulumu (Ana Sunucu)

> **⏱️ Tahmini Süre:** 10-15 dakika  
> **👥 Kim Yapacak:** Öğretmen veya lab sorumlusu  
> **🎯 Amaç:** Kafka ve Central Controller başlatmak, IP adresini diğer makinelere vermek

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

> **⏱️ Tahmini Süre:** 10-12 dakika  
> **👥 Kim Yapacak:** Öğrenci Grubu 1  
> **🎯 Amaç:** 5 CP Engine + 5 CP Monitor başlatmak (toplam 10 servis)  
> **📋 Gerekli Bilgi:** Makine 1'in IP adresi (öğretmenden alınacak)

#### Adım 2.1: Makine 1'den IP Adresini Alma

**Öğretmenden/Makine 1'den şu bilgileri alın:**
```
Makine 1 IP: 192.168.1.105  (Örnek - kendi IP'nizi kullanın)
```

**Bu IP'yi not edin - sonraki adımlarda kullanacaksınız!** 📝

---

#### Adım 2.2: Environment Variables Ayarlama

**PowerShell'de (Makine 2'de):**

```powershell
# Makine 1'den aldığınız IP adresini buraya yazın
$env:KAFKA_BOOTSTRAP = "192.168.1.105:9092"      # ⬅️ Makine 1 IP'yi buraya
$env:CENTRAL_HOST = "192.168.1.105"              # ⬅️ Makine 1 IP'yi buraya
$env:CENTRAL_PORT = "8000"

# Ayarlandığını doğrula
Write-Host "✅ Environment Variables Ayarlandı:" -ForegroundColor Green
Write-Host "   KAFKA_BOOTSTRAP = $env:KAFKA_BOOTSTRAP"
Write-Host "   CENTRAL_HOST = $env:CENTRAL_HOST"
Write-Host "   CENTRAL_PORT = $env:CENTRAL_PORT"
```

**Beklenen Çıktı:**
```
✅ Environment Variables Ayarlandı:
   KAFKA_BOOTSTRAP = 192.168.1.105:9092
   CENTRAL_HOST = 192.168.1.105
   CENTRAL_PORT = 8000
```

---

#### Adım 2.3: Bağlantı Testleri (ÖNEMLİ!)

**Bu adım çok önemli - servisleri başlatmadan önce bağlantıyı test edin!**

**PowerShell'de:**
```powershell
Write-Host "🔍 Makine 1'e bağlantı test ediliyor..." -ForegroundColor Cyan

# Test 1: Kafka portuna erişim (9092)
Write-Host "`n1️⃣  Kafka (port 9092) testi:" -ForegroundColor Yellow
Test-NetConnection -ComputerName $env:CENTRAL_HOST -Port 9092

# Test 2: Central HTTP portuna erişim (8000)
Write-Host "`n2️⃣  Central HTTP (port 8000) testi:" -ForegroundColor Yellow
Test-NetConnection -ComputerName $env:CENTRAL_HOST -Port 8000

# Test 3: Central health endpoint
Write-Host "`n3️⃣  Central health endpoint testi:" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://$($env:CENTRAL_HOST):8000/health" -UseBasicParsing
    Write-Host "   ✅ Central erişilebilir! Status: $($response.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Central erişilemiyor! Hata: $_" -ForegroundColor Red
    Write-Host "   🔧 Makine 1'de firewall ayarlarını kontrol edin!" -ForegroundColor Yellow
}
```

**✅ Başarılı Bağlantı İşaretleri:**
```
TcpTestSucceeded : True  (her iki port için)
✅ Central erişilebilir! Status: 200
```

**❌ Eğer TcpTestSucceeded : False ise:**
1. Makine 1'de firewall kurallarını kontrol edin
2. IP adresinin doğru olduğunu onaylayın
3. Makine 1'de servislerin çalıştığını kontrol edin (`docker ps`)
4. Öğretmene/lab sorumlusuna danışın

---

#### Adım 2.4: Docker Network Oluşturma (KRİTİK ADIM!)

**⚠️ ÖNEMLİ:** Bu network olmazsa CP'ler Central'a kayıt olamaz!
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
  ev-cp-e-1 ev-cp-e-2 ev-cp-e-3 ev-cp-e-4 ev-cp-e-5 `
  ev-cp-m-1 ev-cp-m-2 ev-cp-m-3 ev-cp-m-4 ev-cp-m-5

# Servislerin durumunu kontrol et (10 servis görmelisiniz)
docker compose -f docker/docker-compose.remote-kafka.yml ps

# Tüm CP'lerin çalıştığını doğrula
docker ps --filter "name=ev-cp" --format "table {{.Names}}\t{{.Status}}"
```
Way to add monitor and engine manually
```powershell
# recipe for monitor and engine - run only once
docker build -t ev-cp-engine:latest -f docker/Dockerfile.cp_e ..
docker build -t ev-cp-monitor:latest -f docker/Dockerfile.cp_m ..

Here it is necessary 
docker run -d `
  --name ev-cp-e-NUMBER `
  --network evcharging-network `
  -e CP_ENGINE_KAFKA_BOOTSTRAP="$env:KAFKA_BOOTSTRAP" `
  -e CP_ENGINE_CP_ID="CP-NUMBER" `
  -e CP_ENGINE_HEALTH_PORT=NEXT_PORT `
  -e CP_ENGINE_LOG_LEVEL=INFO `
  -e CP_ENGINE_KW_RATE=VALUE1 `
  -e CP_ENGINE_EURO_RATE=VALUE2 `
  -e CP_ENGINE_TELEMETRY_INTERVAL=1.0 `
  -p NEXT_PORT:NEXT_PORT `
  ev-cp-engine:latest

docker run -d `
  --name ev-cp-m-NUMBER `
  --network evcharging-network `
  -e CP_MONITOR_CP_ID="CP-NUMBER" `
  -e CP_MONITOR_CP_E_HOST="ev-cp-e-NUMBER" `
  -e CP_MONITOR_CP_E_PORT=NEXT_PORT `
  -e CP_MONITOR_CENTRAL_HOST="$env:CENTRAL_HOST" `
  -e CP_MONITOR_CENTRAL_PORT="$env:CENTRAL_PORT" `
  -e CP_MONITOR_HEALTH_INTERVAL=2.0 `
  -e CP_MONITOR_LOG_LEVEL=INFO `
  -e CP_MONITOR_KAFKA_BOOTSTRAP="$env:KAFKA_BOOTSTRAP" `
  ev-cp-monitor:latest

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

> **⏱️ Tahmini Süre:** 8-10 dakika  
> **👥 Kim Yapacak:** Öğrenci Grubu 2  
> **🎯 Amaç:** 5 Driver istemcisi başlatmak (Alice, Bob, Charlie, David, Eve)  
> **📋 Gerekli Bilgi:** Makine 1'in IP adresi + CP'lerin hazır olması (Makine 2'den)

#### Adım 3.1: Makine 1'den IP Adresini Alma

**Öğretmenden/Makine 1'den şu bilgileri alın:**
```
Makine 1 IP: 192.168.1.105  (Örnek - kendi IP'nizi kullanın)
```

**Makine 2'nin hazır olduğundan emin olun!**
- Makine 2'de 10 CP servisi çalışıyor olmalı
- Makine 1 dashboard'unda 5 CP görünüyor olmalı

---

#### Adım 3.2: Environment Variables Ayarlama

**PowerShell'de (Makine 3'te):**

```powershell
# Makine 1'den aldığınız IP adresini buraya yazın
$env:KAFKA_BOOTSTRAP = "192.168.1.105:9092"              # ⬅️ Makine 1 IP'yi buraya
$env:CENTRAL_HTTP_URL = "http://192.168.1.105:8000"      # ⬅️ Makine 1 IP'yi buraya

# Ayarlandığını doğrula
Write-Host "✅ Environment Variables Ayarlandı:" -ForegroundColor Green
Write-Host "   KAFKA_BOOTSTRAP = $env:KAFKA_BOOTSTRAP"
Write-Host "   CENTRAL_HTTP_URL = $env:CENTRAL_HTTP_URL"
```

**Beklenen Çıktı:**
```
✅ Environment Variables Ayarlandı:
   KAFKA_BOOTSTRAP = 192.168.1.105:9092
   CENTRAL_HTTP_URL = http://192.168.1.105:8000
```

---

#### Adım 3.3: Bağlantı Testleri

**PowerShell'de:**
```powershell
Write-Host "🔍 Makine 1'e bağlantı test ediliyor..." -ForegroundColor Cyan

# Test 1: Central health endpoint
Write-Host "`n1️⃣  Central health endpoint testi:" -ForegroundColor Yellow
try {
    $health = Invoke-WebRequest -Uri "$env:CENTRAL_HTTP_URL/health" -UseBasicParsing | ConvertFrom-Json
    Write-Host "   ✅ Central erişilebilir! Status: $($health.status)" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Central erişilemiyor!" -ForegroundColor Red
    exit 1
}

# Test 2: CP'lerin varlığını kontrol et (ÖNEMLİ!)
Write-Host "`n2️⃣  Mevcut CP'leri kontrol ediliyor:" -ForegroundColor Yellow
try {
    $cps = Invoke-WebRequest -Uri "$env:CENTRAL_HTTP_URL/cp" -UseBasicParsing | ConvertFrom-Json
    $cpCount = $cps.charging_points.Count
    
    if ($cpCount -gt 0) {
        Write-Host "   ✅ $cpCount adet CP bulundu!" -ForegroundColor Green
        $cps.charging_points | Select-Object cp_id, engine_state | Format-Table
    } else {
        Write-Host "   ⚠️  Hiç CP bulunamadı! Makine 2'de CP'lerin çalıştığından emin olun!" -ForegroundColor Yellow
        Write-Host "   💡 Makine 2'de .\deploy-lab-cp.ps1 script'ini çalıştırın" -ForegroundColor Cyan
    }
} catch {
    Write-Host "   ❌ CP listesi alınamadı!" -ForegroundColor Red
}

# Test 3: Kafka bağlantısı
Write-Host "`n3️⃣  Kafka bağlantı testi:" -ForegroundColor Yellow
$kafkaHost = $env:KAFKA_BOOTSTRAP -split ':' | Select-Object -First 1
$kafkaPort = $env:KAFKA_BOOTSTRAP -split ':' | Select-Object -Last 1
Test-NetConnection -ComputerName $kafkaHost -Port $kafkaPort
```

**✅ Başarılı Bağlantı İşaretleri:**
- Central health: status = "healthy"
- CP sayısı: 5 adet (CP-001 to CP-005)
- Kafka: TcpTestSucceeded : True

---

#### Adım 3.4: Docker Network Oluşturma

**PowerShell'de:**
```powershell
Write-Host "🌐 Docker network kontrol ediliyor..." -ForegroundColor Cyan

# Network var mı kontrol et
$networkExists = docker network ls | Select-String "ev-charging-simulation-1_evcharging-network"

if (-not $networkExists) {
    Write-Host "   Network yok, oluşturuluyor..." -ForegroundColor Yellow
    docker network create ev-charging-simulation-1_evcharging-network
    Write-Host "   ✅ Network oluşturuldu" -ForegroundColor Green
} else {
    Write-Host "   ✅ Network zaten mevcut" -ForegroundColor Green
}
```

---

#### Adım 3.5: Driver Servislerini Başlatma

**YÖNTEM 1: Script ile (ÖNERİLİR - Otomatik Diagnostic Dahil):**

```powershell
# Proje klasöründe olduğunuzdan emin olun
cd C:\Users\$env:USERNAME\Desktop\ev-charging-simulation

# Deploy script'ini çalıştırın
.\deploy-lab-driver.ps1
```
```powershell
# run this first to create a recipe for the image
docker build -t ev-driver:latest -f docker/Dockerfile.driver ..

# creates an actual image. It is necessary to replace NAME and NEXT_PORT with actual values
docker run -d --name ev-driver-NAME `
  --network evcharging-network `
  -e DRIVER_DRIVER_ID=driver-NAME `
  -e DRIVER_KAFKA_BOOTSTRAP=$env:KAFKA_BOOTSTRAP `
  -e DRIVER_CENTRAL_HTTP_URL=$env:CENTRAL_HTTP_URL `
  -p NEXT_PORT:NEXT_PORT `
  ev-driver:latest

```

**Script ne yapar:**
- ✅ Environment variables'ları kontrol eder
- ✅ Bağlantıyı test eder
- ✅ Network'ü oluşturur (yoksa)
- ✅ 5 Driver servisini başlatır
- ✅ Driver startup durumunu doğrular
- ✅ Sorun varsa diagnostic komutlar gösterir

**YÖNTEM 2: Manuel Docker Compose (Alternatif):**

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

## 🎯 4️⃣ Son Doğrulama ve Test (Tüm Makineler)

> **⏱️ Tahmini Süre:** 5-10 dakika  
> **👥 Kim Yapacak:** Herkes birlikte (koordineli)  
> **🎯 Amaç:** Tüm sistemin birlikte çalıştığını doğrulamak

### Adım 4.1: Hızlı Sistem Özeti

**Her makinede kontrol edin:**

**Makine 1 (PowerShell):**
```powershell
Write-Host "📊 MAKİNE 1 DURUMU" -ForegroundColor Cyan
Write-Host "==================" -ForegroundColor Cyan

# Çalışan servisler
docker ps --format "table {{.Names}}\t{{.Status}}" --filter "name=ev-"

# Kayıtlı CP sayısı
$cpCount = (Invoke-WebRequest -Uri "http://localhost:8000/cp" -UseBasicParsing | ConvertFrom-Json).charging_points.Count
Write-Host "`n✅ Kayıtlı CP Sayısı: $cpCount/5" -ForegroundColor $(if ($cpCount -eq 5) {"Green"} else {"Yellow"})

# Dashboard URL
Write-Host "`n🌐 Dashboard: http://localhost:8000" -ForegroundColor Cyan
```

**Makine 2 (PowerShell):**
```powershell
Write-Host "📊 MAKİNE 2 DURUMU" -ForegroundColor Cyan
Write-Host "==================" -ForegroundColor Cyan

# Çalışan servisler
$cpEngines = (docker ps --filter "name=ev-cp-e" --format "{{.Names}}").Count
$cpMonitors = (docker ps --filter "name=ev-cp-m" --format "{{.Names}}").Count

Write-Host "✅ CP Engines: $cpEngines/5" -ForegroundColor $(if ($cpEngines -eq 5) {"Green"} else {"Red"})
Write-Host "✅ CP Monitors: $cpMonitors/5" -ForegroundColor $(if ($cpMonitors -eq 5) {"Green"} else {"Red"})

# Kayıt durumu
Write-Host "`n🔍 CP Monitor Kayıt Durumu:" -ForegroundColor Yellow
for ($i = 1; $i -le 5; $i++) {
    $cpNum = "{0:D3}" -f $i
    $registered = docker logs ev-cp-m-$cpNum 2>&1 | Select-String "registered with Central successfully"
    if ($registered) {
        Write-Host "   CP-$cpNum: ✅ KAYITLI" -ForegroundColor Green
    } else {
        Write-Host "   CP-$cpNum: ❌ KAYIT YOK" -ForegroundColor Red
    }
}
```

**Makine 3 (PowerShell):**
```powershell
Write-Host "📊 MAKİNE 3 DURUMU" -ForegroundColor Cyan
Write-Host "==================" -ForegroundColor Cyan

# Çalışan servisler
$driverCount = (docker ps --filter "name=ev-driver" --format "{{.Names}}").Count
Write-Host "✅ Drivers: $driverCount/5" -ForegroundColor $(if ($driverCount -eq 5) {"Green"} else {"Red"})

# Dashboard URL'leri
Write-Host "`n🌐 Driver Dashboards:" -ForegroundColor Cyan
Write-Host "   Alice:   http://localhost:8100"
Write-Host "   Bob:     http://localhost:8101"
Write-Host "   Charlie: http://localhost:8102"
Write-Host "   David:   http://localhost:8103"
Write-Host "   Eve:     http://localhost:8104"
```

---

### Adım 4.2: Uçtan Uca Test Senaryosu

**Bu testi tüm ekip birlikte yapın:**

**1️⃣ Makine 1'de: Dashboard'u Açın**
```powershell
# Browser'da aç
Start-Process "http://localhost:8000"
```

**Ne Görmeli:**
- ✅ 5 CP (CP-001 to CP-005) listede
- ✅ Her CP'nin state'i "ACTIVATED"
- ✅ "Active Sessions" bölümünde şarj sessionları

**2️⃣ Makine 3'te: Bir Driver Dashboard'u Açın**
```powershell
# Alice'in dashboard'unu aç
Start-Process "http://localhost:8100"
```

**Ne Görmeli:**
- ✅ "Current Charging Session" bölümü dolu
- ✅ CP ID (örn: CP-002)
- ✅ Charging progress bar ilerliyor
- ✅ Energy, Cost, Duration bilgileri güncelleniyor

**3️⃣ Makine 2'de: CP Loglarını İzleyin**
```powershell
# CP-001'in real-time loglarını izleyin
docker logs -f ev-cp-e-001

# Göreceksiniz:
# - State transitions (ACTIVATED → CHARGING)
# - Telemetry messages (energy, power, cost)
# - Session complete events
```

**4️⃣ Tüm Makinelerde: Log Akışını Gözlemleyin**

**Makine 1:**
```powershell
docker logs -f ev-central | Select-String "session|charge"
```

**Makine 2 (ayrı terminal):**
```powershell
docker logs -f ev-cp-e-001 | Select-String "CHARGING|telemetry"
```

**Makine 3 (ayrı terminal):**
```powershell
docker logs -f ev-driver-alice | Select-String "ACCEPTED|IN_PROGRESS|COMPLETED"
```

**✅ Başarı Kriterleri:**
- Central dashboard'da sessionlar görünüyor
- CP loglarında telemetry mesajları akıyor
- Driver dashboard'unda progress bar ilerliyor
- Tüm 3 makine logları eşzamanlı güncelleniyor

---

### Adım 4.3: Test Senaryosu - CP Crash ve Recovery

**Fault tolerance'ı test edelim:**

**Makine 2'de:**
```powershell
Write-Host "🔧 CP-003'ü crash ettiriyoruz..." -ForegroundColor Yellow

# CP-003 Engine'i durdur
docker stop ev-cp-e-003

Write-Host "⏳ 30 saniye bekleyin..." -ForegroundColor Cyan
Start-Sleep -Seconds 30
```

**Makine 1'de: Dashboard'u kontrol edin**
- CP-003'ün state'i "FAULTY" olmalı
- Diğer 4 CP hala "ACTIVATED" olmalı
- Sistem çalışmaya devam etmeli

**Makine 2'de: Recovery**
```powershell
Write-Host "🔧 CP-003'ü recover ediyoruz..." -ForegroundColor Green

# CP-003'ü yeniden başlat
docker start ev-cp-e-003

Write-Host "⏳ 10 saniye bekleyin..." -ForegroundColor Cyan
Start-Sleep -Seconds 10
```

**Makine 1'de: Dashboard'u tekrar kontrol edin**
- CP-003'ün state'i "FAULTY" → "ACTIVATED" olmalı
- Sistem tamamen geri dönmüş olmalı

**✅ Test Başarılı:**
- CP crash'i sistem çökmesine neden olmadı
- Diğer CP'ler etkilenmedi
- Recovery otomatik oldu

---

### Adım 4.4: Performans Gözlemi

**Makine 1'de: Sistem istatistiklerini görün**

```powershell
Write-Host "📊 SİSTEM İSTATİSTİKLERİ" -ForegroundColor Cyan
Write-Host "=======================" -ForegroundColor Cyan

# CP durumları
$cps = Invoke-WebRequest -Uri "http://localhost:8000/cp" -UseBasicParsing | ConvertFrom-Json | Select-Object -ExpandProperty charging_points

Write-Host "`n🔋 CP DURUMU:" -ForegroundColor Yellow
$cps | Select-Object cp_id, state, engine_state, kw_rate | Format-Table

Write-Host "`n📈 ÖZET:" -ForegroundColor Yellow
Write-Host "   Toplam CP: $($cps.Count)"
Write-Host "   Aktif: $(($cps | Where-Object {$_.engine_state -eq 'ACTIVATED'}).Count)"
Write-Host "   Şarj Yapan: $(($cps | Where-Object {$_.state -eq 'CHARGING'}).Count)"

# Container resource kullanımı
Write-Host "`n💻 RESOURCE KULLANIMI:" -ForegroundColor Yellow
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" --filter "name=ev-"
```

---

## ✅ Son Kontrol Listesi (Başarı Kriterleri)

Aşağıdaki tüm maddeleri kontrol edin:

### Makine 1 (Ana Sunucu):
- [ ] Kafka container'ı "Up" durumda
- [ ] Central container'ı "Up" durumda
- [ ] Dashboard http://localhost:8000 erişilebilir
- [ ] Dashboard'da 5 CP görünüyor
- [ ] Her CP'nin state'i "ACTIVATED"
- [ ] Active sessions bölümünde şarj sessionları var

### Makine 2 (Charging Points):
- [ ] 5 CP Engine container'ı "Up" durumda
- [ ] 5 CP Monitor container'ı "Up" durumda
- [ ] Her CP Monitor "registered successfully" log'u var
- [ ] CP Engine loglarında telemetry mesajları akıyor
- [ ] Environment variables doğru ayarlanmış

### Makine 3 (Drivers):
- [ ] 5 Driver container'ı "Up" durumda
- [ ] Driver dashboard'ları erişilebilir (8100-8104)
- [ ] Dashboard'larda charging sessions görünüyor
- [ ] Driver loglarında "ACCEPTED", "IN_PROGRESS" mesajları var
- [ ] Environment variables doğru ayarlanmış

### Genel Sistem:
- [ ] 3 makine arası network bağlantısı çalışıyor
- [ ] Firewall kuralları doğru ayarlanmış
- [ ] Log akışları tüm makinelerde eşzamanlı
- [ ] CP crash ve recovery test edildi ve başarılı
- [ ] Hiçbir container "Restarting" veya "Exited" durumda değil

---

## 🎓 Başarı! Sisteminiz Hazır

**Tebrikler! 🎉** 3 Windows bilgisayarında dağıtık EV Charging Simulation sisteminizi başarıyla kurdunuz!

### Ne Yaptınız:
✅ 3 makinede Docker kurulumu  
✅ Network bağlantılarını yapılandırma  
✅ Firewall kurallarını ayarlama  
✅ 17 servis (2 + 10 + 5) başarıyla başlatma  
✅ Uçtan uca sistemin çalıştığını doğrulama  

### Şimdi Ne Yapabilirsiniz:

1. **İzleme ve Gözlem:**
   - Makine 1: Central dashboard'dan tüm sistemi izleyin
   - Makine 2: CP loglarını takip edin
   - Makine 3: Driver dashboard'larından şarj sessionlarını gözlemleyin

2. **Test Senaryoları:**
   - CP crash simülasyonu (`docker stop ev-cp-e-XXX`)
   - Yeni CP ekleme (`.\add-cp.ps1 11 150.0 0.40`)
   - Yeni driver ekleme (`.\add-driver.ps1 frank 8105`)

3. **Öğrenme:**
   - Kafka mesajlarını inceleyin
   - State machine transitions'ları gözlemleyin
   - Circuit breaker pattern'ini test edin
   - Fault tolerance mekanizmalarını keşfedin

### Ek Kaynaklar:
- **[TROUBLESHOOTING_GUIDE.md](TROUBLESHOOTING_GUIDE.md)** - Sorun giderme
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Hızlı referans kartı
- **[WINDOWS_DEPLOYMENT.md](WINDOWS_DEPLOYMENT.md)** - Windows PowerShell detayları
- **[CRASH_RESILIENCE.md](CRASH_RESILIENCE.md)** - Fault tolerance testleri

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
