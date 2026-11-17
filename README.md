# All-in Dashboard

Birden fazla trade backtest reposunun sonuçlarını tek tabloda birleştiren dashboard.

## Açma

- `index.html` dosyasını çift tıklayarak açabilirsin.
- veya `start.cmd` dosyasını çalıştır: yerel sunucuyu başlatır ve tarayıcıyı açar.
- Yerel adres: `http://127.0.0.1:8765/`

## Dosyalar

| Dosya | Açıklama |
|---|---|
| `index.html` | Tek sayfa dashboard. `Allinone` ve `Chosen` sekmeleri. |
| `Allinone.xlsx` | Tek sheet: `Allinone`. Tüm satırlar ve yeni metrikler. |
| `allinone.csv` | `;` ayraçlı, virgül ondalıklı, UTF-8 BOM. |
| `allinone.json` | Ham birleşik veri. |
| `start.cmd` | Yerel HTTP sunucusunu başlatır. |

## Özellikler

- **Allinone sekmesi:** tüm strateji × filtre × timeframe satırları.
- **Chosen sekmesi:** satır başındaki `+` ile seçilen stratejiler; seçimler tarayıcıda `localStorage` ile saklanır.
- **CSV indir:** Chosen listesini CSV olarak indirir.
- **Sıralama:** sütun başlığına tıkla; tekrar tıkla yönü çevir.
- **Min/max filtre:** başlığın altındaki filtre satırında metin araması ve sayısal sütunlar için min/max aralığı.
- **Filtreleri temizle / Sıfırla:** tablo filtrelerini veya tüm filtreleri temizler.

## Kapsam

Toplam **3.973 satır**, **6 kaynak**:

| Kaynak | Satır |
|---|---:|
| BigPlan | 563 |
| Book Signal | 1.738 |
| Codex Bulut | 800 |
| Paper ML | 219 |
| Indikator Akademi | 593 |
| V4 Short | 60 |

## Sütunlar

| Sütun | Tanım |
|---|---|
| Kaynak | Verinin geldiği repo. |
| Strateji | Strateji / senaryo adı. |
| Filtre | Uygulanan filtre veya kümülatif filtre aşaması. |
| Timeframe | `5m`, `15m`, `1h`, `4h`, `1d`, `1w`. |
| All Getiri % | İşlem başına ortalama net getiri (tüm dönem). |
| 2026 Getiri % | İşlem başına ortalama net getiri (2026 dilimi). |
| İşlem Sayısı | Toplam işlem sayısı. |
| Karlı/Zararlı İşlem | Karlı işlem sayısı / zararlı işlem sayısı. |
| Karlı İşlem Ort. Süre (saat) | Karlı işlemlerin ortalama elde tutma süresi (saat). |
| Karlı Gün | Günlük net P/L > 0 olan gün sayısı. |
| Karsız Gün | Günlük net P/L < 0 olan gün sayısı. |

## Notlar

- Getiri sütunları **toplam portföy getirisi değil**, işlem başına ortalama net getiridir.
- Farklı repolar farklı evren, dönem, komisyon, slippage ve kaldıraç kullanır.
- V4 Short satırları 12 short formasyonu × 5 kümülatif filtre aşamasını içerir; 1x ve `resolved` işlemler kullanılmıştır.
- Kaynak repolar bu repoda yer almaz; yalnızca birleşik dashboard çıktısı arşivlenir.
- Bu tablo keşif/tarama amaçlıdır; yatırım tavsiyesi değildir.
