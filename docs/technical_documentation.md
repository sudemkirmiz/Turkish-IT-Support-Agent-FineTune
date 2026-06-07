# Technical Documentation

## Architecture

- `backend/`: FastAPI API, model çağrısı, validation, session store.
- `frontend/`: Statik chatbot arayüzü.
- `dataset/`: Fine-tune veri dosyaları için ayrılmış alan.
- `tests/`: Manuel test planları ve sonuç notları.

## Model-Only Rule

Backend assistant cevabı üretmez. Başarılı kullanıcı cevapları fine-tuned modelden gelir. Backend yalnızca JSON parse, schema validation, semantic validation, retry ve metadata ekleme yapar.

## Runtime Data

`backend/data/sessions.json` runtime sırasında oluşabilir ve Git'e eklenmez.
