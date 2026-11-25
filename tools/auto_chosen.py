#!/usr/bin/env python3
"""Chosen listesini otomatik dolduran kurali index.html'e yazar.

Kural:
  - Kaynak: BigPlan, Book Signal, Indikator Akademi, Paper ML
  - Duzeltilmis All getiri > 0 (Paper ML'de duzeltme yok, ham getiri kullanilir)
  - Islem sayisi < 200.000
  - Karli islem ortalama suresi < 240 saat
  - Duzeltilmis kosusu olan kaynaklarda islem sayisi/sure de *Fixed alanlarindan okunur.

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

SOURCES = ["BigPlan", "Book Signal", "Indikator Akademi", "Paper ML"]
# Bu kaynaklarin duzeltilmis kosusu var; islem sayisi ve sure de *Fixed alanlarindan
# okunur. Paper ML'de lookahead duzeltmesi gerekmedigi icin *Fixed alanlari yoktur.
FIXED_SOURCES = {"BigPlan", "Book Signal", "Indikator Akademi"}
MAX_TRADES = 200_000
MAX_HOLD_H = 240.0
RULE_TEXT = (
    "Kaynak: BigPlan · Book Signal · Indikator Akademi · Paper ML | "
    "Düzeltilmiş All getiri > 0 | İşlem sayısı < 200.000 | "
    "Karlı işlem ort. süre < 240 saat"
)

MARKER_RE = re.compile(r"\n// >>> AUTO_CHOSEN.*?// <<< AUTO_CHOSEN", re.S)
META_RE = re.compile(r"(?m)^const META = .*;")


def row_key(row: dict) -> str:
    return "||".join(str(row.get(k, "")) for k in ("source", "strategy", "filter", "timeframe"))


def passes(row: dict) -> bool:
    source = row.get("source")
    if source not in SOURCES:
        return False
    # Duzeltilmis kosusu olan kaynaklarda (retAllFixed / tradesFixed / winHoldHFixed)
    # yalnizca duzeltilmis metrikler kullanilir; *Fixed null ise (duzeltilmis kosuda
    # islem yok) satir secilmez. Paper ML'de duzeltme olmadigi icin ham metrikler.
    suffix = "Fixed" if source in FIXED_SOURCES else ""
    ret = row.get("retAll" + suffix)
    trades = row.get("trades" + suffix)
    hold = row.get("winHoldH" + suffix)
    if ret is None or trades is None or hold is None:
        return False
    return ret > 0 and trades < MAX_TRADES and hold < MAX_HOLD_H


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
        "maxTrades": MAX_TRADES,
        "maxHoldH": MAX_HOLD_H,
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

    keys: list[str] = []
    by_source: Counter[str] = Counter()
    seen: set[str] = set()
    for row in rows:
        if not passes(row):
            continue
        key = row_key(row)
        if key in seen:
            continue
        seen.add(key)
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
