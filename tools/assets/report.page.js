(function () {
  'use strict';
  var PTS = __POINTS__;
  var EMAIL = __EMAIL__;
  var fmt$ = function (n) { return (n < 0 ? '−$' : '$') + Math.abs(Math.round(n)).toLocaleString('en-US'); };
  var fmt$2 = function (n) { return '$' + n.toFixed(2); };
  function esc(s) { return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }
  var closest = function (el, sel) {
    while (el && el.nodeType === 1) {
      var m = el.matches || el.webkitMatchesSelector || el.msMatchesSelector;
      if (m && m.call(el, sel)) return el;
      el = el.parentNode;
    }
    return null;
  };

  // ---- sortable table (desktop presentation) ----
  Array.prototype.forEach.call(document.querySelectorAll('table.sortable'), function (table) {
    var ths = table.tHead.rows[0].cells;
    Array.prototype.forEach.call(ths, function (th, col) {
      if (th.hasAttribute('data-nosort')) return;
      th.querySelector('button').addEventListener('click', function () {
        var dir = th.getAttribute('aria-sort') === 'ascending' ? 'descending' : 'ascending';
        Array.prototype.forEach.call(ths, function (o) { o.removeAttribute('aria-sort'); });
        th.setAttribute('aria-sort', dir);
        var body = table.tBodies[0];
        var rows = Array.prototype.slice.call(body.rows);
        var key = function (tr) {
          var td = tr.cells[col];
          if (td.hasAttribute('data-v')) return parseFloat(td.getAttribute('data-v'));
          var t = td.textContent.trim().replace(/−/g, '-');
          var n = parseFloat(t.replace(/[$,#%]/g, ''));
          return (/^[-+]?[$#]?[\d,.]+/.test(t) && !isNaN(n)) ? n : t.toLowerCase();
        };
        rows.sort(function (a, b) {
          var ka = key(a), kb = key(b), r;
          if (typeof ka === 'number' && typeof kb === 'number') r = ka - kb;
          else r = String(ka).localeCompare(String(kb), undefined, { numeric: true });
          return dir === 'ascending' ? r : -r;
        });
        rows.forEach(function (tr) { body.appendChild(tr); });
      });
    });
  });

  // ---- sortable cards (phone presentation) ----
  var sel = document.getElementById('sl-sort'), list = document.getElementById('sl-cards');
  if (sel && list) sel.addEventListener('change', function () {
    var k = sel.value;
    var cards = Array.prototype.slice.call(list.children);
    cards.sort(function (a, b) {
      var av = parseFloat(a.getAttribute('data-' + k)), bv = parseFloat(b.getAttribute('data-' + k));
      var r = k === 'year' ? bv - av : av - bv;
      return r || (parseFloat(a.getAttribute('data-rank')) - parseFloat(b.getAttribute('data-rank')));
    });
    cards.forEach(function (c) { list.appendChild(c); });
  });

  // ---- tooltip ----
  var tip = document.getElementById('tip');
  function showTip(html, x, y) {
    tip.innerHTML = html; tip.hidden = false;
    var w = tip.offsetWidth, h = tip.offsetHeight;
    var left = x + 14, top = y - h - 12;
    if (left + w > window.innerWidth - 8) left = x - w - 14;
    if (top < 8) top = y + 16;
    tip.style.left = Math.max(8, Math.min(left, window.innerWidth - w - 8)) + 'px'; tip.style.top = top + 'px';
  }
  function hideTip() { tip.hidden = true; }
  var hot = null;
  function clearHot() { if (hot) hot.classList.remove('hot'); hot = null; }
  // touch screens synthesize mouse events after a tap (and some park the virtual pointer elsewhere right after);
  // ignore mouseleave that closely follows a touch so a tapped tooltip stays up until the next tap
  var lastTouch = 0;
  document.addEventListener('touchstart', function () { lastTouch = Date.now(); }, { passive: true, capture: true });
  var recentTouch = function () { return Date.now() - lastTouch < 900; };

  // scatter (desktop + phone variants): nearest point to the pointer / finger, centres come from data-x / data-y
  Array.prototype.forEach.call(document.querySelectorAll('svg.scatter'), function (svg) {
    var centers = Array.prototype.map.call(svg.querySelectorAll('.pt'), function (g) {
      return { x: +g.getAttribute('data-x'), y: +g.getAttribute('data-y'), g: g, i: +g.getAttribute('data-i') };
    });
    var pick = function (clientX, clientY) {
      var ctm = svg.getScreenCTM && svg.getScreenCTM();
      if (!ctm) return;
      var pt = svg.createSVGPoint(); pt.x = clientX; pt.y = clientY;
      var p = pt.matrixTransform(ctm.inverse());
      var best = null, bd = Infinity;
      for (var k = 0; k < centers.length; k++) {
        var c = centers[k], dx = c.x - p.x, dy = c.y - p.y, d = dx * dx + dy * dy;
        if (d < bd) { bd = d; best = c; }
      }
      var maxR = 24 / (ctm.a || 1);
      if (!best || bd > maxR * maxR) { clearHot(); hideTip(); return; }
      if (hot !== best.g) { clearHot(); hot = best.g; hot.classList.add('hot'); }
      var d0 = PTS[best.i];
      var head = (d0.r ? '<b>#' + d0.r + ' · </b>' : '') + '<b>' + d0.y + ' ' + esc(d0.t || 'CX-5') + '</b>';
      var html = head + '<br>' + fmt$(d0.p) + ' · ' + Math.round(d0.m).toLocaleString('en-US') + ' mi<br><span class="t2">' + esc(d0.d || '') + (d0.c ? ' · ' + esc(d0.c) : '') + ' · ' + esc(d0.s) + '</span>';
      var r = best.g.getBoundingClientRect();
      showTip(html, r.left + r.width / 2, r.top);
    };
    svg.addEventListener('mousemove', function (e) { if (!recentTouch()) pick(e.clientX, e.clientY); });
    svg.addEventListener('click', function (e) { pick(e.clientX, e.clientY); });
    svg.addEventListener('mouseleave', function () { if (recentTouch()) return; clearHot(); hideTip(); });
    svg.addEventListener('touchstart', function (e) { var t = e.touches && e.touches[0]; if (t) pick(t.clientX, t.clientY); }, { passive: true });
  });
  var tint = document.getElementById('tint');
  var legend = document.getElementById('scatter-legend');
  if (tint) tint.addEventListener('change', function () {
    Array.prototype.forEach.call(document.querySelectorAll('svg.scatter'), function (s) { s.classList.toggle('tinted', tint.checked); });
    if (legend) legend.classList.toggle('tinted', tint.checked);
  });
  // bars: hover / tap a row
  Array.prototype.forEach.call(document.querySelectorAll('svg.bars .bar-row'), function (g) {
    var show = function (x, y) { if (hot !== g) { clearHot(); hot = g; g.classList.add('hot'); } showTip(esc(g.getAttribute('data-tip')), x, y); };
    g.addEventListener('mousemove', function (e) { if (!recentTouch()) show(e.clientX, e.clientY); });
    g.addEventListener('mouseleave', function () { if (recentTouch()) return; clearHot(); hideTip(); });
    g.addEventListener('click', function (e) { show(e.clientX, e.clientY); });
    g.addEventListener('touchstart', function (e) { var t = e.touches && e.touches[0]; if (t) show(t.clientX, t.clientY); }, { passive: true });
  });
  // tap / click anywhere outside a chart hides the tooltip
  var outside = function (e) { if (!closest(e.target, 'svg.chart')) { clearHot(); hideTip(); } };
  document.addEventListener('touchstart', outside, { passive: true });
  document.addEventListener('click', outside);
  window.addEventListener('scroll', hideTip, { passive: true });
  window.addEventListener('resize', hideTip);

  // ---- calculator ----
  var el = function (id) { return document.getElementById(id); };
  var numval = function (id, dflt) { var v = parseFloat(String(el(id).value).replace(/[^0-9.\-]/g, '')); return isNaN(v) ? dflt : v; };
  // OTD = price x (1 + tax) + doc + licence (tax on the vehicle price; doc and licence added untaxed, as on the dealer sheets);
  // a written out-the-door figure, when entered, replaces the estimate.
  var DOC = __DOC__, LIC = __LIC__;
  function calc() {
    var list = Math.max(0, numval('c-list', 0));
    var down = Math.max(0, numval('c-down', 0));
    var apr = Math.max(0, numval('c-apr', 0));
    var n = Math.max(1, Math.round(numval('c-term', 60)));
    var tax = Math.max(0, numval('c-tax', __TAX__));
    var quoted = Math.max(0, numval('c-otdq', 0));
    var est = list * (1 + tax / 100) + DOC + LIC;
    var otd = quoted > 0 ? quoted : est;
    var lab = el('o-otd-k'); if (lab) lab.textContent = quoted > 0 ? 'Out-the-door (written)' : 'Out-the-door (est.)';
    var fin = Math.max(0, otd - down);
    var r = apr / 100 / 12;
    var pmt = function (P) { return r === 0 ? P / n : P * (r * Math.pow(1 + r, n)) / (Math.pow(1 + r, n) - 1); };
    var m = pmt(fin);
    var interest = m * n - fin;
    el('o-otd').textContent = fmt$(otd);
    el('o-fin').textContent = fmt$(fin);
    el('o-mo').textContent = fmt$(m) + '/mo';
    el('o-int').textContent = fmt$(interest);
    el('o-1k').textContent = fmt$2(pmt(1000)) + '/mo';
  }
  ['c-list', 'c-down', 'c-apr', 'c-term', 'c-tax', 'c-otdq'].forEach(function (id) { var e = el(id); if (e) { e.addEventListener('input', calc); e.addEventListener('change', calc); } });
  if (el('c-list')) calc();

  // ---- copy email (never throws: clipboard API inside the gesture, textarea-select fallback) ----
  var btn = document.getElementById('copy-btn');
  var ta = document.getElementById('email-ta');
  var quote = document.getElementById('email-text');
  var status = document.getElementById('copy-status');
  var setLabel = function (t, ms) { btn.textContent = t; if (ms) setTimeout(function () { btn.textContent = 'Copy'; }, ms); };
  var selectFallback = function () {
    try {
      if (ta) {
        ta.hidden = false; if (quote) quote.hidden = true;
        ta.focus(); ta.select();
        try { ta.setSelectionRange(0, ta.value.length); } catch (e1) { /* older engines */ }
        var ok = false;
        try { ok = !!(document.execCommand && document.execCommand('copy')); } catch (e2) { ok = false; }
        if (ok) { setLabel('Copied', 2200); if (status) status.textContent = 'Copied. The text also stays selected below.'; }
        else { setLabel('Text selected — tap Copy'); if (status) status.textContent = 'Tap Copy in the menu that appears, or press and hold the text.'; }
      } else setLabel('Press and hold the text to copy');
    } catch (e3) { setLabel('Press and hold the text to copy'); }
  };
  if (btn) btn.addEventListener('click', function () {
    try {
      if (navigator.clipboard && typeof navigator.clipboard.writeText === 'function' && window.isSecureContext !== false) {
        navigator.clipboard.writeText(EMAIL).then(function () { setLabel('Copied', 2200); if (status) status.textContent = ''; }, selectFallback);
      } else selectFallback();
    } catch (e) { selectFallback(); }
  });

  // ---- active nav chip + keep it scrolled into view ----
  var nav = document.querySelector('.navlinks');
  var links = {};
  Array.prototype.forEach.call(document.querySelectorAll('.navlinks a'), function (a) { var h = a.getAttribute('href'); if (h.charAt(0) === '#') links[h.slice(1)] = a; });
  var reveal = function (a) {
    if (!nav || !a) return;
    var L = a.offsetLeft, R = L + a.offsetWidth;
    if (L < nav.scrollLeft + 8) nav.scrollLeft = Math.max(0, L - 16);
    else if (R > nav.scrollLeft + nav.clientWidth - 8) nav.scrollLeft = R - nav.clientWidth + 28;
  };
  if ('IntersectionObserver' in window) {
    var current = null;
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) {
          if (current) current.classList.remove('active');
          current = links[en.target.id]; if (current) { current.classList.add('active'); reveal(current); }
        }
      });
    }, { rootMargin: '-45% 0px -50% 0px' });
    Object.keys(links).forEach(function (id) { var s = document.getElementById(id); if (s) io.observe(s); });
  }
})();
