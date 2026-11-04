/* Native display only. All model values and slice indices come from saved assets. */
(() => {
  "use strict";
  const data = JSON.parse(document.getElementById("viewer-data").textContent);
  const slider = document.getElementById("slice-index");
  const zoom = document.getElementById("candidate-zoom");
  const style = document.getElementById("candidate-style");
  const opacity = document.getElementById("overlay-opacity");
  const status = document.getElementById("slice-status");
  const canvases = ["ct-canvas", "annotation-canvas", "candidate-canvas"]
    .map(id => document.getElementById(id));
  let generation = 0;
  let current = null;

  function image(path) {
    if (path === null) return Promise.resolve(null);
    return new Promise((resolve, reject) => {
      const img = new Image();
      img.onload = () => resolve(img);
      img.onerror = () => reject(new Error("Unable to load slice images. Keep the viewer folder beside index.html."));
      img.src = "viewer/" + path;
    });
  }

  function region() {
    const [ni, nj] = data.shape_ijk;
    if (!zoom.checked || !data.bounds_ijk) return [0, 0, ni, nj];
    const [lo, hi] = data.bounds_ijk;
    const [pi, pj] = data.zoom_padding_ij;
    const x = Math.max(0, lo[0] - pi);
    const y = Math.max(0, nj - 1 - hi[1] - pj);
    const right = Math.min(ni, hi[0] + pi + 1);
    const bottom = Math.min(nj, nj - lo[1] + pj);
    return [x, y, right - x, bottom - y];
  }

  function draw() {
    if (!current) return;
    const roi = region();
    canvases.forEach((canvas, i) => {
      canvas.width = roi[2];
      canvas.height = roi[3];
      canvas.style.aspectRatio = (roi[2] * data.spacing[0]) / (roi[3] * data.spacing[1]);
      const ctx = canvas.getContext("2d");
      ctx.imageSmoothingEnabled = false;
      ctx.drawImage(current.ct, ...roi, 0, 0, canvas.width, canvas.height);
      let overlay = i === 1 ? current.annotation : null;
      if (i === 2 && style.value !== "off") overlay = current[style.value];
      if (overlay) {
        ctx.globalAlpha = Number(opacity.value) / 100;
        ctx.drawImage(overlay, ...roi, 0, 0, canvas.width, canvas.height);
        ctx.globalAlpha = 1;
      }
    });
    const k = Number(slider.value);
    const count = data.slice_counts[k];
    status.textContent = `Native k=${k} of ${data.shape_ijk[2] - 1} (zero-based). ` +
      (count ? `${count} retained candidate voxels; maximum score ${data.slice_maxima[k].toFixed(6)}.` :
        "No retained candidate values on this slice.") +
      (zoom.checked ? " Candidate zoom." : " Full view.");
    document.getElementById("previous-slice").disabled = k === 0;
    document.getElementById("next-slice").disabled = k === data.shape_ijk[2] - 1;
  }

  async function load() {
    const version = ++generation;
    const k = Number(slider.value);
    const entry = data.slices[k];
    current = null;
    canvases.forEach(c => c.getContext("2d").clearRect(0, 0, c.width, c.height));
    status.textContent = `Loading native k=${k}...`;
    try {
      const [ct, annotation, candidate, outline] = await Promise.all([
        image(entry.ct), image(entry.annotation), image(entry.candidate), image(entry.outline)
      ]);
      if (version !== generation) return;
      current = {ct, annotation, candidate, outline};
      draw();
    } catch (error) {
      if (version === generation) status.textContent = error.message;
    }
  }

  slider.addEventListener("input", load);
  [zoom, style, opacity].forEach(control => control.addEventListener("input", draw));
  document.getElementById("previous-slice").addEventListener("click", () => {
    slider.value = Math.max(0, Number(slider.value) - 1); load();
  });
  document.getElementById("next-slice").addEventListener("click", () => {
    slider.value = Math.min(data.shape_ijk[2] - 1, Number(slider.value) + 1); load();
  });
  document.getElementById("candidate-focus").addEventListener("click", () => {
    slider.value = data.focus_ijk[2]; load();
  });
  zoom.disabled = data.bounds_ijk === null;
  document.getElementById("candidate-focus").disabled = data.bounds_ijk === null;
  document.getElementById("viewer-directions").textContent =
    `Horizontal: native i (+${data.directions[0]}). Upwards: native j (+${data.directions[1]}). ` +
    `Spacing: ${data.spacing.map(x => Number(x).toFixed(3)).join(" x ")} ${data.units}.`;
  const legend = document.getElementById("annotation-legend");
  if (!data.annotation_labels.length) legend.textContent = "No annotation labels supplied.";
  data.annotation_labels.forEach(item => {
    const label = document.createElement("span");
    const swatch = document.createElement("span");
    swatch.style.cssText = `display:inline-block;width:12px;height:12px;margin-left:12px;background:rgb(${item.rgb.join(",")})`;
    label.append(swatch, document.createTextNode(` Existing label ${item.id} `));
    legend.append(label);
  });
  load();
})();
