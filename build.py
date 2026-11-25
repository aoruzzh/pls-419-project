"""Build the research site as HTML, CSS, JavaScript and JSON files."""
from dataclasses import dataclass
from html import escape, unescape
import json
from pathlib import Path
from posixpath import relpath
import re
from shutil import copytree
import unicodedata

from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup

ROOT = Path(__file__).resolve().parent
templates = Environment(
    loader=FileSystemLoader(ROOT / "templates"),
    autoescape=select_autoescape(),
    trim_blocks=True,
    lstrip_blocks=True,
)

LANGUAGES = {"en": "English", "kk": "Қазақша", "ru": "Русский"}
PAGES = ("home", "methods", "about")
UI = {}
for line in (ROOT / "content" / "ui.txt").read_text(encoding="utf-8").splitlines():
    if line.strip():
        key, *translations = line.split("|")
        UI[key] = dict(zip(LANGUAGES, translations, strict=True))


def location(lang, page):
    parts = [part for part in (lang if lang != "en" else "", page if page != "home" else "") if part]
    return "/".join(parts) or "."


def href(lang, page, target_lang, target_page):
    path = relpath(location(target_lang, target_page), location(lang, page))
    if not path.startswith("."):
        path = "./" + path
    return path + "/"


def page_context(lang, page):
    def text(key):
        return UI[key][lang]

    return {
        "lang": lang,
        "page": page,
        "site_root": relpath(".", location(lang, page)),
        "urls": {target: href(lang, page, lang, target) for target in PAGES},
        "languages": [(code, title, href(lang, page, code, page)) for code, title in LANGUAGES.items()],
        "t": text,
        "messages": {key[3:]: text(key) for key in UI if key.startswith("js_")},
    }


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
    "Daulieva": ("Daulieva and Sagynbay",),
    "Gutova": ("Gutova et al.",),
}


def slug(text):
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")


def read_content(prefix, lang="en"):
    directory = ROOT / "content"
    if lang != "en":
        directory /= lang
    return next(directory.glob(f"{prefix}-*.md")).read_text(encoding="utf-8").strip()


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


def inline(text, lookup, methods_url="./methods/"):
    """Render prose, source URLs, and the two citation forms used in the pack."""
    def link(label, author, year):
        anchor = lookup.get(slug(f"{unescape(author)} {year}"))
        return f'<a class="citation" href="{methods_url}#{anchor}">{label}</a>' if anchor else label

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

    safe = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escape(text, quote=False))
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

    def html(self, lookup, methods_url, table_label):
        if self.kind == "list":
            items = "".join(f"<li>{inline(line[2:], lookup, methods_url)}</li>" for line in self.text.splitlines())
            return Markup(f"<ul>{items}</ul>")
        if self.kind == "table":
            return Markup(f'<div class="table-wrap" tabindex="0" role="region" aria-label="{escape(table_label)}">' +
                          self.table_html(lookup, methods_url) + "</div>")
        tag = {"heading": "h3", "subheading": "h4"}.get(self.kind, "p")
        style = ' class="missing"' if self.text.startswith(("[MISSING:", "[КЕРЕК:", "[НУЖНО:")) else ""
        return Markup(f"<{tag}{style}>{inline(self.text, lookup, methods_url)}</{tag}>")

    def rows(self):
        return [[cell.strip() for cell in row.strip("|").split("|")]
                for row in self.text.splitlines()]

    def table_html(self, lookup, methods_url):
        header, _, *rows = self.rows()
        head = "".join(f'<th scope="col">{inline(cell, lookup, methods_url)}</th>' for cell in header)
        body = "".join(
            f'<tr><th scope="row">{inline(first, lookup, methods_url)}</th>' +
            "".join(f"<td>{inline(cell, lookup, methods_url)}</td>" for cell in rest) + "</tr>"
            for first, *rest in rows
        )
        return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def blocks(prefix, lang="en"):
    # The research Markdown uses headings, plain paragraphs, bullet lists and tables.
    for chunk in re.split(r"\n\s*\n", read_content(prefix, lang)):
        first, _, rest = chunk.partition("\n")
        if first.startswith(("## ", "### ")):
            yield Block("subheading" if first.startswith("### ") else "heading", first.split(" ", 1)[1])
            if rest:
                yield Block("paragraph", rest)
        else:
            kind = "list" if first.startswith("- ") else "table" if first.startswith("|") else "paragraph"
            yield Block(kind, chunk)


def renderer(lookup, context):
    def render(parts):
        return Markup("\n".join(part.html(lookup, context["urls"]["methods"], context["t"]("research_table"))
                                for part in parts))
    return render


def at(parts, title):
    return next(i for i, part in enumerate(parts) if part.text.startswith(title)
                and part.kind in ("heading", "subheading"))


def home(lang):
    _, lookup = references()
    context = page_context(lang, "home")
    text = context["t"]
    original = [list(blocks(f"{i:02d}")) for i in range(6)]
    localized = original if lang == "en" else [list(blocks(f"{i:02d}", lang)) for i in range(6)]
    for i, (source, translation) in enumerate(zip(original, localized)):
        if [part.kind for part in source] != [part.kind for part in translation]:
            raise ValueError(f"Content blocks for {lang}/{i:02d} must match the English layout.")

    hook, problem, data, research, solution, verdict = localized
    _, original_problem, original_data, original_research, original_solution, _ = original
    figure_one, figure_two, gaps, reliability = [
        at(original_data, title) for title in ("Figure 1", "Figure 2", "Where the data", "How far")
    ]
    affected, question = [
        at(original_problem, title) for title in ("Who is affected", "The social-science question")
    ]
    approaches = [at(original_research, f"{i}.") for i in range(1, 5)] + [at(original_research, "Kazakhstan")]
    known = at(original_research, "What is known")
    cases, experiment, bill, scripts = [
        at(original_solution, title) for title in ("Real cases", "Optional:", "The bill", "Citizen explainer scripts")
    ]
    risk_levels = dataset("bill")["risk_levels"]
    rule = dataset("scoring_rule")
    benefit = dataset("birth_benefit_real")
    threshold = rule["income_bands_per_person"][-1]["min"]
    offsets = rule["employment"]["2+"] + rule["children"]["1"]
    close_cases = [(key, threshold + delta, rule["income_bands_per_person"][band]["points"] + offsets, category)
                   for key, delta, band, category in (("below", -1, -2, "C"), ("at", 0, -1, "B"))]
    grouped = lambda value: f"{value:,}" if lang == "en" else f"{value:,}".replace(",", "\u202f")
    context["messages"]["incomeBands"] = [text(f"income_band_{i}") for i in range(len(rule["income_bands_per_person"]))]

    return templates.get_template("index.html").render(
        **context, lookup=lookup, render=renderer(lookup, context), grouped=grouped, close_cases=close_cases,
        purchasing_loss=round(100 * (1 - benefit["rows"][-1]["real"] / benefit["rows"][0]["real"])),
        economy_rows=[benefit["rows"][0], benefit["rows"][-1]], historical_benefit=benefit["rows"][-1]["nominal"],
        hook=hook, problem=problem[:affected], affected=problem[affected:question],
        question=problem[question:], stats=dataset("stats")["cards"],
        data_intro=data[:figure_one], figure_one=data[figure_one:figure_two],
        figure_two=data[figure_two:gaps], gap_heading=data[gaps].text, gaps=data[gaps+1].text.splitlines(),
        reliability=data[reliability:], research_intro=research[:approaches[0]],
        approaches=[research[a:b] for a, b in zip(approaches, approaches[1:])],
        regional=research[approaches[-1]:known], research_summary=research[known+1:],
        solution_intro=solution[:cases], tools=solution[2].rows(),
        cases_heading=solution[cases].text, cases=solution[cases+1:experiment], experiment=solution[experiment:bill],
        bill_heading=solution[bill].text,
        bills=[(risk_levels.get(source_title.text), title, paragraph)
               for source_title, title, paragraph in zip(original_solution[bill+1:scripts:2],
                                                           solution[bill+1:scripts:2], solution[bill+2:scripts:2])],
        scripts=list(zip(solution[scripts+1::2], solution[scripts+2::2])),
        verdict=verdict, income_bands=context["messages"]["incomeBands"],
    )


def article(lang, page, prefix):
    entries, lookup = references()
    context = page_context(lang, page)
    body = renderer(lookup, context)(blocks(prefix, lang))
    if page == "methods":
        rule = list(blocks("02", lang))[2:6]
        body += Markup('<section id="score-rule">') + renderer(lookup, context)(rule) + Markup("</section>")
    return templates.get_template("article.html").render(
        **context,
        title=context["t"](page + "_title"),
        entries=entries if page == "methods" else None,
        body=body,
    )


def enumerate_options(labels):
    return [(str(index), label) for index, label in enumerate(labels)]


def with_citations(text, lookup, methods_url):
    return Markup(inline(text, lookup, methods_url))


templates.filters.update(enumerate_options=enumerate_options, with_citations=with_citations)


def build(destination):
    """Render every language edition and copy their shared browser assets."""
    for lang in LANGUAGES:
        pages = {"home": home(lang), "methods": article(lang, "methods", "06"), "about": article(lang, "about", "07")}
        for page, html in pages.items():
            path = destination / location(lang, page) / "index.html"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(html + "\n", encoding="utf-8")

    for directory in ("static", "data"):
        copytree(ROOT / directory, destination / directory, dirs_exist_ok=True)
    (destination / ".nojekyll").touch()


if __name__ == "__main__":
    destination = ROOT / "dist"
    build(destination)
    print(f"Built static site in {destination}")
