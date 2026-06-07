# Backend Scripts

Utility ve test scriptleri.

---

## 📜 Dosyalar

### `debug_model_loading.py`
**Model Yükleme Debug Script'i**

Qwen 2.5-3B LoRA model yüklemesini test et. Meta tensor ve diğer sorunları diagnoz et.

**Kullanım:**
```bash
cd backend
$env:KMP_DUPLICATE_LIB_OK="TRUE"
python scripts/debug_model_loading.py
```

**Output:**
- ✅ Environment check (Python, PyTorch, CUDA)
- ✅ Model loading attempts (3 strategy)
- ✅ Meta tensor detection
- ✅ Inference test
- ✅ Detailed error messages

**Çıktı Örnekleri:**
```
[INFO] ENVIRONMENT CHECK
Python: 3.13.9
PyTorch: 2.0.1
CUDA Available: True
CUDA Device: NVIDIA A100
VRAM: 40.00 GB

[INFO] MODEL LOADING TEST
>> Attempt 1: AutoPeftModelForCausalLM.from_pretrained()
[SUCCESS] Model loaded!
  - Model device: cuda:0
[SUCCESS] No meta tensors found

[INFO] INFERENCE TEST
[SUCCESS] Tokenized: torch.Size([1, 28])
[SUCCESS] Generation successful: torch.Size([1, 142])
Output: ...
```

---

### `merge_adapter.py`
**LoRA Adapter Merge Script'i**

PEFT LoRA adaptörlerini base model ile merge et. Merged model'ı Hugging Face'e yükle.

**Kullanım:**
```bash
cd backend
python scripts/merge_adapter.py \
    --base "Qwen/Qwen2.5-3B-Instruct" \
    --adapter "oguzinyo/qwen2.5-3b-it-support-lora-v2" \
    --output "./merged_model"
```

**Flags:**
- `--base`: Base model adı (Hugging Face)
- `--adapter`: LoRA adapter repo
- `--output`: Merge edilmiş model çıkış klasörü
- `--push_to_hub`: Hugging Face'e otomatik yükle (opsiyonel)

**Çıkış:**
```
Merged model saved to: ./merged_model
- model.safetensors (3.2GB)
- config.json
- tokenizer.json
```

---

### `test_conversation_flow.py`
**Konuşma Akışı Test Script'i**

Farklı intent kategorilerine karşılık backend'in davranışını test et.

**Kullanım:**
```bash
cd backend
python scripts/test_conversation_flow.py
```

**Test Kategorileri:**
- Technical issues (Teknik sorular)
- Follow-up questions (Takip soruları)
- Small talk (Konuşma)
- Out of scope (Kapsam dışı)
- Unclear (Belirsiz)

---

### `test_real_model.py`
**Gerçek Model Test Script'i**

Qwen modelini gerçek sorunlarla test et. Kategori doğruluğunu kontrol et.

**Kullanım:**
```bash
cd backend
python scripts/test_real_model.py
```

**Test Verileri:**
```python
{
    "message": "Wi-Fi bağlı ama internete giremiyorum.",
    "os": "Windows",
    "expected_category": "network_issue"
}
```

**Output:**
```
Test 1: network_issue
  Input: Wi-Fi bağlı ama internete giremiyorum.
  Predicted: network_issue ✅
  Priority: high
  Risk: safe

[15/15 passed] ✅
Accuracy: 100%
```

---

## 🚀 Quick Start

### Koşu Ortamı Setup

```bash
cd backend

# Python environment
conda create -n it-support-dev python=3.13.9
conda activate it-support-dev

# Dependencies
pip install -r requirements.txt
```

### Tüm Scriptleri Çalıştır

```bash
# Debug
python scripts/debug_model_loading.py

# Test real model
python scripts/test_real_model.py

# Test conversation flow
python scripts/test_conversation_flow.py
```

---

## 📋 Script Özeti

| Script | Amaç | Süre | Output |
|--------|------|------|--------|
| `debug_model_loading.py` | Model yükleme test | 2-5 min | Detailed logs |
| `merge_adapter.py` | LoRA merge | 10-30 min | Merged model |
| `test_conversation_flow.py` | Intent detection | 1 min | Pass/fail |
| `test_real_model.py` | Model accuracy | 3-10 min | Accuracy score |

---

## 🔧 Script Parametreleri

### debug_model_loading.py
```
No parameters needed
```

### merge_adapter.py
```
--base MODEL              Base model name (default: Qwen/Qwen2.5-3B-Instruct)
--adapter MODEL           LoRA adapter repo
--output PATH             Output directory (default: ./merged_model)
--push_to_hub             Push to HF Hub (optional)
--token HF_TOKEN          Hugging Face token (for push_to_hub)
```

### test_conversation_flow.py
```
--iterations N            Number of iterations (default: 1)
--verbose                 Detailed output
```

### test_real_model.py
```
--dataset PATH            Test dataset JSONL (default: ../dataset/test.jsonl)
--verbose                 Show predictions
--save_report PATH        Save report to file
```

---

## 📊 Output Formatları

### debug_model_loading.py
```
== ENVIRONMENT CHECK ==
[INFO] Python: 3.13.9
[INFO] PyTorch: 2.0.1
[INFO] CUDA Available: True

== MODEL LOADING TEST ==
[INFO] Strategy 1: AutoPeftModelForCausalLM...
[SUCCESS] Model loaded!

== INFERENCE TEST ==
[SUCCESS] Generation complete
```

### test_real_model.py
```
Category Accuracy: 95.8%
Priority F1-Score: 93.2%
Risk Level Accuracy: 94.1%

[Passed: 14/15]
[Failed: 1/15]
```

---

## 🐛 Troubleshooting

### "OMP: Error #15: Initializing libiomp5md.dll"
```bash
$env:KMP_DUPLICATE_LIB_OK="TRUE"
python scripts/debug_model_loading.py
```

### "CUDA out of memory"
```bash
$env:CUDA_VISIBLE_DEVICES=""  # CPU fallback
python scripts/debug_model_loading.py
```

### "Model not found"
```bash
# Model'ü indirmek zorunlu
python -c "from transformers import AutoTokenizer; AutoTokenizer.from_pretrained('Qwen/Qwen2.5-3B-Instruct')"
```

---

## 📝 Notlar

- Tüm scriptler `backend/` klasöründen çalıştırılmalıdır
- `KMP_DUPLICATE_LIB_OK=TRUE` gerekli olabilir
- Model indirme 5-15 dakika sürebilir (ilk çalıştırma)
- Test verileri `../dataset/` klasöründedir

---

## 🤝 Katkı

Yeni scriptler eklemek istiyorsan:
1. `docs/`'e Markdown belge ekle
2. Docstrings ekle
3. Test coverage %90+ olsun
4. README.md'yi güncelle

---

**Last Updated:** 2026-06-08
