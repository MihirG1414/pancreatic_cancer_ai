// Exercise the shipped offline interaction, using saved numeric fixtures, not inference.
const { test } = require('node:test');
const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const vm = require('node:vm');
const code = readFileSync(require('node:path').resolve(__dirname, '../src/mirai_ct/assets/report.js'), 'utf8');

function setup({ evidence = true, hash = '' } = {}) {
  const elements = new Map();
  for (const id of ['presentation-mode', 'print-report', 'technical-details',
    ...(evidence ? ['occlusion-block', 'experiment-data', 'control-score', 'occluded-score', 'control-bar', 'occluded-bar', 'experiment-result'] : [])]) {
    elements.set(id, { value: '0', textContent: '', style: {}, attributes: {}, listeners: {},
      addEventListener(event, fn) { this.listeners[event] = fn; },
      setAttribute(key, value) { this.attributes[key] = value; } });
  }
  if (evidence) elements.get('experiment-data').textContent = JSON.stringify({baseline: 0.8, scores: [0.2, 0.9], effects: [0.6, -0.1]});
  const classes = new Set();
  const document = { getElementById: id => elements.get(id) || null,
    body: { classList: { toggle(value) { if (classes.has(value)) { classes.delete(value); return false; } classes.add(value); return true; } } } };
  const window = { location: { hash }, listeners: {}, printCount: 0,
    addEventListener(event, fn) { this.listeners[event] = fn; }, print() { this.printCount++; } };
  vm.runInNewContext(code, { document, window });
  return { get: id => elements.get(id), classes, window };
}

test('experiment selector preserves signed effects and compares actual target scores', () => {
  const { get } = setup();
  assert.equal(get('control-score').textContent, '0.800000');
  assert.equal(get('occluded-score').textContent, '0.200000');
  assert.equal(get('control-bar').style.width, '80%');
  assert.match(get('experiment-result').textContent, /\+0.600000.*not a patient cancer probability/);
  get('occlusion-block').value = '1';
  get('occlusion-block').listeners.change();
  assert.equal(get('occluded-score').textContent, '0.900000');
  assert.equal(get('occluded-bar').style.width, '90%');
  assert.match(get('experiment-result').textContent, /Block 2:.*-0.100000/);
});

test('invalid experiment index cannot replace displayed evidence', () => {
  const { get } = setup();
  const initial = get('experiment-result').textContent;
  for (const value of ['-1', '2', 'NaN', '0.5']) {
    get('occlusion-block').value = value;
    get('occlusion-block').listeners.change();
    assert.equal(get('experiment-result').textContent, initial);
  }
});

test('presentation and print controls work even when no explanation is supplied', () => {
  const { get, classes, window } = setup({evidence: false});
  get('presentation-mode').listeners.click();
  assert.ok(classes.has('presentation-view'));
  assert.equal(get('presentation-mode').attributes['aria-pressed'], 'true');
  get('presentation-mode').listeners.click();
  assert.ok(!classes.has('presentation-view'));
  assert.equal(get('presentation-mode').attributes['aria-pressed'], 'false');
  get('print-report').listeners.click();
  assert.equal(window.printCount, 1);
});

test('technical-details deep links reveal the disclosure on load and navigation', () => {
  const { get, window } = setup({hash: '#technical-details'});
  assert.equal(get('technical-details').open, true);
  get('technical-details').open = false;
  window.listeners.hashchange();
  assert.equal(get('technical-details').open, true);
});
