# Subjectivity-Intersection Mathematics Preprint

This directory contains the editable LaTeX source for the English public
working preprint:

> Satoru Watanabe, *Subjectivity-Intersection Mathematics: Perspective
> Intersection, Emergent O3, and Self-Re-entry*, Public Working Preprint v3.0
> Draft, 5 August 2026.

Reserved DOI: [10.5281/zenodo.21796460](https://doi.org/10.5281/zenodo.21796460)

Previous citable version: [10.5281/zenodo.21791244](https://doi.org/10.5281/zenodo.21791244)

The corresponding PDF is generated at:

```text
output/pdf/subjectivity-intersection-mathematics-preprint-v3-draft.pdf
```

## Status

This is a versioned public working preprint. Version 3.0 reorganizes the
framework around reciprocal perspective intersection. It identifies the learned
nonseparable C as a distributed operational third perspective, O3, under an
explicit functional definition of perspective, and reports the staged
preregistered evidence through Experiment 006A. The theoretical identification
is distinguished from the preregistered 006A decision and from claims about
phenomenal experience or independent subjecthood. A dedicated section cites
the Subjectivity Intersection Ontology preprint and states both the structural
bridge and the remaining difference between its ontological prototype and the
computational operational form.

## Build

Run XeLaTeX twice from the repository root:

```text
xelatex -output-directory=output/pdf \
  docs/preprint/SUBJECTIVITY_INTERSECTION_MATHEMATICS_PREPRINT_V3.tex

xelatex -output-directory=output/pdf \
  docs/preprint/SUBJECTIVITY_INTERSECTION_MATHEMATICS_PREPRINT_V3.tex
```

The public PDF was visually inspected after rendering all pages. The source
PDF used for translation was not reused as a production artifact because its
embedded Japanese font was not rendered reliably outside Apple PDF tools.

## Rights

Copyright (c) 2026 Satoru Watanabe. All rights reserved.
