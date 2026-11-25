# Milletlerarası Hukuk Ders Notları — Sphinx

Notlar `notlar/` klasöründe, haftalara göre bölünmüş Markdown (MyST) dosyalarıdır.
`milletlerarasi_hukuk_ders_notlari.md` orijinal tek dosyadır; derlemeye dahil edilmez.

## Kurulum (bir kez)

    python3 -m venv --system-site-packages .venv
    .venv/bin/pip install -r requirements.txt

## Derleme

    make html        # çıktı: _build/html/index.html
    make latexpdf    # PDF (xelatex gerekir)
    make clean
