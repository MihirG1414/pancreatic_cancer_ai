// Execute the actual viewer script with a minimal DOM to test state coordination.
// These tests do not substitute for browser rendering/interaction verification.
const { test } = require('node:test');
const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const { resolve } = require('node:path');
const vm = require('node:vm');

const code = readFileSync(resolve(__dirname, '../src/mirai_ct/assets/viewer.js'), 'utf8');
const settle = () => new Promise(resolve => setImmediate(resolve));

function setup({ auto = true, empty = false, annotation = true } = {}) {
  const data = {
    shape_ijk: [80, 100, 3], spacing: [2, 3, 4], units: 'mm', directions: ['R', 'A', 'S'],
    zoom_padding_ij: [5, 5], focus_ijk: [20, 35, 1],
    bounds_ijk: empty ? null : [[10, 20, 1], [30, 50, 1]],
    slice_counts: empty ? [0, 0, 0] : [0, 23, 0], slice_maxima: [0, 0.9, 0],
    annotation_labels: annotation ? [{ id: 2, rgb: [255, 0, 0] }] : [],
    slices: [0, 1, 2].map(k => ({ k, ct: `${k}-ct.png`, candidate: `${k}-candidate.png`,
      outline: `${k}-outline.png`, annotation: annotation ? `${k}-annotation.png` : null }))
  };
  const elements = new Map();
  const pending = [];
  class Element {
    constructor() {
      this.style = {}; this.listeners = {}; this.children = []; this.textContent = '';
      this.checked = false; this.value = ''; this.disabled = false;
      this.ctx = { draws: [], globalAlpha: 1,
        clearRect() { this.draws = []; },
        drawImage(...args) { this.draws.push({ args, alpha: this.globalAlpha }); } };
    }
    addEventListener(type, fn) { this.listeners[type] = fn; }
    append(...nodes) { this.children.push(...nodes); }
    getContext() { return this.ctx; }
    emit(type = 'input') { return this.listeners[type](); }
    set width(value) { this._width = value; this.ctx.draws = []; this.ctx.globalAlpha = 1; }
    get width() { return this._width; }
  }
  const document = {
    getElementById(id) {
      if (!elements.has(id)) elements.set(id, new Element());
      return elements.get(id);
    },
    createElement: () => new Element(), createTextNode: text => text,
  };
  const get = id => document.getElementById(id);
  get('viewer-data').textContent = JSON.stringify(data);
  get('slice-index').value = '1'; get('candidate-style').value = 'candidate';
  get('overlay-opacity').value = '65';
  class Image {
    set src(value) {
      this.path = value;
      const request = { resolve: () => this.onload(), reject: () => this.onerror() };
      pending.push(request);
      if (auto) queueMicrotask(request.resolve);
    }
  }
  vm.runInNewContext(code, { document, Image });
  return { get, pending };
}

test('initial panels share slice and opacity', async () => {
  const { get } = setup(); await settle();
  assert.match(get('slice-status').textContent, /Native k=1.*23 retained/);
  assert.equal(get('ct-canvas').ctx.draws.length, 1);
  const draws = get('candidate-canvas').ctx.draws;
  assert.equal(draws[0].args[0].path, 'viewer/1-ct.png');
  assert.equal(draws[1].args[0].path, 'viewer/1-candidate.png');
  assert.equal(draws[1].alpha, 0.65);
});

test('zoom applies identical native crop to every panel', async () => {
  const { get } = setup(); await settle();
  get('candidate-zoom').checked = true; get('candidate-zoom').emit();
  for (const id of ['ct-canvas', 'annotation-canvas', 'candidate-canvas']) {
    assert.deepEqual(Array.from(get(id).ctx.draws[0].args.slice(1)), [5, 44, 31, 41, 0, 0, 31, 41]);
    assert.equal(get(id).width, 31);
    assert.equal(get(id).height, 41);
  }
});

test('outline, off and opacity controls alter display only', async () => {
  const { get } = setup(); await settle();
  get('candidate-style').value = 'outline'; get('candidate-style').emit();
  assert.equal(get('candidate-canvas').ctx.draws[1].args[0].path, 'viewer/1-outline.png');
  get('overlay-opacity').value = '20'; get('overlay-opacity').emit();
  assert.equal(get('candidate-canvas').ctx.draws[1].alpha, 0.2);
  get('candidate-style').value = 'off'; get('candidate-style').emit();
  assert.equal(get('candidate-canvas').ctx.draws.length, 1);
  assert.equal(get('annotation-canvas').ctx.draws.length, 2);
});

test('slice navigation, boundaries and focus button', async () => {
  const { get } = setup(); await settle();
  await get('previous-slice').emit('click');
  await settle();
  assert.equal(Number(get('slice-index').value), 0);
  assert.equal(get('previous-slice').disabled, true);
  assert.match(get('slice-status').textContent, /No retained candidate/);
  get('slice-index').value = '2'; await get('slice-index').emit();
  assert.equal(get('next-slice').disabled, true);
  await get('candidate-focus').emit('click');
  await settle();
  assert.equal(Number(get('slice-index').value), 1);
});

test('out-of-order image loads cannot paint stale mixed slices', async () => {
  const { get, pending } = setup({ auto: false });
  get('slice-index').value = '0'; get('slice-index').emit();
  get('slice-index').value = '2'; get('slice-index').emit();
  pending.slice(8, 12).forEach(x => x.resolve()); await settle();
  pending.slice(0, 8).forEach(x => x.resolve()); await settle();
  assert.match(get('slice-status').textContent, /Native k=2/);
  for (const id of ['ct-canvas', 'annotation-canvas', 'candidate-canvas']) {
    assert.equal(get(id).ctx.draws[0].args[0].path, 'viewer/2-ct.png');
  }
});

test('missing asset produces an explicit error and cleared panels', async () => {
  const { get, pending } = setup({ auto: false });
  pending[0].reject(); pending.slice(1).forEach(x => x.resolve()); await settle();
  assert.match(get('slice-status').textContent, /Unable to load slice images/);
  assert.equal(get('candidate-canvas').ctx.draws.length, 0);
});

test('empty map and absent annotation are explicit', async () => {
  const { get } = setup({ empty: true, annotation: false }); await settle();
  assert.equal(get('candidate-zoom').disabled, true);
  assert.equal(get('candidate-focus').disabled, true);
  assert.equal(get('annotation-canvas').ctx.draws.length, 1);
  assert.match(get('annotation-legend').textContent, /No annotation labels/);
});
