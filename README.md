# Fine Tune Edilmiş IT Support Agent 

> **AI destekli Türkçe BT destek sistemi** — Fine-tuned LLM, model-only backend mimarisi ve semantik doğrulama hattı ile teknik sorun analizi, sınıflandırması ve çözüm önerisi sunan IT uygulaması.

![Python 3.13](https://img.shields.io/badge/python-3.13.9-blue)
![FastAPI](https://img.shields.io/badge/fastapi-latest-009688)
![PyTorch](https://img.shields.io/badge/pytorch-with%20cuda-ee4c2c)
![Testler](https://img.shields.io/badge/testler-50%2F50%20geçti-brightgreen)

## Proje Özeti

Bu proje, kullanıcıların teknik problemlerini fine-tune edilmiş bir model ile analiz eden Türkçe IT destek asistanıdır. Backend modeli çağırır, modelin JSON çıktısını parse eder ve doğrular. Frontend ise sohbet arayüzü, teknik detaylar, oturum geçmişi, model değerlendirme ekranı ve sistem durumu ekranı sunar.

Fine-tune süreci ekip çalışmasıyla yürütülmüştür. Backend ve frontend entegrasyonu proje kapsamında uçtan uca geliştirilmiştir.

## Özellikler

- **Fine-tuned model entegrasyonu** — Qwen tabanlı LoRA adapter modeli kullanır.
- **Model-only backend mimarisi** — Backend hazır cevap üretmez, model cevabını doğrular.
- **JSON parse ve validation** — Model çıktısı şema, alan tipi ve güvenlik kontrollerinden geçer.
- **Niyet tespiti** — Teknik sorun, takip mesajı, smalltalk, kapsam dışı ve belirsiz mesajları ayırır.
- **Sohbet geçmişi** — Frontend localStorage ve backend session store ile bağlam korunur.
- **OS seçimi** — Windows, macOS, Linux ve Unknown OS desteklenir.
- **Teknik detaylar alanı** — Kategori, öncelik, risk, model metadata ve advisory uyarıları gösterilir.
- **Evaluation dashboard** — Hazır senaryolarla model çıktıları test edilebilir.
- **Sistem durumu ekranı** — Backend health ve model bilgileri arayüzden görülebilir.

## Ekran Görüntüleri

Destek asistanı:

![Destek Asistanı](docs/screenshots/destek_asistanı.png)

Model değerlendirme:

![Model Değerlendirme](docs/screenshots/model_değerlendirme.png)

Sistem durumu:

![Sistem Durumu](docs/screenshots/sistem_durumu.png)

## Teknoloji Yığını

Backend:

- FastAPI
- Pydantic v2
- PyTorch
- Hugging Face Transformers
- PEFT / LoRA
- Uvicorn
- pytest

Frontend:

- HTML5
- CSS3
- Vanilla JavaScript
- localStorage
- Fetch API

Model ve fine-tune:

- Base model: `Qwen/Qwen2.5-3B-Instruct`
- Eğitim yöntemi: QLoRA + Unsloth
- Eğitim ortamı: Google Colab T4 GPU
- LoRA adapter: `oguzinyo/qwen2.5-3b-it-support-lora-v2`

## Model-Only Mimari

- Backend hazır teknik cevap üretmez.
- Mock/template/fallback/policy response kullanılmaz.
- Başarılı cevaplar fine-tuned modelden gelir.
- Model geçersiz JSON üretirse aynı modelle retry yapılır.
- Retry başarısız olursa API `502` dönebilir.
- Cevap kalitesi dataset ve fine-tune kalitesine bağlıdır.

```text
Frontend
  -> FastAPI Backend
    -> Intent Router
    -> Prompt Builder
    -> Fine-tuned Model
    -> JSON Extraction
    -> Schema + Semantic Validation
    -> Frontend Render
```

## Ana Bileşenler

| Bileşen | Amaç |
| --- | --- |
| `backend/app/main.py` | API endpointleri ve analiz akışı |
| `backend/app/model_service.py` | Model yükleme, inference ve GPU/CPU yönetimi |
| `backend/app/prompts.py` | Prompt şablonları |
| `backend/app/conversation_router.py` | Intent tespiti ve takip mesajı yardımcıları |
| `backend/app/response_normalizer.py` | Normalizasyon, blocking ve advisory validation |
| `backend/app/json_utils.py` | Model çıktısından JSON çıkarımı |
| `backend/app/schemas.py` | Pydantic request/response modelleri |
| `backend/app/session_store.py` | Oturum ve konuşma bağlamı |

## Kullanılan Model

```ini
FINE_TUNED_MODEL_NAME=oguzinyo/qwen2.5-3b-it-support-lora-v2
```

## JSON Response Formatı

Model cevabında beklenen ana alanlar:

- `category`
- `priority`
- `summary`
- `possible_causes`
- `questions`
- `solution_steps`
- `risk_level`
- `assistant_message` opsiyonel

`assistant_message` yalnızca frontend'de daha doğal gösterim için kullanılır; zorunlu yapılandırılmış alanların yerine geçmez.

Örnek:

```json
{
  "category": "network_issue",
  "priority": "medium",
  "summary": "Kullanıcı Wi-Fi bağlı olduğu halde internete erişemediğini belirtiyor.",
  "possible_causes": ["DNS problemi", "Modem veya yönlendirici sorunu"],
  "questions": ["Aynı ağdaki diğer cihazlar internete girebiliyor mu?"],
  "solution_steps": ["Wi-Fi bağlantısını kapatıp tekrar açın.", "Modemi yeniden başlatın."],
  "risk_level": "safe",
  "assistant_message": "Wi-Fi bağlı görünüp internet erişimi olmadığında önce ağ ve DNS tarafını kontrol edebiliriz."
}
```

## Kurulum

Ön koşullar:

- Python 3.11+ önerilir; proje Python 3.13.9 ile test edilmiştir.
- Conda veya Python sanal ortamı kullanılabilir.
- NVIDIA GPU opsiyoneldir; CPU ile de çalışabilir ancak daha yavaş olabilir.

```powershell
git clone https://github.com/sudemkirmiz/Turkish-IT-Support-Agent-FineTune.git
cd Turkish-IT-Support-Agent-FineTune
cd backend
pip install -r requirements.txt
```

## Backend Çalıştırma

PowerShell:

```powershell
cd backend
$env:KMP_DUPLICATE_LIB_OK="TRUE"
python -m uvicorn app.main:app --port 8000
```

Özel conda environment örneği:

```powershell
& "C:\Users\MSI\anaconda3\envs\it-support-agent\python.exe" -m uvicorn app.main:app --port 8000
```

Health endpoint:

```text
http://127.0.0.1:8000/health
```

## Frontend Çalıştırma

Backend static servis ediyorsa:

```text
http://127.0.0.1:8000/
```

Alternatif olarak doğrudan açılabilir:

```text
frontend/index.html
```

## API Örneği

Endpoint:

```http
POST /analyze
```

Request:

```json
{
  "message": "Wi-Fi bağlı ama internete giremiyorum.",
  "os": "Windows",
  "session_id": "optional"
}
```

## Test Komutları

```powershell
python -m pytest backend\tests
node --check frontend\app.js
```

## Fine-Tune Dosyaları

Bu repoda fine-tune için kullanılan JSONL veri dosyaları şu konumdadır:

```text
dataset/train.jsonl
dataset/test.jsonl
```

Son eğitim çalışma alanında kullanılan dosya yapısı:

```text
data/final/train.jsonl
data/final/test.jsonl
```

Dosyalar chat fine-tuning formatındadır:

```json
{"messages":[{"role":"system","content":"..."},{"role":"user","content":"..."},{"role":"assistant","content":"{...}"}]}
```

## Veri Üretimi

Fine-tune veri hazırlama sürecinde kullanılan komutlar:

```powershell
python scripts/split_merged_output.py
```

Eski CSV kaynaklarını birleştirme ve train/test ayrımı için kullanılan komutlar:

```powershell
python scripts/combine_finetune_csv.py
python scripts/split_finetune_dataset.py
```

Not: Bu yardımcı scriptler mevcut repo içinde bulunmuyorsa, fine-tune çalışma alanında veya veri hazırlama paketinde tutulmuş olabilir.

## Model Eğitimi

Fine-tune notebookları eğitim çalışma alanında `notebooks/` klasörü altında tutulmuştur.

Kullanılan temel model:

```text
Qwen/Qwen2.5-3B-Instruct
```

Eğitim yöntemi:

```text
QLoRA + Unsloth + Colab T4 GPU
```

Hugging Face LoRA adapter repo adı:

```text
oguzinyo/qwen2.5-3b-it-support-lora-v2
```

## Proje Yapısı

```text
Turkish-IT-Support-Agent-FineTune/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── model_service.py
│   │   ├── prompts.py
│   │   ├── conversation_router.py
│   │   ├── response_normalizer.py
│   │   ├── json_utils.py
│   │   ├── schemas.py
│   │   └── session_store.py
│   ├── tests/
│   ├── scripts/
│   ├── data/
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── index.html
│   ├── app.js
│   └── style.css
├── dataset/
│   ├── train.jsonl
│   ├── test.jsonl
│   └── README.md
├── docs/
│   ├── screenshots/
│   ├── technical_documentation.md
│   ├── model_quality_notes.md
│   └── fine_tune_process.md
├── tests/
│   ├── test_cases.md
│   └── test_results.md
├── .gitignore
├── LICENSE
└── README.md
```

## Bilinen Sınırlılıklar

- Local model olduğu için cevap süresi değişebilir ve yavaş olabilir.
- Model bazen bozuk Türkçe veya yetersiz cevap üretebilir.
- Backend model cevabını hazır cevapla düzeltmez.
- Daha iyi sonuç için dataset iyileştirilip model yeniden fine-tune edilmelidir.

## GitHub'a Eklenmemesi Gerekenler

- `.env`
- `sessions.json`
- `__pycache__`
- `.pytest_cache`
- `node_modules`
- model cache
- `*.safetensors`
- `*.bin`

## Kaynaklar

- Backend kodu: `backend/app/`
- Frontend kodu: `frontend/`
- Testler: `backend/tests/`
- Dataset: `dataset/`
- Dokümantasyon: `docs/`
