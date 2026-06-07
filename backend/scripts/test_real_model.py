#!/usr/bin/env python3
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.json_utils import JSONExtractionError, extract_json
from backend.app.model_service import analyze_message
from backend.app.response_normalizer import ModelOutputSemanticError, normalize_model_output, validate_model_semantics
from backend.app.schemas import ITSupportResponse


CASES = [
    {"name": "network_issue", "message": "Wi-Fi bağlı görünüyor ama internete giremiyorum.", "os": "Windows"},
    {"name": "software_issue", "message": "Chrome sürekli çöküyor neden olur bu?", "os": "Linux"},
    {"name": "hardware_issue", "message": "Laptop çok ısınıyor ve kendi kendine kapanıyor.", "os": "Windows"},
    {"name": "driver_issue", "message": "Ekran kartı driver güncellemesinden sonra oyun açılmıyor.", "os": "Windows"},
    {"name": "peripheral_issue", "message": "Mikrofonum Zoom’da çalışmıyor.", "os": "macOS"},
    {"name": "security_issue", "message": "Şüpheli bir dosya indirdim, bilgisayar garip davranıyor.", "os": "Windows"},
    {"name": "storage_issue", "message": "Diskim dolu görünüyor ama neyi sileceğimi bilmiyorum.", "os": "Windows"},
    {"name": "os_error", "message": "Linux güncellemesinden sonra sistem açılırken hata veriyor.", "os": "Linux"},
    {"name": "unknown_issue", "message": "Bilgisayar garip davranıyor ama tam anlatamıyorum.", "os": "Unknown"},
]


def run_case(case: dict[str, str]) -> bool:
    print("=" * 80)
    print(f"{case['name']}: {case['message']} ({case['os']})")
    print("=" * 80)

    raw_output = analyze_message(case["message"], case["os"])
    print("\nRAW OUTPUT:")
    print(raw_output)

    retry_used = False
    first_reasons = []
    retry_reasons = []
    validated, reasons = validate_raw_output(raw_output, case)
    if validated is None:
        first_reasons = reasons
        retry_used = True
        print("\nVALIDATION FAILED, RETRYING ONCE:")
        print(json.dumps(reasons, ensure_ascii=False, indent=2))
        retry_message = build_retry_message(case, raw_output, reasons)
        raw_output = analyze_message(retry_message, case["os"])
        print("\nRETRY RAW OUTPUT:")
        print(raw_output)
        validated, reasons = validate_raw_output(raw_output, case)
        if validated is None:
            retry_reasons = reasons
            print("\nRETRY VALIDATION FAILED, RETURNING FAILURE WITHOUT BACKEND-GENERATED RESPONSE:")
            print(json.dumps(reasons, ensure_ascii=False, indent=2))
            return False

    print("\nJSON PARSE/VALIDATION: OK")
    result = validated.model_dump()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("\nSUMMARY:")
    print(f"category: {result['category']}")
    print(f"priority: {result['priority']}")
    print(f"risk_level: {result['risk_level']}")
    print(f"summary: {result['summary']}")
    print(f"possible_causes count: {len(result['possible_causes'])}")
    print(f"questions count: {len(result['questions'])}")
    print(f"solution_steps count: {len(result['solution_steps'])}")
    print(f"retry used: {retry_used}")
    print("repair used: False")
    print(f"first validation reasons: {first_reasons}")
    print(f"retry validation reasons: {retry_reasons}")
    print(f"final validation reasons: {reasons}")
    print("OS compatibility: OK")
    print("risk/priority consistency: OK")
    print("semantic validation: OK")
    return True


def validate_raw_output(raw_output: str, case: dict[str, str]):
    try:
        parsed = extract_json(raw_output)
        normalized = normalize_model_output(parsed, case["message"], case["os"])
        validated = ITSupportResponse.model_validate(normalized)
        validate_model_semantics(validated.model_dump(), case["message"], case["os"])
        return validated, []
    except JSONExtractionError:
        return None, ["model returned invalid JSON"]
    except ModelOutputSemanticError as exc:
        return None, exc.reasons
    except ValueError as exc:
        return None, [str(exc)]


def build_retry_message(case: dict[str, str], previous_output: str, reasons: list[str]) -> str:
    reasons_text = "\n".join(f"- {reason}" for reason in reasons)
    return f"""Onceki model cevabi kalite kontrolunden gecemedi. Ayni kullanici istegini yeniden analiz et.

Orijinal kullanici mesaji:
{case['message']}

Isletim sistemi:
{case['os']}

Onceki model cevabi:
{previous_output[:1500]}

Validation failure reasons:
{reasons_text}

Sadece gecerli JSON uret. OS ile uyumsuz adim verme. Alan rollerini koru. Summary genel olmasin. Kullanici baglamindan kopma. Priority ve risk_level tutarli olsun."""


def main() -> int:
    failures = 0
    for case in CASES:
        if not run_case(case):
            failures += 1

    print("=" * 80)
    print(f"Completed: {len(CASES) - failures}/{len(CASES)} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
