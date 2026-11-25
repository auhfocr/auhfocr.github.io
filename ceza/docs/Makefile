SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = .
BUILDDIR      = _build

help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

# PDF (LaTeX gerektirmez, rinohtype): make pdf
VENV_SPHINX   ?= ../.venv/bin/sphinx-build
pdf:
	@$(VENV_SPHINX) -b rinoh "$(SOURCEDIR)" "$(BUILDDIR)/rinoh" $(SPHINXOPTS) $(O)
	@cp "$(BUILDDIR)/rinoh/ceza-hukuku-genel-hukumler.pdf" "../Ceza Hukuku Genel Hükümler Ders Notları (Sphinx).pdf"

.PHONY: help pdf Makefile

%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
