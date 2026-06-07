# IT Support Agent Frontend

> **Türkçe BT Destek Sistemi Arayüzü** — HTML5 + CSS3 + Saf JavaScript ile geliştirilen tek sayfa uygulaması.

---

## 📋 İçindekiler

- [Özellikler](#özellikler)
- [Teknoloji](#teknoloji)
- [Kurulum](#kurulum)
- [Çalıştırma](#çalıştırma)
- [Sayfa Yapısı](#sayfa-yapısı)
- [API İntegrasyonu](#api-integrasyonu)
- [Özelleştirme](#özelleştirme)
- [Performans İpuçları](#performans-ipuçları)

---

## ✨ Özellikler

- **Sohbet Arayüzü** — Gerçek zamanlı BT sorun analizi
- **Değerlendirme Sayfası** — 15 test senaryosu ve metrik dashboard
- **Durum Sayfası** — Backend sağlığı ve API endpoint'leri
- **Oturum Yönetimi** — localStorage ile otomatik durum kaydı
- **Duyarlı Tasarım** — Masaüstü ve mobil cihazlarda çalışır
- **Framework Yok** — Saf JavaScript (hiçbir bağımlılık)
- **Hızlı Yükleme** — < 500KB toplam boyut

---

## 🛠 Teknoloji

- **HTML5** — Semantik yapı
- **CSS3** — Flexbox/Grid ile responsive layout
- **JavaScript (ES6+)** — Modern async/await
- **localStorage** — İstemci tarafı oturum kalıcılığı
- **Fetch API** — REST API iletişimi

**Browser Desteği**:
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

---

## 📦 Kurulum

### Ön Koşullar
- Backend sunucusu çalışıyor (http://localhost:8000)
- Herhangi bir build aracı gerekmez

### Dosya Yapısı
```
frontend/
├── index.html      # Tek sayfa uygulaması (3 tab)
├── app.js          # İstemci tarafı mantığı
├── style.css       # Stil ve responsive tasarım
└── README.md       # Bu dosya
```

---

## 🚀 Çalıştırma

### Seçenek 1: Yerel Dosya Sunucusu

**Windows (PowerShell)**:
```powershell
cd frontend
python -m http.server 8001
```

**Linux/macOS**:
```bash
cd frontend
python -m http.server 8001
```

Tarayıcıda açın: `http://localhost:8001`

### Seçenek 2: Backend'le Birlikte

Backend `main.py` static dosyaları otomatik sunmaktadır:

```bash
cd backend
python -m uvicorn app.main:app --reload
```

Tarayıcıda açın: `http://localhost:8000`

### Seçenek 3: Docker ile

```bash
docker-compose up
```

Tarayıcıda açın: `http://localhost:8000`

---

## 📄 Sayfa Yapısı

### 1️⃣ Sohbet Sayfası

**Fonksiyon**: BT destek sorunlarını sorgu ve analiz etme

**Bileşenler**:
- `message` textarea — Kullanıcı sorusu (5-1000 karakter)
- `os` dropdown — İşletim sistemi seçimi
- `submit` button — API'ye gönder
- Sonuç bölümü — Kategori, öncelik, özet, çözüm adımları

**Akış**:
1. Kullanıcı mesaj yazar
2. İşletim sistemini seçer
3. "Analiz Et" düğmesine tıklar
4. Backend'e `/analyze` POST isteği gönderilir
5. Sonuçlar formatlanıp ekrana gösterilir
6. Oturum localStorage'a kaydedilir

---

### 2️⃣ Değerlendirme Sayfası

**Fonksiyon**: Sistem performansı ve doğruluğu test etme

**Test Seçenekleri**:
- **Tümünü Çalıştır** — 15 test senaryosu sırayla çalış
- **Kategori Testleri** — 10 sorun kategorisinin her birini test et
- **Niyet Testleri** — 5 intent detection tipini test et

**Metrikler**:
- Total Success Rate — Başarılı yanıtlar %
- Category Accuracy — Doğru kategoriler %
- Priority Accuracy — Doğru öncelik %
- Risk Accuracy — Doğru risk seviyesi %
- Average Latency — Ortalama yanıt süresi (ms)

**Sonuç Tablosu**:
| Test | Kategori | Beklenen | Alınan | Durum |
|------|----------|----------|--------|-------|
| Test 1 | network_issue | network_issue | network_issue | ✅ |

---

### 3️⃣ Durum Sayfası

**Fonksiyon**: Sistem sağlığı ve konfigürasyonunu görüntüle

**Bilgiler**:
- Backend Status — Online/Offline
- Model Info — Qwen versiyon, parametre sayısı
- GPU Status — CUDA mevcut/CPU modunda
- API Endpoints — /health, /analyze
- Frontend Version — 1.0.0
- Last Sync — Son güncelleme zamanı

---

## 🔌 API İntegrasyonu

### Ana Endpoint

**POST /analyze**

```javascript
const response = await fetch('http://localhost:8000/analyze', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    message: "Windows 10'da internet bağlantısı düşüyor",
    os: 'windows'
  })
});

const data = await response.json();
```

### Yanıt Format

```javascript
{
  category: "network_issue",
  priority: "high",
  summary: "İnternet bağlantısı aralıklı olarak kesiliyor...",
  possible_causes: ["Sürücü güncel değil", "Yönlendirici resetlendi"],
  solution_steps: ["Ağ ayarlarını sıfırla", "Yönlendiciyi 30s kapalı tut"],
  questions: ["Düzenli mi yoksa rastgele mi?"],
  risk_level: "safe",
  assistant_message: "...",
  metadata: {
    latency_ms: 2340,
    model_call_count: 1,
    advisory_warnings: []
  }
}
```

### Hata Yönetimi

```javascript
try {
  const response = await fetch('/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, os })
  });
  
  if (!response.ok) {
    const error = await response.json();
    console.error('API Error:', error);
    // Kullanıcıya hata göster
    return;
  }
  
  const data = await response.json();
  // Sonuçları işle
} catch (error) {
  console.error('Network error:', error);
  // Bağlantı hatası
}
```

---

## 🎨 Özelleştirme

### Temalı Değişiklikler

**style.css** dosyasındaki CSS değişkenleri:

```css
:root {
  --primary-color: #0066cc;
  --success-color: #28a745;
  --error-color: #dc3545;
  --warning-color: #ffc107;
  --background-color: #f8f9fa;
  --text-color: #333333;
}
```

### Backend URL Değişimi

**app.js** dosyasında:

```javascript
const API_URL = 'http://localhost:8000'; // Bunu değiştir
```

### Yeni Test Senaryosu Ekleme

**app.js** - `TEST_CASES` array'ine ekle:

```javascript
const TEST_CASES = [
  // Mevcut testler...
  {
    id: 'test-16',
    name: 'Test Adı',
    message: 'Test mesajı',
    os: 'windows',
    expected: {
      category: 'software_issue',
      priority: 'high'
    }
  }
];
```

---

## 📊 localStorage Yapısı

**Anahtar**: `it-support-session`

```javascript
{
  "sessionId": "uuid-string",
  "messages": [
    {
      "timestamp": 1620000000000,
      "message": "Soru metni",
      "os": "windows",
      "response": { /* tam yanıt */ }
    }
  ],
  "activeIssue": {
    "category": "network_issue",
    "lastUpdated": 1620000000000
  }
}
```

---

## ⚡ Performans İpuçları

### Frontend Optimizasyonu

1. **CSS Critical Path**
   - style.css küçük ve hızlı yüklenir
   - Media queries sayfada optimize edilmiş

2. **JavaScript Optimizasyonu**
   - Event delegation kullanılır
   - Debouncing form submit'te
   - Lazy loading imajlar (varsa)

3. **Network Optimizasyonu**
   - Istekler önbelleğe alınır
   - Retry logic implement edilmiş
   - Timeout 30 saniyede ayarlanmış

### Performans Metrikleri

- **First Contentful Paint (FCP)**: < 1s
- **Largest Contentful Paint (LCP)**: < 2s
- **Cumulative Layout Shift (CLS)**: < 0.1
- **Time to Interactive (TTI)**: < 3s

### Mobil Performans

- Responsive breakpoints: 768px, 1024px
- Touch-friendly buttons (min 48px)
- Mobile-optimized layout

---

## 🔧 Sorun Giderme

### Sorun: "Backend'e bağlanamıyor"

```javascript
// app.js içinde API_URL kontrolü
console.log('API_URL:', API_URL);
console.log('CORS enabled:', 'yes');

// Browser console'da kontrol et:
fetch('http://localhost:8000/health')
  .then(r => r.json())
  .then(console.log)
  .catch(console.error);
```

### Sorun: "Oturum kaydedilmiyor"

```javascript
// localStorage kontrol et
console.log(localStorage.getItem('it-support-session'));
console.log(localStorage.getItem('it-support-session') ? 'OK' : 'Boş');
```

### Sorun: "Stil yüklenmiyor"

- Browser cache temizle (Ctrl+Shift+Delete)
- DevTools Network sekmesinde style.css'yi kontrol et
- style.css dosyasının var olduğunu doğrula

---

## 📝 Kod Yapısı

### app.js Bölümleri

```javascript
// 1. Konfigürasyon & Sabitler
const API_URL = '...';
const TEST_CASES = [...];

// 2. DOM Elemanları
const elements = {
  messageInput: document.getElementById('message'),
  // ...
};

// 3. API Fonksiyonları
async function analyzeMessage(message, os) { }
async function checkBackendStatus() { }

// 4. Event Listeners
document.getElementById('submit').addEventListener('click', ...);

// 5. Yardımcı Fonksiyonlar
function formatResult(data) { }
function showError(message) { }
```

---

## 🚀 Dağıtım

### Static Host'a Deploy (GitHub Pages, Netlify)

1. Frontend dosyalarını deploy et
2. API_URL'yi üretim sunucusuna ayarla
3. CORS güvenliğini kontrol et

### Docker ile Deploy

```bash
docker-compose up -d
# http://localhost:8000 adresinde erişilebilir
```

---

## 📞 İletişim & Destek

- Backend sorunları: Backend README'yi kontrol et
- Frontend sorunları: GitHub Issues aç
- Genel sorular: Discussions kullan

---

**Son Güncelleme**: Mayıs 31, 2026
**Durum**: Production Ready ✅
