#!/usr/bin/env python3
"""ceza_hukuku_genel_hukumler_notlari.md -> Sphinx (reStructuredText) projesi.

Kullanım: python3 md2sphinx.py ceza_hukuku_genel_hukumler_notlari.md docs

Her "## N. Hafta (tarih | Sayfa X–Y)" başlığı ayrı bir sayfa olur;
"# N. DÖNEM" başlıkları donemN/ klasörlerine ayırır. Dosyanın ilk
dönem başlığından önceki kısmı ana sayfaya (index.rst) girer.
"""
import re
import sys
import unicodedata
from pathlib import Path

from markdown_it import MarkdownIt
from markdown_it.tree import SyntaxTreeNode

SRC = Path(sys.argv[1])
OUT = Path(sys.argv[2])

DONEM_RE = re.compile(r"^# (\d+)\. DÖNEM\b")
HAFTA_RE = re.compile(r"^## (?P<hafta>.+?) \((?P<tarih>.+?) \| Sayfa (?P<sayfa>.+)\)\s*$")
PAGE_RE = re.compile(r"^## (Sayfa \d+.*)$")  # bu notlarda yok; Renderer için
SECTION_CHARS = ["=", "-", "~", "^", '"', "'"]


def split_weeks(lines):
    """(önsöz satırları, [(dönem, hafta, tarih, sayfa, satırlar), ...])"""
    preface, weeks = [], []
    donem = None
    for line in lines:
        m = DONEM_RE.match(line)
        if m:
            donem = int(m.group(1))
            continue
        m = HAFTA_RE.match(line)
        if m and donem is not None:
            weeks.append((donem, m["hafta"], m["tarih"], m["sayfa"], []))
            continue
        if weeks:
            weeks[-1][4].append(line)
        elif donem is None and not line.startswith("# "):
            preface.append(line)
    return preface, weeks


def week_slug(hafta):
    nums = re.findall(r"\d+", hafta)
    return "-".join(f"{int(n):02d}" for n in nums) + "-hafta"


# ---------------------------------------------------------------- inline
BEFORE_OK = set(" \t\n'\"([{<-/:")
AFTER_OK = set(" \t\n-.,:;!?\\/'\")]}>")


def ok_before(c):
    return c == "" or c in BEFORE_OK or unicodedata.category(c) in ("Ps", "Pi", "Pf", "Pd", "Po", "Zs")


def ok_after(c):
    return c == "" or c in AFTER_OK or unicodedata.category(c) in ("Pe", "Pi", "Pf", "Pd", "Po", "Zs")


def esc(text):
    text = text.replace("\\", "\\\\")
    for ch in "*`|_":
        text = text.replace(ch, "\\" + ch)
    return text


def plain(node):
    """Bir düğümün düz metni (iç içe vurgu reST'te desteklenmez)."""
    if node.type in ("text", "code_inline"):
        return node.content
    if node.type in ("softbreak", "hardbreak"):
        return " "
    if node.type == "html_inline":
        return " " if re.match(r"<br\s*/?>", node.content, re.I) else node.content
    return "".join(plain(c) for c in node.children)


def inline_segments(node):
    """Satır listesi döndürür; her satır (tür, metin) parçalarından oluşur."""
    lines = [[]]
    for c in node.children:
        t = c.type
        if t == "text":
            lines[-1].append(("t", c.content))
        elif t in ("softbreak", "hardbreak"):
            lines.append([])
        elif t == "html_inline":
            if re.match(r"<br\s*/?>", c.content, re.I):
                lines.append([])
            else:
                lines[-1].append(("t", c.content))
        elif t == "strong":
            lines[-1].append(("**", plain(c)))
        elif t == "em":
            # em içinde strong varsa strong olarak bas
            kind = "**" if any(g.type == "strong" for g in c.children) else "*"
            lines[-1].append((kind, plain(c)))
        elif t == "code_inline":
            lines[-1].append(("``", c.content))
        elif t == "link":
            href = c.attrs.get("href", "")
            txt = plain(c)
            lines[-1].append(("link", (txt, href)))
        elif t == "image":
            lines[-1].append(("t", plain(c)))
        else:
            lines[-1].append(("t", plain(c)))
    return lines


def render_segments(segs):
    # bitişik düz metinleri birleştir
    merged = []
    for k, v in segs:
        if k == "t" and merged and merged[-1][0] == "t":
            merged[-1] = ("t", merged[-1][1] + v)
        else:
            merged.append((k, v))
    out = []
    for i, (k, v) in enumerate(merged):
        if k == "t":
            out.append(esc(v))
            continue
        if k == "link":
            txt, href = v
            piece = f"`{esc(txt)} <{href}>`__" if txt.strip() else href
            lead, trail = "", ""
        else:
            raw = v if k == "``" else v
            stripped = raw.strip()
            lead = raw[: len(raw) - len(raw.lstrip())]
            trail = raw[len(raw.rstrip()):]
            if not stripped:
                out.append(esc(raw))
                continue
            if k == "``":
                piece = f"``{stripped}``"
            else:
                piece = f"{k}{esc(stripped)}{k}"
        prev = "".join(out)
        prev_c = (lead[-1:] if lead else prev[-1:])
        nxt_raw = merged[i + 1][1] if i + 1 < len(merged) else ""
        if trail:
            nxt_c = trail[:1]
        elif i + 1 < len(merged) and merged[i + 1][0] == "t":
            nxt_c = nxt_raw[:1]
        elif i + 1 < len(merged):
            nxt_c = "*"  # ardışık işaretleme: ayırıcı gerekir
        else:
            nxt_c = ""
        s = lead
        if not ok_before(prev_c) or (prev.endswith("\\") and not lead):
            s += "\\ "
        s += piece
        if not ok_after(nxt_c):
            s += "\\ "
        s += trail
        out.append(s)
    return "".join(out).rstrip()


BLOCKISH = re.compile(
    r"^(?:[-*+•‣⁃](?:\s|$)|\(?(?:\d+|[a-zA-Z]|[ivxlcdmIVXLCDM]+|#)[.)](?:\s|$)|:|\.\.(?:\s|$)|>>>|-{1,2}\w|\[)"
)
PUNCT_LINE = re.compile(r"^([!-/:-@\[-`{-~])\1+\s*$")


def guard_line(s):
    if BLOCKISH.match(s) or PUNCT_LINE.match(s):
        return "\\" + s
    return s


def render_inline(node):
    lines = [render_segments(segs) for segs in inline_segments(node)]
    lines = [l for l in lines]
    while lines and not lines[-1].strip():
        lines.pop()
    while lines and not lines[0].strip():
        lines.pop(0)
    return lines


def paragraph_block(node):
    lines = render_inline(node)
    if not lines:
        return []
    if len(lines) == 1:
        return [guard_line(lines[0].strip())]
    return ["| " + l.strip() if l.strip() else "|" for l in lines]


# ---------------------------------------------------------------- blocks
class Renderer:
    def __init__(self):
        self.stack = []  # açık başlıkların md seviyeleri

    def blocks(self, nodes):
        out = []
        for n in nodes:
            b = self.block(n)
            if b is None:
                continue
            if out and out[-1] != "":
                out.append("")
            out.extend(b)
        return out

    def block(self, n):
        t = n.type
        if t == "heading":
            return self.heading(n)
        if t == "paragraph":
            return paragraph_block(n.children[0]) or None
        if t in ("bullet_list", "ordered_list"):
            return self.lst(n)
        if t == "blockquote":
            return self.quote(n)
        if t == "table":
            return self.table(n)
        if t == "hr":
            return None
        if t in ("fence", "code_block"):
            body = n.content.rstrip("\n").split("\n")
            return ["::", ""] + ["   " + l for l in body]
        if t == "html_block":
            txt = n.content.strip()
            return [guard_line(esc(txt))] if txt else None
        raise SystemExit(f"bilinmeyen blok: {t}")

    def heading(self, n):
        level = int(n.tag[1])
        title = " ".join(render_inline(n.children[0])).strip()
        raw = plain(n.children[0]).strip()
        m = PAGE_RE.match("## " + raw) if level == 2 else None
        if m:
            return [f".. rubric:: {title}", "   :class: sayfa"]
        if level == 1:
            return [f".. rubric:: {title}"]
        while self.stack and self.stack[-1] >= level:
            self.stack.pop()
        self.stack.append(level)
        depth = len(self.stack)
        ch = SECTION_CHARS[min(depth, len(SECTION_CHARS)) - 1]
        title = guard_line(title)
        width = max(len(title), 4)
        return [title, ch * (width + 2)]

    def lst(self, n):
        ordered = n.type == "ordered_list"
        start = int(n.attrs.get("start", 1)) if ordered else 1
        out = []
        for i, item in enumerate(n.children):
            marker = f"{start + i}." if ordered else "-"
            ind = " " * (len(marker) + 1)
            body = self.blocks(item.children)
            if not body:
                out.append(marker)
                continue
            if body[0].startswith("| ") or body[0] == "|":
                # satır bloğu liste öğesinin ilk satırında olabilir
                pass
            out.append(f"{marker} {body[0]}")
            for l in body[1:]:
                out.append(ind + l if l else "")
        return out

    # blok alıntı etiketi -> (yönerge, sınıf)
    LABELS = [
        (re.compile(r"^NOT(LAR)?\b"), "note"),
        (re.compile(r"^UYARI\b"), "warning"),
        (re.compile(r"^SONUÇ OLARAK\b"), "tip"),
        (re.compile(r"^BİLGİLENDİRME\b"), "important"),
        (re.compile(r"^Soru[–-]Cevap\b"), "hint"),
    ]

    def quote(self, n):
        children = list(n.children)
        kind = title = None
        if children and children[0].type == "paragraph":
            inl = children[0].children[0]
            kids = [c for c in inl.children if not (c.type == "text" and not c.content)]
            first = kids[0] if kids else None
            if first is not None and first.type == "strong":
                label = plain(first).strip().rstrip(":").strip()
                for rx, k in self.LABELS:
                    if rx.match(label):
                        kind, title = k, tr_title(label)
                        break
                if kind:
                    # baştaki "ETİKET:" kısmını kaldır
                    kids = kids[1:]
                    while kids and kids[0].type in ("softbreak", "hardbreak"):
                        kids = kids[1:]
                    if kids and kids[0].type == "text":
                        kids[0].token.content = kids[0].content.lstrip(": ")
                        if not kids[0].content:
                            kids = kids[1:]
                    inl.children = kids
                    if not kids:
                        children = children[1:]
        body = self.blocks(children)
        if kind:
            head = [f".. admonition:: {esc(title)}", f"   :class: {kind}"]
            if not body:
                return head
            return head + [""] + ["   " + l if l else "" for l in body]
        if not body:
            return None
        # Önceki bloğa bağlanmaması için boş yorum + girintili blok alıntı
        return ["..", ""] + ["   " + l if l else "" for l in body]

    def table(self, n):
        rows = []
        for sect in n.children:  # thead / tbody
            for tr in sect.children:
                cells = []
                for td in tr.children:
                    inl = td.children[0] if td.children else None
                    if inl is None:
                        cells.append([])
                        continue
                    lines = [l.strip() for l in render_inline(inl)]
                    cells.append(self._cell(lines))
                rows.append(cells)
        ncols = max(len(r) for r in rows)
        out = [".. list-table::", "   :header-rows: 1", "   :class: longtable", ""]
        for r in rows:
            r = r + [[]] * (ncols - len(r))
            for ci, cell in enumerate(r):
                prefix = "   * - " if ci == 0 else "     - "
                if not cell:
                    out.append(prefix.rstrip())
                    continue
                out.append(prefix + cell[0])
                for l in cell[1:]:
                    out.append("       " + l if l else "")
        return out

    @staticmethod
    def _cell(lines):
        """<br> ile bölünmüş hücre: satır bloğu; '- ' ile başlayanlar madde."""
        lines = [l for l in lines]
        while lines and not lines[-1]:
            lines.pop()
        if not lines:
            return []
        if len(lines) == 1:
            return [guard_line(lines[0])]
        return ["| " + l if l else "|" for l in lines]


_TR_LOWER = str.maketrans({"I": "ı", "İ": "i"})


def tr_title(label):
    """'BİLGİLENDİRME (Quiz Sorusu – Sayfa 38)' -> 'Bilgilendirme (Quiz Sorusu – Sayfa 38)'"""
    def fix(word):
        if len(word) > 1 and word.isupper() and not re.fullmatch(r"[IVXLC]+", word):
            low = word.translate(_TR_LOWER).lower()
            head = {"i": "İ", "ı": "I"}.get(low[0], low[0].upper())
            return head + low[1:]
        return word
    return re.sub(r"\w+", lambda m: fix(m.group(0)), label)


def convert(chunk_lines):
    md = MarkdownIt("commonmark", {"html": True}).enable("table")
    tokens = md.parse("".join(chunk_lines))
    tree = SyntaxTreeNode(tokens)
    r = Renderer()
    return r.blocks(tree.children)


def title_block(title, char="#"):
    bar = char * (len(title) + 2)
    return [bar, " " + title, bar, ""]


DONEM_NAMES = {1: "1. Dönem (Güz)", 2: "2. Dönem (Bahar)"}


def main():
    lines = SRC.read_text(encoding="utf-8").splitlines(keepends=True)
    preface, weeks = split_weeks(lines)
    title = next(l[2:].strip() for l in lines if l.startswith("# "))

    index = title_block(title) + convert(preface) + [
        "",
        "Her sayfa bir ders haftasıdır; başlığın altındaki *Not sayfaları*",
        "satırı, özgün el yazısı notlardaki sayfa aralığını gösterir.",
        "",
        ".. toctree::",
        "   :maxdepth: 2",
        "   :caption: İçindekiler",
        "",
    ] + [f"   donem{d}/index" for d in sorted({w[0] for w in weeks})]
    (OUT / "index.rst").write_text("\n".join(index) + "\n", encoding="utf-8")

    for d in sorted({w[0] for w in weeks}):
        (OUT / f"donem{d}").mkdir(parents=True, exist_ok=True)
        idx = title_block(DONEM_NAMES.get(d, f"{d}. Dönem")) + [
            ".. toctree::", "   :maxdepth: 2", "   :glob:", "", "   [0-9]*"]
        (OUT / f"donem{d}" / "index.rst").write_text("\n".join(idx) + "\n", encoding="utf-8")

    for d, hafta, tarih, sayfa, chunk in weeks:
        page_title = f"{hafta} ({tarih})"
        body = convert(chunk)
        meta = [f".. rst-class:: hafta-meta", "", f"*Not sayfaları: {esc(sayfa)}*", ""]
        text = "\n".join(title_block(page_title) + meta + body).rstrip() + "\n"
        fname = f"donem{d}/{week_slug(hafta)}.rst"
        (OUT / fname).write_text(text, encoding="utf-8")
        print(f"{fname}  ({len(chunk)} md satırı)")


if __name__ == "__main__":
    main()
