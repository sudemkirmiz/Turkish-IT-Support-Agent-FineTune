import json
import pytest

from backend.app.json_utils import JSONExtractionError, extract_json


class TestExtractJsonClean:
    """Temiz JSON parse testleri"""

    def test_extract_json_with_clean_object(self):
        """Temiz JSON object parse edilir."""
        obj = {
            "category": "network_issue",
            "priority": "high",
            "summary": "Test özet.",
            "possible_causes": ["neden 1", "neden 2"],
            "questions": ["soru 1?", "soru 2?"],
            "solution_steps": ["adım 1", "adım 2"],
            "risk_level": "safe",
        }
        json_str = json.dumps(obj, ensure_ascii=False)
        result = extract_json(json_str)
        assert result == obj

    def test_extract_json_with_unicode(self):
        """Unicode karakterleri içeren JSON parse edilir."""
        obj = {
            "category": "software_issue",
            "priority": "medium",
            "summary": "Yazılım çöküşü.",
            "possible_causes": ["Bellek taşması", "Sürüm uyumsuzluğu"],
            "questions": ["Hata kodu nedir?", "Ne zaman başladı?"],
            "solution_steps": ["Tarayıcı cache temizle", "Yazılımı güncelle"],
            "risk_level": "warning",
        }
        json_str = json.dumps(obj, ensure_ascii=False)
        result = extract_json(json_str)
        assert result == obj

    def test_extract_json_from_nested_arrays(self):
        """İçinde nested array olan object parse edilir."""
        obj = {
            "category": "os_error",
            "priority": "critical",
            "summary": "İşletim sistemi hatası.",
            "possible_causes": ["Dosya sistemi hasar", "Driver sorunu"],
            "questions": ["Başlangıç yazılımı sorunsuz mu?", "Hata mesajı nedir?"],
            "solution_steps": ["Günlük başlat", "Sistem dosyaları onar"],
            "risk_level": "dangerous",
        }
        json_str = json.dumps(obj, ensure_ascii=False)
        result = extract_json(json_str)
        assert result == obj


class TestExtractJsonWithExtraText:
    """JSON öncesinde/sonrasında metin testleri"""

    def test_extract_json_with_explanation_before(self):
        """JSON öncesinde açıklama varsa object ayıklanır."""
        obj = {
            "category": "hardware_issue",
            "priority": "high",
            "summary": "Donanım arızası.",
            "possible_causes": ["Isı soğutması yetersiz", "RAM defekti"],
            "questions": ["Fan ses yüksek mi?", "Bilgisayar restarts mi?"],
            "solution_steps": ["Soğutma kontrol et", "RAM testi yap"],
            "risk_level": "warning",
        }
        json_str = f"Analiz sonucu:\n{json.dumps(obj, ensure_ascii=False)}"
        result = extract_json(json_str)
        assert result == obj

    def test_extract_json_with_text_after(self):
        """JSON sonrasında ekstra metin varsa object ayıklanır."""
        obj = {
            "category": "performance_issue",
            "priority": "medium",
            "summary": "Bilgisayar yavaş.",
            "possible_causes": ["Virüs/Malware", "Disk full"],
            "questions": ["Disk doluluk nedir?", "Arkaplan processleri nedir?"],
            "solution_steps": ["Virüs taraması yap", "Disk temizle"],
            "risk_level": "safe",
        }
        json_str = f"{json.dumps(obj, ensure_ascii=False)}\n\nEğer sorun devam ederse teknik destek ile iletişime geçin."
        result = extract_json(json_str)
        assert result == obj

    def test_extract_json_with_text_before_and_after(self):
        """JSON'ün hem önü hem arkası metin içerirse object ayıklanır."""
        obj = {
            "category": "driver_issue",
            "priority": "high",
            "summary": "Driver sorunu.",
            "possible_causes": ["Eski sürüm driver", "Sürücü çakışması"],
            "questions": ["Device Manager'da sarı ünlem var mı?", "Driver ne zaman kuruldu?"],
            "solution_steps": ["Driver güncelle", "Eski driveri kaldır"],
            "risk_level": "warning",
        }
        prefix = "Sorun analiz ediliyor...\n"
        suffix = "\n\nÜsteğinde yardım talep edebilirsiniz."
        json_str = f"{prefix}{json.dumps(obj, ensure_ascii=False)}{suffix}"
        result = extract_json(json_str)
        assert result == obj


class TestExtractJsonMultiple:
    """Birden fazla JSON içeren testler"""

    def test_extract_first_valid_json_when_multiple_objects(self):
        """Birden fazla { varsa ilk geçerli JSON object ayıklanır."""
        obj1 = {"category": "network_issue", "priority": "low"}
        obj2 = {"category": "software_issue", "priority": "high"}
        
        # Birden fazla JSON, ama json_utils ilk geçerli biri seçmeli
        json_str = f"İlk deneme: {json.dumps(obj1)}\nİkinci deneme: {json.dumps(obj2)}"
        result = extract_json(json_str)
        # İlk geçerli JSON object'i seçer
        assert result["category"] == "network_issue"


class TestExtractJsonEdgeCases:
    """Edge case testleri"""

    def test_extract_json_with_escaped_quotes_in_string(self):
        """String içinde escaped tırnak varsa parse edilir."""
        obj = {
            "category": "security_issue",
            "priority": "critical",
            "summary": 'Güvenlik sorunu "Ransomware" riski.',
            "possible_causes": ["Spam e-posta", "Güvenilmez download"],
            "questions": ["Dosyalar kilitli mi?", 'Ekran mesajı görüyor musunuz?'],
            "solution_steps": ["Antivirus kapat", "Güvenli modda başlat"],
            "risk_level": "dangerous",
        }
        json_str = json.dumps(obj, ensure_ascii=False)
        result = extract_json(json_str)
        assert result["category"] == "security_issue"

    def test_extract_json_with_whitespace(self):
        """Fazla whitespace varsa yine parse edilir."""
        obj = {
            "category": "peripheral_issue",
            "priority": "medium",
            "summary": "Çevre birimi problemi.",
            "possible_causes": ["Bağlantı sosu", "Driver eksik"],
            "questions": ["Cihaz tanınıyor mu?", "Kablo sağlam mı?"],
            "solution_steps": ["USB bağlantısını kontrol et", "Driver yükle"],
            "risk_level": "safe",
        }
        json_str = f"\n\n{json.dumps(obj, ensure_ascii=False)}\n\n"
        result = extract_json(json_str)
        assert result["category"] == "peripheral_issue"

    def test_extract_json_empty_string_raises_error(self):
        """Boş string error verir."""
        with pytest.raises(JSONExtractionError, match="Modelden cevap alınamadı"):
            extract_json("")

    def test_extract_json_whitespace_only_raises_error(self):
        """Yalnızca whitespace error verir."""
        with pytest.raises(JSONExtractionError, match="Modelden cevap alınamadı"):
            extract_json("   \n\n  ")

    def test_extract_json_no_braces_raises_error(self):
        """Hiç { yoksa error verir."""
        with pytest.raises(JSONExtractionError, match="geçerli JSON"):
            extract_json("Bu metin JSON değil.")

    def test_extract_json_only_opening_brace_raises_error(self):
        """Kapanmayan { error verir."""
        with pytest.raises(JSONExtractionError, match="geçerli JSON"):
            extract_json('{"category": "network_issue"')

    def test_extract_json_invalid_json_raises_error(self):
        """Geçersiz JSON sözdizimi error verir."""
        with pytest.raises(JSONExtractionError, match="geçerli JSON"):
            extract_json('{"category": network_issue}')  # string değil

    def test_extract_json_top_level_array_raises_error(self):
        """Üst seviye array error verir."""
        with pytest.raises(JSONExtractionError, match="geçerli JSON"):
            # Array kullanılıyor, sadece {} ile başlayması lazım
            extract_json('["Güncelleme sonrası ses hatası", "Başka cihazda da mı?"]')


class TestExtractJsonCommonModelOutputs:
    """Modelin tipik hatalı output'ları test et"""

    def test_extract_json_with_model_preamble(self):
        """Model cevapın başına açıklama yazarsa ayıklanır."""
        obj = {
            "category": "storage_issue",
            "priority": "high",
            "summary": "Depolama sorunu.",
            "possible_causes": ["Disk dolu", "Bad sector"],
            "questions": ["Hangi sürücü full?", "Kaç GB kalmış?"],
            "solution_steps": ["Gereksiz dosyaları sil", "Disk kontrol et"],
            "risk_level": "warning",
        }
        model_output = f"Sorun analiz ediliyor, lütfen bekleyin...\n\n{json.dumps(obj, ensure_ascii=False)}\n\nAnaliz tamamlandı."
        result = extract_json(model_output)
        assert result["category"] == "storage_issue"

    def test_extract_json_with_trailing_explanation(self):
        """Model JSON'un sonuna açıklama yazarsa ayıklanır."""
        obj = {
            "category": "unknown_issue",
            "priority": "medium",
            "summary": "Bilinmeyen sorun.",
            "possible_causes": ["Tanımlanmamış hata", "Sistem sorunu"],
            "questions": ["Hata kodu nedir?", "Ne zaman başladı?"],
            "solution_steps": ["Sistem güncellemesini kontrol et", "Sabit disks scan et"],
            "risk_level": "safe",
        }
        model_output = f'{json.dumps(obj, ensure_ascii=False)}\n\nEğer sorununuz devam ederse, bize rapor edin.'
        result = extract_json(model_output)
        assert result["category"] == "unknown_issue"

    def test_extract_json_with_markdown_formatting(self):
        """Model JSON'u markdown içinde yazarsa ayıklanır."""
        obj = {
            "category": "os_error",
            "priority": "critical",
            "summary": "İşletim sistemi arızası.",
            "possible_causes": ["Boot sektörü hasar", "BIOS ayarı"],
            "questions": ["Bilgisayar açılıyor mu?", "Başlangıç disksi var mı?"],
            "solution_steps": ["Başlangıç yazılımını onar", "BIOS sıfırla"],
            "risk_level": "dangerous",
        }
        model_output = f"""
## Sorun Analizi

```json
{json.dumps(obj, ensure_ascii=False)}
```

Lütfen yukarıdaki önerileri deneyin.
"""
        result = extract_json(model_output)
        assert result["category"] == "os_error"
