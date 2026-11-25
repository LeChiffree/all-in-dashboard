#!/usr/bin/env python3
"""Düzeltilmiş backtest sonuçlarını all-in-dashboard'a ekler.

- BigPlan: out/pro_bundle_fixed.json (+ pro_bundle_fixed_strict.json)
- Indikator Akademi: tools/dash/data/agg/*.bin (yeni koşu)
- Book Signal: filter_layer/dashboard_data.json (yeni koşu)

Mevcut alanlar "öncesi" olarak korunur; yanlarına *Fixed alanları eklenir.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from pathlib import Path

import numpy as np

DASH = Path(r"C:\Users\GIGABAYT\Projects\all-in-dashboard")
IA = Path(r"C:\Users\GIGABAYT\Projects\indikator-akademi")
BP = Path(r"C:\Users\GIGABAYT\Projects\bigplan-backtest-lab")

BP_FIXED = Path(r"D:\BigPlan\out\pro_bundle_fixed.json")
BP_STRICT = Path(r"D:\BigPlan\out\pro_bundle_fixed_strict.json")
IA_AGG = IA / "tools" / "dash" / "data" / "agg"
IA_SCEN = IA / "tools" / "dash" / "data" / "scenarios.json"
BS_DATA = Path(r"D:\Paper_ML_BSH\analysis\book_signal_review\backtest\filter_layer\dashboard_data.json")
BS_STATS_FILE = BS_DATA.parent / "daily_stats.json"
BS_STATS: dict[str, list] = {}

GRID_START = dt.date(2022, 8, 1)
DAY0 = dt.date(2022, 8, 1)
D26 = (dt.date(2026, 1, 1) - DAY0).days

ND, NH, NB, F = 1500, 168, 9, 31
HDR = 14
KEYS = ["n", "wins", "sumR", "sumR2", "grossW", "grossL", "barsSum", "best", "worst",
        "winBars", "longN", "longSumR", "shortN", "shortSumR"]


def fbytes(nS: int) -> int:
    raw = HDR * 8 + ND * 12 + NH * 12 + NB * 12 + nS * 16
    return (raw + 7) // 8 * 8


def parse_block(buf: bytes, off: int, nS: int) -> dict:
    d = {}
    v = np.frombuffer(buf, dtype="<f8", count=HDR, offset=off)
    for k, x in zip(KEYS, v):
        d[k] = float(x)
    off += HDR * 8

    def take(dtype, n):
        nonlocal off
        a = np.frombuffer(buf, dtype=dtype, count=n, offset=off)
        off += n * np.dtype(dtype).itemsize
        return a

    d["dPos"] = take("<f4", ND)
    d["dNeg"] = take("<f4", ND)
    d["dCnt"] = take("<u4", ND)
    d["hPos"] = take("<f4", NH)
    d["hNeg"] = take("<f4", NH)
    d["hCnt"] = take("<u4", NH)
    d["uPos"] = take("<f4", NB)
    d["uNeg"] = take("<f4", NB)
    d["uCnt"] = take("<u4", NB)
    return d


def periods_from_daily(p, ng, cnt):
    """Günlük pozitif/negatif seriden gün/hafta/ay sayıları."""
    p = np.asarray(p, dtype=float)
    ng = np.asarray(ng, dtype=float)
    cnt = np.asarray(cnt, dtype=float)
    active = cnt > 0
    net = p - ng
    prof_d = int(((net > 0) & active).sum())
    loss_d = int(((net < 0) & active).sum())

    weeks: dict[str, list[float]] = {}
    months: dict[tuple[int, int], list[float]] = {}
    for i in np.nonzero(active)[0]:
        day = GRID_START + dt.timedelta(days=int(i))
        wk = (day - dt.timedelta(days=day.weekday())).isoformat()
        w = weeks.setdefault(wk, [0.0, 0.0])
        w[0] += float(p[i]); w[1] += float(ng[i])
        mo = (day.year, day.month)
        z = months.setdefault(mo, [0.0, 0.0])
        z[0] += float(p[i]); z[1] += float(ng[i])
    prof_w = sum(1 for a, b in weeks.values() if a - b > 0)
    loss_w = sum(1 for a, b in weeks.values() if a - b < 0)
    prof_m = sum(1 for a, b in months.values() if a - b > 0)
    loss_m = sum(1 for a, b in months.values() if a - b < 0)
    return prof_d, loss_d, prof_w, loss_w, prof_m, loss_m


def ia_metrics(d: dict) -> dict:
    n = float(d["n"])
    wins = float(d["wins"])
    if n <= 0:
        return {"retAllFixed": None, "ret2026Fixed": None, "tradesFixed": 0,
                "winRatioFixed": None, "winHoldHFixed": None,
                "profitDaysFixed": None, "lossDaysFixed": None,
                "profitWeeksFixed": None, "lossWeeksFixed": None,
                "profitMonthsFixed": None, "lossMonthsFixed": None}
    c = d["dCnt"]
    p = d["dPos"].astype(float)
    ng = d["dNeg"].astype(float)
    n26 = float(c[D26:].sum())
    ret26 = float((p[D26:].sum() - ng[D26:].sum()) / n26 * 100) if n26 > 0 else 0.0
    pd_, ld, pw, lw, pm, lm = periods_from_daily(p, ng, c)
    losses = n - wins
    return {
        "retAllFixed": round(float(d["sumR"] / n * 100), 4),
        "ret2026Fixed": round(ret26, 4),
        "tradesFixed": int(n),
        "winRatioFixed": round(wins / losses, 4) if losses > 0 else None,
        "winHoldHFixed": round(float(d["winBars"] / wins / 60.0), 2) if wins > 0 else None,
        "profitDaysFixed": pd_, "lossDaysFixed": ld,
        "profitWeeksFixed": pw, "lossWeeksFixed": lw,
        "profitMonthsFixed": pm, "lossMonthsFixed": lm,
    }


def bp_metrics(st: dict) -> dict:
    agg = st.get("agg") or {}
    n = int(agg.get("n") or 0)
    p = agg.get("dayPosC") or []
    ng = agg.get("dayNegC") or []
    pd_, ld, pw, lw, pm, lm = periods_from_daily(p, ng, [1 if (a or b) else 0 for a, b in zip(p, ng)])
    return {
        "retAllFixed": round(float(st.get("totAvg") or 0) * 100, 4),
        "ret2026Fixed": round(float(st.get("y26Avg") or 0) * 100, 4),
        "tradesFixed": n,
        "winRatioFixed": st.get("winRatio"),
        "winHoldHFixed": st.get("winDurH"),
        "profitDaysFixed": pd_, "lossDaysFixed": ld,
        "profitWeeksFixed": pw, "lossWeeksFixed": lw,
        "profitMonthsFixed": pm, "lossMonthsFixed": lm,
    }


def bs_metrics(b: dict) -> dict:
    """Book Signal filter_layer result → dashboard *Fixed alanları."""
    stats = BS_STATS.get(f"{b.get('idx')}|{b.get('filter_id')}")
    if stats:
        prof_d, loss_d, pw, lw, pm, lm = stats
    else:
        # Yedek: gunluk seri yalnızca pozitif çiftler için tutuluyor.
        daily = b.get("daily") or []
        prof_d = sum(1 for x in daily if x[4] > 0)
        loss_d = sum(1 for x in daily if x[4] < 0)
        weeks: dict[str, float] = {}
        months: dict[tuple[int, int], float] = {}
        for day, _cnt, _pos, _neg, net in daily:
            if not net:
                continue
            d = dt.datetime.utcfromtimestamp(day * 86400).date()
            wk = (d - dt.timedelta(days=d.weekday())).isoformat()
            weeks[wk] = weeks.get(wk, 0.0) + net
            mo = (d.year, d.month)
            months[mo] = months.get(mo, 0.0) + net
        pw = sum(1 for v in weeks.values() if v > 0)
        lw = sum(1 for v in weeks.values() if v < 0)
        pm = sum(1 for v in months.values() if v > 0)
        lm = sum(1 for v in months.values() if v < 0)
    wins = int(b.get("wins_total") or 0)
    losses = int(b.get("losses_total") or 0)
    return {
        "retAllFixed": round(float(b.get("avg_net") or 0) * 100, 4),
        "ret2026Fixed": None if b.get("ret_2026") is None else round(float(b["ret_2026"]) * 100, 4),
        "tradesFixed": int(b.get("n") or 0),
        "winRatioFixed": round(wins / losses, 4) if losses > 0 else (float(wins) if wins else None),
        "winHoldHFixed": b.get("win_hold_h"),
        "profitDaysFixed": prof_d, "lossDaysFixed": loss_d,
        "profitWeeksFixed": pw, "lossWeeksFixed": lw,
        "profitMonthsFixed": pm, "lossMonthsFixed": lm,
    }


def add_ratios(row: dict, suffix: str) -> None:
    pairs = [("profitDays", "lossDays", "dayRatio"),
             ("profitWeeks", "lossWeeks", "weekRatio"),
             ("profitMonths", "lossMonths", "monthRatio")]
    for pf, lf, rf in pairs:
        prof = row.get(pf + suffix)
        loss = row.get(lf + suffix)
        row[rf + suffix] = round(float(prof) / float(loss), 4) if (prof is not None and loss) else None


CSV_FIELDS = [
    ("Kaynak", "source"), ("Strateji", "strategy"), ("Filtre", "filter"), ("Timeframe", "timeframe"),
    ("All Getiri %", "retAll"), ("All Getiri % (Düzeltilmiş)", "retAllFixed"),
    ("2026 Getiri %", "ret2026"), ("2026 Getiri % (Düzeltilmiş)", "ret2026Fixed"),
    ("İşlem Sayısı", "trades"), ("Karlı/Zararlı İşlem", "winRatio"),
    ("Karlı İşlem Ort. Süre (saat)", "winHoldH"),
    ("Karlı Gün", "profitDays"), ("Karsız Gün", "lossDays"), ("Gün Oranı", "dayRatio"),
    ("Karlı Hafta", "profitWeeks"), ("Karsız Hafta", "lossWeeks"), ("Hafta Oranı", "weekRatio"),
    ("Karlı Ay", "profitMonths"), ("Karsız Ay", "lossMonths"), ("Ay Oranı", "monthRatio"),
]

NUMERIC_FIELDS = {
    "retAll", "retAllFixed", "ret2026", "ret2026Fixed", "winRatio", "winHoldH",
    "profitDays", "lossDays", "profitWeeks", "lossWeeks", "profitMonths", "lossMonths",
    "dayRatio", "weekRatio", "monthRatio",
}
INTEGER_FIELDS = {
    "trades", "profitDays", "lossDays", "profitWeeks", "lossWeeks", "profitMonths", "lossMonths",
}


def write_tables(rows: list[dict]) -> None:
    import pandas as pd

    frame = pd.DataFrame([{label: row.get(field) for label, field in CSV_FIELDS} for row in rows],
                         columns=[label for label, _ in CSV_FIELDS])
    for label, field in CSV_FIELDS:
        if field in NUMERIC_FIELDS:
            frame[label] = pd.to_numeric(frame[label], errors="coerce")
            if field in INTEGER_FIELDS:
                frame[label] = frame[label].astype("Int64")
    frame.to_csv(DASH / "allinone.csv", sep=";", index=False, encoding="utf-8-sig", decimal=",")
    with pd.ExcelWriter(DASH / "Allinone.xlsx", engine="openpyxl") as writer:
        frame.to_excel(writer, sheet_name="Allinone", index=False)
    print("yazıldı: allinone.csv / Allinone.xlsx")


def patch_html(rows: list[dict]) -> None:
    html = (DASH / "index.html").read_text(encoding="utf-8")

    def rep(old: str, new: str) -> None:
        nonlocal html
        if html.count(old) != 1:
            raise SystemExit(f"HTML eşleşmesi {html.count(old)} kez: {old[:70]!r}")
        html = html.replace(old, new)

    if 'data-k="retAllFixed"' not in html:
        rep("  th.sg-col { color: #9db8e8; border-left: 1px solid rgba(90,140,255,.22); }",
            "  th.fix-col { color: #7ee0b8; border-left: 1px solid rgba(126,224,184,.25); }\n"
            "  td.fix-col { background: rgba(126,224,184,.05); border-left: 1px solid rgba(126,224,184,.15); }\n"
            "  tbody tr:hover td.fix-col { background: rgba(126,224,184,.10); }\n"
            "  th.sg-col { color: #9db8e8; border-left: 1px solid rgba(90,140,255,.22); }")

        rep('<th data-k="retAll" class="num">All Getiri %<span class="arrow"></span></th>',
            '<th data-k="retAll" class="num">All Getiri %<span class="arrow"></span></th>\n'
            '          <th data-k="retAllFixed" class="num fix-col">All Getiri % (Düzeltilmiş)<span class="arrow"></span></th>')
        rep('<th data-k="ret2026" class="num">2026 Getiri %<span class="arrow"></span></th>',
            '<th data-k="ret2026" class="num">2026 Getiri %<span class="arrow"></span></th>\n'
            '          <th data-k="ret2026Fixed" class="num fix-col">2026 Getiri % (Düzeltilmiş)<span class="arrow"></span></th>')

        rep('<th><div class="range"><input data-tf="retAllMin" placeholder="min" inputmode="decimal"><span>–</span><input data-tf="retAllMax" placeholder="max" inputmode="decimal"></div></th>',
            '<th><div class="range"><input data-tf="retAllMin" placeholder="min" inputmode="decimal"><span>–</span><input data-tf="retAllMax" placeholder="max" inputmode="decimal"></div></th>\n          <th></th>')
        rep('<th><div class="range"><input data-tf="ret2026Min" placeholder="min" inputmode="decimal"><span>–</span><input data-tf="ret2026Max" placeholder="max" inputmode="decimal"></div></th>',
            '<th><div class="range"><input data-tf="ret2026Min" placeholder="min" inputmode="decimal"><span>–</span><input data-tf="ret2026Max" placeholder="max" inputmode="decimal"></div></th>\n          <th></th>')

        rep("'<td class=\"num\">' + fmtPct(row.retAll) + \"</td>\" +",
            "'<td class=\"num\">' + fmtPct(row.retAll) + \"</td>\" +\n"
            "        '<td class=\"num fix-col\">' + fmtPct(row.retAllFixed) + \"</td>\" +")
        rep("'<td class=\"num\">' + fmtPct(row.ret2026) + \"</td>\" +",
            "'<td class=\"num\">' + fmtPct(row.ret2026) + \"</td>\" +\n"
            "        '<td class=\"num fix-col\">' + fmtPct(row.ret2026Fixed) + \"</td>\" +")

        rep('colspan="27"', 'colspan="33"')

        rep('retAll: "All Getiri", ret2026: "2026 Getiri", trades: "İşlem",',
            'retAll: "All Getiri", retAllFixed: "All Getiri (Düzeltilmiş)",\n'
            '    ret2026: "2026 Getiri", ret2026Fixed: "2026 Getiri (Düzeltilmiş)", trades: "İşlem",')

        rep('"All Getiri %", "All Getiri % (S)", "2026 Getiri %", "2026 Getiri % (S)",',
            '"All Getiri %", "All Getiri % (Düzeltilmiş)", "All Getiri % (S)",\n'
            '    "2026 Getiri %", "2026 Getiri % (Düzeltilmiş)", "2026 Getiri % (S)",')
        rep('      csvNum(row.retAll),\n      csvNum(row.sRetAll),',
            '      csvNum(row.retAll),\n      csvNum(row.retAllFixed),\n      csvNum(row.sRetAll),')
        rep('      csvNum(row.ret2026),\n      csvNum(row.sRet2026),',
            '      csvNum(row.ret2026),\n      csvNum(row.ret2026Fixed),\n      csvNum(row.sRet2026),')

    start = html.find("const ROWS = ")
    end = html.find("\nconst META", start)
    if start < 0 or end < 0:
        raise SystemExit("ROWS/META bloğu bulunamadı")
    payload = json.dumps(rows, ensure_ascii=False, separators=(",", ":"))
    html = html[:start] + "const ROWS = " + payload + ";" + html[end:]

    (DASH / "index.html").write_text(html, encoding="utf-8")
    print("yazıldı: index.html")


def write_bigplan_table(rows: list[dict]) -> None:
    import pandas as pd

    bp = [r for r in rows if r.get("source") == "BigPlan" and r.get("retAllFixed") is not None]
    frame = pd.DataFrame([{
        "Anahtar": str(r.get("detail", "")).split(" · ")[-1],
        "Strateji": r.get("strategy"),
        "Timeframe": r.get("timeframe"),
        "Filtre": r.get("filter"),
        "Getiri Öncesi %": r.get("retAll"),
        "Getiri Düzeltilmiş %": r.get("retAllFixed"),
        "Getiri Sıkı Stop %": r.get("retAllFixedStrict"),
        "2026 Öncesi %": r.get("ret2026"),
        "2026 Düzeltilmiş %": r.get("ret2026Fixed"),
        "2026 Sıkı Stop %": r.get("ret2026FixedStrict"),
        "İşlem Öncesi": r.get("trades"),
        "İşlem Düzeltilmiş": r.get("tradesFixed"),
        "İşlem Sıkı Stop": r.get("tradesFixedStrict"),
    } for r in bp])
    frame.to_csv(DASH / "bigplan_fixed.csv", sep=";", index=False, encoding="utf-8-sig", decimal=",")
    print(f"yazıldı: bigplan_fixed.csv ({len(bp)} satır)")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true", help="allinone.json/csv/xlsx/html dosyalarını yaz")
    args = ap.parse_args()

    data = json.loads((DASH / "allinone.json").read_text(encoding="utf-8"))
    rows = data["rows"]

    # --- BigPlan ---
    bp_fixed = {s["key"]: s for s in json.loads(BP_FIXED.read_text(encoding="utf-8"))["states"]}
    bp_strict = {s["key"]: s for s in json.loads(BP_STRICT.read_text(encoding="utf-8"))["states"]}

    # --- Book Signal ---
    bs = {}
    if BS_DATA.exists():
        for r in json.loads(BS_DATA.read_text(encoding="utf-8"))["results"]:
            bs[(str(r["sid"]), str(r["filter_id"]))] = r
        if BS_STATS_FILE.exists():
            BS_STATS.update(json.loads(BS_STATS_FILE.read_text(encoding="utf-8")))

    # --- Indikator Akademi ---
    scen = json.loads(IA_SCEN.read_text(encoding="utf-8"))
    nS = len(scen["symbols"])
    FB = fbytes(nS)
    bin_cache: dict[int, bytes] = {}
    filt_cache: dict[tuple[int, int], dict] = {}

    def ia_block(idx: int, fid: int) -> dict:
        key = (idx, fid)
        if key in filt_cache:
            return filt_cache[key]
        if idx not in bin_cache:
            bin_cache[idx] = (IA_AGG / f"{idx}.bin").read_bytes()
        d = parse_block(bin_cache[idx], fid * FB, nS)
        filt_cache[key] = d
        return d

    changed_bp = changed_ia = changed_bs = 0
    for row in rows:
        src = row.get("source")
        if src == "BigPlan":
            key = str(row.get("detail", "")).split(" · ")[-1]
            f = bp_fixed.get(key)
            if not f:
                continue
            row.update(bp_metrics(f))
            s = bp_strict.get(key)
            if s:
                m = bp_metrics(s)
                for k, v in m.items():
                    row[k + "Strict"] = v
                add_ratios(row, "Strict")
            add_ratios(row, "Fixed")
            row["fixNote"] = "ATR/NATR stop giriş barından (i-1) + trailing çapa giriş fiyatı"
            changed_bp += 1
        elif src == "Indikator Akademi":
            m = re.search(r"agg/(\d+)\.bin · filter (\d+)", str(row.get("detail", "")))
            if not m:
                continue
            d = ia_block(int(m.group(1)), int(m.group(2)))
            row.update(ia_metrics(d))
            add_ratios(row, "Fixed")
            row["fixNote"] = "filtre maskesi giriş barı yerine önceki bar (feat(i-1))"
            changed_ia += 1
        elif src == "Book Signal":
            parts = str(row.get("detail", "")).split(" · ")
            if len(parts) < 2:
                continue
            b = bs.get((parts[-2].strip(), parts[-1].strip()))
            if not b:
                continue
            row.update(bs_metrics(b))
            add_ratios(row, "Fixed")
            row["fixNote"] = "short stop yön simetrisi + dedup anahtarı düzeltmesi"
            changed_bs += 1

    print(f"BigPlan satır: {changed_bp}, IA satır: {changed_ia}, Book Signal satır: {changed_bs}")

    if not args.write:
        return

    data["generated"] = dt.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    cols = list(data.get("columns") or [])
    for c in ("All Getiri % (Düzeltilmiş)", "2026 Getiri % (Düzeltilmiş)"):
        if c not in cols:
            cols.append(c)
    data["columns"] = cols
    (DASH / "allinone.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print("yazıldı: allinone.json")
    write_tables(rows)
    patch_html(rows)
    write_bigplan_table(rows)


if __name__ == "__main__":
    main()
