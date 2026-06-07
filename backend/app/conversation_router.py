"""Conversation intent detection helpers."""

# ===== INTENT DETECTION TERMS =====

FOLLOW_UP_TERMS = (
    "olmuyor", "düzelmedi", "duzelmedi", "başka ne yapayım", "baska ne yapayim",
    "işe yaramadı", "ise yaramadi", "hala aynı", "hala ayni", "hâlâ aynı",
    "denedim olmadı", "denedim olmadi", "yine oluyor", "tekrar oluyor",
    "ama yine", "ama hala", "ama hâlâ",
)

SMALLTALK_TERMS = (
    "sen kimsin", "kimsin", "merhaba", "selam", "teşekkürler", "tesekkurler",
    "teşekkür ederim", "tesekkur ederim", "tamam", "ne yapıyorsun", "ne yapiyorsun",
    "nasılsın", "nasilsin", "naber",
)

OUT_OF_SCOPE_TERMS = (
    "hava nasıl", "hava nasil", "hava durumu", "yemek tarifi", "tarif verir misin", "tarif",
    "bugün tarih", "bugun tarih", "tarih nedir", "tarih", "spor", "spor haberleri",
    "okul", "magazin", "film öner", "film oner",
)

TRIED_STEP_PATTERNS = {
    "yeniden başlatma denendi": ("yeniden başlattım", "yeniden baslattim", "restart attım", "restart attim", "kapatıp açtım", "kapatip actim"),
    "güncelleme denendi": ("güncelledim", "guncelledim", "update yaptım", "update yaptim"),
    "yeniden kurulum denendi": ("sildim", "tekrar kurdum", "yeniden kurdum", "kaldırdım", "kaldirdim"),
    "cache temizleme denendi": ("cache temizledim", "önbellek temizledim", "onbellek temizledim", "çerezleri temizledim"),
    "farklı tarayıcı denendi": ("farklı tarayıcı", "farkli tarayici", "başka tarayıcı", "baska tarayici"),
    "tarama denendi": ("tarama yaptım", "tarama yaptim", "antivirüs", "defender taraması"),
    "eklenti kapatma denendi": ("eklentileri kapattım", "eklentileri kapattim", "eklenti kapattım", "eklenti kapattim", "eklentileri devre dışı", "eklentileri devre disi"),
    "donanım hızlandırma kapatma denendi": ("donanım hızlandırmayı kapattım", "donanim hizlandirmayi kapattim", "hardware acceleration kapattım"),
}

CATEGORY_KEYWORDS = (
    ("security_issue", ("virüs", "virus", "şüpheli dosya", "supheli dosya", "malware", "ransomware", "oltalama", "phishing", "zararlı", "zararli")),
    ("driver_issue", ("driver", "sürücü", "surucu", "ekran kartı", "ekran karti", "ses sürücüsü", "wi-fi driver")),
    ("peripheral_issue", ("mikrofon", "kamera", "yazıcı", "yazici", "mouse", "klavye", "kulaklık", "kulaklik", "bluetooth", "zoom’da mikrofon", "zoom'da mikrofon")),
    ("storage_issue", ("disk dolu", "depolama", "dosya silemiyorum", "hard disk", "ssd", "harici disk", "alan yok")),
    ("hardware_issue", ("laptop ısınıyor", "laptop isiniyor", "fan", "batarya", "ekran siyah", "açılmıyor", "acilmiyor", "kendi kendine kapanıyor", "kendi kendine kapaniyor", "fiziksel")),
    ("os_error", ("mavi ekran", "kernel panic", "windows update sonrası sistem açılmıyor", "linux güncellemesinden sonra boot", "sistem açılırken hata", "sistem acilirken hata", "işletim sistemi hatası", "sistem dosyası hatası")),
    ("network_issue", ("wi-fi", "wifi", "internet", "dns", "modem", "router", "bağlantı", "baglanti", "site açılmıyor", "site acilmiyor", "ping", " ip ", "404", "409", "500", "http hata")),
    ("performance_issue", ("çok yavaş", "cok yavas", "kasıyor", "kasiyor", "donuyor", "ram", "cpu", "performans")),
    ("software_issue", ("chrome", "firefox", "edge", "browser", "tarayıcı", "tarayici", "uygulama çöküyor", "uygulama cokuyor", "program açılmıyor", "program acilmiyor", "uygulama kapanıyor", "uygulama kapaniyor", "exe açılmıyor", "kurulum hatası")),
)


def is_follow_up(message: str, session: dict) -> bool:
    if not session.get("active_issue"):
        return False
    key = message.strip().lower()
    if is_smalltalk(message):
        return False
    return any(term in key for term in FOLLOW_UP_TERMS)


def is_smalltalk(message: str) -> bool:
    key = message.strip().lower().strip(" .!?\n\t")
    return any(key == term or key.startswith(f"{term} ") for term in SMALLTALK_TERMS)


def is_out_of_scope(message: str) -> bool:
    key = message.strip().lower().strip(" .!?\n\t")
    return any(term in key for term in OUT_OF_SCOPE_TERMS)


def detect_intent(message: str, session: dict) -> str:
    if is_smalltalk(message):
        return "smalltalk"
    if is_out_of_scope(message):
        return "out_of_scope"
    if is_follow_up(message, session):
        return "follow_up"
    if any(term in message.strip().lower() for _, terms in CATEGORY_KEYWORDS for term in terms):
        return "technical_issue"
    return "unclear"


def extract_tried_steps(message: str) -> list[str]:
    key = message.strip().lower()
    tried = []
    for label, patterns in TRIED_STEP_PATTERNS.items():
        if any(pattern in key for pattern in patterns):
            tried.append(label)
    if any(term in key for term in ("olmuyor", "olmadı", "olmadi", "işe yaramadı", "ise yaramadi", "düzelmedi", "duzelmedi")):
        tried.append("önceki öneriler işe yaramadı")
    return tried

