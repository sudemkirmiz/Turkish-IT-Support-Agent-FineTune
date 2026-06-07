import json
import re


class JSONExtractionError(ValueError):
    pass


def extract_json(raw_output: str) -> dict:
    """
    Model çıktısından geçerli JSON object'i ayıkla.
    
    Süslü parantez dengesi takip edilerek, modelin output'unda
    geçerli JSON object'i bulmaya çalışır.
    
    Brace matching kullanarak:
    - İlk { karakterinden başla
    - String içi tırnakları ve escape karakterlerini dikkate al
    - Süslü parantez dengesi sıfıra düştüğünde aday JSON'u parse etmeyi dene
    - Birden fazla { varsa sırayla dene
    - Geçerli dict bulunursa onu döndür
    
    Argümanlar:
        raw_output: Model tarafından döndürülen ham metin
        
    Dönüş:
        dict: Geçerli JSON object'i
        
    İstisnalar:
        JSONExtractionError: Geçerli JSON object bulunamazsa
    """
    if not raw_output or not raw_output.strip():
        raise JSONExtractionError("Modelden cevap alınamadı.")

    # Tüm { pozisyonlarını bul
    brace_positions = [i for i, char in enumerate(raw_output) if char == "{"]
    
    if not brace_positions:
        raise JSONExtractionError("Model çıktısı geçerli JSON formatında değil.")
    
    # Her { pozisyonundan başlayarak deneme yap
    for start_pos in brace_positions:
        try:
            parsed = _extract_json_from_position(raw_output, start_pos)
            if isinstance(parsed, dict):
                return parsed
        except (json.JSONDecodeError, JSONExtractionError):
            # Bu pozisyon başarısız, sonrakini dene
            continue
    
    # Hiçbir geçerli JSON bulunamadı
    raise JSONExtractionError("Model çıktısı geçerli JSON formatında değil.")


def _extract_json_from_position(raw_output: str, start_pos: int) -> dict:
    """
    Verilen pozisyondan başlayarak geçerli JSON object'i ayıkla.
    
    Brace matching kullanarak süslü parantez dengesi takip edilir:
    - String içi tırnaklar (\" ve \\) dikkate alınır
    - Denge sıfıra düştüğünde parsing denenir
    """
    brace_balance = 0
    in_string = False
    escape_next = False
    
    for pos in range(start_pos, len(raw_output)):
        char = raw_output[pos]
        
        # Escape karakteri işle
        if escape_next:
            escape_next = False
            continue
        
        if char == "\\":
            escape_next = True
            continue
        
        # String içi/dışı takip et
        if char == '"':
            in_string = not in_string
            continue
        
        # String dışındaysa parantez dengesi takip et
        if not in_string:
            if char == "{":
                brace_balance += 1
            elif char == "}":
                brace_balance -= 1
                
                # Denge sıfıra ulaştı = potansiyel JSON object tamamlandı
                if brace_balance == 0:
                    json_text = raw_output[start_pos : pos + 1]
                    try:
                        parsed = json.loads(json_text)
                        if not isinstance(parsed, dict):
                            raise JSONExtractionError(
                                "Model çıktısı JSON object formatında olmalıdır."
                            )
                        return parsed
                    except json.JSONDecodeError:
                        # Bu pozisyon başarısız
                        raise JSONExtractionError(
                            "Model çıktısı geçerli JSON formatında değil."
                        )
            
            # Denge negatif oldu = yapı bozuldu
            if brace_balance < 0:
                raise JSONExtractionError(
                    "Model çıktısı geçerli JSON formatında değil."
                )
    
    # Loop bittti ama denge hala pozitif = JSON kapanmadı
    raise JSONExtractionError("Model çıktısı geçerli JSON formatında değil.")
def extract_partial_json(raw_output: str) -> dict:
    text = raw_output[raw_output.find("{") :] if "{" in raw_output else raw_output
    if not text.strip().startswith("{"):
        return {}

    data = {
        "category": "unknown_issue",
        "priority": "medium",
        "summary": "Sorun analiz edildi.",
        "possible_causes": ["Belirti netlestirilmeli."],
        "questions": ["Sorun ne zamandir devam ediyor?"],
        "solution_steps": ["Cihazi yeniden baslatin ve tekrar deneyin."],
        "risk_level": "warning",
    }

    for key in data:
        value = _extract_partial_value(text, key)
        if value is not None:
            data[key] = value

    return data


def _extract_partial_value(text: str, key: str):
    match = re.search(rf'"{re.escape(key)}"\s*:\s*(\[[^\]]*\]|"(?:\\.|[^"\\])*")', text)
    if not match:
        return None

    raw_value = match.group(1)
    try:
        return json.loads(raw_value)
    except json.JSONDecodeError:
        if raw_value.startswith('"'):
            return raw_value.strip('"')
        return None
