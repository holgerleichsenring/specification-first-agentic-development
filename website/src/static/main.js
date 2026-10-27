(function () {
document.querySelectorAll('.copy').forEach(function (b) {
  b.addEventListener('click', function () {
    var el = document.getElementById(b.dataset.copy);
    var text = el.textContent.trim();
    var done = function () { b.textContent = 'Copied'; setTimeout(function () { b.textContent = 'Copy'; }, 1600); };
    try {
      navigator.clipboard.writeText(text).then(done, function () { select(el); });
    } catch (e) { select(el); }
  });
});
function select(el) { var r = document.createRange(); r.selectNodeContents(el); var s = window.getSelection(); s.removeAllRanges(); s.addRange(r); }
var tabs = document.querySelectorAll('.tabs [role="tab"]');
tabs.forEach(function (t) {
  t.addEventListener('click', function () {
    tabs.forEach(function (o) { o.setAttribute('aria-selected', o === t ? 'true' : 'false'); document.getElementById(o.getAttribute('aria-controls')).hidden = o !== t; });
  });
});
(function () {
  // stage per spec: 1 reviewed, 2 building, 3 through the gate, 4 merged
  var frames = [
    { a: 1, b: 1, c: 1, d: 1, e: 1 },
    { a: 2, b: 1, c: 1, d: 2, e: 2 },
    { a: 3, b: 2, c: 1, d: 2, e: 3 },
    { a: 3, b: 3, c: 2, d: 3, e: 3 },
    { a: 3, b: 3, c: 3, d: 3, e: 3 },
    { a: 4, b: 4, c: 4, d: 4, e: 4 }
  ];  var rows = document.querySelectorAll('.row[data-s]');
  var state = document.getElementById('b-state'), foot = document.getElementById('b-foot'), pr = document.getElementById('b-pr');
  if (!rows.length || !state) return;
  function cell(st, k) {
    if (k === 0) return 'on';
    if (k === 1) return st === 2 ? 'now' : (st > 2 ? 'on' : '');
    if (k === 2) return st >= 3 ? 'on' : '';
    return st >= 4 ? 'on' : '';
  }
  function show(n) {
    var f = frames[n], last = n === frames.length - 1;
    rows.forEach(function (r) {
      r.querySelectorAll('.track i').forEach(function (c, k) { c.className = cell(f[r.dataset.s], k); });
    });
    state.textContent = last ? 'one pull request' : (n === 0 ? 'reviewed' : 'building');
    foot.innerHTML = last ? '<b>merged tree verified</b> · CI green · 5 specs in one pull request'
      : (n === 0 ? '<b>5 specs reviewed</b> · cuts applied · grouped by the files they touch'
      : '<b>3 worktrees</b> building in parallel · every spec commit through the gate');
    pr.classList.toggle('open', last);
  }
  var n = 2; show(n);
  var reduce = false;
  try { reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches; } catch (e) {}
  if (!reduce) setInterval(function () { n = (n + 1) % frames.length; show(n); }, 1700);
})();
})();

(function () {
  var vsc = document.querySelector('.vsc'); if (!vsc) return;
  var stage = document.querySelector('.ide-stage');
  var pills = document.querySelectorAll('.ide-steps [data-step]');
  var log = vsc.querySelector('.cc-log'), input = vsc.querySelector('.cc-input'), typed = document.getElementById('cc-typed');
  var startPane = ['main', 'main', 'spec', 'spec', 'code'], finalPane = ['main', 'spec', 'spec', 'code', 'app'];
  var $ = function (id) { return document.getElementById(id); };
  var reduce = false;
  try { reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches; } catch (e) {}

  // one timeline per step: type = you type it, tool = a skill runs it, say = the agent answers
  var T = [
    [['type', 'c1', 22], ['tool', 'c2', 700], ['tool', 'c3', 600, 'main'], ['say', 'c4'], ['type', 'c5', 40]],
    [['type', 'c6'], ['tool', 'c8', 700, 'spec', ['t-spec']], ['say', 'c27'], ['type', 'c28', 45], ['tool', 'c7', 900, null, ['e-planned', 'e-spec', 'br-spec'], ['br-main-off']], ['say', 'c9']],
    [['type', 'c10'], ['tool', 'c11', 900, null, null, ['m-ok1', 'm-ok2']], ['tool', 'c12', 2200], ['tool', 'c13', 700, null, null, ['m-strike', 'm-cut', 'm-add']], ['say', 'c14']],
    [['type', 'c15'], ['say', 'c29'], ['type', 'c30', 80], ['tool', 'c16', 600, 'code', ['e-todos', 't-code'], ['e-planned-off']], ['tool', 'c17', 600, null, ['e-list']], ['tool', 'c18', 600, null, ['e-test']], ['tool', 'c19', 1500], ['tool', 'c20', 500, null, ['e-dec', 'e-done'], ['e-active-off']], ['say', 'c21']],
    [['type', 'c22'], ['tool', 'c23', 1700], ['tool', 'c24', 900], ['tool', 'c26', 1200, 'app', ['t-app']], ['say', 'c25'], ['tick']]
  ];
  var cmds = { c6: '/spec-first:create-spec', c10: '/spec-first:review-spec', c15: '/spec-first:apply-spec', c22: '/spec-first:deliver-spec' };

  function inRange(spec, r) { var p = spec.split('-'); return r >= +p[0] && r <= +(p[1] || p[0]); }
  function applyRange(r) {
    vsc.querySelectorAll('[data-show]').forEach(function (el) { el.hidden = !inRange(el.dataset.show, r); el.classList.remove('in', 'run'); });
    $('m-strike').classList.toggle('struck', r === 2);
    $('app-tick').classList.remove('is-done'); $('app-count').textContent = '2 open · saved in this browser';
  }
  function open(pane, animate) {
    vsc.querySelectorAll('[data-pane]').forEach(function (el) { el.hidden = el.dataset.pane !== pane; });
    vsc.querySelectorAll('.vsc-tabs .tab').forEach(function (t) { t.classList.toggle('on', t.dataset.tab === pane); });
    var tab = $('t-' + pane); if (tab) tab.hidden = false;
    var p = $('p-' + pane);
    if (animate && p) { p.classList.remove('in'); void p.offsetWidth; p.classList.add('in'); }
    return p;
  }
  function bubbles(n) { stage.querySelectorAll('.bubble').forEach(function (b) { b.hidden = !inRange(b.dataset.show, n); }); }
  function pill(n) { pills.forEach(function (b) { b.setAttribute('aria-pressed', +b.dataset.step === n ? 'true' : 'false'); }); vsc.dataset.step = n; }
  function scroll() { log.scrollTop = log.scrollHeight; }
  function complete(n) {
    applyRange(n); open(finalPane[n]); bubbles(n); pill(n); typed.textContent = '';
    if (n === 4) { $('app-tick').classList.add('is-done'); $('app-count').textContent = '1 open · saved in this browser'; }
    setTimeout(scroll, 30);
  }

  var token = 0;
  function wait(ms, t) { return new Promise(function (res, rej) { setTimeout(function () { t === token ? res() : rej(); }, ms); }); }
  function reveal(el) { if (!el) return; el.hidden = false; el.classList.remove('in'); void el.offsetWidth; el.classList.add('in'); }
  async function typeInto(text, speed, t) {
    input.classList.add('typing'); typed.textContent = '';
    for (var i = 1; i <= text.length; i++) { typed.textContent = text.slice(0, i); await wait(speed, t); }
    await wait(350, t); typed.textContent = ''; input.classList.remove('typing');
  }
  async function writeLines(pane, n, t) {
    var p = $('p-' + pane); if (!p || !p.querySelectorAll) return;
    var lines = Array.prototype.filter.call(p.querySelectorAll('.ln'), function (l) { return !l.dataset.show || inRange(l.dataset.show, n); });
    if (pane === 'app') { reveal(p); return; }
    lines.forEach(function (l) { l.hidden = true; });
    for (var i = 0; i < lines.length; i++) { reveal(lines[i]); await wait(55, t); }
  }
  async function play(n, t) {
    applyRange(n - 1); open(startPane[n]); bubbles(n); pill(n);
    if (n === 0) { $('br-main').hidden = false; vsc.querySelectorAll('.vsc-code').forEach(function (p) { if (p.id !== 'p-main') p.hidden = true; }); $('p-main').hidden = true; }
    for (var k = 0; k < T[n].length; k++) {
      var a = T[n][k], el = $(a[1]);
      if (a[0] === 'type') { await typeInto(cmds[a[1]] || el.textContent.trim(), a[2] || 70, t); reveal(el); scroll(); await wait(500, t); }
      if (a[0] === 'tool') {
        reveal(el); el.classList.add('run'); scroll();
        await wait(a[2], t); el.classList.remove('run');
        (a[4] || []).forEach(function (id) { reveal($(id)); });
        if (a[3]) { open(a[3], true); await writeLines(a[3], n, t); }
        for (var m = 0; m < (a[5] || []).length; m++) {
          var id = a[5][m];
          if (/-off$/.test(id)) { $(id === 'br-main-off' ? 'br-main' : id.slice(0, -4)).hidden = true; if (id === 'e-planned-off') reveal($('e-active')); continue; }
          if (id === 'm-strike') $('m-strike').classList.add('struck'); else reveal($(id));
          await wait(450, t);
        }
        await wait(250, t);
      }
      if (a[0] === 'say') { reveal(el); scroll(); await wait(900, t); }
      if (a[0] === 'tick') { await wait(700, t); $('app-tick').classList.add('is-done'); $('app-count').textContent = '1 open · saved in this browser'; }
    }
    await wait(n === 4 ? 4200 : 2200, t);
  }
  async function loop(n) {
    var t = ++token;
    try { for (;;) { await play(n, t); n = (n + 1) % 5; } } catch (e) { /* replaced by a newer run */ }
  }
  pills.forEach(function (b) {
    b.addEventListener('click', function () { var n = +b.dataset.step; if (reduce) { token++; complete(n); } else loop(n); });
  });
  if (reduce) complete(2); else loop(0);
})();
