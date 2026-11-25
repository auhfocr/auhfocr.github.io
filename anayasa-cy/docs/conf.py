# Sphinx yapılandırması — Anayasa Hukuku (Prof. Dr. Selin Esen, 2022–2023)
# Ortak tema/HTML/PDF ayarları: _tema/ortak.py · Ders bilgileri: dersler.toml
import pathlib
import sys

_kok = next(p for p in pathlib.Path(__file__).resolve().parents if (p / "dersler.toml").exists())
sys.path.insert(0, str(_kok / "_tema"))
from ortak import yapilandir  # noqa: E402

# Eski rinohtype PDF ayarı (isteğe bağlı): sphinx-build -b rinoh . _build/rinoh
rinoh_documents = [
    dict(
        doc="index",
        target="anayasa-hukuku",
        title="Anayasa Hukuku Ders Notları",
        subtitle="I. ve II. Dönem (2022–2023)",
        author="Prof. Dr. Selin Esen (derleyen: Cengiz Yıldırım)",
        date="2023",
        template="anayasa.rtt",
    )
]

yapilandir(globals(), "anayasa-cy")
