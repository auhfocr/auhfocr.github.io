# Hukuk Ders Notları

Ankara Üniversitesi Hukuk Fakültesi ders notlarım. Her ders ayrı bir Sphinx
projesi; hepsi aynı temayla (`_tema/ankara_hukuk`) derlenir ve her biri için
hem **web sürümü** hem **PDF** üretilir. Site GitHub Pages üzerinde yayınlanır.

| Ders | Klasör | Yıl |
|---|---|---|
| Anayasa Hukuku | `anayasa/docs` | 2018–2019 |
| Anayasa Hukuku (Prof. Dr. Selin Esen) | `anayasa-cy/docs` | 2022–2023 |
| Borçlar Hukuku Genel Hükümler | `borc/docs/source` | 2022–2023 |
| Ceza Hukuku Genel Hükümler | `ceza/docs` | 2018–2019 |
| İdare Hukuku | `idare/source` | 2022–2023 |
| Kamu Maliyesi | `maliye/docs` | 2022–2023 |
| Milletlerarası Hukuk | `millet` | 2022–2023 |

## Yapı

```
dersler.toml              derslerin listesi ve bilgileri (tek kaynak)
build.py                  tüm dersleri derler, ana sayfayı üretir → _site/
_tema/
  ortak.py                ortak Sphinx ayarları (tema, HTML, LaTeX/PDF)
  ankara_hukuk/           HTML teması (layout, CSS, JS, amblem)
  latex/                  PDF görünümü: kapak, başlıklar, üst bilgi, yazı tipleri
  ankara_hukuk_ek.py      küçük uzantı (özgün not sayfası işaretleri PDF'de)
  anasayfa.html           tüm dersler sayfasının şablonu
.github/workflows/pages.yml   GitHub Actions: derle + yayınla
```

Her dersin `conf.py` dosyası yalnızca `yapilandir(globals(), "<kimlik>")`
çağırır; ders adı, hoca, yıl, şube gibi bilgiler `dersler.toml` içindedir.

## Yerelde derleme

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

.venv/bin/python build.py --pdf-yok      # yalnızca HTML (hızlı)
.venv/bin/python build.py                # HTML + PDF (XeLaTeX gerekir)
.venv/bin/python build.py ceza millet    # yalnızca bazı dersler
python3 -m http.server -d _site          # http://localhost:8000
```

PDF için XeLaTeX gerekir. Fedora'da: `sudo dnf install texlive-scheme-medium
texlive-tex-gyre latexmk`. Ubuntu'da: iş akışındaki `apt-get install`
satırına bakın. Derleme günlükleri `_build/gunluk/` klasörüne yazılır.

Tek bir dersi eskisi gibi kendi klasöründe de derleyebilirsiniz
(ör. `cd ceza/docs && make html`). Tema yine aynı olur.

## GitHub Pages'e yayınlama

1. GitHub'da yeni bir depo açın ve bu klasörü gönderin:

   ```sh
   git init -b main
   git add .
   git commit -m "Ders notları sitesi"
   git remote add origin git@github.com:auhfocr/auhfocr.github.io.git
   git push -u origin main
   ```

2. Depoda **Settings → Pages → Build and deployment → Source** ayarını
   **GitHub Actions** yapın.
3. Her `main` gönderiminde iş akışı tüm dersleri HTML ve PDF olarak derleyip
   yayınlar. Site adresi: <https://auhfocr.github.io/>.

## Yeni ders eklemek

1. Dersin Sphinx kaynağını yeni bir klasöre koyun (ör. `medeni/docs`).
2. `dersler.toml` dosyasına bir `[[ders]]` bloğu ekleyin.
3. Klasördeki `conf.py` dosyasını başka bir dersinkinden kopyalayıp kimliği
   değiştirin.

## Not

Notlar öğrenci tarafından tutulmuştur; Ankara Üniversitesi'nin ya da öğretim
üyelerinin resmî yayını değildir. Tema okulun lacivert-altın renklerinden ve
Hitit güneş kursu motifinden esinlenir; resmî logo kullanılmamıştır.
