import logging
import time
import os

try:
    from .config import FINE_TUNED_MODEL_NAME, MODEL_LOCAL_FILES_ONLY, MODEL_MAX_GENERATION_SECONDS, MODEL_MAX_NEW_TOKENS
    from .prompts import build_initial_prompt
except ImportError:
    from app.config import FINE_TUNED_MODEL_NAME, MODEL_LOCAL_FILES_ONLY, MODEL_MAX_GENERATION_SECONDS, MODEL_MAX_NEW_TOKENS
    from app.prompts import build_initial_prompt

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

_MODEL = None
_TOKENIZER = None
_DEVICE = None
_DEVICE_MAP = None


class ModelServiceError(RuntimeError):
    pass


class ModelConfigurationError(ModelServiceError):
    pass


class ModelIntegrationError(ModelServiceError):
    pass


def _check_gpu_availability():
    """GPU/CUDA kullanılabilirliğini kontrol et."""
    try:
        import torch
        
        if torch.cuda.is_available():
            device_name = torch.cuda.get_device_name(0)
            device_count = torch.cuda.device_count()
            vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            logger.info(f"✓ GPU BULUNDU: {device_name} (VRAM: {vram_gb:.2f} GB)")
            logger.info(f"✓ CUDA Devices: {device_count}")
            return "cuda"
        else:
            logger.warning("⚠ GPU BULUNAMADI - CPU üzerinde çalışacak (ÇOK YAVAS)")
            return "cpu"
    except Exception as e:
        logger.error(f"GPU kontrol hatası: {e}")
        return "cpu"


def _get_model_device_map(device: str):
    """Model yüklemesi için device map stratejisi seç."""
    if device == "cuda":
        logger.info("📱 Device map: auto (GPU bulundu)")
        return "auto"
    else:
        logger.info("📱 Device map: cpu (GPU yok)")
        return "cpu"


def analyze_message(message: str, os: str) -> str:
    if not FINE_TUNED_MODEL_NAME:
        raise ModelConfigurationError("Fine-tune model adı yapılandırılmadı.")

    start_time = time.time()
    logger.info(f"🔄 Analiz başlanıyor... OS: {os}")
    
    try:
        # Model yükleme
        load_start = time.time()
        model, tokenizer = _load_fine_tuned_model()
        load_time = time.time() - load_start
        logger.info(f"⏱ Model yükleme süresi: {load_time:.2f}s")
        
        # Mesaj hazırlama
        msg_start = time.time()
        messages = _build_model_messages(message, os)
        msg_time = time.time() - msg_start
        
        # Prompt oluşturma
        if hasattr(tokenizer, "apply_chat_template") and getattr(tokenizer, "chat_template", None):
            prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        else:
            prompt = _build_model_prompt(messages)
        
        logger.debug(f"📝 Prompt uzunluğu: {len(prompt)} karakterler")
        
        # Tokenization
        token_start = time.time()
        inputs = tokenizer(prompt, return_tensors="pt")
        inputs = {key: value.to(model.device) for key, value in inputs.items()}
        token_time = time.time() - token_start
        logger.info(f"⏱ Tokenization süresi: {token_time:.2f}s")
        
        for config in (getattr(model, "generation_config", None), getattr(model, "config", None)):
            if config is not None and hasattr(config, "max_length"):
                config.max_length = None

        # Model inference
        gen_start = time.time()
        logger.info(
            f"🧠 Model çalışıyor (device: {model.device}, max_new_tokens={MODEL_MAX_NEW_TOKENS}, "
            f"max_time={MODEL_MAX_GENERATION_SECONDS}s)..."
        )
        
        import torch

        # Tüm input tensors'ı model device'ına move et (tekrar)
        inputs = {key: value.to(model.device) for key, value in inputs.items()}
        logger.debug(f"✓ Input tensors device: {inputs['input_ids'].device}")

        with torch.no_grad():  # inference_mode yerine no_grad kullan (meta tensor uyumsuzluğu önlemek için)
            output_ids = model.generate(
                **inputs,
                max_new_tokens=MODEL_MAX_NEW_TOKENS,
                max_time=MODEL_MAX_GENERATION_SECONDS,
                do_sample=False,
                repetition_penalty=1.1,
                eos_token_id=_get_eos_token_ids(tokenizer),
                pad_token_id=tokenizer.pad_token_id or tokenizer.eos_token_id,
            )
        
        gen_time = time.time() - gen_start
        logger.info(f"⏱ Inference süresi: {gen_time:.2f}s")
        
        # Decode
        generated_ids = output_ids[0][inputs["input_ids"].shape[-1] :]
        result = tokenizer.decode(generated_ids, skip_special_tokens=True).strip()
        logger.debug(f"📤 Raw model output (first 1500 chars):\n{result[:1500]}")
        if generated_ids.shape[-1] >= MODEL_MAX_NEW_TOKENS:
            logger.warning(
                "⚠ output may be truncated: generated token count reached "
                f"MODEL_MAX_NEW_TOKENS={MODEL_MAX_NEW_TOKENS}"
            )
        if gen_time >= MODEL_MAX_GENERATION_SECONDS:
            logger.warning(
                "⚠ output may be truncated: generation reached "
                f"MODEL_MAX_GENERATION_SECONDS={MODEL_MAX_GENERATION_SECONDS}"
            )
        
        total_time = time.time() - start_time
        logger.info(f"✅ Analiz tamamlandı ({total_time:.2f}s toplam)")
        logger.debug(f"📤 Çıktı: {result[:100]}...")
        
        return result
        
    except ModelServiceError:
        raise
    except Exception as exc:
        logger.error(f"❌ Model çağrısı hatası: {exc}")
        raise ModelIntegrationError(f"Fine-tune model çağrısı başarısız: {exc}") from exc


def _load_fine_tuned_model():
    global _MODEL, _TOKENIZER, _DEVICE, _DEVICE_MAP

    if _MODEL is not None and _TOKENIZER is not None:
        logger.debug("✓ Model zaten yüklü, cache'den kullanılıyor")
        return _MODEL, _TOKENIZER

    logger.info("=" * 50)
    logger.info("🚀 MODEL YÜKLEME BAŞLANIYOR")
    logger.info("=" * 50)
    
    try:
        import torch
        from peft import AutoPeftModelForCausalLM
        from transformers import AutoTokenizer
    except ImportError as exc:
        raise ModelConfigurationError("Fine-tune model için transformers, peft ve torch paketleri kurulmalıdır.") from exc

    try:
        # 1. GPU kontrol
        if _DEVICE is None:
            _DEVICE = _check_gpu_availability()
            _DEVICE_MAP = _get_model_device_map(_DEVICE)
        
        # 2. Tokenizer yükleme
        logger.info("📥 Tokenizer yükleniyor...")
        tokenizer_model_name = FINE_TUNED_MODEL_NAME
        try:
            from huggingface_hub import snapshot_download

            tokenizer_model_name = snapshot_download(
                FINE_TUNED_MODEL_NAME,
                local_files_only=MODEL_LOCAL_FILES_ONLY,
            )
            logger.info(f"Tokenizer adapter snapshot'tan yuklenecek: {tokenizer_model_name}")
        except Exception as exc:
            logger.warning(f"Adapter snapshot okunamadi, tokenizer repo id'den yuklenecek: {exc}")
        _TOKENIZER = AutoTokenizer.from_pretrained(
            tokenizer_model_name,
            trust_remote_code=True,
            local_files_only=MODEL_LOCAL_FILES_ONLY,
        )
        if _TOKENIZER.pad_token_id is None:
            _TOKENIZER.pad_token = _TOKENIZER.eos_token
        logger.info("✓ Tokenizer yüklendi")
        
        # 3. Quantization kontrol
        use_quantization = _DEVICE == "cuda" and _check_quantization_available()
        quantization_config = None
        
        if use_quantization:
            logger.info("🔧 Quantization etkinleştirildi (8-bit)")
            try:
                from transformers import BitsAndBytesConfig
                quantization_config = BitsAndBytesConfig(load_in_8bit=True)
            except Exception as e:
                logger.warning(f"⚠ Quantization config oluşturma hatası: {e}")
                use_quantization = False
        
        # 4. Model yükleme (meta tensor problemi çözmek için iyileştirildi)
        logger.info("📥 Model yükleniyor (bu biraz zaman alabilir)...")
        load_kwargs = {
            "trust_remote_code": True,
            "device_map": _DEVICE_MAP,
        }
        if _DEVICE == "cuda":
            load_kwargs["torch_dtype"] = torch.float16
        else:
            load_kwargs["torch_dtype"] = torch.float32
        
        if use_quantization and quantization_config:
            load_kwargs["quantization_config"] = quantization_config
        
        try:
            # Strategi 1: PEFT Model direkt yükle (tavsiye edilen)
            logger.debug("Strategi 1: AutoPeftModelForCausalLM.from_pretrained()")
            _MODEL = AutoPeftModelForCausalLM.from_pretrained(
                FINE_TUNED_MODEL_NAME,
                local_files_only=MODEL_LOCAL_FILES_ONLY,
                **load_kwargs
            )
            logger.info(f"✓ PEFT Model yüklendi (Device: {_MODEL.device})")
            
        except Exception as exc:
            msg = str(exc)
            logger.warning(f"⚠ PEFT yükleme başarısız: {msg[:200]}")
            
            # Strategi 2: Base model + Manual LoRA (meta tensor sorunlarını çözmek için)
            if "meta tensor" in msg.lower() or "copy out of meta" in msg.lower():
                logger.info("🔄 Strategi 2: Base Model + Manual LoRA loading...")
                try:
                    from transformers import AutoModelForCausalLM
                    from peft import PeftConfig, get_peft_model
                    
                    base_model_name = "Qwen/Qwen2.5-3B-Instruct"
                    logger.info(f"📥 Base model yükleniyor: {base_model_name}")
                    
                    base_load_kwargs = {
                        "trust_remote_code": True,
                        "device_map": _DEVICE_MAP,
                        "torch_dtype": load_kwargs.get("torch_dtype", torch.float32),
                    }
                    
                    _MODEL = AutoModelForCausalLM.from_pretrained(
                        base_model_name,
                        local_files_only=MODEL_LOCAL_FILES_ONLY,
                        **base_load_kwargs
                    )
                    logger.info(f"✓ Base model yüklendi: {_MODEL.device}")
                    
                    # LoRA config yükle
                    logger.info(f"📥 LoRA config yükleniyor: {FINE_TUNED_MODEL_NAME}")
                    peft_config = PeftConfig.from_pretrained(FINE_TUNED_MODEL_NAME)
                    logger.info(f"✓ LoRA config yüklendi")
                    
                    # LoRA uygula
                    logger.info("🔌 LoRA base model'e uygulanıyor...")
                    _MODEL = get_peft_model(_MODEL, peft_config)
                    logger.info(f"✓ LoRA uygulandı: {_MODEL.device}")
                    
                except Exception as exc2:
                    logger.error(f"❌ Strategi 2 de başarısız: {exc2}")
                    raise ModelIntegrationError(f"Model yükleme stratejileri başarısız: {exc}") from exc
            
            # Strategi 3: CPU fallback
            elif "cuda" in msg.lower() or "device" in msg.lower():
                logger.info("♻ Strategi 3: CPU fallback...")
                load_kwargs["device_map"] = "cpu"
                load_kwargs.pop("torch_dtype", None)
                if use_quantization:
                    load_kwargs.pop("quantization_config", None)
                
                _MODEL = AutoPeftModelForCausalLM.from_pretrained(
                    FINE_TUNED_MODEL_NAME,
                    local_files_only=MODEL_LOCAL_FILES_ONLY,
                    **load_kwargs
                )
                logger.info(f"✓ Model CPU'da yüklendi")
            else:
                raise
        
        # 5. Model merge seçeneği (opsiyonel - daha hızlı inference)
        # NOT: Meta tensor sorunundan kaçınmak için merge'i devre dışı bıraktık
        # Bunun yerine PEFT LoRA adaptörleri direkt kullanılıyor (stable + hızlı)
        logger.info("✓ LoRA adaptörleri direkt kullanılıyor (merge devre dışı)")
        
        # 6. Model device'a move et ve eval mode
        if _DEVICE == "cuda":
            _MODEL = _MODEL.to("cuda:0")
            logger.info("✓ Model CUDA cihazına taşındı")
        _MODEL.eval()
        logger.info("✓ Model eval mode'a alındı")
        logger.info("=" * 50)
        logger.info("✅ MODEL YÜKLEME BAŞARILI")
        logger.info("=" * 50)
        
    except Exception as exc:
        logger.error(f"❌ Model yükleme hatası: {exc}")
        _MODEL = None
        _TOKENIZER = None
        raise ModelIntegrationError(f"Fine-tune model yüklenemedi: {exc}") from exc

    return _MODEL, _TOKENIZER


def _check_quantization_available():
    """8-bit quantization desteği kontrol et."""
    try:
        import bitsandbytes  # noqa
        logger.info("✓ bitsandbytes bulundu (quantization kullanılabilir)")
        return True
    except ImportError:
        logger.warning("⚠ bitsandbytes bulunamadı (quantization kapatılıyor)")
        return False


def _should_merge_model():
    """Model merge edilmeli mi kontrol et."""
    # Merge, özellikle küçük modeller için inference hızını arttırır
    # PEFT adapter'larını base model'e bütünleştirir
    merge = os.getenv("MERGE_LORA_ADAPTERS", "false").lower() == "true"
    if merge:
        logger.info("📌 Model merge etme etkinleştirildi (env: MERGE_LORA_ADAPTERS=true)")
    return merge


def _get_eos_token_ids(tokenizer) -> list[int] | int:
    token_ids = []
    for token_id in (
        tokenizer.eos_token_id,
        tokenizer.convert_tokens_to_ids("<|im_end|>"),
        tokenizer.convert_tokens_to_ids("<|endoftext|>"),
    ):
        if isinstance(token_id, int) and token_id >= 0 and token_id not in token_ids:
            token_ids.append(token_id)
    return token_ids or tokenizer.eos_token_id


def _build_model_messages(message: str, os: str) -> list[dict[str, str]]:
    return build_initial_prompt(message, os)


def _build_model_prompt(messages: list[dict[str, str]]) -> str:
    system_prompt = messages[0]["content"]
    user_prompt = messages[1]["content"]
    return (
        "<|im_start|>system\n"
        f"{system_prompt}\n"
        "<|im_end|>\n"
        "<|im_start|>user\n"
        f"{user_prompt}\n"
        "<|im_end|>\n"
        "<|im_start|>assistant\n"
    )
