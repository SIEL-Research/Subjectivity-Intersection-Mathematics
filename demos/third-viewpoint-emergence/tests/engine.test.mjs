import assert from "node:assert/strict";
import test from "node:test";
import { createModel, extractRelation, runExperiment, SeededRandom } from "../experiment.worker.js";
import { config } from "../config.js";

test("the model contains A and B but no installed C or O3", () => {
  const model = createModel(4, 3, new SeededRandom(1), false);
  assert.equal(model.C, undefined);
  assert.equal(model.O3, undefined);
  assert.equal(model.carrier, undefined);
});

test("the relational trace is exact inclusion-exclusion", () => {
  const state = (a, b) => ({ a: Float64Array.from(a), b: Float64Array.from(b) });
  const trace = extractRelation(
    state([4, 5], [6, 7]),
    state([1, 2], [2, 2]),
    state([2, 1], [1, 3]),
    state([0, 1], [0, 1])
  );
  assert.deepEqual(Array.from(trace), [1, 3, 3, 3]);
});

test("a tiny live run computes bilateral intervention, exchange, and re-entry", async () => {
  const tiny = structuredClone(config);
  Object.assign(tiny.modes.quick, {
    hiddenDimension: 3,
    symbolClasses: 2,
    randomControls: 3,
    epochs: 3,
    trainEpisodes: 8,
    validationEpisodes: 6,
    interventionEpisodes: 4,
    exchangeEpisodes: 4
  });
  Object.assign(tiny.thresholds, {
    taskBothCorrectMin: 0,
    independentRelationRatioMax: 1,
    bilateralCeIncreaseMin: -1,
    randomPercentileMin: 0,
    crossPairDegradationMin: -1,
    transportedFractionMin: 0,
    transportTransitionsRequired: 0,
    gradientNormAbort: 1000
  });
  Object.assign(tiny.thresholds006A, {
    taskBothCorrectMin: 0,
    interactingComponentMin: 0,
    bilateralSupportMin: 0,
    transportedFractionMin: 0,
    transportTransitionsRequired: 0,
    bilateralOutputResponseMin: 0,
    crossPairDegradationMin: -1,
    reconstructionErrorMax: 1
  });
  const output = await runExperiment({ config: tiny, mode: "quick", seed: 42 });
  const joint = output.primary.experiment006A.interacting;
  assert.equal(output.primary.architecture.thirdState, false);
  assert.equal(output.primary.training.carrierSpecificLoss, false);
  assert.equal(joint.transport.length, 3);
  assert.equal(joint.reconstruction.length, 3);
  assert.ok(Number.isFinite(joint.deletion.nextStateDifference));
  assert.ok(Number.isFinite(joint.crossPairEffect));
});
