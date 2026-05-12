PANDOC ?= pandoc
DOCS := $(wildcard *.md)
LONG_DOCS := $(filter-out README.md,$(DOCS))
HTML_OUT := _build/html
PDF_OUT := _build/pdf

.PHONY: build-html build-pdf clean

build-html:
	@mkdir -p $(HTML_OUT)
	@for f in $(LONG_DOCS); do \
		name="$${f%.md}"; \
		$(PANDOC) "$${f}" -s -o "$(HTML_OUT)/$${name}.html"; \
		echo "built $(HTML_OUT)/$${name}.html"; \
	done

build-pdf:
	@mkdir -p $(PDF_OUT)
	@for f in $(LONG_DOCS); do \
		name="$${f%.md}"; \
		$(PANDOC) "$${f}" -s -o "$(PDF_OUT)/$${name}.pdf"; \
		echo "built $(PDF_OUT)/$${name}.pdf"; \
	done

clean:
	rm -rf _build
