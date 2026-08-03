# Subjectivity-Intersection Mathematics Preprint

This directory contains the editable LaTeX source for the English public
working preprint:

> Satoru Watanabe, *Subjectivity-Intersection Mathematics: A Mathematical
> Research Program for Relational Generation*, Public Working Preprint v1.0,
> 4 August 2026.

DOI: [10.5281/zenodo.21781152](https://doi.org/10.5281/zenodo.21781152)

The corresponding PDF is generated at:

```text
output/pdf/subjectivity-intersection-mathematics-preprint-v1.pdf
```

## Status

This is a versioned public working preprint. It reports the framework and the
registered computational evidence through Experiment 006R. Experiment 007 and
later joint work are outside its scope.

## Build

Run XeLaTeX twice from the repository root:

```text
xelatex -output-directory=output/pdf \
  docs/preprint/SUBJECTIVITY_INTERSECTION_MATHEMATICS_PREPRINT_V1.tex

xelatex -output-directory=output/pdf \
  docs/preprint/SUBJECTIVITY_INTERSECTION_MATHEMATICS_PREPRINT_V1.tex
```

The public PDF was visually inspected after rendering all pages. The source
PDF used for translation was not reused as a production artifact because its
embedded Japanese font was not rendered reliably outside Apple PDF tools.

## Rights

Copyright (c) 2026 Satoru Watanabe. All rights reserved.
