#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Registration-safe tests for Experiment 007C."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path


HERE = Path(__file__).resolve().parent
RUN_PATH = HERE / "run.py"
D12_DEFAULT = Path(
    "/Users/satoru/Documents/Codex/2026-08-04/d12rg-riemann-readonly"
)


def load_runner():
    spec = importlib.util.spec_from_file_location("e007c_run", RUN_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load runner")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    runner = load_runner()
    dummy = {
        "primitive_id": "PX",
        "input_types_list": ["X"],
        "output_type": "X",
        "linearity": "linear",
        "direction": "none",
    }
    assert runner.parameter_free_unary(dummy)
    assert runner.role_candidates(
        [dummy],
        "PI_ADM",
        {
            "arity": 1,
            "same_input_output_type": True,
            "linearity": "linear",
            "parameter_free": True,
            "idempotent": True,
        },
    ) == []

    with tempfile.TemporaryDirectory(prefix="e007c-registration-") as temporary:
        out_dir = Path(temporary)
        subprocess.run(
            [
                sys.executable,
                str(RUN_PATH),
                "--mode",
                "registration-check",
                "--d12rg-repo",
                str(D12_DEFAULT),
                "--out-dir",
                str(out_dir),
                "--check",
            ],
            check=True,
        )
        record = json.loads(
            (out_dir / "registration_check.json").read_text(encoding="utf-8")
        )
        assert record["status"] == "REGISTRATION_VERIFIED_NOT_EXECUTED"
        assert not (out_dir / "RESULT.md").exists()
    print("registration-safe tests = PASS")


if __name__ == "__main__":
    main()
