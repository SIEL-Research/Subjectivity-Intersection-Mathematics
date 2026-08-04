/*
 * Emergent Third Viewpoint live numerical engine.
 * There is deliberately no C/O3/shared-carrier state and no carrier loss.
 * The only learned objective is reciprocal cross-entropy recall.
 */

let stopRequested = false;

export class SeededRandom {
  constructor(seed) {
    this.state = (Number(seed) >>> 0) || 0x6d2b79f5;
    this.spare = null;
  }
  next() {
    let t = (this.state += 0x6d2b79f5);
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  }
  int(max) { return Math.floor(this.next() * max); }
  normal() {
    if (this.spare !== null) { const s = this.spare; this.spare = null; return s; }
    const u = Math.max(this.next(), 1e-12);
    const v = this.next();
    const mag = Math.sqrt(-2 * Math.log(u));
    this.spare = mag * Math.sin(2 * Math.PI * v);
    return mag * Math.cos(2 * Math.PI * v);
  }
  shuffle(items) {
    for (let i = items.length - 1; i > 0; i--) {
      const j = this.int(i + 1);
      [items[i], items[j]] = [items[j], items[i]];
    }
    return items;
  }
}

const zeros = (n) => new Float64Array(n);
const clone = (x) => Float64Array.from(x);
const addScaled = (a, b, s) => { for (let i = 0; i < a.length; i++) a[i] += b[i] * s; };
const dot = (a, b) => { let x = 0; for (let i = 0; i < a.length; i++) x += a[i] * b[i]; return x; };
export const vectorNorm = (a) => Math.sqrt(dot(a, a));
export const cosine = (a, b) => {
  const den = vectorNorm(a) * vectorNorm(b);
  return den > 1e-12 ? dot(a, b) / den : 0;
};
const mean = (a) => a.length ? a.reduce((s, x) => s + x, 0) / a.length : 0;
const finite = (x) => Number.isFinite(x) && !Number.isNaN(x);
const round = (x, n = 10) => Number(x.toFixed(n));

function matVec(m, v, rows, cols) {
  const out = zeros(rows);
  for (let r = 0; r < rows; r++) {
    let s = 0;
    const off = r * cols;
    for (let c = 0; c < cols; c++) s += m[off + c] * v[c];
    out[r] = s;
  }
  return out;
}

function matTVec(m, v, rows, cols) {
  const out = zeros(cols);
  for (let r = 0; r < rows; r++) {
    const vr = v[r];
    const off = r * cols;
    for (let c = 0; c < cols; c++) out[c] += m[off + c] * vr;
  }
  return out;
}

function outerAdd(target, a, b) {
  const cols = b.length;
  for (let r = 0; r < a.length; r++) {
    const off = r * cols;
    for (let c = 0; c < cols; c++) target[off + c] += a[r] * b[c];
  }
}

function softmax(logits) {
  let mx = -Infinity;
  for (const x of logits) mx = Math.max(mx, x);
  const p = zeros(logits.length);
  let z = 0;
  for (let i = 0; i < logits.length; i++) { p[i] = Math.exp(logits[i] - mx); z += p[i]; }
  for (let i = 0; i < p.length; i++) p[i] /= z;
  return p;
}

function argmax(x) {
  let k = 0;
  for (let i = 1; i < x.length; i++) if (x[i] > x[k]) k = i;
  return k;
}

function parameterKeys(independent) {
  return independent
    ? ["WAA", "PAA", "WBB", "PBB", "UA", "UB", "bA", "bB", "VA", "VB"]
    : ["WAA", "WAB", "WBB", "WBA", "UA", "UB", "bA", "bB", "VA", "VB"];
}

export function createModel(d, k, rng, independent = false, dualRelay = false) {
  const model = { d, k, independent, dualRelay };
  const recurrentScale = 0.62 / Math.sqrt(d);
  const inputScale = 0.75 / Math.sqrt(k);
  const outputScale = 0.55 / Math.sqrt(d);
  const matrix = (n, scale) => Float64Array.from({ length: n }, () => rng.normal() * scale);
  model.WAA = matrix(d * d, recurrentScale);
  model.WBB = matrix(d * d, recurrentScale);
  if (independent) {
    model.PAA = matrix(d * d, recurrentScale);
    model.PBB = matrix(d * d, recurrentScale);
  } else {
    model.WAB = matrix(d * d, recurrentScale);
    model.WBA = matrix(d * d, recurrentScale);
  }
  model.UA = matrix(d * k, inputScale);
  model.UB = matrix(d * k, inputScale);
  model.bA = zeros(d);
  model.bB = zeros(d);
  model.VA = matrix(k * d, outputScale);
  model.VB = matrix(k * d, outputScale);
  return model;
}

function state(a, b) { return { a, b }; }
function cloneState(s) { return state(clone(s.a), clone(s.b)); }
function concatState(s) { return Float64Array.from([...s.a, ...s.b]); }
function splitState(v, d) { return state(v.slice(0, d), v.slice(d)); }

function step(model, prev, symbolA, symbolB, flags = { ab: true, ba: true }) {
  const { d, k, independent, dualRelay } = model;
  const za = matVec(model.WAA, prev.a, d, d);
  const zb = matVec(model.WBB, prev.b, d, d);
  const incomingA = independent ? matVec(model.PAA, prev.a, d, d)
    : flags.ab ? matVec(model.WAB, prev.b, d, d) : zeros(d);
  const incomingB = independent ? matVec(model.PBB, prev.b, d, d)
    : flags.ba ? matVec(model.WBA, prev.a, d, d) : zeros(d);
  for (let i = 0; i < d; i++) {
    za[i] += incomingA[i] + model.bA[i];
    zb[i] += incomingB[i] + model.bB[i];
    const inputA = dualRelay ? symbolB : symbolA;
    const inputB = dualRelay ? symbolA : symbolB;
    if (inputA >= 0) za[i] += model.UA[i * k + inputA];
    if (inputB >= 0) zb[i] += model.UB[i * k + inputB];
    za[i] = Math.tanh(za[i]);
    zb[i] = Math.tanh(zb[i]);
  }
  return state(za, zb);
}

function sequenceInputs(config, episode) {
  const total = config.sequence.inputSteps + config.sequence.interactionSteps + config.sequence.delaySteps;
  return Array.from({ length: total }, (_, t) => t < config.sequence.inputSteps
    ? [episode.sA, episode.sB] : [-1, -1]);
}

export function forward(model, episode, config, flags = { ab: true, ba: true }, initial = null, inputs = null) {
  const seq = inputs || sequenceInputs(config, episode);
  const states = [initial ? cloneState(initial) : state(zeros(model.d), zeros(model.d))];
  for (const [sA, sB] of seq) states.push(step(model, states.at(-1), sA, sB, flags));
  const final = states.at(-1);
  const pA = softmax(matVec(model.VA, final.a, model.k, model.d));
  const pB = softmax(matVec(model.VB, final.b, model.k, model.d));
  const ceA = -Math.log(Math.max(pA[episode.sB], 1e-12));
  const ceB = -Math.log(Math.max(pB[episode.sA], 1e-12));
  return { states, pA, pB, ceA, ceB, correctA: argmax(pA) === episode.sB, correctB: argmax(pB) === episode.sA };
}

function gradients(model, episode, config) {
  const out = forward(model, episode, config);
  const g = {};
  for (const key of parameterKeys(model.independent)) g[key] = zeros(model[key].length);
  const dLogA = clone(out.pA); dLogA[episode.sB] -= 1;
  const dLogB = clone(out.pB); dLogB[episode.sA] -= 1;
  outerAdd(g.VA, dLogA, out.states.at(-1).a);
  outerAdd(g.VB, dLogB, out.states.at(-1).b);
  let dhA = matTVec(model.VA, dLogA, model.k, model.d);
  let dhB = matTVec(model.VB, dLogB, model.k, model.d);
  const seq = sequenceInputs(config, episode);
  for (let t = seq.length - 1; t >= 0; t--) {
    const cur = out.states[t + 1];
    const prev = out.states[t];
    const dzA = zeros(model.d), dzB = zeros(model.d);
    for (let i = 0; i < model.d; i++) {
      dzA[i] = dhA[i] * (1 - cur.a[i] * cur.a[i]);
      dzB[i] = dhB[i] * (1 - cur.b[i] * cur.b[i]);
      g.bA[i] += dzA[i]; g.bB[i] += dzB[i];
    }
    outerAdd(g.WAA, dzA, prev.a);
    outerAdd(g.WBB, dzB, prev.b);
    if (model.independent) {
      outerAdd(g.PAA, dzA, prev.a); outerAdd(g.PBB, dzB, prev.b);
    } else {
      outerAdd(g.WAB, dzA, prev.b); outerAdd(g.WBA, dzB, prev.a);
    }
    const [sA, sB] = seq[t];
    const inputA = model.dualRelay ? sB : sA;
    const inputB = model.dualRelay ? sA : sB;
    if (inputA >= 0) for (let i = 0; i < model.d; i++) g.UA[i * model.k + inputA] += dzA[i];
    if (inputB >= 0) for (let i = 0; i < model.d; i++) g.UB[i * model.k + inputB] += dzB[i];
    const nextA = matTVec(model.WAA, dzA, model.d, model.d);
    const nextB = matTVec(model.WBB, dzB, model.d, model.d);
    if (model.independent) {
      addScaled(nextA, matTVec(model.PAA, dzA, model.d, model.d), 1);
      addScaled(nextB, matTVec(model.PBB, dzB, model.d, model.d), 1);
    } else {
      addScaled(nextA, matTVec(model.WBA, dzB, model.d, model.d), 1);
      addScaled(nextB, matTVec(model.WAB, dzA, model.d, model.d), 1);
    }
    dhA = nextA; dhB = nextB;
  }
  let norm2 = 0;
  for (const key of parameterKeys(model.independent)) for (const x of g[key]) norm2 += x * x;
  return { g, loss: out.ceA + out.ceB, norm: Math.sqrt(norm2) };
}

function evaluate(model, episodes, config) {
  let ceA = 0, ceB = 0, a = 0, b = 0, both = 0;
  for (const ep of episodes) {
    const x = forward(model, ep, config);
    ceA += x.ceA; ceB += x.ceB;
    a += x.correctA; b += x.correctB; both += x.correctA && x.correctB;
  }
  const n = episodes.length;
  return { ceA: ceA / n, ceB: ceB / n, accuracyA: a / n, accuracyB: b / n, bothCorrect: both / n };
}

async function trainModel(model, episodes, validation, config, rng, emit, label) {
  const keys = parameterKeys(model.independent);
  const m = {}, v = {};
  for (const key of keys) { m[key] = zeros(model[key].length); v[key] = zeros(model[key].length); }
  const history = [];
  let update = 0;
  const batchSize = Math.min(16, episodes.length);
  for (let epoch = 1; epoch <= config.mode.epochs; epoch++) {
    if (stopRequested) throw new Error("STOPPED");
    const order = rng.shuffle(Array.from({ length: episodes.length }, (_, i) => i));
    let epochLoss = 0, epochNorm = 0, batches = 0;
    for (let p = 0; p < order.length; p += batchSize) {
      const aggregate = {};
      for (const key of keys) aggregate[key] = zeros(model[key].length);
      let batchLoss = 0;
      const end = Math.min(p + batchSize, order.length);
      for (let q = p; q < end; q++) {
        const item = gradients(model, episodes[order[q]], config);
        batchLoss += item.loss;
        for (const key of keys) addScaled(aggregate[key], item.g[key], 1 / (end - p));
      }
      let norm2 = 0;
      for (const key of keys) for (const x of aggregate[key]) norm2 += x * x;
      let gradNorm = Math.sqrt(norm2);
      if (!finite(gradNorm) || gradNorm > config.thresholds.gradientNormAbort) throw new Error("GRADIENT_EXPLOSION");
      const clip = Math.min(1, 5 / Math.max(gradNorm, 1e-12));
      update++;
      for (const key of keys) {
        const w = model[key], gg = aggregate[key];
        for (let i = 0; i < w.length; i++) {
          const gi = gg[i] * clip;
          m[key][i] = 0.9 * m[key][i] + 0.1 * gi;
          v[key][i] = 0.999 * v[key][i] + 0.001 * gi * gi;
          const mh = m[key][i] / (1 - Math.pow(0.9, update));
          const vh = v[key][i] / (1 - Math.pow(0.999, update));
          w[i] -= config.mode.learningRate * mh / (Math.sqrt(vh) + 1e-8);
        }
      }
      epochLoss += batchLoss / (end - p);
      epochNorm += gradNorm;
      batches++;
    }
    const val = evaluate(model, validation, config);
    const point = { epoch, loss: epochLoss / batches, gradientNorm: epochNorm / batches, ...val };
    history.push(point);
    if (epoch === 1 || epoch % 2 === 0 || epoch === config.mode.epochs) emit({ type: "progress", phase: label, ...point });
    await new Promise((resolve) => setTimeout(resolve, 0));
  }
  return history;
}

export function makeDataset(k, counts, seed) {
  const names = ["training", "validation", "intervention", "exchange"];
  const result = {};
  let globalId = 0;
  names.forEach((name, splitIndex) => {
    const rng = new SeededRandom((seed + Math.imul(splitIndex + 1, 0x9e3779b9)) >>> 0);
    const base = [];
    for (let a = 0; a < k; a++) for (let b = 0; b < k; b++) base.push([a, b]);
    const episodes = [];
    while (episodes.length < counts[splitIndex]) {
      for (const [sA, sB] of rng.shuffle(base.map((x) => [...x]))) {
        if (episodes.length >= counts[splitIndex]) break;
        episodes.push({ id: `${name}-${globalId++}`, sA, sB, split: name });
      }
    }
    result[name] = episodes;
  });
  return result;
}

export function extractRelation(full, aOnly, bOnly, zero) {
  const f = concatState(full), a = concatState(aOnly), b = concatState(bOnly), z = concatState(zero);
  const r = zeros(f.length);
  for (let i = 0; i < r.length; i++) r[i] = f[i] - a[i] - b[i] + z[i];
  return r;
}

function branchesAt(model, ep, config, index) {
  const full = forward(model, ep, config, { ab: true, ba: true }).states[index];
  const aOnly = forward(model, ep, config, { ab: false, ba: true }).states[index];
  const bOnly = forward(model, ep, config, { ab: true, ba: false }).states[index];
  const zero = forward(model, ep, config, { ab: false, ba: false }).states[index];
  return { full, aOnly, bOnly, zero, relation: extractRelation(full, aOnly, bOnly, zero) };
}

function maskedInputs(config, ep, includeA, includeB) {
  const total = config.sequence.inputSteps + config.sequence.interactionSteps + config.sequence.delaySteps;
  return Array.from({ length: total }, (_, t) => t < config.sequence.inputSteps
    ? [includeA ? ep.sA : -1, includeB ? ep.sB : -1] : [-1, -1]);
}

// Experiment 006A miniature extractor: the recurrent rules stay identical;
// only the presence of A's and B's inputs changes across ab/a0/0b/00.
function jointBranchesAt(model, ep, config, index) {
  const run = (includeA, includeB) => forward(
    model, ep, config, { ab: true, ba: true }, null,
    maskedInputs(config, ep, includeA, includeB),
  ).states[index];
  const full = run(true, true);
  const aOnly = run(true, false);
  const bOnly = run(false, true);
  const zero = run(false, false);
  return { full, aOnly, bOnly, zero, relation: extractRelation(full, aOnly, bOnly, zero) };
}

function jointComponentStats(model, episodes, config) {
  const rows = episodes.map((ep) => {
    const r = jointBranchesAt(model, ep, config, config.interventionStateIndex).relation;
    return {
      norm: vectorNorm(r),
      normA: vectorNorm(r.slice(0, model.d)),
      normB: vectorNorm(r.slice(model.d)),
    };
  });
  return {
    relationNorm: mean(rows.map((row) => row.norm)),
    relationNormMax: Math.max(...rows.map((row) => row.norm)),
    bilateralSupportFraction: mean(rows.map((row) => Number(row.normA > 1e-10 && row.normB > 1e-10))),
  };
}

function rollFrom(model, initial, steps, flags = { ab: true, ba: true }) {
  let cur = cloneState(initial);
  const states = [cloneState(cur)];
  for (let t = 0; t < steps; t++) { cur = step(model, cur, -1, -1, flags); states.push(cur); }
  return states;
}

function outputAt(model, s, ep) {
  const pA = softmax(matVec(model.VA, s.a, model.k, model.d));
  const pB = softmax(matVec(model.VB, s.b, model.k, model.d));
  return {
    pA, pB,
    ceA: -Math.log(Math.max(pA[ep.sB], 1e-12)),
    ceB: -Math.log(Math.max(pB[ep.sA], 1e-12)),
    correctA: argmax(pA) === ep.sB,
    correctB: argmax(pB) === ep.sA,
  };
}

function l1ProbabilityChange(a, b) {
  let s = 0;
  for (let i = 0; i < a.length; i++) s += Math.abs(a[i] - b[i]);
  return s / 2;
}

export function normMatch(candidate, reference, d) {
  const out = clone(candidate);
  for (const [start, end] of [[0, d], [d, d * 2]]) {
    const c = vectorNorm(out.slice(start, end));
    const r = vectorNorm(reference.slice(start, end));
    const scale = c > 1e-12 ? r / c : 0;
    for (let i = start; i < end; i++) out[i] *= scale;
  }
  return out;
}

function interventionMetrics(model, ep, config, branches, vector, operation = "subtract") {
  const idx = config.interventionStateIndex;
  const remaining = config.sequence.inputSteps + config.sequence.interactionSteps + config.sequence.delaySteps - idx;
  const baseFinal = rollFrom(model, branches.full, remaining).at(-1);
  const changedVec = concatState(branches.full);
  for (let i = 0; i < changedVec.length; i++) changedVec[i] += operation === "subtract" ? -vector[i] : vector[i];
  const changedState = splitState(changedVec, model.d);
  const changedFinal = rollFrom(model, changedState, remaining).at(-1);
  const base = outputAt(model, baseFinal, ep), changed = outputAt(model, changedFinal, ep);
  const nextBase = step(model, branches.full, -1, -1);
  const nextChanged = step(model, changedState, -1, -1);
  return {
    ceIncreaseA: changed.ceA - base.ceA,
    ceIncreaseB: changed.ceB - base.ceB,
    probabilityChangeA: l1ProbabilityChange(base.pA, changed.pA),
    probabilityChangeB: l1ProbabilityChange(base.pB, changed.pB),
    bothCorrectChange: Number(changed.correctA && changed.correctB) - Number(base.correctA && base.correctB),
    nextStateDifference: vectorNorm(Float64Array.from(concatState(nextBase), (x, i) => x - concatState(nextChanged)[i])),
    baseBothCorrect: Number(base.correctA && base.correctB),
    changedBothCorrect: Number(changed.correctA && changed.correctB),
  };
}

function averageObjects(rows) {
  const out = {};
  if (!rows.length) return out;
  for (const key of Object.keys(rows[0])) if (typeof rows[0][key] === "number") out[key] = mean(rows.map((r) => r[key]));
  return out;
}

function randomDirection(rng, reference, d) {
  const raw = Float64Array.from({ length: d * 2 }, () => rng.normal());
  return normMatch(raw, reference, d);
}

function counterfactualAnalysis(model, episodes, exchangeEpisodes, config, rng, emit, branchBuilder = branchesAt, jointInputMode = false) {
  const rows = [], rawStates = [];
  const randomEffectsByDirection = Array.from({ length: config.mode.randomControls }, () => []);
  const relationEffects = [];
  const individualEffects = [];
  const exchangeEffects = [];
  const transportRows = [[], [], []];
  const reconstructionRows = [[], [], []];
  const exchangeLog = [];
  for (let e = 0; e < episodes.length; e++) {
    const ep = episodes[e];
    const br = branchBuilder(model, ep, config, config.interventionStateIndex);
    const own = br.relation;
    const ownMetrics = interventionMetrics(model, ep, config, br, own);
    const relationEffect = ownMetrics.ceIncreaseA + ownMetrics.ceIncreaseB;
    relationEffects.push(relationEffect);

    const individualRaw = concatState(state(
      Float64Array.from(br.aOnly.a, (x, i) => x - br.zero.a[i]),
      Float64Array.from(br.bOnly.b, (x, i) => x - br.zero.b[i]),
    ));
    const individual = normMatch(individualRaw, own, model.d);
    const individualMetrics = interventionMetrics(model, ep, config, br, individual);
    individualEffects.push(individualMetrics.ceIncreaseA + individualMetrics.ceIncreaseB);

    const sourceEp = exchangeEpisodes[e % exchangeEpisodes.length];
    const sourceBr = branchBuilder(model, sourceEp, config, config.interventionStateIndex);
    const swapped = normMatch(sourceBr.relation, own, model.d);
    const targetMinusOwn = concatState(br.full);
    for (let i = 0; i < targetMinusOwn.length; i++) targetMinusOwn[i] = targetMinusOwn[i] - own[i] + swapped[i];
    const idx = config.interventionStateIndex;
    const total = config.sequence.inputSteps + config.sequence.interactionSteps + config.sequence.delaySteps;
    const baseFinal = rollFrom(model, br.full, total - idx).at(-1);
    const swapFinal = rollFrom(model, splitState(targetMinusOwn, model.d), total - idx).at(-1);
    const baseOut = outputAt(model, baseFinal, ep), swapOut = outputAt(model, swapFinal, ep);
    const exchangeMetric = {
      ceIncreaseA: swapOut.ceA - baseOut.ceA,
      ceIncreaseB: swapOut.ceB - baseOut.ceB,
      probabilityChangeA: l1ProbabilityChange(baseOut.pA, swapOut.pA),
      probabilityChangeB: l1ProbabilityChange(baseOut.pB, swapOut.pB),
      bothCorrectChange: Number(swapOut.correctA && swapOut.correctB) - Number(baseOut.correctA && baseOut.correctB),
    };
    exchangeEffects.push(exchangeMetric.ceIncreaseA + exchangeMetric.ceIncreaseB);
    exchangeLog.push({ targetEpisodeId: ep.id, sourceEpisodeId: sourceEp.id, targetSymbols: [ep.sA, ep.sB], sourceSymbols: [sourceEp.sA, sourceEp.sB] });

    const perRandom = [];
    for (let q = 0; q < config.mode.randomControls; q++) {
      const rv = randomDirection(rng, own, model.d);
      const rm = interventionMetrics(model, ep, config, br, rv);
      perRandom.push(rm.ceIncreaseA + rm.ceIncreaseB);
    }
    perRandom.forEach((value, direction) => randomEffectsByDirection[direction].push(value));

    let normalBranches = { full: cloneState(br.full), aOnly: cloneState(br.aOnly), bOnly: cloneState(br.bOnly), zero: cloneState(br.zero) };
    let interventionFull = splitState(Float64Array.from(concatState(br.full), (x, i) => x - own[i]), model.d);
    let currentRelation = own;
    for (let t = 0; t < 3; t++) {
      const nextNormal = jointInputMode ? {
        full: step(model, normalBranches.full, -1, -1, { ab: true, ba: true }),
        aOnly: step(model, normalBranches.aOnly, -1, -1, { ab: true, ba: true }),
        bOnly: step(model, normalBranches.bOnly, -1, -1, { ab: true, ba: true }),
        zero: step(model, normalBranches.zero, -1, -1, { ab: true, ba: true }),
      } : {
        full: step(model, normalBranches.full, -1, -1, { ab: true, ba: true }),
        aOnly: step(model, normalBranches.aOnly, -1, -1, { ab: false, ba: true }),
        bOnly: step(model, normalBranches.bOnly, -1, -1, { ab: true, ba: false }),
        zero: step(model, normalBranches.zero, -1, -1, { ab: false, ba: false }),
      };
      const nextInterventionFull = step(model, interventionFull, -1, -1, { ab: true, ba: true });
      const nextR = extractRelation(nextNormal.full, nextNormal.aOnly, nextNormal.bOnly, nextNormal.zero);
      const nextRMinus = extractRelation(nextInterventionFull, nextNormal.aOnly, nextNormal.bOnly, nextNormal.zero);
      const delta = Float64Array.from(nextR, (x, i) => x - nextRMinus[i]);
      const observed = Float64Array.from(concatState(nextNormal.full), (x, i) => x - concatState(nextInterventionFull)[i]);
      const error = Float64Array.from(observed, (x, i) => x - delta[i]);
      const randomTransport = [];
      for (let q = 0; q < config.mode.randomControls; q++) {
        const rv = randomDirection(rng, currentRelation, model.d);
        const alt = splitState(Float64Array.from(concatState(normalBranches.full), (x, i) => x - rv[i]), model.d);
        const altNext = step(model, alt, -1, -1);
        randomTransport.push(vectorNorm(Float64Array.from(concatState(nextNormal.full), (x, i) => x - concatState(altNext)[i])));
      }
      const effect = vectorNorm(observed);
      const percentile = randomTransport.filter((x) => effect > x).length / randomTransport.length;
      const remain = Math.max(0, 2 - t);
      const baseOutput = outputAt(model, rollFrom(model, nextNormal.full, remain).at(-1), ep);
      const intOutput = outputAt(model, rollFrom(model, nextInterventionFull, remain).at(-1), ep);
      transportRows[t].push({
        transportedFraction: vectorNorm(delta) / Math.max(vectorNorm(nextR), 1e-12),
        directionalAlignment: cosine(delta, nextR),
        relationRemovalEffect: effect,
        randomDirectionPercentile: percentile,
        bilateralOutputEffectA: l1ProbabilityChange(baseOutput.pA, intOutput.pA),
        bilateralOutputEffectB: l1ProbabilityChange(baseOutput.pB, intOutput.pB),
      });
      reconstructionRows[t].push({
        observedMissingContribution: vectorNorm(observed),
        reconstructedContribution: vectorNorm(delta),
        absoluteError: vectorNorm(error),
        relativeError: vectorNorm(error) / Math.max(vectorNorm(observed), 1e-12),
        cosineAlignment: cosine(observed, delta),
      });
      normalBranches = nextNormal;
      interventionFull = nextInterventionFull;
      currentRelation = nextR;
    }

    const relationNormA = vectorNorm(own.slice(0, model.d));
    const relationNormB = vectorNorm(own.slice(model.d));
    rows.push({
      episodeId: ep.id,
      relationNorm: vectorNorm(own), relationNormA, relationNormB,
      bilateralSupport: Number(relationNormA > 1e-10 && relationNormB > 1e-10),
      bilateralOutputResponse: Number(ownMetrics.probabilityChangeA > 1e-10 && ownMetrics.probabilityChangeB > 1e-10),
      deletion: ownMetrics, individualHistory: individualMetrics, exchange: exchangeMetric,
    });
    rawStates.push({
      episodeId: ep.id,
      full: Array.from(concatState(br.full)), aOnly: Array.from(concatState(br.aOnly)),
      bOnly: Array.from(concatState(br.bOnly)), zeroInteraction: Array.from(concatState(br.zero)),
      relation: Array.from(own), relationAFromB: Array.from(own.slice(0, model.d)), relationBFromA: Array.from(own.slice(model.d)),
    });
    if (e % 4 === 0) emit({ type: "progress", phase: "intervention", interventionProgress: (e + 1) / episodes.length });
  }
  const relationMean = mean(relationEffects);
  const randomEffects = randomEffectsByDirection.map((values) => mean(values));
  const randomMean = mean(randomEffects);
  const percentile = randomEffects.filter((x) => relationMean > x).length / Math.max(randomEffects.length, 1);
  return {
    relationNorm: mean(rows.map((r) => r.relationNorm)),
    relationNormMax: Math.max(...rows.map((r) => r.relationNorm)),
    bilateralSupportFraction: mean(rows.map((r) => r.bilateralSupport)),
    bilateralOutputResponseFraction: mean(rows.map((r) => r.bilateralOutputResponse)),
    deletion: averageObjects(rows.map((r) => r.deletion)),
    individualHistory: averageObjects(rows.map((r) => r.individualHistory)),
    crossPair: averageObjects(rows.map((r) => r.exchange)),
    relationEffect: relationMean,
    individualEffect: mean(individualEffects),
    crossPairEffect: mean(exchangeEffects),
    randomControl: { countPerEpisode: config.mode.randomControls, distribution: randomEffects.map((x) => round(x)), mean: randomMean, percentile, exceededCount: randomEffects.filter((x) => relationMean > x).length },
    transport: transportRows.map((x, stepIndex) => ({ step: stepIndex + 1, ...averageObjects(x) })),
    reconstruction: reconstructionRows.map((x, stepIndex) => ({ step: stepIndex + 1, ...averageObjects(x) })),
    exchangeLog,
    episodes: rows,
    rawStates,
  };
}

export function sha256Hex(bytes) {
  const k = Uint32Array.from([
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2,
  ]);
  const rotateRight = (value, amount) => (value >>> amount) | (value << (32 - amount));
  const paddedLength = Math.ceil((bytes.length + 9) / 64) * 64;
  const message = new Uint8Array(paddedLength);
  message.set(bytes);
  message[bytes.length] = 0x80;
  const bitLength = bytes.length * 8;
  const high = Math.floor(bitLength / 0x100000000);
  const low = bitLength >>> 0;
  for (let i = 0; i < 4; i++) {
    message[paddedLength - 8 + i] = (high >>> (24 - i * 8)) & 0xff;
    message[paddedLength - 4 + i] = (low >>> (24 - i * 8)) & 0xff;
  }
  const hash = Uint32Array.from([0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19]);
  const words = new Uint32Array(64);
  for (let offset = 0; offset < message.length; offset += 64) {
    for (let i = 0; i < 16; i++) {
      const p = offset + i * 4;
      words[i] = ((message[p] << 24) | (message[p + 1] << 16) | (message[p + 2] << 8) | message[p + 3]) >>> 0;
    }
    for (let i = 16; i < 64; i++) {
      const s0 = rotateRight(words[i - 15], 7) ^ rotateRight(words[i - 15], 18) ^ (words[i - 15] >>> 3);
      const s1 = rotateRight(words[i - 2], 17) ^ rotateRight(words[i - 2], 19) ^ (words[i - 2] >>> 10);
      words[i] = (words[i - 16] + s0 + words[i - 7] + s1) >>> 0;
    }
    let [a, b, c, d, e, f, g, h] = hash;
    for (let i = 0; i < 64; i++) {
      const sigma1 = rotateRight(e, 6) ^ rotateRight(e, 11) ^ rotateRight(e, 25);
      const choice = (e & f) ^ (~e & g);
      const temp1 = (h + sigma1 + choice + k[i] + words[i]) >>> 0;
      const sigma0 = rotateRight(a, 2) ^ rotateRight(a, 13) ^ rotateRight(a, 22);
      const majority = (a & b) ^ (a & c) ^ (b & c);
      const temp2 = (sigma0 + majority) >>> 0;
      h = g; g = f; f = e; e = (d + temp1) >>> 0;
      d = c; c = b; b = a; a = (temp1 + temp2) >>> 0;
    }
    hash[0] = (hash[0] + a) >>> 0; hash[1] = (hash[1] + b) >>> 0;
    hash[2] = (hash[2] + c) >>> 0; hash[3] = (hash[3] + d) >>> 0;
    hash[4] = (hash[4] + e) >>> 0; hash[5] = (hash[5] + f) >>> 0;
    hash[6] = (hash[6] + g) >>> 0; hash[7] = (hash[7] + h) >>> 0;
  }
  return Array.from(hash, (word) => word.toString(16).padStart(8, "0")).join("");
}

function sha256Weights(model) {
  const values = [];
  for (const key of parameterKeys(model.independent)) values.push(...model[key]);
  const bytes = new TextEncoder().encode(values.map((x) => x.toPrecision(17)).join(","));
  return sha256Hex(bytes);
}

function parameterCount(d, k) { return 4 * d * d + 4 * d * k + 2 * d; }

function decide(metrics, independent, thresholds) {
  const transported = metrics.analysis.transport.filter((x) => x.transportedFraction >= thresholds.transportedFractionMin).length;
  const checks = [
    { id: "task", label: "Reciprocal recall competence", passed: metrics.validation.bothCorrect >= thresholds.taskBothCorrectMin, value: metrics.validation.bothCorrect, threshold: thresholds.taskBothCorrectMin },
    { id: "independent", label: "Relational norm exceeds the independent control", passed: independent.relationNorm <= metrics.analysis.relationNorm * thresholds.independentRelationRatioMax, value: independent.relationNorm / Math.max(metrics.analysis.relationNorm, 1e-12), threshold: thresholds.independentRelationRatioMax },
    { id: "bilateral", label: "Erasure affects both A and B", passed: metrics.analysis.deletion.ceIncreaseA > thresholds.bilateralCeIncreaseMin && metrics.analysis.deletion.ceIncreaseB > thresholds.bilateralCeIncreaseMin, value: Math.min(metrics.analysis.deletion.ceIncreaseA, metrics.analysis.deletion.ceIncreaseB), threshold: thresholds.bilateralCeIncreaseMin },
    { id: "rank", label: "Rank against norm-matched random directions", passed: metrics.analysis.randomControl.percentile >= thresholds.randomPercentileMin, value: metrics.analysis.randomControl.percentile, threshold: thresholds.randomPercentileMin },
    { id: "exchange", label: "Cross-pair substitution degrades performance", passed: metrics.analysis.crossPairEffect > thresholds.crossPairDegradationMin, value: metrics.analysis.crossPairEffect, threshold: thresholds.crossPairDegradationMin },
    { id: "transport", label: "Relational contribution persists across three transitions", passed: transported >= thresholds.transportTransitionsRequired, value: transported, threshold: thresholds.transportTransitionsRequired },
  ];
  const passed = checks.filter((x) => x.passed).length;
  const status = passed >= thresholds.supportChecksRequired ? "supported" : passed >= thresholds.partialChecksRequired ? "partial" : "not-supported";
  return { status, passed, total: checks.length, checks };
}

function decide006A(interacting, dualRelay, validation, dualValidation, thresholds) {
  const transported = interacting.transport.filter(
    (row) => row.transportedFraction >= thresholds.transportedFractionMin,
  ).length;
  const checks = [
    { id: "both-task-competent", label: "Both systems master reciprocal recall", passed: validation.bothCorrect >= thresholds.taskBothCorrectMin && dualValidation.bothCorrect >= thresholds.taskBothCorrectMin, value: Math.min(validation.bothCorrect, dualValidation.bothCorrect), threshold: thresholds.taskBothCorrectMin },
    { id: "dual-zero", label: "Separate memories produce zero joint component", passed: dualRelay.relationNormMax <= thresholds.dualComponentMax, value: dualRelay.relationNormMax, threshold: thresholds.dualComponentMax },
    { id: "joint-nonzero", label: "Interaction leaves a nonzero joint component", passed: interacting.relationNorm >= thresholds.interactingComponentMin, value: interacting.relationNorm, threshold: thresholds.interactingComponentMin },
    { id: "bilateral-support", label: "The joint component spans both A and B", passed: interacting.bilateralSupportFraction >= thresholds.bilateralSupportMin, value: interacting.bilateralSupportFraction, threshold: thresholds.bilateralSupportMin },
    { id: "transport", label: "The joint component continues into later states", passed: transported >= thresholds.transportTransitionsRequired, value: transported, threshold: thresholds.transportTransitionsRequired },
    { id: "bilateral-action", label: "Erasing the joint component changes both outputs", passed: interacting.bilateralOutputResponseFraction >= thresholds.bilateralOutputResponseMin, value: interacting.bilateralOutputResponseFraction, threshold: thresholds.bilateralOutputResponseMin },
    { id: "exchange", label: "Another pair's component cannot substitute for it", passed: interacting.crossPairEffect > thresholds.crossPairDegradationMin, value: interacting.crossPairEffect, threshold: thresholds.crossPairDegradationMin },
    { id: "reconstruction", label: "The missing next-state contribution is reconstructed", passed: Math.max(...interacting.reconstruction.map((row) => row.absoluteError)) <= thresholds.reconstructionErrorMax, value: Math.max(...interacting.reconstruction.map((row) => row.absoluteError)), threshold: thresholds.reconstructionErrorMax },
  ];
  const passed = checks.filter((check) => check.passed).length;
  const status = passed === checks.length ? "supported" : passed >= thresholds.partialChecksRequired ? "partial" : "not-supported";
  return { status, passed, total: checks.length, checks };
}

function publicConfig(config) {
  return { ...config, mode: { ...config.mode } };
}

async function runSingle(seed, config, emit, includeRaw = true) {
  const counts = [config.mode.trainEpisodes, config.mode.validationEpisodes, config.mode.interventionEpisodes, config.mode.exchangeEpisodes];
  const data = makeDataset(config.mode.symbolClasses, counts, seed);
  const interactionRng = new SeededRandom(seed ^ 0x1a2b3c4d);
  const controlRng = new SeededRandom(seed ^ 0x5e6f7788);
  const model = createModel(config.mode.hiddenDimension, config.mode.symbolClasses, interactionRng, false);
  // Equal-capacity competent control: one private relay receives only B and
  // answers for A; the other receives only A and answers for B. The relays do
  // not interact, so an ab-a0-0b+00 joint term cancels by construction.
  const independent = createModel(config.mode.hiddenDimension, config.mode.symbolClasses, controlRng, true, true);
  const untrained006A = jointComponentStats(model, data.intervention, config);
  const untrainedDual006A = jointComponentStats(independent, data.intervention, config);
  const history = await trainModel(model, data.training, data.validation, config, interactionRng, emit, "training-interaction");
  const independentHistory = await trainModel(independent, data.training, data.validation, config, controlRng, emit, "training-dual-relay");
  emit({ type: "progress", phase: "counterfactual" });
  const analysis = counterfactualAnalysis(model, data.intervention, data.exchange, config, interactionRng, emit);
  const independentAnalysis = counterfactualAnalysis(independent, data.intervention, data.exchange, config, controlRng, () => {});
  emit({ type: "progress", phase: "joint-006a" });
  const joint006A = counterfactualAnalysis(model, data.intervention, data.exchange, config, interactionRng, emit, jointBranchesAt, true);
  const dualRelay006A = counterfactualAnalysis(independent, data.intervention, data.exchange, config, controlRng, () => {}, jointBranchesAt, true);
  const validation = evaluate(model, data.validation, config);
  const independentValidation = evaluate(independent, data.validation, config);
  joint006A.untrainedRelationNorm = untrained006A.relationNorm;
  joint006A.trainingAmplification = joint006A.relationNorm / Math.max(untrained006A.relationNorm, 1e-12);
  dualRelay006A.untrainedRelationNorm = untrainedDual006A.relationNorm;
  dualRelay006A.trainingAmplification = dualRelay006A.relationNorm / Math.max(untrainedDual006A.relationNorm, 1e-12);
  const result = {
    seed,
    architecture: { type: "two-agent coupled tanh RNN", hiddenDimension: config.mode.hiddenDimension, symbolClasses: config.mode.symbolClasses, persistentStates: ["hA", "hB"], thirdState: false, parameterCount: parameterCount(config.mode.hiddenDimension, config.mode.symbolClasses) },
    training: { history, final: history.at(-1), objective: "CE(A recalls sB) + CE(B recalls sA)", carrierSpecificLoss: false },
    independentTraining: { history: independentHistory, final: independentHistory.at(-1), architecture: "equal-capacity dual directed relay; no cross-relay path" },
    validation,
    independentValidation,
    analysis,
    independentAnalysis: { relationNorm: independentAnalysis.relationNorm, relationEffect: independentAnalysis.relationEffect, validation: independentValidation },
    experiment006A: {
      question: "one nonseparable joint contribution versus two additive directed memories",
      formula: "C(t)=H(ab)-H(a0)-H(0b)+H(00)",
      interacting: joint006A,
      dualRelay: dualRelay006A,
      controlDescription: "two disconnected competent directed memories with equal active parameter count",
      parameterCountMatched: true,
    },
    evaluationEpisodeIds: { validation: data.validation.map((x) => x.id), intervention: data.intervention.map((x) => x.id), exchange: data.exchange.map((x) => x.id) },
    modelWeightHash: await sha256Weights(model),
  };
  result.decision = decide(result, result.independentAnalysis, config.thresholds);
  result.experiment006A.decision = decide006A(
    joint006A, dualRelay006A, validation, independentValidation, config.thresholds006A,
  );
  if (!includeRaw) {
    delete result.analysis.rawStates;
    delete result.analysis.episodes;
    delete result.analysis.randomControl.distribution;
    delete result.experiment006A.interacting.rawStates;
    delete result.experiment006A.interacting.episodes;
    delete result.experiment006A.interacting.randomControl.distribution;
    delete result.experiment006A.dualRelay.rawStates;
    delete result.experiment006A.dualRelay.episodes;
    delete result.experiment006A.dualRelay.randomControl.distribution;
    result.training.history = [result.training.final];
    result.independentTraining.history = [result.independentTraining.final];
  }
  return result;
}

export async function runExperiment(payload, emit = () => {}) {
  stopRequested = false;
  const config = { ...payload.config, mode: { ...payload.config.modes[payload.mode] } };
  delete config.modes;
  config.interventionStateIndex = payload.config.interventionStateIndex;
  const baseSeed = Number(payload.seed) >>> 0;
  const perSeed = [];
  let primary = null;
  for (let i = 0; i < config.mode.seedCount; i++) {
    const seed = (baseSeed + Math.imul(i, 0x9e3779b9)) >>> 0;
    emit({ type: "progress", phase: "seed", seedIndex: i + 1, seedCount: config.mode.seedCount, activeSeed: seed });
    const result = await runSingle(seed, config, emit, i === 0);
    if (i === 0) primary = result;
    perSeed.push({
      seed, validation: result.validation, relationNorm: result.analysis.relationNorm,
      relationEffect: result.analysis.relationEffect,
      randomPercentile: result.analysis.randomControl.percentile,
      transport: result.analysis.transport, decision: result.decision,
      experiment006A: {
        interactingJointNorm: result.experiment006A.interacting.relationNorm,
        dualRelayJointNorm: result.experiment006A.dualRelay.relationNorm,
        dualRelayAccuracy: result.independentValidation.bothCorrect,
        decision: result.experiment006A.decision,
      },
    });
  }
  const output = {
    schemaVersion: "1.1.0",
    generatedAt: new Date().toISOString(),
    config: publicConfig(config),
    seed: baseSeed,
    primary,
    perSeed,
    aggregate: {
      validationAccuracyA: mean(perSeed.map((x) => x.validation.accuracyA)),
      validationAccuracyB: mean(perSeed.map((x) => x.validation.accuracyB)),
      bothCorrect: mean(perSeed.map((x) => x.validation.bothCorrect)),
      relationNorm: mean(perSeed.map((x) => x.relationNorm)),
      supportedSeeds: perSeed.filter((x) => x.decision.status === "supported").length,
      partialSeeds: perSeed.filter((x) => x.decision.status === "partial").length,
      notSupportedSeeds: perSeed.filter((x) => x.decision.status === "not-supported").length,
      experiment006ASupportedSeeds: perSeed.filter((x) => x.experiment006A.decision.status === "supported").length,
    },
  };
  return output;
}

if (typeof WorkerGlobalScope !== "undefined" && globalThis instanceof WorkerGlobalScope) {
  globalThis.onmessage = async (event) => {
    if (event.data?.type === "STOP") { stopRequested = true; return; }
    if (event.data?.type !== "START") return;
    try {
      const result = await runExperiment(event.data.payload, (message) => globalThis.postMessage(message));
      globalThis.postMessage({ type: "complete", result });
    } catch (error) {
      globalThis.postMessage({ type: error?.message === "STOPPED" ? "stopped" : "error", message: error?.message || String(error) });
    }
  };
}
