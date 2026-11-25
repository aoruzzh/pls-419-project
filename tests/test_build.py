from html.parser import HTMLParser
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from urllib.parse import urljoin, urlsplit

from build import build


class Page(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.ids = set()
        self.links = []
        self.feed(html)

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if "id" in attrs:
            self.ids.add(attrs["id"])
        if tag in ("a", "link", "script"):
            url = attrs.get("href") or attrs.get("src")
            if url:
                self.links.append(url)


class StaticBuildTests(TestCase):
    @classmethod
    def setUpClass(cls):
        temporary = TemporaryDirectory()
        cls.addClassCleanup(temporary.cleanup)
        cls.output = Path(temporary.name) / "dist"
        build(cls.output)

    def test_build_contains_pages_and_browser_assets(self):
        home = (self.output / "index.html").read_text(encoding="utf-8")
        self.assertTrue({"problem", "data", "research", "solution", "verdict", "simulator"} <= Page(home).ids)
        self.assertIn("./methods/#undp-kazakhstan-n-d", Page(home).links)
        self.assertIn("./methods/#bizmedia-kz-2026", Page(home).links)
        self.assertIn("which research and design suggestions they accepted or rejected",
                      (self.output / "about/index.html").read_text(encoding="utf-8"))
        self.assertTrue((self.output / ".nojekyll").is_file())
        for name in ("site.css", "site.mjs", "charts.mjs", "score.mjs", "locale.mjs"):
            self.assertTrue((self.output / "static" / name).is_file())
        for name, field in (("scoring_rule", "income_bands_per_person"), ("birth_benefit_real", "rows")):
            data = json.loads((self.output / "data" / f"{name}.json").read_text(encoding="utf-8"))
            self.assertTrue(data[field])

    def test_language_editions_render_the_problem_and_case_comparison(self):
        examples = (
            ("en", "", "The issue is exclusion", "When state registries define"),
            ("kk", "kk/", "Мәселе", "Мемлекеттік тізілімдер"),
            ("ru", "ru/", "Проблема", "Когда государственные реестры"),
        )
        for lang, prefix, issue, question in examples:
            with self.subTest(lang=lang):
                home = (self.output / f"{prefix}index.html").read_text(encoding="utf-8")
                self.assertIn(f'<html lang="{lang}">', home)
                self.assertIn(f"<strong>{issue}", home)
                self.assertIn(f"<strong>{question}", home)
                self.assertEqual(home.count('data-income-point='), 2)
                self.assertEqual(home.count('data-language-link'), 3)
                self.assertIn('id="site-messages"', home)
                for page in ("methods", "about"):
                    content = (self.output / prefix / page / "index.html").read_text(encoding="utf-8")
                    self.assertIn(f'<html lang="{lang}">', content)

    def test_local_links_resolve_at_root_and_in_hosting_subdirectory(self):
        for prefix in ("/", "/scored-for-support/"):
            origin = "https://example.test"
            for page_path in self.output.rglob("*.html"):
                path = page_path.relative_to(self.output)
                page_url = origin + prefix + path.parent.as_posix().removeprefix(".").strip("/")
                page_url = page_url.rstrip("/") + "/"
                page = Page(page_path.read_text(encoding="utf-8"))
                for link in page.links:
                    destination = urlsplit(urljoin(page_url, link))
                    if destination.netloc != "example.test":
                        continue
                    with self.subTest(page_url=page_url, link=link):
                        self.assertTrue(destination.path.startswith(prefix))
                        target = self.output / destination.path.removeprefix(prefix)
                        if destination.path.endswith("/"):
                            target /= "index.html"
                        self.assertTrue(target.is_file())
                        if destination.fragment:
                            target_page = Page(target.read_text(encoding="utf-8"))
                            self.assertIn(destination.fragment, target_page.ids)

    def test_responsive_photos_and_translated_credits(self):
        images = json.loads((self.output / "data/images.json").read_text())
        for name, info in images.items():
            for width in (640, 1024, 1600):
                for ext in ("jpg", "avif", "webp"):
                    asset = self.output / f"static/img/{name}-{width}.{ext}"
                    self.assertTrue(asset.is_file(), asset)
                    if ext == "webp":
                        self.assertLess(asset.stat().st_size, 200000)
            self.assertTrue(info["credit"])
            if not info["generated"]:
                self.assertTrue(info["licence_url"])
        for prefix, caption in [("", "AI-generated illustration"), ("kk/", "ЖИ жасаған иллюстрация"), ("ru/", "Иллюстрация, созданная ИИ")]:
            html = (self.output / prefix / "index.html").read_text()
            self.assertEqual(html.count("<picture>"), len(images))
            self.assertEqual(html.count(caption), sum(info["generated"] for info in images.values()))
            self.assertIn('width="1250" height="703" alt="', html)
            self.assertNotIn('height="703" alt=""', html)
            self.assertIn("110\u202f846" if prefix else "110,846", html)
            for name in images:
                self.assertIn(f"{name}-1600.avif 1600w", html)
