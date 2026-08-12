#!/usr/bin/env python3
"""Listing inbox: paste-a-link submissions in, analyses out (data/inbox.json → ask.html via build_site.py).

    python3 tools/inbox.py fetch [--csv-file PATH]     # pull new links from the response sheet (or a local CSV), queue them
    python3 tools/inbox.py list-queued                 # queued items as JSON (id + url)
    python3 tools/inbox.py start <id>                  # mark an item "analyzing" (optional)
    python3 tools/inbox.py record <id> analysis.json   # validate + attach an analysis, mark done / error
    python3 tools/inbox.py render [build args]         # regenerate the site (delegates to tools/build_site.py)

Everything that arrives through the sheet is untrusted text: URLs are reduced to http(s) links, notes are
tag-stripped and capped, names are cut to a first name, and build_site.py HTML-escapes every field again
at render time. See tools/README.md ("Ask page / listing inbox") for the hourly routine and its two-step
(read-only analyst → recorder) split.
"""
import argparse, csv, datetime, hashlib, html, io, json, os, re, ssl, subprocess, sys, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_INBOX = os.path.join(ROOT, 'data', 'inbox.json')
EMPTY = {'config': {'formUrl': None, 'sheetCsvUrl': None, 'pollNote': 'checked hourly'}, 'items': []}

NOTE_MAX, NAME_MAX, URL_MAX = 300, 30, 600
STATUSES = ('queued', 'analyzing', 'done', 'error')
VERDICTS = ('pursue', 'benchmark', 'skip', 'not a CX-5', "couldn't load")

# ----------------------------------------------------------------------------- io
def load(path):
    if not os.path.exists(path):
        return json.loads(json.dumps(EMPTY))
    with open(path, encoding='utf-8') as f:
        d = json.load(f)
    d.setdefault('config', {}); d.setdefault('items', [])
    for k, v in EMPTY['config'].items():
        d['config'].setdefault(k, v)
    return d

def save(path, d):
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(d, f, indent=2, ensure_ascii=False)
        f.write('\n')
    os.replace(tmp, path)

def now_iso():
    return datetime.datetime.now().replace(microsecond=0).isoformat()

# ----------------------------------------------------------------------------- text hygiene (sheet content is untrusted)
BLOCK_RE = re.compile(r'(?is)<(script|style)[^>]*>.*?</\1\s*>')
TAG_RE = re.compile(r'<[^>]*>')
CTRL_RE = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]')

def clean_text(s, cap):
    """Strip tags / control chars, unescape entities once, collapse whitespace, cap length."""
    if s is None: return None
    s = str(s)
    s = TAG_RE.sub('', BLOCK_RE.sub(' ', s))
    s = html.unescape(s)
    s = TAG_RE.sub('', BLOCK_RE.sub(' ', s))   # entities may have decoded into tags
    s = CTRL_RE.sub(' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    if len(s) > cap: s = s[:cap - 1].rstrip() + '…'
    return s or None

def first_name(s):
    s = clean_text(s, 80)
    if not s: return None
    tok = re.split(r'[\s,;/@]+', s)[0]
    tok = re.sub(r"[^A-Za-zÀ-ɏ'\-]", '', tok)
    return tok[:NAME_MAX].capitalize() if tok else None

# ----------------------------------------------------------------------------- URLs
URL_RE = re.compile(r'''(?i)\b((?:https?://|www\.)[^\s<>"'\]\[(){}]+)''')
TRACKING_EXACT = {
    'resultsetid', 'searchuuid', 'srpc', 'ourls', 'sourceid', 'sourcecontext', 'searchid', 'listingposition', 'position',
    'px8324', 'dnetworktype', 'gclid', 'gbraid', 'wbraid', 'fbclid', 'msclkid', 'dclid', 'yclid', 'igshid', 'mc_cid', 'mc_eid',
    '_ga', '_gl', '_hsenc', '_hsmi', 'ref', 'refsource', 'referrer', 'clickid', 'clicktype', 'aff', 'affid', 'campaign',
    'searchzip', 'distance', 'entityselectinghelper.selectedentity', 'sortdir', 'sorttype', 'inventorysearchwidgettype',
    'newsearchfromoverviewpage', 'nonshippablebaseline', 'trk', 'trkid', 'si', 'spm', 'sc_cid', 'cmp', 'cid', 'lnx_variation',
}
TRACKING_PREFIX = ('utm_', 'cgf', 'ga_', 'pk_', 'hsa_', 'mkt_', 'icid', 'int_')
TRAIL_PUNCT = '.,;:!?)]}>\'"'

def extract_urls(text):
    """Every http(s) URL in a cell (people paste sentences around links); www.* gets https://; other schemes dropped."""
    out = []
    for m in URL_RE.finditer(str(text or '')):
        u = m.group(1).rstrip(TRAIL_PUNCT)
        if u.lower().startswith('www.'): u = 'https://' + u
        out.append(u)
    return out

def normalize_url(u):
    """Lower-case scheme/host, drop tracking params + non-listing fragments, keep ids. Returns None if not http(s)."""
    u = (u or '').strip()
    if len(u) > 4 * URL_MAX: return None
    try:
        p = urllib.parse.urlsplit(u)
    except ValueError:
        return None
    scheme = (p.scheme or '').lower()
    if scheme not in ('http', 'https'): return None
    host = (p.hostname or '').lower()
    if not host or '.' not in host: return None
    if re.search(r'[^a-z0-9.\-]', host): return None
    netloc = host + (f':{p.port}' if p.port and p.port not in (80, 443) else '')
    q = [(k, v) for k, v in urllib.parse.parse_qsl(p.query, keep_blank_values=False)
         if k.lower() not in TRACKING_EXACT and not k.lower().startswith(TRACKING_PREFIX)]
    frag = ''
    m = re.search(r'listing[=/](\d{6,12})', p.fragment or '')
    if m: frag = 'listing=' + m.group(1)          # CarGurus carries the listing id in the hash
    path = re.sub(r'/{2,}', '/', p.path or '/') or '/'
    out = urllib.parse.urlunsplit((scheme, netloc, urllib.parse.quote(path, safe="/+-_.~!$&'()*,;=:@%"), urllib.parse.urlencode(q), frag))
    return out if len(out) <= URL_MAX else None

def item_id(norm_url):
    return hashlib.sha1(norm_url.encode('utf-8')).hexdigest()

# ----------------------------------------------------------------------------- sheet fetch
def sheet_export_url(u):
    """Accept the CSV export URL as-is, or derive it from a docs.google.com .../edit[#?]gid=N link."""
    if not u: return None
    if 'export?format=csv' in u or 'output=csv' in u or not u.startswith('https://docs.google.com/spreadsheets/'): return u
    m = re.search(r'/spreadsheets/d/([A-Za-z0-9_\-]+)', u)
    if not m: return u
    g = re.search(r'[#?&]gid=(\d+)', u)
    return f'https://docs.google.com/spreadsheets/d/{m.group(1)}/export?format=csv' + (f'&gid={g.group(1)}' if g else '')

def http_get(url, timeout=40):
    ctx = ssl.create_default_context()
    for env in ('SSL_CERT_FILE', 'REQUESTS_CA_BUNDLE', 'CURL_CA_BUNDLE'):
        cafile = os.environ.get(env)
        if cafile and os.path.exists(cafile):
            try: ctx.load_verify_locations(cafile=cafile)
            except (ssl.SSLError, OSError): pass
    opener = urllib.request.build_opener(urllib.request.ProxyHandler(), urllib.request.HTTPSHandler(context=ctx))
    req = urllib.request.Request(url, headers={'User-Agent': 'cx5-inbox/1.0 (+read-only csv poll)', 'Accept': 'text/csv,*/*;q=0.5'})
    with opener.open(req, timeout=timeout) as r:
        raw = r.read(2_000_000 + 1)
        if len(raw) > 2_000_000: raise RuntimeError('sheet export larger than 2 MB; refusing')
        ctype = r.headers.get('Content-Type', '')
    text = raw.decode('utf-8-sig', errors='replace')
    if 'html' in ctype.lower() and '<html' in text[:2000].lower():
        raise RuntimeError('got an HTML page instead of CSV: is the sheet shared as "Anyone with the link: Viewer"?')
    return text

HEADER_KEYS = {
    'timestamp': ('timestamp', 'submitted', 'time', 'date'),
    'link': ('link', 'url', 'listing', 'paste'),
    'note': ('know', 'note', 'comment', 'anything', 'detail', 'message'),
    'name': ('name', 'who are you', 'your name'),
}

def map_headers(headers):
    cols = {}
    low = [str(h or '').strip().lower() for h in headers]
    for key, words in HEADER_KEYS.items():
        for i, h in enumerate(low):
            if i in cols.values(): continue
            if any(w in h for w in words):
                cols[key] = i; break
    return cols

TS_FORMATS = ('%m/%d/%Y %H:%M:%S', '%m/%d/%Y %H:%M', '%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M', '%d/%m/%Y %H:%M:%S', '%Y-%m-%d', '%m/%d/%Y')

def parse_ts(s):
    s = (s or '').strip()
    for f in TS_FORMATS:
        try: dt = datetime.datetime.strptime(s, f).replace(microsecond=0)
        except ValueError: continue
        return dt.isoformat() if '%H' in f else dt.date().isoformat()
    return None

def parse_rows(text):
    rows = list(csv.reader(io.StringIO(text)))
    if not rows: return []
    cols = map_headers(rows[0])
    body = rows[1:] if cols else rows          # no recognisable header → treat every row as data, scan all cells
    out = []
    for r in body:
        if not any((c or '').strip() for c in r): continue
        cell = lambda k: (r[cols[k]] if k in cols and cols[k] < len(r) else '')
        link_cells = [cell('link')] if 'link' in cols else list(r)
        urls = []
        for c in link_cells: urls += extract_urls(c)
        if not urls and 'link' in cols:            # link typed into the wrong box
            for c in r: urls += extract_urls(c)
        out.append({'urls': urls, 'ts': parse_ts(cell('timestamp')) or clean_text(cell('timestamp'), 40),
                    'note': clean_text(cell('note'), NOTE_MAX), 'name': first_name(cell('name')), 'rawLink': clean_text(cell('link'), 120)})
    return out

def cmd_fetch(a):
    d = load(a.inbox)
    if a.csv_file:
        with open(a.csv_file, encoding='utf-8-sig', errors='replace') as f: text = f.read()
        source = a.csv_file
    else:
        url = sheet_export_url(d['config'].get('sheetCsvUrl'))
        if not url:
            print('[]'); print('inbox: config.sheetCsvUrl is not set; nothing to fetch', file=sys.stderr); return 0
        text = http_get(url); source = url
    known = {it['id'] for it in d['items']}
    new, skipped = [], []
    for row in parse_rows(text):
        if not row['urls']:
            skipped.append({'reason': 'no http(s) link in row', 'cell': row['rawLink']}); continue
        for raw in row['urls']:
            norm = normalize_url(raw)
            if not norm:
                skipped.append({'reason': 'not an http(s) URL', 'cell': clean_text(raw, 80)}); continue
            iid = item_id(norm)
            if iid in known:
                skipped.append({'reason': 'duplicate', 'id': iid[:10], 'url': norm}); continue
            known.add(iid)
            it = {'id': iid, 'url': norm, 'submittedAt': row['ts'] or now_iso(), 'submittedNote': row['note'], 'submitter': row['name'],
                  'status': 'queued', 'analyzedAt': None, 'listing': None, 'numbers': None, 'verdict': None}
            new.append(it)
    if new and not a.dry_run:
        d['items'].extend(new); save(a.inbox, d)
    print(json.dumps(new, indent=2, ensure_ascii=False))
    print(f'inbox: {len(new)} queued from {source}' + (' (dry run, not saved)' if a.dry_run and new else '') +
          (f'; skipped {len(skipped)}: ' + json.dumps(skipped, ensure_ascii=False) if skipped else ''), file=sys.stderr)
    return 0

def cmd_list_queued(a):
    d = load(a.inbox)
    print(json.dumps([{'id': it['id'], 'url': it['url'], 'status': it['status'], 'submittedAt': it.get('submittedAt'), 'note': it.get('submittedNote')}
                      for it in d['items'] if it['status'] in ('queued', 'analyzing')], indent=2, ensure_ascii=False))
    return 0

def find(d, iid):
    hits = [it for it in d['items'] if it['id'] == iid or (len(iid) >= 6 and it['id'].startswith(iid))]
    if len(hits) != 1:
        sys.exit(f'inbox: id {iid!r} matched {len(hits)} items')
    return hits[0]

def cmd_start(a):
    d = load(a.inbox); it = find(d, a.id)
    it['status'] = 'analyzing'; save(a.inbox, d); print(json.dumps({'id': it['id'], 'status': it['status']}))
    return 0

# ----------------------------------------------------------------------------- record: schema-checked merge of an analysis file
S, I, F, B = 'str', 'int', 'num', 'bool'
def s(cap=240): return ('str', cap)
def url(): return ('url', URL_MAX)
def lst(inner, cap=12): return ('list', inner, cap)
SCHEMA = {
    'status': s(12),
    'error': s(300),
    'analyzedAt': s(25),
    'listing': {
        'year': I, 'make': s(30), 'model': s(40), 'trim': s(80), 'miles': I, 'price': F, 'docFee': F, 'dealer': s(80), 'city': s(60), 'state': s(2),
        'vin': s(17), 'stock': s(20), 'daysListed': I,
        'priceHistory': lst({'date': s(10), 'price': F, 'note': s(120)}, 20),
        'history': {'owners': I, 'accidents': I, 'rental': ('any', 60), 'cpo': ('any', 80)},
        'deal': {'cgRating': s(20), 'cgDelta': F, 'kbbFpp': F, 'kbbDelta': F},
        'photos': I,
        'links': {'source': url(), 'cargurus': url(), 'kbb': url()},
    },
    'numbers': {'taxRate': F, 'estOtd': F, 'monthly0': F, 'monthly5k': F, 'basis': s(240)},
    'verdict': {'label': s(20), 'oneLine': s(400), 'bullets': lst(s(700), 12), 'flags': lst(s(400), 12), 'openingMove': s(900), 'targetOtd': F, 'slot': s(500)},
}

def check(value, spec, path, errs):
    """Return a cleaned copy of value per spec; append problems to errs; drop unknown keys."""
    if value is None: return None
    if isinstance(spec, dict):
        if not isinstance(value, dict):
            errs.append(f'{path}: expected object'); return None
        out = {}
        for k, v in value.items():
            if k not in spec:
                errs.append(f'{path}.{k}: unknown key dropped'); continue
            out[k] = check(v, spec[k], f'{path}.{k}', errs)
        return out
    kind = spec if isinstance(spec, str) else spec[0]
    if kind == 'list':
        if not isinstance(value, list):
            errs.append(f'{path}: expected list'); return None
        if len(value) > spec[2]: errs.append(f'{path}: capped at {spec[2]} entries')
        return [check(v, spec[1], f'{path}[{i}]', errs) for i, v in enumerate(value[:spec[2]])]
    if kind in ('str', 'url'):
        if not isinstance(value, (str, int, float)) or isinstance(value, bool):
            errs.append(f'{path}: expected string'); return None
        t = clean_text(value, spec[1])
        if kind == 'url' and t is not None:
            n = t if urllib.parse.urlsplit(t).scheme in ('http', 'https') and not re.search(r'\s', t) else None
            if not n: errs.append(f'{path}: not an http(s) URL, dropped')
            return n
        return t
    if kind == 'any':
        if isinstance(value, bool) or value is None: return value
        if isinstance(value, (int, float)): return value
        return clean_text(value, spec[1])
    if kind == 'bool':
        if isinstance(value, bool): return value
        errs.append(f'{path}: expected true/false'); return None
    if kind in ('int', 'num'):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            errs.append(f'{path}: expected number'); return None
        if abs(value) > 10_000_000: errs.append(f'{path}: out of range'); return None
        return int(round(value)) if kind == 'int' else value
    errs.append(f'{path}: bad schema'); return None

def cmd_record(a):
    d = load(a.inbox); it = find(d, a.id)
    with open(a.analysis, encoding='utf-8') as f: raw = json.load(f)
    errs = []
    clean = check(raw, SCHEMA, 'analysis', errs) or {}
    v = clean.get('verdict') or {}
    if v.get('label') and v['label'] not in VERDICTS:
        errs.append(f'analysis.verdict.label: {v["label"]!r} not one of {VERDICTS}; set to skip'); v['label'] = 'skip'
    status = clean.get('status')
    if status not in ('done', 'error'):
        status = 'error' if (clean.get('error') and not clean.get('listing')) or v.get('label') == "couldn't load" and not clean.get('listing') else 'done'
    if status == 'done' and not (v.get('label') and v.get('oneLine')):
        sys.exit('inbox: a done analysis needs verdict.label and verdict.oneLine; nothing recorded. Problems: ' + '; '.join(errs))
    it.update(status=status, analyzedAt=clean.get('analyzedAt') or now_iso(), listing=clean.get('listing'), numbers=clean.get('numbers'),
              verdict=v or None)
    if clean.get('error'): it['error'] = clean['error']
    elif 'error' in it and status == 'done': it.pop('error')
    save(a.inbox, d)
    print(json.dumps({'id': it['id'], 'status': it['status'], 'verdict': (it.get('verdict') or {}).get('label'), 'warnings': errs}, indent=2, ensure_ascii=False))
    return 0

def cmd_render(a):
    """build_site.py already renders ask.html from data/inbox.json; this just runs it (extra args pass through, e.g. --no-pdf)."""
    return subprocess.call([sys.executable, os.path.join(ROOT, 'tools', 'build_site.py')] + list(a.build_args))

# ----------------------------------------------------------------------------- main
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--inbox', default=DEFAULT_INBOX, help='inbox JSON path (default data/inbox.json)')
    sub = ap.add_subparsers(dest='cmd', required=True)
    f = sub.add_parser('fetch', help='queue new links from the response sheet CSV')
    f.add_argument('--csv-file', help='read a local CSV instead of config.sheetCsvUrl (testing)')
    f.add_argument('--dry-run', action='store_true', help='parse and print, do not save')
    f.set_defaults(fn=cmd_fetch)
    sub.add_parser('list-queued', help='queued / analyzing items as JSON').set_defaults(fn=cmd_list_queued)
    st = sub.add_parser('start', help='mark an item analyzing'); st.add_argument('id'); st.set_defaults(fn=cmd_start)
    r = sub.add_parser('record', help='attach a validated analysis to an item'); r.add_argument('id'); r.add_argument('analysis'); r.set_defaults(fn=cmd_record)
    rd = sub.add_parser('render', help='regenerate the site (tools/build_site.py)'); rd.add_argument('build_args', nargs=argparse.REMAINDER); rd.set_defaults(fn=cmd_render)
    a = ap.parse_args(argv)
    return a.fn(a)

if __name__ == '__main__':
    sys.exit(main())
