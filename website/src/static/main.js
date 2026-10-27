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
var tabs = document.querySelectorAll('[role="tab"]');
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
