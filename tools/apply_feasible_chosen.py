#!/usr/bin/env python3
"""Apply the 85-row feasible Chosen migration, then rebuild AUTO_CHOSEN."""

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
        """Seçim `allinone_chosen_v3` anahtarıyla `localStorage`'da saklanır. Yeni sürüm boş
  listeyle başlar; `Auto seç` butonuyla otomatik kural ayrıca uygulanabilir.""",
        """Seçim `allinone_chosen_v4` anahtarıyla `localStorage`'da saklanır. Yeni sürüm
  fizibilite kuralıyla seçilen 85 satırla başlar; `Auto seç` aynı kuralı yeniden uygular.""",
    )
    subprocess.run([sys.executable, str(ROOT / "tools" / "auto_chosen.py")], check=True)


if __name__ == "__main__":
    main()
