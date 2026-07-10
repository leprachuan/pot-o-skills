---
name: product-researcher
description: >
  Research products and display results on a live canvas with product images, prices,
  star ratings from multiple sources (Amazon, Google, Reddit, review sites like Wirecutter/RTINGS/PCMag),
  pros/cons, and working buy links. Use when the user wants to compare products, research before
  buying, find the best options in a category, look up reviews, or says things like
  "research X", "compare these products", "find the best Y", "show me reviews for",
  "help me pick a backpack/laptop/camera/headphones/etc", or attaches a screenshot of products
  from a shopping site. Renders everything on the live canvas (requires live-canvas skill).
---

# Product Researcher

Researches products and renders a rich comparison canvas with images, multi-source ratings, pros/cons, and buy links.

## Workflow

### 1. Identify Products to Research

From user input, extract:
- Products explicitly named or shown (e.g., from screenshots)
- Product category (e.g., "travel backpack", "noise-cancelling headphones")
- Any specific models already in the user's cart/wishlist

Also add **2–3 top-rated competitors** from your research to give the user comparison context.

### 2. Research Each Product (use WebSearch)

For each product, run these searches and extract the data:

```
"{product name} review pros cons 2025"
"{product name} amazon rating site:amazon.com"
"{product name} reddit review recommended"
"{product name} buy price site:amazon.com OR site:{brand}.com"
"{product name} site:rtings.com OR site:pcmag.com OR site:techradar.com review score"
```

Extract per product:
- **price** — current retail price
- **image_url** — direct CDN/product image URL (from brand site, NOT Amazon thumbnail)
- **buy_links** — up to 3: Amazon, brand official, Best Buy, etc. — must be exact product URLs
- **ratings** — from as many of these sources as you can find:
  - `amazon`: `{"score": 4.5, "count": "1,234 ratings"}`
  - `google`: `{"score": 4.3, "count": "500+ reviews"}`
  - `reddit`: `{"score": 4.0, "label": "Highly recommended"}`
  - `rtings` / `pcmag` / `wirecutter` / `techradar` — use `"max": 10` or `"max": 5` as appropriate
- **pros** — 4–6 concrete bullet points from reviews
- **cons** — 3–5 real weaknesses from reviews
- **summary** — one expert sentence (e.g. "Pack Hacker's top pick for one-bag travel")
- **recommended** — `true` for the single overall best pick
- **tag** — e.g. `"In Your Cart"`, `"Best Value"`, `"Recommended"`, `"Budget Pick"`

**Image URL tips:**
- Fetch the brand's product page to find CDN image URLs (usually `cdn.shopify.com`, `brand.com/cdn/shop/files/...`)
- Avoid Amazon image URLs (often blocked). Use brand site or retailer CDN URLs.
- URL should end in `.jpg`, `.webp`, or `.png` with no login required

**Ratings accuracy:** Only include ratings you actually found via search — never fabricate scores.

### 3. Build the JSON Data File

Write all product data to `/tmp/pr_research.json` as a JSON array:

```json
[
  {
    "name": "Product Name — Variant",
    "price": "$99.99",
    "tag": "In Your Cart",
    "image_url": "https://cdn.example.com/product.jpg",
    "buy_links": [
      {"store": "Amazon", "url": "https://amazon.com/dp/ASIN", "price": "$99.99"},
      {"store": "Official Site", "url": "https://brand.com/product"}
    ],
    "ratings": {
      "amazon": {"score": 4.5, "count": "1,234 ratings"},
      "google": {"score": 4.3, "count": "500+ reviews"},
      "wirecutter": {"score": 4.0, "max": 5, "label": "Top Pick"}
    },
    "pros": ["Pro 1", "Pro 2", "Pro 3"],
    "cons": ["Con 1", "Con 2"],
    "recommended": false,
    "summary": "Optional expert one-liner"
  }
]
```


### 4. Render the Canvas

Find the `render_canvas.py` script inside this skill's `scripts/` directory.

```bash
python3 /path/to/product-researcher/scripts/render_canvas.py \
  --data /tmp/pr_research.json \
  --title "🔍 [Category] Research"
```

Override the canvas host if needed (e.g. for Tailscale/remote access):
```bash
python3 render_canvas.py --data /tmp/pr_research.json --host YOUR_HOST_IP --title "🔍 ..."
```

Or set it via environment variable:
```bash
CANVAS_HOST=YOUR_HOST_IP python3 render_canvas.py --data /tmp/pr_research.json --title "🔍 ..."
```

The script auto-downloads images, builds a summary highlights bar (Best Value / Top Pick / Highest Rated), and renders all product cards with ratings, pros/cons, and buy links.

To update an existing canvas session instead of opening a new tab:
```bash
... --session SESSION_ID
```

The canvas lib path defaults to `../../live-canvas/claude/implementation` relative to the script.
Override with `CANVAS_LIB_PATH` env var if your live-canvas skill is installed elsewhere.

### 5. Report to User

- Share the canvas URL: `http://CANVAS_HOST:18793/?session=SESSION_ID`
- Summarize top picks in chat: best value, overall winner, best for their specific use case
- Note that buy links require right-click → open in new tab

## Tips

- **Buy link validity**: Verify the ASIN or URL slug points to the exact product — not a search page
- **Image fallback**: If image fails to download, the script shows a 📦 placeholder automatically
- **Parallel searching**: Run multiple WebSearch calls in parallel to speed up research on large product lists
- **Session reuse**: Use `--session` to push updates to the same canvas tab without opening a new one
