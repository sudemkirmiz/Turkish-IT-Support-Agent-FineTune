#!/usr/bin/env python3
"""Merge a PEFT LoRA adapter into a base model and save merged model locally.

Usage:
  python scripts/merge_adapter.py --base MODEL --adapter ADAPTER --out_dir merged_model

Reads defaults from backend/.env if present: BASE_MODEL_NAME, FINE_TUNED_MODEL_NAME.
"""
import argparse
import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND_DIR / ".env")

DEFAULT_ADAPTER = os.getenv("FINE_TUNED_MODEL_NAME")
DEFAULT_BASE = os.getenv("BASE_MODEL_NAME")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default=DEFAULT_BASE, help="Base model name or path (e.g. Qwen/Qwen2.5-3B)")
    parser.add_argument("--adapter", default=DEFAULT_ADAPTER, help="PEFT adapter repo or path")
    parser.add_argument("--out_dir", default=str(BACKEND_DIR / "merged_model"), help="Output directory for merged model")
    args = parser.parse_args()

    if not args.base:
        raise SystemExit("Base model not provided. Set BASE_MODEL_NAME in backend/.env or pass --base.")
    if not args.adapter:
        raise SystemExit("Adapter (fine-tuned) model not provided. Set FINE_TUNED_MODEL_NAME in backend/.env or pass --adapter.")

    print(f"Base model: {args.base}")
    print(f"Adapter: {args.adapter}")
    print(f"Output dir: {args.out_dir}")

    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        from peft import PeftModel
    except Exception as exc:
        raise SystemExit(f"Missing dependencies: {exc}\nInstall transformers, peft and torch.")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print("Loading base model (this may download many files)...")
    base = AutoModelForCausalLM.from_pretrained(args.base, device_map="cpu", trust_remote_code=True)

    print("Applying PEFT adapter...")
    peft = PeftModel.from_pretrained(base, args.adapter)

    print("Merging adapter into base model (this may use memory)...")
    if hasattr(peft, "merge_and_unload"):
        merged = peft.merge_and_unload()
    else:
        # fallback: try to save the peft object directly
        merged = peft

    print("Saving merged model to disk...")
    try:
        merged.save_pretrained(out_dir)
    except Exception as exc:
        # Some PeftModel wrappers delegate save to base model
        base.save_pretrained(out_dir)

    # Save tokenizer as well
    print("Saving tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(args.adapter, trust_remote_code=True)
    tokenizer.save_pretrained(out_dir)

    print("Done. Set FINE_TUNED_MODEL_NAME to the local path and restart the backend:")
    print(f"FINE_TUNED_MODEL_NAME={out_dir}")


if __name__ == "__main__":
    main()
