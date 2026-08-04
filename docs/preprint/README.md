# Subjectivity-Intersection Mathematics Preprint

This directory contains the editable LaTeX source for the English public
working preprint:

> Satoru Watanabe, *Subjectivity-Intersection Mathematics: Relational
> Generation, Emergent C, and Self-Re-entry*, Public Working Preprint v2.0
> Draft, 4 August 2026.

Reserved DOI: [10.5281/zenodo.21791244](https://doi.org/10.5281/zenodo.21791244)

Previous citable version: [10.5281/zenodo.21781152](https://doi.org/10.5281/zenodo.21781152)

The corresponding PDF is generated at:

```text
output/pdf/subjectivity-intersection-mathematics-preprint-v2-draft.pdf
```

## Status

This is a versioned public working preprint. Version 2.0 Draft reports the
framework and the staged preregistered computational evidence through
Experiment 006A, including spontaneous relational-carrier formation, causal
self-re-entry, architecture-dependent identifiability, and joint
nonseparability. It does not claim ontological O3, consciousness, or a third
subject.

## Build

Run XeLaTeX twice from the repository root:

```text
xelatex -output-directory=output/pdf \
  docs/preprint/SUBJECTIVITY_INTERSECTION_MATHEMATICS_PREPRINT_V2.tex

xelatex -output-directory=output/pdf \
  docs/preprint/SUBJECTIVITY_INTERSECTION_MATHEMATICS_PREPRINT_V2.tex
```

The public PDF was visually inspected after rendering all pages. The source
PDF used for translation was not reused as a production artifact because its
embedded Japanese font was not rendered reliably outside Apple PDF tools.

## Rights

Copyright (c) 2026 Satoru Watanabe. All rights reserved.
