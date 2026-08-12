# Subjectivity-Intersection Mathematics Preprint

This directory contains the editable LaTeX source for the English public
working preprint series. The current draft is:

> Satoru Watanabe, *Subjectivity-Intersection Mathematics: Constitutive
> Closure and Stabilized O3 Return across Atomic, Molecular, and Cellular
> Systems*, Public Working Preprint v4.2 Draft, 13 August 2026.

The Version 4.2 DOI will be assigned at public release.

Preceding public version (v4.1) DOI:
[10.5281/zenodo.21877695](https://doi.org/10.5281/zenodo.21877695)

Previous public working version:
[10.5281/zenodo.21796491](https://doi.org/10.5281/zenodo.21796491)

The corresponding PDF is generated at:

```text
output/pdf/subjectivity-intersection-mathematics-preprint-v4-2-en-draft.pdf
```

## Status

This is a versioned public working preprint. Version 4.2 retains the formal
constitutive-closure structure and domain boundaries of Version 4.1, narrows
E011 to a held-out representation-covariance test inside one frozen reduced
bridge, and adds the independent cross-domain E012--E014 sequence. The two
preregistered negative decisions are preserved: E012 rejected uniform
mismatch specificity and E013 rejected common absolute calibration. E014 then
prospectively supported stabilized O3-return specificity across independently
executed atomic, molecular, and cellular targets without a shared scalar
mediator. A compression ladder separates source construction, intervention,
readout, and the cross-domain sign invariant.

## Build

Run XeLaTeX from the repository root:

```text
xelatex -jobname=subjectivity-intersection-mathematics-preprint-v4-2-en-draft \
  -output-directory=output/pdf \
  docs/preprint/SUBJECTIVITY_INTERSECTION_MATHEMATICS_PREPRINT_V4_2_EN.tex
```

Run the command twice to stabilize the table of contents and references. The
PDF is rendered page by page for visual inspection before release.

## Rights

Copyright (c) 2026 Satoru Watanabe. All rights reserved.
