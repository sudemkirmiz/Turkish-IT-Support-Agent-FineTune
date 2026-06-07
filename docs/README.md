# Dokümantasyon

Bu klasör proje hakkında detaylı dokümantasyon içerir.

---

## 📚 Dosyalar

### [`fine_tune_process.md`](fine_tune_process.md)
**Fine-Tune Süreci (20KB+)**
- Model mimarisi (Qwen 2.5-3B)
- Eğitim teknolojileri (QLoRA + Unsloth)
- Eğitim konfigürasyonu ve hiperparametreler
- Adım adım eğitim süreci
- Değerlendirme metrikleri
- Model merge ve deployment
- Bilinen sorunlar ve çözümleri

**Kimin Okuması Gerekir:**
- ML engineers
- Fine-tune ile ilgilenenler
- Model geliştirmeyi merak edenler

---

### [`technical_documentation.md`](technical_documentation.md)
**Teknik Dokümantasyon**
- Proje mimarisi
- Bileşen açıklamaları
- Data flow
- Runtime notları

**Kimin Okuması Gerekir:**
- Backend developers
- DevOps engineers
- Sistem yöneticileri

---

### [`model_quality_notes.md`](model_quality_notes.md)
**Model Kalitesi Notları**
- Performans metrikleri
- Bilinen limitasyonlar
- İyileştirme fırsatları
- Test sonuçları

**Kimin Okuması Gerekir:**
- QA/testing team
- Product managers
- Stakeholders

---

### [`TROUBLESHOOTING.md`](TROUBLESHOOTING.md)
**Sorun Giderme Rehberi**
- Meta tensor hatası çözümü
- Yaygın hatalar ve çözümleri
- Debug scriptleri
- Performans optimizasyonları

**Kimin Okuması Gerekir:**
- Developers (kurulum/deployment sırasında)
- DevOps engineers
- Support team

---

### [`API.md`](API.md) (opsiyonel)
**API Referansı**
- Detaylı endpoint dokümantasyonu
- Request/response örnekleri
- Error codes
- Rate limiting

---

## 📖 Hızlı Referans

| Başlık | Dosya | Sürü | Konu |
|--------|-------|------|------|
| Fine-Tune | [fine_tune_process.md](fine_tune_process.md) | 20KB+ | Model eğitimi |
| Teknik | [technical_documentation.md](technical_documentation.md) | 5KB | Mimari |
| Kalite | [model_quality_notes.md](model_quality_notes.md) | 3KB | Test sonuçları |
| Sorun Gid. | [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | 10KB | Hata çözümleri |

---

## 🔗 Ana Repo Linkleri

- **Main README**: [`../README.md`](../README.md)
- **Backend**: [`../backend/README.md`](../backend/README.md) (varsa)
- **Frontend**: [`../frontend/README.md`](../frontend/README.md)
- **Dataset**: [`../dataset/README.md`](../dataset/README.md)

---

## 🚀 Kullanım Senaryoları

### Senaryo 1: Fine-Tune Yapmak İstiyorum
1. [`fine_tune_process.md`](fine_tune_process.md) oku
2. Jupyter notebooks'u GitHub'dan indir
3. Google Colab'da çalıştır

### Senaryo 2: Backend Kurulumu Yapmak İstiyorum
1. Ana [`README.md`](../README.md) oku
2. Hata alırsan [`TROUBLESHOOTING.md`](TROUBLESHOOTING.md) kontrol et
3. [`technical_documentation.md`](technical_documentation.md) oku

### Senaryo 3: Proje Hakkında Genel Bilgi İstiyorum
1. Ana [`README.md`](../README.md) oku
2. [`technical_documentation.md`](technical_documentation.md) oku
3. [`model_quality_notes.md`](model_quality_notes.md) oku

---

## 📝 Dökümentasyon Katkısı

Dökümentasyonu geliştirmek istiyorsan:

1. **Typo buldum**: Issue açıp linki paylaş
2. **Cümle daha açık olabilir**: PR aç (CONTRIBUTING.md oku)
3. **Yeni bölüm eklemek istiyorum**: Önce issue aç, discuss et

---

## 🔍 Dokümantasyon Standartları

Tüm dokümantasyon:
- ✅ Türkçe yazılmış
- ✅ Markdown formatında
- ✅ İçindekiler (TOC) içeriyor
- ✅ Kod örnekleri içeriyor
- ✅ Links/referanslar içeriyor
- ✅ Son güncelleme tarihi belirtilmiş

---

## 📞 Sorular veya Sorunlar?

- **Technical Issues**: GitHub Issues aç
- **Documentation Questions**: GitHub Discussions kullan
- **General Support**: support@example.com

---

**Last Updated:** 2026-06-08  
**Maintainer:** IT Support Agent Team
