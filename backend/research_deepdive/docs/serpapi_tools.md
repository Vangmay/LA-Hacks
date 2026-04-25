# SerpApi / Google Scholar Tool Notes

These notes are implementation guidance for the SerpApi Google Scholar tools in
`backend/research_deepdive/tools.py`.

Official docs:

- Google Scholar Organic Results API: https://serpapi.com/google-scholar-organic-results
- Search API: https://serpapi.com/search-api
- Google Scholar Cite API: https://serpapi.com/google-scholar-cite-api

## Role In The Pipeline

SerpApi is not the canonical paper graph. Use it to supplement Semantic Scholar
when:

- Semantic Scholar search misses a title or phrase;
- Google Scholar snippets expose useful wording;
- you need corroborating citation/version metadata;
- you need broad discovery for obscure phrases, reproductions, or critiques.

## Core Request

Endpoint:

```text
GET https://serpapi.com/search?engine=google_scholar
```

Common parameters:

- `engine=google_scholar`
- `q=<query>`
- `api_key=<SERPAPI_API_KEY>`
- `start=<pagination offset>`
- `num=<result count when supported>`
- `as_ylo=<lower publication year>`
- `as_yhi=<upper publication year>`
- `cites=<Google Scholar cites id>` for cited-by searches
- `cluster=<Google Scholar cluster id>` for all-versions / related discovery
- `scisbd=1|2` for recently added articles sorted by date

The tool registry splits these behaviors into:

- `google_scholar_search`
- `google_scholar_cited_by_search`
- `google_scholar_related_pages_search`
- `google_scholar_cite_formats`

## Expected Output

The docs describe Google Scholar results as `organic_results`. Results may
include:

- `position`
- `title`
- `result_id`
- `link`
- `snippet`
- `publication_info`
- `resources`
- `inline_links`
- `cited_by`
- `versions`
- `related_pages_link`

Store the raw `result_id` and query parameters. They are useful for citation and
version follow-up calls.

## Usage Rules

- Use precise queries first, especially exact titles and quoted method names.
- Record snippets but do not treat snippets as full-paper evidence.
- Map high-value results back into Semantic Scholar with title/DOI/arXiv lookup
  whenever possible.
- Label SerpApi-derived papers as `serpapi` until resolved.
- Do not scrape Google Scholar directly; use the configured API.
