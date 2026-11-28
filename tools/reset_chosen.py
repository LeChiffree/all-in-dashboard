#!/usr/bin/env python3
"""Reset Chosen storage to an empty v3 list in dashboard and picker."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: Path, old: str, new: str) -> bool:
    text = path.read_text(encoding="utf-8")
    if new in text:
        return False
    if old not in text:
        raise SystemExit(f"Expected text not found in {path}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    return True


def main() -> None:
    changed = False
    index = ROOT / "index.html"
    picker = ROOT / "picker.html"
    readme = ROOT / "README.md"

    changed |= replace_once(index, 'const STORAGE_KEY = "allinone_chosen_v2";', 'const STORAGE_KEY = "allinone_chosen_v3";')
    changed |= replace_once(picker, "const $=id=>document.getElementById(id), STORAGE_KEY='allinone_chosen_v2';", "const $=id=>document.getElementById(id), STORAGE_KEY='allinone_chosen_v3';")
    changed |= replace_once(
        index,
        """  if (stored == null) {
    // İlk açılış: kurala uyan satırlar otomatik seçili gelir.
    chosen = new Set(validKeys(AUTO_KEYS));
    saveChosen();
    return;
  }""",
        """  if (stored == null) {
    // Yeni Chosen sürümü boş başlar; seçimler kullanıcı tarafından yapılır.
    chosen = new Set();
    saveChosen();
    return;
  }""",
    )
    changed |= replace_once(
        readme,
        """- **Chosen sekmesi:** satır başındaki `+` ile seçilen stratejiler; seçimler tarayıcıda `localStorage` ile saklanır.
  İlk açılışta aşağıdaki kurala uyan satırlar **otomatik seçili** gelir; `Auto seç` butonu kuralı yeniden uygular.""",
        """- **Chosen sekmesi:** satır başındaki `+` ile seçilen stratejiler; seçimler tarayıcıda `localStorage` ile saklanır.
  Chosen ilk açılışta boş gelir; `Auto seç` butonu istenirse aşağıdaki kuralı uygular.""",
    )
    changed |= replace_once(
        readme,
        """- Seçim `allinone_chosen_v2` anahtarıyla `localStorage`'da saklanır. Tarayıcıda kayıtlı
  bir seçim varsa otomatik liste uygulanmaz; `Auto seç` butonuyla uygulanır.""",
        """- Seçim `allinone_chosen_v3` anahtarıyla `localStorage`'da saklanır. Yeni sürüm boş
  listeyle başlar; `Auto seç` butonuyla otomatik kural ayrıca uygulanabilir.""",
    )
    print("Chosen reset applied." if changed else "Chosen reset already applied.")


if __name__ == "__main__":
    main()
