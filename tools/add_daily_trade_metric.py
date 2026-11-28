#!/usr/bin/env python3
"""Dashboard'a kombinasyon bazında günlük ortalama işlem sütunlarını ekler."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "index.html"
README = ROOT / "README.md"


def replace_once(text: str, old: str, new: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"Beklenen eşleşme sayısı 1, bulunan {count}: {old[:80]!r}")
    return text.replace(old, new)


def main() -> None:
    html = INDEX.read_text(encoding="utf-8")
    marker = 'data-k="tradesPerDay"'
    if marker in html:
        print("Günlük işlem metriği zaten mevcut.")
        return

    html = replace_once(
        html,
        '          <th data-k="sTrades" class="num sg-col">İşlem Sayısı (S)<span class="arrow"></span></th>',
        '          <th data-k="sTrades" class="num sg-col">İşlem Sayısı (S)<span class="arrow"></span></th>\n'
        '          <th data-k="tradesPerDay" class="num">Gün Başına Ort. İşlem<span class="arrow"></span></th>\n'
        '          <th data-k="tradesPerDayFixed" class="num fix-col">Gün Başına Ort. İşlem (Düz.)<span class="arrow"></span></th>\n'
        '          <th data-k="sTradesPerDay" class="num sg-col">Gün Başına Ort. İşlem (S)<span class="arrow"></span></th>',
    )
    html = replace_once(
        html,
        '          <th><div class="range"><input data-tf="tradesMin" placeholder="min" inputmode="numeric"><span>–</span><input data-tf="tradesMax" placeholder="max" inputmode="numeric"></div></th>\n          <th></th>\n          <th></th>',
        '          <th><div class="range"><input data-tf="tradesMin" placeholder="min" inputmode="numeric"><span>–</span><input data-tf="tradesMax" placeholder="max" inputmode="numeric"></div></th>\n'
        '          <th></th>\n          <th></th>\n          <th></th>\n          <th></th>\n          <th></th>',
    )
    html = replace_once(
        html,
        'const FIX_KEYS = ["retAll", "ret2026", "trades", "winRatio", "winHoldH",',
        'const FIX_KEYS = ["retAll", "ret2026", "trades", "tradesPerDay", "winRatio", "winHoldH",',
    )
    html = replace_once(
        html,
        '  row.monthRatio = periodRatio(row.profitMonths, row.lossMonths);\n}\n\nconst rowByKey',
        '  row.monthRatio = periodRatio(row.profitMonths, row.lossMonths);\n}\n\n'
        '// Kombinasyon başına günlük işlem yoğunluğu. Gün kapsamı, backtestte P/L oluşan\n'
        '// kârlı ve karsız günlerin toplamıdır; veri olmayan veya sıfır günlük satırlar boş kalır.\n'
        'for (const row of ROWS) {\n'
        '  row.tradesPerDay = tradesPerDay(row.trades, row.profitDays, row.lossDays);\n'
        '  row.tradesPerDayFixed = tradesPerDay(\n'
        '    row.tradesFixed != null ? row.tradesFixed : row.trades,\n'
        '    row.profitDaysFixed != null ? row.profitDaysFixed : row.profitDays,\n'
        '    row.lossDaysFixed != null ? row.lossDaysFixed : row.lossDays\n'
        '  );\n'
        '  row.sTradesPerDay = tradesPerDay(row.sTrades, row.sProfitDays, row.sLossDays);\n'
        '}\n\n'
        '// Düzeltilmiş görünümü, Singular ve günlük işlem alanları eklendikten sonra yenile.\n'
        'FIXED_ROWS.length = 0;\n'
        'for (const row of ROWS) {\n'
        '  const fixedRow = Object.assign({}, row);\n'
        '  for (const key of FIX_KEYS) {\n'
        '    const value = row[key + "Fixed"];\n'
        '    if (value != null) fixedRow[key] = value;\n'
        '  }\n'
        '  FIXED_ROWS.push(fixedRow);\n'
        '}\n\nconst rowByKey',
    )
    html = replace_once(
        html,
        'function fmtHours(value) {',
        'function tradesPerDay(trades, profitDays, lossDays) {\n'
        '  const count = Number(trades);\n  const profit = Number(profitDays);\n  const loss = Number(lossDays);\n'
        '  const days = profit + loss;\n'
        '  if (!Number.isFinite(count) || !Number.isFinite(profit) || !Number.isFinite(loss) || days <= 0) return null;\n'
        '  return count / days;\n}\n\n'
        'function fmtDecimal(value) {\n'
        '  if (value == null || !Number.isFinite(Number(value))) return \'<span class="muted">—</span>\';\n'
        '  return Number(value).toLocaleString("tr-TR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });\n}\n\n'
        'function fmtHours(value) {',
    )
    html = replace_once(html, 'colspan="34"', 'colspan="37"')
    html = replace_once(
        html,
        '        \'<td class="num sg-col">\' + fmtIntCell(row.sTrades) + "</td>" +',
        '        \'<td class="num sg-col">\' + fmtIntCell(row.sTrades) + "</td>" +\n'
        '        \'<td class="num">\' + fmtDecimal(row.tradesPerDay) + "</td>" +\n'
        '        \'<td class="num fix-col">\' + fmtDecimal(row.tradesPerDayFixed) + "</td>" +\n'
        '        \'<td class="num sg-col">\' + fmtDecimal(row.sTradesPerDay) + "</td>" +',
    )
    html = replace_once(
        html,
        '    ret2026: "2026 Getiri", ret2026Fixed: "2026 Getiri (Düzeltilmiş)", trades: "İşlem",',
        '    ret2026: "2026 Getiri", ret2026Fixed: "2026 Getiri (Düzeltilmiş)", trades: "İşlem",\n'
        '    tradesPerDay: "Gün Başına Ort. İşlem", tradesPerDayFixed: "Gün Başına Ort. İşlem (Düzeltilmiş)", sTradesPerDay: "Gün Başına Ort. İşlem (S)",',
    )
    html = replace_once(
        html,
        '    "İşlem Sayısı", "İşlem Sayısı (Düz.)", "İşlem Sayısı (S)", "Karlı/Zararlı İşlem", "Karlı/Zararlı İşlem (S)",',
        '    "İşlem Sayısı", "İşlem Sayısı (Düz.)", "İşlem Sayısı (S)",\n'
        '    "Gün Başına Ort. İşlem", "Gün Başına Ort. İşlem (Düz.)", "Gün Başına Ort. İşlem (S)",\n'
        '    "Karlı/Zararlı İşlem", "Karlı/Zararlı İşlem (S)",',
    )
    html = replace_once(
        html,
        '      row.sTrades,\n      csvNum(row.winRatio),',
        '      row.sTrades,\n      csvNum(row.tradesPerDay),\n      csvNum(row.tradesPerDayFixed),\n'
        '      csvNum(row.sTradesPerDay),\n      csvNum(row.winRatio),',
    )
    INDEX.write_text(html, encoding="utf-8")

    readme = README.read_text(encoding="utf-8")
    readme = replace_once(
        readme,
        '- **Sıralama:** sütun başlığına tıkla; tekrar tıkla yönü çevir.',
        '- **Sıralama:** sütun başlığına tıkla; tekrar tıkla yönü çevir.\n'
        '- **Gün başına ortalama işlem:** her kombinasyon için `İşlem Sayısı / (Karlı Gün + Karsız Gün)`; ham, düzeltilmiş ve Singular sonuçları ayrı gösterilir.',
    )
    README.write_text(readme, encoding="utf-8")
    print("Dashboard günlük işlem metriğiyle güncellendi.")


if __name__ == "__main__":
    main()
