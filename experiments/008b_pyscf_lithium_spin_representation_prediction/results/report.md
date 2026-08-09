# Experiment 008B Result

Primary decision: **FULL_FACTORISED_GENERATOR_SUPPORTED**

- Observed Li-6/Li-7 interval ratio: `0.284012567335709`
- Full factorised prediction: `0.283993247420257`
- Nuclear-g-only control: `0.378657663227009`
- Representation-only control: `0.75`
- Full model log error: `6.80271749263816e-05`
- Clamped PySCF Li-6 prediction: `217.072535973768 MHz`
- Clamped PySCF Li-7 prediction: `764.358089305347 MHz`
- Li-6 absolute signed relative error: `0.0512857256506059`
- Li-7 absolute signed relative error: `0.05121421208511`
- Measurement SHA-256: `65b80eff5fbda9c11df5de97c6befda0ef65a823ad2666387f8400409d54e7bd`

The primary test asks whether the jointly generated nuclear-g and representation factors predict the raw lithium isotope interval ratio. The PySCF absolute intervals are mandatory secondary diagnostics.
