#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Singular-Backtest payload'larını dashboard sekmesi için sıkıştırır.

Altı repodaki `singular_results.json` dosyalarını okur, ortak şemaya çevirir
ve `singular/summary.js` (`window.SINGULAR_DATA = ...`) ile `summary.json`
üretir. Dashboard `index.html` doğrudan dosyadan açılabilsin diye JSON yerine
script olarak yazılır.

Kullanım:
  python singular/build_summary.py
  python singular/build_summary.py --codex=... --indikator=...
"""
from __future__ import annotations

import argparse
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DASH = os.path.dirname(HERE)
PROJECTS = os.path.dirname(DASH)


def default_paths():
    return {
        "codex": os.path.join(PROJECTS, "Codex-Bulut-Backtests", "Singular-Backtest", "singular_results.json"),
        "paper": os.path.join(PROJECTS, "paper-ml-bsh", "Singular-Backtest", "singular_results.json"),
        "bigplan": os.path.join(PROJECTS, "bigplan-backtest-lab", "Singular-Backtest", "singular_results.json"),
        "book": os.path.join(PROJECTS, "book-signal-review", "Singular-Backtest", "results", "singular_results.json"),
        "v4": os.path.join(PROJECTS, "binance-v4-strategy-research", "Singular-Backtest", "results", "singular_results.json"),
        "indikator": os.path.join(PROJECTS, "indikator-akademi", "Singular-Backtest", "results", "singular_results.json"),
    }


def num(v, default=0.0):
    try:
        x = float(v)
        return x if x == x else default
    except Exception:
        return default


def pick(d, *names, default=0.0):
    for n in names:
        if n in d and d[n] is not None:
            return d[n]
    return default


def ratio(wins, losses):
    w, l = num(wins), num(losses)
    return (w / l) if l else w


def totals_of(pay, key, which):
    t = pay.get("totals", {}).get(which, {})
    ret = num(pick(t, "retAll", "avgRet", "avg_ret"))
    if key == "codex":
        ret *= 100.0
    return {
        "trades": round(num(pick(t, "trades"))),
        "retAll": round(ret, 4),
        "winRate": round(num(pick(t, "winRate", "win_rate")), 4),
        "winHoldH": round(num(pick(t, "winHoldH", "win_hold_h")), 2),
    }


def row(key, o):
    """Ortak satır şeması."""
    if key == "codex":
        nret = num(pick(o, "n_avg_ret")) * 100
        sret = num(pick(o, "s_avg_ret")) * 100
        n26 = num(pick(o, "n_ret2026")) * 100
        s26 = num(pick(o, "s_ret2026")) * 100
        nw = ratio(pick(o, "n_wins"), pick(o, "n_losses"))
        sw = ratio(pick(o, "s_wins"), pick(o, "s_losses"))
        name = f"{o.get('sid', '')} · {o.get('name', '')}" if o.get("sid") is not None else str(o.get("name", ""))
        tf = str(o.get("tf", ""))
        flt = "—"
        nwrate = num(pick(o, "n_win_rate"))
        swrate = num(pick(o, "s_win_rate"))
        nh = num(pick(o, "n_win_hold_h"))
        sh = num(pick(o, "s_win_hold_h"))
    elif key == "paper":
        nret, sret = num(pick(o, "n_retAll")), num(pick(o, "s_retAll"))
        n26, s26 = num(pick(o, "n_ret2026")), num(pick(o, "s_ret2026"))
        nw, sw = num(pick(o, "n_winRatio")), num(pick(o, "s_winRatio"))
        nm = o.get("name") or o.get("scenario") or o.get("strategy") or ""
        name = str(nm)
        tf = str(o.get("tf", ""))
        flt = str(o.get("filter", "") or "")
        if o.get("threshold") is not None:
            flt += f" · eşik {o['threshold']}"
        nwrate, swrate = num(pick(o, "n_win_rate")), num(pick(o, "s_win_rate"))
        nh, sh = num(pick(o, "n_winHoldH")), num(pick(o, "s_winHoldH"))
    elif key == "bigplan":
        nret, sret = num(pick(o, "n_retAll", "n_avgRet")), num(pick(o, "s_retAll", "s_avgRet"))
        n26, s26 = num(pick(o, "n_ret2026")), num(pick(o, "s_ret2026"))
        nw, sw = num(pick(o, "n_winRatio")), num(pick(o, "s_winRatio"))
        name = str(o.get("title", o.get("id", "")))
        tf = "tümü"
        flt = str(o.get("kind", ""))
        nwrate, swrate = num(pick(o, "n_winRate")), num(pick(o, "s_winRate"))
        nh, sh = num(pick(o, "n_winHoldH")), num(pick(o, "s_winHoldH"))
    else:  # book / v4 / indikator
        nret, sret = num(pick(o, "n_retAll")), num(pick(o, "s_retAll"))
        n26, s26 = num(pick(o, "n_ret2026")), num(pick(o, "s_ret2026"))
        nw, sw = num(pick(o, "n_winRatio")), num(pick(o, "s_winRatio"))
        name = str(o.get("title") or o.get("strategy") or o.get("sid") or "")
        tf = str(o.get("timeframe", o.get("tf", "")))
        flt = str(o.get("filter_label", o.get("stage_label", "")) or "")
        nwrate, swrate = num(pick(o, "n_winRate")), num(pick(o, "s_winRate"))
        nh, sh = num(pick(o, "n_winHoldH")), num(pick(o, "s_winHoldH"))

    nt = num(pick(o, "n_trades"))
    st = num(pick(o, "s_trades"))
    if key == "codex" and not st:
        st = num(pick(o, "s_trades"))
    b = num(pick(o, "blocked"))
    bp = num(pick(o, "blocked_pct"))
    if not bp and nt:
        bp = max(0.0, nt - st) / nt * 100
    return {
        "n": name,
        "t": tf,
        "f": flt,
        "nt": round(nt),
        "st": round(st),
        "b": round(b),
        "bp": round(bp, 2),
        "nr": round(nret, 4),
        "sr": round(sret, 4),
        "n26": round(n26, 4),
        "s26": round(s26, 4),
        "nw": round(nw, 4),
        "sw": round(sw, 4),
        "nh": round(nh, 2),
        "sh": round(sh, 2),
        "nwr": round(nwrate, 4),
        "swr": round(swrate, 4),
    }


def rows_of(key, pay):
    if key == "codex":
        return pay.get("strategies", [])
    if key == "paper":
        return pay.get("scenarios", [])
    if key == "bigplan":
        return pay.get("configs", [])
    return pay.get("rows", [])


def build(paths):
    order = [
        ("bigplan", "BigPlan", "bigplan-backtest-lab"),
        ("book", "Book Signal", "book-signal-review"),
        ("codex", "Codex Bulut", "Codex-Bulut-Backtests"),
        ("paper", "Paper ML", "paper-ml-bsh"),
        ("indikator", "Indikator Akademi", "indikator-akademi"),
        ("v4", "V4 Short", "binance-v4-strategy-research"),
    ]
    out = []
    for key, label, repo in order:
        path = paths[key]
        if not os.path.exists(path):
            print(f"[skip] {key}: {path} yok")
            continue
        with open(path, encoding="utf-8") as f:
            pay = json.load(f)
        total = pay.get("totals", {})
        tn = totals_of(pay, key, "normal")
        # singular totals
        st = total.get("singular", {})
        sing = totals_of(pay, key, "singular")
        blocked = total.get("blocked")
        if blocked is None:
            blocked = max(0, tn["trades"] - sing["trades"])
        bp = total.get("blocked_pct")
        if bp is None:
            bp = (blocked / tn["trades"] * 100) if tn["trades"] else 0.0
        rows = [row(key, o) for o in rows_of(key, pay)]
        print(f"[ok] {label}: {len(rows):,} satır | normal {tn['trades']:,} -> singular {sing['trades']:,} (%{num(bp):.2f})")
        out.append({
            "key": key,
            "label": label,
            "repo": repo,
            "scope": pay.get("scope"),
            "scope_label": pay.get("scope_label") or pay.get("scope") or "",
            "rule": pay.get("rule", ""),
            "generated_at": pay.get("generated_at"),
            "totals": {
                "normal": tn,
                "singular": sing,
                "blocked": round(num(blocked)),
                "blocked_pct": round(num(bp), 2),
            },
            "rows": rows,
        })
    return {
        "generated_at": __import__("datetime").datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "repos": out,
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
    with open(os.path.join(HERE, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    with open(os.path.join(HERE, "summary.js"), "w", encoding="utf-8") as f:
        f.write("window.SINGULAR_DATA = ")
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
        f.write(";\n")
    total = sum(len(r["rows"]) for r in data["repos"])
    print(f"[done] {len(data['repos'])} repo, {total:,} satır → singular/summary.js")


if __name__ == "__main__":
    main()
