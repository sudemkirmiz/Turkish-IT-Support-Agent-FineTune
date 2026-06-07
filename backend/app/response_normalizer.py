"""
Response normalization and semantic validation.

This module handles:
1. Normalizing model JSON output (stripping, fixing casing)
2. Validating semantic consistency (summary quality, list content, actionability)
3. Detecting policy violations (dangerous steps, OS mismatches, unsupported details)
"""

import logging

logger = logging.getLogger(__name__)

# ===== VALID VALUES =====

VALID_CATEGORIES = {
    "network_issue", "performance_issue", "hardware_issue", "software_issue", "os_error",
    "storage_issue", "driver_issue", "security_issue", "peripheral_issue", "unknown_issue",
}

VALID_PRIORITIES = {"low", "medium", "high", "critical"}
VALID_RISK_LEVELS = {"safe", "warning", "dangerous"}

# ===== CONTENT VALIDATION TERMS =====

GENERIC_SUMMARIES = {
    "software issue bildirimi", "sorun analiz edildi", "kullanici sorun bildiriyor",
    "kullanıcı sorun bildiriyor", "problem bildirimi", "kullanici sorun yasiyor",
    "kullanıcı sorun yaşıyor", "teknik destek talebi", "sorun bildirimi",
}

# ===== ISSUE CRITICALITY DETECTION =====

CRITICAL_TERMS = (
    "hic acilmiyor", "hiç açılmıyor", "veri kaybi", "veri kaybı", "ransomware", "fidye",
    "sistem kullanilamaz", "sistem kullanılamaz", "hic calismiyor", "hiç çalışmıyor",
    "tamamen kullanilamaz", "tamamen kullanılamaz",
)

NON_CRITICAL_ISSUE_TERMS = (
    "chrome", "tarayici", "tarayıcı", "site", "http 409", "409", "bazi siteler", "bazı siteler",
    "uygulama cokuyor", "uygulama çöküyor", "internet", "wifi", "wi-fi", "yavas", "yavaş",
    "yazici", "yazıcı", "mikrofon", "kamera", "bluetooth", "performans",
)

# ===== SOLUTION STEP SAFETY TERMS =====

DANGEROUS_STEP_TERMS = (
    "format", "registry sil", "kayıt defteri sil", "kayit defteri sil", "sistem dosyasi sil",
    "sistem dosyası sil", "rm -rf /", "partition", "bolum sil", "bölüm sil", "fabrika ayar",
)

WARNING_STEP_TERMS = (
    "sudo apt remove", "sudo apt purge", "yonetici", "yönetici", "admin", "driver kaldir",
    "driver kaldır", "sistem ayari sifirla", "sistem ayarı sıfırla", "ag ayarlarini sifirla",
    "ağ ayarlarını sıfırla", "servisi yeniden baslat", "servisi yeniden başlat",
    "yeniden kur", "kaldirip yeniden kur", "kaldırıp yeniden kur", "teknik destek",
    "teknik servis", "guvenlik ekibi", "güvenlik ekibi", "geri donus noktasi",
    "geri dönüş noktası", "yedek",
)

# ===== STEP FORMATTING DETECTION =====

QUESTION_TERMS = (" mi", " mı", " mu", " mü", "hangi", "ne zaman", "nerede", "nasil", "nasıl", "var mi", "var mı")

ACTION_TERMS = (
    "kontrol", "kontrol edin", "test edin", "deneyin", "temizleyin", "kapatin", "kapatın",
    "acin", "açın", "guncelleyin", "güncelleyin", "dogrulayin", "doğrulayın", "not edin",
    "kaydedin", "karsilastirin", "karşılaştırın", "listeleyin", "baslatin", "başlatın",
    "durdurun", "devre disi birakin", "devre dışı bırakın", "etkinlestirin", "etkinleştirin",
    "kaldirin", "kaldırın", "yeniden kurun", "tarama baslatin", "tarama başlatın",
    "yedekleyin", "tasiyin", "taşıyın", "arsivleyin", "arşivleyin", "bildirin",
    "inceleyin", "calistirin", "çalıştırın", "baglantiyi kontrol", "bağlantıyı kontrol",
    "hata mesajini kontrol", "hata mesajını kontrol",
)

# ===== OS-SPECIFIC TERMS =====

WINDOWS_SPECIFIC_TERMS = (
    "windows update", "denetim masasi", "denetim masası", "aygit yoneticisi",
    "aygıt yöneticisi", "powershell", "registry", "regedit", "services.msc",
    "gorev yoneticisi", "görev yöneticisi",
)

LINUX_SPECIFIC_TERMS = (
    "sudo", "sudo apt", "apt-get", "systemctl", "chmod", "chown", "journalctl", "dmesg",
    "lsusb", "lspci", "grep", "bash", "shell script", "linux terminal",
)

MACOS_SPECIFIC_TERMS = ("brew", "launchctl")

# ===== UNSUPPORTED DETAILS =====

UNSUPPORTED_DETAIL_TERMS = ("ubuntu", "debian", "fedora", "edge", "firefox", "safari", "zoom", "teams", "chrome")

# ===== RESTART PATTERN DETECTION =====

RESTART_DONE_TERMS = ("yeniden baslattim", "yeniden başlattım", "restart attim", "restart attım", "denedim", "olmadı", "olmadi", "duzelmedi", "düzelmedi")

RESTART_STEP_TERMS = ("yeniden baslat", "yeniden başlat", "restart")


# ===== CUSTOM EXCEPTIONS =====

class ModelOutputSemanticError(ValueError):
    """Raised when model output fails semantic validation."""
    def __init__(self, reasons: list[str]):
        self.reasons = reasons
        super().__init__("; ".join(reasons))


# ===== PUBLIC API: NORMALIZATION & VALIDATION =====

def normalize_model_output(data: dict, message: str = "", os: str = "") -> dict:
    """Normalize model output: strip whitespace, clean lists."""
    normalized = dict(data)
    for field in ("assistant_message", "category", "priority", "summary", "risk_level"):
        if isinstance(normalized.get(field), str):
            normalized[field] = normalized[field].strip()
    if "possible_causes" in normalized:
        normalized["possible_causes"] = _normalize_list(normalized["possible_causes"])
    if "questions" in normalized:
        normalized["questions"] = _normalize_list(normalized["questions"])
    if "solution_steps" in normalized:
        normalized["solution_steps"] = _normalize_list(normalized["solution_steps"])
    return normalized


def validate_model_semantics(data: dict, message: str = "", os: str = "") -> list[str]:
    """Validate model output semantics; raise exception if blocking errors found."""
    reasons = collect_blocking_validation_errors(data, message, os)
    if reasons:
        raise ModelOutputSemanticError(reasons)
    return reasons


def collect_validation_issues(data: dict, message: str = "", os: str = "") -> dict[str, list[str]]:
    """Collect all validation issues: blocking errors and advisory warnings."""
    reasons = collect_semantic_validation_reasons(data, message, os)
    blocking = []
    advisory = []
    for reason in reasons:
        if _is_blocking_reason(reason):
            blocking.append(reason)
        else:
            advisory.append(reason)
    return {"blocking_errors": blocking, "advisory_warnings": advisory}


def collect_blocking_validation_errors(data: dict, message: str = "", os: str = "") -> list[str]:
    """Get only blocking validation errors (short-hand)."""
    return collect_validation_issues(data, message, os)["blocking_errors"]


def collect_semantic_validation_reasons(data: dict, message: str = "", os: str = "") -> list[str]:
    """Comprehensive semantic validation of response fields."""
    reasons: list[str] = []
    
    # Validate summary quality
    summary = str(data.get("summary", "")).strip()
    summary_key = _normalize_text(summary)
    if not summary:
        reasons.append("summary is empty")
    elif summary_key in {_normalize_text(item) for item in GENERIC_SUMMARIES} or len(summary_key.split()) < 4:
        reasons.append("summary is too generic")

    # Validate list fields
    possible_causes = data.get("possible_causes")
    questions = data.get("questions")
    solution_steps = data.get("solution_steps")

    if not isinstance(possible_causes, list) or len(possible_causes) < 2:
        reasons.append("possible_causes has fewer than 2 items")
    if not isinstance(questions, list) or len(questions) < 1:
        reasons.append("questions has fewer than 1 item")
    if not isinstance(solution_steps, list) or len(solution_steps) < 3:
        reasons.append("solution_steps has fewer than 3 actionable steps")

    # Validate list content quality
    if isinstance(possible_causes, list):
        if any(_looks_like_question(str(item)) for item in possible_causes):
            reasons.append("possible_causes contains a question")
    if isinstance(questions, list):
        if any(not _looks_like_question(str(item)) for item in questions):
            reasons.append("questions contains non-question item")
    if isinstance(solution_steps, list):
        if any(not _looks_actionable(str(item)) for item in solution_steps):
            reasons.append("solution_steps contains non-actionable item")

    # Build response text for consistency checks
    response_parts = [summary]
    if isinstance(possible_causes, list):
        response_parts.extend(str(item) for item in possible_causes)
    if isinstance(questions, list):
        response_parts.extend(str(item) for item in questions)
    if isinstance(solution_steps, list):
        response_parts.extend(str(item) for item in solution_steps)
    response_text = _normalize_text(" ".join(response_parts))

    # Policy-based validation
    reasons.extend(_os_compatibility_reasons(response_text, os))
    reasons.extend(_context_consistency_reasons(response_text, message))
    reasons.extend(_risk_consistency_reasons(data, message))
    reasons.extend(_priority_consistency_reasons(data, message))

    # Check for repeated steps
    message_key = _normalize_text(message)
    if any(term in message_key for term in RESTART_DONE_TERMS):
        if isinstance(solution_steps, list):
            for step in solution_steps:
                if any(term in _normalize_text(str(step)) for term in RESTART_STEP_TERMS):
                    reasons.append("solution repeats an already tried step")

    return reasons


def _normalize_priority_and_risk(data: dict, message: str) -> None:
    message_key = _normalize_text(message)
    issue_is_browser_web = any(term in message_key for term in NON_CRITICAL_ISSUE_TERMS)
    issue_is_critical = any(term in message_key for term in CRITICAL_TERMS)

    if data.get("priority") in {"high", "critical"} and issue_is_browser_web and not issue_is_critical:
        logger.info("priority normalized from high to medium because issue is non-critical browser/web issue")
        data["priority"] = "medium"

    steps = data.get("solution_steps")
    if not isinstance(steps, list):
        return

    step_text = _normalize_text(" ".join(str(step) for step in steps))
    has_dangerous_step = any(term in step_text for term in DANGEROUS_STEP_TERMS)
    has_warning_step = any(term in step_text for term in WARNING_STEP_TERMS)

    if has_dangerous_step and data.get("risk_level") != "dangerous":
        logger.info("risk normalized to dangerous because solution steps include dangerous operations")
        data["risk_level"] = "dangerous"
    elif data.get("risk_level") in {"warning", "dangerous"} and not has_warning_step and not has_dangerous_step:
        logger.info("risk normalized from warning/dangerous to safe because all steps are safe")
        data["risk_level"] = "safe"


def _normalize_choice(value: object, valid_values: set[str], aliases: dict[str, str]) -> object:
    if not isinstance(value, str):
        return value

    key = value.strip().lower().replace("-", "_").replace(" ", "_")
    if key in valid_values:
        return key
    if key in aliases:
        return aliases[key]

    for alias, normalized in aliases.items():
        if alias in key:
            return normalized

    return value


def _normalize_list(value: object) -> list[str]:
    if isinstance(value, list):
        items = value
    else:
        return value

    cleaned = [str(item).strip() for item in items if str(item).strip()]
    return cleaned


def _is_blocking_reason(reason: str) -> bool:
    blocking_terms = (
        "response contains Windows-specific instruction for Linux request",
        "response contains Linux-specific instruction for Windows request",
        "response contains Windows-specific or Linux-specific instruction for macOS request",
        "dangerous solution step lacks explicit warning or professional support guidance",
    )
    if reason in blocking_terms:
        return True
    if "dangerous" in reason and "safe solution steps" not in reason:
        return True
    return False


def _normalize_text(value: str) -> str:
    return value.strip().lower().replace("ı", "i")


def _looks_like_question(value: str) -> bool:
    key = _normalize_text(value)
    return key.endswith("?") or any(term in key for term in QUESTION_TERMS)


def _looks_actionable(value: str) -> bool:
    key = _normalize_text(value)
    if key.endswith("?") or len(key.split()) < 3:
        return False
    if key.startswith("gerekirse") and not any(term in key for term in ACTION_TERMS):
        return False
    if key in {"teknik destek alin", "teknik destek alın", "destek alin", "destek alın"}:
        return False
    return any(term in key for term in ACTION_TERMS)


def _os_compatibility_reasons(response_text: str, os: str) -> list[str]:
    os_key = _normalize_text(os)
    if os_key == "linux" and _contains_os_specific_term(response_text, WINDOWS_SPECIFIC_TERMS + MACOS_SPECIFIC_TERMS):
        return ["response contains Windows-specific instruction for Linux request"]
    if os_key == "windows" and _contains_os_specific_term(response_text, LINUX_SPECIFIC_TERMS + MACOS_SPECIFIC_TERMS):
        return ["response contains Linux-specific instruction for Windows request"]
    if os_key == "macos" and _contains_os_specific_term(response_text, WINDOWS_SPECIFIC_TERMS + LINUX_SPECIFIC_TERMS):
        return ["response contains Windows-specific or Linux-specific instruction for macOS request"]
    if os_key == "unknown" and _contains_os_specific_term(response_text, WINDOWS_SPECIFIC_TERMS + LINUX_SPECIFIC_TERMS + MACOS_SPECIFIC_TERMS):
        return ["response contains OS-specific instruction for Unknown OS request"]
    return []


def _contains_os_specific_term(text: str, terms: tuple[str, ...]) -> bool:
    padded = f" {text} "
    for term in terms:
        term_key = _normalize_text(term)
        if " " in term_key or "." in term_key or "-" in term_key:
            if term_key in text:
                return True
        elif f" {term_key} " in padded:
            return True
    return False


def _context_consistency_reasons(response_text: str, message: str) -> list[str]:
    message_key = _normalize_text(message)
    for term in UNSUPPORTED_DETAIL_TERMS:
        if term in response_text and term not in message_key:
            if term in {"chrome", "zoom"} and any(generic in message_key for generic in ("tarayici", "tarayıcı", "toplanti", "toplantı")):
                continue
            return ["response introduces unsupported product or OS detail"]
    return []


def _risk_consistency_reasons(data: dict, message: str) -> list[str]:
    risk = data.get("risk_level")
    steps = data.get("solution_steps")
    if not isinstance(steps, list):
        return []

    step_text = _normalize_text(" ".join(str(step) for step in steps))
    has_dangerous_step = any(term in step_text for term in DANGEROUS_STEP_TERMS)
    has_warning_step = any(term in step_text for term in WARNING_STEP_TERMS)
    reasons = []
    if risk == "dangerous" and not has_dangerous_step:
        reasons.append("risk_level dangerous is inconsistent with safe solution steps")
    if risk == "warning" and not has_warning_step and not has_dangerous_step:
        reasons.append("risk_level warning is inconsistent with safe solution steps")
    if has_dangerous_step and "destek" not in step_text and "yedek" not in step_text and "uyari" not in step_text and "uyarı" not in step_text:
        reasons.append("dangerous solution step lacks explicit warning or professional support guidance")
    return reasons


def _priority_consistency_reasons(data: dict, message: str) -> list[str]:
    priority = data.get("priority")
    message_key = _normalize_text(message)
    issue_is_non_critical = any(term in message_key for term in NON_CRITICAL_ISSUE_TERMS)
    issue_is_critical = any(term in message_key for term in CRITICAL_TERMS)
    if priority == "critical" and not issue_is_critical:
        return ["priority critical is inconsistent with non-critical issue"]
    if priority == "high" and issue_is_non_critical and not issue_is_critical:
        return ["priority high is inconsistent with non-critical issue"]
    return []
