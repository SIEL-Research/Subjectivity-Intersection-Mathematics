# Native-energy readout comparison

| Method | Pass fraction | Median margin | Minimum margin | All-pass profiles | Positive-majority profiles |
|---|---:|---:|---:|---:|---:|
| exact_minimum | 1.000000 | 0.556250 | 0.021875 | 58/58 | 58/58 |
| boltzmann_temperature | 1.000000 | 0.678230 | 0.131830 | 58/58 | 58/58 |
| native_depth_exponential | 1.000000 | 0.213137 | 0.013066 | 58/58 | 58/58 |
| native_depth_linear | 1.000000 | 0.247562 | 0.013328 | 58/58 | 58/58 |
| first_gap_exponential | 1.000000 | 0.626204 | 0.056571 | 58/58 | 58/58 |
| energy_rank | 1.000000 | 0.265920 | 0.097049 | 58/58 | 58/58 |
| native_quantile_0.10 | 1.000000 | 0.745000 | 0.112500 | 58/58 | 58/58 |
| native_quantile_0.20 | 0.983908 | 0.669687 | -0.140625 | 56/58 | 57/58 |
| native_quantile_0.25 | 0.975862 | 0.555625 | -0.171875 | 53/58 | 58/58 |
| native_quantile_0.33 | 0.905747 | 0.453125 | -0.171875 | 51/58 | 52/58 |

All methods were compared after E013 and are exploratory.
