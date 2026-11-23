export const referenceFamily = Object.freeze({
  income: '5', workers: '2+', children: '1', loan: '0',
  overdue: 'none', car: '1', housing: '1',
});

export function categoriesFor(score, rule) {
  return rule.categories
    .filter(({ min = -Infinity, max = Infinity }) => score >= min && score <= max)
    .map(({ cat }) => cat);
}

export function scoreFamily(family, rule) {
  const overdue = {
    none: 0, one: rule.overdue_90d_one_adult, all: rule.overdue_90d_all_adults,
  };
  const components = [
    ['Income per person', rule.income_bands_per_person[Number(family.income)].points],
    ['Working members', rule.employment[family.workers]],
    ['Children', rule.children[family.children]],
    ['Active loan', family.loan === '1' ? rule.active_loan : 0],
    ['Overdue debt', overdue[family.overdue]],
    ['Car ownership', family.car === '0' ? rule.no_car : 0],
    ['Housing', family.housing === '0' ? rule.no_own_housing : 0],
  ];
  const points = components.reduce((sum, [, value]) => sum + value, 0);
  const categories = categoriesFor(points, rule);
  return {
    points,
    categories,
    components,
    excluded: categories.length > 0 && categories.every(cat => rule.excluded_categories.includes(cat)),
  };
}

export function incomeOptions(income, rule) {
  const bands = rule.income_bands_per_person;
  if (income === 0) return [0];
  // The pack leaves the numerical poverty line blank.
  if (income < bands[3].min) return [1, 2];
  return [bands.findLastIndex(band => band.min !== undefined && income >= band.min)];
}

export function projectBenefit(benefit, rate, basis) {
  const last = benefit.rows.at(-1);
  const baseValue = basis === '2020' ? last.real : last.nominal;
  return Math.round(baseValue / (1 + rate / 100));
}
