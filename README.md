# Link Building Rank Checker

This project provides a small Python utility that helps link builders keep an eye on how a target site ranks for specific search queries compared to competitor domains. The tool works with stored SERP (search engine result page) data for offline analysis and can also fetch live data from [SerpAPI](https://serpapi.com/) when an API key is available.

## Features

- Compare the rank of multiple domains for a given search query.
- Works offline using pre-downloaded SERP JSON files.
- Optional SerpAPI integration for live lookups when the `SERPAPI_API_KEY` environment variable (or `--api-key` argument) is provided.
- Simple tabular CLI output that is easy to copy into outreach reports.

## Installation

The project has no mandatory dependencies for offline analysis. Install the optional `requests` package if you plan to fetch live SERP data:

```bash
pip install -r requirements.txt  # only required for live lookups
```

You can also install `pytest` if you would like to run the tests locally.

## Usage

Prepare a SERP JSON file (for example, exported from SerpAPI) and run:

```bash
python -m link_tool.rank_checker "best link building tools" example.com competitor.com --results-file path/to/serp.json
```

When a SerpAPI key is available you can omit `--results-file` and fetch live data:

```bash
export SERPAPI_API_KEY="your_api_key"
python -m link_tool.rank_checker "best link building tools" example.com competitor.com
```

Example output:

```
Domain            | Rank | Matched URL
-----------------+------+-------------------------------------------------
example.com       | 1    | https://www.example.com/link-building
competitor.com    | 3    | https://www.competitor.com/blog/ranking-guide
```

## Running the Tests

Install `pytest` and execute:

```bash
pytest
```

## Project Structure

- `link_tool/` – core library code and CLI entry point.
- `tests/` – automated tests and sample SERP fixtures.
