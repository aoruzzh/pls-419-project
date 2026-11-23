import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { test } from 'node:test';
import { categoriesFor, incomeOptions, projectBenefit, referenceFamily, scoreFamily } from '../static/score.mjs';

const load = async name => JSON.parse(await readFile(new URL(`../data/${name}.json`, import.meta.url)));
const rule = await load('scoring_rule');
const benefit = await load('birth_benefit_real');

test('reference family crosses from C to B at four subsistence minimums', () => {
  const below = scoreFamily(referenceFamily, rule);
  const at = scoreFamily({ ...referenceFamily, income: '6' }, rule);
  assert.deepEqual([below.points, below.categories, below.excluded], [650, ['C'], false]);
  assert.deepEqual([at.points, at.categories, at.excluded], [870, ['B'], true]);
  assert.deepEqual(incomeOptions(203403, rule), [5]);
  assert.deepEqual(incomeOptions(203404, rule), [6]);
});

test('upper boundaries and reported category overlaps remain exact', () => {
  for (const [points, category] of [[729, 'C'], [730, 'B'], [1799, 'B'], [1800, 'A']]) {
    assert.deepEqual(categoriesFor(points, rule), [category]);
  }
  assert.deepEqual(categoriesFor(-30, rule), ['C', 'D']);
  assert.deepEqual(categoriesFor(-459, rule), ['D', 'E']);
  assert.deepEqual(incomeOptions(1, rule), [1, 2]);
});

test('all supported deductions flow through to the category', () => {
  const result = scoreFamily({ income: '0', workers: '0', children: '4+', loan: '1', overdue: 'all', car: '0', housing: '0' }, rule);
  assert.equal(result.points, -1000);
  assert.deepEqual(result.categories, ['E']);
});

test('inflation projection holds the nominal benefit constant', () => {
  assert.equal(projectBenefit(benefit, 0, '2020'), 94116);
  assert.equal(projectBenefit(benefit, 20, '2026'), 136958);
});
