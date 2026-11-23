"""Build the research site as HTML, CSS, JavaScript and JSON files."""
from dataclasses import dataclass
from html import escape, unescape
import json
from pathlib import Path
import re
from shutil import copytree
import unicodedata

from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup

ROOT = Path(__file__).resolve().parent
templates = Environment(
    loader=FileSystemLoader(ROOT / "templates"),
    autoescape=select_autoescape(),
)

YEAR = r"(?:\d{4}[a-z]?|n\.d\.)"
PROSE_LINK = re.compile(r"https?://[^\s<>]+")
REFERENCE = re.compile(r"^(.*?)\. \((" + YEAR + r")(?:,|\))")
ALIASES = {
    "Aiken": ("Aiken et al.",),
    "Brown": ("Brown, Ravallion and van de Walle",),
    "CDB.kz": ("Ministry of Labour via CDB.kz",),
    "Bizmedia.kz": ("Resolution No. 870, via Bizmedia.kz",),
    "Bureau of National Statistics of Kazakhstan": ("Bureau of National Statistics",),
    "Finratings.kz": ("Finratings",),
    "Ministry of Labour and Social Protection of the Population": ("Ministry of Labour",),
    "Noriega-Campero": ("Noriega-Campero et al.",),
    "Gosciak": ("Gosciak et al.",),
    "Alatas": ("Alatas et al.",),
    "Herd": ("Herd and Moynihan", "Herd & Moynihan"),
    "Ko": ("Ko and Moffitt", "Ko & Moffitt"),
    "Hanna": ("Hanna and Olken", "Hanna & Olken"),
    "McBride": ("McBride and Nichols", "McBride & Nichols"),
    "Selbst": ("Selbst et al.",),
    "Grosh": ("Grosh et al.",),
    "Scott": ("James Scott",),
}


def slug(text):
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")


def read_content(prefix):
    return next((ROOT / "content").glob(f"{prefix}-*.md")).read_text(encoding="utf-8").strip()


def dataset(name):
    return json.loads((ROOT / "data" / f"{name}.json").read_text(encoding="utf-8"))


def references():
    entries, lookup = [], {}
    for line in read_content("08").splitlines():
        if not line.startswith("- "):
            continue
        text = line[2:]
        match = REFERENCE.match(text)
        if not match:
            continue
        author, year = match.groups()
        author = author.split(",")[0]
        anchor = slug(f"{author} {year}")
        entries.append((anchor, Markup(inline(text, {}))))
        for name in (author, *ALIASES.get(author, ())):
            lookup[slug(f"{name} {year}")] = anchor
    return entries, lookup


def inline(text, lookup, site_root="."):
    """Render prose, source URLs, and the two citation forms used in the pack."""
    def link(label, author, year):
        anchor = lookup.get(slug(f"{unescape(author)} {year}"))
        return f'<a class="citation" href="{site_root}/methods/#{anchor}">{label}</a>' if anchor else label

    def cite_group(match):
        chunks = []
        for fragment in match[1].split(";"):
            citation = re.fullmatch(r"(\s*)(.+?),\s*(" + YEAR + r")", fragment)
            if citation:
                space, author, year = citation.groups()
                chunks.append(space + link(fragment.strip(), author, year))
            else:
                chunks.append(fragment)
        return "(" + ";".join(chunks) + ")"

    def external(match):
        url = match[0].rstrip(".,;)")
        return f'<a href="{escape(url, quote=True)}">{escape(url)}</a>' + escape(match[0][len(url):])

    parts = []
    cursor = 0
    for url in PROSE_LINK.finditer(text):
        parts.extend([escape(text[cursor:url.start()]), external(url)])
        cursor = url.end()
    if parts:
        return "".join(parts) + escape(text[cursor:])

    safe = escape(text, quote=False)
    names = [*ALIASES, *(alias for group in ALIASES.values() for alias in group),
             "Bureau of National Statistics"]
    authors = "|".join(re.escape(escape(name, quote=False)) for name in sorted(names, key=len, reverse=True))

    def narrative(match):
        author, years = match.groups()
        linked = re.sub(YEAR, lambda year: link(year[0], author, year[0]), years)
        return f"{author} ({linked})"

    safe = re.sub(r"(?<![\w>])(" + authors + r") \((" + YEAR + r"(?:, " + YEAR + r")*)\)",
                  narrative, safe)
    safe = re.sub(r"\((?=[^()]*,\s*(?:\d{4}|n\.d\.))([^()]+)\)", cite_group, safe)
    return safe


@dataclass
class Block:
    kind: str
    text: str

    def html(self, lookup, site_root):
        if self.kind == "list":
            items = "".join(f"<li>{inline(line[2:], lookup, site_root)}</li>" for line in self.text.splitlines())
            return Markup(f"<ul>{items}</ul>")
        if self.kind == "table":
            return Markup('<div class="table-wrap" tabindex="0" role="region" aria-label="Research table">' +
                          self.table_html(lookup, site_root) + "</div>")
        tag = {"heading": "h3", "subheading": "h4"}.get(self.kind, "p")
        style = ' class="missing"' if self.text.startswith("[MISSING:") else ""
        return Markup(f"<{tag}{style}>{inline(self.text, lookup, site_root)}</{tag}>")

    def rows(self):
        return [[cell.strip() for cell in row.strip("|").split("|")]
                for row in self.text.splitlines()]

    def table_html(self, lookup, site_root):
        header, _, *rows = self.rows()
        head = "".join(f'<th scope="col">{inline(cell, lookup, site_root)}</th>' for cell in header)
        body = "".join(
            f'<tr><th scope="row">{inline(first, lookup, site_root)}</th>' +
            "".join(f"<td>{inline(cell, lookup, site_root)}</td>" for cell in rest) + "</tr>"
            for first, *rest in rows
        )
        return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def blocks(prefix):
    # The research Markdown uses headings, plain paragraphs, bullet lists and tables.
    for chunk in re.split(r"\n\s*\n", read_content(prefix)):
        first, _, rest = chunk.partition("\n")
        if first.startswith(("## ", "### ")):
            yield Block("subheading" if first.startswith("### ") else "heading", first.split(" ", 1)[1])
            if rest:
                yield Block("paragraph", rest)
        else:
            kind = "list" if first.startswith("- ") else "table" if first.startswith("|") else "paragraph"
            yield Block(kind, chunk)


def render_blocks(parts, lookup, site_root):
    return Markup("\n".join(part.html(lookup, site_root) for part in parts))


def at(parts, title):
    return next(i for i, part in enumerate(parts) if part.text.startswith(title)
                and part.kind in ("heading", "subheading"))


def home():
    _, lookup = references()
    hook, problem, data, research, solution, verdict = [list(blocks(f"{i:02d}")) for i in range(6)]
    figure_one, figure_two, gaps, reliability = [
        at(data, title) for title in ("Figure 1", "Figure 2", "Where the data", "How far")
    ]
    affected, question = [at(problem, title) for title in ("Who is affected", "The social-science question")]
    approaches = [at(research, f"{i}.") for i in range(1, 5)] + [at(research, "Kazakhstan")]
    known = at(research, "What is known")
    cases, experiment, bill, scripts = [
        at(solution, title) for title in ("Real cases", "Optional:", "The bill", "Citizen explainer scripts")
    ]
    risk_levels = dataset("bill")["risk_levels"]
    rule = dataset("scoring_rule")
    benefit = dataset("birth_benefit_real")
    return templates.get_template("index.html").render(
        page="home", site_root=".", lookup=lookup, render=lambda parts: render_blocks(parts, lookup, "."),
        hook=hook, problem=problem[:affected], affected=problem[affected:question],
        question=problem[question:], stats=dataset("stats")["cards"],
        data_intro=data[:figure_one], figure_one=data[figure_one:figure_two],
        figure_two=data[figure_two:gaps], gaps=data[gaps+1].text.splitlines(),
        reliability=data[reliability:], research_intro=research[:approaches[0]],
        approaches=[research[a:b] for a, b in zip(approaches, approaches[1:])],
        regional=research[approaches[-1]:known], research_summary=research[known+1:],
        solution_intro=solution[:cases], tools=solution[2].rows(),
        cases=solution[cases+1:experiment], experiment=solution[experiment:bill],
        bills=[(risk_levels.get(title.text), title, paragraph)
               for title, paragraph in zip(solution[bill+1:scripts:2], solution[bill+2:scripts:2])],
        scripts=list(zip(solution[scripts+1::2], solution[scripts+2::2])),
        verdict=verdict, rule=rule, benefit=benefit, income_bands=rule["income_bands_per_person"],
    )


def methods():
    entries, lookup = references()
    return templates.get_template("article.html").render(
        page="methods", site_root="..", title="Methods & sources", entries=entries,
        body=render_blocks(blocks("06"), lookup, ".."),
    )


def about():
    _, lookup = references()
    return templates.get_template("article.html").render(
        page="about", site_root="..", title="AI transparency", body=render_blocks(blocks("07"), lookup, ".."),
    )


def enumerate_options(labels):
    return [(str(index), label) for index, label in enumerate(labels)]


def with_citations(text, lookup):
    return Markup(inline(text, lookup))


templates.filters.update(enumerate_options=enumerate_options, with_citations=with_citations)


def build(destination):
    """Render the three pages and copy their browser assets."""
    pages = {"index.html": home(), "methods/index.html": methods(), "about/index.html": about()}
    for name, html in pages.items():
        path = destination / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(html + "\n", encoding="utf-8")

    for directory in ("static", "data"):
        copytree(ROOT / directory, destination / directory, dirs_exist_ok=True)
    (destination / ".nojekyll").touch()


if __name__ == "__main__":
    destination = ROOT / "dist"
    build(destination)
    print(f"Built static site in {destination}")
