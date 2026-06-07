# Model Quality Notes

Bilinen durumlar:

- Model bazen JSON dışı cevap üretebilir; backend aynı model ile bir retry yapar.
- Türkçe cevap kalitesi dataset kalitesine bağlıdır.
- Backend cevap üretmez veya semantic düzeltme yapmaz.
- Advisory validation kalite uyarılarını metadata olarak döndürebilir.
