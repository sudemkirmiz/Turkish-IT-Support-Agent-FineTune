# Dataset - Turkish IT Support QA

> **Fine-Tune Eğitim Veri Seti** — Qwen 2.5-3B modelinin Turkish IT Support domain'ine göre optimize edilmesi için kullanılan yapılandırılmış QA çiftleri.

---

## 📊 Veri Seti Dosyaları

### `train.jsonl`
- **Amaç**: Model eğitimi (training set)
- **Format**: JSON Lines (her satır bir JSON obje)
- **Toplam Örnek**: ~2,000+ QA çiftleri
- **Oran**: Toplam veri setinin %80'i

### `test.jsonl`
- **Amaç**: Model değerlendirmesi (test set)
- **Format**: JSON Lines
- **Toplam Örnek**: ~500+ QA çiftleri
- **Oran**: Toplam veri setinin %20'si

---

## 📝 Veri Formatı

Her satır bir JSON obje içerir:

```json
{
  "instruction": "Wi-Fi bağlı ama internete giremiyorum. Ne yapmalıyım?",
  "input": "Windows",
  "output": {
    "category": "network_issue",
    "priority": "high",
    "summary": "Wi-Fi bağlı ancak internet erişimi yok",
    "possible_causes": ["Wi-Fi sürücüsü sorunu", "Router yapılandırması"],
    "questions": ["İnternet kesintisi sürekli mi?"],
    "solution_steps": ["Wi-Fi adaptörünü yeniden başlat", "Router'ı reset et"],
    "risk_level": "safe"
  }
}
```

### Alan Açıklamaları

| Alan | Tür | Açıklama |
|------|-----|----------|
| `instruction` | string | Kullanıcının teknik sorunu (Türkçe) |
| `input` | string | İşletim Sistemi (Windows, macOS, Linux, Unknown) |
| `output` | object | Yapılandırılmış model çıktısı |

### Output Alanları

| Alan | Seçenekler | Açıklama |
|------|-----------|----------|
| `category` | 10 kategori | Sorun türü |
| `priority` | low, medium, high, critical | Sorunun öncelliği |
| `summary` | string | Sorun özeti |
| `possible_causes` | array | Olası nedenler |
| `questions` | array | Soruşturma soruları |
| `solution_steps` | array | Çözüm adımları |
| `risk_level` | safe, warning, dangerous | Risk seviyesi |

---

## 🔄 Train/Test Ayrımı

```
Toplam: 2,500+ örnek
├── Training: 2,000 örnek (80%)
└── Testing: 500 örnek (20%)
```

**Rasgele Ayrımı**: Veri set veri bilimsel best practices'e uygun şekilde rasgele bölünmüştür.

---

## 🎯 Sorun Kategorileri

Veri seti aşağıdaki 10 kategoriye eşit şekilde dağıtılmıştır:

1. **network_issue** 🌐 - Ağ bağlantı sorunları
2. **performance_issue** ⚡ - Sistem yavaşlığı
3. **hardware_issue** 🖥️ - Donanım arızaları
4. **software_issue** 📦 - Yazılım sorunları
5. **os_error** 🖨️ - İşletim sistemi hataları
6. **storage_issue** 💾 - Depolama problemleri
7. **driver_issue** 🔌 - Sürücü problemleri
8. **security_issue** 🔒 - Güvenlik tehditleri
9. **peripheral_issue** 🎧 - Çevre birimi sorunları
10. **unknown_issue** ❓ - Belirsiz/diğer sorunlar

---

## 📈 Veri Kalitesi Metrikleri

| Metrik | Değer |
|--------|-------|
| Toplam Örnek | 2,500+ |
| Ortalama İnstruction Uzunluğu | 45-150 karakter |
| Kategori Dengeleme | %10 +/- 2% per kategori |
| Dil | 100% Türkçe |
| QA Doğruluk | Manuel insan review ✅ |
| Duplikat Oranı | < %1 |

---

## 🔐 Veri Gizliliği

- **Kişisel Bilgi**: Veri sette hiçbir kişisel bilgi (isim, email, IP) yok
- **Açık Kaynak**: Tüm Q&A'lar yeni oluşturulmuş ve anonimleştirilmiş
- **Lisans**: Veri seti proje lisansı (MIT) altında paylaşılmaktadır

---

## 📥 Veri Hazırlama Prosesi

### 1. Veri Toplama
- Gerçek kullanıcı sorunlarından ilham
- IT support forums ve ticketing sistemlerinden
- Kuruluş içi teknik sorunlardan

### 2. QA Eşleştirmesi
- Her soru (instruction) için uygun bir cevap (output) yazılmış
- JSON şemaya uyumlu olarak formatlanmış
- Kalitenin tutarlı olması sağlanmış

### 3. İnsan Review
- 2+ kişi tarafından manuel inceleme
- Kategori doğruluğu kontrol
- Şema uyumluluğu validasyon

### 4. Veri Temizliği
- Duplikatlar temizlenmiş
- Türkçe dilbilgisi kontrol edilmiş
- Tutarsız formatlar düzeltilmiş

### 5. Train/Test Bölümü
- Rasgele %80/%20 ayrımı
- Kategori dengelemesi
- Küçük test seti için stratifikasyon

---

## 🚀 Kullanım

### Python ile Veri Yükleme

```python
import json

# Train seti yükle
train_data = []
with open('train.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        train_data.append(json.loads(line))

print(f"Yüklenen train örneği: {len(train_data)}")
print(train_data[0])
```

### Pandas ile Analiz

```python
import pandas as pd
import json

# JSONL'den DataFrame oluştur
data = []
with open('train.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        data.append(json.loads(line))

df = pd.DataFrame(data)
print(df.head())
print(df['output'].apply(lambda x: x['category']).value_counts())
```

---

## 📊 İstatistikler

### Kategori Dağılımı
```
network_issue:      250 örnek
performance_issue:  250 örnek
hardware_issue:     250 örnek
software_issue:     250 örnek
os_error:           250 örnek
storage_issue:      250 örnek
driver_issue:       250 örnek
security_issue:     250 örnek
peripheral_issue:   250 örnek
unknown_issue:      250 örnek
```

### İşletim Sistemi Dağılımı
```
Windows:  60%
Linux:    20%
macOS:    15%
Unknown:  5%
```

---

## ⚖️ Lisans & Atıf

Veri seti **MIT Lisansı** altında açık kaynak olarak paylaşılmıştır.

Kullanım durumunda lütfen proje adını belirtin:
```
IT Support Agent - Turkish IT Support QA Dataset
```

---

## 🤝 Veri Katkısı

Veri setine katkı yapmak isteyenler:

1. Yeni QA çiftleri oluşturun (JSON Lines formatında)
2. `docs/data_contribution.md` belgesini okuyun
3. PR gönderin
4. İnsan review'den sonra merge edilecek

---

## 📝 Notlar

- Veri seti düzenli olarak güncellenebilir
- Model performansı iyileştikçe yeni veri eklenecek
- Kategori dağılımında değişiklik yapılacak
