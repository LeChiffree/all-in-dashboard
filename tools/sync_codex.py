#!/usr/bin/env python3
"""Codex filtre satırlarını güncel payload ile senkronize et.

- `allinone.json` içindeki mevcut Codex satırlarının normal metriklerini
  `filter_normal.json` ile yeniler.
- `filter_normal.json` içinde olup `allinone.json`'da olmayan satırları ekler.
- `index.html` içindeki `const ROWS` / `const META` bloklarını yeniden üretir.
- `allinone.csv` ve `Allinone.xlsx` dosyalarını doğru sütun eşlemesiyle yazar.
- Son olarak `singular/build_summary.py` çalıştırır.
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

DASH = Path(__file__).resolve().parents[1]
PROJECTS = DASH.parent
NORMAL = PROJECTS / "Codex-Bulut-Backtests/Singular-Backtest/results/filter_normal.json"
SINGULAR = PROJECTS / "Codex-Bulut-Backtests/Singular-Backtest/results/filter_singular.json"
ALLINONE = DASH / "allinone.json"
INDEX = DASH / "index.html"
CSV = DASH / "allinone.csv"
XLSX = DASH / "Allinone.xlsx"

# allinone.json satır anahtarları -> dışa aktarım sütunları
EXPORT_KEYS = [
    "source", "strategy", "filter", "timeframe", "retAll", "ret2026",
    "trades", "winRatio", "winHoldH", "profitDays", "lossDays",
]
NORMAL_FIELDS = [
    "winRatio", "winHoldH", "profitDays", "lossDays",
    "profitWeeks", "lossWeeks", "profitMonths", "lossMonths",
]


def pct(value):
    """Kesirli getiriyi yüzdeye çevir; None ise None bırak."""
    if value is None:
        return None
    return round(float(value) * 100.0, 6)


def source_key(key: str, value: dict) -> tuple[str, str, str]:
    return (value.get("scenario_name", ""), key.split("|")[1], value.get("filter_label"))


def row_key(row: dict) -> tuple[str, str, str]:
    return (row.get("strategy", ""), str(row.get("timeframe", "")), str(row.get("filter", "")))


def apply_normal(row: dict, value: dict) -> None:
    row["retAll"] = pct(value.get("retAll"))
    row["ret2026"] = pct(value.get("ret2026"))
    row["trades"] = int(value["trades"]) if value.get("trades") is not None else 0
    for field in NORMAL_FIELDS:
        row[field] = value.get(field)


def make_row(key: str, value: dict) -> dict:
    sid, tf, fid = key.split("|")
    row = {
        "source": "Codex Bulut",
        "strategy": value.get("scenario_name", ""),
        "filter": value.get("filter_label", ""),
        "timeframe": tf,
        "detail": f"Codex-Bulut-Backtests/results/filter_overall_results.csv · {sid} · {fid}",
    }
    apply_normal(row, value)
    return row


def replace_embedded(html: str, rows: list[dict], row_count: int) -> str:
    start = html.find("const ROWS = ")
    end = html.find("\nconst META", start)
    if start < 0 or end < 0:
        raise RuntimeError("index.html içinde ROWS bloğu bulunamadı")
    payload = json.dumps(rows, ensure_ascii=False, separators=(",", ":"))
    html = html[:start] + "const ROWS = " + payload + ";" + html[end:]

    meta_start = html.find("const META = ")
    meta_end = html.find(";", meta_start)
    if meta_start < 0 or meta_end < 0:
        raise RuntimeError("index.html içinde META bloğu bulunamadı")
    sources = []
    for row in rows:
        if row["source"] not in sources:
            sources.append(row["source"])
    meta = {
        "generated": datetime.now().strftime("%d.%m.%Y %H:%M"),
        "row_count": row_count,
        "sources": sources,
    }
    html = html[:meta_start] + "const META = " + json.dumps(meta, ensure_ascii=False) + ";" + html[meta_end + 1:]
    return html


def main() -> None:
    normal = json.load(open(NORMAL, encoding="utf-8"))
    payload = json.load(open(ALLINONE, encoding="utf-8"))
    rows = payload["rows"]

    current = {}
    for row in rows:
        if row.get("source") == "Codex Bulut":
            current[row_key(row)] = row

    updated = 0
    for key, value in normal.items():
        row = current.get(source_key(key, value))
        if row is not None:
            apply_normal(row, value)
            updated += 1

    added = 0
    for key, value in normal.items():
        if source_key(key, value) in current:
            continue
        row = make_row(key, value)
        rows.append(row)
        current[row_key(row)] = row
        added += 1

    payload["generated"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    payload["row_count"] = len(rows)
    with open(ALLINONE, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)

    frame = pd.DataFrame(rows).reindex(columns=EXPORT_KEYS)
    frame.columns = payload["columns"]
    frame.to_csv(CSV, sep=";", index=False, encoding="utf-8-sig", decimal=",")
    with pd.ExcelWriter(XLSX, engine="openpyxl") as writer:
        frame.to_excel(writer, sheet_name="Allinone", index=False)

    html = INDEX.read_text(encoding="utf-8")
    html = replace_embedded(html, rows, len(rows))
    INDEX.write_text(html, encoding="utf-8")

    print(f"Codex güncellenen satır: {updated:,}")
    print(f"Codex eklenen satır:     {added:,}")
    print(f"Toplam satır:            {len(rows):,}")
    print("allinone.json / allinone.csv / Allinone.xlsx / index.html yazıldı")

    subprocess.run([sys.executable, "singular/build_summary.py"], cwd=DASH, check=True)
    subprocess.run([sys.executable, "tools/auto_chosen.py"], cwd=DASH, check=True)


if __name__ == "__main__":
    main()
