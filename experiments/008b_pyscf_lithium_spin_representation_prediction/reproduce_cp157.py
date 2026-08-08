#!/usr/bin/env python3
"""Optionally reproduce the frozen CP-157 PySCF electronic coefficient."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import math
import warnings

import numpy as np
from pyscf import gto, scf
from pyscf.data.gyro import get_nuc_g_factor

warnings.filterwarnings("ignore", message="Module .* is under testing")
warnings.filterwarnings("ignore", message="Module infrared is not fully tested")

from pyscf.prop.hfc import uhf as uhf_hfc  # noqa: E402


FROZEN_COEFFICIENT_MHZ_PER_G = 176.04278247339448
PROPERTIES_SOURCE_COMMIT = "4eee5a430fb47eca5962f36fdcaf75c2b87e7ede"


def reproduce() -> dict[str, object]:
    basis = {"Li": gto.uncontract(gto.basis.load("cc-pCVQZ", "Li"))}
    molecule = gto.M(
        atom="Li 0 0 0",
        basis=basis,
        charge=0,
        spin=1,
        symmetry=False,
        verbose=0,
    )
    mean_field = scf.UHF(molecule)
    mean_field.conv_tol = 1e-12
    mean_field.max_cycle = 100
    mean_field.kernel()
    density = np.asarray(mean_field.make_rdm1(), dtype=float)
    hfc_object = uhf_hfc.HFC(mean_field)
    tensor = np.asarray(uhf_hfc.make_fcdip(hfc_object, density), dtype=float)[0]
    coefficient = float(np.trace(tensor / get_nuc_g_factor("Li")) / 3.0)
    relative_error = abs(coefficient / FROZEN_COEFFICIENT_MHZ_PER_G - 1.0)
    return {
        "pyscf_version": importlib.metadata.version("pyscf"),
        "pyscf_properties_version": importlib.metadata.version("pyscf-properties"),
        "registered_properties_source_commit": PROPERTIES_SOURCE_COMMIT,
        "scf_converged": bool(mean_field.converged),
        "calculated_hfc_per_nuclear_g_mhz": coefficient,
        "frozen_hfc_per_nuclear_g_mhz": FROZEN_COEFFICIENT_MHZ_PER_G,
        "relative_error": relative_error,
        "reproduction_pass": bool(mean_field.converged and relative_error <= 1e-10),
        "target_hyperfine_frequencies_loaded": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = reproduce()
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("PASS" if result["reproduction_pass"] else "FAIL")
        print("HFC/g = %.15g MHz" % result["calculated_hfc_per_nuclear_g_mhz"])
    return 0 if result["reproduction_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
