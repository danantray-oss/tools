import json
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from link_tool.rank_checker import RankChecker, RankingResult


def load_sample_data():
    fixture_path = Path(__file__).parent / "tests_data" / "sample_serp.json"
    with fixture_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def test_normalize_domain_removes_protocol_and_www():
    assert RankChecker._normalize_domain("https://www.Example.com") == "example.com"


def test_find_rank_exact_domain_match():
    data = load_sample_data()
    rank, url = RankChecker._find_rank(data["organic_results"], "example.com")
    assert rank == 1
    assert url == "https://www.example.com/link-building"


def test_find_rank_matches_subdomain():
    data = load_sample_data()
    rank, url = RankChecker._find_rank(data["organic_results"], "domain.com")
    assert rank == 3
    assert url == "https://sub.domain.com/article"


def test_check_rank_returns_all_domains():
    data = load_sample_data()
    checker = RankChecker()
    results = checker.check_rank(
        query="best link building tools",
        domains=["example.com", "competitor-two.org", "missing-site.com"],
        serp_data=data,
    )

    assert [result.rank for result in results] == [1, 4, None]
    assert results[1].matched_url == "https://www.competitor-two.org/overview"


def test_format_results_table_creates_columns():
    results = [
        RankingResult(domain="example.com", rank=1, matched_url="https://example.com"),
        RankingResult(domain="missing.com", rank=None, matched_url=None),
    ]
    checker = RankChecker()
    table = checker.format_results_table(results)
    assert "example.com" in table
    assert "missing.com" in table
    assert "-" in table  # indicates missing rank
