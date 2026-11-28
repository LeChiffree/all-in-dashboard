#!/usr/bin/env python3
"""Chosen listesini otomatik dolduran kurali index.html'e yazar.

Kural:
  - Codex Bulut haric, yalnizca gercek duzeltilmis sonuclar
  - Duzeltilmis All getiri > 0
  - Karli islem ortalama suresi <= 230 saat
  - Hafta K/Z >= 1.5 ve gun K/Z >= 1
  - Her kaynak + strateji + timeframe icin en yuksek duzeltilmis All getirili tek filtre

Secilen satirlarin anahtarlari index.html icine `const AUTO_CHOSEN` olarak
gomulur. Dashboard ilk acilista (localStorage'da secim yoksa) bu listeyi
otomatik isaretler; "Auto sec" butonu kurali yeniden uygular.

Kullanim:
    python tools/auto_chosen.py            # index.html'i guncelle
    python tools/auto_chosen.py --dry-run  # sadece ozet yazdir
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from collections import Counter
from pathlib import Path

DASH = Path(__file__).resolve().parents[1]
INDEX = DASH / "index.html"

SOURCES = ["BigPlan", "Book Signal", "Indikator Akademi", "Paper ML", "V4 Short"]
MAX_HOLD_H = 230.0
MIN_WEEK_RATIO = 1.5
MIN_DAY_RATIO = 1.0
RULE_TEXT = (
    "Codex Bulut hariç | Düzeltilmiş All getiri > 0 | "
    "Karlı işlem ort. süre ≤ 230 saat | Hafta K/Z ≥ 1,5 | Gün K/Z ≥ 1 | "
    "Her strateji + timeframe için en iyi tek filtre"
)

MARKER_RE = re.compile(r"\n// >>> AUTO_CHOSEN.*?// <<< AUTO_CHOSEN", re.S)
META_RE = re.compile(r"(?m)^const META = .*;")


def row_key(row: dict) -> str:
    return "||".join(str(row.get(k, "")) for k in ("source", "strategy", "filter", "timeframe"))


def passes(row: dict) -> bool:
    if row.get("source") not in SOURCES:
        return False
    values = [row.get(k) for k in ("retAllFixed", "winHoldHFixed", "weekRatioFixed", "dayRatioFixed")]
    if any(v is None for v in values):
        return False
    ret, hold, week_ratio, day_ratio = values
    return ret > 0 and hold <= MAX_HOLD_H and week_ratio >= MIN_WEEK_RATIO and day_ratio >= MIN_DAY_RATIO


def rank(row: dict) -> tuple:
    """En iyi filtre: All getiri, hafta K/Z, gun K/Z; sonra daha kisa sure."""
    return (
        row["retAllFixed"],
        row["weekRatioFixed"],
        row["dayRatioFixed"],
        -row["winHoldHFixed"],
        row.get("tradesFixed") or 0,
    )


def load_rows(html: str) -> list[dict]:
    start = html.index("const ROWS = ") + len("const ROWS = ")
    end = html.index("\nconst META", start)
    return json.loads(html[start:end].rstrip().rstrip(";"))


def build_block(keys: list[str], by_source: dict[str, int], generated: str, eol: str) -> str:
    meta = {
        "generated": generated,
        "rule": RULE_TEXT,
        "count": len(keys),
        "bySource": by_source,
        "sources": SOURCES,
        "maxHoldH": MAX_HOLD_H,
        "minWeekRatio": MIN_WEEK_RATIO,
        "minDayRatio": MIN_DAY_RATIO,
        "groupBy": ["source", "strategy", "timeframe"],
    }
    lines = [
        "",
        "// >>> AUTO_CHOSEN (tools/auto_chosen.py tarafindan uretilir; elle duzenlemeyin)",
        "const AUTO_CHOSEN = " + json.dumps(keys, ensure_ascii=False, separators=(",", ":")) + ";",
        "const AUTO_CHOSEN_META = " + json.dumps(meta, ensure_ascii=False, separators=(",", ":")) + ";",
        "// <<< AUTO_CHOSEN",
    ]
    return eol.join(lines) + eol


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="index.html'i yazma, sadece ozet goster")
    args = parser.parse_args()

    with INDEX.open("r", encoding="utf-8", newline="") as fh:
        html = fh.read()
    eol = "\r\n" if "\r\n" in html else "\n"
    rows = load_rows(html)

    best: dict[tuple[str, str, str], dict] = {}
    for row in rows:
        if not passes(row):
            continue
        group = (row["source"], row["strategy"], row["timeframe"])
        if group not in best or rank(row) > rank(best[group]):
            best[group] = row

    keys: list[str] = []
    by_source: Counter[str] = Counter()
    for row in best.values():
        key = row_key(row)
        keys.append(key)
        by_source[row["source"]] += 1

    keys.sort()
    generated = dt.datetime.now().strftime("%d.%m.%Y %H:%M")

    print(f"{len(rows):,} satir tarandi, {len(keys):,} satir secildi".replace(",", "."))
    for source in SOURCES:
        print(f"  {source:<20} {by_source.get(source, 0):>6,}".replace(",", "."))

    if args.dry_run:
        return 0

    block = build_block(keys, {s: by_source.get(s, 0) for s in SOURCES}, generated, eol)
    if MARKER_RE.search(html):
        html = MARKER_RE.sub(lambda _m: block, html, count=1)
    else:
        meta_match = META_RE.search(html)
        if not meta_match:
            raise SystemExit("const META satiri bulunamadi; AUTO_CHOSEN blogu eklenemedi.")
        html = html[: meta_match.end()] + block + html[meta_match.end():]

    with INDEX.open("w", encoding="utf-8", newline="") as fh:
        fh.write(html)
    print(f"index.html guncellendi: AUTO_CHOSEN ({generated})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
