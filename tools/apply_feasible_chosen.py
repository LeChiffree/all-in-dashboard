#!/usr/bin/env python3
"""Apply the feasible Chosen migration, then rebuild AUTO_CHOSEN."""

from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def replace_if_needed(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if new in text:
        return
    if old not in text:
        raise SystemExit(f"Expected text not found in {path}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def main() -> None:
    replace_if_needed(ROOT / "index.html", 'const STORAGE_KEY = "allinone_chosen_v3";', 'const STORAGE_KEY = "allinone_chosen_v4";')
    replace_if_needed(ROOT / "picker.html", "STORAGE_KEY='allinone_chosen_v3'", "STORAGE_KEY='allinone_chosen_v4'")
    replace_if_needed(
        ROOT / "index.html",
        """    // Yeni Chosen sürümü boş başlar; seçimler kullanıcı tarafından yapılır.
    chosen = new Set();""",
        """    // Yeni Chosen sürümü fizibilite kuralıyla tekilleştirilmiş listeyle başlar.
    chosen = new Set(validKeys(AUTO_KEYS));""",
    )
    replace_if_needed(
        ROOT / "README.md",
        "Chosen ilk açılışta boş gelir; `Auto seç` butonu istenirse aşağıdaki kuralı uygular.",
        "Chosen ilk açılışta aşağıdaki fizibilite kuralıyla tekilleştirilmiş listeyi getirir; `Auto seç` aynı kuralı yeniden uygular.",
    )
    replace_if_needed(
        ROOT / "README.md",
        """Seçim `allinone_chosen_v4` anahtarıyla `localStorage`'da saklanır. Yeni sürüm
  fizibilite kuralıyla seçilen 85 satırla başlar; `Auto seç` aynı kuralı yeniden uygular.""",
        """Seçim `allinone_chosen_v4` anahtarıyla `localStorage`'da saklanır. Yeni sürüm
  fizibilite kuralıyla kategori bağımsız tekilleştirilen 64 satırla başlar; `Auto seç` aynı kuralı yeniden uygular.""",
    )
    replace_if_needed(
        ROOT / "index.html",
        """  } catch (error) {
    chosen = new Set();
  }
}

function saveChosen() {""",
        """  } catch (error) {
    chosen = new Set();
  }
  dedupeChosenAcrossSources();
}

function saveChosen() {""",
    )
    replace_if_needed(
        ROOT / "index.html",
        """function esc(value) {""",
        """function dedupeChosenAcrossSources() {
  const best = new Map();
  const score = (row) => [
    Number(row.retAllFixed), Number(row.weekRatioFixed), Number(row.dayRatioFixed),
    -Number(row.winHoldHFixed), Number(row.tradesFixed) || 0,
  ];
  const better = (a, b) => {
    const x = score(a), y = score(b);
    for (let i = 0; i < x.length; i++) if (x[i] !== y[i]) return x[i] > y[i];
    return false;
  };
  for (const key of chosen) {
    const row = rowByKey.get(key);
    if (!row) continue;
    const group = row.strategy + "||" + row.timeframe;
    const old = best.get(group);
    if (!old || better(row, old)) best.set(group, row);
  }
  const normalized = new Set([...best.values()].map(rowKey));
  if (normalized.size !== chosen.size) {
    chosen = normalized;
    saveChosen();
  }
}

function esc(value) {""",
    )
    subprocess.run([sys.executable, str(ROOT / "tools" / "auto_chosen.py")], check=True)


if __name__ == "__main__":
    main()
