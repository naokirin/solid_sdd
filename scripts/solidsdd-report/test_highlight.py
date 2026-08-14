#!/usr/bin/env python3
"""Unit tests for solidsdd-report highlight.py."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import highlight  # noqa: E402


class HighlightTests(unittest.TestCase):
    def test_json_keys_and_strings_distinguished(self) -> None:
        out = highlight.highlight_json('{"a": "b", "n": 1, "t": true, "z": null}')
        self.assertIn('<span class="tok-key">&quot;a&quot;</span>', out)
        self.assertIn('<span class="tok-str">&quot;b&quot;</span>', out)
        self.assertIn('<span class="tok-num">1</span>', out)
        self.assertIn('<span class="tok-bool">true</span>', out)
        self.assertIn('<span class="tok-null">null</span>', out)

    def test_json_escapes_html(self) -> None:
        out = highlight.highlight_json('{"a": "<script>"}')
        self.assertNotIn("<script>", out)
        self.assertIn("&lt;script&gt;", out)

    def test_yaml_key_and_scalar(self) -> None:
        out = highlight.highlight_yaml("title: Inventory API\ncount: 3\nok: true\n")
        self.assertIn('<span class="tok-key">title</span>', out)
        self.assertIn('<span class="tok-str">Inventory API</span>', out)
        self.assertIn('<span class="tok-num">3</span>', out)
        self.assertIn('<span class="tok-bool">true</span>', out)

    def test_yaml_comment(self) -> None:
        out = highlight.highlight_yaml("a: 1 # note\n")
        self.assertIn('<span class="tok-comment"># note</span>', out)

    def test_gherkin_keyword_contrasts_with_prose(self) -> None:
        out = highlight.highlight_gherkin("Scenario: Do a thing\n  Given a precondition\n")
        self.assertIn('<span class="tok-kw">Scenario</span>', out)
        self.assertIn('<span class="tok-kw">Given</span>', out)
        # Prose stays unwrapped (near-white inherited from the surrounding element).
        self.assertIn("Do a thing", out)
        self.assertNotIn('<span class="tok-kw">Do a thing</span>', out)

    def test_gherkin_tag_line(self) -> None:
        out = highlight.highlight_gherkin("@R1 @SC1\nScenario: X\n")
        self.assertIn('<span class="tok-tag">@R1 @SC1</span>', out)

    def test_ocl_keyword_and_comment(self) -> None:
        out = highlight.highlight_ocl("-- doc\ncontext Thing\ninv: self.x > 0\n")
        self.assertIn('<span class="tok-comment">-- doc</span>', out)
        self.assertIn('<span class="tok-kw">context</span>', out)
        self.assertIn('<span class="tok-kw">self</span>', out)

    def test_graphql_keyword(self) -> None:
        out = highlight.highlight_graphql("type Query {\n  thing: Thing\n}\n")
        self.assertIn('<span class="tok-kw">type</span>', out)

    def test_detect_language_by_suffix(self) -> None:
        self.assertEqual(highlight.detect_language(Path("a.json")), "json")
        self.assertEqual(highlight.detect_language(Path("a.yaml")), "yaml")
        self.assertEqual(highlight.detect_language(Path("a.yml")), "yaml")
        self.assertEqual(highlight.detect_language(Path("a.feature")), "gherkin")
        self.assertEqual(highlight.detect_language(Path("a.ocl")), "ocl")
        self.assertEqual(highlight.detect_language(Path("a.graphql")), "graphql")
        self.assertEqual(highlight.detect_language(Path("a.txt")), "text")

    def test_embed_file_truncates_large_files(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        path = Path(tmp.name) / "big.json"
        path.write_text('{"a": "' + ("x" * 200) + '"}', encoding="utf-8")
        result = highlight.embed_file(path, max_bytes=50)
        self.assertTrue(result["truncated"])
        self.assertGreater(result["original_bytes"], 50)

    def test_embed_file_no_truncation_for_small_files(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        path = Path(tmp.name) / "small.json"
        path.write_text('{"a": 1}', encoding="utf-8")
        result = highlight.embed_file(path)
        self.assertFalse(result["truncated"])
        self.assertEqual(result["language"], "json")

    def test_token_css_has_no_loud_colors(self) -> None:
        # Regression guard for the "avoid loud yellow/chartreuse" constraint:
        # none of the fixed token colors should be a pure/near-pure yellow.
        for line in highlight.TOKEN_CSS.splitlines():
            self.assertNotIn("#ff0", line.lower())
            self.assertNotIn("#ffff00", line.lower())


if __name__ == "__main__":
    unittest.main()
