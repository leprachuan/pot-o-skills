#!/usr/bin/env python3
"""
Product Researcher — Canvas Renderer
Accepts a JSON file of product data and renders a rich research canvas.

Usage:
    python3 render_canvas.py --data /tmp/products.json [--session SESSION_ID] [--title "My Research"]

JSON schema (list of product objects):
[
  {
    "name": "Product Name",
    "price": "$99.99",
    "tag": "In Cart | Recommended | Budget Pick | etc.",
    "image_url": "https://...",
    "buy_links": [
      {"store": "Amazon", "url": "https://amazon.com/...", "price": "$99.99"},
      {"store": "Official Site", "url": "https://brand.com/product"}
    ],
    "ratings": {
      "amazon":  {"score": 4.5, "count": "1,234 ratings"},
      "google":  {"score": 4.3, "count": "500+ reviews"},
      "rtings":  {"score": 8.2, "max": 10},
      "pcmag":   {"score": 4.0, "max": 5},
      "reddit":  {"score": 4.2, "label": "Highly recommended"}
    },
    "pros": ["Pro 1", "Pro 2"],
    "cons": ["Con 1", "Con 2"],
    "recommended": false,
    "summary": "Optional one-line expert summary"
  }
]
"""

import sys
import os
import json
import argparse
import subprocess
import urllib.request
import hashlib
import tempfile

_canvas_lib = os.environ.get(
    'CANVAS_LIB_PATH',
    os.path.join(os.path.dirname(__file__), '..', '..', '..', 'live-canvas', 'claude', 'implementation')
)
sys.path.insert(0, os.path.abspath(_canvas_lib))

def download_image(url, dest_dir):
    """Download image to dest_dir, return local filename or None on failure."""
    if not url:
        return None
    ext = url.split('?')[0].split('.')[-1].lower()
    if ext not in ('jpg', 'jpeg', 'png', 'webp', 'gif'):
        ext = 'jpg'
    fname = hashlib.md5(url.encode()).hexdigest()[:12] + '.' + ext
    fpath = os.path.join(dest_dir, fname)
    if os.path.exists(fpath) and os.path.getsize(fpath) > 1000:
        return fpath
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = resp.read()
        if len(data) > 1000:
            with open(fpath, 'wb') as f:
                f.write(data)
            return fpath
    except Exception:
        pass
    return None


def stars_html(score, max_score=5):
    """Render star rating as HTML."""
    pct = (score / max_score) * 5
    full = int(pct)
    half = 1 if (pct - full) >= 0.4 else 0
    empty = 5 - full - half
    s = '★' * full + ('½' if half else '') + '☆' * empty
    return f'<span style="color:#f59e0b;font-size:12px">{s}</span>'


def ratings_html(ratings):
    if not ratings:
        return ''
    parts = []
    for source, info in ratings.items():
        score = info.get('score')
        max_s = info.get('max', 5)
        count = info.get('count', '')
        label = info.get('label', '')
        if score is None:
            continue
        src_label = source.capitalize()
        score_display = f'{score}/{max_s}' if max_s != 5 else f'{score}/5'
        stars = stars_html(score, max_s)
        count_str = f'<span style="color:#64748b;font-size:10px"> ({count or label})</span>' if (count or label) else ''
        parts.append(
            f'<div style="display:flex;align-items:center;gap:4px;margin:2px 0">'
            f'<span style="color:#94a3b8;font-size:10px;width:52px;flex-shrink:0">{src_label}</span>'
            f'{stars}'
            f'<span style="color:#cbd5e1;font-size:11px;margin-left:2px">{score_display}</span>'
            f'{count_str}</div>'
        )
    return '\n'.join(parts)


def buy_links_html(buy_links):
    if not buy_links:
        return ''
    btns = []
    for i, link in enumerate(buy_links[:3]):
        store = link.get('store', 'Buy')
        url = link.get('url', '#')
        price = link.get('price', '')
        color = '#f59e0b' if i == 0 else '#3b82f6'
        label = f'{store}{" — " + price if price else ""}'
        btns.append(
            f'<a href="{url}" style="display:inline-block;background:{color};color:#000 if i==0 else #fff;'
            f'font-size:11px;font-weight:600;padding:5px 12px;border-radius:6px;text-decoration:none;margin-right:6px;margin-bottom:4px;color:{"#000" if i==0 else "#fff"}">'
            f'🛒 {label}</a>'
        )
    return ''.join(btns) + '<div style="font-size:9px;color:#475569;margin-top:2px">Right-click → open in new tab</div>'


def product_card_html(product, img_base_path, session_id):
    name = product.get('name', 'Unknown')
    price = product.get('price', '')
    tag = product.get('tag', '')
    image_url = product.get('image_url', '')
    pros = product.get('pros', [])
    cons = product.get('cons', [])
    ratings = product.get('ratings', {})
    buy_links = product.get('buy_links', [])
    recommended = product.get('recommended', False)
    summary = product.get('summary', '')

    border = '2px solid #f59e0b' if recommended else '1px solid rgba(255,255,255,0.08)'
    rec_badge = ('<span style="background:#f59e0b;color:#000;font-size:10px;font-weight:700;'
                 'padding:2px 8px;border-radius:12px;margin-left:8px">⭐ TOP PICK</span>') if recommended else ''

    tag_html = (f'<span style="background:rgba(255,255,255,0.1);color:#94a3b8;font-size:11px;'
                f'padding:2px 8px;border-radius:10px;margin-left:6px">{tag}</span>') if tag else ''

    # Resolve image
    img_src = ''
    if image_url:
        local = download_image(image_url, img_base_path)
        if local:
            rel = os.path.basename(local)
            img_src = f'/ai-media/{session_id}/pr_imgs/{rel}'
        else:
            img_src = image_url  # fallback to remote URL

    img_html = (f'<img src="{img_src}" style="width:130px;height:130px;object-fit:cover;'
                f'border-radius:8px;background:#1e293b" onerror="this.style.opacity=0.3"/>'
                if img_src else
                f'<div style="width:130px;height:130px;background:#1e293b;border-radius:8px;'
                f'display:flex;align-items:center;justify-content:center;color:#475569;font-size:24px">📦</div>')

    pros_html = ''.join(f'<li style="color:#4ade80;margin:2px 0;font-size:12px">✓ {p}</li>' for p in pros)
    cons_html = ''.join(f'<li style="color:#f87171;margin:2px 0;font-size:12px">✗ {c}</li>' for c in cons)
    summary_html = (f'<div style="font-size:12px;color:#94a3b8;font-style:italic;margin-bottom:8px;'
                    f'border-left:2px solid #334155;padding-left:8px">{summary}</div>') if summary else ''

    return f'''
<div style="background:rgba(255,255,255,0.04);border:{border};border-radius:12px;padding:16px;
     display:flex;gap:16px;margin-bottom:8px">
  <div style="flex-shrink:0">{img_html}</div>
  <div style="flex:1;min-width:0">
    <div style="display:flex;align-items:center;flex-wrap:wrap;gap:4px;margin-bottom:6px">
      <span style="font-size:15px;font-weight:700;color:#f1f5f9">{name}</span>
      {rec_badge}{tag_html}
    </div>
    <div style="font-size:20px;font-weight:800;color:#4ade80;margin-bottom:6px">{price}</div>
    {summary_html}
    <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-bottom:10px">
      <div>
        <div style="font-size:10px;font-weight:600;color:#64748b;margin-bottom:4px;text-transform:uppercase;letter-spacing:0.05em">Ratings</div>
        {ratings_html(ratings)}
      </div>
      <div>
        <div style="font-size:10px;font-weight:600;color:#64748b;margin-bottom:4px;text-transform:uppercase;letter-spacing:0.05em">Pros</div>
        <ul style="list-style:none;padding:0;margin:0">{pros_html}</ul>
      </div>
      <div>
        <div style="font-size:10px;font-weight:600;color:#64748b;margin-bottom:4px;text-transform:uppercase;letter-spacing:0.05em">Cons</div>
        <ul style="list-style:none;padding:0;margin:0">{cons_html}</ul>
      </div>
    </div>
    {buy_links_html(buy_links)}
  </div>
</div>'''


def compute_summary_bar(products):
    """Build a summary highlights row from products."""
    best_value = min(
        (p for p in products if p.get('price') and p['price'].replace('$','').replace(',','').split()[0].replace('.','').isdigit()),
        key=lambda p: float(p['price'].replace('$','').replace(',','').split()[0]),
        default=None
    )
    top_pick = next((p for p in products if p.get('recommended')), None)

    def avg_rating(p):
        r = p.get('ratings', {})
        scores = []
        for v in r.values():
            s = v.get('score')
            m = v.get('max', 5)
            if s:
                scores.append(s / m * 5)
        return sum(scores) / len(scores) if scores else 0

    highest_rated = max(products, key=avg_rating, default=None)

    cards = []
    if best_value:
        cards.append(('💰 Best Value', best_value['name'], best_value.get('price',''), 'rgba(74,222,128,0.1)', 'rgba(74,222,128,0.3)'))
    if top_pick:
        cards.append(('⭐ Top Pick', top_pick['name'], top_pick.get('price',''), 'rgba(245,158,11,0.1)', 'rgba(245,158,11,0.3)'))
    if highest_rated and highest_rated != top_pick:
        cards.append(('📊 Highest Rated', highest_rated['name'], highest_rated.get('price',''), 'rgba(59,130,246,0.1)', 'rgba(59,130,246,0.3)'))

    if not cards:
        return ''

    html = '<div style="display:flex;gap:12px;flex-wrap:wrap;margin-bottom:4px">'
    for (label, name, price, bg, border) in cards:
        html += (f'<div style="background:{bg};border:1px solid {border};border-radius:8px;'
                 f'padding:10px 16px;flex:1;min-width:180px">'
                 f'<div style="font-size:11px;color:#64748b;font-weight:600;text-transform:uppercase;letter-spacing:0.05em">{label}</div>'
                 f'<div style="font-size:13px;color:#f1f5f9;font-weight:700;margin-top:4px">{name}</div>'
                 f'<div style="font-size:12px;color:#94a3b8">{price}</div></div>')
    html += '</div>'
    return html


def main():
    parser = argparse.ArgumentParser(description='Render product research to live canvas')
    parser.add_argument('--data', required=True, help='Path to JSON file with product data')
    parser.add_argument('--session', default=None, help='Canvas session ID (auto-generated if not provided)')
    parser.add_argument('--title', default='🔍 Product Research', help='Canvas title')
    parser.add_argument('--host', default=None, help='Canvas host (default: CANVAS_HOST env or localhost)')
    args = parser.parse_args()

    if args.host:
        os.environ['CANVAS_HOST'] = args.host

    with open(args.data) as f:
        products = json.load(f)

    from canvas import Canvas
    c = Canvas(session_id=args.session)

    session_id = c.session_id
    img_dir = f'/tmp/webui_ai_media/{session_id}/pr_imgs'
    os.makedirs(img_dir, exist_ok=True)

    host = os.environ.get('CANVAS_HOST', 'localhost')
    print(f'Session: {session_id}')
    print(f'URL: http://{host}:18793/?session={session_id}')
    print(f'Rendering {len(products)} products...')

    # Build components
    summary_bar = compute_summary_bar(products)
    components = [
        {'type': 'heading', 'level': 1, 'text': args.title},
        {'type': 'html', 'content': summary_bar} if summary_bar else {'type': 'text', 'text': f'{len(products)} products researched'},
        {'type': 'divider'},
        {'type': 'html', 'content': f'<div style="font-size:11px;color:#475569;margin-bottom:8px">'
                                    f'{len(products)} products &nbsp;|&nbsp; '
                                    f'Ratings sourced from Amazon, Google, and review sites &nbsp;|&nbsp; '
                                    f'Right-click buy links → open in new tab</div>'},
    ]

    for product in products:
        card_html = product_card_html(product, img_dir, session_id)
        components.append({'type': 'html', 'content': card_html})

    c.render(components)
    print('Canvas rendered successfully!')
    return session_id


if __name__ == '__main__':
    main()
