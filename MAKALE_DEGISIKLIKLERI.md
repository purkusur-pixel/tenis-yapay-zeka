# Makale (TR.docx → TR_son.docx) değişiklik listesi

Tüm sayılar `06_bes_model_karsilastirma.py` çıktılarından alınmıştır (`cikti/karsilastirma/`).
**Ana analiz** (54 bölge; Tablo 1–4, Şekil 1–3) başka bir kodla üretildiği için **değiştirilmedi**.
Değişen kısım, yeni 4 girdi → 4 çıktı sistemine karşılık gelen **tamamlayıcı analiz** ve ona bağlı yerlerdir.
52 Mendeley atıfının tamamı korunmuştur; kaynakça değişmemiştir (yeni kaynak eklenmedi).

## Neden değişti?
Eski tamamlayıcı analiz 30 öznitelik kullanıyordu: vuruş türü, spin, yükseklik ve kademe **girdi** olarak yer alıyordu.
Makale de bunun bir tutarsızlık olduğunu kendisi belirtiyordu.
Yeni analizde yalnızca bir antrenörün makine arayüzünde seçebileceği 4 bağlam **girdi** olarak kullanılıyor:
cinsiyet, maç düzeyi, vuranın konumu ve rakibin konumu.
Spin, yükseklik ve kademe ise artık **çıktı**.
Bu değişiklik iki sonucu tersine çevirdi:
1. MLP artık en iyi model değil. En düşük log-kaybını ağaç toplulukları veriyor (XGBoost / LightGBM).
2. "En iyi model diğerlerine anlamlı üstünlük sağlamamıştır" cümlesi artık doğru değil. XGBoost, düşme bölgesi log-kaybında diğer dört modelden anlamlı ölçüde daha iyi. Ancak kazanç küçük, ilk-1 doğruluğundaki fark da anlamlı değil.

## Yerlere göre değişiklikler

| # | Yer | Değişiklik |
|---|---|---|
| 1 | **Öz** | "Kanonik 18 hücreli…anlamlı bulunmamıştır" iki cümlesi yerine yeni tamamlayıcı analizin özeti yazıldı (5 model, 4 çıktı; XGBoost 2.304 vs frekans 2.395; ilk-1 19.6% vs 18.6%; yükseklikte üstünlük yok). |
| 2 | **1 Giriş, son paragraf** (RQ'lar) | RQ2'nin arkasına tamamlayıcı analizin sorusu eklendi (spin, yükseklik ve kademe konum senaryosundan öğrenilebilir mi; 5 model ayrışıyor mu). |
| 3 | **2.8 başlığı** | "…dört girdili ve dört çıktılı atış modelinde beş makine öğrenmesi modelinin karşılaştırılması" |
| 4 | **2.8, 1. paragraf** | Baştan yazıldı: 4 farklılık; 15 öznitelik; vuruş türü kullanılmıyor; spin, yükseklik ve kademe çıktı olarak modelleniyor; sınıf dağılımları; spin etiketi uyarısı. |
| 5 | **2.8, 2. paragraf** | Tüm hiperparametreler yazıldı (frekans tablosu, LR, RF, XGBoost, LightGBM, MLP). **[YAZARLAR TAMAMLAYACAK: hiperparametreler] dolduruldu.** |
| 6 | **2.8, 3. paragraf** | Değerlendirme: log-kaybı birincil ölçüt; Brier, ECE, ilk-1, dengeli doğruluk; 2,000 maç bootstrap GA; eşleştirilmiş farklar; Wilcoxon (log-kaybı ve ilk-1) + Holm; McNemar'ın neden kullanılmadığı; servis/ralli raporlaması. |
| 7 | **2.9** | **[YAZARLAR TAMAMLAYACAK: Python ve kütüphane sürümleri] dolduruldu** (Python 3.13.18, NumPy 2.5.4, pandas 3.1.0, SciPy 1.18.1, scikit-learn 1.9.1, XGBoost 3.4.1, LightGBM 4.7.0, Matplotlib 3.11.2). Betik adları eklendi. |
| 8 | **3.5 başlığı** | "…beş makine öğrenmesi modelinin dört çıktıda karşılaştırılması" |
| 9 | **3.5, 1. paragraf** | Baştan yazıldı: düşme bölgesi sonuçları (Tablo 5, Şekil 4, Şekil 5). |
| 10 | **3.5, 2. paragraf (yeni)** | Spin, yükseklik ve kademe sonuçları (Tablo 6). |
| 11 | **3.5, 3. paragraf (yeni)** | Servis ve ralli kırılımı (Tablo 7): yüksek doğruluk büyük ölçüde servislerden geliyor. |
| 12 | **4.1, son paragraf** | Baştan yazıldı. Lojistik regresyon burada neden zayıf (konumlar sayısal, ana analizde one-hot); kazançlar küçük; kalibrasyon (LightGBM ECE); servis etkisi. |
| 13 | **4.2, yeni paragraf** | Prototip arayüz: 4,356 kombinasyonluk önceden hesaplanmış tablo (2.7 MB). Model çalıştırmadan okuma, gömülü denetleyiciye uygunluk. Best eğitimde var, arayüzde Orta ve Low. |
| 14 | **4.4 Sınırlılıklar** | "Üreteç henüz spini modellememektedir" cümlesi güncellendi. Spin artık çıktı olarak modelleniyor ama etiketler tutarsız. Servis/ralli ayrımı yalnızca konumdan yapılıyor. |
| 15 | **5 Sonuç** | 2. cümle değişti: ağaç toplulukları tutarlı ama küçük kazanç sağlıyor, yükseklikte kazanç yok. |
| 16 | **Veri erişilebilirliği** | Kodun Ek Materyal'de olduğu cümlesi eklendi. |
| 17 | **Üretken YZ beyanı** | "prototip arayüzü yazmak" eklendi, tarih "Ekim–Kasım 2026" yapıldı. |
| 18 | **Tablo 5** | Tamamen yenilendi: 7 model × log-kaybı (95% GA), Brier, ECE, ilk-1, ilk-3, kaba, ortalama hata. |
| 19 | **Tablo 6 (yeni)** | Spin, yükseklik ve kademe; 7 model × log-kaybı (95% GA), Brier, ECE, ilk-1, dengeli doğruluk. |
| 20 | **Tablo 7 (yeni)** | Servis ve ralli: frekans tablosu ve en iyi model. |
| 21 | **Şekil 4 (yeni)** | Frekans tablosuna göre log-kaybı farkı, 95% GA, 4 panel. |
| 22 | **Şekil 5 (yeni)** | Güvenirlik eğrileri (en iyi model ve frekans tablosu), 4 panel. |
| 23 | Sarı vurgular | Yalnızca doldurulan yer tutucularda ve eski Tablo 5'te vardı; bunlar kaldırıldı. |

## Hâlâ yazarın tamamlaması gerekenler (değiştirilmedi)
- 2.1: **[YAZARLAR TAMAMLAYACAK: video kaynakları, işaretleme yazılımı, işaretleyicilerin sayısı ve eğitimi …]**
- Etik beyanı: **[YAZARLAR ONAYLAYACAK: etik onay / muafiyet]**
- Yazar katkıları: **[YAZARLAR CRediT rollerini … TAMAMLAYACAK]**
- Sorumlu yazar e-postası (başlık sayfasında boş).
- Mendeley'de "Refresh" yapılması önerilir: atıflar korunsa da yeri değişen atıflar oldu (McNemar atfı aynı paragrafta yer değiştirdi).

## Kendi bilgisayarında yeniden çalıştırırsan
`python 06_bes_model_karsilastirma.py` aynı veriyle aynı sayıları üretir (tohum 42).
Kütüphane sürümleri farklıysa `cikti/karsilastirma/surumler.csv` dosyasındaki değerleri 2.9'a yaz.
Sayılar son basamakta değişirse Tablo 5–7'yi `karsilastirma_tablolari.xlsx` dosyasından güncelle.
