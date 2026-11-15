/* Presentation of saved research values only; no inference or external requests. */
(() => {
  "use strict";
  const presentation = document.getElementById("presentation-mode");
  if (presentation) presentation.addEventListener("click", () => {
    const enabled = document.body.classList.toggle("presentation-view");
    presentation.setAttribute("aria-pressed", String(enabled));
    presentation.textContent = enabled ? "Exit presentation" : "Presentation view";
  });
  const print = document.getElementById("print-report");
  if (print) print.addEventListener("click", () => window.print());
  const details = document.getElementById("technical-details");
  function revealDetails() {
    if (details && window.location.hash === "#technical-details") details.open = true;
  }
  window.addEventListener("hashchange", revealDetails);
  revealDetails();
  const selector = document.getElementById("occlusion-block");
  const dataNode = document.getElementById("experiment-data");
  if (!selector || !dataNode) return;
  const data = JSON.parse(dataNode.textContent);
  function showExperiment() {
    const index = Number(selector.value);
    if (!Number.isInteger(index) || index < 0 || index >= data.scores.length) return;
    const score = data.scores[index];
    const effect = data.effects[index];
    document.getElementById("control-score").textContent = data.baseline.toFixed(6);
    document.getElementById("occluded-score").textContent = score.toFixed(6);
    document.getElementById("control-bar").style.width = `${100 * data.baseline}%`;
    document.getElementById("occluded-bar").style.width = `${100 * score}%`;
    document.getElementById("experiment-result").textContent =
      `Block ${index + 1}: baseline minus occluded = ${effect >= 0 ? "+" : ""}${effect.toFixed(6)}. ` +
      "Fixed stage-2 target; not a patient cancer probability.";
  }
  selector.addEventListener("change", showExperiment);
  showExperiment();
})();
