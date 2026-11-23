# Scored for Support

A static research site about Kazakhstan’s Digital Family Card in English, Kazakh, and Russian. Python and Jinja generate the home, methods, and AI transparency pages in each language. The household simulator, charts, and prototypes run in the browser using vanilla JavaScript.

## Build and preview

Use Python 3.10 or newer.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python build.py
python3 -m http.server 4173 --bind 127.0.0.1 --directory dist
```

Open http://127.0.0.1:4173. If `dist/` is already built, run just the last command. Run the build again after editing the source files.

## Share or host the site

For a preview on your local network, run:

```sh
python3 -m http.server 4173 --bind 0.0.0.0 --directory dist
```

On macOS, run `ipconfig getifaddr en0` to find your Wi-Fi address. Someone on the same network can open `http://<your-local-ip>:4173` while the server is running.

To host the site, publish the contents of `dist/` to a static host such as GitHub Pages. The output includes `.nojekyll` and uses relative URLs so it works at a domain root or under a repository path.

## Edit the project

- `content/` contains the English research copy and shared references. `content/kk/` and `content/ru/` contain the Kazakh and Russian prose. Keep the same block types and order across languages so the build can place each translation around the interactive components. The renderer supports headings, paragraphs, bold phrases, bullet lists, pipe tables, and citations.
- `content/ui.txt` contains the interface strings in English, Kazakh, and Russian, in that order.
- `data/scoring_rule.json` contains the reported scoring values. The two low-income options are selectable in the simulator. The chart shows their possible range until the monetary poverty line is supplied and the code can map it to the appropriate band.
- `data/birth_benefit_real.json` contains the historical series. The 2027 projection holds the nominal benefit at the January 2026 value.
- `data/bill.json` contains the five author-set risk levels. A null value shows “Set by author.”
- `static/score.mjs` contains the pure scoring functions. Scenario links store inputs in the URL fragment and restore them in the browser.

The project uses the pack’s public hook. Before publication, verify the scoring methodology and affected benefits against the official texts, resolve the overlapping lower categories, and finish the placeholders in the methods and AI transparency pages.

## Check locally

```sh
.venv/bin/python -m unittest discover -s tests
node --test tests/scoring.test.mjs
```

The scoring tests use Node.js 20 or newer. Node.js is optional for building and previewing the site.
