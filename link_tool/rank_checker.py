"""Tools for checking search rankings of target and competitor domains."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Sequence
from urllib.parse import urlparse

try:  # pragma: no cover - requests is optional for offline usage
    import requests
except Exception:  # pragma: no cover - handled gracefully when missing
    requests = None


@dataclass(frozen=True)
class RankingResult:
    """Represents the ranking information for a single domain."""

    domain: str
    rank: Optional[int]
    matched_url: Optional[str]

    def to_row(self) -> List[str]:
        """Return a human-readable table row."""
        position = str(self.rank) if self.rank is not None else "-"
        return [self.domain, position, self.matched_url or "-"]


class RankChecker:
    """High level API for retrieving and inspecting search rankings.

    The checker can work entirely offline using previously downloaded SERP
    (search engine result page) data, or it can fetch fresh data using
    `serpapi.com` when an API key is supplied.
    """

    SERP_API_URL = "https://serpapi.com/search"

    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        engine: str = "google",
        location: Optional[str] = None,
        device: Optional[str] = None,
    ) -> None:
        self.api_key = api_key or os.getenv("SERPAPI_API_KEY")
        self.engine = engine
        self.location = location
        self.device = device

    # ------------------------------------------------------------------
    # Public helpers
    def check_rank(
        self,
        query: str,
        domains: Sequence[str],
        *,
        num_results: int = 20,
        results_file: Optional[str] = None,
        serp_data: Optional[Dict[str, Any]] = None,
    ) -> List[RankingResult]:
        """Return ranking information for each requested domain.

        Args:
            query: The search query to evaluate.
            domains: Iterable of domains that should be compared.
            num_results: Number of search results to fetch (SerpAPI only).
            results_file: Optional path to a JSON file containing SERP data.
            serp_data: Pre-parsed SERP data, mainly for unit testing.
        """

        serp = serp_data or self._get_serp_data(
            query=query,
            num_results=num_results,
            results_file=results_file,
        )
        organic_results = serp.get("organic_results", []) if serp else []
        results: List[RankingResult] = []
        for domain in domains:
            rank, matched_url = self._find_rank(organic_results, domain)
            results.append(RankingResult(domain=domain, rank=rank, matched_url=matched_url))
        return results

    def format_results_table(self, results: Sequence[RankingResult]) -> str:
        """Return a pretty formatted table for command-line output."""

        headers = ["Domain", "Rank", "Matched URL"]
        column_widths = [len(h) for h in headers]
        table_rows: List[List[str]] = []
        for result in results:
            row = result.to_row()
            table_rows.append(row)
            for index, cell in enumerate(row):
                column_widths[index] = max(column_widths[index], len(cell))

        def _format_row(row: Sequence[str]) -> str:
            return " | ".join(cell.ljust(column_widths[idx]) for idx, cell in enumerate(row))

        line = "-+-".join("-" * width for width in column_widths)
        parts = [_format_row(headers), line]
        parts.extend(_format_row(row) for row in table_rows)
        return "\n".join(parts)

    # ------------------------------------------------------------------
    # Internal helpers
    def _get_serp_data(
        self,
        *,
        query: str,
        num_results: int,
        results_file: Optional[str],
    ) -> Dict[str, Any]:
        if results_file:
            return self._load_serp_from_file(results_file)
        return self._fetch_serp_from_api(query=query, num_results=num_results)

    def _fetch_serp_from_api(self, *, query: str, num_results: int) -> Dict[str, Any]:
        if not self.api_key:
            raise RuntimeError(
                "No SERP API key available. Provide one via the constructor or the SERPAPI_API_KEY environment variable."
            )
        if requests is None:  # pragma: no cover - depends on optional dependency
            raise RuntimeError("The requests package is required to fetch live SERP data.")

        params = {
            "api_key": self.api_key,
            "engine": self.engine,
            "q": query,
            "num": num_results,
        }
        if self.location:
            params["location"] = self.location
        if self.device:
            params["device"] = self.device

        response = requests.get(self.SERP_API_URL, params=params, timeout=30)
        response.raise_for_status()
        return response.json()

    @staticmethod
    def _load_serp_from_file(path: str) -> Dict[str, Any]:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)

    @staticmethod
    def _normalize_domain(domain: str) -> str:
        domain = domain.lower().strip()
        if domain.startswith("http://") or domain.startswith("https://"):
            domain = urlparse(domain).netloc
        if domain.startswith("www."):
            domain = domain[4:]
        return domain

    @classmethod
    def _match_domain(cls, candidate_url: str, target_domain: str) -> bool:
        parsed = urlparse(candidate_url)
        candidate_domain = parsed.netloc.lower()
        if candidate_domain.startswith("www."):
            candidate_domain = candidate_domain[4:]
        normalized_target = cls._normalize_domain(target_domain)
        if candidate_domain == normalized_target:
            return True
        return candidate_domain.endswith("." + normalized_target)

    @classmethod
    def _find_rank(
        cls,
        organic_results: Iterable[Dict[str, Any]],
        target_domain: str,
    ) -> (Optional[int], Optional[str]):
        normalized = cls._normalize_domain(target_domain)
        for index, result in enumerate(organic_results, start=1):
            url = result.get("link") or result.get("displayed_link")
            if not url:
                continue
            if cls._match_domain(url, normalized):
                return index, url
        return None, None


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Command-line entry point."""

    import argparse

    parser = argparse.ArgumentParser(description="Check search rankings for target and competitor domains.")
    parser.add_argument("query", help="Search term to look up")
    parser.add_argument("target", help="Primary domain or URL to track")
    parser.add_argument(
        "competitors",
        nargs="*",
        help="Additional competitor domains to compare against",
    )
    parser.add_argument("--results-file", help="Path to a JSON SERP file to use instead of live lookup")
    parser.add_argument("--num-results", type=int, default=20, help="Number of results to request from the SERP API")
    parser.add_argument("--engine", default="google", help="Search engine to use with the SERP API")
    parser.add_argument("--location", help="Location parameter for the SERP API")
    parser.add_argument("--device", help="Device type for the SERP API (desktop, mobile, tablet)")
    parser.add_argument("--api-key", help="SERP API key. Overrides the SERPAPI_API_KEY environment variable")

    args = parser.parse_args(argv)

    checker = RankChecker(
        api_key=args.api_key,
        engine=args.engine,
        location=args.location,
        device=args.device,
    )
    domains = [args.target] + list(args.competitors)
    results = checker.check_rank(
        args.query,
        domains,
        num_results=args.num_results,
        results_file=args.results_file,
    )
    print(checker.format_results_table(results))
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI execution
    raise SystemExit(main())
