"""SKILL.md follows the Agent Skills format; docs and the HTML guide stay consistent with the engine."""
from __future__ import annotations

import re
import unittest
from html.parser import HTMLParser

from helpers import ROOT, SKILL

import workflow  # noqa: E402

# Evidence badge text per language, keyed by the badge's data-evidence value.
LABELS = {
    "en": {"tested": "Tested", "checked": "Checked in installed version", "docs": "Vendor docs",
           "unverified": "Unverified"},
    "ar": {"tested": "مُختبَر", "checked": "مفحوص في النسخة المثبّتة", "docs": "حسب الوثائق الرسمية",
           "unverified": "غير متحقَّق منه"},
}
INSTALL_COMMANDS = {"install", "update", "doctor", "uninstall", "add-template", "list-templates"}


def frontmatter(text: str) -> tuple:
    assert text.startswith("---\n"), "SKILL.md must start with YAML frontmatter"
    end = text.index("\n---\n", 4)
    return text[4:end], text[end + 5:]


def code_text(path) -> str:
    """Only the code in a document: fenced blocks and inline spans (Markdown), <code>/<pre> (HTML)."""
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".html":
        parts = re.findall(r"<(?:code|pre)[^>]*>(.*?)</(?:code|pre)>", text, re.S)
        return "\n".join(re.sub(r"<[^>]+>", "", p) for p in parts)
    blocks = re.findall(r"```[^\n]*\n(.*?)```", text, re.S)
    spans = re.findall(r"`([^`\n]+)`", re.sub(r"```.*?```", "", text, flags=re.S))
    return "\n".join(blocks + spans)


def public_text_files() -> list:
    files = [ROOT / "README.md", ROOT / "index.html", SKILL / "SKILL.md"]
    files += sorted((ROOT / "docs").glob("*.md")) + sorted((SKILL / "references").glob("*.md"))
    return [f for f in files if f.exists()]


class SkillFormatTest(unittest.TestCase):
    def setUp(self) -> None:
        self.front, self.body = frontmatter((SKILL / "SKILL.md").read_text(encoding="utf-8"))

    def field(self, name: str) -> str:
        match = re.search(rf"^{name}:\s*(.+)$", self.front, re.M)
        self.assertIsNotNone(match, f"frontmatter field {name} missing")
        return match.group(1).strip().strip('"')

    def test_name_follows_the_spec_and_matches_the_folder(self) -> None:
        name = self.field("name")
        self.assertEqual(name, SKILL.name)
        self.assertRegex(name, r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
        self.assertLessEqual(len(name), 64)

    def test_description_and_compatibility_lengths(self) -> None:
        description = self.field("description")
        self.assertTrue(1 <= len(description) <= 1024)
        self.assertIn("ai-dev-workflow", description)
        self.assertLessEqual(len(self.field("compatibility")), 500)

    def test_manual_only_settings_are_present(self) -> None:
        self.assertEqual(self.field("disable-model-invocation"), "true")
        openai = (SKILL / "agents" / "openai.yaml").read_text(encoding="utf-8")
        self.assertRegex(openai, r"(?m)^\s+allow_implicit_invocation:\s*false\s*$")

    def test_metadata_values_are_strings(self) -> None:
        block = re.search(r"^metadata:\n((?:  .+\n)+)", self.front, re.M)
        self.assertIsNotNone(block)
        for line in block.group(1).splitlines():
            key, _, value = line.strip().partition(":")
            self.assertTrue(value.strip(), key)
        self.assertIn('version: "1.0.0"', block.group(1))

    def test_body_is_short_and_hard_rules_come_first(self) -> None:
        self.assertLess(len(self.body.splitlines()), 500)
        first = re.search(r"^## (.+)$", self.body, re.M).group(1)
        self.assertTrue(first.startswith("Hard rules"), first)

    def test_linked_and_stage_references_exist(self) -> None:
        for link in re.findall(r"\]\((references/[^)]+)\)", self.body):
            self.assertTrue((SKILL / link).exists(), link)
        for path in set(workflow.REFERENCE.values()):
            self.assertTrue((SKILL / path).exists(), path)


class ConsistencyTest(unittest.TestCase):
    def test_documented_engine_commands_exist(self) -> None:
        parser = workflow.build_parser()
        commands = set(parser._subparsers._group_actions[0].choices)  # noqa: SLF001
        for path in public_text_files():
            for command in re.findall(r"workflow\.py[ \t]+([a-z][a-z-]*)", code_text(path)):
                self.assertIn(command, commands, f"{path.name}: workflow.py {command}")

    def test_documented_installer_commands_exist(self) -> None:
        for path in public_text_files():
            for command in re.findall(r"install\.py[ \t]+([a-z][a-z-]*)", code_text(path)):
                self.assertIn(command, INSTALL_COMMANDS, f"{path.name}: install.py {command}")

    def test_one_name_and_one_invocation_syntax(self) -> None:
        for path in [ROOT / "README.md", ROOT / "index.html"]:
            if path.exists():
                text = path.read_text(encoding="utf-8")
                self.assertIn("/ai-dev-workflow", text, path.name)
                self.assertIn("$ai-dev-workflow", text, path.name)
        for path in public_text_files():
            self.assertNotIn("develop-feature", path.read_text(encoding="utf-8"), path.name)

    def test_no_numeric_limits_in_the_shipped_rules(self) -> None:
        text = (ROOT / "examples" / "templates" / "example-spec-template.rules.json").read_text(encoding="utf-8").lower()
        for word in ("min_", "max_", "minimum", "maximum", "at least", "at most"):
            self.assertNotIn(word, text)


class _Collector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title = ""
        self._in_title = False
        self.badges = []
        self._badge = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "title":
            self._in_title = True
        if "data-evidence" in attrs:
            self._badge = [attrs.get("data-evidence-key"), attrs["data-evidence"], ""]

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        if self._badge is not None:
            self.badges.append((self._badge[0], self._badge[1], self._badge[2].strip()))
            self._badge = None

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        if self._badge is not None:
            self._badge[2] += data


def language_parts(html: str) -> dict:
    """The Arabic and English halves of index.html (the Arabic container comes first)."""
    ar, en, end = html.index('<div id="ar"'), html.index('<div id="en"'), html.index("</main>")
    return {"ar": html[ar:en], "en": html[en:end]}


@unittest.skipUnless((ROOT / "index.html").exists(), "index.html not generated yet")
class HtmlGuideTest(unittest.TestCase):
    def setUp(self) -> None:
        self.html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.parts = language_parts(self.html)

    def test_loads_nothing_from_the_network(self) -> None:
        forbidden = [
            r"<script[^>]*\ssrc=", r"<link[^>]+href=[\"']?https?:", r"<img[^>]+src=[\"']?https?:",
            r"@import", r"url\(\s*[\"']?https?:", r"\bfetch\(", r"XMLHttpRequest", r"<iframe",
        ]
        for pattern in forbidden:
            self.assertIsNone(re.search(pattern, self.html, re.I), pattern)

    def test_parses_and_has_both_languages_and_toggles(self) -> None:
        collector = _Collector()
        collector.feed(self.html)
        self.assertIn("AIDevWorkflow", collector.title)
        self.assertIn('<div id="ar" class="lang" lang="ar" dir="rtl">', self.html)
        self.assertIn('<div id="en" class="lang" lang="en" dir="ltr">', self.html)
        self.assertIn('id="lang-toggle"', self.html)
        self.assertIn('id="theme-toggle"', self.html)

    def test_each_language_uses_its_own_evidence_labels_and_both_agree(self) -> None:
        keyed = {}
        for lang, part in self.parts.items():
            collector = _Collector()
            collector.feed(part)
            self.assertTrue(collector.badges, lang)
            for key, evidence, label in collector.badges:
                self.assertIn(evidence, LABELS[lang], f"{lang}: {key}")
                self.assertEqual(label, LABELS[lang][evidence], f"{lang}: {key}")
            keyed[lang] = {key: evidence for key, evidence, _ in collector.badges if key}
        self.assertTrue(keyed["en"])
        self.assertEqual(keyed["ar"], keyed["en"])

    def test_both_languages_have_the_same_sections_and_links_stay_inside(self) -> None:
        ids = {lang: re.findall(rf'<section id="{lang}-([a-z-]+)"', part) for lang, part in self.parts.items()}
        self.assertTrue(ids["en"])
        self.assertEqual(ids["ar"], ids["en"])
        for lang, part in self.parts.items():
            targets = set(re.findall(rf'\bid="({lang}-[a-z-]+)"', part))
            for target in re.findall(r'<a\s[^>]*href="#([^"]*)"', part):
                self.assertTrue(target.startswith(f"{lang}-"), f"{lang} links to #{target}")
                self.assertIn(target, targets, f"{lang}: #{target} does not exist")
            nav = re.search(rf'<nav class="topnav nav-{lang}"[^>]*>(.*?)</nav>', self.html, re.S)
            self.assertIsNotNone(nav, f"{lang}: top navigation missing")
            for target in re.findall(r'href="#([^"]+)"', nav.group(1)):
                self.assertIn(target, targets, f"{lang}: top navigation links to missing #{target}")

    def test_every_command_block_is_marked_terminal_or_chat(self) -> None:
        def kinds(text: str) -> list:
            return [classes.split()[0] for classes in re.findall(r'<div class="act ([a-z ]+)">', text)]

        self.assertTrue(kinds(self.html))
        self.assertLessEqual(set(kinds(self.html)), {"term", "chat"})
        self.assertEqual(kinds(self.parts["ar"]), kinds(self.parts["en"]))


if __name__ == "__main__":
    unittest.main()
