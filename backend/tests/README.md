# Backend Tests

Unit ve integration testleri.

---

## 📋 Test Dosyaları

### `conftest.py`
**Pytest Konfigürasyonu**
- Fixtures tanımları
- Setup/teardown
- Mock'lar
- Test helpers

---

### `test_analyze.py`
**API Analyze Endpoint Testleri (35+ test)**

Model çıkarımı ve API response'ları test et.

**Test Kategorileri:**

#### Health Check
```python
def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
```

#### Intent Detection
```python
def test_analyze_network_issue()
def test_analyze_performance_issue()
def test_analyze_hardware_issue()
# ... 10 kategori
```

#### Error Handling
```python
def test_analyze_empty_message()
def test_analyze_invalid_os()
def test_model_loading_failure()
```

#### Session Management
```python
def test_create_session()
def test_list_sessions()
def test_delete_session()
```

**Çalıştırma:**
```bash
pytest test_analyze.py -v
# veya
pytest test_analyze.py::test_analyze_network_issue -v
```

---

### `test_json_utils.py`
**JSON Çıkarma ve Doğrulama Testleri (15+ test)**

JSON parsing ve fuzzy matching test et.

**Test Kategorileri:**

#### Valid JSON
```python
def test_extract_valid_json()
def test_extract_json_with_typos()
def test_extract_nested_json()
```

#### Invalid JSON
```python
def test_extract_invalid_json()
def test_extract_empty_string()
def test_extract_partial_json()
```

#### Fuzzy Matching
```python
def test_fuzzy_match_enum_values()
def test_fuzzy_match_with_case_insensitive()
```

**Çalıştırma:**
```bash
pytest test_json_utils.py -v
pytest test_json_utils.py::test_extract_valid_json -v
```

---

## 🚀 Tüm Testleri Çalıştırma

### Temel Komutlar

```bash
# Tüm testler
pytest tests/ -v

# Coverage raporu
pytest tests/ --cov=app --cov-report=html

# Belirli bir test dosyası
pytest tests/test_analyze.py -v

# Belirli bir test
pytest tests/test_analyze.py::test_analyze_network_issue -v

# Parallel çalıştırma (hızlı)
pytest tests/ -n auto -v

# Fail edilen testleri tekrar çalıştır
pytest tests/ --lf -v
```

### Test Markers

```bash
# Slow testleri atla
pytest tests/ -m "not slow"

# Sadece integration testleri
pytest tests/ -m integration

# Sadece unit testleri
pytest tests/ -m unit
```

---

## 📊 Test Kapsamı

### Target Coverage
- **Genel**: 90%+
- **Critical paths**: 100%
- **Error handling**: 95%+

### Mevcut Coverage
```
app/
├── main.py                  95%
├── model_service.py         92%
├── conversation_router.py   88%
├── json_utils.py            94%
├── response_normalizer.py   91%
└── session_store.py         89%
```

### Coverage Report Oluştur

```bash
# HTML report
pytest tests/ --cov=app --cov-report=html
# Open: htmlcov/index.html

# Terminal report
pytest tests/ --cov=app --cov-report=term-missing

# Specific file
pytest tests/ --cov=app.model_service --cov-report=term
```

---

## ✅ Test Yazma Rehberi

### Test Dosyası Yapısı

```python
"""Test module for app.model_service."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from app.model_service import analyze_message, ModelServiceError

# Fixtures
@pytest.fixture
def sample_message():
    return "Wi-Fi bağlı ama internete giremiyorum."

@pytest.fixture
def mock_model():
    with patch('app.model_service.AutoPeftModelForCausalLM') as mock:
        yield mock

# Tests
class TestAnalyzeMessage:
    """Tests for analyze_message function."""
    
    def test_analyze_network_issue(self, sample_message):
        """Test network issue detection."""
        result = analyze_message(sample_message, "Windows")
        
        assert result["category"] == "network_issue"
        assert "priority" in result
        assert result["risk_level"] in ["safe", "warning", "dangerous"]
    
    def test_analyze_with_invalid_os(self):
        """Test error handling for invalid OS."""
        with pytest.raises(ValueError):
            analyze_message("Test message", "InvalidOS")
    
    @pytest.mark.slow
    def test_analyze_performance(self):
        """Test response time is under 5 seconds."""
        import time
        start = time.time()
        
        result = analyze_message("Test", "Windows")
        
        elapsed = time.time() - start
        assert elapsed < 5.0, f"Response took {elapsed}s"
```

### Best Practices

- ✅ Descriptive test names
- ✅ One assertion per test (ideally)
- ✅ Use fixtures for setup
- ✅ Test edge cases
- ✅ Test error paths
- ✅ Use mocks wisely
- ✅ Docstrings

---

## 🐛 Test Debugging

### Verbose Output
```bash
pytest tests/ -v -s  # -s shows print statements
```

### Enter Debugger on Failure
```bash
pytest tests/ --pdb  # drops to pdb on failure
```

### Show Local Variables
```bash
pytest tests/ -l
```

### Capture Logs
```bash
pytest tests/ --log-cli-level=DEBUG
```

---

## 📋 Test Checklist (PR Açarken)

- [ ] Yeni testler yazdım
- [ ] Mevcut testler geçiyor (`pytest tests/ -v`)
- [ ] Coverage %90+ (`pytest --cov=app`)
- [ ] Slow testleri işaretledim (`@pytest.mark.slow`)
- [ ] Docstring'ler var
- [ ] Edge cases test edilmiş
- [ ] Error paths test edilmiş

---

## 🚀 CI/CD Integration

### GitHub Actions Example
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: 3.13
      - run: pip install -r requirements.txt
      - run: pytest tests/ --cov=app
      - run: pytest tests/ --cov=app --cov-report=xml
```

---

## 📚 Kaynaklar

- [Pytest Docs](https://docs.pytest.org/)
- [unittest.mock](https://docs.python.org/3/library/unittest.mock.html)
- [Coverage.py](https://coverage.readthedocs.io/)

---

**Last Updated:** 2026-06-08
