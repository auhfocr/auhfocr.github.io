# Sphinx Makefile — kullanım: make html | make latexpdf | make clean
SPHINXBUILD ?= $(if $(wildcard .venv/bin/python),.venv/bin/python -m sphinx,sphinx-build)
SPHINXOPTS  ?=
SOURCEDIR    = .
BUILDDIR     = _build

help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS)

.PHONY: help Makefile

%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS)
