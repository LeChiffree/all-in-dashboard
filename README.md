# All-in Dashboard

Birden fazla trade backtest reposunun sonuçlarını tek tabloda birleştiren dashboard.

## Açma

- `index.html` dosyasını çift tıklayarak açabilirsin.
- veya `start.cmd` dosyasını çalıştır: yerel sunucuyu başlatır ve tarayıcıyı açar.
- Yerel adres: `http://127.0.0.1:8765/`

## Dosyalar

| Dosya | Açıklama |
|---|---|
| `index.html` | Tek sayfa dashboard. `Allinone` ve `Chosen` sekmeleri; Allinone tablosunda tekil (S) sütunları. |
| `singular/summary.js` | Altı reponun tekil sonuçları; Allinone tablosundaki (S) sütunlarını doldurur. |
| `singular/build_summary.py` | Repo payload'larını Allinone satırlarıyla eşleştirip `summary.js` üretir. |
| `Allinone.xlsx` | Tek sheet: `Allinone`. Tüm satırlar ve metrikler. |
| `allinone.csv` | `;` ayraçlı, virgül ondalıklı, UTF-8 BOM. |
| `allinone.json` | Ham birleşik veri. |
| `start.cmd` | Yerel HTTP sunucusunu başlatır. |
| `tools/auto_chosen.py` | Chosen otomatik seçim kuralını uygular ve `index.html` içindeki `AUTO_CHOSEN` bloğunu yeniler. |

## Özellikler

- **Menülü uygulama (`menu.html`):** kaynak → strateji → timeframe adımlarıyla ilgili filtreleri listeler ve düzeltilmiş All getiriye göre sıralar.
- **Allinone sekmesi:** tüm strateji × filtre × timeframe satırları.
- **Singular (S) sütunları:** her metrik sütununun hemen sağında, aynı coinde tek
  açık işlem kuralının sonucu; normal ve tekil değer yan yana karşılaştırılır.
- **Chosen sekmesi:** satır başındaki `+` ile seçilen stratejiler; seçimler tarayıcıda `localStorage` ile saklanır.
  İlk açılışta aşağıdaki kurala uyan satırlar **otomatik seçili** gelir; `Auto seç` butonu kuralı yeniden uygular.
- **CSV indir:** Chosen listesini CSV olarak indirir.
- **Sıralama:** sütun başlığına tıkla; tekrar tıkla yönü çevir.
- **Min/max filtre:** başlığın altındaki filtre satırında metin araması ve sayısal sütunlar için min/max aralığı.
- **Filtreleri temizle / Sıfırla:** tablo filtrelerini veya tüm filtreleri temizler.

## Kapsam

Toplam **65.220 satır**, **6 kaynak**, **309 filtre**:

| Kaynak | Satır |
|---|---:|
| BigPlan | 563 |
| Book Signal | 1.738 |
| Codex Bulut | 44.770 |
| Paper ML | 219 |
| Indikator Akademi | 17.870 |
| V4 Short | 60 |

## Sütunlar

| Sütun | Tanım |
|---|---|
| Kaynak | Verinin geldiği repo. |
| Strateji | Strateji / senaryo adı. |
| Filtre | Uygulanan filtre veya kümülatif filtre aşaması. |
| Timeframe | `5m`, `15m`, `1h`, `4h`, `1d`, `1w`. |
| All Getiri % | İşlem başına ortalama net getiri (tüm dönem). |
| All Getiri % (Düzeltilmiş) | Lookahead düzeltmeleri sonrası aynı metrik (bkz. `_raporlar/all-in-dashboard-lookahead-denetimi-2026-11-24/RAPOR.md`). |
| 2026 Getiri % | İşlem başına ortalama net getiri (2026 dilimi). |
| 2026 Getiri % (Düzeltilmiş) | Lookahead düzeltmeleri sonrası 2026 metriği. |
| İşlem Sayısı | Toplam işlem sayısı. |
| İşlem Sayısı (Düz.) | Düzeltilmiş koşunun toplam işlem sayısı (Paper ML'de boştur). |
| Karlı/Zararlı İşlem | Karlı işlem sayısı / zararlı işlem sayısı. |
| Karlı İşlem Ort. Süre (saat) | Karlı işlemlerin ortalama elde tutma süresi (saat). |
| Karlı İşlem Ort. Süre (Düz.) | Düzeltilmiş koşuda karlı işlemlerin ortalama süresi (saat). |
| Karlı Gün | Günlük net P/L > 0 olan gün sayısı. |
| Karsız Gün | Günlük net P/L < 0 olan gün sayısı. |
| Karlı Hafta | Pazartesi başlangıçlı haftanın toplam net P/L > 0 olan hafta sayısı. |
| Karsız Hafta | Haftalık toplam net P/L < 0 olan hafta sayısı. |
| Karlı Ay | Takvim ayının toplam net P/L > 0 olan ay sayısı. |
| Karsız Ay | Aylık toplam net P/L < 0 olan ay sayısı. |

## Düzeltilmiş değerler modu

Üst çubuktaki **Düzeltilmiş değerler** anahtarı işaretlendiğinde tablo, sıralama,
filtreler, istatistikler ve CSV indirmesi aynı satırların `*Fixed` alanlarını
kullanır. Kapsam: All Getiri, 2026 Getiri, İşlem Sayısı, Karlı/Zararlı İşlem,
Karlı İşlem Ort. Süre, Karlı/Karsız Gün-Hafta-Ay sayıları ve bunların oranları
(`dayRatio`, `weekRatio`, `monthRatio` → `*Fixed`). Book Signal'de
`winRatioFixed`, yeni koşunun `win_rate` değerinden `wr / (1 - wr)` ile türetilir.
Veri yenilendikten sonra `python tools/apply_fixed.py --write` alanları ve
`index.html` içindeki satırları birlikte günceller.

## Book Signal düzeltmesi (25.11.2026)

Book Signal kaynağında iki hata düzeltildi ve 525 sembol × 191 spec ile yeniden koşuldu:

| Hata | Düzeltme |
|---|---|
| `stop_mode = signal_low` short tarafta girişin altına stop koyuyordu; trade sessizce reddediliyordu | Stop yön simetrisi (`signal_low` → short'ta `signal_high`) |
| Spec tekilleştirme anahtarı var olmayan `stop` / `time` alanlarını kullanıyordu; 214 spec 120'ye çöküyordu | Anahtar `stop_atr`, `time_bars`, `stop_mode`, `exit_long/short`, `atr_n` üzerinden |

Sonuç (1.738 ortak satır): 431 satır değişti, ortalama **+0,056 puan**, pozitif satır **366 → 420**, toplam işlem **+%27,8**.
`stop_mode = atr` olan 1.168 satır birebir aynı kaldı; etki yalnız short stopu kullanan 570 satırda.

Notlar:

- Düzeltme öncesi/sonrası ayrıntı: `_raporlar/all-in-dashboard-lookahead-denetimi-2026-11-24/BOOK-SIGNAL-DENETIMI.md`.
- 191 spec'in 5'i yapısal olarak ölü (`ema(close,50) > ema(close,50)` totolojisi ve hiç tetiklenmeyen bir Heikin-Ashi deseni).
- Dedup düzeltmesiyle ortaya çıkan **70 spec / 1.050 satır** dashboard'a eklenmedi; bu satırların düzeltme öncesi değeri yok (eski koşuda hiç çalışmamışlardı). Tamamı `book_signal_fixed.csv` içinde.

## Chosen otomatik seçimi (25.11.2026)

`Chosen` listesi, düzeltilmiş backtest sonuçlarına göre otomatik doldurulur. Kural:

- Kaynak: **BigPlan, Book Signal, Indikator Akademi, Paper ML**
- **Düzeltilmiş** All getiri > 0 (Paper ML'de lookahead düzeltmesi olmadığı için ham getiri kullanılır)
- İşlem sayısı < **200.000**
- Karlı işlem ortalama süresi < **240 saat**

| Kaynak | Seçilen | Kaynak satır |
|---|---:|---:|
| BigPlan | 342 | 563 |
| Book Signal | 224 | 1.738 |
| Indikator Akademi | 4.120 | 17.870 |
| Paper ML | 214 | 219 |
| **Toplam** | **4.900** | 20.390 |

Notlar:

- BigPlan / Book Signal / Indikator Akademi satırlarında işlem sayısı ve süre de
  düzeltilmiş koşudan (`tradesFixed`, `winHoldHFixed`) okunur; bu yüzden ham
  `İşlem Sayısı` sütunundan farklı olabilir. Karşılaştırma için tabloya
  `İşlem Sayısı (Düz.)` ve `Karlı İşlem Ort. Süre (Düz.)` sütunları eklendi.
- Düzeltilmiş koşuda hiç işlem üretmeyen satırlarda `retAllFixed` boştur; bu satırlar seçilmez.
- Liste `index.html` içindeki `AUTO_CHOSEN` bloğunda durur. Veri yenilendikten sonra:

```bash
python tools/auto_chosen.py
```

- Seçim `allinone_chosen_v2` anahtarıyla `localStorage`'da saklanır. Tarayıcıda kayıtlı
  bir seçim varsa otomatik liste uygulanmaz; `Auto seç` butonuyla uygulanır.

## Filtre kapsamı

- **BigPlan:** 184 filtre varyantı.
- **Book Signal:** baseline + 14 filtre.
- **Codex Bulut:** baseline + 55 filtre. Filtre satırları all-period ve 2026 getirisi, işlem sayısı, karlı/zararlı oranı, karlı işlem süresi ve gün/hafta/ay sayılarını içerir.
- **Indikator Akademi:** 600 senaryo × 31 filtre tam olarak eklenir. `Filtresiz` yalnızca bu 31 filtrenin ilk satırıdır.
- **Paper ML:** senaryo içindeki filtre ve threshold varyantları.
- **V4 Short:** 12 short formasyonu × 5 kümülatif aşama (`1 → 12 → 123 → 1234 → 12345`).

## Notlar

- Getiri sütunları **toplam portföy getirisi değil**, işlem başına ortalama net getiridir.
- Gün/hafta/ay sayıları tüm coinlerin aynı dönemdeki net P/L'si toplandıktan sonra
  portföy düzeyinde hesaplanır; coin başına kâr/zarar günleri ayrı ayrı sayılıp
  toplanmaz.
- Farklı repolar farklı evren, dönem, komisyon, slippage ve kaldıraç kullanır.
- V4 Short satırları 1x ve `resolved` işlemler kullanır.
- Kaynak repolar bu repoda yer almaz; yalnızca birleşik dashboard çıktısı arşivlenir.
- Bu tablo keşif/tarama amaçlıdır; yatırım tavsiyesi değildir.

## Singular sütunlarını yenileme

`singular/summary.js`, altı repodaki `singular_results.json` dosyalarından ve Allinone satır anahtarlarıyla eşleştirilerek üretilir:

```bash
python singular/build_summary.py
```

Varsayılan olarak komşu repo klasörlerini okur (`../Codex-Bulut-Backtests`, ...).
Farklı konumlar için `--codex=... --book=...` gibi argümanlar kullanılabilir.
Codex için `filter_singular.json` ve `filter_normal.json` birlikte okunur; Codex
normal sütunları da bu veri setiyle yenilenir (kaynak allinone'daki şişmiş işlem
sayıları düzeltilir). `summary.js` yoksa (S) sütunları boş kalır; normal tablo
etkilenmez.

Codex filtre payload'ı değiştiğinde (yeni filtre satırları dahil) tam senkron için:

```bash
python tools/sync_codex.py
```

Bu komut `allinone.json` içindeki Codex satırlarını `filter_normal.json` ile
günceller, eksik Codex satırlarını ekler, `allinone.csv` / `Allinone.xlsx` /
`index.html` çıktılarını yeniden üretir, `singular/build_summary.py` ve
`tools/auto_chosen.py` betiklerini çalıştırır.

