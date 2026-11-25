"""Küçük Sphinx uzantısı: notlara özgü işaretlerin PDF görünümü.

``.. rubric:: Sayfa 12 (Not Sayfa: 18)`` + ``:class: sayfa`` biçimindeki özgün
not sayfası işaretleri LaTeX'te varsayılan olarak ``\\subsubsection*`` olur;
bunları sağa yaslı küçük bir işarete (``\\AUsayfaIsareti``) çeviriyoruz.
HTML tarafında aynı işaretler CSS ile biçimlenir (``p.rubric.sayfa``).
"""

from docutils import nodes


def _latex_kacis(metin: str) -> str:
    for a, b in (("\\", r"\textbackslash{}"), ("&", r"\&"), ("%", r"\%"),
                 ("$", r"\$"), ("#", r"\#"), ("_", r"\_"), ("{", r"\{"),
                 ("}", r"\}"), ("~", r"\textasciitilde{}"), ("^", r"\^{}")):
        metin = metin.replace(a, b)
    return metin


def _sayfa_isaretleri(app, doctree, docname):
    if app.builder.format != "latex":
        return
    for rubric in list(doctree.findall(nodes.rubric)):
        if "sayfa" in rubric.get("classes", []):
            ham = nodes.raw(
                "", rf"\AUsayfaIsareti{{{_latex_kacis(rubric.astext())}}}" + "\n",
                format="latex",
            )
            rubric.replace_self(ham)


def setup(app):
    app.connect("doctree-resolved", _sayfa_isaretleri)
    return {"parallel_read_safe": True, "parallel_write_safe": True}
