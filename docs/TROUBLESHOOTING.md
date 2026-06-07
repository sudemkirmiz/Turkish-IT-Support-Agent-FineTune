## Model Meta Tensor Hatası - Çözüm Rehberi

**Hata Mesajı:**
```
Cannot copy out of meta tensor; no data!
```

---

## 🔍 Sorunun Sebebi

Bu hata, LoRA adaptörü yükleme sırasında meta tensors (placeholder tensors) ile çalışmaya çalışırken ortaya çıkıyor. Genellikle:

1. **PEFT/LoRA yükleme sorunu** - Adaptörlerin tam yüklenmemesi
2. **Device mismatch** - Model ve input'lar farklı cihazlarda
3. **Meta tensor initialization** - Model ağırlıkları placeholder olarak kalması

---

## ✅ Çözümler (Sırasıyla Deneyin)

### Çözüm 1: Backend Kodu Güncelle ⭐ (ÖNERİLEN)

Backend'deki `model_service.py` güncellenmiş ve **3 stratejili fallback** mekanizması eklenmiş:

**Strategi 1:** AutoPeftModelForCausalLM (normal)  
**Strategi 2:** Base Model + Manual LoRA (meta tensor fix)  
**Strategi 3:** CPU fallback (GPU sorunu varsa)

**Dosya:** `backend/app/model_service.py`

Dosya zaten güncellendi. Backend'i yeniden başlatın:

```powershell
cd backend
$env:KMP_DUPLICATE_LIB_OK="TRUE"
python -m uvicorn app.main:app --reload --port 8000
```

---

### Çözüm 2: Ortam Değişkenlerini Kontrol Et

**File:** `backend/.env`

```env
# ✅ DOĞRU AYARLAR:
FINE_TUNED_MODEL_NAME=oguzinyo/qwen2.5-3b-it-support-lora-v2
MODEL_LOCAL_FILES_ONLY=false
MODEL_MAX_NEW_TOKENS=384
MODEL_MAX_GENERATION_SECONDS=120

# CPU'da çalıştırmak isterseniz:
CUDA_VISIBLE_DEVICES=
```

---

### Çözüm 3: Model'i Manuel Test Et

**File:** `backend/debug_model_loading.py` (hazırlanmış)

```bash
cd backend
$env:KMP_DUPLICATE_LIB_OK="TRUE"
python debug_model_loading.py
```

Bu script:
- 3 farklı yükleme stratejisini dener
- Meta tensors olup olmadığını kontrol eder
- Çıkarım testini çalıştırır
- Detaylı hata mesajları gösterir

---

### Çözüm 4: Bağımlılıkları Güncelle

Meta tensor sorunu bazen PyTorch/Transformers sürüm uyumsuzluğundan kaynaklanır:

```bash
cd backend

# Bağımlılıkları kaldır
pip uninstall torch transformers peft -y

# Yeniden kur
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install transformers==4.40.0
pip install peft==0.11.1
pip install accelerate
pip install bitsandbytes
```

---

### Çözüm 5: CUDA Devre Dışı Bırak (Test için)

GPU'dan kaynaklanan sorun varsa CPU'da test et:

```bash
$env:CUDA_VISIBLE_DEVICES=""
python -m uvicorn app.main:app --port 8000
```

---

### Çözüm 6: Model Cache'ini Temizle

Corruptted cache dosyaları sorun yaratabilir:

**Windows:**
```powershell
Remove-Item -Recurse -Force "$env:USERPROFILE\.cache\huggingface"
```

**Linux/macOS:**
```bash
rm -rf ~/.cache/huggingface
```

Sonra yeniden başlat:
```bash
python -m uvicorn app.main:app --port 8000
```

---

## 🧪 Test Etme

### 1. Health Check
```bash
curl http://127.0.0.1:8000/health
```

### 2. Simple Request
```bash
curl -X POST "http://127.0.0.1:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Wi-Fi bagli ama internete giremiyorum.",
    "os": "Windows"
  }'
```

### 3. Debug Mode
Backend loglarını kontrol et:
```
2026-06-08 XX:XX:XX,XXX - app.model_service - INFO - 🔄 Analiz başlanıyor...
2026-06-08 XX:XX:XX,XXX - app.model_service - DEBUG - ✓ Model zaten yüklü, cache'den kullanılıyor
2026-06-08 XX:XX:XX,XXX - app.model_service - INFO - ✅ Analiz tamamlandı
```

---

## 📊 Performans Beklentileri

| Senaryo | Süre | Status |
|---------|------|--------|
| İlk çalıştırma (model yükle) | 30-60s | Normal |
| Normal request (GPU) | 2-4s | Hızlı ✅ |
| Normal request (CPU) | 10-30s | Yavaş |
| Timeout | > 120s | Hata |

---

## 🆘 Eğer Hala Sorun Varsa

### Loglarda Ne Arayacaksınız?

✅ **Başarı İşaretleri:**
```
✓ Model yüklendi (Device: cuda:0)
✓ LoRA adaptörleri direkt kullanılıyor
✓ Model eval mode'a alındı
✅ Analiz tamamlandı
```

❌ **Hata İşaretleri:**
```
Cannot copy out of meta tensor  → Çözüm 2-3'ü deneyin
CUDA out of memory            → Çözüm 5'i (CPU fallback)
Model yüklemesi başarısız     → Çözüm 4'ü (güncelleme)
```

### GitHub Issues'a Rapor Verin

Eğer sorun devam ederse:
1. `debug_model_loading.py` çıktısını kaydedin
2. Backend log'unu (`stderr`) kaydedin
3. Sistem info'nu kaydedin:
```bash
nvidia-smi  # GPU info
python -c "import torch; print(torch.__version__)"  # PyTorch version
python -c "import peft; print(peft.__version__)"    # PEFT version
```

---

## 📝 Notlar

- Meta tensor sorunu **prodüktif bir çözüm olmadığı için**, fallback stratejiler eklenmiş
- Qwen2.5-3B çok hızlı olması için optimizasyonlar yapıldı
- PEFT LoRA adaptörleri direkt kullanılıyor (merge kapatılı - stability için)

---

**Made with ❤️ for Debugging**
