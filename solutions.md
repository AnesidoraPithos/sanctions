# Solutions Log

Running record of bug fixes and improvements implemented across the project.

---

## 2026-03-25 — Report UI Fixes + Subsidiary Search Improvements

### Problem Summary

Three distinct issues were identified:

1. **Intelligence Report tab was broken** — the markdown renderer used a chained `.replace()` approach that corrupted all non-heading content (every `\n` was turned into `</h1>\n`), causing numbered reference lists to run together, links to be unclickable, and `[Source: url]` citations to render as plain text. Risk scoring appeared as an unstyled paragraph.

2. **Network Relations tab showed Wikipedia as plain text** — the `company_dict` built by `_search_wikipedia_subsidiaries()` had no `reference_url` field, so the frontend rendered "Wikipedia" as plain text instead of a hyperlink to the actual page.

3. **Low subsidiary coverage** — only Wikipedia and DuckDuckGo were used as subsidiary sources, returning around 8 results for well-known companies like Huawei. High-quality sources such as greyb.com were untapped.

---

### Change 1 — Fix Intelligence Report Markdown Renderer

**File:** `frontend/app/results/[id]/page.tsx`

**What changed:**

Replaced the broken inline `.replace()` chain with a standalone `renderMarkdown(text)` function defined before the component. The renderer processes the report line-by-line and:

- Converts `# `, `## `, `### ` headings to `<h1>`, `<h2>`, `<h3>` (open and close on the same line).
- Converts ordered list lines (`1. ...`) to `<ol><li>...</li></ol>`, opening `<ol>` on the first item and closing it on a blank or non-list line.
- Converts unordered list lines (`- ` or `* `) to `<ul><li>...</li></ul>` with the same open/close logic.
- Converts blank lines to `<br/>` after closing any open list.
- Wraps all other non-empty lines in `<p>...</p>`.
- Detects `Risk Level:` paragraphs and renders them as a styled callout box (dark background, amber left border) with the risk header on its own line and each scoring component (`|`-separated) on its own bullet line.

Inline processing applied to all elements:
- `[Source: https://...]` → compact `<a href="...">[Source]</a>` citation
- `[text](url)` → `<a href="url" target="_blank">text</a>`
- `**text**` → `<strong>text</strong>`
- Bare `https://...` URLs → clickable `<a>` tags (covers the References section)

---

### Change 2 — Add Wikipedia `reference_url` for Network Relations

**File:** `agents/research_agent.py` — `_search_wikipedia_subsidiaries()`

**What changed:**

Before building `company_dict` for each extracted entity, the page URL is now computed from `page_title`:

```python
wiki_url = f"https://en.wikipedia.org/wiki/{page_title.replace(' ', '_')}"
```

This URL is stored as `'reference_url': wiki_url` in `company_dict`. The frontend's `EntityCard` component already renders `reference_url` as a hyperlink when present, so "Wikipedia" now links directly to the relevant page.

---

### Change 3 — Add Google Search for Subsidiaries

**Files:** `agents/research_agent.py`, `backend/requirements.txt`, `frontend/app/results/[id]/page.tsx`

#### 3a. Dependency

Added `googlesearch-python==1.2.3` to `backend/requirements.txt`.

#### 3b. Import

Added a guarded import in `research_agent.py`:

```python
try:
    from googlesearch import search as google_search
    GOOGLE_SEARCH_AVAILABLE = True
except ImportError:
    GOOGLE_SEARCH_AVAILABLE = False
```

If the package is not installed, the method returns `[]` gracefully with a warning log.

#### 3c. New method: `_search_google_subsidiaries(company_name)`

Logic:
1. Builds two queries: a `site:insights.greyb.com` query and a general subsidiaries query.
2. Calls `google_search()` for each, collecting up to 5 URLs per query, deduplicating across queries.
3. Sorts URLs so greyb.com results are tried first; takes the top 3.
4. For each URL: fetches with `requests.get()` (15 s timeout, browser-like User-Agent), strips nav/footer/script/style noise with BeautifulSoup, truncates to 15,000 characters, and passes to the LLM with the same pipe-delimited extraction prompt used by `_search_subsidiaries_duckduckgo`.
5. Parses LLM output with the same validation logic (strips leading numbers, filters placeholders, calls `_validate_company_name`).
6. Returns a list of subsidiary dicts with `source='google'` and `reference_url=<source URL>`.
7. `time.sleep(2)` between Google requests to avoid rate-limiting. Entire method wrapped in `try/except` returning `[]` on any failure.

#### 3d. Wired into the main flow

In the Wikipedia + DuckDuckGo fallback path, after the existing DuckDuckGo call:

```python
google_subs = self._search_google_subsidiaries(parent_company_name)
if google_subs:
    # deduplicate by name (case-insensitive) before merging
    for sub in google_subs:
        if sub['name'].lower() not in seen_names:
            subsidiaries.append(sub)
            seen_names.add(sub['name'].lower())
    data_sources_tried.append('google')
```

The `method_label` is now built dynamically from `data_sources_tried` (e.g. `wikipedia+duckduckgo+google`).

`formatSourceName` in `page.tsx` updated: `case 'google': return 'Google'`.

---

### Verification Steps

1. Install new dependency: `pip install -r backend/requirements.txt`
2. Start backend: `uvicorn app:app --reload` (from `backend/`)
3. Start frontend: `npm run dev` (from `frontend/`)
4. Search for **Huawei** with network tier enabled.
   - **Report tab:** numbered references should be clickable links; risk block should appear as an amber callout box.
   - **Network Relations tab:** Wikipedia entries should show a clickable "Wikipedia" link.
   - **Subsidiaries count:** should exceed the previous baseline of ~8; Google/greyb.com results should be visible with source labelled "Google".
