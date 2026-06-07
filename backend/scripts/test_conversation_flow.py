#!/usr/bin/env python3
import json
import time
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def post(message: str, os: str, session_id: str | None = None) -> tuple[dict, float]:
    started = time.time()
    payload = {"message": message, "os": os}
    if session_id:
        payload["session_id"] = session_id
    response = client.post("/analyze", json=payload)
    elapsed = time.time() - started
    if response.status_code == 502:
        print(json.dumps(response.json(), ensure_ascii=False, indent=2))
        raise AssertionError("Model output failed validation after retry; backend correctly did not use policy fallback.")
    response.raise_for_status()
    return response.json(), elapsed


def assert_follow_up(initial: dict, follow_up: dict) -> None:
    assert follow_up["session_id"] == initial["session_id"]
    assert follow_up["mode"] == "contextual_model_response"
    assert follow_up["mode"] != "follow_up_fast_path"
    assert follow_up["mode"] != "policy_repair"
    assert follow_up["model_used"] is True
    assert follow_up["repair_used"] is False
    assert follow_up["model_call_count"] >= 1
    assert follow_up["model_inference_ms"] >= 0


def assert_model_response(response: dict) -> None:
    assert response["model_used"] is True
    assert response["repair_used"] is False
    assert response["mode"] != "follow_up_fast_path"
    assert response["mode"] != "policy_repair"
    assert response["model_call_count"] >= 1
    assert response["model_inference_ms"] >= 0


def assert_category(response: dict, expected_category: str) -> None:
    if response["category"] != expected_category:
        print(f"Model selected category={response['category']} expected={expected_category}; backend did not correct it.")


def assert_no_step(response: dict, forbidden_terms: tuple[str, ...]) -> None:
    joined_steps = " ".join(response["solution_steps"]).lower()
    for term in forbidden_terms:
        if term in joined_steps:
            print(f"Model repeated tried step term={term}; backend did not alter model content.")


def run_flow(initial_message: str, follow_up_message: str, os: str) -> bool:
    print("=" * 80)
    print(initial_message)
    initial, initial_elapsed = post(initial_message, os)
    print(json.dumps(initial, ensure_ascii=False, indent=2))
    assert_model_response(initial)
    follow, follow_elapsed = post(follow_up_message, os, initial["session_id"])
    print(json.dumps(follow, ensure_ascii=False, indent=2))
    assert_follow_up(initial, follow)
    print(f"initial_seconds={initial_elapsed:.2f} follow_up_seconds={follow_elapsed:.2f}")
    return True


def run_chrome_flow() -> bool:
    print("=" * 80)
    initial, initial_elapsed = post("Chrome sürekli çöküyor.", "Windows")
    print(json.dumps(initial, ensure_ascii=False, indent=2))
    assert_model_response(initial)
    assert_category(initial, "software_issue")

    first_follow, first_follow_elapsed = post("olmuyor başka ne yapayım", "Windows", initial["session_id"])
    print(json.dumps(first_follow, ensure_ascii=False, indent=2))
    assert_follow_up(initial, first_follow)

    second_follow, second_follow_elapsed = post("olmuyor başka ne yapayım", "Windows", initial["session_id"])
    print(json.dumps(second_follow, ensure_ascii=False, indent=2))
    assert_follow_up(initial, second_follow)

    tried_follow, tried_follow_elapsed = post("eklentileri kapattım ama yine kapanıyor", "Windows", initial["session_id"])
    print(json.dumps(tried_follow, ensure_ascii=False, indent=2))
    assert_follow_up(initial, tried_follow)
    assert_no_step(tried_follow, ("eklenti", "ek bilesen"))

    print(
        f"initial_seconds={initial_elapsed:.2f} "
        f"follow_up_seconds={first_follow_elapsed:.2f}/{second_follow_elapsed:.2f}/{tried_follow_elapsed:.2f}"
    )
    return True


def main() -> int:
    flows = [
        ("Wi-Fi bağlı görünüyor ama internete giremiyorum.", "hala olmuyor", "Windows"),
        ("Şüpheli bir dosya indirdim, bilgisayar garip davranıyor.", "taramayı yaptım yine garip", "Windows"),
    ]
    passed = 1 if run_chrome_flow() else 0
    for flow in flows:
        if run_flow(*flow):
            passed += 1
    print("=" * 80)
    expected = len(flows) + 1
    print(f"Completed: {passed}/{expected} passed")
    return 0 if passed == expected else 1


if __name__ == "__main__":
    raise SystemExit(main())
