#!/usr/bin/env python3
"""Build the whole CX-5 buyer's-report site from data/board.json.

    python3 tools/build_site.py            # index.html, status.html, map.html, trims.html, ask.html + PDF, XLSX, DOCX
    python3 tools/build_site.py --no-pdf   # skip the Chromium print step

Every number, table row, chart marker and download derives from data/board.json
(plus data/inbox.json for the Ask page). Never hand-edit the generated files; edit the data and re-run.
"""
import json, math, html, re, os, sys, subprocess, datetime, urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, 'tools')
ASSETS = os.path.join(TOOLS, 'assets')
B = json.load(open(os.path.join(ROOT, 'data', 'board.json'), encoding='utf-8'))
META = B['meta']
_INBOX_PATH = os.path.join(ROOT, 'data', 'inbox.json')
INBOX = json.load(open(_INBOX_PATH, encoding='utf-8')) if os.path.exists(_INBOX_PATH) else {'config': {}, 'items': []}

# ----------------------------------------------------------------------------- helpers
def esc(s):
    return html.escape(str('' if s is None else s), quote=True)

def money(n, cents=False):
    if n is None: return '—'
    if cents and abs(n - round(n)) > 0.004:
        return ('−$' if n < 0 else '$') + '{:,.2f}'.format(abs(n))
    return ('−$' if n < 0 else '$') + '{:,.0f}'.format(abs(round(n)))

def signed(n):
    return ('+' if n > 0 else '−' if n < 0 else '') + '$' + '{:,.0f}'.format(abs(round(n)))

def num(n): return '{:,.0f}'.format(round(n))
def f1(v): return '{:.1f}'.format(v)

def d_iso(s): return datetime.date.fromisoformat(s)
def d_short(s):  # 'Aug 12'
    d = d_iso(s); return d.strftime('%b ') + str(d.day)
def d_long(s):   # 'Aug 12, 2026'
    d = d_iso(s); return d.strftime('%b ') + f'{d.day}, {d.year}'
def d_dow(s):    # 'Wed Aug 12, 2026'
    d = d_iso(s); return d.strftime('%a %b ') + f'{d.day}, {d.year}'

REF = META['refreshed']; PUB = META['published']
CTX = {'refreshed': d_short(REF), 'published': d_short(PUB)}

def tpl(s, car=None):
    """Prose fields may reference {days} (car's days listed) and {refreshed}/{published}."""
    if s is None: return ''
    ctx = dict(CTX)
    if car is not None:
        ctx['days'] = car.get('daysListed') if car.get('daysListed') is not None else '?'
        ctx['rank'] = car['rank']
    return re.sub(r'\{(\w+)\}', lambda m: str(ctx.get(m.group(1), m.group(0))), s)

def ascii_safe(doc):
    """Escape non-ASCII per context so the file survives any charset guess."""
    def rep(m):
        script, style = m.group(1), m.group(2)
        if script: return re.sub(r'[^\x00-\x7F]', lambda c: '\\u%04x' % ord(c.group(0)), script)
        if style: return re.sub(r'[^\x00-\x7F]', lambda c: '\\%x ' % ord(c.group(0)), style)
        return re.sub(r'[^\x00-\x7F]', lambda c: '&#%d;' % ord(c.group(0)), m.group(0))
    return re.sub(r'(<script>[\s\S]*?</script>)|(<style>[\s\S]*?</style>)|([^<]+|<)', rep, doc)

def haversine_mi(a, b):
    R = 3958.7613
    lat1, lon1, lat2, lon2 = map(math.radians, [a[0], a[1], b[0], b[1]])
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))

def src_class(s): return 'src-' + re.sub(r'[^a-z0-9]+', '', str(s).lower())
def badge(text, cls): return f'<span class="badge {cls}">{esc(text)}</span>'
def src_badge(s): return badge(s, 'src ' + src_class(s))
def ext(url, text, cls=None, label=None):
    a = f' class="{cls}"' if cls else ''
    l = f' aria-label="{esc(label)}"' if label else ''
    return f'<a{a} href="{esc(url)}" target="_blank" rel="noopener"{l}>{text}</a>'

FAVICON = '<link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>🚗</text></svg>">'

# ----------------------------------------------------------------------------- model
DEALERS = B['dealers']
CARS = sorted(B['cars'], key=lambda c: c['rank'])
BY_RANK = {c['rank']: c for c in CARS}
for c in CARS:
    c['dealer'] = DEALERS[c['dealerKey']]
LIVE = [c for c in CARS if c['status'] == 'live']
BENCH = [c for c in CARS if c['status'] == 'benchmark']
IN_PLAY = [c for c in CARS if c['status'] in ('live', 'benchmark')]
SOLD = [c for c in CARS if c['status'] == 'sold']
QUOTED = [c for c in IN_PLAY if c.get('quote')]
QUOTED_NUM = [c for c in QUOTED if c['quote'].get('otd')]

# Sweeps: entries without a "scope" re-check the numbered board (newest first; BOARD_SWEEPS[0] drives the TL;DR);
# scoped entries (e.g. scope "2024 watch") are side sweeps that only feed the watchlist and the method lists.
BOARD_SWEEPS = [s for s in B['sweeps'] if not s.get('scope')]
SIDE_SWEEPS = [s for s in B['sweeps'] if s.get('scope')]
SWEEP_DATES = sorted({s['date'] for s in BOARD_SWEEPS})

# Watchlist: flat items, optionally tagged with "group"; untagged items fall in the first (default) group.
WATCH_GROUPS = B.get('watchlistGroups') or [{'key': 'parked', 'title': 'Screened and parked', 'intro': ''}]
def watch_items(key):
    default = WATCH_GROUPS[0]['key']
    return [w for w in B['watchlist'] if (w.get('group') or default) == key]

APR, N = META['apr'], META['termMonths']
def pmt(P, apr=APR, n=N):
    r = apr / 100 / 12
    return P / n if r == 0 else P * (r * (1 + r) ** n) / ((1 + r) ** n - 1)
PER1K = pmt(1000)

def doc_fee(c):
    p = c['price']
    return p['docFee'] if p.get('docFee') is not None else (c['dealer'].get('docFee') or META['docFeeWA'])

def tax_rate(c):
    return c['dealer'].get('taxRate') or META['defaultTaxRate']

def est_otd(price, rate, doc, lic=None):
    lic = META['licenseEst'] if lic is None else lic
    return price * (1 + rate / 100) + doc + lic

def cost_row(c):
    rate, doc = tax_rate(c), doc_fee(c)
    adv = c['price']['advertised']
    est = est_otd(adv, rate, doc)
    q = c.get('quote') or {}
    row = {'car': c, 'rate': rate, 'doc': doc, 'advertised': adv, 'est': est, 'struck': None}
    if q.get('otd'):
        # site rule: public pages carry a written-quote chip only, never the dealer's figures
        row.update(basis='quoted', otd=est, price=adv, date=q.get('date'))
    else:
        row.update(basis='est', otd=est, price=adv, date=c['price'].get('asOf'))
    row['m0'] = pmt(row['otd']); row['m5'] = pmt(max(0, row['otd'] - 5000)); row['interest'] = row['m0'] * N - row['otd']
    return row

COST = {c['rank']: cost_row(c) for c in IN_PLAY}
COST_SORTED = sorted(COST.values(), key=lambda r: r['otd'])

def clean_history(c):
    return c['history'].get('accidents') == 0

def solid(c):
    h = c['history']
    return (c['status'] == 'live' and clean_history(c) and (h.get('owners') == 1 or h.get('cpo'))
            and (c['dealer']['type'] == 'franchise' or h.get('cpo')))

SOLID_RULE = 'lowest estimated out-the-door figure among live cars with a verified 1-owner / 0-accident history (or Mazda CPO) at a franchise dealer'
STRETCH_RULE = 'best-value live 2023 in the Turbo / Premium tiers, ranked by list price against KBB Seattle fair purchase price'
solid_cands = [c for c in LIVE if solid(c)]
CHEAPEST = min(solid_cands, key=lambda c: COST[c['rank']]['otd']) if solid_cands else None
def value_score(c):
    d = c['deal']
    if d.get('kbbFpp'): return d['kbbFpp'] - c['price']['advertised']
    return d.get('belowMarket') or 0
stretch_cands = [c for c in LIVE if c['year'] == 2023 and (c.get('turbo') or c['trimKey'] in ('2.5 S Premium', '2.5 S Premium Plus', '2.5 Turbo')) and clean_history(c)]
STRETCH = max(stretch_cands, key=value_score) if stretch_cands else None
if STRETCH is CHEAPEST and len(stretch_cands) > 1:
    STRETCH = sorted(stretch_cands, key=value_score)[-2]

PICKS = sorted([c for c in IN_PLAY if c.get('topPick')], key=lambda c: c['topPick'])
if len(PICKS) < 3:  # promote by value among live WA cars if a pick went away
    pool = sorted([c for c in LIVE if c not in PICKS and c['dealer']['state'] == 'WA' and clean_history(c)],
                  key=lambda c: -(value_score(c)))
    for c in pool[:3 - len(PICKS)]:
        c['pickTag'] = c.get('pickTag') or 'By value'; PICKS.append(c)

HOME = tuple(META['home'])
def dist_mi(c):
    d = c['dealer']
    return haversine_mi(HOME, (d['lat'], d['lon'])) if d.get('lat') else None

# --- market cloud + trim table recompute
CLOUD = B['market']['cloud']
def trim_low(year, key):
    cands = []
    for p in CLOUD:
        if p.get('board'): continue
        if p['y'] == year and p.get('tk') == key and p.get('seenLatest'):
            cands.append({'price': p['p'], 'src': p['s'], 'label': p['s'], 'rank': None})
    for c in IN_PLAY:
        if c['year'] == year and c['trimKey'] == key and clean_history(c):
            cands.append({'price': c['price']['listed'], 'src': c['links']['primarySource'], 'label': f"#{c['rank']}", 'rank': c['rank']})
    if not cands: return None, 0
    return min(cands, key=lambda x: x['price']), len(cands)

TRIMS = []
for t in B['trims']:
    low, n = trim_low(t['year'], t['trim'])
    row = dict(t, low=low['price'] if low else None, lowSrc=(low['label'] if low else None), lowRank=(low['rank'] if low else None), n=n)
    ref = t['kbbSeattle'] if t['kbbSeattle'] else t['kbbNational']
    row['vsNat'] = not t['kbbSeattle']
    row['delta'] = (row['low'] - ref) if (row['low'] is not None and ref) else None
    row['hl'] = bool(low and low['rank'])
    TRIMS.append(row)
BAR_ROWS = [t for t in TRIMS if t['kbbSeattle'] and t['low'] is not None]

# --- scatter points: cloud (minus board duplicates) then board cars (sold hollow, live labelled; #1 drawn last)
POINTS = [{'y': p['y'], 'm': p['m'], 'p': p['p'], 'r': None, 't': p['t'], 'd': p['d'], 'c': p['c'], 's': p['s'], 'gone': False} for p in CLOUD if not p.get('board')]
for c in sorted(CARS, key=lambda c: (c['status'] != 'sold', -c['rank'])):
    if not (c.get('miles') and c['price'].get('listed')): continue
    POINTS.append({'y': c['year'], 'm': c['miles'], 'p': c['price']['listed'], 'r': c['rank'], 't': c['trimFull'] + (' (sold %s)' % d_short(c['soldInfo']['date']) if c['status'] == 'sold' else ''),
                   'd': c['dealer']['name'], 'c': c['dealer']['city'], 's': c['links']['primarySource'], 'gone': c['status'] == 'sold'})
N_CLOUD = sum(1 for p in CLOUD)
N_SEEN = sum(1 for p in CLOUD if p.get('seenLatest'))

# ----------------------------------------------------------------------------- SVG charts (ported 1:1 from the Aug 7 generator; sold picks hollow + unlabelled)
SCATTER = {
    'd': dict(id='scatter', cls='d', W=900, H=470, m=dict(l=66, r=26, t=22, b=56), xLabelStep=5000, xMinorStep=0, cloudK=1, slK=1.75, cw=7.6, lh=14, mr=9, yTitle='rotated'),
    'm': dict(id='scatter-m', cls='m', W=360, H=410, m=dict(l=44, r=14, t=30, b=50), xLabelStep=10000, xMinorStep=5000, cloudK=0.9, slK=1.5, cw=8.6, lh=16, mr=8, yTitle='top'),
}
def scatter_svg(prof):
    W, H, m = prof['W'], prof['H'], prof['m']
    pw, ph = W - m['l'] - m['r'], H - m['t'] - m['b']
    x0, x1, y0, y1 = 14000, 50000, 22500, 29500
    sx = lambda v: m['l'] + (v - x0) / (x1 - x0) * pw
    sy = lambda v: m['t'] + (y1 - v) / (y1 - y0) * ph
    g = ''
    for y in range(23000, 29001, 1000):
        g += f'<line class="grid" x1="{m["l"]}" x2="{W - m["r"]}" y1="{f1(sy(y))}" y2="{f1(sy(y))}"/>'
        g += f'<text class="tick" x="{m["l"] - (6 if prof["cls"] == "m" else 10)}" y="{f1(sy(y) + 4.5)}" text-anchor="end">${y // 1000}k</text>'
    if prof['xMinorStep']:
        for x in range(15000, 50000, prof['xMinorStep']):
            if (x - 10000) % prof['xLabelStep'] == 0: continue
            g += f'<line class="grid-minor" x1="{f1(sx(x))}" x2="{f1(sx(x))}" y1="{m["t"]}" y2="{H - m["b"]}"/>'
    for x in range(15000 if prof['xLabelStep'] == 5000 else 20000, 50001, prof['xLabelStep']):
        g += f'<line class="grid grid-v" x1="{f1(sx(x))}" x2="{f1(sx(x))}" y1="{m["t"]}" y2="{H - m["b"]}"/>'
        g += f'<text class="tick" x="{f1(sx(x))}" y="{H - m["b"] + 18}" text-anchor="middle">{x // 1000}k</text>'
    g += f'<line class="axis" x1="{m["l"]}" x2="{W - m["r"]}" y1="{H - m["b"]}" y2="{H - m["b"]}"/>'
    g += f'<text class="axis-title" x="{f1(m["l"] + pw / 2)}" y="{H - (8 if prof["cls"] == "m" else 10)}" text-anchor="middle">Odometer (miles)</text>'
    if prof['yTitle'] == 'rotated':
        yc = m['t'] + ph / 2
        g += f'<text class="axis-title" x="16" y="{yc:g}" text-anchor="middle" transform="rotate(-90 16 {yc:g})">List price</text>'
    else:
        g += f'<text class="axis-title" x="{m["l"] - 38}" y="16" text-anchor="start">List price</text>'

    def shape(p, cx, cy, k):
        if p['y'] == 2021: return f'<circle cx="{f1(cx)}" cy="{f1(cy)}" r="{f1(3.7 * k)}"/>'
        if p['y'] == 2022:
            s = 4.7 * k; return f'<path d="M{f1(cx)},{f1(cy - s)}l{f1(s)},{f1(s)}l{f1(-s)},{f1(s)}l{f1(-s)},{f1(-s)}z"/>'
        s = 4.9 * k
        return f'<path d="M{f1(cx)},{f1(cy - s)}L{f1(cx + s * 0.95)},{f1(cy + s * 0.7)}L{f1(cx - s * 0.95)},{f1(cy + s * 0.7)}z"/>'

    pts, labels, placed = '', '', []
    o = prof['mr']
    marker_boxes = [dict(x=sx(p['m']) - o, y=sy(p['p']) - o, w=2 * o, h=2 * o) for p in POINTS if p['r']]
    overlaps = lambda a, b: a['x'] < b['x'] + b['w'] and a['x'] + a['w'] > b['x'] and a['y'] < b['y'] + b['h'] and a['y'] + a['h'] > b['y']
    for i, p in enumerate(POINTS):
        cx, cy = sx(p['m']), sy(min(max(p['p'], y0), y1))
        k = prof['slK'] if p['r'] else prof['cloudK']
        cls = f'pt y{p["y"]}' + (' sl' if p['r'] else '') + (' gone' if p['gone'] else '')
        pts += f'<g class="{cls}" data-i="{i}" data-x="{f1(cx)}" data-y="{f1(cy)}">{shape(p, cx, cy, k)}</g>'
        if p['r'] and not p['gone']:
            text = f'#{p["r"]}'
            w, h = len(text) * prof['cw'] + 4, prof['lh']
            cands = [dict(x=cx + o, y=cy - o - h), dict(x=cx - o - w, y=cy - o - h), dict(x=cx + o, y=cy + o - 1), dict(x=cx - o - w, y=cy + o - 1),
                     dict(x=cx + o + 2, y=cy - h / 2), dict(x=cx - w / 2, y=cy - o - 3 - h), dict(x=cx - o - 2 - w, y=cy - h / 2)]
            def ok(cd):
                bx = dict(x=cd['x'], y=cd['y'], w=w, h=h)
                if bx['x'] < m['l'] or bx['x'] + w > W - m['r'] or bx['y'] < m['t'] or bx['y'] + h > H - m['b']: return False
                if any(overlaps(bx, q) for q in placed): return False
                if any(overlaps(bx, q) and not (abs(q['x'] + o - cx) < .5 and abs(q['y'] + o - cy) < .5) for q in marker_boxes): return False
                return True
            box = next((cd for cd in cands if ok(cd)), cands[0])
            placed.append(dict(x=box['x'], y=box['y'], w=w, h=h))
            labels += f'<text class="pt-label" x="{f1(box["x"] + 2)}" y="{f1(box["y"] + h - 3)}">{text}</text>'
    n_live = sum(1 for p in POINTS if p['r'] and not p['gone'])
    return (f'<svg class="chart scatter {prof["cls"]}" id="{prof["id"]}" viewBox="0 0 {W} {H}" role="img" aria-label="Scatter plot of {N_CLOUD} passing listings: odometer miles on the x axis, list price on the y axis. The {n_live} live board cars are numbered.">\n'
            f'  <rect class="plot-bg" x="{m["l"]}" y="{m["t"]}" width="{pw}" height="{ph}"/>\n  {g}\n  <g class="pts">{pts}</g>\n  <g class="labels">{labels}</g>\n</svg>')

def bar_tip(r):
    return esc(f'{r["year"]} {r["trim"]}: lowest clean listing {money(r["low"])} ({r["lowSrc"]}) vs KBB Seattle FPP {money(r["kbbSeattle"])} → {signed(r["delta"])}')
def tick_label(v): return '$0' if v == 0 else signed(v).replace(',000', 'k')

def bars_desktop():
    rows = BAR_ROWS; rowH, W = 30, 900; m = dict(l=200, r=34, t=40, b=40)
    H = m['t'] + len(rows) * rowH + m['b']; pw = W - m['l'] - m['r']; d0, d1 = -3500, 2000
    sx = lambda v: m['l'] + (v - d0) / (d1 - d0) * pw
    g = ''
    for v in range(-3000, 1001, 1000):
        g += f'<line class="grid grid-v" x1="{f1(sx(v))}" x2="{f1(sx(v))}" y1="{m["t"] - 6}" y2="{H - m["b"]}"/>'
        g += f'<text class="tick" x="{f1(sx(v))}" y="{H - m["b"] + 18}" text-anchor="middle">{tick_label(v)}</text>'
    g += f'<text class="axis-note" x="{sx(0) - 8}" y="{m["t"] - 16}" text-anchor="end">← listed under KBB Seattle fair price</text>'
    g += f'<text class="axis-note" x="{sx(0) + 8}" y="{m["t"] - 16}" text-anchor="start">over →</text>'
    bars, prev = '', None
    for i, r in enumerate(rows):
        yc = m['t'] + i * rowH + rowH / 2
        if prev is not None and prev != r['year']: g += f'<line class="grid" x1="10" x2="{W - m["r"]}" y1="{f1(yc - rowH / 2)}" y2="{f1(yc - rowH / 2)}"/>'
        prev = r['year']
        xz, xv = sx(0), sx(max(d0, min(d1, r['delta'])))
        x, w = min(xz, xv), max(1.5, abs(xv - xz)); cls = 'bar-good' if r['delta'] < 0 else 'bar-bad'
        lx = xv - 6 if r['delta'] < 0 else xv + 6
        bars += (f'<g class="bar-row" data-tip="{bar_tip(r)}"><rect class="row-hit" x="0" y="{f1(yc - rowH / 2)}" width="{W}" height="{rowH}"/>'
                 f'<text class="row-label" x="{m["l"] - 12}" y="{f1(yc + 4)}" text-anchor="end"><tspan class="row-year">{r["year"]}</tspan> {esc(r["trim"])}</text>'
                 f'<rect class="{cls}" x="{f1(x)}" y="{f1(yc - 7)}" width="{f1(w)}" height="14" rx="2"/>'
                 f'<text class="bar-val" x="{f1(lx)}" y="{f1(yc + 4)}" text-anchor="{"end" if r["delta"] < 0 else "start"}">{signed(r["delta"])}</text></g>')
    g += f'<line class="axis" x1="{f1(sx(0))}" x2="{f1(sx(0))}" y1="{m["t"] - 6}" y2="{H - m["b"]}"/>'
    return f'<svg class="chart bars d" id="bars" viewBox="0 0 {W} {H}" role="img" aria-label="Horizontal bar chart: lowest clean listing minus KBB Seattle fair purchase price, by year and trim. Negative bars mean the trim is listed under book value.">\n  {g}\n  {bars}\n</svg>'

def bars_mobile():
    rows = BAR_ROWS; rowH, W = 46, 360; m = dict(l=8, r=8, t=42, b=36)
    H = m['t'] + len(rows) * rowH + m['b']; pw = W - m['l'] - m['r']; d0, d1 = -3500, 2000
    sx = lambda v: m['l'] + (v - d0) / (d1 - d0) * pw
    g = ''
    for v in range(-3000, 1001, 1000):
        g += f'<line class="grid grid-v" x1="{f1(sx(v))}" x2="{f1(sx(v))}" y1="{m["t"] - 4}" y2="{H - m["b"]}"/>'
        g += f'<text class="tick" x="{f1(sx(v))}" y="{H - m["b"] + 19}" text-anchor="middle">{tick_label(v)}</text>'
    g += f'<text class="axis-note" x="{m["l"]}" y="18" text-anchor="start">← listed under KBB Seattle fair price</text>'
    g += f'<text class="axis-note" x="{W - m["r"]}" y="18" text-anchor="end">over →</text>'
    bars, prev = '', None
    for i, r in enumerate(rows):
        yTop = m['t'] + i * rowH
        if prev is not None and prev != r['year']: g += f'<line class="grid" x1="0" x2="{W}" y1="{f1(yTop)}" y2="{f1(yTop)}"/>'
        prev = r['year']
        xz, xv = sx(0), sx(max(d0, min(d1, r['delta'])))
        x, w = min(xz, xv), max(1.5, abs(xv - xz)); cls = 'bar-good' if r['delta'] < 0 else 'bar-bad'
        bars += (f'<g class="bar-row" data-tip="{bar_tip(r)}"><rect class="row-hit" x="0" y="{f1(yTop)}" width="{W}" height="{rowH}"/>'
                 f'<text class="row-label" x="{m["l"]}" y="{f1(yTop + 17)}" text-anchor="start"><tspan class="row-year">{r["year"]}</tspan> {esc(r["trim"])}</text>'
                 f'<text class="bar-val {"neg" if r["delta"] < 0 else "pos"}" x="{W - m["r"]}" y="{f1(yTop + 17)}" text-anchor="end">{signed(r["delta"])}</text>'
                 f'<rect class="{cls}" x="{f1(x)}" y="{f1(yTop + 24)}" width="{f1(w)}" height="13" rx="2"/></g>')
    g += f'<line class="axis" x1="{f1(sx(0))}" x2="{f1(sx(0))}" y1="{m["t"] - 4}" y2="{H - m["b"]}"/>'
    return f'<svg class="chart bars m" id="bars-m" viewBox="0 0 {W} {H}" role="img" aria-label="Horizontal bar chart: lowest clean listing minus KBB Seattle fair purchase price, by year and trim. Negative bars mean the trim is listed under book value.">\n  {g}\n  {bars}\n</svg>'

def legend_glyph(y):
    if y == 2021: return '<svg class="lg y2021" viewBox="0 0 14 14" aria-hidden="true"><circle cx="7" cy="7" r="4.2"/></svg>'
    if y == 2022: return '<svg class="lg y2022" viewBox="0 0 14 14" aria-hidden="true"><path d="M7,1.8l5.2,5.2l-5.2,5.2l-5.2,-5.2z"/></svg>'
    return '<svg class="lg y2023" viewBox="0 0 14 14" aria-hidden="true"><path d="M7,1.6L12.4,10.8L1.6,10.8z"/></svg>'

# ----------------------------------------------------------------------------- shared car presenters
def hist_short(c):
    h = c['history']; own = f'{h["owners"]}-own' if h.get('owners') else '?-own'
    return f'{own} / {h.get("accidents") if h.get("accidents") is not None else "?"}' + (' · CPO' if h.get('cpo') else '')

def hist_words(c):
    h = c['history']; parts = []
    if h.get('owners'): parts.append(f'{h["owners"]} owner' + ('s' if h['owners'] != 1 else ''))
    if h.get('accidents') is not None: parts.append(f'{h["accidents"]} accident' + ('s' if h['accidents'] != 1 else ''))
    return ' · '.join(parts) or 'history unverified'

def deal_cls(c):
    r = (c['deal'].get('rating') or '').lower()
    return {'great': 'great', 'good': 'good', 'fair': 'fair', 'no-haggle': 'nohaggle'}.get(r, 'plain')
def deal_sort(c): return {'great': 3, 'good': 2, 'fair': 1}.get((c['deal'].get('rating') or '').lower(), 0)

def price_listed_display(c):
    p = c['price']
    return p.get('listedDisplay') or money(p['listed'])

def quoted_selling(c):
    # site rule: dealer-quoted figures never render on the public pages
    return None

def latest_html(c, short=False):
    t = c['latest'].get('short') if short else c['latest']['text']
    return f'<strong>Latest:</strong> {esc(tpl(t, c))}'

def car_title(c): return f'{c["year"]} {c["trim"]}'
def dealer_city(c): return c['dealer']['city']

# ----------------------------------------------------------------------------- index.html sections
NAV = [('#tldr', 'TL;DR'), ('ask.html', 'Ask'), ('#top3', 'Top 3'), ('#shortlist', 'Shortlist'), ('#watchlist', 'Watchlist'), ('#chart', 'Price vs. miles'), ('#trims', 'Trims'), ('status.html', 'Status'), ('map.html', 'Dealership map'),
       ('trims.html', 'Trim guide'), ('#cost', 'Monthly cost'), ('#nohaggle', 'No-haggle'), ('#email', 'Email'), ('#sources', 'Sources')]
# page-level nav shared by status.html / ask.html (trims.html carries the same links in its template; map.html has its own header)
PAGES = [('index.html', 'Report'), ('ask.html', 'Ask'), ('status.html', 'Status'), ('map.html', 'Map'), ('trims.html', 'Trim guide')]
def pages_nav(current):
    return ''.join(f'<a href="{h}"{" aria-current=" + chr(34) + "page" + chr(34) if h == current else ""}>{esc(l)}</a>' for h, l in PAGES)

def car_ref(c, with_price=True):
    s = f'#{c["rank"]} {c["year"]} {c["trim"]} at {c["dealer"]["short"]}'
    return s + (f' ({money(c["price"]["listed"])})' if with_price else '')

def tldr():
    sw = BOARD_SWEEPS[0]
    side_today = [s for s in SIDE_SWEEPS if s['date'] == REF]
    sold_recent = [c for c in SOLD]
    sold_txt = ', '.join(f'#{c["rank"]} ({c["soldInfo"].get("short") or c["dealer"]["short"]})' for c in sold_recent)
    quotes_txt = '; '.join(
        f'{c["dealer"]["short"]} (#{c["rank"]}' + (', accident on the Carfax' if not clean_history(c) else '') + ')'
        for c in QUOTED)
    bench = BENCH[0] if BENCH else None
    new_today = [c for c in IN_PLAY if c.get('foundDate') == REF]
    b1 = (f'<strong>Update {d_short(REF)}:</strong> fresh {esc(sw["kind"])}. ' +
          (f'{len(sold_recent)} tracked cars have sold and are removed from the tables below: {esc(sold_txt)}. ' if sold_recent else '') +
          f'Every other numbered car re-verified with no listed-price change' + (f' except {", ".join("#%d" % r for r in sw.get("unverifiable", []))} (not reachable from the sweep environment)' if sw.get('unverifiable') else '') + '. ' +
          (f'Written quotes are in hand from {quotes_txt}; the figures stay off this public page. ' if QUOTED else '') +
          (f'No-haggle anchor: {bench["year"]} {bench["trim"].split(" ·")[0]} at {esc(bench["dealer"]["name"])}, {money(bench["price"]["listed"])}, no transfer fee. ' if bench else '') +
          (f'{len(new_today)} new WA listing{"s" if len(new_today) != 1 else ""} passed today\'s screen ({", ".join("#%d" % c["rank"] for c in new_today)}). ' if new_today else '') +
          ''.join(f'{esc(s["scope"].split(" ")[0])}s checked {d_short(s["date"])} in a separate sweep: <a href="#watchlist">watchlist only</a> ({len(s.get("watchlistVins") or [])} cars), none joins the numbered board. ' for s in side_today) +
          'Live availability on the <a href="status.html">status board</a>.')
    b2 = esc(tpl(B['prose']['bestRemaining']))
    cs, st = COST[CHEAPEST['rank']], COST[STRETCH['rank']]
    dy = STRETCH['year'] - CHEAPEST['year']; dm = (STRETCH['miles'] - CHEAPEST['miles']) / 1000
    buys = []
    if dy > 0: buys.append(f'{dy} model year' + ('s' if dy > 1 else ''))
    if STRETCH.get('turbo') and not CHEAPEST.get('turbo'): buys.append('the turbo')
    if dm < -1: buys.append(f'{abs(dm):.0f}k fewer miles')
    b3 = (f'Cheapest solid vs. stretch: #{CHEAPEST["rank"]} {CHEAPEST["year"]} {CHEAPEST["trim"]} at {money(cs["otd"])} out-the-door ({cs["basis"]}, {money(cs["m0"])}/mo) vs. #{STRETCH["rank"]} {STRETCH["year"]} {STRETCH["trim"]} at {money(st["otd"])} ({st["basis"]}, {money(st["m0"])}/mo): '
          f'{signed(st["otd"] - cs["otd"])} and {signed(st["m0"] - cs["m0"])}/mo buys {", ".join(buys) if buys else "the newer car"}.')
    def fpp_phrase(c):
        d = c['deal']
        if d.get('kbbFpp') and d.get('kbbFppDelta') is not None:
            gap = d['kbbFppDelta']
            return f'#{c["rank"]} {c["year"]} {c["trim"]} sits {money(abs(gap))} {"under" if gap > 0 else "over"} KBB Seattle fair purchase price ({money(d["kbbFpp"] - gap)} vs. {money(d["kbbFpp"])})'
        return f'#{c["rank"]} has no KBB figure'
    sig = [c for c in IN_PLAY if c['trimKey'] == 'Signature (turbo)']
    sig_txt = ''
    if sig:
        s = min(sig, key=lambda c: c['price']['advertised'])
        if s['deal'].get('kbbFpp') and s['deal'].get('kbbFppDelta') is not None:
            g = -s['deal']['kbbFppDelta']
            sig_txt = f' The 2021 Signature generally trades over book (#{s["rank"]} is {money(abs(g))} {"over" if g > 0 else "under"} its KBB figure' + (f' but {money(bench["price"]["listed"] - s["price"]["advertised"])} under the CarMax benchmark' if bench and bench['price']['listed'] > s['price']['advertised'] else '') + ').'
    gone_match = [c for c in SOLD if c['trimKey'] == 'GT Reserve (turbo)']
    b4 = 'Trim value: ' + fpp_phrase(STRETCH) + ' and ' + fpp_phrase(CHEAPEST) + '.' + (f' The {money(gone_match[0]["price"]["listed"])} GT Reserve that matched them sold {d_short(gone_match[0]["soldInfo"]["date"])}.' if gone_match else '') + sig_txt
    b5 = f'Financing math: every $1,000 financed ≈ ${PER1K:.2f}/mo at {APR:.2f}% APR over {N} months. No Mazda CPO promo rate applies to the CX-5 right now (3.9% is CX-90/CX-70 only).'
    return ''.join(f'<li>{b}</li>' for b in [b1, b2, esc(b3), esc(b4), esc(b5)])

def changes():
    items = ''
    for ch in B['changelog']:
        items += f'<li><span class="when">{esc(d_long(ch["date"]))}:</span> ' + ' '.join(esc(b) for b in ch['bullets']) + '</li>'
    return items

def pick_card(c):
    cr = COST[c['rank']]; d = c['dealer']; dm = dist_mi(c)
    price = money(c['price']['listed'])
    if c['price'].get('aug7') and c['price']['aug7'] != c['price']['listed']:
        price += f' <span class="muted small">was {money(c["price"]["aug7"])} {d_short(PUB)}</span>'
    qs = quoted_selling(c)
    if qs: price += f' <span class="muted small">{money(qs)} quoted</span>'
    away = f'{dm:.0f} mi away' if dm is not None and dm < 60 else (f'{dm:.0f} mi' if dm else '')
    meta = f'{num(c["miles"])} mi · {esc(d["short"])} · {esc(d["city"])} <span class="muted">({away}{" · " if away else ""}{c["daysListed"]} days listed as of {d_short(REF)})</span>'
    dl = c['deal']; dtxt = (dl.get('rating') or '—') + (f' · {dl["display"].replace("<", "under").replace("FPP", "FPP")}' if dl.get('display') else '')
    badges = badge(dtxt, 'deal ' + deal_cls(c)) + badge(hist_words(c), 'plain') + (badge('CPO', 'cpo') if c['history'].get('cpo') else '')
    basis = f'est. OTD {money(cr["otd"])}' + (' · written quote in hand' if cr['basis'] == 'quoted' else '')
    return f'''    <article class="pick">
      <div class="pick-head"><span class="rank">#{c["rank"]}</span><span class="pick-tag">{esc(c.get("pickTag") or "")}</span>{src_badge(c["links"]["primarySource"])}</div>
      <h3>{esc(car_title(c))}</h3>
      <div class="price">{price}</div>
      <div class="pick-meta">{meta}</div>
      <div class="pick-badges">{badges}</div>
      <div class="monthly"><strong>{money(cr["m0"])}/mo</strong> <span class="muted">at $0 down on the {basis} · {APR:.2f}% · {N} mo</span></div>
      <p class="why">{esc(tpl(c.get("pickWhy") or "", c))}</p>
      {ext(c["links"]["primary"], "View listing", "btn")}
    </article>'''

def top3():
    gone_picks = [c for c in SOLD if c['rank'] in (1, 3, 7)]  # picks at publication were #3, #1, #7
    note = (f'Picks are drawn from live cars only, as of the {d_short(REF)} refresh; ranks refer to the full board (#1–#{max(c["rank"] for c in CARS)}), so gaps are expected. '
            + (' '.join(f'#{c["rank"]}, a pick at publication, sold {d_short(c["soldInfo"]["date"])} ({esc(c["soldInfo"]["how"])}).' for c in gone_picks) + ' ' if gone_picks else '')
            + 'Monthly figures use the dealer-city estimate for every car; a “quoted” chip marks cars whose written sheet is in hand, with the figures kept off this page. See the <a href="status.html">status board</a> for what remains.')
    return f'''  <div class="sec-head"><h2>Top 3 right now ({d_short(REF)})</h2><p class="muted">{note}</p></div>
  <div class="picks">
{chr(10).join(pick_card(c) for c in PICKS[:3])}</div>
  <p class="muted small runner">{esc(tpl(B["prose"]["runnerUp"]))}</p>'''

def status_badge(c):
    return badge('Benchmark', 'status-benchmark') if c['status'] == 'benchmark' else badge('Active', 'status-active')

def list_cell(c):
    p = c['price']; qs = quoted_selling(c)
    if qs:
        return f'<strong>{money(qs, True)}</strong> <span class="badge plain">quoted</span><div class="delta">listed {money(p["listed"])}</div>'
    return f'<strong>{money(p["listed"])}</strong>' + (f'<div class="delta">{esc(p["listedNote"])}</div>' if p.get('listedNote') else '')

def deal_cell(c, tag='div'):
    d = c['deal']; out = badge(d.get('rating') or '—', 'deal ' + deal_cls(c))
    lines = [x for x in [d.get('display'), d.get('note')] if x]
    if tag == 'div':
        return out + ''.join(f'<div class="delta">{esc(x)}</div>' for x in lines)
    return out + (f'<span class="delta">{esc(" · ".join(lines))}</span>' if lines else '')

def note_cell(c, which='table'):
    parts = []
    if which == 'table' and c.get('features'): parts.append(f'<span class="muted">{esc(c["features"])}</span>')
    if c.get('tag'): parts.append(f'<strong>{esc(c["tag"])}</strong>')
    body = (c.get('notes') or {}).get(which) or (c.get('notes') or {}).get('table')
    if body: parts.append(esc(tpl(body, c)))
    parts.append(latest_html(c, short=(which == 'card')))
    return ' '.join(parts)

def also_text(c, card=False):
    a = c['links'].get('alsoOnCard') if card and c['links'].get('alsoOnCard') else c['links'].get('alsoOn')
    return ('also ' + ', '.join(a)) if a else ''

SHORTLIST = [c for c in IN_PLAY if c['cohort'] == 'aug7']
CANDIDATES = [c for c in IN_PLAY if c['cohort'] != 'aug7']

def shortlist_table():
    heads = [('#', 'num'), ('Status', ''), ('Source · also on', ''), ('Year', 'num'), ('Trim', ''), ('Miles', 'num'), ('List $', 'num'), ('Seller · City', ''), ('Deal / Δ', ''), ('History', ''), ('Note', '')]
    ths = ''.join(f'<th scope="col"{" class=" + chr(34) + cls + chr(34) if cls else ""}><button type="button">{esc(h)}<span class="si" aria-hidden="true"></span></button></th>' for h, cls in heads)
    rows = ''
    for c in SHORTLIST:
        d = c['dealer']; qs = quoted_selling(c)
        rows += f'''<tr>
      <td class="num" data-v="{c["rank"]}"><span class="rank sm">#{c["rank"]}</span></td><td data-v="{0 if c["status"] == "live" else 1}">{status_badge(c)}</td>
      <td data-v-text="{esc(c["links"]["primarySource"])}">{src_badge(c["links"]["primarySource"])}<div class="also">{esc(also_text(c))}</div></td>
      <td class="num" data-v="{c["year"]}">{c["year"]}</td>
      <td>{ext(c["links"]["primary"], esc(c["trim"]))}</td>
      <td class="num" data-v="{c["miles"]}">{num(c["miles"])}</td>
      <td class="num" data-v="{qs or c["price"]["listed"]}">{list_cell(c)}</td>
      <td>{esc(d["short"])}<br><span class="muted">{esc(d["city"])}</span></td>
      <td data-v="{deal_sort(c)}">{deal_cell(c)}</td>
      <td>{esc(hist_short(c))}</td>
      <td class="note">{note_cell(c, "table")}</td>
    </tr>'''
    return f'<div class="scroll"><table class="data sortable" id="shortlist-table"><thead><tr>{ths}</tr></thead><tbody>{rows}</tbody></table></div>'

def shortlist_cards():
    cards = ''
    for c in SHORTLIST:
        d = c['dealer']; cr = COST[c['rank']]; qs = quoted_selling(c); p = c['price']
        ptxt = f'{money(qs, True)} <span class="badge plain">quoted</span>' if qs else money(p['listed'])
        mo_note = 'at $0 down' + (f' · listed {money(p["listed"])}' if qs else (f' · was {money(p["aug7"])} {d_short(PUB)}' if p.get('aug7') and p['aug7'] != p['listed'] else ''))
        cards += f'''<article class="slc" role="listitem" data-rank="{c["rank"]}" data-price="{qs or p["listed"]}" data-miles="{c["miles"]}" data-year="{c["year"]}" data-monthly="{round(cr["m0"])}">
      <header class="slc-head"><span class="rank">#{c["rank"]}</span><h3 class="slc-title"><span class="yr">{c["year"]}</span> {esc(c["trim"])}</h3>{src_badge(c["links"]["primarySource"])}</header>
      <div class="slc-price"><span class="p">{ptxt}</span><span class="mo"><strong>{money(cr["m0"])}</strong>/mo <span class="muted">{mo_note}</span></span></div>
      <p class="slc-meta">{num(c["miles"])} mi · {esc(d["short"])} · {esc(d["city"])}</p>
      <dl class="slc-facts">
        <div><dt>Deal / Δ</dt><dd>{deal_cell(c, "span")}</dd></div>
        <div><dt>1-own / Acc</dt><dd>{esc(hist_short(c).replace(" · CPO", ""))}</dd></div>
        <div><dt>CPO</dt><dd>{"<strong>Yes</strong>" if c["history"].get("cpo") else "No"}</dd></div>
        <div><dt>Source · also on</dt><dd>{esc(c["links"]["primarySource"])}{("<span class=" + chr(34) + "also" + chr(34) + ">" + esc(also_text(c, True)) + "</span>") if also_text(c, True) else ""}</dd></div>
      </dl>
      <p class="slc-note">{note_cell(c, "card")}</p>
      {ext(c["links"]["primary"], "View listing", "btn block", f"View listing #{c['rank']} in a new tab")}
    </article>
    '''
    return f'''<div class="sl-tools"><label for="sl-sort">Sort by</label>
      <span class="selwrap"><select class="select" id="sl-sort">
        <option value="rank" selected>Value rank</option>
        <option value="price">Price · low to high</option>
        <option value="miles">Miles · low to high</option>
        <option value="year">Year · newest first</option>
        <option value="monthly">Monthly · low to high</option>
      </select></span></div>
    <div class="sl-cards" id="sl-cards" role="list">{cards}</div>'''

def sold_phrase(c):
    lab = c.get('soldInfo', {}).get('short') or f'{c["dealer"]["short"]} {c["year"]} {c["trim"].split(" (")[0]}'
    return f'#{c["rank"]} {lab} ({d_short(c["soldInfo"]["date"])})'

def removed_line(cars):
    if not cars: return ''
    return 'Removed as sold: ' + ', '.join(sold_phrase(c) for c in cars) + '.'

def candidates_table():
    rows = ''
    for c in CANDIDATES:
        d = c['dealer']; p = c['price']; qs = quoted_selling(c)
        car = ext(c['links']['primary'], esc(f'{c["year"]} {c["trim"]}')) + (f' <span class="badge warn">NEW {d_short(c["foundDate"])}</span>' if c.get('isNew') or c.get('foundDate') == REF else '')
        city = d['city'].split(',')[0] + ('' if d['state'] == 'WA' else ' ' + d['state'])
        if c.get('sellerDisplay'):
            seller = esc(c['sellerDisplay'])
        elif d['type'] == 'independent' or not d.get('website'):
            seller = esc(f'{d["name"]}, {city}' + (' WA' if d['state'] == 'WA' else ''))
        else:
            seller = ext(d['website'], esc(d['short'])) + ', ' + esc(city)
        if qs:
            price = f'{money(qs, True)} <span class="badge plain">quoted</span><div class="muted small">listed {money(p["listed"])}</div>'
        else:
            price = esc(price_listed_display(c)) + (f'<div class="muted small">{esc(p["listedNote"])}</div>' if p.get('listedNote') and not p.get('listedDisplay') else '')
        body = (c.get('notes') or {}).get('candidate') or ''
        note = f'{esc(c["features"])} {tpl(body, c)} {latest_html(c)}'
        rows += f'    <tr><td class="num">#{c["rank"]}</td><td>{car}</td><td>{seller}</td><td class="num">{num(c["miles"])}</td><td class="num">{price}</td><td class="note">{note}</td></tr>\n'
    return rows

def candidates_footer():
    sw = BOARD_SWEEPS[0]
    gone = [c for c in SOLD if c['cohort'] != 'aug7']
    g = (' and '.join(f'#{c["rank"]} ({c["dealer"]["short"]} {c["year"]} {c["trim"]}, {money(c["price"]["listed"])})' for c in gone) + f' sold and are removed. ') if gone else ''
    sc = sw.get('sourceCounts') or {}
    return (g + f'{d_short(sw["date"])} sweep: {sw.get("uniqueVins")} VINs across AutoTempest, CarGurus, KBB, CarMax, Carvana and Craigslist; {sw.get("newVins")} not seen before, {sw.get("newDisqualified")} disqualified (unwanted trim, out-of-area no-haggle units no better than #15, no value signal), {sw.get("newPassed")} added'
            + (f' as {", ".join("#%d" % r for r in sw.get("added", []))}' if sw.get('added') else '') + '. ' + esc(sw.get('note') or ''))

# ----------------------------------------------------------------------------- watchlist (parked + side-sweep groups)
def watch_move(w):
    l = w.get('latest') or {}
    if not l.get('seen', True): return f'not seen {d_short(l["asOf"])}' if l.get('asOf') else 'not seen'
    mv = l.get('move')
    bits = []
    if mv: bits.append(f'{signed(mv)} since first seen')
    elif l.get('price') is not None and not w.get('group'): bits.append('no move')
    if l.get('daysListed') is not None: bits.append(f'{l["daysListed"]} d listed')
    if l.get('deal'): bits.append(f'{l["deal"]} Deal')
    return ' · '.join(bits)

def watch_parked_table(items):
    rows = ''
    for w in items:
        l = w.get('latest') or {}
        price = money(l.get('price')) if l.get('price') is not None else (money(l.get('was')) + ' <span class="muted small">(last seen)</span>' if l.get('was') else '—')
        rows += (f'    <tr><td>{ext(w["url"], esc(w["car"]))}</td><td>{esc(w["dealer"])}{"" if w.get("state") in (None, "WA") else " <span class=" + chr(34) + "badge plain" + chr(34) + ">" + esc(w["state"]) + "</span>"}</td>'
                 f'<td class="num">{price}<div class="muted small">{esc(watch_move(w))}</div></td><td class="note">{esc(tpl(w["whyNot"]))}</td></tr>\n')
    return f'''<p class="scroll-hint" aria-hidden="true">scroll for more columns →</p>
  <div class="scroll"><table class="data watch">
    <thead><tr><th>Car</th><th>Seller</th><th>Price {d_short(REF)}</th><th>Why parked</th></tr></thead><tbody>
{rows}  </tbody></table></div>'''

def watch_links(w):
    names = {'cargurus': 'CarGurus', 'kbb': 'KBB', 'carscom': 'Cars.com', 'autotrader': 'Autotrader', 'dealer': 'dealer site', 'carmax': 'CarMax', 'carvana': 'Carvana'}
    ls = w.get('links') or {}
    return ' · '.join(ext(u, names.get(k, k), 'small') for k, u in ls.items() if u and u != w.get('url'))

def watch_detail_table(items):
    """Richer rows for side-sweep groups (year / trim / VIN / est. OTD / monthly / history / flags)."""
    rows = ''
    for w in items:
        h = w.get('history') or {}; dl = w.get('deal') or {}; mo = w.get('monthly') or {}
        title = f'{w.get("year", "")} {w.get("trim", "")}'.strip() or w['car']
        car = ext(w['url'], esc(title)) + (f'<div class="muted small">listed as “{esc(w["trimListed"])}”</div>' if w.get('trimListed') else '')
        car += f'<div class="muted small"><span class="nb">VIN {esc(w.get("vin") or "—")}</span>' + (f' · stock {esc(w["stock"])}' if w.get('stock') else '') + '</div>'
        more = watch_links(w)
        if more: car += f'<div class="small">also on {more}</div>'
        seller = esc(w['dealer']) + (f'<div class="muted small">{esc(w.get("city") or "")}' + (' · independent' if w.get('dealerType') == 'independent' else '') + '</div>' if w.get('city') or w.get('dealerType') else '')
        mv = watch_move(w)
        price = f'<strong>{money(w.get("price"))}</strong>' + (f'<div class="muted small">{num(w["miles"])} mi</div>' if w.get('miles') is not None else '') + (f'<div class="muted small">{esc(mv)}</div>' if mv else '')
        otd = (f'{money(w["estOtd"])}<div class="muted small">est. at {w.get("taxRate", META["defaultTaxRate"]):.2f}%</div>' if w.get('estOtd') else '—') + (f'<div class="small"><strong>{money(mo["m0"])}</strong>/mo at $0 dn</div><div class="muted small">{money(mo["m5"])}/mo at $5k dn</div>' if mo.get('m0') else '')
        hist = []
        if h.get('owners'): hist.append(f'{h["owners"]}-owner')
        if h.get('accidents') is not None: hist.append(f'{h["accidents"]} accidents' if h['accidents'] != 1 else '1 accident')
        if h.get('rental'): hist.append(f'rental: {h["rental"]}')
        if h.get('cpo'): hist.append(h['cpo'])
        if h.get('photos'): hist.append(f'{h["photos"]} photos')
        deal_txt = esc(dl.get('display') or '')
        flags = ''.join(f'<li>{esc(f)}</li>' for f in (w.get('flags') or []))
        why = (f'<div class="small hist"><strong>History:</strong> {esc(" · ".join(hist)) or "unverified"}' + (f' · {deal_txt}' if deal_txt else '') + '</div>'
               + f'{esc(tpl(w["whyNot"]))}' + (f'<ul class="flags small">{flags}</ul>' if flags else ''))
        rows += f'    <tr><td>{car}</td><td>{seller}</td><td class="num">{price}</td><td class="num">{otd}</td><td class="note">{why}</td></tr>\n'
    return f'''<p class="scroll-hint" aria-hidden="true">scroll for more columns →</p>
  <div class="scroll"><table class="data watch watch-detail">
    <thead><tr><th>Car · VIN</th><th>Seller</th><th>Price {d_short(REF)} · miles</th><th>Est. OTD · /mo</th><th>History · why it is watch-only</th></tr></thead><tbody>
{rows}  </tbody></table></div>'''

def watchlist_section():
    parts = ''
    for i, g in enumerate(WATCH_GROUPS):
        items = watch_items(g['key'])
        if not items: continue
        sw = next((s for s in SIDE_SWEEPS if s.get('scope') == g['key']), None)
        head = f'<h3 class="sub" id="watch-{re.sub(r"[^a-z0-9]+", "-", g["key"].lower())}">{esc(g["title"])} <span class="muted">({len(items)})</span></h3>'
        intro = f'<p class="small muted">{esc(tpl(g.get("intro") or ""))}</p>' if g.get('intro') else ''
        table = watch_parked_table(items) if i == 0 else watch_detail_table(items)
        foot = f'<p class="muted small">{d_short(sw["date"])} {esc(sw["kind"])}: {esc(sw.get("note") or "")}</p>' if sw else ''
        parts += f'  {head}\n  {intro}\n  {table}\n  {foot}\n'
    return parts

def trim_table():
    rows = ''
    for t in TRIMS:
        if t['low'] is None:
            low, delta, dcls = '<span class="muted">—</span>', '<span class="muted">—</span>', 'muted'
        else:
            b1, b2 = ('<strong>', '</strong>') if t['hl'] else ('', '')
            low = f'{b1}{money(t["low"])}{b2} <span class="muted small">({esc(t["lowSrc"])})</span>'
            dcls = 'muted' if t['vsNat'] else ('good-t' if t['delta'] < 0 else 'bad-t')
            delta = f'{b1}{signed(t["delta"])}{"²" if t["vsNat"] else ""}{b2}'
        rows += f'''<tr{' class="hl"' if t['hl'] else ''}>
      <td class="num">{t["year"]}</td><td>{esc(t["trim"])}</td>
      <td class="num">{money(t["kbbNational"])}</td>
      <td class="num">{money(t["kbbSeattle"]) if t["kbbSeattle"] else '<span class="muted">—</span>'}</td>
      <td class="num">{low}</td>
      <td class="num {dcls}">{delta}</td>
      <td class="num">{t["n"]}</td></tr>'''
    return f'''<p class="scroll-hint" aria-hidden="true">scroll for more columns →</p>
  <div class="scroll"><table class="data" id="trim-table"><thead><tr>
    <th class="num">Year</th><th>Trim</th><th class="num">KBB nat'l FPP</th><th class="num">KBB Seattle FPP¹</th><th class="num">Lowest clean listing ({d_short(REF)})</th><th class="num">Δ vs Seattle</th><th class="num">Listings</th>
  </tr></thead><tbody>{rows}</tbody></table></div>'''

def soft_market():
    out = []
    withsea = [t for t in TRIMS if t['kbbSeattle'] and t['low'] is not None]
    if withsea:
        best = min(withsea, key=lambda t: t['delta'])
        out.append((f'{best["year"]} {best["trim"]} is the standout buy', f': {money(best["low"])} ({best["lowSrc"]}) vs Seattle FPP {money(best["kbbSeattle"])}, {money(abs(best["delta"]))} under book.'))
        under = sorted([t for t in withsea if t['delta'] < -1000 and t is not best], key=lambda t: t['delta'])
        if under:
            out.append(('Also well under book', ': ' + '; '.join(f'{t["year"]} {t["trim"]} {money(t["low"])} vs {money(t["kbbSeattle"])} ({signed(t["delta"])})' for t in under[:3]) + '.'))
    p23 = next((t for t in TRIMS if t['year'] == 2023 and t['trim'] == '2.5 S Premium' and t['low']), None)
    pp23 = next((t for t in TRIMS if t['year'] == 2023 and t['trim'] == '2.5 S Premium Plus' and t['low']), None)
    if p23 and pp23:
        gap = pp23['low'] - p23['low']
        out.append(('Premium Plus vs. Premium (2023)', f': lowest Premium is {money(p23["low"])}, lowest Premium Plus {money(pp23["low"])}; the {money(gap)} gap buys the 360° camera, ventilated seats, wireless CarPlay and heated rear seats, about {money(gap * PER1K / 1000)}/mo.'))
    over = [t for t in withsea if t['delta'] > 300]
    if over:
        out.append(('Trading over book', ': ' + '; '.join(f'{t["year"]} {t["trim"]} ({money(t["low"])} vs {money(t["kbbSeattle"])}, {signed(t["delta"])})' for t in over) + '. Negotiate these to FPP or walk to the tier below.'))
    return ''.join(f'<li><strong>{esc(a)}</strong>{esc(b)}</li>' for a, b in out)

def rates_used():
    seen = {}
    for c in IN_PLAY:
        d = c['dealer']
        if d['state'] == 'WA': seen[d['city'].split(',')[0]] = d['taxRate']
    return ' · '.join(f'{k} {v:.2f}%' for k, v in sorted(seen.items(), key=lambda kv: -kv[1]))

def cost_assumptions():
    rows = [('Term', f'{N} months'), ('APR', f'{APR:.2f}%, {META["aprSource"]}'), ('Credit-union check', META['creditUnionCheck']), ('CPO promo', META['cpoPromo']),
            ('Sales tax', f'Dealer-city vehicle rate: {rates_used()}; Oregon dealers → {META["useTaxRateOR"]:.2f}% WA use tax'),
            ('Fees', f'+${META["docFeeWA"]} doc (WA; ${META["docFeeOR"]} OR; $0–$100 where the dealer advertises none) · +${META["licenseEst"]} est. license / title / RTA'),
            ('Out-the-door', 'Est. OTD = price × (1 + rate) + doc + $%d; a “quoted” chip marks cars with a written dealer sheet in hand, figures kept off this page' % META['licenseEst']),
            ('Payment', f'M = P · r(1+r)^n / ((1+r)^n − 1), r = APR/12, n = {N}')]
    return ''.join(f'<div><dt>{esc(k)}</dt><dd>{esc(v)}</dd></div>' for k, v in rows)

def basis_cell(r):
    if r['basis'] == 'quoted':
        return f'<span class="badge basis quoted">quoted</span><span class="sub">{d_short(r["date"])} sheet</span>'
    return f'<span class="badge basis est">est.</span><span class="sub">{r["rate"]:.2f}%{" use tax" if r["car"]["dealer"]["state"] != "WA" else ""} + ${r["doc"]:,.0f} doc</span>'

def cost_table():
    rows = ''
    for r in COST_SORTED:
        c = r['car']
        name = f'{c["year"]} {c["trim"].split(" ·")[0]} <span class="sub">{esc(c["dealer"]["short"])}{" · benchmark" if c["status"] == "benchmark" else ""}{" · accident on Carfax" if not clean_history(c) else ""}</span>'
        otd = money(r['otd'])
        ptxt = money(r['price']) + (f'<span class="sub">listed {money(c["price"]["listed"])}</span>' if r['basis'] == 'quoted' and round(r['price']) != c['price']['listed'] else '')
        rows += f'<tr{" class=" + chr(34) + "bench" + chr(34) if c["status"] == "benchmark" else ""}><td class="num"><span class="rank sm">#{c["rank"]}</span></td><td>{name}</td><td>{basis_cell(r)}</td><td class="num">{ptxt}</td><td class="num">{otd}</td><td class="num"><strong>{money(r["m0"])}</strong></td><td class="num">{money(r["m5"])}</td><td class="num">{money(r["interest"])}</td></tr>'
    return f'''<p class="scroll-hint" aria-hidden="true">scroll for more columns →</p>
  <div class="scroll"><table class="data" id="cost-table"><thead><tr><th class="num">#</th><th>Car</th><th>Basis</th><th class="num">Price</th><th class="num">OTD</th><th class="num">@ $0 down</th><th class="num">@ $5k down</th><th class="num">Total interest @ $0</th></tr></thead><tbody>{rows}</tbody></table></div>'''

def compare_table():
    cs, st = COST[CHEAPEST['rank']], COST[STRETCH['rank']]
    def rowf(label, c, r):
        return (f'<tr><th scope="row">{label}</th><td>#{c["rank"]} {c["year"]} {esc(c["trim"])} · {round(c["miles"] / 1000)}k mi<span class="sub">{esc(c["dealer"]["short"])}, {esc(c["dealer"]["city"])}</span></td>'
                f'<td class="num">{money(r["price"])}</td><td class="num">{money(r["otd"])} <span class="badge basis {r["basis"]}">{r["basis"]}{"" if r["basis"] == "quoted" else ""}</span></td><td class="num">{money(r["m0"])}</td><td class="num">{money(r["m5"])}</td></tr>')
    dy = STRETCH['year'] - CHEAPEST['year']; dm = round((STRETCH['miles'] - CHEAPEST['miles']) / 1000)
    what = [f'{dy:+d} model yr' + ('s' if abs(dy) != 1 else '')] if dy else []
    if STRETCH.get('turbo') != CHEAPEST.get('turbo'): what.append('+turbo' if STRETCH.get('turbo') else '−turbo')
    if CHEAPEST.get('ventilatedSeats') and not STRETCH.get('ventilatedSeats'): what.append('−ventilated seats')
    what.append(f'{"−" if dm < 0 else "+"}{abs(dm)}k mi')
    delta = (f'<tr class="delta-row"><th scope="row">Δ</th><td>{esc(", ".join(what))}</td><td class="num">{signed(st["price"] - cs["price"])}</td><td class="num">{signed(st["otd"] - cs["otd"])}</td>'
             f'<td class="num"><strong>{signed(st["m0"] - cs["m0"])}/mo</strong></td><td class="num">{signed(st["m5"] - cs["m5"])}/mo</td></tr>')
    return (f'<div class="scroll fit"><table class="data compact" id="compare-table"><thead><tr><th></th><th>Car</th><th class="num">Price</th><th class="num">OTD</th><th class="num">@ $0 down</th><th class="num">@ $5k down</th></tr></thead>'
            f'<tbody>{rowf("Cheapest solid", CHEAPEST, cs)}{rowf("Stretch", STRETCH, st)}{delta}</tbody></table></div>'
            f'<p class="rulenote">Cheapest solid = {esc(SOLID_RULE)}. Stretch = {esc(STRETCH_RULE)}. Both are recomputed from the board on every refresh.</p>')

# calculator: pre-filled with the cheapest-solid car; a written sheet reproduces exactly (price × (1+tax) + doc + licence)
def calc_defaults():
    c = CHEAPEST; r = COST[c['rank']]; q = c.get('quote') or {}
    d = dict(price=r['price'], tax=r['rate'], doc=r['doc'], lic=META['licenseEst'])
    d['est'] = d['price'] * (1 + d['tax'] / 100) + d['doc'] + d['lic']
    # site rule: the public example always uses the estimate; dealer figures stay off the page
    d.update(otdq=0, otd=d['est'], mode='est')
    d['m0'] = pmt(d['otd']); d['m5'] = pmt(max(0, d['otd'] - 5000)); d['interest'] = d['m0'] * N - d['otd']
    # guard: the static example must equal the car's cost-table row (never a new number)
    for k in ('otd', 'm0', 'm5', 'interest'):
        assert round(d[k]) == round(r[k]), f'calculator example disagrees with cost table on {k}: {d[k]} vs {r[k]}'
    return d
CALC = calc_defaults()

def calculator():
    c = CHEAPEST; d = CALC; q = c.get('quote') or {}
    inp = lambda id, val, pre, post, mode: f'<span class="inwrap">{"<span class=" + chr(34) + "pre" + chr(34) + ">" + pre + "</span>" if pre else ""}<input type="text" id="{id}" value="{val}" inputmode="{mode}" autocomplete="off" autocorrect="off" spellcheck="false" enterkeyhint="done">{"<span class=" + chr(34) + "post" + chr(34) + ">" + post + "</span>" if post else ""}</span>'
    where = c['dealer']['city'].split(',')[0]
    if d['mode'] == 'written':
        sheet = ''
        if q.get('selling') and q.get('taxRate') and q.get('license') is not None:
            sheet = f" ({money(q['selling'])} selling + {q['taxRate']:.2f}% tax + ${q.get('doc') or 0:,.0f} doc + ${q['license']:,.0f} licence on the {d_short(q['date'])} sheet)"
        how = (f"Pre-filled with #{c['rank']}: its price at the {where} rate and, in the written box, the dealer's out-the-door total of {money(d['otdq'], True)}{sheet}. "
               f"Clear the written box to see this page's estimate instead ({money(d['est'])} with the ${d['lic']:,.0f} licence assumption).")
    else:
        how = f"Pre-filled with #{c['rank']} at its {where} rate."
    return f'''<div class="calc" id="calculator">
    <h3 class="sub">Payment calculator</h3>
    <p class="muted small">Same math as the table: OTD = price × (1 + tax) + doc + licence (tax on the vehicle price; the doc fee and licence estimate are added untaxed, as on the dealer sheets received), or the written out-the-door figure if you enter one; standard amortization. {esc(how)}</p>
    <div class="calc-grid">
      <label>Vehicle price {inp('c-list', f"{d['price']:g}", '$', '', 'decimal')}</label>
      <label>Sales tax {inp('c-tax', f"{d['tax']:.2f}", '', '%', 'decimal')}</label>
      <label>Written OTD (optional) {inp('c-otdq', f"{d['otdq']:.2f}" if d['otdq'] else '', '$', '', 'decimal')}</label>
      <label>Down payment {inp('c-down', '0', '$', '', 'decimal')}</label>
      <label>APR {inp('c-apr', f'{APR:.2f}', '', '%', 'decimal')}</label>
      <label>Term {inp('c-term', str(N), '', 'mo', 'numeric')}</label>
    </div>
    <div class="calc-out" aria-live="polite">
      <div><span class="k" id="o-otd-k">Out-the-door ({'written' if d['otdq'] else 'est.'})</span><span class="v" id="o-otd">{money(d['otd'])}</span></div>
      <div><span class="k">Amount financed</span><span class="v" id="o-fin">{money(d['otd'])}</span></div>
      <div class="em"><span class="k">Monthly payment</span><span class="v" id="o-mo">{money(d['m0'])}/mo</span></div>
      <div><span class="k">Total interest</span><span class="v" id="o-int">{money(d['interest'])}</span></div>
      <div><span class="k">Per $1,000 financed</span><span class="v" id="o-1k">${PER1K:.2f}/mo</span></div>
    </div>
    <p class="calc-example"><strong>Worked example, #{c['rank']} {esc(car_title(c))} (cheapest solid):</strong> {money(d['price'])} price → {money(d['otd'])} out-the-door → <strong>{money(d['m0'])}/mo</strong> at $0 down, or <strong>{money(d['m5'])}/mo</strong> with $5,000 down ({APR:.2f}% APR, {N} mo). Constants: ${d['doc']:,.0f} doc fee and ${d['lic']:,.0f} licence estimate.</p>
  </div>'''

def no_haggle():
    out = ''
    for n in B['noHaggle']:
        cm = f'{esc(n["seller"])} <strong>{money(n["price"])}</strong> <span class="muted">({esc(n["detail"])}{", #%d" % n["car"] if n.get("car") else ""})</span>' if n.get('price') else f'{esc(n["seller"])}: <span class="muted">{esc(n["detail"])}</span>'
        cv = f' · Carvana {money(n["carvana"]["price"])} <span class="muted">({esc(n["carvana"]["detail"])})</span>' if n.get('carvana') else ''
        note = f'; {esc(n["note"])}' if n.get('note') else ''
        out += f'<li><strong>{esc(n["tier"])}:</strong> {cm}{cv}{note}.</li>'
    return out

def sources_table():
    rows = ''.join(f'<tr><td><strong>{esc(s["source"])}</strong></td><td>{badge(s["statusLabel"], "status " + s["status"])}</td><td class="num">{s["pulled"]}</td><td class="small">{esc(s["added"])}</td></tr>' for s in B['sources'])
    return f'<div class="scroll"><table class="data" id="sources-table"><thead><tr><th>Source</th><th>Status</th><th class="num">Pulled</th><th>What it added</th></tr></thead><tbody>{rows}</tbody></table></div>'

def page_js():
    js = open(os.path.join(ASSETS, 'report.page.js'), encoding='utf-8').read()
    pts = [{'y': p['y'], 'm': p['m'], 'p': p['p'], 'r': p['r'], 't': p['t'], 'd': p['d'], 'c': p['c'], 's': p['s']} for p in POINTS]
    js = (js.replace('__POINTS__', json.dumps(pts, ensure_ascii=False, separators=(',', ':')))
            .replace('__EMAIL__', json.dumps(B['prose']['email'], ensure_ascii=False))
            .replace('__DOC__', str(CALC['doc'])).replace('__LIC__', str(CALC['lic'])).replace('__TAX__', f"{CALC['tax']:.2f}"))
    assert '__' not in re.sub(r'__proto__', '', js) or not re.search(r'__[A-Z]+__', js), 'unreplaced placeholder in page JS'
    return js

def downloads_line():
    return ('<p class="downloads">Downloads (same data as this page, regenerated ' + d_short(REF) + '): <a href="CX5-Seattle-Buyers-Report.pdf">PDF</a> · <a href="CX5-Seattle-Buyers-Report.xlsx">Excel</a> · <a href="cx5_report.docx">Word</a></p>')

def build_index():
    css = open(os.path.join(ASSETS, 'report.css'), encoding='utf-8').read()
    n_live, n_sold, n_q = len(IN_PLAY), len(SOLD), len(QUOTED)
    pill = f'Published {d_short(PUB)} · refreshed {d_long(REF)}: {n_live} cars in play, {n_sold} sold, {n_q} written quotes in hand · every row shows price, miles, days listed and dealer replies as of the {d_short(REF)} sweep · listings change daily; verify before contacting'
    sold_aug7 = [c for c in SOLD if c['cohort'] == 'aug7']
    latest_foot = (f'Data captured {d_long(PUB)}; board and candidates re-checked with fresh sweeps ' + ', '.join(d_short(d) for d in SWEEP_DATES) + f', {d_iso(REF).year}'
                   + ''.join(f'; {esc(s["scope"].split(" ")[0])} model year swept separately {d_short(s["date"])} (watchlist only)' for s in SIDE_SWEEPS)
                   + '. This page, the status board, the map and the downloads are regenerated together from one board file on every refresh.')
    n_watch = len(B['watchlist']); side_groups = [g for g in WATCH_GROUPS[1:] if watch_items(g['key'])]
    body = f'''<script>document.documentElement.classList.add('js');</script>
<a class="skip" href="#tldr">Skip to content</a>
<nav class="topnav" aria-label="Sections"><div class="wrap navwrap">
  <a class="brand" href="#top">CX-5 Buyer's Report</a>
  <div class="navlinks">{''.join(f'<a href="{h}"><span>{esc(l)}</span></a>' for h, l in NAV)}</div>
</div></nav>

<header class="masthead wrap" id="top">
  <p class="eyebrow">Used-car research · Seattle, WA</p>
  <h1>{esc(META["title"]).replace("CX-5", '<span class="nb">CX-5</span>')}</h1>
  <p class="scope">{esc(META["scope"])}</p>
  <div class="mast-row">
    <span class="pill"><span class="dot" aria-hidden="true"></span>{esc(pill)}</span>
    <span class="funnel">{esc(META["funnel"])}</span>
  </div>
  {downloads_line()}
  <p class="askline"><a href="ask.html"><strong>Have a listing you want checked?</strong> <span aria-hidden="true">&rarr;</span> Ask page</a></p>
  <p class="tipline">Tip: open this file in Safari or Chrome for sorting and the payment calculator.</p>
</header>

<main class="wrap">

<section class="card" id="tldr">
  <h2>TL;DR</h2>
  <ul class="tldr">{tldr()}</ul>
</section>

<section class="card" id="changes">
  <div class="sec-head"><h2>What changed</h2><p class="muted">Refresh log; newest first. Generated build {d_iso(REF).isoformat()}.</p></div>
  <ul class="changes">{changes()}</ul>
</section>

<section class="card" id="top3">
{top3()}
</section>

<section class="card" id="shortlist">
  <div class="sec-head"><h2>Shortlist: {len(SHORTLIST)} active cars, ranked by value</h2><p class="muted">Click a column header to sort. Row data is as of the {d_short(REF)} sweep: today's listed price (or a lower written quote, marked “quoted”), latest odometer, days listed, today's CarGurus / KBB value figure, and the latest word from each dealer. Sold cars are removed (list below the table); rank numbers stay stable, so gaps are expected. The <a href="CX5-Seattle-Buyers-Report.pdf">PDF</a>, <a href="CX5-Seattle-Buyers-Report.xlsx">Excel</a> and <a href="cx5_report.docx">Word</a> copies carry the same {d_short(REF)} data.</p></div>
  <p class="small">{esc(B["prose"]["shortlistIntro"])}</p>
  <div class="sl-table-view">{shortlist_table()}</div>
  <div class="sl-card-view">{shortlist_cards()}</div>
  <p class="muted small removed">{esc(removed_line(SOLD))}{" No further car met the two-source sold test on " + d_short(REF) + "." if not BOARD_SWEEPS[0].get("sold") else ""} Rank numbers are kept stable, so gaps are expected.</p>
  <p class="muted small dq">{esc(B["prose"]["notableDQ"])}</p>
</section>

<section class="card" id="newfinds">
  <div class="sec-head"><h2>New candidates: {" + ".join(sorted({d_short(c["foundDate"]) + (" sweep" if c["foundDate"] == REF else " re-scan") for c in CANDIDATES}, key=lambda s: s))}</h2><p class="muted">Comfort-first additions from the WA-priority sweeps, not yet folded into the ranked shortlist above. Row data as of {d_short(REF)}: listed asking price (or a lower written quote, marked “quoted”), latest miles, days listed, and the latest word from the dealer.</p></div>
  <div class="scroll"><table class="data">
    <thead><tr><th>#</th><th>Car</th><th>Seller</th><th>Miles</th><th>Price</th><th>Why it matters · latest</th></tr></thead><tbody>
{candidates_table()}  </tbody></table></div>
  <p class="muted small">{candidates_footer()}</p>
</section>

<section class="card" id="watchlist">
  <div class="sec-head"><h2>Watchlist: {n_watch} cars screened, not on the board</h2><p class="muted">Not numbered board cars and not in the top picks, cost table or chart. Re-priced on each sweep (price column as of {d_short(REF)}); a car moves onto the board only if it clears the same filters and beats a live finalist on out-the-door cost.{" " + " ".join(esc(g["title"].split(" (")[0]) + " sits in its own group below." for g in side_groups) if side_groups else ""}</p></div>
{watchlist_section()}</section>

<section class="card" id="chart">
  <div class="sec-head"><h2>Price vs. miles: where the picks sit in the market</h2></div>
  <div class="legend" id="scatter-legend">
    <span class="lg-item">{legend_glyph(2021)} 2021</span>
    <span class="lg-item">{legend_glyph(2022)} 2022</span>
    <span class="lg-item">{legend_glyph(2023)} 2023</span>
    <span class="lg-sep" aria-hidden="true"></span>
    <span class="lg-item"><svg class="lg cloud" viewBox="0 0 14 14" aria-hidden="true"><circle cx="7" cy="7" r="3.4"/></svg> passing listing ({N_CLOUD})</span>
    <span class="lg-item"><svg class="lg slmark" viewBox="0 0 14 14" aria-hidden="true"><circle cx="7" cy="7" r="5"/></svg> live board car, labeled by rank</span>
    <span class="lg-item"><svg class="lg gonemark" viewBox="0 0 14 14" aria-hidden="true"><circle cx="7" cy="7" r="5"/></svg> sold ({", ".join("#%d" % c["rank"] for c in SOLD)}), hollow at last asking price</span>
    <label class="toggle"><input type="checkbox" id="tint"> Tint cloud by model year</label>
  </div>
  <div class="chart-wrap" id="scatter-wrap">{scatter_svg(SCATTER["d"])}{scatter_svg(SCATTER["m"])}</div>
  <p class="caption">All {N_CLOUD} listings that passed the {d_short(PUB)} filters (from the merged, de-duplicated set), re-priced wherever the {d_short(REF)} sweep saw the same VIN ({N_SEEN} of {N_CLOUD}), plus every board car at today's price. Read it vertically: at any given mileage, a dot <em>below the cloud</em> is priced under comparable cars; that is where the numbered live cars should sit, and mostly do. Sold cars are drawn hollow and unlabeled at their last asking price. Hover or tap a dot for details.</p>
</section>

<section class="card" id="trims">
  <div class="sec-head"><h2>Which trim is the best buy</h2><p class="muted">KBB Fair Purchase Price vs. the lowest clean listing still live</p></div>
  <p class="small muted">{esc(B["prose"]["trimIntro"])} Lowest clean listing = cheapest {d_short(PUB)}-passing listing the {d_short(REF)} sweep still saw (by VIN, at today's price) or a live board car with a verified 0-accident history; “—” where nothing in that cell is live.</p>
  {trim_table()}
  <div class="footnotes small muted">{''.join(f'<p>{esc(f)}</p>' for f in B["prose"]["trimFootnotes"])}</div>
  <h3 class="sub">Δ vs. KBB Seattle fair purchase price <span class="muted">(rows with a Seattle FPP and a live listing)</span></h3>
  <div class="chart-wrap" id="bars-wrap">{bars_desktop()}{bars_mobile()}</div>
  <h3 class="sub">Where the market is soft right now</h3>
  <ul class="soft">{soft_market()}</ul>
</section>

<section class="card" id="cost">
  <div class="sec-head"><h2>What it costs per month</h2><p class="muted">Live cars only, sorted by out-the-door. Where a dealer has replied in writing, the quoted OTD replaces the estimate.</p></div>
  <dl class="assump">{cost_assumptions()}</dl>
  <p class="small muted taxnote">{esc(META["taxNote"])}</p>
  {cost_table()}
  <p class="thumb">Rule of thumb: every $1,000 financed ≈ ${PER1K:.2f}/mo at {APR:.2f}% / {N} mo.</p>
  <h3 class="sub">Cheapest solid vs. stretch</h3>
  {compare_table()}
  {calculator()}
</section>

<section class="card" id="nohaggle">
  <div class="sec-head"><h2>No-haggle ceiling: CarMax / Carvana</h2></div>
  <p>{esc(B["prose"]["noHaggleIntro"])}</p>
  <ul class="nh">{no_haggle()}</ul>
</section>

<section class="card" id="email">
  <div class="sec-head"><h2>Email template: itemized OTD request</h2><button type="button" class="btn ghost" id="copy-btn" data-label="Copy">Copy</button></div>
  <blockquote class="email" id="email-text">{esc(B["prose"]["email"]).replace("itemized out-the-door quote in writing", "<strong>itemized out-the-door quote in writing</strong>")}</blockquote>
  <textarea class="email-ta" id="email-ta" readonly rows="9" aria-label="Email template text, selected for copying" hidden>{esc(B["prose"]["email"])}</textarea>
  <p class="copy-status" id="copy-status" aria-live="polite"></p>
</section>

<section class="card" id="sources">
  <div class="sec-head"><h2>Sources &amp; method</h2><p class="muted">{esc(B["prose"]["sourcesHead"])}</p></div>
  {sources_table()}
  <p>{esc(B["prose"]["honestRead"]).replace("Honest read:", "<strong>Honest read:</strong>")}</p>
  <p>{esc(B["prose"]["dedupe"]).replace("Dedupe:", "<strong>Dedupe:</strong>")}</p>
  <h3 class="sub">Re-check sweeps</h3>
  <ul class="rules">{''.join(f'<li><strong>{esc(d_long(s["date"]))}:</strong> {esc(s["kind"])}. {esc(s.get("method") or "")}</li>' for s in B["sweeps"])}</ul>
  <h3 class="sub">Filter &amp; ranking rules</h3>
  <ul class="rules">{''.join(f'<li>{esc(r)}</li>' for r in B["prose"]["filterRules"])}</ul>
  <p class="recall">{esc(B["prose"]["recallNote"]).replace("NHTSA recalls:", "<strong>NHTSA recalls:</strong>").replace("nhtsa.gov/recalls", '<a href="https://www.nhtsa.gov/recalls" target="_blank" rel="noopener">nhtsa.gov/recalls</a>')}</p>
  <h3 class="sub">Footnotes</h3>
  <ul class="foot small muted">{''.join(f'<li>{esc(f)}</li>' for f in B["prose"]["footnotes"])}<li>{esc(latest_foot)}</li></ul>
</section>

</main>

<footer class="wrap footer"><p>Research compiled {d_long(PUB)} as a read-only scan; buyer outreach to dealers began Aug 11 and listings were last re-checked {d_long(REF)} (see the <a href="status.html">status board</a>). Not affiliated with any seller. Verify history reports and pricing independently before purchase.</p></footer>
<div class="tip" id="tip" role="tooltip" hidden></div>
<script>{page_js()}</script>
'''
    doc = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
{FAVICON}
<title>CX-5 Seattle Buyer's Report</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<meta name="format-detection" content="telephone=no">
<meta name="color-scheme" content="light">
<meta name="generator" content="tools/build_site.py from data/board.json (refreshed {REF})">
<style>{css}</style>
</head>
<body>
{body}</body>
</html>
'''
    return ascii_safe(doc)

# ----------------------------------------------------------------------------- status.html
def yr_chip(c): return f'<span class="yr y{str(c["year"])[2:]}">\'{str(c["year"])[2:]}</span>'

def dealer_links(d, suffix=True):
    sites = d.get('sites') or []
    if sites:
        s = ' / '.join(f'<a href="{esc(x["url"])}">{esc(x["name"])}</a>' for x in sites)
    else:
        s = esc(d['name'])
    extra = d['statusName'].replace(d.get('short') or '', '').replace(' / '.join(x['name'] for x in sites), '').strip() if suffix else ''
    # statusName carries the qualifier ("(Portland OR)", "Renton · no transfer fee"): append whatever is not the linked name
    sn = d['statusName']
    for x in sites: sn = sn.replace(x['name'], '\x00', 1)
    tail = sn.split('\x00')[-1] if '\x00' in sn else ''
    return s + esc(tail) if sites else esc(d['statusName'])

def fit_order(c): return (c.get('comfortRank') or 99, c['rank'])

def status_rows():
    rows = ''
    for c in sorted(IN_PLAY, key=fit_order):
        sbd = c.get('statusBoard') or {}
        d = c['dealer']; p = c['price']; q = c.get('quote') or {}
        tshort = c["trim"] + (" · CPO" if c["history"].get("cpo") and "CPO" not in c["trim"] else "")
        car = f'<a href="{esc(c["links"]["primary"])}">{yr_chip(c)} {esc(tshort)}{(" " + esc(sbd["carSuffix"])) if sbd.get("carSuffix") else ""}</a>'
        if c.get('foundDate') == REF: car += f' <span class="note">NEW {d_short(REF)}</span>'
        listnote = sbd.get('listNote')
        qs = quoted_selling(c)
        if qs and not listnote: listnote = f'quoted selling {money(qs, True)}'
        elif qs and 'quoted' not in (listnote or ''): listnote = f'{listnote}; quoted selling {money(qs, True)}'
        lst = esc(price_listed_display(c)) + (f' <span class="note">{esc(tpl(listnote, c))}</span>' if listnote else '')
        ab = sbd.get('availBadge') or ('Reference' if c['status'] == 'benchmark' else 'Active')
        avail = f'<span class="badge ok">{esc(ab)}</span>' + (f' <span class="note">{esc(tpl(sbd["availability"], c))}</span>' if sbd.get('availability') else '')
        inq = esc(sbd.get('inquiry') or {'none': 'Not contacted', 'nohaggle': '—'}.get(c['contact'], 'Sent'))
        if c['contact'] == 'nohaggle':
            wq = 'Fixed price'
        elif sbd.get('quoteBadge'):
            wq = f'<span class="badge {sbd.get("quoteBadgeCls") or "wait"}">{esc(sbd["quoteBadge"])}</span>' + (f' <span class="note">{esc(sbd["quoteNote"])}</span>' if sbd.get('quoteNote') else '')
        elif q:
            wq = '<span class="badge ok">Received</span>' + (f' <span class="note">{money(q["otd"], True)} OTD</span>' if q.get('otd') else '')
        elif c['contact'] in ('sent', 'engaged'):
            wq = '<span class="badge wait">Awaiting</span>'
        else:
            wq = '—'
        rows += f'      <tr><td class="num">{c["rank"]}</td><td>{car}</td><td>{dealer_links(d)}</td><td class="num">{lst}</td><td>{avail}</td><td class="num">{inq}</td><td>{wq}</td></tr>\n'
    return rows

def status_inquiries():
    rows = ''
    for k in B['inquiryOrder']:
        d = DEALERS[k]; i = d.get('inquiry') or {}
        cars_here = [c for c in CARS if c['dealerKey'] == k]
        name = dealer_links(d) if d.get('sites') else esc(d['statusName'])
        if all(c['contact'] == 'none' for c in cars_here) and cars_here and not d.get('sites'):
            name = esc(d['statusName']) + ' · ' + ', '.join(f'#{c["rank"]}' for c in cars_here)
        rows += f'      <tr><td>{name}</td><td class="num">{esc(i.get("sent") or "—")}</td><td>{esc(i.get("latest") or "—")}</td></tr>\n'
    return rows

def status_sold():
    rows = ''
    for c in SOLD:
        d = c['dealer']; si = c['soldInfo']
        label = si.get('label') or f'{c["trimFull"]} · {round(c["miles"] / 1000)}k mi'
        rows += f'      <tr class="gone"><td><a href="{esc(c["links"]["primary"])}">{yr_chip(c)} {esc(label)}</a></td><td>{dealer_links(d)}</td><td class="num">{money(c["price"]["listed"])}</td><td><span class="badge sold">Sold</span> <span class="note">{esc(si["how"])}</span></td></tr>\n'
    return rows

def build_status():
    css = open(os.path.join(ASSETS, 'status.css'), encoding='utf-8').read()
    sw = BOARD_SWEEPS[0]
    doc = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
{FAVICON}
<title>CX-5 Search: Live Status Board</title>
<meta name="generator" content="tools/build_site.py from data/board.json (refreshed {REF})">
<style>
{css}
</style>
</head>
<body>
<nav class="topnav" aria-label="Sections"><div class="navwrap">
  <a class="brand" href="index.html">CX-5 Buyer's Report</a>
  <div class="navlinks">{pages_nav("status.html")}</div>
</div></nav>

<header class="masthead wrap">
  <p class="eyebrow">Live board · availability, inquiries &amp; quotes</p>
  <h1>Search status: <em>live board</em></h1>
  <p class="scope">Last updated <code>{d_dow(REF)} · {esc(sw["kind"].split(" sweep")[0])} sweep</code> (dealer replies logged through {esc(META["commsThrough"])}) · {esc(B["prose"]["statusScope"])}</p>
</header>

<main class="wrap">

<section class="card">
  <h2>Cars in play: {len(IN_PLAY)}</h2>
  <div class="scroll">
    <table>
      <tr><th>#</th><th>Car</th><th>Dealer</th><th>List</th><th>Availability</th><th>Inquiry</th><th>Written quote</th></tr>
{status_rows()}    </table>
  </div>
  <p class="note">{d_short(REF)} sweep: {esc(sw.get("note") or "")} {esc(B["prose"]["statusFootnote"]).replace("full shortlist table", '<a href="index.html#shortlist">full shortlist table</a>').replace("trim guide", '<a href="trims.html">trim guide</a>')} {len(QUOTED)} written quotes in hand, {len(SOLD)} cars sold since {d_short(PUB)}.</p>
</section>

<section class="card">
  <h2>Dealer inquiries</h2>
  <div class="scroll">
    <table>
      <tr><th>Dealer</th><th>Inquiry sent</th><th>Latest from them</th></tr>
{status_inquiries()}    </table>
  </div>
</section>

<section class="card">
  <h2>Sold and removed</h2>
  <div class="scroll">
    <table>
      <tr><th>Car</th><th>Dealer</th><th>Was listed</th><th>Status</th></tr>
{status_sold()}    </table>
  </div>
  <p class="note">Removed from the report tables when confirmed gone; the report, its PDF / Excel / Word downloads and this board are regenerated together from the same board file, so all of them show the {d_short(REF)} set.</p>
</section>

</main>
<footer class="footer wrap">Companion to the <a href="index.html">CX-5 Seattle Buyer's Report</a>. Availability is best-effort: a car is only truly available when the dealer confirms it on the phone or in writing.</footer>
</body>
</html>
'''
    return ascii_safe(doc)

# ----------------------------------------------------------------------------- map.html
PIN = {
    'contacted': {'color': '#1a7657', 'label': 'Contacted — quote pending or in hand', 'cls': 'good'},
    'todo': {'color': '#c8860d', 'label': 'Live, not yet contacted', 'cls': 'warn'},
    'nohaggle': {'color': '#2a5da8', 'label': 'No-haggle (CarMax) — fixed price', 'cls': 'info'},
    'sold': {'color': '#898179', 'label': 'Sold / parked — nothing live here', 'cls': 'sold'},
}
CAR_CLS = {'quote': 'good', 'contacted': 'good', 'foldin': 'muted', 'todo': 'warn', 'nohaggle': 'info', 'sold': 'sold'}

def map_kind(c):
    if c['status'] == 'sold': return 'sold'
    if c['status'] == 'benchmark' or c['contact'] == 'nohaggle': return 'nohaggle'
    if c['contact'] == 'quote': return 'quote'
    if c['contact'] in ('sent', 'engaged'): return 'contacted'
    return 'todo'

def map_car(c):
    kind = map_kind(c); p = c['price']
    line = f'{c["year"]} CX-5 {c["trimFull"].split(" (")[0].replace(" — Mazda Certified Pre-Owned", " · Mazda CPO")}' + (' (ventilated seats)' if c.get('ventilatedSeats') and 'entilat' not in c['trimFull'] and 'Signature' not in c['trimFull'] else '') + f' · {num(c["miles"])} mi'
    if kind != 'sold' and c.get('daysListed'): line += f' · {c["daysListed"]} days listed'
    if c.get('foundDate') == REF: line += f' · NEW {d_short(REF)}'
    qs = quoted_selling(c)
    if kind == 'sold': price = 'was ' + money(p['listed']) + (f' {p["listedNote"]}' if p.get('listedNote') and 'transfer' in p['listedNote'] else '')
    elif qs: price = f'{money(qs, True)} quoted (listed {price_listed_display(c)})'
    else: price = price_listed_display(c)
    if kind == 'sold':
        status = c['soldInfo'].get('statusLine') or ('Sold — ' + c['soldInfo']['how'])
    else:
        t = tpl(c['latest']['text'], c); status = t[0].upper() + t[1:]
        if kind == 'nohaggle': status = 'Reference car · fixed price, no transfer fee — nothing to request; visit or hold online. ' + status
    note = tpl((c.get('map') or {}).get('note'), c) or None
    listing = c['links'].get('others', {}).get(c['links'].get('mapListing') or '') or c['links']['primary']
    return {'rank': c['rank'], 'line': line, 'price': price, 'listing': listing, 'kind': kind, 'status': status, 'note': note}

def build_map():
    LEAFLET_CSS = open(os.path.join(ASSETS, 'leaflet-1.9.4.css'), encoding='utf-8').read()
    LEAFLET_JS = open(os.path.join(ASSETS, 'leaflet-1.9.4.js'), encoding='utf-8').read()
    if 'sourceMappingURL' in LEAFLET_JS: LEAFLET_JS = LEAFLET_JS.rsplit('//# sourceMappingURL', 1)[0].rstrip()
    dealers = []
    unmapped = []
    for k, d in DEALERS.items():
        cs = [map_car(c) for c in CARS if c['dealerKey'] == k]
        if not cs: continue
        entry = {'id': k, 'name': d['mapName'], 'city': d['city'], 'region': d.get('region'), 'website': d.get('website') or cs[0]['listing'], 'cars': cs,
                 'nohaggle': d['type'] == 'nohaggle', 'addr_note': d.get('note') if 'Pin is' in (d.get('note') or '') else None}
        if d.get('lat') is None:
            entry['why_unmapped'] = d.get('note') or 'not mapped'; unmapped.append(entry); continue
        entry.update(lat=d['lat'], lon=d['lon'], address=d['address'], addr_from_osm=bool(d.get('addressSource') and 'OpenStreetMap POI' in d['addressSource']))
        entry['dist'] = haversine_mi(HOME, (d['lat'], d['lon']))
        entry['directions'] = 'https://www.google.com/maps/dir/?api=1&destination=' + urllib.parse.quote(d['address'])
        kinds = {c['kind'] for c in cs}
        entry['bucket'] = ('nohaggle' if entry['nohaggle'] and kinds - {'sold'} else 'contacted' if kinds & {'quote', 'contacted'} else 'todo' if kinds & {'todo', 'foldin'} else 'sold')
        entry['live'] = entry['bucket'] != 'sold'
        dealers.append(entry)
    BY_ID = {d['id']: d for d in dealers}
    ranks = lambda d: ', '.join(f"#{c['rank']}" for c in d['cars'] if c['kind'] != 'sold') or ', '.join(f"#{c['rank']}" for c in d['cars'])
    gmaps_route = lambda addrs: 'https://www.google.com/maps/dir/' + '/'.join(urllib.parse.quote(p, safe='') for p in ['Seattle, WA ' + META['homeZip']] + addrs)

    def car_line_html(c, compact):
        price = f'<strong>{esc(c["price"])}</strong>' if c['kind'] != 'sold' else f'<span class="was">{esc(c["price"])}</span>'
        note = f' <span class="pn">({esc(c["note"])})</span>' if c.get('note') else ''
        wrap_cls = ('pcar' if compact else 'car') + (' soldcar' if c['kind'] == 'sold' else '')
        return (f'<div class="{wrap_cls}"><span class="{"rank" if compact else "rank sm"}">#{c["rank"]}</span> {esc(c["line"])} · {price}{note}'
                f' · <a href="{esc(c["listing"])}" target="_blank" rel="noopener">Listing</a><div class="cstat {CAR_CLS[c["kind"]]}">{esc(c["status"])}</div></div>')

    def popup_html(d):
        b = PIN[d['bucket']]; first_live = next((c for c in d['cars'] if c['kind'] != 'sold'), d['cars'][0])
        return (f'<div class="pop"><div class="pname">{esc(d["name"])} <span class="pcity">· {esc(d["city"])} · {d["dist"]:.0f} mi</span></div><div class="paddr">{esc(d["address"])}</div>'
                + ''.join(car_line_html(c, True) for c in d['cars']) + f'<div class="pstat {b["cls"]}">{esc(b["label"])}</div><div class="plinks">'
                f'<a class="btn" href="{esc(d["directions"])}" target="_blank" rel="noopener">Directions</a><a class="btn ghost" href="{esc(first_live["listing"])}" target="_blank" rel="noopener">Listing</a></div></div>')

    js_dealers = [{'lat': d['lat'], 'lon': d['lon'], 'name': f'{d["name"]} ({ranks(d)})', 'color': PIN[d['bucket']]['color'], 'sold': d['bucket'] == 'sold', 'popup': popup_html(d)}
                  for d in sorted(dealers, key=lambda x: x['bucket'] != 'sold')]

    def card_html(d, mapped=True):
        b = PIN[d['bucket']] if mapped else PIN['sold']
        cars = ''.join(car_line_html(c, False) for c in d['cars'])
        addr_bits = []
        if mapped:
            addr_bits.append(esc(d['address']))
            if d.get('addr_from_osm'): addr_bits.append('<span class="approx">address per OpenStreetMap — confirm before driving</span>')
            if d.get('addr_note'): addr_bits.append(f'<span class="approx">{esc(d["addr_note"])}</span>')
        else:
            addr_bits.append(esc(d['city']) + ' — ' + esc(d['why_unmapped']))
        links = []
        if mapped: links.append(f'<a href="{esc(d["directions"])}" target="_blank" rel="noopener">Directions</a>')
        first_live = next((c for c in d['cars'] if c['kind'] != 'sold'), d['cars'][0])
        links.append(f'<a href="{esc(first_live["listing"])}" target="_blank" rel="noopener">Listing</a>')
        if d.get('website') and d['website'] != first_live['listing']: links.append(f'<a href="{esc(d["website"])}" target="_blank" rel="noopener">Website</a>')
        dist = f'{d["dist"]:.0f} mi' if mapped else '—'
        return f'''      <div class="dcard{' is-sold' if b is PIN['sold'] else ''}" id="d-{esc(d['id'])}">
        <div class="dc-head">
          <span class="dist">{dist}</span>
          <span class="dname">{esc(d["name"])} <span class="dcity">· {esc(d["city"])}</span></span>
          <span class="badge {b["cls"]}">{esc(b["label"])}</span>
        </div>
        <div class="dc-cars">{cars}</div>
        <div class="dc-addr muted small">{' · '.join(addr_bits)}</div>
        <div class="dc-links">
          {' '.join(links)}
        </div>
      </div>'''

    live_sorted = sorted([d for d in dealers if d['live']], key=lambda x: x['dist'])
    sold_sorted = sorted([d for d in dealers if not d['live']], key=lambda x: x['dist'])
    cards_live = '\n'.join(card_html(d) for d in live_sorted)
    cards_sold = '\n'.join(card_html(d) for d in sold_sorted) + '\n' + '\n'.join(card_html(d, mapped=False) for d in unmapped)
    n_live_dealers = len(live_sorted)
    n_live_cars = sum(1 for d in dealers for c in d['cars'] if c['kind'] != 'sold')
    n_sold_cars = sum(1 for d in dealers + unmapped for c in d['cars'] if c['kind'] == 'sold')

    clusters = ''
    for cd in B['routes']:
        stops = [BY_ID[s] for s in cd['order'] if s in BY_ID and BY_ID[s]['live']]
        if not stops: continue
        stops_line = ' → '.join(f'{esc(s["name"])} <span class="muted">({ranks(s)} · {s["dist"]:.0f} mi)</span>' for s in stops)
        clusters += f'''      <div class="cluster">
        <h3>{esc(cd["title"])}</h3>
        <p class="small stops">{stops_line}</p>
        <p>{esc(cd["worth"])}</p>
        <a class="btn ghost" href="{esc(gmaps_route([s["address"] for s in stops]))}" target="_blank" rel="noopener">Open route in Google Maps</a>
      </div>
'''
    legend_items = ''.join(f'<span class="lg"><span class="lgdot" style="background:{v["color"]}"></span>{esc(v["label"])}</span>' for v in PIN.values())
    PAGE_CSS = open(os.path.join(ASSETS, 'map.css'), encoding='utf-8').read()
    MAP_JS = '''
(function() {
  var dealers = %s;
  var map = L.map('map', { scrollWheelZoom: false, tap: true });
  L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 18,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
  }).addTo(map);
  var pts = [];
  dealers.forEach(function(d) {
    var sz = d.sold ? 16 : 22;
    var icon = L.divIcon({
      className: '', iconSize: [sz, sz], iconAnchor: [sz / 2, sz], popupAnchor: [0, -sz + 2],
      html: '<div class="pin' + (d.sold ? ' sold' : '') + '" style="background:' + d.color + '"></div>'
    });
    var m = L.marker([d.lat, d.lon], { icon: icon, title: d.name, zIndexOffset: d.sold ? -1000 : 0 }).addTo(map);
    m.bindPopup(d.popup, { maxWidth: 310, minWidth: 230 });
    pts.push([d.lat, d.lon]);
  });
  map.fitBounds(pts, { padding: [30, 30] });
})();
''' % json.dumps(js_dealers)
    as_of = f'Status as of {d_long(REF)} (listing sweep; dealer replies logged through {META["commsThrough"]})'
    max_rank = max(c['rank'] for c in CARS)
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>CX-5 dealerships — test-drive map</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<meta name="format-detection" content="telephone=no">
<meta name="color-scheme" content="light">
<meta name="generator" content="tools/build_site.py from data/board.json (refreshed {REF})">
<style>
/* Leaflet 1.9.4 (inlined; sha256 verified: p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=) */
{LEAFLET_CSS}
</style>
<style>{PAGE_CSS}</style>
</head>
<body>
<header class="wrap masthead">
  <div class="toplinks">
    <a class="back" href="./">&larr; Back to the report</a>
    <span class="sibs"><a href="./ask.html">Ask</a><a href="./status.html">Status board</a><a href="./trims.html">Trim guide</a></span>
  </div>
  <h1>CX-5 dealerships — test-drive map</h1>
  <p class="asof">{as_of} · board #1–#{max_rank} · {n_live_cars} live cars at {n_live_dealers} dealers, {n_sold_cars} sold · distances are straight-line from Seattle {META["homeZip"]}</p>
</header>
<main class="wrap">
  <section class="card">
    <div id="map" role="region" aria-label="Map of shortlist dealerships"></div>
    <noscript><span class="nsnote">The interactive map needs JavaScript. The dealer list below works without it.</span></noscript>
    <div class="legend">{legend_items}</div>
    <p class="mapnote">Pin colour is per dealer: green if any car there has an inquiry out, amber if a live car there has not been contacted, blue for no-haggle, grey (small) where everything is sold. Map tiles © OpenStreetMap contributors; needs an internet connection for the map background.</p>
  </section>

  <section class="card" id="list">
    <h2>Dealers by distance</h2>
    <p class="summary">{esc(B["prose"]["mapSummary"])}</p>
    <div class="dcards">
{cards_live}
    </div>
    <p class="subhead">Sold or off the map</p>
    <div class="dcards">
{cards_sold}
    </div>
  </section>

  <section class="card" id="routes">
    <h2>Saturday route groupings</h2>
    <p class="muted small">Live dealers only (sold lots dropped). Distances are straight-line from {META["homeZip"]}; drive-time notes are rough, no live traffic. Each Google Maps link starts from Seattle {META["homeZip"]} and chains the stops in the order shown.</p>
    <div class="clusters">
{clusters}    </div>
  </section>
</main>
<script>
/* Leaflet 1.9.4 (inlined; sha256 verified: 20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=) */
{LEAFLET_JS}
</script>
<script>{MAP_JS}</script>
</body>
</html>
'''

# ----------------------------------------------------------------------------- trims.html (static guide + generated candidates table)
def build_trims():
    t = open(os.path.join(TOOLS, 'templates', 'trims.html'), encoding='utf-8').read()
    tier_order = {'Full comfort': 0, 'Comfort': 1, 'The look': 2, 'Everyday': 3}
    rows = ''
    for c in sorted([c for c in IN_PLAY if c.get('guide')], key=lambda c: (tier_order.get(c['guide']['tier'], 9), c['price']['listed'])):
        d = c['dealer']; g = c['guide']
        where = (' / '.join(f'<a href="{esc(s["url"])}">{esc(s["name"])}</a>' for s in d['sites']) if d.get('sites') and d['type'] != 'independent' else esc(d['name'])) + ' · ' + esc(d['city'].replace(',', ''))
        flags = []
        if c['history'].get('cpo'): flags.append('CPO')
        if c.get('foundDate') != PUB: flags.append('new find ' + d_short(c['foundDate']))
        if not clean_history(c): flags.append('accident on Carfax')
        rows += (f'      <tr><td><a href="{esc(c["links"]["primary"])}">{yr_chip(c)} {esc(c["trim"])}</a> <span class="note">#{c["rank"]}</span><br><span class="note">{where}{(" · " + esc(", ".join(flags))) if flags else ""}</span></td>'
                 f'<td class="tier">{esc(g["tier"])}</td><td>{esc(c["engine"])}</td><td>{esc(g["highlights"])}</td><td class="num">{round(c["miles"] / 1000)}k</td><td class="num">{esc(price_listed_display(c))}</td></tr>\n')
    gone = [c for c in SOLD if c.get('ventilatedSeats') or c['trimKey'] in ('GT Reserve (turbo)',)]
    for c in gone:
        d = c['dealer']
        rows += (f'      <tr class="sold"><td><s><a href="{esc(c["links"]["primary"])}">{yr_chip(c)} {esc(c["trim"])}</a></s> · sold {d_short(c["soldInfo"]["date"])}<br><span class="note">{esc(d["name"])} · {esc(d["city"].replace(",", ""))}</span></td>'
                 f'<td class="tier">—</td><td>{esc(c["engine"])}</td><td>Removed from the board</td><td class="num">{round(c["miles"] / 1000)}k</td><td class="num"><s>{money(c["price"]["listed"])}</s></td></tr>\n')
    note = f'<p class="note">{esc(B["prose"]["guideReading"]).replace("status board", "<a href=" + chr(34) + "status.html" + chr(34) + ">status board</a>").replace("main report", "<a href=" + chr(34) + "index.html" + chr(34) + ">main report</a>")} Live cars as of the {d_short(REF)} refresh, grouped by tier; prices are listed asking prices.</p>'
    return t.replace('<!--CANDIDATE_ROWS-->\n', rows).replace('<!--CANDIDATE_NOTE-->', note)

# ----------------------------------------------------------------------------- ask.html (submit-a-listing inbox; data/inbox.json via tools/inbox.py)
# Everything in an inbox item is untrusted text (it arrives through a public form): every field goes through esc(),
# links render only when they are http(s), and the page carries no script at all.
VERDICT_BADGE = {'pursue': ('Pursue', 'vd-pursue'), 'benchmark': ('Benchmark', 'vd-benchmark'), 'skip': ('Skip', 'vd-skip'),
                 'not a CX-5': ('Not a CX-5', 'vd-notcx5'), "couldn't load": ("Couldn't load", 'vd-couldntload')}

def t_disp(s, with_time=True):
    """'2026-08-12T09:14:05' → 'Aug 12, 9:14 AM'; '2026-08-12' → 'Aug 12'; anything else is echoed escaped."""
    s = str(s or '').strip()
    if not s: return ''
    try:
        if 'T' in s or ' ' in s:
            dt = datetime.datetime.fromisoformat(s.replace(' ', 'T')[:19])
            out = dt.strftime('%b ') + str(dt.day)
            if with_time: out += ', ' + (dt.strftime('%I:%M %p').lstrip('0'))
            if dt.year != d_iso(REF).year: out += f', {dt.year}'
            return out
        d = datetime.date.fromisoformat(s[:10])
        return d.strftime('%b ') + str(d.day) + (f', {d.year}' if d.year != d_iso(REF).year else '')
    except ValueError:
        return esc(s[:40])

def safe_href(u):
    u = str(u or '').strip()
    return u if urllib.parse.urlsplit(u).scheme in ('http', 'https') and not re.search(r'[\s<>"\']', u) else None

def host_of(u):
    h = urllib.parse.urlsplit(str(u or '')).hostname or ''
    return h[4:] if h.startswith('www.') else h

def city_rate(city, state):
    if (state or 'WA') != 'WA': return META['useTaxRateOR']
    key = f'{(city or "").split(",")[0].strip()}, WA'
    return B['taxRatesByCity'].get(key) or META['defaultTaxRate']

def inbox_numbers(it):
    """Public rule: the Ask page shows estimates only (price × (1 + dealer-city rate) + doc + licence), never a dealer-quoted OTD."""
    L = it.get('listing') or {}; n = dict(it.get('numbers') or {})
    price = L.get('price')
    if price:
        rate = n.get('taxRate') or city_rate(L.get('city'), L.get('state'))
        doc = L.get('docFee') if L.get('docFee') is not None else (META['docFeeWA'] if (L.get('state') or 'WA') == 'WA' else META['docFeeOR'])
        est = est_otd(price, rate, doc)
        n.setdefault('taxRate', rate); n.setdefault('estOtd', est)
        n.setdefault('monthly0', pmt(n['estOtd'])); n.setdefault('monthly5k', pmt(max(0, n['estOtd'] - 5000)))
        n.setdefault('basis', f'est. at {rate:.2f}% + ${doc:,.0f} doc + ${META["licenseEst"]:,} licence')
    return n

def judge_rules():
    yrs = re.search(r'(20\d\d)\D+(20\d\d)', META['title'])
    span = f'{yrs.group(1)}–{yrs.group(2)}' if yrs else '2021–2023'
    return [
        ('Right car, right trim', f'{span} Mazda CX-5 (a 2024 gets a look if the price is right). Comfort trims first: Premium / Premium Plus, Grand Touring with the Premium Package, Carbon Edition, Turbo, Signature. Base trims (Sport, Select, plain 2.5 S) only count if they are more than $3,000 under the going rate.'),
        ('Under 50,000 miles', 'and ideally one owner. Higher-mile cars can still be useful as a price benchmark, but they do not go on the board.'),
        ('Clean history', 'no reported accidents, no rental / fleet past, no lemon or frame-damage flags, a real VIN and at least a handful of real photos. Mazda Certified Pre-Owned is a plus, not a must.'),
        ('Priced at or under market', 'we check the asking price against KBB Fair Purchase Price and the CarGurus market value for that exact car, look at how long it has been listed and whether the price has been cut, and compare it with the cars already on the board.'),
        ('What it really costs', f'estimated out-the-door = price × (1 + the dealer city’s sales-tax rate, {min(B["taxRatesByCity"].values()):.1f}–{max(B["taxRatesByCity"].values()):.1f}% around here) + ${META["docFeeWA"]} doc fee + ${META["licenseEst"]} licence, then a monthly payment at {APR:.2f}% APR over {N} months (about ${PER1K:.2f} per $1,000 financed) at $0 and $5,000 down. Dealer-quoted figures never appear on this page.'),
    ]

def flag_cls(f):
    m = re.match(r'\s*(RED|YELLOW|AMBER|GREEN)\b', str(f), re.I)
    return {'red': 'f-red', 'yellow': 'f-yellow', 'amber': 'f-yellow', 'green': 'f-green'}.get(m.group(1).lower(), '') if m else ''

def inbox_card(it):
    st = it.get('status') or 'queued'
    L = it.get('listing') or {}; V = it.get('verdict') or {}; n = inbox_numbers(it)
    sid = esc(str(it.get('id') or '')[:8])
    src = safe_href(it.get('url'))
    sub_bits = ['submitted ' + t_disp(it.get('submittedAt'))] if it.get('submittedAt') else ['submitted']
    if it.get('submitter'): sub_bits.append('by ' + esc(it['submitter']))
    foot = ' '.join(sub_bits) + (f' · <q>{esc(it["submittedNote"])}</q>' if it.get('submittedNote') else '')
    url_line = f'<p class="ib-url">{ext(src, esc(it["url"])) if src else esc(it.get("url"))}</p>'
    if st in ('queued', 'analyzing'):
        lab, cls = ('Queued', 'vd-queued') if st == 'queued' else ('Analyzing', 'vd-analyzing')
        line = 'In line — ' + sub_bits[0] if st == 'queued' else 'Being checked now — ' + sub_bits[0]
        return f'''    <article class="ib is-{st}" id="a-{sid}">
      <header class="ib-head">{badge(lab, "vd " + cls)}<span class="muted small">{esc(host_of(it.get("url")))}</span></header>
      <p class="ib-one">{line}{(" by " + esc(it["submitter"])) if it.get("submitter") else ""}.</p>
      {url_line}
      {f'<footer class="ib-foot"><q>{esc(it["submittedNote"])}</q></footer>' if it.get("submittedNote") else ""}
    </article>'''
    label = V.get('label') or ("couldn't load" if st == 'error' else 'skip')
    lab, cls = VERDICT_BADGE.get(label, (label.title(), 'vd-skip'))
    if st == 'error' and label != "couldn't load": lab, cls = "Couldn't load", 'vd-error'
    # title: year make model trim · dealer · city
    car = ' '.join(str(x) for x in [L.get('year'), L.get('make'), L.get('model'), L.get('trim')] if x)
    where = ' · '.join(esc(x) for x in [L.get('dealer'), ', '.join(y for y in [L.get('city'), L.get('state')] if y)] if x)
    title = (esc(car) or esc(host_of(it.get('url')))) + (f'<span class="sub"><span class="sep"> · </span>{where}</span>' if where else '')
    facts = []
    if L.get('price') is not None: facts.append(f'<span class="p">{money(L["price"])}</span>' + (f' <span class="muted small">+ ${L["docFee"]:,.0f} doc</span>' if L.get('docFee') else ''))
    if L.get('miles') is not None: facts.append(f'<span>{num(L["miles"])} mi</span>')
    if n.get('estOtd'): facts.append(f'<span>est. OTD <strong>{money(n["estOtd"])}</strong></span>')
    if n.get('monthly0'): facts.append(f'<span class="mo"><strong>{money(n["monthly0"])}</strong>/mo <span class="muted small">$0 down · {money(n.get("monthly5k"))}/mo with $5k down</span></span>')
    body = []
    if V.get('bullets'): body.append('<div><h4>Why</h4><ul>' + ''.join(f'<li>{esc(b)}</li>' for b in V['bullets']) + '</ul></div>')
    if V.get('flags'): body.append('<div><h4>Flags</h4><ul class="ib-flags">' + ''.join(f'<li class="{flag_cls(f)}">{esc(f)}</li>' for f in V['flags']) + '</ul></div>')
    if V.get('openingMove'): body.append(f'<div><h4>Opening move</h4><p>{esc(V["openingMove"])}' + (f' <span class="muted">(target OTD {money(V["targetOtd"])})</span>' if V.get('targetOtd') else '') + '</p></div>')
    if V.get('slot'): body.append(f'<div><h4>Where it would slot vs. the board</h4><p>{esc(V["slot"])}</p></div>')
    dl = []
    if L.get('vin'): dl.append(('VIN · stock', esc(L['vin']) + (f' · {esc(L["stock"])}' if L.get('stock') else '')))
    if L.get('daysListed') is not None: dl.append(('Days listed', f'{L["daysListed"]} as of {t_disp(it.get("analyzedAt"), False)}'))
    ph = [p for p in (L.get('priceHistory') or []) if p and p.get('price')]
    if ph: dl.append(('Price history', ' → '.join((t_disp(p.get('date'), False) + ' ' if p.get('date') else '') + money(p['price']) + (f' <span class="muted small">({esc(p["note"])})</span>' if p.get('note') else '') for p in ph)))
    h = L.get('history') or {}
    if h:
        hb = []
        if h.get('owners'): hb.append(f'{h["owners"]} owner' + ('s' if h['owners'] != 1 else ''))
        if h.get('accidents') is not None: hb.append(f'{h["accidents"]} accident' + ('s' if h['accidents'] != 1 else ''))
        if h.get('rental') not in (None, False, ''): hb.append('rental / fleet: ' + ('yes' if h['rental'] is True else esc(h['rental'])))
        elif h.get('rental') is False: hb.append('no rental / fleet flag')
        if h.get('cpo') not in (None, False, ''): hb.append('CPO' if h['cpo'] is True else esc(h['cpo']))
        if L.get('photos'): hb.append(f'{L["photos"]} photos')
        dl.append(('History', ' · '.join(hb) or 'unverified'))
    dd = L.get('deal') or {}
    if dd:
        db = []
        if dd.get('cgRating'): db.append(f'CarGurus {esc(dd["cgRating"])}' + (f' ({money(abs(dd["cgDelta"]))} {"under" if dd["cgDelta"] < 0 else "over"} their market value)' if dd.get('cgDelta') else ''))
        if dd.get('kbbFpp'): db.append(f'KBB fair purchase price {money(dd["kbbFpp"])}' + (f' → asking is {money(abs(dd["kbbDelta"]))} {"under" if dd["kbbDelta"] < 0 else "over"}' if dd.get('kbbDelta') else ''))
        if db: dl.append(('Market check', ' · '.join(db)))
    if n.get('estOtd'): dl.append(('OTD basis', esc(n.get('basis') or 'estimate')))
    if dl: body.append('<div><h4>Listing facts</h4><dl class="ib-dl">' + ''.join(f'<dt>{k}</dt><dd>{v}</dd>' for k, v in dl) + '</dl></div>')
    links = L.get('links') or {}
    lk = [(safe_href(links.get('source')) or src, 'Source listing'), (safe_href(links.get('cargurus')), 'CarGurus'), (safe_href(links.get('kbb')), 'KBB')]
    lk = [(u, t) for u, t in lk if u]
    if lk: body.append('<div class="ib-links">' + ''.join(ext(u, t, 'btn ghost') for u, t in lk) + '</div>')
    err = f'<p class="ib-one bad-t">{esc(it["error"])}</p>' if it.get('error') else ''
    details = f'<details class="ib-more"><summary>Details: why, flags, opening move, links</summary><div class="ib-body">{"".join(body)}</div></details>' if body else ''
    return f'''    <article class="ib is-{re.sub(r"[^a-z0-9]", "", label)}" id="a-{sid}">
      <header class="ib-head">{badge(lab, "vd " + cls)}<span class="when">checked {t_disp(it.get("analyzedAt"), False)}</span></header>
      <h3 class="ib-title">{title}</h3>
      {f'<p class="ib-facts">{" ".join(facts)}</p>' if facts else url_line}
      {f'<p class="ib-one">{esc(V["oneLine"])}</p>' if V.get("oneLine") else ""}{err}
      {details}
      <footer class="ib-foot">{foot}</footer>
    </article>'''

def build_ask():
    css = open(os.path.join(ASSETS, 'report.css'), encoding='utf-8').read() + '\n' + open(os.path.join(ASSETS, 'ask.css'), encoding='utf-8').read()
    cfg = INBOX.get('config') or {}
    items = sorted(INBOX.get('items') or [], key=lambda it: (str(it.get('analyzedAt') or it.get('submittedAt') or ''), str(it.get('submittedAt') or '')), reverse=True)
    n_done = sum(1 for it in items if it.get('status') in ('done', 'error')); n_wait = len(items) - n_done
    form = safe_href(cfg.get('formUrl'))
    if form:
        cta = f'''<div class="ask-cta">
    {ext(form, 'Paste a link <span class="sub">(opens a 10-second form)</span>', 'btn')}
    <p class="eta">Results appear below within about an hour (sooner if {esc(META.get("buyerFirstName") or "someone")} pokes it). New links are {esc(cfg.get("pollNote") or "checked hourly")}.</p>
  </div>'''
    else:
        cta = '<p class="notconn">Submission form not connected yet. Once it is, a button here opens a 10-second form: paste the link, add a note if you like, done.</p>'
    rules = ''.join(f'<li><strong>{esc(a)}:</strong> {esc(b)}</li>' for a, b in judge_rules())
    legend = ' '.join(badge(l, 'vd ' + c) for l, c in [('Pursue', 'vd-pursue'), ('Benchmark', 'vd-benchmark'), ('Skip', 'vd-skip'), ('Not a CX-5', 'vd-notcx5'), ("Couldn't load", 'vd-couldntload'), ('Queued', 'vd-queued')])
    cards = '\n'.join(inbox_card(it) for it in items) if items else '<p class="empty">Nothing submitted yet.</p>'
    body = f'''<nav class="topnav" aria-label="Sections"><div class="wrap navwrap">
  <a class="brand" href="index.html">CX-5 Buyer's Report</a>
  <div class="navlinks">{''.join(f'<a href="{h}"{" class=" + chr(34) + "active" + chr(34) + " aria-current=" + chr(34) + "page" + chr(34) if h == "ask.html" else ""}><span>{esc(l)}</span></a>' for h, l in PAGES)}</div>
</div></nav>

<header class="masthead ask-mast wrap" id="top">
  <p class="eyebrow">CX-5 search · Seattle · send a link</p>
  <h1>Send us a listing to check</h1>
  <p class="scope">Seen a CX-5 for sale somewhere: a dealer page, CarGurus, Autotrader, KBB, Craigslist, a Facebook post? Paste the link and we run it through the same checks as the <a href="index.html">report</a>: right trim, miles, history, price against the market, and what it would really cost per month. The answer lands on this page.</p>
  {cta}
</header>

<main class="wrap">

<section class="card" id="how">
  <div class="sec-head"><h2>How we judge a listing</h2><p class="muted">Same rules as the numbered board, so every answer below reads the same way.</p></div>
  <ul class="judge">{rules}</ul>
  <p class="legend-v"><span>Verdicts:</span> {legend} <span>· “benchmark” means useful as a price reference but not one to chase.</span></p>
</section>

<section class="card" id="analyses">
  <div class="sec-head"><h2>Analyses</h2><p class="muted">Newest first · {n_done} checked{f", {n_wait} in line" if n_wait else ""} · figures as of the day each was checked; listings change daily.</p></div>
  <div class="inbox-list">
{cards}
  </div>
</section>

</main>

<footer class="wrap footer"><p>Read-only research: nobody here contacts a seller on your behalf from this page, and nothing is affiliated with any dealer or listing site. Prices, availability and history badges are as found on the day checked; verify the history report, the out-the-door sheet and the car itself before buying. Board changes stay manual: a “pursue” here does not add a car to the <a href="status.html">status board</a> by itself.</p></footer>
'''
    doc = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
{FAVICON}
<title>Ask: send a CX-5 listing to check</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<meta name="format-detection" content="telephone=no">
<meta name="color-scheme" content="light">
<meta name="generator" content="tools/build_site.py from data/inbox.json + data/board.json (refreshed {REF})">
<style>{css}</style>
</head>
<body>
{body}</body>
</html>
'''
    return ascii_safe(doc)

# ----------------------------------------------------------------------------- downloads
def build_pdf(index_path, pdf_path):
    script = r'''
const cands = ['/opt/node-tools/node_modules/playwright', 'playwright'];
let chromium = null;
for (const c of cands) { try { chromium = require(c).chromium; break; } catch (e) {} }
if (!chromium) { console.log('NO_PLAYWRIGHT'); process.exit(2); }
(async () => {
  const browser = await chromium.launch({ headless: true, args: ['--no-proxy-server'] });
  const page = await (await browser.newContext({ viewport: { width: 1100, height: 900 } })).newPage();
  await page.route('**/*', r => r.request().url().startsWith('file:') ? r.continue() : r.abort());
  await page.goto('file://' + process.argv[1], { waitUntil: 'load' });
  await page.emulateMedia({ media: 'print' });
  await page.waitForTimeout(200);
  await page.pdf({ path: process.argv[2], format: 'Letter', printBackground: true, margin: { top: '0.5in', bottom: '0.5in', left: '0.45in', right: '0.45in' } });
  await browser.close();
  console.log('PDF_OK');
})().catch(e => { console.error(e); process.exit(1); });
'''
    try:
        out = subprocess.run(['node', '-e', script, index_path, pdf_path], capture_output=True, text=True, timeout=180)
    except FileNotFoundError:
        print('  ! node not found; PDF not rebuilt'); return False
    if 'PDF_OK' in out.stdout:
        return True
    if 'NO_PLAYWRIGHT' in out.stdout and _build_pdf_py(index_path, pdf_path):
        return True
    print('  ! PDF step failed:', (out.stdout + out.stderr).strip()[:400]); return False

def _build_pdf_py(index_path, pdf_path):
    # fallback for environments with python playwright + a preinstalled chromium but no node playwright
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return False
    import glob as _glob
    try:
        with sync_playwright() as pw:
            try:
                browser = pw.chromium.launch(headless=True, args=['--no-proxy-server'])
            except Exception:
                exes = _glob.glob('/opt/pw-browsers/chromium*/chrome-linux/chrome') or _glob.glob('/opt/pw-browsers/chromium')
                if not exes: return False
                browser = pw.chromium.launch(headless=True, executable_path=exes[0], args=['--no-proxy-server'])
            page = browser.new_context(viewport={'width': 1100, 'height': 900}).new_page()
            page.route('**/*', lambda r: r.continue_() if r.request.url.startswith('file:') else r.abort())
            page.goto('file://' + index_path, wait_until='load')
            page.emulate_media(media='print')
            page.wait_for_timeout(200)
            page.pdf(path=pdf_path, format='Letter', print_background=True, margin={'top': '0.5in', 'bottom': '0.5in', 'left': '0.45in', 'right': '0.45in'})
            browser.close()
        return True
    except Exception as e:
        print('  ! python PDF fallback failed:', str(e)[:200]); return False

def model_for_downloads():
    """Plain data handed to tools/downloads.py (xlsx + docx) so both derive from the same computed rows as the page.
    Site rule: the public downloads carry no dealer quote figures, counters, or gaps — quote objects are
    stripped from the copy handed over, and cost rows render on the estimate basis."""
    import copy as _copy
    bundle = _copy.deepcopy(dict(B=B, CARS=CARS, IN_PLAY=IN_PLAY, LIVE=LIVE, SOLD=SOLD, COST=COST, COST_SORTED=COST_SORTED, CHEAPEST=CHEAPEST, STRETCH=STRETCH, PICKS=PICKS))
    quoted_ranks = {c['rank'] for c in QUOTED}
    for c in bundle['CARS']:
        c['quote'] = None; c['counter'] = None
    for c in bundle['B'].get('cars', []):
        c['quote'] = None; c['counter'] = None
    for r in bundle['COST'].values():
        r['basis'] = 'est'; r['struck'] = None
    return dict(B=bundle['B'], META=META, CARS=bundle['CARS'], IN_PLAY=bundle['IN_PLAY'], LIVE=bundle['LIVE'], SOLD=bundle['SOLD'],
                QUOTED=[c for c in bundle['CARS'] if c['rank'] in quoted_ranks], COST=bundle['COST'], COST_SORTED=bundle['COST_SORTED'], CHEAPEST=bundle['CHEAPEST'], STRETCH=bundle['STRETCH'],
                PICKS=bundle['PICKS'], TRIMS=TRIMS, CALC=CALC, PER1K=PER1K, APR=APR, N=N, REF=REF, PUB=PUB, SOLID_RULE=SOLID_RULE, STRETCH_RULE=STRETCH_RULE,
                WATCH_GROUPS=[dict(g, items=[w for w in bundle['B']['watchlist'] if (w.get('group') or WATCH_GROUPS[0]['key']) == g['key']]) for g in WATCH_GROUPS],
                helpers=dict(money=money, signed=signed, num=num, d_short=d_short, d_long=d_long, tpl=tpl, tax_rate=tax_rate, doc_fee=doc_fee, hist_short=hist_short,
                             hist_words=hist_words, clean_history=clean_history, quoted_selling=quoted_selling, price_listed_display=price_listed_display, dist_mi=dist_mi, pmt=pmt))

# ----------------------------------------------------------------------------- main
def main():
    args = set(sys.argv[1:])
    outputs = {
        'index.html': build_index(),
        'status.html': build_status(),
        'map.html': build_map(),
        'trims.html': build_trims(),
        'ask.html': build_ask(),
    }
    for name, content in outputs.items():
        with open(os.path.join(ROOT, name), 'w', encoding='utf-8') as f: f.write(content)
        print(f'wrote {name} ({len(content):,} bytes)')
    sys.path.insert(0, TOOLS)
    import downloads
    m = model_for_downloads()
    downloads.build_xlsx(m, os.path.join(ROOT, 'CX5-Seattle-Buyers-Report.xlsx'))
    downloads.build_docx(m, os.path.join(ROOT, 'cx5_report.docx'))
    if '--no-pdf' not in args:
        if build_pdf(os.path.join(ROOT, 'index.html'), os.path.join(ROOT, 'CX5-Seattle-Buyers-Report.pdf')):
            print('wrote CX5-Seattle-Buyers-Report.pdf')
    # summary for the log
    print(f'\nrefreshed {REF}: {len(IN_PLAY)} in play ({len(LIVE)} live + {len(IN_PLAY) - len(LIVE)} benchmark), {len(SOLD)} sold, {len(QUOTED)} quotes ({len([c for c in QUOTED if c["quote"].get("otd")])} with figures)')
    print(f'cheapest solid: #{CHEAPEST["rank"]}  stretch: #{STRETCH["rank"]}  picks: {[c["rank"] for c in PICKS[:3]]}  calc: {CALC["mode"]} otd={CALC["otd"]:.2f}')
    print('cost table (by OTD):')
    for r in COST_SORTED:
        c = r['car']
        print(f'  #{c["rank"]:<3} {c["year"]} {c["trim"][:26]:26} {r["basis"]:6} price {r["price"]:>9,.0f}  OTD {r["otd"]:>9,.0f}  @0 {r["m0"]:>4,.0f}  @5k {r["m5"]:>4,.0f}  int {r["interest"]:>5,.0f}' + (f'  struck {r["struck"]:,.0f}' if r.get('struck') else ''))
    print('trims:')
    for t in TRIMS:
        print(f'  {t["year"]} {t["trim"]:22} low {money(t["low"]):>8} ({t["lowSrc"]}) n={t["n"]} delta {signed(t["delta"]) if t["delta"] is not None else "-"}')

if __name__ == '__main__':
    main()
