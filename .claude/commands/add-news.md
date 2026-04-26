# Add news

Add a news item to `data/news.yaml` from a URL.

## Steps

1. **Fetch the article** at the URL provided in $ARGUMENTS using WebFetch. Extract: title, publication date, and the 3–5 most important facts (numbers, model names, key claims).

2. **Determine the `type`** from this list:
   - `update` — new model release, product announcement, company news
   - `new-feature` — new feature on this site
   - `new-content` — new article/animation/map on this site
   - `research` — paper or research finding

3. **Write a concise bilingual entry** (EN + FR). Target: 2–3 sentences each. Include concrete numbers when available (scores, params, prices, dates). No marketing fluff.

4. **Insert the entry** at the top of the `news:` list in `data/news.yaml`, using today's date if no publication date is found. Format:

```yaml
  - date: YYYY-MM-DD
    type: <type>
    title:
      en: "<title in English>"
      fr: "<title in French>"
    description:
      en: "<2-3 sentence summary in English with key facts and numbers>"
      fr: "<résumé de 2-3 phrases en français avec chiffres clés>"
    link: <url>
```

5. **Regenerate** `web/index.html`:
```bash
python scripts/generate_home.py
```

6. **Confirm** to the user: title added, date, and type.
