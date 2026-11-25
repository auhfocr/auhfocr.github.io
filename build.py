#!/usr/bin/env python3
"""Tüm ders notlarını derleyip GitHub Pages sitesini üretir.

Kullanım::

    python build.py                 # HTML + PDF (XeLaTeX varsa), çıktı: _site/
    python build.py --pdf-yok       # yalnızca HTML (hızlı önizleme)
    python build.py ceza millet     # yalnızca seçilen dersler (+ ana sayfa)
    python build.py --sadece-anasayfa

Çıktı yapısı::

    _site/index.html                       tüm dersler (ana sayfa)
    _site/_static/                         ana sayfanın stil ve amblemi
    _site/<kimlik>/index.html              dersin web sürümü
    _site/<kimlik>/<kimlik>-ders-notlari.pdf
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import datetime as dt
import os
import pathlib
import shutil
import subprocess
import sys
import tomllib

import jinja2

KOK = pathlib.Path(__file__).resolve().parent
TEMA = KOK / "_tema"
SITE = KOK / "_site"
ARA = KOK / "_build"  # ara çıktılar (doctree, LaTeX)

sys.path.insert(0, str(TEMA))
from ortak import pdf_adi  # noqa: E402


def kayit() -> dict:
    with open(KOK / "dersler.toml", "rb") as f:
        return tomllib.load(f)


def calistir(komut: list[str], gunluk: pathlib.Path) -> None:
    gunluk.parent.mkdir(parents=True, exist_ok=True)
    with open(gunluk, "w", encoding="utf-8") as f:
        sonuc = subprocess.run(komut, stdin=subprocess.DEVNULL, stdout=f,
                               stderr=subprocess.STDOUT, cwd=KOK)
    if sonuc.returncode != 0:
        son = gunluk.read_text(encoding="utf-8", errors="replace").splitlines()[-40:]
        raise RuntimeError(
            f"Komut başarısız ({sonuc.returncode}): {' '.join(komut)}\n"
            f"Günlük: {gunluk}\n" + "\n".join(son)
        )


def sphinx(*arglar: str) -> list[str]:
    return [sys.executable, "-m", "sphinx", "-q", *arglar]


def html_derle(ders: dict, pdf_var: bool) -> None:
    kimlik = ders["kimlik"]
    hedef = SITE / kimlik
    if hedef.exists():
        shutil.rmtree(hedef)
    komut = sphinx(
        "-b", "html", "-j", "auto",
        "-d", str(ARA / "doctrees" / kimlik),
        "-A", f"pdf_var={'1' if pdf_var else ''}",
        str(KOK / ders["kaynak"]), str(hedef),
    )
    calistir(komut, ARA / "gunluk" / f"{kimlik}-html.txt")


def pdf_derle(ders: dict) -> tuple[pathlib.Path, str]:
    """PDF'i üretir; (yol, uyarı) döndürür. LaTeX küçük hatalarla da PDF
    üretebilir; o durumda PDF kullanılır ama uyarı verilir."""
    kimlik = ders["kimlik"]
    latex = ARA / "latex" / kimlik
    kaynak = latex / "latex" / f"{kimlik}.pdf"
    kaynak.unlink(missing_ok=True)
    calistir(
        sphinx("-b", "latex", "-d", str(ARA / "doctrees-latex" / kimlik),
               str(KOK / ders["kaynak"]), str(latex / "latex")),
        ARA / "gunluk" / f"{kimlik}-latex.txt",
    )
    # latexmk + xelatex. nonstopmode: küçük LaTeX hataları derlemeyi durdurmaz;
    # hata olursa PDF yine kullanılır ama uyarı verilir.
    komut = ["make", "-C", str(latex / "latex"), "all-pdf",
             "LATEXOPTS=-interaction=nonstopmode", "LATEXMKOPTS=-silent -f"]
    gunluk = ARA / "gunluk" / f"{kimlik}-pdf.txt"
    uyari = ""
    try:
        calistir(komut, gunluk)
    except RuntimeError:
        if not kaynak.exists():
            raise
        uyari = f"LaTeX hata bildirdi ama PDF üretildi; ayrıntı: {latex / 'latex' / (kimlik + '.log')}"
    hedef = SITE / kimlik / pdf_adi(kimlik)
    hedef.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(kaynak, hedef)
    return hedef, uyari


def bolum_sayisi(kimlik: str) -> int:
    """Dersin web sürümündeki not sayfası sayısı (dizin sayfaları hariç)."""
    kok = SITE / kimlik
    say = 0
    for f in kok.rglob("*.html"):
        goreli = f.relative_to(kok)
        if goreli.parts[0].startswith("_") or f.name in {"index.html", "search.html", "genindex.html"}:
            continue
        say += 1
    return say


def boyut_metni(yol: pathlib.Path) -> str:
    mb = yol.stat().st_size / (1024 * 1024)
    return f"{mb:.1f}".replace(".", ",") + " MB"


def anasayfa(veri: dict) -> None:
    site, dersler = veri["site"], veri["ders"]
    kartlar = []
    for d in dersler:
        html_var = (SITE / d["kimlik"] / "index.html").exists()
        pdf = SITE / d["kimlik"] / pdf_adi(d["kimlik"])
        kartlar.append({
            **d,
            "html_var": html_var,
            "bolum": bolum_sayisi(d["kimlik"]) if html_var else 0,
            "pdf_url": f"{d['kimlik']}/{pdf.name}" if pdf.exists() else "",
            "pdf_boyut": boyut_metni(pdf) if pdf.exists() else "",
        })
    gruplar: dict[int, list] = {}
    for k in kartlar:
        gruplar.setdefault(int(k.get("sinif", 0)), []).append(k)

    ortam = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(TEMA)),
        autoescape=True, trim_blocks=True, lstrip_blocks=True,
    )
    sablon = ortam.get_template("anasayfa.html")
    metin = sablon.render(
        site=site,
        gruplar=sorted(gruplar.items()),
        ders_sayisi=len(kartlar),
        bolum_toplam=sum(k["bolum"] for k in kartlar),
        pdf_sayisi=sum(1 for k in kartlar if k["pdf_url"]),
        tarih=dt.date.today().strftime("%d.%m.%Y"),
    )
    SITE.mkdir(parents=True, exist_ok=True)
    (SITE / "index.html").write_text(metin, encoding="utf-8")
    statik = SITE / "_static"
    statik.mkdir(exist_ok=True)
    for ad in ("ankara.css", "ankara.js", "amblem.svg"):
        shutil.copy2(TEMA / "ankara_hukuk" / "static" / ad, statik / ad)
    # ankara.css basic.css'i içe aktarır; ana sayfada boş bir dosya yeterli.
    (statik / "basic.css").write_text("/* ana sayfa için gerekmez */\n", encoding="utf-8")
    (SITE / ".nojekyll").write_text("", encoding="utf-8")


def main() -> int:
    veri = kayit()
    tum = {d["kimlik"]: d for d in veri["ders"]}

    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dersler", nargs="*", help=f"derlenecek dersler (varsayılan: hepsi): {', '.join(tum)}")
    ap.add_argument("--pdf-yok", action="store_true", help="PDF üretme, yalnızca HTML")
    ap.add_argument("--pdf-zorunlu", action="store_true", help="XeLaTeX yoksa ya da PDF başarısızsa hata ver")
    ap.add_argument("--sadece-anasayfa", action="store_true", help="yalnızca ana sayfayı yeniden üret")
    ap.add_argument("-j", "--paralel", type=int, default=min(4, os.cpu_count() or 1),
                    help="aynı anda derlenecek PDF sayısı")
    args = ap.parse_args()

    bilinmeyen = [k for k in args.dersler if k not in tum]
    if bilinmeyen:
        ap.error(f"bilinmeyen ders: {', '.join(bilinmeyen)}")
    secilen = [tum[k] for k in (args.dersler or tum)]

    if args.sadece_anasayfa:
        anasayfa(veri)
        print(f"Ana sayfa: {SITE / 'index.html'}")
        return 0

    pdf_istendi = not args.pdf_yok
    if pdf_istendi and not all(shutil.which(a) for a in ("xelatex", "latexmk", "make")):
        if args.pdf_zorunlu:
            print("HATA: PDF için xelatex, latexmk ve make gerekli.", file=sys.stderr)
            return 1
        print("! xelatex/latexmk bulunamadı; PDF'ler atlanıyor (yalnızca HTML).")
        pdf_istendi = False

    hatalar: list[str] = []
    for d in secilen:
        print(f"→ HTML  {d['kimlik']:<11} {d['ad']}", flush=True)
        try:
            html_derle(d, pdf_istendi)
        except RuntimeError as e:
            hatalar.append(str(e))

    if pdf_istendi:
        with cf.ThreadPoolExecutor(max_workers=max(1, args.paralel)) as havuz:
            isler = {havuz.submit(pdf_derle, d): d for d in secilen}
            for is_ in cf.as_completed(isler):
                d = isler[is_]
                try:
                    yol, uyari = is_.result()
                    print(f"✓ PDF   {d['kimlik']:<11} {boyut_metni(yol)}", flush=True)
                    if uyari:
                        print(f"  ! {uyari}", flush=True)
                except RuntimeError as e:
                    print(f"✗ PDF   {d['kimlik']}", flush=True)
                    hatalar.append(str(e))

    anasayfa(veri)
    print(f"Site hazır: {SITE / 'index.html'}")

    if hatalar:
        print("\n".join(["", "Hatalar:", *hatalar]), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
