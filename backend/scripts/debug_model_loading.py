#!/usr/bin/env python3
"""
Model Loading Debug Script
For diagnosing meta tensor error
"""

import logging
import torch
import sys
import io
import os

# Force UTF-8 encoding
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Logging setup
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_environment():
    """Environment check"""
    print("\n" + "="*60)
    print("[INFO] ENVIRONMENT CHECK")
    print("="*60)
    
    print(f"Python: {sys.version.split()[0]}")
    print(f"PyTorch: {torch.__version__}")
    print(f"CUDA Available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"CUDA Device: {torch.cuda.get_device_name(0)}")
        print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")

def test_model_loading():
    """Test model loading"""
    print("\n" + "="*60)
    print("[INFO] MODEL LOADING TEST")
    print("="*60)
    
    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer
        from peft import AutoPeftModelForCausalLM
        
        model_name = "oguzinyo/qwen2.5-3b-it-support-lora-v2"
        base_model = "Qwen/Qwen2.5-3B-Instruct"
        
        logger.info(f"Loading model: {model_name}")
        
        # Try 1: AutoPeftModelForCausalLM (original approach)
        print("\n>> Attempt 1: AutoPeftModelForCausalLM.from_pretrained()")
        try:
            device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Using device: {device}")
            
            model = AutoPeftModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch.float16 if device == "cuda" else torch.float32,
                device_map="auto",
                trust_remote_code=True,
            )
            
            logger.info(f"[SUCCESS] Model loaded!")
            logger.info(f"  - Model device: {model.device}")
            logger.info(f"  - Model type: {type(model)}")
            
            # Check for meta tensors
            has_meta = False
            meta_params = []
            for name, param in model.named_parameters():
                if param.device.type == 'meta':
                    has_meta = True
                    meta_params.append(name)
                    if len(meta_params) <= 5:
                        logger.warning(f"  [WARNING] Meta tensor found: {name}")
            
            if has_meta:
                logger.warning(f"  Total meta tensors: {len(meta_params)}")
            else:
                logger.info("  [SUCCESS] No meta tensors found")
            
            return model
            
        except Exception as e1:
            logger.error(f"[FAILED] Attempt 1: {str(e1)[:200]}")
            
            # Try 2: Load base + LoRA separately
            print("\n>> Attempt 2: Load Base Model + LoRA Config")
            try:
                logger.info(f"Loading base model: {base_model}")
                base = AutoModelForCausalLM.from_pretrained(
                    base_model,
                    torch_dtype=torch.float16 if device == "cuda" else torch.float32,
                    device_map="auto",
                    trust_remote_code=True,
                )
                logger.info(f"[SUCCESS] Base model loaded: {base.device}")
                
                # Load LoRA config
                from peft import PeftConfig, get_peft_model
                
                logger.info(f"Loading LoRA config: {model_name}")
                peft_config = PeftConfig.from_pretrained(model_name)
                logger.info(f"[SUCCESS] LoRA config loaded")
                
                # Apply LoRA
                logger.info("Applying LoRA...")
                model = get_peft_model(base, peft_config)
                logger.info(f"[SUCCESS] LoRA applied: {model.device}")
                
                return model
                
            except Exception as e2:
                logger.error(f"[FAILED] Attempt 2: {str(e2)[:200]}")
                raise
    
    except Exception as e:
        logger.error(f"[FAILED] Model loading: {str(e)}", exc_info=True)
        raise

def test_inference(model):
    """Test inference"""
    print("\n" + "="*60)
    print("[INFO] INFERENCE TEST")
    print("="*60)
    
    try:
        from transformers import AutoTokenizer
        
        tokenizer = AutoTokenizer.from_pretrained(
            "Qwen/Qwen2.5-3B-Instruct",
            trust_remote_code=True,
        )
        if tokenizer.pad_token_id is None:
            tokenizer.pad_token = tokenizer.eos_token
        
        # Simple prompt
        prompt = "Wi-Fi bagli ama internete giremiyorum."
        logger.info(f"Prompt: {prompt}")
        
        # Tokenize
        inputs = tokenizer(prompt, return_tensors="pt")
        logger.info(f"[SUCCESS] Tokenized: {inputs['input_ids'].shape}")
        
        # Move to model device
        device = next(model.parameters()).device
        logger.info(f"Model device: {device}")
        
        inputs = {k: v.to(device) for k, v in inputs.items()}
        logger.info(f"[SUCCESS] Inputs moved to device: {inputs['input_ids'].device}")
        
        # Generate
        logger.info("Generating...")
        model.eval()
        
        with torch.no_grad():
            output_ids = model.generate(
                **inputs,
                max_new_tokens=128,
                do_sample=False,
            )
        
        logger.info(f"[SUCCESS] Generation successful: {output_ids.shape}")
        
        # Decode
        output = tokenizer.decode(output_ids[0], skip_special_tokens=True)
        logger.info(f"Output (first 200 chars): {output[:200]}...")
        
    except Exception as e:
        logger.error(f"[FAILED] Inference: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    try:
        check_environment()
        model = test_model_loading()
        test_inference(model)
        
        print("\n" + "="*60)
        print("[SUCCESS] ALL TESTS PASSED!")
        print("="*60)
        
    except Exception as e:
        print("\n" + "="*60)
        print(f"[ERROR] {str(e)}")
        print("="*60)
        sys.exit(1)
