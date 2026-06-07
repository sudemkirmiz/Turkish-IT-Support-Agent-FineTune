import json

from fastapi.testclient import TestClient

import backend.app.main as main
import backend.app.model_service as model_service
from backend.app.response_normalizer import validate_model_semantics
from backend.app.main import app


client = TestClient(app)

REQUIRED_RESPONSE_FIELDS = (
    "category",
    "priority",
    "summary",
    "possible_causes",
    "questions",
    "solution_steps",
    "risk_level",
)


def assert_required_response_fields(body: dict) -> None:
    for field in REQUIRED_RESPONSE_FIELDS:
        assert field in body
        assert body[field] is not None
    assert isinstance(body["summary"], str)
    assert isinstance(body["possible_causes"], list)
    assert isinstance(body["questions"], list)
    assert isinstance(body["solution_steps"], list)


def fake_model_output(category: str) -> str:
    return json.dumps(
        {
            "assistant_message": "Kullanıcı test ortamında teknik sorun bildiriyor. Şu adımları deneyebilirsiniz.",
            "category": category,
            "priority": "medium",
            "summary": "Kullanıcı test ortamında teknik sorun bildiriyor.",
            "possible_causes": ["Test neden bir", "Test neden iki"],
            "questions": ["Test soru?"],
            "solution_steps": ["Test durumunu kontrol edin.", "İlgili ayarı kontrol edin.", "Sorunu tekrar test edin."],
            "risk_level": "safe",
        },
        ensure_ascii=False,
    )


def fake_model_output_with_values(category: str, priority: str, risk_level: str) -> str:
    return json.dumps(
        {
            "assistant_message": "Kullanıcı test ortamında teknik sorun bildiriyor. Şu adımları deneyebilirsiniz.",
            "category": category,
            "priority": priority,
            "summary": "Kullanıcı test ortamında teknik sorun bildiriyor.",
            "possible_causes": ["Test neden bir", "Test neden iki"],
            "questions": ["Test soru?"],
            "solution_steps": ["Test durumunu kontrol edin.", "İlgili ayarı kontrol edin.", "Sorunu tekrar test edin."],
            "risk_level": risk_level,
        },
        ensure_ascii=False,
    )


def patch_model_response(monkeypatch, category: str) -> None:
    monkeypatch.setattr(main, "analyze_message", lambda message, os: fake_model_output(category))


def test_health_returns_ok():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "it-support-backend"}


def test_analyze_returns_valid_response_for_software_issue(monkeypatch):
    patch_model_response(monkeypatch, "software_issue")

    response = client.post("/analyze", json={"message": "Chrome sürekli çöküyor.", "os": "Windows"})
    body = response.json()

    assert response.status_code == 200
    assert body["category"] == "software_issue"
    assert body["priority"] in ["low", "medium", "high", "critical"]
    assert body["risk_level"] in ["safe", "warning", "dangerous"]
    assert isinstance(body["possible_causes"], list)
    assert isinstance(body["questions"], list)
    assert isinstance(body["solution_steps"], list)
    assert body["model_used"] is True
    assert body["repair_used"] is False
    assert body["mode"] == "initial_model_response"
    assert body["model_call_count"] == 1
    assert body["model_inference_ms"] >= 0
    assert body["assistant_message"] == "Kullanıcı test ortamında teknik sorun bildiriyor. Şu adımları deneyebilirsiniz."
    assert_required_response_fields(body)


def test_analyze_rejects_non_schema_enum_variants_after_retry(monkeypatch):
    monkeypatch.setattr(main, "analyze_message", lambda message, os: fake_model_output_with_values("http_error", "normal", "riskli"))

    response = client.post("/analyze", json={"message": "Bazı sitelerde 409 hata kodlu bir hata alıyorum.", "os": "Windows"})
    body = response.json()

    assert response.status_code == 502
    assert body["error_type"] == "invalid_model_semantics"


def test_analyze_returns_security_issue(monkeypatch):
    patch_model_response(monkeypatch, "security_issue")

    response = client.post("/analyze", json={"message": "Bilgisayarımda virüs olabilir.", "os": "Windows"})

    assert response.status_code == 200
    assert response.json()["category"] == "security_issue"


def test_analyze_returns_network_issue(monkeypatch):
    patch_model_response(monkeypatch, "network_issue")

    response = client.post("/analyze", json={"message": "Wi-Fi bağlı ama internete giremiyorum.", "os": "Windows"})

    assert response.status_code == 200
    assert response.json()["category"] == "network_issue"


def test_analyze_returns_performance_issue(monkeypatch):
    patch_model_response(monkeypatch, "performance_issue")

    response = client.post("/analyze", json={"message": "Bilgisayarım çok yavaşladı ve sürekli donuyor.", "os": "Windows"})

    assert response.status_code == 200
    assert response.json()["category"] == "performance_issue"


def test_analyze_returns_storage_issue(monkeypatch):
    patch_model_response(monkeypatch, "storage_issue")

    response = client.post("/analyze", json={"message": "Diskim dolu görünüyor ama neyi sileceğimi bilmiyorum.", "os": "Windows"})

    assert response.status_code == 200
    assert response.json()["category"] == "storage_issue"


def test_analyze_returns_os_error(monkeypatch):
    patch_model_response(monkeypatch, "os_error")

    response = client.post("/analyze", json={"message": "Windows güncellemesinden sonra ses gelmiyor.", "os": "Windows"})

    assert response.status_code == 200
    assert response.json()["category"] == "os_error"


def test_analyze_returns_unknown_issue(monkeypatch):
    patch_model_response(monkeypatch, "unknown_issue")

    response = client.post("/analyze", json={"message": "Ne olduğunu bilmiyorum ama bilgisayar garip davranıyor.", "os": "Unknown"})

    assert response.status_code == 200
    assert response.json()["category"] == "unknown_issue"


def test_analyze_returns_hardware_issue(monkeypatch):
    patch_model_response(monkeypatch, "hardware_issue")

    response = client.post("/analyze", json={"message": "Laptop çok ısınıyor ve kendi kendine kapanıyor.", "os": "Windows"})

    assert response.status_code == 200
    assert response.json()["category"] == "hardware_issue"


def test_analyze_returns_driver_issue(monkeypatch):
    patch_model_response(monkeypatch, "driver_issue")

    response = client.post("/analyze", json={"message": "Ekran kartı driver güncellemesinden sonra oyun açılmıyor.", "os": "Windows"})

    assert response.status_code == 200
    assert response.json()["category"] == "driver_issue"


def test_analyze_returns_peripheral_issue(monkeypatch):
    patch_model_response(monkeypatch, "peripheral_issue")

    response = client.post("/analyze", json={"message": "Bluetooth kulaklığım bağlanıyor ama ses gelmiyor.", "os": "Windows"})

    assert response.status_code == 200
    assert response.json()["category"] == "peripheral_issue"


def test_analyze_rejects_blank_message():
    response = client.post("/analyze", json={"message": "   ", "os": "Windows"})

    assert response.status_code == 422


def test_analyze_rejects_invalid_os():
    response = client.post("/analyze", json={"message": "Chrome açılmıyor.", "os": "Android"})

    assert response.status_code == 422


def test_analyze_returns_clear_error_when_fine_tuned_model_name_is_missing(monkeypatch):
    monkeypatch.setattr(main, "analyze_message", lambda message, os: (_ for _ in ()).throw(model_service.ModelConfigurationError("Fine-tune model adı yapılandırılmadı.")))

    response = client.post("/analyze", json={"message": "Wi-Fi bağlı ama internete giremiyorum.", "os": "Windows"})

    assert response.status_code == 500
    assert response.json() == {"detail": "Fine-tune model adı yapılandırılmadı."}


def test_analyze_returns_clear_error_when_fine_tuned_model_loading_fails(monkeypatch):
    monkeypatch.setattr(main, "analyze_message", lambda message, os: (_ for _ in ()).throw(model_service.ModelIntegrationError("Fine-tune model yüklenemedi: test")))

    response = client.post("/analyze", json={"message": "Wi-Fi bağlı ama internete giremiyorum.", "os": "Windows"})

    assert response.status_code == 501
    assert response.json() == {"detail": "Fine-tune model yüklenemedi: test"}


def test_analyze_returns_502_when_invalid_json_retry_fails(monkeypatch):
    monkeypatch.setattr(main, "analyze_message", lambda message, os: '{"')

    response = client.post("/analyze", json={"message": "Chrome sürekli çöküyor.", "os": "Linux"})
    body = response.json()

    assert response.status_code == 502
    assert body["error_type"] == "invalid_model_json"


def test_analyze_returns_advisory_warnings_without_retry(monkeypatch):
    monkeypatch.setattr(
        main,
        "analyze_message",
        lambda message, os: fake_model_output_with_values("software_issue", "medium", "safe").replace(
            "Kullanıcı test ortamında teknik sorun bildiriyor.", "Software issue bildirimi"
        ),
    )

    response = client.post("/analyze", json={"message": "Chrome sürekli çöküyor.", "os": "Linux"})
    body = response.json()

    assert response.status_code == 200
    assert body["summary"] == "Software issue bildirimi"
    assert body["retry_used"] is False
    assert body["model_call_count"] == 1
    assert "summary is too generic" in body["advisory_warnings"]


def test_analyze_does_not_normalize_browser_priority_or_risk(monkeypatch):
    monkeypatch.setattr(
        main,
        "analyze_message",
        lambda message, os: json.dumps(
            {
                "category": "software_issue",
                "priority": "high",
                "summary": "Kullanıcı Linux üzerinde Chrome tarayıcısının sürekli çöktüğünü belirtiyor.",
                "possible_causes": ["Bozuk Chrome kullanıcı profili", "Uyumsuz tarayıcı eklentisi"],
                "questions": ["Chrome açılır açılmaz mı kapanıyor?"],
                "solution_steps": [
                    "Chrome'u eklentiler devre dışı olacak şekilde başlatıp tekrar deneyin.",
                    "Chrome profil ayarlarını kontrol edin.",
                    "Tarayıcı güncellemelerini kontrol edin.",
                ],
                "risk_level": "warning",
            },
            ensure_ascii=False,
        ),
    )

    response = client.post("/analyze", json={"message": "Chrome sürekli çöküyor neden olur bu?", "os": "Linux"})
    body = response.json()

    assert response.status_code == 200
    assert body["priority"] == "high"
    assert body["risk_level"] == "warning"
    assert body["assistant_message"] is None
    assert_required_response_fields(body)
    assert "priority high is inconsistent with non-critical issue" in body["advisory_warnings"]


def test_analyze_retries_once_after_semantic_failure(monkeypatch):
    calls = []

    def fake_analyze(message, os):
        calls.append(message)
        if len(calls) == 1:
            return json.dumps(
                {
                    "category": "software_issue",
                    "priority": "medium",
                    "summary": "Kullanıcı Linux üzerinde tarayıcı çökmesi yaşadığını belirtiyor.",
                    "possible_causes": ["Bozuk kullanıcı profili", "Uyumsuz tarayıcı eklentisi"],
                    "questions": ["Sorun belirli bir işlemden sonra mı oluşuyor?"],
                    "solution_steps": ["Windows Update ayarlarını kontrol edin.", "Tarayıcı profilini kontrol edin.", "Tarayıcıyı tekrar test edin."],
                    "risk_level": "safe",
                },
                ensure_ascii=False,
            )
        return json.dumps(
            {
                "category": "software_issue",
                "priority": "medium",
                "summary": "Kullanıcı Linux üzerinde tarayıcı çökmesi yaşadığını belirtiyor.",
                "possible_causes": ["Bozuk kullanıcı profili", "Uyumsuz tarayıcı eklentisi"],
                "questions": ["Sorun belirli bir işlemden sonra mı oluşuyor?"],
                "solution_steps": ["Tarayıcı eklentilerini devre dışı bırakıp test edin.", "Yeni bir kullanıcı profili oluşturup kontrol edin.", "Tarayıcı güncellemelerini kontrol edin."],
                "risk_level": "safe",
            },
            ensure_ascii=False,
        )

    monkeypatch.setattr(main, "analyze_message", fake_analyze)

    response = client.post("/analyze", json={"message": "Tarayıcı sürekli çöküyor.", "os": "Linux"})
    body = response.json()

    assert response.status_code == 200
    assert body["category"] == "software_issue"
    assert len(calls) == 2
    assert "Validation failure reasons" in calls[1]
    assert body["model_used"] is True
    assert body["repair_used"] is False
    assert body["mode"] == "model_retry"
    assert body["retry_used"] is True
    assert body["model_call_count"] == 2
    assert body["model_inference_ms"] >= 0


def test_follow_up_uses_contextual_model_response(monkeypatch):
    calls = []

    def fake_analyze(message, os):
        calls.append(message)
        return fake_model_output("software_issue")

    monkeypatch.setattr(main, "analyze_message", fake_analyze)

    initial = client.post("/analyze", json={"message": "Chrome sürekli çöküyor.", "os": "Windows"}).json()
    follow = client.post("/analyze", json={"message": "olmuyor başka ne yapayım", "os": "Windows", "session_id": initial["session_id"]})
    body = follow.json()

    assert follow.status_code == 200
    assert body["session_id"] == initial["session_id"]
    assert body["model_used"] is True
    assert body["repair_used"] is False
    assert body["mode"] == "contextual_model_response"
    assert body["model_call_count"] == 1
    assert "Aktif sorun ozeti" in calls[-1]
    assert "Son onerilen solution_steps" in calls[-1]
    assert_required_response_fields(body)


def test_smalltalk_does_not_use_active_ticket_context(monkeypatch):
    calls = []

    def fake_analyze(message, os):
        calls.append(message)
        if "sen kimsin" in message.lower():
            return json.dumps(
                {
                    "category": "unknown_issue",
                    "priority": "low",
                    "summary": "Ben teknik sorunlarını analiz etmek için tasarlanmış bir IT destek asistanıyım.",
                    "possible_causes": [],
                    "questions": ["Yaşadığın teknik sorunu kısaca anlatır mısın?"],
                    "solution_steps": ["Sorununu yaz, ben olası nedenleri ve çözüm adımlarını düzenli şekilde paylaşayım."],
                    "risk_level": "safe",
                },
                ensure_ascii=False,
            )
        return fake_model_output("network_issue")

    monkeypatch.setattr(main, "analyze_message", fake_analyze)

    initial = client.post("/analyze", json={"message": "internetim çok yavaş çalışıyor sebebi ne olabilir", "os": "Windows"}).json()
    smalltalk = client.post("/analyze", json={"message": "sen kimsin", "os": "Windows", "session_id": initial["session_id"]})
    body = smalltalk.json()

    assert smalltalk.status_code == 200
    assert body["mode"] == "smalltalk_model_response"
    assert body["model_used"] is True
    assert body["model_call_count"] >= 1
    assert_required_response_fields(body)
    assert "Onceki kategori" not in calls[-1]
    assert "internetim çok yavaş" not in calls[-1]
    assert "normal sohbet" in calls[-1]
    response_text = " ".join([body["summary"], *body["solution_steps"], *body["questions"]]).lower()
    assert not any(term in response_text for term in ("submit", "different", "slow", "type"))


def test_thanks_routes_to_smalltalk_without_active_ticket_context(monkeypatch):
    calls = []

    def fake_analyze(message, os):
        calls.append(message)
        if "teşekkürler" in message.lower():
            return json.dumps(
                {
                    "category": "unknown_issue",
                    "priority": "low",
                    "summary": "Kullanıcı kısa bir teşekkür mesajı yazdı.",
                    "possible_causes": [],
                    "questions": ["Başka bir teknik konuda yardımcı olmamı ister misin?"],
                    "solution_steps": ["Yeni bir teknik sorun yaşarsan kısaca yaz.", "Varsa cihaz veya uygulama adını ekle.", "Hata mesajı varsa paylaş."],
                    "risk_level": "safe",
                },
                ensure_ascii=False,
            )
        return fake_model_output("software_issue")

    monkeypatch.setattr(main, "analyze_message", fake_analyze)

    initial = client.post("/analyze", json={"message": "Chrome sürekli çöküyor.", "os": "Windows"}).json()
    smalltalk = client.post("/analyze", json={"message": "teşekkürler", "os": "Windows", "session_id": initial["session_id"]})
    body = smalltalk.json()

    assert smalltalk.status_code == 200
    assert body["mode"] == "smalltalk_model_response"
    assert body["model_used"] is True
    assert body["model_call_count"] >= 1
    assert "Onceki kategori" not in calls[-1]
    assert "Chrome sürekli çöküyor" not in calls[-1]
    assert "normal sohbet" in calls[-1]


def test_out_of_scope_does_not_use_active_ticket_context(monkeypatch):
    calls = []

    def fake_analyze(message, os):
        calls.append(message)
        if "hava" in message.lower():
            return json.dumps(
                {
                    "assistant_message": "Ben IT destek asistanıyım. Hava durumu yerine bilgisayar, internet, yazılım veya cihaz sorunlarında yardımcı olabilirim.",
                    "category": "unknown_issue",
                    "priority": "low",
                    "summary": "Bu mesaj IT destek kapsamı dışında görünüyor.",
                    "possible_causes": [],
                    "questions": ["Yardımcı olmamı istediğin teknik sorun nedir?"],
                    "solution_steps": ["Bilgisayar, internet, yazılım veya cihazla ilgili yaşadığın sorunu yaz."],
                    "risk_level": "safe",
                },
                ensure_ascii=False,
            )
        return fake_model_output("network_issue")

    monkeypatch.setattr(main, "analyze_message", fake_analyze)

    initial = client.post("/analyze", json={"message": "internetim çok yavaş çalışıyor sebebi ne olabilir", "os": "Windows"}).json()
    out_of_scope = client.post("/analyze", json={"message": "hava durumu nasıl", "os": "Windows", "session_id": initial["session_id"]})
    body = out_of_scope.json()

    assert out_of_scope.status_code == 200
    assert body["mode"] == "out_of_scope_model_response"
    assert body["model_used"] is True
    assert body["repair_used"] is False
    assert body["model_call_count"] == 1
    assert_required_response_fields(body)
    assert "Onceki kategori" not in calls[-1]
    assert "internetim çok yavaş" not in calls[-1]
    assert "IT destek kapsami disinda" in calls[-1]
    assert body["assistant_message"].startswith("Ben IT destek asistanıyım")


def test_performance_issue_routes_to_initial_model_response(monkeypatch):
    calls = []

    def fake_analyze(message, os):
        calls.append(message)
        return fake_model_output("performance_issue")

    monkeypatch.setattr(main, "analyze_message", fake_analyze)

    response = client.post("/analyze", json={"message": "Bilgisayarım çok yavaşladı", "os": "Windows"})
    body = response.json()

    assert response.status_code == 200
    assert body["mode"] == "initial_model_response"
    assert body["category"] == "performance_issue"
    assert body["model_used"] is True
    assert body["model_call_count"] == 1
    assert calls[-1] == "Bilgisayarım çok yavaşladı"


def test_internet_follow_up_keeps_context(monkeypatch):
    calls = []

    def fake_analyze(message, os):
        calls.append(message)
        return fake_model_output("network_issue")

    monkeypatch.setattr(main, "analyze_message", fake_analyze)

    initial = client.post("/analyze", json={"message": "internetim çok yavaş", "os": "Windows"}).json()
    follow = client.post("/analyze", json={"message": "olmuyor başka ne yapayım", "os": "Windows", "session_id": initial["session_id"]})
    body = follow.json()

    assert follow.status_code == 200
    assert body["mode"] == "contextual_model_response"
    assert body["model_used"] is True
    assert body["model_call_count"] >= 1
    assert "Aktif sorun ozeti" in calls[-1]
    assert "internetim çok yavaş" in calls[-1]
    assert_required_response_fields(body)


def test_denied_attempt_follow_up_keeps_context(monkeypatch):
    calls = []

    def fake_analyze(message, os):
        calls.append(message)
        return fake_model_output("software_issue")

    monkeypatch.setattr(main, "analyze_message", fake_analyze)

    initial = client.post("/analyze", json={"message": "Chrome sürekli çöküyor.", "os": "Windows"}).json()
    follow = client.post("/analyze", json={"message": "denedim olmadı", "os": "Windows", "session_id": initial["session_id"]})
    body = follow.json()

    assert follow.status_code == 200
    assert body["mode"] == "contextual_model_response"
    assert body["model_used"] is True
    assert body["model_call_count"] >= 1
    assert "Aktif sorun ozeti" in calls[-1]
    assert "Chrome sürekli çöküyor" in calls[-1]


def test_unclear_request_asks_model_for_clarifying_json(monkeypatch):
    calls = []

    def fake_analyze(message, os):
        calls.append(message)
        return json.dumps(
            {
                "assistant_message": "Yardımcı olabilmem için yaşadığın teknik sorunu biraz daha anlatır mısın?",
                "category": "unknown_issue",
                "priority": "low",
                "summary": "Kullanıcının teknik sorunu netleşmediği için ek bilgi gerekiyor.",
                "possible_causes": ["Sorun türü henüz net değil", "Cihaz veya uygulama bilgisi eksik"],
                "questions": ["Hangi cihaz veya uygulamada sorun yaşıyorsun?"],
                "solution_steps": ["Sorunun hangi cihazda olduğunu yaz.", "Varsa hata mesajını ekle.", "Sorunun ne zaman başladığını belirt."],
                "risk_level": "safe",
            },
            ensure_ascii=False,
        )

    monkeypatch.setattr(main, "analyze_message", fake_analyze)

    response = client.post("/analyze", json={"message": "bir şey oldu", "os": "Windows"})
    body = response.json()

    assert response.status_code == 200
    assert body["mode"] == "unclear_model_response"
    assert body["model_used"] is True
    assert body["model_call_count"] == 1
    assert "teknik destek istegi olabilir" in calls[-1]
    assert_required_response_fields(body)


def test_successful_responses_keep_document_required_fields(monkeypatch):
    patch_model_response(monkeypatch, "software_issue")

    response = client.post("/analyze", json={"message": "Chrome sürekli çöküyor.", "os": "Windows"})
    body = response.json()

    assert response.status_code == 200
    assert_required_response_fields(body)
    assert body["model_used"] is True
    assert body["repair_used"] is False
    assert body["model_call_count"] >= 1


def test_unknown_os_specific_instruction_is_advisory_not_blocking(monkeypatch):
    monkeypatch.setattr(
        main,
        "analyze_message",
        lambda message, os: json.dumps(
            {
                "category": "performance_issue",
                "priority": "medium",
                "summary": "Kullanıcı bilgisayarın yavaş çalıştığını belirtiyor.",
                "possible_causes": ["Arka plan uygulamaları", "Yüksek kaynak kullanımı"],
                "questions": ["Yavaşlama tüm işlemlerde mi oluyor?"],
                "solution_steps": [
                    "Görev Yöneticisi üzerinden kaynak kullanımını kontrol edin.",
                    "Başlangıç uygulamalarını kontrol edin.",
                    "Disk kullanımını kontrol edin.",
                ],
                "risk_level": "safe",
            },
            ensure_ascii=False,
        ),
    )

    response = client.post("/analyze", json={"message": "Bilgisayarım çok yavaşladı.", "os": "Unknown"})
    body = response.json()

    assert response.status_code == 200
    assert body["model_used"] is True
    assert body["repair_used"] is False
    assert "response contains OS-specific instruction for Unknown OS request" in body["advisory_warnings"]


def test_storage_policy_steps_are_actionable():
    data = {
        "category": "storage_issue",
        "priority": "medium",
        "summary": "Kullanıcı Windows üzerinde disk alanı sorunu yaşadığını belirtiyor.",
        "possible_causes": ["Diskte yetersiz boş alan", "Geçici dosyaların fazla yer kaplaması"],
        "questions": ["Hangi sürücüde boş alan az görünüyor?"],
        "solution_steps": [
            "Disk kullanimini klasor ve dosya turlerine gore kontrol edin.",
            "Gereksiz gecici dosyalari ve onbellekleri guvenli sekilde temizleyin.",
            "Buyuk dosyalari yedekleyip tasima veya arsivleme seceneklerini degerlendirin.",
            "Disk sagligi veya dosya sistemi uyarisi olup olmadigini kontrol edin.",
        ],
        "risk_level": "safe",
    }

    assert validate_model_semantics(data, "Diskim dolu görünüyor ama neyi sileceğimi bilmiyorum.", "Windows") == []


def test_windows_network_policy_is_not_linux_specific():
    data = {
        "category": "network_issue",
        "priority": "medium",
        "summary": "Kullanici Windows uzerinde wi-fi ile ilgili sorun yasadigini belirtiyor.",
        "possible_causes": [
            "DNS veya ad cozme problemi",
            "Modem, router veya ag baglantisi sorunu",
            "IP yapilandirmasi veya ag adaptor problemi",
        ],
        "questions": ["Sorun tum sitelerde mi yoksa belirli servislerde mi olusuyor?"],
        "solution_steps": [
            "Farkli bir web sitesi veya servisle baglantiyi test edin.",
            "VPN veya proxy kullaniyorsaniz gecici olarak kapatip tekrar deneyin.",
            "Modem, router ve cihazdaki ag baglantisi durumunu kontrol edin.",
            "Ag ayarlarinda DNS veya IP yapilandirmasini kontrol edin.",
        ],
        "risk_level": "safe",
    }

    assert validate_model_semantics(data, "Wi-Fi bağlı görünüyor ama internete giremiyorum.", "Windows") == []
