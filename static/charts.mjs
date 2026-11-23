import { incomeOptions, projectBenefit, referenceFamily, scoreFamily } from './score.mjs';

import { messages, text } from './locale.mjs';

const number = new Intl.NumberFormat(document.documentElement.lang);
const fmt = (value) => number.format(value);
const money = (value) => `${fmt(value)} ₸`;
const $ = (id) => document.getElementById(id);
const blue = '#065451';
const amber = '#933a25';
const archetypes = { reference: {}, noChildren: { children: '0' }, oneEarner: { workers: '1' } };

function chart(canvas, { xDomain, yDomain, xTicks, yTicks, formatX, formatY }) {
  const { width, height } = canvas.getBoundingClientRect();
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  canvas.width = Math.round(width * dpr);
  canvas.height = Math.round(height * dpr);
  const ctx = canvas.getContext('2d');
  ctx.scale(dpr, dpr);
  const compact = width < 500;
  const left = compact ? 43 : 55;
  const top = 15;
  const right = width - 18;
  const bottom = height - 28;
  const x = (value) => left + (value - xDomain[0]) / (xDomain[1] - xDomain[0]) * (right - left);
  const y = (value) => bottom - (value - yDomain[0]) / (yDomain[1] - yDomain[0]) * (bottom - top);
  ctx.font = `${compact ? 11 : 12}px ui-monospace, monospace`;
  ctx.fillStyle = '#46546a';
  ctx.textBaseline = 'middle';
  ctx.textAlign = 'right';
  for (const tick of yTicks) {
    ctx.beginPath();
    ctx.strokeStyle = '#d9d9d2';
    ctx.lineWidth = 1;
    ctx.moveTo(left, y(tick));
    ctx.lineTo(right, y(tick));
    ctx.stroke();
    ctx.fillText(formatY(tick), left - 6, y(tick));
  }
  ctx.textAlign = 'center';
  for (const tick of xTicks) ctx.fillText(formatX(tick), x(tick), bottom + 15);
  return { ctx, x, y, top, bottom };
}

function line({ ctx, x, y }, points, color, dash = []) {
  ctx.save();
  ctx.strokeStyle = color;
  ctx.lineWidth = 2.6;
  ctx.setLineDash(dash);
  ctx.beginPath();
  points.forEach(([a, b], index) => index ? ctx.lineTo(x(a), y(b)) : ctx.moveTo(x(a), y(b)));
  ctx.stroke();
  ctx.restore();
}

function marker({ ctx, x, y }, a, b, color) {
  ctx.beginPath();
  ctx.fillStyle = color;
  ctx.arc(x(a), y(b), 4.5, 0, Math.PI * 2);
  ctx.fill();
}

function table(parent, headings, rows) {
  const table = document.createElement('table');
  const head = table.createTHead().insertRow();
  for (const heading of headings) {
    const th = document.createElement('th');
    th.scope = 'col';
    th.textContent = heading;
    head.append(th);
  }
  const body = table.createTBody();
  for (const row of rows) {
    const tr = body.insertRow();
    row.forEach(value => { tr.insertCell().textContent = value; });
  }
  parent.setAttribute('role', 'region');
  parent.setAttribute('aria-label', text('chartData'));
  parent.tabIndex = 0;
  parent.replaceChildren(table);
}

function onResize(canvas, draw) {
  new ResizeObserver(draw).observe(canvas);
}

export function initCliff(rule, benefit) {
  const input = $('chart-income');
  const select = $('archetype');
  const canvas = $('cliff-chart');
  const bands = rule.income_bands_per_person;
  const cliff = bands.at(-1).min;
  const minimum = rule.subsistence_minimum_2026;
  const maximum = minimum * 5;
  const exclusion = rule.categories.find(({ cat }) => cat === 'B').min;
  input.min = 0;
  input.max = maximum;
  input.step = 1;
  input.value = cliff - 1;
  $('income-max').textContent = money(maximum);
  let wasExcluded;

  function examples() {
    return { ...referenceFamily, ...archetypes[select.value] };
  }

  function result(band) {
    return scoreFamily({ ...examples(), income: String(band) }, rule);
  }

  function draw() {
    const plot = chart(canvas, {
      xDomain: [0, maximum], yDomain: [0, 1000],
      xTicks: [0, minimum * 2, cliff, maximum], yTicks: [0, 250, 500, exclusion, 1000],
      formatX: (value) => fmt(value),
      formatY: fmt,
    });
    const { ctx, x, y, top, bottom } = plot;
    ctx.fillStyle = '#f9ebe5';
    ctx.fillRect(x(0), top, x(maximum) - x(0), y(exclusion) - top);
    ctx.fillStyle = '#e0eeea';
    ctx.fillRect(x(0), y(result(2).points), x(minimum) - x(0), y(result(1).points) - y(result(2).points));
    line(plot, [[0, result(1).points], [minimum, result(1).points]], blue, [4, 4]);
    line(plot, [[0, result(2).points], [minimum, result(2).points]], blue, [4, 4]);
    marker(plot, 0, result(0).points, blue);
    const steps = [[minimum, result(3).points]];
    for (const [index, band] of bands.entries()) {
      if (index <= 3) continue;
      steps.push([band.min, result(index - 1).points], [band.min, result(index).points]);
    }
    steps.push([maximum, result(bands.length - 1).points]);
    line(plot, steps, blue);
    ctx.save();
    line(plot, [[0, exclusion], [maximum, exclusion]], amber, [5, 5]);
    ctx.setLineDash([4, 4]);
    ctx.strokeStyle = amber;
    ctx.beginPath();
    ctx.moveTo(x(cliff), top);
    ctx.lineTo(x(cliff), bottom);
    ctx.stroke();
    ctx.restore();
    const income = Number(input.value);
    for (const band of incomeOptions(income, rule)) marker(plot, income, result(band).points, amber);
  }

  function update() {
    const income = Number(input.value);
    const sample = incomeOptions(income, rule).map(result);
    const points = sample.map(value => value.points).join('–');
    const categories = [...new Set(sample.flatMap(value => value.categories))].join(' / ');
    const excluded = sample.every(value => value.excluded);
    const status = $('cliff-status');
    $('chart-income-value').textContent = money(income);
    input.setAttribute('aria-valuetext', text('incomeAmount', { amount: fmt(income) }));
    status.textContent = text('points', { points, categories });
    status.classList.toggle('warm', excluded);
    const badge = $('benefit-status');
    const historical = money(benefit.rows.at(-1).nominal);
    badge.textContent = text(excluded ? 'benefitExcluded' : 'benefitIncluded', { amount: historical });
    badge.classList.toggle('warm', excluded);
    if (wasExcluded !== undefined && excluded !== wasExcluded && !matchMedia('(prefers-reduced-motion: reduce)').matches) {
      badge.getAnimations().forEach(animation => animation.cancel());
      badge.animate([
        { transform: 'translateX(0)' }, { transform: 'translateX(-3px)' },
        { transform: 'translateX(3px)' }, { transform: 'translateX(0)' },
      ], { duration: 220 });
    }
    wasExcluded = excluded;
    draw();
  }

  function updateExample() {
    const low = result(5);
    const high = result(6);
    $('cliff-summary').textContent = text('cliffSummary', {
      threshold: money(cliff), low: low.points, lowCat: low.categories.join('/'),
      high: high.points, highCat: high.categories.join('/'), minimum: money(minimum),
    });
    table($('cliff-table'), ['band', 'score', 'category'].map(key => text(key)), messages.incomeBands.map((label, index) => {
      const value = result(index);
      return [label, value.points, value.categories.join(' / ')];
    }));
    update();
  }

  for (const comparison of document.querySelectorAll('[data-income-point]')) {
    comparison.addEventListener('click', (event) => {
      if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
      select.value = 'reference';
      input.value = comparison.dataset.incomePoint === 'below' ? cliff - 1 : cliff;
      updateExample();
    });
  }
  $('below-cliff').addEventListener('click', () => { input.value = cliff - 1; update(); });
  $('at-cliff').addEventListener('click', () => { input.value = cliff; update(); });
  input.addEventListener('input', update);
  select.addEventListener('change', updateExample);
  onResize(canvas, draw);
  updateExample();
}

export function initBenefit(benefit) {
  const input = $('inflation-rate');
  const view = $('price-view');
  const canvas = $('benefit-chart');
  const rows = benefit.rows;
  const last = rows.at(-1);
  const nextYear = last.year + 1;
  const real = (row) => view.value === '2020' ? row.real : Math.round(row.real * last.nominal / last.real);
  const projection = () => projectBenefit(benefit, Number(input.value), view.value);

  function draw() {
    const plot = chart(canvas, {
      xDomain: [rows[0].year, nextYear], yDomain: [75000, 205000],
      xTicks: rows.map(row => row.year).concat(nextYear),
      yTicks: [80000, 120000, 160000, 200000],
      formatX: String, formatY: value => `${value / 1000}k`,
    });
    const nominalSeries = rows.map(row => [row.year, row.nominal]);
    const realSeries = rows.map(row => [row.year, real(row)]);
    line(plot, nominalSeries, blue);
    line(plot, realSeries, amber, [6, 5]);
    line(plot, [realSeries.at(-1), [nextYear, projection()]], amber, [2, 5]);
    for (const [year, value] of nominalSeries) marker(plot, year, value, blue);
    for (const [year, value] of realSeries) marker(plot, year, value, amber);
    marker(plot, nextYear, projection(), amber);
  }

  function update() {
    const basis = view.value;
    const rate = input.value;
    $('inflation-value').textContent = `${rate}%`;
    $('real-key').textContent = text('real', { basis });
    $('projection').textContent = text('projection', {
      year: nextYear, amount: money(projection()), basis, rate, nominal: money(last.nominal),
    });
    table($('benefit-table'), [text('january'), text('nominal'), text('realTable', { basis })], [
      ...rows.map(row => [row.year, money(row.nominal), money(real(row))]),
      [text('projectedYear', { year: nextYear }), text('assumed', { amount: money(last.nominal) }), money(projection())],
    ]);
    draw();
  }
  input.addEventListener('input', update);
  view.addEventListener('change', update);
  onResize(canvas, draw);
  update();
}
