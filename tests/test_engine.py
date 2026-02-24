"""Tests for the folder-enforcer rules engine."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from engine import FolderRules, PatternRule, parse_rules, slugify, suggest, validate


SAMPLE_RULES = """
# Allowed top-level folders
clients
personal
products
research
skills

# Pattern hints
pattern:*research*|*analysis*|*comparison* -> research/
pattern:*client*|*invoice*|*proposal* -> clients/
pattern:*product*|*app*|*tool*|*extension* -> products/
pattern:*tax*|*finance*|*health*|*career* -> personal/
"""


class TestParseRules:
    def test_parses_allowed_folders(self):
        rules = parse_rules(SAMPLE_RULES)
        assert rules.allowed == ["clients", "personal", "products", "research", "skills"]

    def test_parses_patterns(self):
        rules = parse_rules(SAMPLE_RULES)
        assert len(rules.patterns) == 4
        assert rules.patterns[0].target == "research/"
        assert "*research*" in rules.patterns[0].globs

    def test_skips_comments_and_blanks(self):
        rules = parse_rules("# comment\n\nclients\n  \n# another\nresearch")
        assert rules.allowed == ["clients", "research"]
        assert rules.patterns == []

    def test_preserves_raw(self):
        rules = parse_rules(SAMPLE_RULES)
        assert "clients" in rules.raw

    def test_empty_input(self):
        rules = parse_rules("")
        assert rules.allowed == []
        assert rules.patterns == []

    def test_malformed_pattern_ignored(self):
        rules = parse_rules("pattern:*foo* no arrow here")
        assert rules.patterns == []


class TestSlugify:
    def test_basic(self):
        assert slugify("Standing Desk Research") == "standing-desk-research"

    def test_special_chars(self):
        assert slugify("Acme Corp. Invoice #123") == "acme-corp-invoice-123"

    def test_extra_spaces(self):
        assert slugify("  lots   of   spaces  ") == "lots-of-spaces"

    def test_already_slugified(self):
        assert slugify("already-good") == "already-good"


class TestSuggest:
    def setup_method(self):
        self.rules = parse_rules(SAMPLE_RULES)

    def test_pattern_match(self):
        result = suggest(self.rules, "standing desk research", "markdown")
        assert "research/" in result
        assert "standing-desk-research.md" in result
        assert "Matched pattern" in result

    def test_pattern_match_analysis(self):
        result = suggest(self.rules, "competitor analysis Q1", "pdf")
        assert "research/" in result
        assert "competitor-analysis-q1.pdf" in result

    def test_client_pattern(self):
        result = suggest(self.rules, "Acme Corp invoice", "pdf")
        assert "clients/" in result
        assert "acme-corp-invoice.pdf" in result

    def test_product_pattern(self):
        result = suggest(self.rules, "new todo app idea", "markdown")
        assert "products/" in result

    def test_personal_pattern(self):
        result = suggest(self.rules, "tax optimization 2026", "markdown")
        assert "personal/" in result

    def test_category_name_in_description(self):
        result = suggest(self.rules, "skills documentation", "markdown")
        assert "skills/" in result
        assert "Description contains category" in result

    def test_no_match(self):
        result = suggest(self.rules, "random thing", "file")
        assert "No pattern match" in result
        assert "Available categories" in result

    def test_file_type_extension(self):
        result = suggest(self.rules, "meeting notes research", "markdown")
        assert ".md" in result

    def test_file_type_dot_extension(self):
        result = suggest(self.rules, "data export research", ".csv")
        assert ".csv" in result

    def test_folder_type_no_extension(self):
        result = suggest(self.rules, "new research project", "folder")
        assert "research/" in result
        # folder type should not add extension
        assert not result.split("\n")[0].endswith(".md")


class TestValidate:
    def setup_method(self):
        self.rules = parse_rules(SAMPLE_RULES)

    def test_valid_path(self):
        result = validate(self.rules, "clients/acme/invoice.pdf")
        assert "Valid" in result
        assert "clients" in result

    def test_valid_nested(self):
        result = validate(self.rules, "research/standing-desks.md")
        assert "Valid" in result

    def test_invalid_path(self):
        result = validate(self.rules, "misc/random-file.txt")
        assert "Invalid" in result
        assert "misc" in result

    def test_empty_path(self):
        result = validate(self.rules, "")
        assert "Invalid" in result
