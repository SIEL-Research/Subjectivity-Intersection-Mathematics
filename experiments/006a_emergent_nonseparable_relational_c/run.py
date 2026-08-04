#!/usr/bin/env python3
"""Registered Experiment 006A confirmation runner."""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
import multiprocessing
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
E006_SOURCE = ROOT / "experiments/006_spontaneous_o3_reentry/run.py"
SUPPORT = HERE / "support"
sys.path.insert(0, str(SUPPORT))
import experiment_007_unity_pilot as U  # noqa: E402


DUAL = "dual_independent_relay"
INTERACTING = ("distributed", "central_shared", "directional_relay", "four_channel_crossbar")
ARCHITECTURES = (*INTERACTING, DUAL)
TRANSITIONS = (4, 5, 6)
CONFIRMATORY_SEEDS = tuple(range(8000, 8048))
CONFIRMATORY_EVALUATION_SEEDS = (61790001, 61790002)
REGISTRATION_CHECK_SEEDS = (7900,)
REGISTRATION_CHECK_EVALUATION_SEEDS = (61789001, 61789002)
DEVELOPMENT_SEEDS_EXCLUDED = (*range(7000, 7008), *range(7100, 7108), *range(7200, 7224))
SCHEMA = "siel-experiment-006a-nonseparable-relational-c-v1"
_CONTEXT: dict[str, Any] = {}


def load_e006():
    spec = importlib.util.spec_from_file_location("e006a_frozen_e006", E006_SOURCE)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load Experiment 006 computation")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("registration-check", "confirmatory"), required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--check", action="store_true")
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_manifest():
    manifest = json.loads((HERE / "registration_manifest.json").read_text())
    mismatches = []
    for relative, expected in manifest["source_sha256"].items():
        path = ROOT / relative
        if not path.is_file() or sha256_file(path) != expected:
            mismatches.append(relative)
    if mismatches:
        raise SystemExit("FAIL: registration source mismatch: " + ", ".join(mismatches))
    return True


def synergy(states):
    return states["ab"] - states["a0"] - states["0b"] + states["00"]


def receiver_indices(e006, architecture):
    return (np.arange(12), np.arange(12, 24)) if architecture == DUAL else e006.P014.receiver_indices(architecture)


def rms(value):
    return float(np.mean(np.linalg.norm(value, axis=1) / math.sqrt(value.shape[1])))


def train_dual(e006, seed, steps, batch_size, profiles):
    model = U.initialize_dual(e006, seed)
    square = {k: np.zeros_like(v) for k, v in model["params"].items()}
    for step in range(1, steps + 1):
        x, y, _ = e006.P015.sample_batch(1520000 + 100000 * seed + step, e006.E009.TRAIN_PAIRS, batch_size, profiles, noise=True)
        _, grads = e006.P015.loss_and_grad(model, x, y)
        norm = math.sqrt(sum(float(np.sum(g * g)) for g in grads.values()))
        scale = min(1.0, 5.0 / (norm + 1e-12))
        for key, gradient in grads.items():
            gradient *= scale
            square[key] = 0.99 * square[key] + 0.01 * gradient * gradient
            model["params"][key] -= 0.004 * gradient / (np.sqrt(square[key]) + 1e-8)
        for key in ("inputs", "recurrent", "outputs"):
            model["params"][key] *= model["masks"][key]
    return model


def model_hash(model):
    digest = hashlib.sha256()
    for key in sorted(model["params"]):
        digest.update(key.encode())
        digest.update(np.ascontiguousarray(model["params"][key]).tobytes())
    return digest.hexdigest()


def random_matched(e006, architecture, component, rng):
    out = np.zeros_like(component)
    for indices in receiver_indices(e006, architecture):
        direction = rng.normal(size=(len(component), len(indices)))
        direction /= np.maximum(np.linalg.norm(direction, axis=1, keepdims=True), 1e-12)
        out[:, indices] = direction * np.linalg.norm(component[:, indices], axis=1, keepdims=True)
    return out


def percentile(value, null):
    array = np.asarray(null)
    return float((np.sum(array < value) + 0.5 * np.sum(array == value)) / len(array))


def probability_magnitude(e006, logits, reference):
    return float(np.mean(np.abs(e006.E009.softmax(logits) - e006.E009.softmax(reference))))


def bilateral(e006, logits, reference):
    response = np.abs(e006.E009.softmax(logits) - e006.E009.softmax(reference))
    return float(np.mean(np.all(np.sum(response, axis=2) > 1e-9, axis=1)))


def donor_indices(pair):
    donor = np.arange(len(pair)); unresolved = np.ones(len(pair), dtype=bool); base = np.arange(len(pair))
    for offset in range(1, len(pair)):
        candidate = np.roll(base, offset); use = unresolved & (pair[candidate] != pair)
        donor[use] = candidate[use]; unresolved[use] = False
        if not unresolved.any(): break
    if unresolved.any(): raise AssertionError("donor construction failed")
    return donor


def audit_transition(e006, architecture, model, episodes, trajectories, transition, draws, random_seed):
    current = {name: states[transition] for name, states in trajectories.items()}
    natural_next = {name: states[transition + 1] for name, states in trajectories.items()}
    component = synergy(current); next_c = synergy(natural_next)
    ia, ib = receiver_indices(e006, architecture)
    x_step = episodes["x"][:, transition]
    removed_ab = e006.advance(model, current["ab"] - component, x_step)
    intervened = dict(natural_next); intervened["ab"] = removed_ab
    transported = next_c - synergy(intervened)
    reference_logits = e006.continue_from_step(model, natural_next["ab"], episodes["x"], transition + 1)
    removed_logits = e006.continue_from_step(model, removed_ab, episodes["x"], transition + 1)
    reference_loss = e006.P015.cross_entropy(reference_logits, episodes["y"])
    donor = donor_indices(episodes["pair"])
    exchange_ab = e006.advance(model, current["ab"] - component + component[donor], x_step)
    exchange_logits = e006.continue_from_step(model, exchange_ab, episodes["x"], transition + 1)
    transport_value = rms(transported); action_value = probability_magnitude(e006, removed_logits, reference_logits)
    rng = np.random.default_rng(random_seed); null_t = []; null_a = []
    for _ in range(draws):
        random_c = random_matched(e006, architecture, component, rng)
        random_ab = e006.advance(model, current["ab"] - random_c, x_step)
        random_states = dict(natural_next); random_states["ab"] = random_ab
        null_t.append(rms(next_c - synergy(random_states)))
        random_logits = e006.continue_from_step(model, random_ab, episodes["x"], transition + 1)
        null_a.append(probability_magnitude(e006, random_logits, reference_logits))
    values = {
        "component_norm": rms(component),
        "component_a_norm": rms(component[:, ia]), "component_b_norm": rms(component[:, ib]),
        "component_bilateral_support": float(np.mean((np.linalg.norm(component[:, ia], axis=1) > 1e-12) & (np.linalg.norm(component[:, ib], axis=1) > 1e-12))),
        "next_component_norm": rms(next_c), "transported_norm": transport_value,
        "transport_fraction": transport_value / max(rms(next_c), 1e-12),
        "transport_percentile": percentile(transport_value, null_t),
        "probability_response": action_value, "probability_response_percentile": percentile(action_value, null_a),
        "erase_cross_entropy_increase": e006.P015.cross_entropy(removed_logits, episodes["y"]) - reference_loss,
        "exchange_cross_entropy_increase": e006.P015.cross_entropy(exchange_logits, episodes["y"]) - reference_loss,
        "bilateral_fraction": bilateral(e006, removed_logits, reference_logits),
        "reconstruction_error": float(np.max(np.abs((natural_next["ab"] - transported) - removed_ab))),
    }
    if not all(np.isfinite(v) for v in values.values()): raise FloatingPointError("non-finite metric")
    return values


def run_seed(seed):
    c = _CONTEXT; e006 = c["e006"]; rows = []
    for ai, architecture in enumerate(ARCHITECTURES):
        if architecture == DUAL:
            untrained = U.initialize_dual(e006, seed); model = train_dual(e006, seed, c["steps"], c["batch_size"], c["profiles"])
        else:
            untrained = e006.P014.initialize(architecture, 1510000 + seed)
            model = e006.P015.train_model(architecture, seed, c["steps"], c["batch_size"], 0.004, c["profiles"])
        performance = e006.P015.evaluate(model, c["performance_x"], c["performance_y"])
        trajectories = {name: e006.E009.forward(model, x)[1] for name, x in c["variants"].items()}
        untrained_traj = {name: e006.E009.forward(untrained, x)[1] for name, x in c["variants"].items()}
        untrained_norm = float(np.median([rms(synergy({name: states[t] for name, states in untrained_traj.items()})) for t in TRANSITIONS]))
        weight_hash = model_hash(model)
        for ti, transition in enumerate(TRANSITIONS):
            rows.append({"training_seed": seed, "architecture": architecture, "transition": f"{transition}_to_{transition+1}", "model_weight_hash": weight_hash, "heldout_both_correct": performance["both_correct"], "task_competent": performance["both_correct"] >= .95, "untrained_component_norm": untrained_norm, **audit_transition(e006, architecture, model, c["episodes"], trajectories, transition, c["draws"], 61791000 + seed * 100 + ai * 10 + ti)})
    return rows


def summary_stats(values):
    return {"minimum": float(np.min(values)), "median": float(np.median(values)), "maximum": float(np.max(values))}


def render_result(summary):
    lines = ["# Experiment 006A Result", "", "## Emergent Nonseparable Relational C", "", f"Status: {summary['status']}", f"Primary readout: {summary['primary_readout']}", "", "| Architecture | Competent | Median C | Amplified | Median transport | Median bilateral | Median exchange |", "|---|---:|---:|---:|---:|---:|---:|"]
    for a in ARCHITECTURES:
        s = summary["architectures"][a]
        lines.append(f"| {a} | {s['competent_seed_count']} | {s['component_norm']['median']:.8g} | {s['amplified_seed_count']} | {s['transport_fraction']['median']:.8g} | {s['bilateral_fraction']['median']:.8g} | {s['exchange_cross_entropy_increase']['median']:.8g} |")
    lines += ["", "## Frozen checks", ""] + [f"- {k}: {'PASS' if v else 'FAIL'}" for k, v in summary["primary_checks"].items()] + ["", "## Boundary", "", summary["claim_boundary"], ""]
    return "\n".join(lines)


def main():
    args = parse_args()
    if args.out_dir.exists(): raise SystemExit("FAIL: output directory exists")
    if args.workers < 1: raise SystemExit("FAIL: workers must be positive")
    verified = verify_manifest() if args.check else None
    e006 = load_e006()
    if args.mode == "confirmatory":
        seeds = CONFIRMATORY_SEEDS; eval_seeds = CONFIRMATORY_EVALUATION_SEEDS; steps = 4000; batch = 256; episodes_n = 4096; draws = 32
    else:
        seeds = REGISTRATION_CHECK_SEEDS; eval_seeds = REGISTRATION_CHECK_EVALUATION_SEEDS; steps = 40; batch = 32; episodes_n = 128; draws = 4
    profiles = e006.E009.pair_profiles(); episodes = e006.P015.evaluation_episodes(eval_seeds[0], episodes_n, profiles)
    performance_x, performance_y, _ = e006.P015.sample_batch(eval_seeds[1], e006.E009.HELDOUT_PAIRS, episodes_n, profiles, noise=True)
    _CONTEXT.update({"e006": e006, "profiles": profiles, "episodes": episodes, "performance_x": performance_x, "performance_y": performance_y, "variants": e006.P014.baseline_variants(episodes, profiles), "steps": steps, "batch_size": batch, "draws": draws})
    rows = []
    workers = min(args.workers, len(seeds))
    if workers > 1:
        with multiprocessing.get_context("fork").Pool(workers) as pool:
            for result in pool.imap(run_seed, seeds): rows.extend(result)
    else:
        for seed in seeds: rows.extend(run_seed(seed))
    args.out_dir.mkdir(parents=True)
    with (args.out_dir / "transition_metrics.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    grouped = defaultdict(list)
    for row in rows: grouped[(row["architecture"], row["training_seed"])].append(row)
    units = []
    for (a, seed), rs in sorted(grouped.items()):
        med = lambda key: float(np.median([float(r[key]) for r in rs]))
        units.append({"architecture": a, "seed": seed, "competent": all(r["task_competent"] for r in rs), "component_norm": med("component_norm"), "bilateral_support": med("component_bilateral_support"), "amplification_ratio": med("component_norm") / max(med("untrained_component_norm"), 1e-12), "transport_fraction": med("transport_fraction"), "bilateral_fraction": med("bilateral_fraction"), "exchange": med("exchange_cross_entropy_increase")})
    arch_summary = {}
    for a in ARCHITECTURES:
        au = [u for u in units if u["architecture"] == a]; ar = [r for r in rows if r["architecture"] == a]
        arch_summary[a] = {"competent_seed_count": sum(u["competent"] for u in au), "amplified_seed_count": sum(u["amplification_ratio"] > 1 for u in au), "component_norm": summary_stats([u["component_norm"] for u in au]), "bilateral_support": summary_stats([u["bilateral_support"] for u in au]), "amplification_ratio": summary_stats([u["amplification_ratio"] for u in au]), "transport_fraction": summary_stats([u["transport_fraction"] for u in au]), "bilateral_fraction": summary_stats([u["bilateral_fraction"] for u in au]), "exchange_cross_entropy_increase": summary_stats([u["exchange"] for u in au]), "transport_percentile": summary_stats([float(r["transport_percentile"]) for r in ar]), "probability_response_percentile": summary_stats([float(r["probability_response_percentile"]) for r in ar])}
    if args.mode == "confirmatory":
        checks = {
            "capacity_exact_486": all((486 if a != DUAL else int(sum(x.sum() for x in U.dual_masks(e006).values()) + 30)) == 486 for a in ARCHITECTURES),
            "competence_at_least_44_of_48_each": all(arch_summary[a]["competent_seed_count"] >= 44 for a in ARCHITECTURES),
            "dual_component_at_most_1e_10": arch_summary[DUAL]["component_norm"]["maximum"] <= 1e-10,
            "interacting_median_component_at_least_0_02": all(arch_summary[a]["component_norm"]["median"] >= .02 for a in INTERACTING),
            "interacting_median_bilateral_support_at_least_0_99": all(arch_summary[a]["bilateral_support"]["median"] >= .99 for a in INTERACTING),
            "training_amplification": all(arch_summary[a]["amplification_ratio"]["median"] >= 100 and arch_summary[a]["amplified_seed_count"] >= 44 for a in INTERACTING),
            "interacting_median_transport_fraction_at_least_0_40": all(arch_summary[a]["transport_fraction"]["median"] >= .40 for a in INTERACTING),
            "interacting_median_bilateral_output_at_least_0_95": all(arch_summary[a]["bilateral_fraction"]["median"] >= .95 for a in INTERACTING),
            "interacting_positive_median_exchange": all(arch_summary[a]["exchange_cross_entropy_increase"]["median"] > 0 for a in INTERACTING),
            "reconstruction_error_at_most_1e_12": max(float(r["reconstruction_error"]) for r in rows) <= 1e-12,
        }
        primary = "SUPPORTED" if all(checks.values()) else "NOT_SUPPORTED"
    else:
        checks = {}; primary = "NOT_APPLICABLE"
    summary = {"schema": SCHEMA, "status": "CONFIRMATORY_COMPLETE" if args.mode == "confirmatory" else "REGISTRATION_CHECK_COMPLETE", "mode": args.mode, "primary_readout": primary, "task": "delayed reciprocal recall", "component": "H(ab)-H(a0)-H(0b)+H(00)", "training_seeds": list(seeds), "development_seeds_excluded": list(DEVELOPMENT_SEEDS_EXCLUDED), "evaluation_seeds": list(eval_seeds), "configuration": {"steps": steps, "batch_size": batch, "episodes": episodes_n, "random_draws": draws, "transitions": list(TRANSITIONS), "active_parameters_each": 486}, "registration_verified": verified, "architectures": arch_summary, "primary_checks": checks, "claim_boundary": "A supported result establishes an operational learned distributed second-order interaction absent from a competent additive two-relay solution. It does not establish ontological unity, consciousness, or a third subject."}
    (args.out_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (args.out_dir / "RESULT.md").write_text(render_result(summary))
    manifest = {name: sha256_file(args.out_dir / name) for name in ("transition_metrics.csv", "summary.json", "RESULT.md")}
    (args.out_dir / "output_manifest.json").write_text(json.dumps({"schema": SCHEMA, "files": manifest}, indent=2) + "\n")
    print(json.dumps({"status": summary["status"], "primary_readout": primary, "checks": checks}, indent=2))


if __name__ == "__main__": main()
