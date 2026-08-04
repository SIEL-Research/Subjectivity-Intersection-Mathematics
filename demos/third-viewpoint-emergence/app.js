import { config } from "./config.js";

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];
const symbols = ["●", "◆", "✦", "△"];
const phases = {
  seed: "INITIALISING TWO VIEWPOINTS",
  "training-interaction": "A AND B ARE ENCOUNTERING EACH OTHER",
  "training-dual-relay": "BUILDING THE SEPARATE-MEMORY CONTROL",
  counterfactual: "ASKING WHAT A OR B COULD DO ALONE",
  "joint-006a": "SEARCHING FOR A VIEWPOINT IN NEITHER ALONE",
  intervention: "ERASING, EXCHANGING, AND ADVANCING O3"
};

let worker;
let result;

const pct = (value, digits = 0) => Number.isFinite(value) ? `${(value * 100).toFixed(digits)}%` : "—";
const num = (value, digits = 5) => Number.isFinite(value) ? Number(value).toFixed(digits) : "—";
const check = (decision, id) => decision?.checks?.find((row) => row.id === id);

function setPair(seed) {
  const a = (seed >>> 0) % 4;
  let b = ((Math.imul(seed >>> 0, 7) + 3) >>> 0) % 4;
  if (a === b) b = (b + 1) % 4;
  $("#symbol-a").textContent = symbols[a];
  $("#symbol-b").textContent = symbols[b];
  return { a, b };
}

function start() {
  const seed = Number($("#seed").value) >>> 0;
  $("#seed").value = String(seed);
  setPair(seed);
  $("#run").disabled = true;
  $("#run-panel").hidden = false;
  $("#discovery").hidden = true;
  $("#world").classList.add("meeting");
  $("#world").classList.remove("emerged");
  $("#absence").hidden = false;
  $("#o3").hidden = true;
  $("#run-panel").scrollIntoView({ behavior: "smooth", block: "center" });
  worker?.terminate();
  worker = new Worker("./experiment.worker.js", { type: "module" });
  worker.onmessage = ({ data }) => {
    if (data.type === "progress") updateProgress(data);
    if (data.type === "complete") reveal(data.result);
    if (data.type === "error" || data.type === "stopped") fail(data.message || "The run stopped.");
  };
  worker.onerror = () => fail("The live numerical engine could not start. Serve this folder over HTTP rather than opening the file directly.");
  worker.postMessage({ type: "START", payload: { config, mode: "quick", seed } });
}

function updateProgress(data) {
  $("#phase-label").textContent = phases[data.phase] || "RUNNING THE LIVE EXPERIMENT";
  const epoch = data.epoch || 0;
  $("#epoch").textContent = `${epoch} / ${config.modes.quick.epochs}`;
  $("#progress-bar").style.width = `${Math.min(100, epoch / config.modes.quick.epochs * 100)}%`;
  $("#loss").textContent = num(data.loss, 4);
  $("#accuracy-a").textContent = pct(data.accuracyA);
  $("#accuracy-b").textContent = pct(data.accuracyB);
}

function reveal(run) {
  result = run;
  worker?.terminate();
  $("#run").disabled = false;
  $("#progress-bar").style.width = "100%";
  $("#phase-label").textContent = "THE LIVE RUN IS COMPLETE";
  const primary = run.primary;
  const joint = primary.experiment006A.interacting;
  const decision = primary.experiment006A.decision;
  const supported = decision.status === "supported";

  $("#discovery").hidden = false;
  $("#world").classList.toggle("emerged", supported);
  $("#absence").hidden = supported;
  $("#o3").hidden = !supported;
  $("#discovery-title").textContent = supported ? "A third viewpoint emerged." : "This encounter did not reveal a third viewpoint.";
  $("#discovery-copy").textContent = supported
    ? `A and B learned the same task as the separate-memory control. But only the interacting pair left a nonzero contribution (${num(joint.relationNorm, 4)}) that neither viewpoint contained alone.`
    : "The frozen evidence gates were not all satisfied in this seed. The demo preserves that outcome rather than replacing it with a successful run.";

  const pair = setPair(Number($("#seed").value) >>> 0);
  const viewData = {
    a: {
      label: "VIEWPOINT A",
      headline: `I learned what B saw: ${symbols[pair.b]}`,
      copy: `A recalls B with ${pct(primary.validation.accuracyA)} accuracy. A contains one side of the interaction, but not the whole third viewpoint.`,
      mark: "A"
    },
    b: {
      label: "VIEWPOINT B",
      headline: `I learned what A saw: ${symbols[pair.a]}`,
      copy: `B recalls A with ${pct(primary.validation.accuracyB)} accuracy. B contains the other side, but not the whole third viewpoint.`,
      mark: "B"
    },
    o3: {
      label: "THE EMERGENT THIRD VIEWPOINT",
      headline: supported ? "I exist only through this encounter." : "No stable O3 was detected in this encounter.",
      copy: supported
        ? `No third box stores me. I am distributed across A and B, specific to their shared history, and visible only after subtracting what each could have produced alone. My measured norm in this run is ${num(joint.relationNorm, 5)}.`
        : "The operational evidence did not cross every preregistered gate. Try a new seed to begin a genuinely new encounter.",
      mark: "O3"
    }
  };
  window.__viewData = viewData;
  selectView("o3");

  $("#verdict-status").textContent = supported ? `${decision.passed}/${decision.total} EVIDENCE GATES PASSED` : `${decision.passed}/${decision.total} EVIDENCE GATES PASSED`;
  $("#verdict-title").textContent = supported ? "O3 was not installed. Its operational trace formed through A × B." : "No emergence claim is made for this run.";
  $("#verdict-copy").textContent = supported
    ? "The detected viewpoint was nonlocalised, pair-specific, bilateral, intervention-sensitive, and transported into later joint states. It was not needed by the separate-memory control and was not named in the learning objective."
    : "The same unchanged procedure reports an unsupported outcome when its evidence gates do not pass.";

  $("#checks").innerHTML = decision.checks.map((row) => `<div class="check ${row.passed ? "" : "failed"}"><i>${row.passed ? "✓" : "×"}</i><span>${row.label}</span><b>${num(row.value, 6)} / ${num(row.threshold, 6)}</b></div>`).join("");
  $("#discovery").scrollIntoView({ behavior: "smooth", block: "start" });
}

function selectView(name) {
  const data = window.__viewData?.[name];
  if (!data) return;
  $$("[data-view]").forEach((button) => button.classList.toggle("selected", button.dataset.view === name));
  $("#view-window").dataset.view = name;
  $("#view-label").textContent = data.label;
  $("#view-headline").textContent = data.headline;
  $("#view-copy").textContent = data.copy;
  $("#view-mark").textContent = data.mark;
}

function runIntervention(kind) {
  if (!result) return;
  $$("[data-test]").forEach((button) => button.classList.toggle("selected", button.dataset.test === kind));
  const joint = result.primary.experiment006A.interacting;
  const box = $("#test-result");
  if (kind === "erase") {
    box.innerHTML = `<span>O3 ERASED · A AND B REMAIN</span><strong>Both viewpoints changed.</strong><p>A output changed by ${num(joint.deletion.probabilityChangeA, 6)} and B by ${num(joint.deletion.probabilityChangeB, 6)}. The next joint state moved by ${num(joint.deletion.nextStateDifference, 6)}.</p>`;
  }
  if (kind === "swap") {
    box.innerHTML = `<span>O3 REPLACED WITH ANOTHER PAIR'S TRACE</span><strong>The borrowed viewpoint did not fit.</strong><p>Cross-pair substitution degraded the learned relation by ${num(joint.crossPairEffect, 6)}. O3 is indexed to this pair and its encounter history.</p>`;
  }
  if (kind === "reentry") {
    const values = joint.transport.map((row) => pct(row.transportedFraction, 1)).join(" → ");
    box.innerHTML = `<span>NO NEW SIGNAL · THREE RECURRENT UPDATES</span><strong>O3 entered the formation of O3 again.</strong><p>The transported fraction continued across three later joint states: ${values}. This is the operational trace of self-re-entry.</p>`;
  }
}

function fail(message) {
  worker?.terminate();
  $("#run").disabled = false;
  $("#run-title").innerHTML = `<span class="error">${message}</span>`;
  $("#phase-label").textContent = "RUN STOPPED";
}

function download() {
  if (!result) return;
  const blob = new Blob([JSON.stringify(result, null, 2)], { type: "application/json" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = `third-viewpoint-${result.seed}.json`;
  link.click();
  URL.revokeObjectURL(link.href);
}

$("#run").addEventListener("click", start);
$("#stop").addEventListener("click", () => { worker?.postMessage({ type: "STOP" }); worker?.terminate(); fail("The run was stopped by the visitor."); });
$("#o3").addEventListener("click", () => { selectView("o3"); $("#view-window").scrollIntoView({ behavior: "smooth", block: "center" }); });
$$("[data-view]").forEach((button) => button.addEventListener("click", () => selectView(button.dataset.view)));
$$("[data-test]").forEach((button) => button.addEventListener("click", () => runIntervention(button.dataset.test)));
$("#download").addEventListener("click", download);
$("#again").addEventListener("click", () => {
  const random = new Uint32Array(1);
  crypto.getRandomValues(random);
  $("#seed").value = String(random[0]);
  result = undefined;
  $("#discovery").hidden = true;
  $("#run-panel").hidden = true;
  $("#world").classList.remove("emerged", "meeting");
  $("#o3").hidden = true;
  $("#absence").hidden = false;
  setPair(random[0]);
  $("#hero").scrollIntoView({ behavior: "smooth", block: "start" });
});

setPair(config.registeredSeed);
