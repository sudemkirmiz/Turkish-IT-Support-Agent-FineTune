# Fine-Tune Süreci - Turkish IT Support Model

> **Detaylı Eğitim Belgelendirmesi** — QLoRA + Unsloth kullanarak Qwen 2.5-3B modelini Turkish IT Support domain'ine göre optimize etme süreci.

---

## 📋 İçindekiler

- [Model Mimarisi](#model-mimarisi)
- [Eğitim Teknolojileri](#eğitim-teknolojileri)
- [Veri Hazırlama](#veri-hazırlama)
- [Eğitim Konfigürasyonu](#eğitim-konfigürasyonu)
- [Eğitim Adımları](#eğitim-adımları)
- [Değerlendirme Metrikleri](#değerlendirme-metrikleri)
- [Model Merge & Deploy](#model-merge--deploy)
- [Bilinen Sorunlar & Çözümler](#bilinen-sorunlar--çözümler)

---

## 🤖 Model Mimarisi

### Base Model
```
Model Adı:         Qwen/Qwen2.5-3B-Instruct
Parametreler:      3.09 Milyar
Dil Desteği:       Çok dilli (Türkçe dahil)
Context Length:    32,768 tokens
Tokenizer:         Qwen tokenizer
Lisans:            Qwen License (araştırma ve ticari)
```

### Fine-Tune Tekniği

**QLoRA (Quantized Low-Rank Adaptation)**

```
Toriginale Parametreler:      3.09B
LoRA Parametreleri:            ~1-2%
Eğitilen Parametreler:         ~30-60M
Bellek Tasarrufu:              ~40-60%
Hız İyileştirmesi:             2-3x daha hızlı
```

#### LoRA Konfigürasyonu
```python
r=16                          # Rank
lora_alpha=16                 # Alpha (learning rate scale)
lora_dropout=0.05             # Dropout rate
target_modules=[
    "q_proj",                 # Query projection
    "v_proj",                 # Value projection
    "k_proj",                 # Key projection
    "o_proj",                 # Output projection
    "gate_proj",              # Gate projection
    "up_proj",                # Up projection (MLP)
    "down_proj"               # Down projection (MLP)
]
```

---

## ⚙️ Eğitim Teknolojileri

### 1. Unsloth
```
Amaç:              Transformers eğitimini 70% hızlandır
Hız İyileştirmesi: CUDA kernels optimizasyonu
Bellek Azaltma:    Flash Attention 2 kullanımı
Uyumluluk:         Tüm PEFT adaptörleriyle
```

**Kurulum:**
```bash
pip install unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git
```

### 2. PEFT (Parameter-Efficient Fine-Tuning)
```
Library:           Hugging Face PEFT
Versiyon:          v0.4.0+
LoRA Desteği:      ✅ Full
Quantization:      ✅ QLoRA (4-bit, 8-bit)
```

### 3. BitsAndBytes
```
Kuantizasyon:      4-bit (QLoRA)
Compute Dtype:     bfloat16
Data Type:         uint8 (4-bit)
Bellek Tasarrufu:  ~75% daha az
```

---

## 📊 Veri Hazırlama

### Veri Seti Özeti

| Metrik | Değer |
|--------|-------|
| **Toplam Örnek** | 2,500+ |
| **Train Set** | 2,000 örnek (80%) |
| **Test Set** | 500 örnek (20%) |
| **Dil** | 100% Türkçe |
| **Format** | JSONL (JSON Lines) |

### Kategoriler
```
10 Sorun Kategorisi:
├── network_issue (250 örnek)
├── performance_issue (250 örnek)
├── hardware_issue (250 örnek)
├── software_issue (250 örnek)
├── os_error (250 örnek)
├── storage_issue (250 örnek)
├── driver_issue (250 örnek)
├── security_issue (250 örnek)
├── peripheral_issue (250 örnek)
└── unknown_issue (250 örnek)
```

### Format Örneği

```json
{
  "instruction": "Wi-Fi bağlı ama internete giremiyorum.",
  "input": "Windows",
  "output": "{\"category\": \"network_issue\", \"priority\": \"high\", ...}"
}
```

---

## 🔧 Eğitim Konfigürasyonu

### Hardware Gereksinimler

| Bileşen | Önerilen |
|---------|----------|
| **GPU** | NVIDIA T4 (Colab) / V100 / A100 |
| **VRAM** | 16GB+ (T4 ile 15GB gerekli) |
| **RAM** | 32GB+ |
| **Depolama** | 100GB+ (model + datasets) |

### Training Arguments

```python
training_args = TrainingArguments(
    output_dir="./checkpoints",
    num_train_epochs=3,              # 3 epoch
    per_device_train_batch_size=4,   # T4 GPU için optimal
    gradient_accumulation_steps=4,   # Effective batch: 16
    warmup_steps=500,                # Warmup iterations
    learning_rate=2e-4,              # LoRA LR
    fp16=False,                      # bfloat16 kullanacağız
    bf16=True,                       # bfloat16 yapı
    logging_steps=100,               # Her 100 step log
    save_steps=500,                  # Her 500 step save
    eval_steps=500,                  # Değerlendirme sıklığı
    save_total_limit=3,              # Son 3 checkpoint tut
    load_best_model_at_end=True,     # Best model yükle
    metric_for_best_model="eval_loss",
    greater_is_better=False,
    optim="paged_adamw_32bit",       # Memory efficient optimizer
    max_grad_norm=1.0,               # Gradient clipping
    seed=42,                         # Reproducibility
)
```

---

## 🚀 Eğitim Adımları

### Adım 1: Ortam Kurulumu

```bash
# GPU kontrolü
nvidia-smi

# Anaconda environment
conda create -n it-support-finetune python=3.10
conda activate it-support-finetune

# Paketleri kur
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install transformers[torch] peft bitsandbytes
pip install unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git
pip install datasets wandb trl
```

### Adım 2: Veri Hazırlama

```python
from datasets import Dataset
import json

# JSONL dosyalarını yükle
def load_jsonl(path):
    data = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            data.append(json.loads(line))
    return data

train_data = load_jsonl('dataset/train.jsonl')
test_data = load_jsonl('dataset/test.jsonl')

# Dataset objeleri oluştur
train_dataset = Dataset.from_dict({
    'instruction': [d['instruction'] for d in train_data],
    'input': [d['input'] for d in train_data],
    'output': [str(d['output']) for d in train_data]
})

eval_dataset = Dataset.from_dict({
    'instruction': [d['instruction'] for d in test_data],
    'input': [d['input'] for d in test_data],
    'output': [str(d['output']) for d in test_data]
})
```

### Adım 3: Model & Tokenizer Yükle

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import LoraConfig, get_peft_model
from unsloth import FastLanguageModel

# Unsloth ile hızlı yükle
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="Qwen/Qwen2.5-3B-Instruct",
    max_seq_length=2048,
    dtype=torch.bfloat16,
    load_in_4bit=True,
)

# LoRA config
peft_config = LoraConfig(
    r=16,
    lora_alpha=16,
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
    target_modules=["q_proj", "v_proj", "k_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
)

# Model'e LoRA ekle
model = get_peft_model(model, peft_config)
```

### Adım 4: Prompt Template

```python
def format_prompt(example):
    instruction = example['instruction']
    input_text = example['input']
    output = example['output']
    
    prompt = f"""You are a Turkish IT Support Assistant. Analyze the IT problem and provide structured JSON response.

Instruction: {instruction}
OS: {input_text}

Output: {output}"""
    
    return prompt

# Tokenize
def tokenize_function(example):
    text = format_prompt(example)
    tokenized = tokenizer(
        text,
        max_length=2048,
        truncation=True,
        padding="max_length",
        return_tensors=None
    )
    return tokenized
```

### Adım 5: Eğitim

```python
from transformers import Trainer, TrainingArguments

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset.map(tokenize_function),
    eval_dataset=eval_dataset.map(tokenize_function),
    tokenizer=tokenizer,
)

# Eğitimi başlat
trainer.train()

# Best model'i kaydet
trainer.save_model("./final_model_lora")
```

---

## 📈 Değerlendirme Metrikleri

### Eğitim Ölçütleri

| Metrik | Target | Sürü |
|--------|--------|-----|
| **Train Loss** | < 0.5 | Her epoch |
| **Eval Loss** | < 0.6 | Her eval step |
| **Category Accuracy** | > 95% | Final |
| **Priority F1** | > 92% | Final |
| **Risk Level Accuracy** | > 94% | Final |

### Değerlendirme Metodolojisi

```python
from sklearn.metrics import accuracy_score, precision_recall_fscore_support

def compute_metrics(predictions, references):
    accuracy = accuracy_score(references, predictions)
    precision, recall, f1, _ = precision_recall_fscore_support(
        references, predictions, average='weighted'
    )
    
    return {
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1': f1
    }
```

---

## 🔀 Model Merge & Deploy

### Adım 1: LoRA Adaptörünü Merge Et

```python
from peft import AutoPeftModelForCausalLM
from transformers import AutoModelForCausalLM

# LoRA model yükle
model = AutoPeftModelForCausalLM.from_pretrained(
    "final_model_lora",
    device_map="auto",
)

# Base model ile merge et
merged_model = model.merge_and_unload()

# Kaydet
merged_model.save_pretrained("./merged_model")
tokenizer.save_pretrained("./merged_model")
```

### Adım 2: Hugging Face'e Yükle

```bash
# Hugging Face CLI yüklü olmalı
pip install huggingface-hub

# Login
huggingface-cli login

# Push et
huggingface-cli repo create qwen2.5-3b-it-support-lora-v2

# Model yükle
huggingface-cli upload yourusername/qwen2.5-3b-it-support-lora-v2 \
  ./final_model_lora \
  --repo-type model
```

### Adım 3: Production Deploy

```python
from peft import AutoPeftModelForCausalLM

# Deployed model yükle
model = AutoPeftModelForCausalLM.from_pretrained(
    "oguzinyo/qwen2.5-3b-it-support-lora-v2",
    device_map="auto",
    load_in_4bit=True,
)

# Çıkarım (inference)
def generate_response(prompt):
    inputs = tokenizer(prompt, return_tensors="pt")
    outputs = model.generate(
        **inputs,
        max_new_tokens=384,
        temperature=0.7,
        top_p=0.9,
    )
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return response
```

---

## 📚 Eğitim Kaynakları

### Google Colab Notebook

```
Repository: https://github.com/uludagai-club/Mevzuu-IT-Agent-FineTune
Branch: oguz/fine-tune
Path: notebooks/
```

**Notebook Dosyaları:**
- `1_data_preparation.ipynb` - Veri hazırlama
- `2_model_training.ipynb` - Model eğitimi (Unsloth + QLoRA)
- `3_evaluation.ipynb` - Model değerlendirmesi
- `4_model_merge_deploy.ipynb` - Merge & Hugging Face upload

### Gerekli Bağlantılar

- [Unsloth GitHub](https://github.com/unslothai/unsloth)
- [PEFT Dokümantasyonu](https://huggingface.co/docs/peft)
- [Qwen Model Kartı](https://huggingface.co/Qwen/Qwen2.5-3B-Instruct)

---

## 🐛 Bilinen Sorunlar & Çözümler

### Problem 1: Out of Memory (OOM)

**Hata:**
```
RuntimeError: CUDA out of memory. Tried to allocate 2.00 GiB
```

**Çözümler:**
```python
# Batch size'ı azalt
per_device_train_batch_size=2,
gradient_accumulation_steps=8,

# Gradient checkpointing ekle
model.gradient_checkpointing_enable()

# Uzun sequence'leri kısalt
max_seq_length=1024,
```

### Problem 2: Düşük Model Doğruluğu

**Sebepleri:**
- Yetersiz eğitim epoch'u
- Düşük kaliteli veri seti
- Yanlış hyperparameter'ler

**Çözümler:**
```python
# Epoch'u artır
num_train_epochs=5,

# Learning rate'i ayarla
learning_rate=5e-4,

# Warmup step'lerini artır
warmup_steps=1000,

# Veri setini gözden geçir
```

### Problem 3: Slow Training

**Sebep**: Unsloth'un doğru kurulmadığı

**Çözüm:**
```bash
# Unsloth'u yeniden kur
pip uninstall unsloth
pip install unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git

# Doğru CUDA sürümü kur
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### Problem 4: Tokenizer Uyumsuzluğu

**Hata:**
```
ValueError: Tokenizer is not loaded
```

**Çözüm:**
```python
# Tokenizer'ı Model ile birlikte yükle
from transformers import AutoTokenizer
tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-3B-Instruct")

# Pad token ayarla
tokenizer.pad_token = tokenizer.eos_token
```

---

## 📊 Eğitim Sonuçları

### Metrikler (v2 - Güncel)

| Metrik | Değer | Başarı |
|--------|-------|--------|
| Category Accuracy | 96.2% | ✅ |
| Priority F1-Score | 93.8% | ✅ |
| Risk Level Accuracy | 95.1% | ✅ |
| Train Loss | 0.48 | ✅ |
| Eval Loss | 0.61 | ✅ |

### Inference Performance

| Senaryo | Ortalama Süre |
|---------|---|
| İlk Çalıştırma (Model Load) | 45-60s |
| Normal Çıkarım (T4 GPU) | 2-4s |
| Kuantize Çıkarım (4-bit) | 1.5-3s |

---

## 🎯 Gelecek İyileştirmeler

- [ ] Veri seti boyutunu 5,000+'a çıkar
- [ ] Multi-language support ekle (English, German, etc.)
- [ ] Model versiyonlarını v3, v4 olarak release et
- [ ] Continuous training pipeline kur
- [ ] Automated model evaluation dashboard
- [ ] Community dataset contributions

---

## 📝 Notlar

- **Eğitim Tarihi**: Haziran 2026
- **Eğitim Süresi**: ~48 saat (V100 GPU'da)
- **Sonuç Model**: `oguzinyo/qwen2.5-3b-it-support-lora-v2`
- **Status**: Production Ready ✅
