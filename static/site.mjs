import { categoriesFor, scoreFamily } from './score.mjs';
import { initBenefit, initCliff } from './charts.mjs';
import { text } from './locale.mjs';

document.documentElement.classList.add('js');
const $ = (id) => document.getElementById(id);
const motion = matchMedia('(prefers-reduced-motion: reduce)');
const signed = (number) => number > 0 ? `+${number}` : String(number).replace('-', '−');

const menu = document.querySelector('.menu-button');
const nav = $('site-nav');
const languageLinks = [...document.querySelectorAll('[data-language-link]')];
function syncLanguageLinks() {
  for (const link of languageLinks) {
    const url = new URL(link.href);
    url.hash = location.hash;
    link.href = url.href;
  }
}
syncLanguageLinks();
window.addEventListener('hashchange', syncLanguageLinks);
function closeMenu() {
  nav.classList.remove('open');
  menu.setAttribute('aria-expanded', 'false');
}
menu.addEventListener('click', () => {
  const open = nav.classList.toggle('open');
  menu.setAttribute('aria-expanded', String(open));
});
nav.addEventListener('click', (event) => { if (event.target.closest('a')) closeMenu(); });
document.addEventListener('keydown', (event) => {
  if (event.key === 'Escape' && nav.classList.contains('open')) {
    closeMenu();
    menu.focus();
  }
});

const arcLinks = [...document.querySelectorAll('.arc-link')];
const chapters = arcLinks.map(link => $(link.hash.slice(1)));
let scrolling = false;
function updateProgress() {
  const maximum = document.documentElement.scrollHeight - innerHeight;
  $('reading-progress').style.transform = `scaleX(${maximum > 0 ? scrollY / maximum : 0})`;
  const chapter = chapters.findLastIndex(section => section.getBoundingClientRect().top <= innerHeight / 3);
  arcLinks.forEach((link, index) => {
    if (index === chapter) link.setAttribute('aria-current', 'location');
    else link.removeAttribute('aria-current');
  });
  scrolling = false;
}
window.addEventListener('scroll', () => {
  if (!scrolling) {
    scrolling = true;
    requestAnimationFrame(updateProgress);
  }
}, { passive: true });
window.addEventListener('resize', updateProgress);
updateProgress();

function initTabs() {
  const list = $('bill-tabs');
  const tabs = [...list.querySelectorAll('button')];
  const panels = tabs.map(tab => $(tab.dataset.tab));
  list.setAttribute('role', 'tablist');
  list.hidden = false;
  tabs.forEach((tab, index) => {
    tab.setAttribute('role', 'tab');
    tab.setAttribute('aria-controls', panels[index].id);
    panels[index].setAttribute('role', 'tabpanel');
    panels[index].setAttribute('aria-labelledby', tab.id);
    panels[index].tabIndex = 0;
    tab.addEventListener('click', () => activate(index));
    tab.addEventListener('keydown', (event) => {
      const keys = { ArrowLeft: index - 1, ArrowRight: index + 1, Home: 0, End: tabs.length - 1 };
      if (!Object.hasOwn(keys, event.key)) return;
      event.preventDefault();
      const next = (keys[event.key] + tabs.length) % tabs.length;
      activate(next);
      tabs[next].focus();
    });
  });

  function activate(active) {
    tabs.forEach((tab, index) => {
      tab.setAttribute('aria-selected', String(index === active));
      tab.tabIndex = index === active ? 0 : -1;
      panels[index].hidden = index !== active;
    });
  }
  activate(0);
}

function scalePoint(score, rule, channel) {
  const scale = document.querySelector(`[data-scale="${channel}"]`);
  const bounds = [...rule.categories].reverse().map(category => category.min ?? -500).concat(2000);
  const weights = [1, 2, 3, 4, 1];
  const segment = Math.max(0, Math.min(4, bounds.findLastIndex(bound => score >= bound)));
  const fraction = Math.max(0, Math.min(1, (score - bounds[segment]) / (bounds[segment + 1] - bounds[segment])));
  const position = (weights.slice(0, segment).reduce((sum, weight) => sum + weight, 0) + weights[segment] * fraction) / 11;
  scale.style.setProperty('--position', `${Math.min(99, Math.max(1, position * 100))}%`);
}

function initScoreExamples(rule) {
  const points = [
    rule.income_bands_per_person.at(-1).points, rule.employment['2+'],
    rule.children['1'], rule.active_loan,
  ];
  const tokens = [...$('score-tokens').querySelectorAll('span')];
  const sum = points.reduce((total, value) => total + value, 0);
  tokens.forEach((token, index) => { token.querySelector('b').textContent = signed(points[index]); });
  function setDemo(score) {
    $('demo-result').textContent = text('points', { points: score, categories: categoriesFor(score, rule).join(' / ') });
    scalePoint(score, rule, 'demo');
  }
  let replay = [];
  setDemo(sum);
  $('replay-score').addEventListener('click', () => {
    replay.forEach(clearTimeout);
    tokens.forEach(token => token.getAnimations().forEach(animation => animation.cancel()));
    if (motion.matches) { setDemo(sum); return; }
    setDemo(0);
    replay = tokens.map((token, index) => setTimeout(() => {
      token.animate([{ opacity: .3, transform: 'translateY(-9px)' }, { opacity: 1, transform: 'none' }], { duration: 220 });
      setDemo(points.slice(0, index + 1).reduce((total, value) => total + value, 0));
    }, index * 220));
  });
}

function initSimulator(rule) {
  const form = $('family-form');
  const category = $('sim-category');
  const output = $('sim-points');
  const share = $('share-url');
  const shareStatus = $('share-status');

  function clearShare() {
    $('share-label').hidden = true;
    shareStatus.textContent = '';
  }

  function update() {
    clearShare();
    const values = Object.fromEntries(new FormData(form));
    const sample = scoreFamily(values, rule);
    category.textContent = sample.categories.join('/');
    category.classList.toggle('cool', !sample.excluded);
    category.classList.toggle('ambiguous', sample.categories.length > 1);
    $('sim-score').textContent = sample.points;
    $('sim-meaning').textContent = sample.categories.length > 1
      ? text('simAmbiguous')
      : sample.excluded ? text('simExcluded') : text('simIncluded');
    scalePoint(sample.points, rule, 'sim');
    output.replaceChildren(...sample.components.map(([label, points]) => {
      const row = document.createElement('div');
      const term = document.createElement('dt');
      const value = document.createElement('dd');
      term.textContent = text(label);
      value.textContent = signed(points);
      row.append(term, value);
      return row;
    }));
  }

  function restore() {
    if (!location.hash.startsWith('#simulator?')) return;
    const params = new URLSearchParams(location.hash.slice('#simulator?'.length));
    for (const input of form.querySelectorAll('input[type="radio"]')) {
      if (params.get(input.name) === input.value) input.checked = true;
    }
    $('simulator').scrollIntoView({ behavior: 'instant' });
  }

  form.addEventListener('submit', event => event.preventDefault());
  form.addEventListener('change', update);
  form.addEventListener('reset', () => {
    if (location.hash.startsWith('#simulator?')) history.replaceState(null, '', '#simulator');
    syncLanguageLinks();
    requestAnimationFrame(update);
  });
  window.addEventListener('hashchange', () => { restore(); update(); });
  $('share-family').addEventListener('click', async () => {
    const url = new URL(location.href);
    url.hash = `simulator?${new URLSearchParams(new FormData(form))}`;
    history.replaceState(null, '', url);
    syncLanguageLinks();
    share.value = url.href;
    $('share-label').hidden = false;
    try {
      await navigator.clipboard.writeText(url.href);
      shareStatus.textContent = text('shared');
    } catch {
      share.focus();
      share.select();
      shareStatus.textContent = text('copy');
    }
  });
  restore();
  update();
}

async function readDataset(name) {
  const response = await fetch(new URL(`../data/${name}.json`, import.meta.url));
  if (!response.ok) throw new Error(`Unable to load ${name}.`);
  return response.json();
}

if (document.body.dataset.page === 'home') {
  initTabs();
  try {
    const [rule, benefit] = await Promise.all([readDataset('scoring_rule'), readDataset('birth_benefit_real')]);
    initScoreExamples(rule);
    initSimulator(rule);
    initCliff(rule, benefit);
    initBenefit(benefit);
  } catch (error) {
    console.error(error);
    const message = document.createElement('p');
    message.className = 'notice';
    message.textContent = text('loadError');
    $('family-form').before(message);
  }
}

if (!motion.matches && 'IntersectionObserver' in window) {
  const observer = new IntersectionObserver(entries => {
    for (const entry of entries) {
      if (entry.isIntersecting) {
        entry.target.classList.add('enter-view');
        observer.unobserve(entry.target);
      }
    }
  });
  document.querySelectorAll('.chapter-heading, .economy-card, .record-guide, .chart-card, .simulator, .decision-flow, .prototype-grid, .source-plot, .contributions .panel, .methods-intro .panel, .regional, .verdict-grid').forEach(block => observer.observe(block));
}
