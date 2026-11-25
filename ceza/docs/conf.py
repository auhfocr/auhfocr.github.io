# Sphinx yapılandırması — Ceza Hukuku Genel Hükümler
# Ortak tema/HTML/PDF ayarları: _tema/ortak.py · Ders bilgileri: dersler.toml
import pathlib
import sys

_kok = next(p for p in pathlib.Path(__file__).resolve().parents if (p / "dersler.toml").exists())
sys.path.insert(0, str(_kok / "_tema"))
from ortak import yapilandir  # noqa: E402

# Eski rinohtype PDF ayarı (isteğe bağlı): make pdf
rinoh_documents = [
    dict(
        doc="index",
        target="ceza-hukuku-genel-hukumler",
        title="Ceza Hukuku Genel Hükümler",
        subtitle="Ders Notları (2018–2019)",
        author="Prof. Dr. Muharrem Özen & Ar. Gör. Eylem Baş",
        date="2018–2019",
        template="ceza.rtt",
    )
]

yapilandir(globals(), "ceza")
