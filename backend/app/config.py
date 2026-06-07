import os
from pathlib import Path

from dotenv import load_dotenv


BACKEND_DIR = Path(__file__).resolve().parents[1]

load_dotenv(BACKEND_DIR / ".env")


FINE_TUNED_MODEL_NAME = os.getenv("FINE_TUNED_MODEL_NAME", "oguzinyo/qwen2.5-3b-it-support-lora-v2").strip()
MODEL_MAX_NEW_TOKENS = int(os.getenv("MODEL_MAX_NEW_TOKENS", "384"))
MODEL_MAX_GENERATION_SECONDS = int(os.getenv("MODEL_MAX_GENERATION_SECONDS", "120"))
MODEL_LOCAL_FILES_ONLY = os.getenv("MODEL_LOCAL_FILES_ONLY", "true").strip().lower() == "true"

if MODEL_LOCAL_FILES_ONLY:
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
