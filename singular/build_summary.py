#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Singular-Backtest payload'larını Allinone satırlarıyla eşleştirir.

Altı repodaki singular sonuçları, `allinone.json` satırlarının anahtarıyla
(source||strategy||filter||timeframe) eşleştirir ve
`singular/summary.js` (`window.SINGULAR_DATA = {byKey: ...}`) üretir.

Dashboard bu dosyayı yükleyip Allinone tablosunda normal sütunların yanındaki
singular sütunları doldurur.

Kullanım:
  python singular/build_summary.py
"""
from __future__ import annotations

import argparse
import json
import os
import re
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
DASH = os.path.dirname(HERE)
PROJECTS = os.path.dirname(DASH)


def default_paths():
    return {
        "codex": os.path.join(PROJECTS, "Codex-Bulut-Backtests", "Singular-Backtest", "singular_results.json"),
        "codex_filters": os.path.join(PROJECTS, "Codex-Bulut-Backtests", "Singular-Backtest", "results", "filter_singular.json"),
        "codex_normal_filters": os.path.join(PROJECTS, "Codex-Bulut-Backtests", "Singular-Backtest", "results", "filter_normal.json"),
        "paper": os.path.join(PROJECTS, "paper-ml-bsh", "Singular-Backtest", "singular_results.json"),
        "bigplan": os.path.join(PROJECTS, "bigplan-backtest-lab", "Singular-Backtest", "singular_results.json"),
        "book": os.path.join(PROJECTS, "book-signal-review", "Singular-Backtest", "results", "singular_results.json"),
        "v4": os.path.join(PROJECTS, "binance-v4-strategy-research", "Singular-Backtest", "results", "singular_results.json"),
        "indikator": os.path.join(PROJECTS, "indikator-akademi", "Singular-Backtest", "results", "singular_results.json"),
        "allinone": os.path.join(DASH, "allinone.json"),
    }


def num(v, default=0.0):
    try:
        x = float(v)
        return x if x == x else default
    except Exception:
        return default


def gm(m, name, prefix="s_"):
    """Önekli (varsayılan s_) ya da düz alanı oku."""
    return m.get(prefix + name, m.get(name))


def flat(m, scale=1.0, prefix="s_", per_trade=False):
    if per_trade:
        retAll = num(gm(m, "avg_ret", prefix))
        ret2026 = num(gm(m, "avg_ret2026", prefix))
    else:
        retAll = num(gm(m, "retAll", prefix)) * scale
        ret2026 = num(gm(m, "ret2026", prefix)) * scale
    return {
        "trades": round(num(gm(m, "trades", prefix))),
        "retAll": round(retAll, 4),
        "ret2026": round(ret2026, 4),
        "winRatio": (None if gm(m, "winRatio", prefix) is None else round(num(gm(m, "winRatio", prefix)), 4)),
        "winHoldH": (None if gm(m, "winHoldH", prefix) is None else round(num(gm(m, "winHoldH", prefix)), 2)),
        "profitDays": (None if gm(m, "profitDays", prefix) is None else round(num(gm(m, "profitDays", prefix)))),
        "lossDays": (None if gm(m, "lossDays", prefix) is None else round(num(gm(m, "lossDays", prefix)))),
        "profitWeeks": (None if gm(m, "profitWeeks", prefix) is None else round(num(gm(m, "profitWeeks", prefix)))),
        "lossWeeks": (None if gm(m, "lossWeeks", prefix) is None else round(num(gm(m, "lossWeeks", prefix)))),
        "profitMonths": (None if gm(m, "profitMonths", prefix) is None else round(num(gm(m, "profitMonths", prefix)))),
        "lossMonths": (None if gm(m, "lossMonths", prefix) is None else round(num(gm(m, "lossMonths", prefix)))),
    }


def periods(m):
    """Yalnızca hafta/ay kâr-zarar sayılarını normal taraf için taşı."""
    return {
        "profitWeeks": (None if gm(m, "profitWeeks", "n_") is None else round(num(gm(m, "profitWeeks", "n_")))),
        "lossWeeks": (None if gm(m, "lossWeeks", "n_") is None else round(num(gm(m, "lossWeeks", "n_")))),
        "profitMonths": (None if gm(m, "profitMonths", "n_") is None else round(num(gm(m, "profitMonths", "n_")))),
        "lossMonths": (None if gm(m, "lossMonths", "n_") is None else round(num(gm(m, "lossMonths", "n_")))),
    }


def key_of(r):
    return "||".join([r["source"], r["strategy"], str(r["filter"]), str(r["timeframe"])])


def build(paths):
    with open(paths["allinone"], encoding="utf-8") as f:
        rows = json.load(f)["rows"]

    by_source = {}
    for r in rows:
        by_source.setdefault(r["source"], []).append(r)

    out = {}
    matched = {}

    # ---------------- BigPlan: states key = detail son parçası ----------------
    p = paths["bigplan"]
    if os.path.exists(p):
        pay = json.load(open(p, encoding="utf-8"))
        idx = {r["detail"].rsplit(" · ", 1)[-1]: r for r in by_source.get("BigPlan", [])}
        n = 0
        for st in pay.get("states", []):
            r = idx.get(st.get("key"))
            if r:
                out[key_of(r)] = {"n": periods(st), "s": flat(st)}
                n += 1
        matched["BigPlan"] = (n, len(by_source.get("BigPlan", [])))

    # ---------------- Book: detail son iki parçası = sid, filter_id ----------------
    p = paths["book"]
    if os.path.exists(p):
        pay = json.load(open(p, encoding="utf-8"))
        idx = {}
        for r in by_source.get("Book Signal", []):
            parts = r["detail"].rsplit(" · ", 2)
            if len(parts) >= 3:
                idx[(parts[-2], parts[-1])] = r
        n = 0
        for row in pay.get("rows", []):
            r = idx.get((row["sid"], str(row["filter_id"])))
            if r:
                out[key_of(r)] = {"n": periods(row), "s": flat(row)}
                n += 1
        matched["Book Signal"] = (n, len(by_source.get("Book Signal", [])))

    # ---------------- Codex: filtre düzeyi (yeni) + baseline ----------------
    p = paths["codex_filters"]
    if os.path.exists(p):
        filt = json.load(open(p, encoding="utf-8"))
        pn = paths.get("codex_normal_filters")
        norm = json.load(open(pn, encoding="utf-8")) if pn and os.path.exists(pn) else {}
        idx = {}
        for r in by_source.get("Codex Bulut", []):
            idx[(r["strategy"], r["timeframe"], str(r["filter"]))] = r
        n = 0
        miss = 0
        for k, v in filt.items():
            r = idx.get((v.get("scenario_name", ""), k.split("|")[1], v.get("filter_label")))
            if r:
                nv = norm.get(k)
                out[key_of(r)] = {
                    "n": flat(nv, scale=100.0, prefix="n_") if nv else None,
                    "s": flat(v, scale=100.0),
                }
                n += 1
            else:
                miss += 1
        matched["Codex Bulut"] = (n, len(by_source.get("Codex Bulut", [])))
        print(f"[codex] filtre eşleşmesi {n:,}, eşleşmeyen {miss:,}")

    # ---------------- Paper: scenario id + tf ----------------
    p = paths["paper"]
    if os.path.exists(p):
        pay = json.load(open(p, encoding="utf-8"))
        idx = {}
        for r in by_source.get("Paper ML", []):
            m = re.search(r"scenario (\d+)", r["detail"])
            if m:
                idx[(int(m.group(1)), r["timeframe"])] = r
        n = 0
        for sc in pay.get("scenarios", []):
            r = idx.get((int(sc["sid"]), sc.get("tf")))
            if r:
                out[key_of(r)] = {"n": periods(sc), "s": flat(sc, per_trade=True)}
                n += 1
        matched["Paper ML"] = (n, len(by_source.get("Paper ML", [])))

    # ---------------- Indikator: si + filter ----------------
    p = paths["indikator"]
    if os.path.exists(p):
        pay = json.load(open(p, encoding="utf-8"))
        idx = {}
        for r in by_source.get("Indikator Akademi", []):
            m = re.search(r"agg/(\d+)\.bin · filter (\d+)", r["detail"])
            if m:
                idx[(int(m.group(1)), int(m.group(2)))] = r
        n = 0
        for row in pay.get("rows", []):
            r = idx.get((int(row["idx"]), int(row["filter_id"])))
            if r:
                out[key_of(r)] = {"n": periods(row), "s": flat(row)}
                n += 1
        matched["Indikator Akademi"] = (n, len(by_source.get("Indikator Akademi", [])))

    # ---------------- V4: pattern + variant + stage ----------------
    p = paths["v4"]
    if os.path.exists(p):
        pay = json.load(open(p, encoding="utf-8"))
        idx = {}
        for r in by_source.get("V4 Short", []):
            m = re.search(r"pattern (\d+) · (.+) · stage(\d+)", r["detail"])
            if m:
                idx[(int(m.group(1)), m.group(2), int(m.group(3)))] = r
        n = 0
        for row in pay.get("rows", []):
            r = idx.get((int(row["pattern_id"]), row["variant"], int(str(row["filter_id"]))))
            if r:
                out[key_of(r)] = {"n": periods(row), "s": flat(row)}
                n += 1
        matched["V4 Short"] = (n, len(by_source.get("V4 Short", [])))

    return {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "allinone_rows": len(rows),
        "matched_rows": len(out),
        "matched": {k: {"matched": v[0], "total": v[1]} for k, v in matched.items()},
        "byKey": out,
    }


def main():
    ap = argparse.ArgumentParser()
    for k in default_paths():
        ap.add_argument(f"--{k}")
    args = ap.parse_args()
    paths = default_paths()
    for k in paths:
        v = getattr(args, k)
        if v:
            paths[k] = v
    data = build(paths)
    os.makedirs(HERE, exist_ok=True)
    with open(os.path.join(HERE, "summary.js"), "w", encoding="utf-8") as f:
        f.write("window.SINGULAR_DATA = ")
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
        f.write(";\n")
    print(f"[done] {data['matched_rows']:,}/{data['allinone_rows']:,} satır eşleşti")
    for k, v in data["matched"].items():
        print(f"  {k}: {v['matched']:,}/{v['total']:,}")


if __name__ == "__main__":
    main()
