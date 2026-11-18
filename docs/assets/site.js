// lemo-animi gallery: puppets turn round on twos, loops play only while on screen, copy buttons, theme.
(function () {
  var still = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  var root = document.documentElement;
  try { var th = localStorage.getItem('animi-theme'); if (th) root.dataset.theme = th; } catch (e) {}

  // ---- a full turn: front, 3/4, side, back, then side and 3/4 mirrored, front. 8 drawings a second.
  var SEQ = [1, 2, 3, -2, -1, 0];
  function turn(el) {
    if (!el || el._busy) return;
    el._busy = true;
    var i = 0;
    (function next() {
      var v = SEQ[i++];
      el.classList.remove('f1', 'f2', 'f3', 'flip');
      if (v) el.classList.add('f' + Math.abs(v));
      if (v < 0) el.classList.add('flip');
      if (i < SEQ.length) setTimeout(next, 125); else el._busy = false;
    })();
  }
  document.querySelectorAll('[data-turn]').forEach(function (box) {
    var sp = box.querySelector('.sprite');
    box.addEventListener('pointerenter', function () { turn(sp); });
    box.addEventListener('focus', function () { turn(sp); });
    box.addEventListener('click', function () { turn(sp); });
  });

  // ---- now and then one of the cast turns by itself while the shelf is on screen
  var shelf = document.querySelector('.cast');
  if (shelf && !still && 'IntersectionObserver' in window) {
    var seen = false, sprites = shelf.querySelectorAll('.sprite'), last = -1;
    new IntersectionObserver(function (es) { seen = es[0].isIntersecting; }).observe(shelf);
    setTimeout(function () { sprites.forEach(function (s, k) { setTimeout(function () { turn(s); }, k * 180); }); }, 700);
    setInterval(function () {
      if (!seen || document.hidden) return;
      var k; do { k = Math.floor(Math.random() * sprites.length); } while (k === last && sprites.length > 1);
      last = k; turn(sprites[k]);
    }, 2600);
  }

  // ---- loops play only while on screen; with reduced motion they wait for a click
  var vids = document.querySelectorAll('video[data-loop]');
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (e) {
        var v = e.target;
        if (e.isIntersecting && !still) { v.preload = 'auto'; var p = v.play(); if (p && p.catch) p.catch(function () {}); }
        else v.pause();
      });
    }, { threshold: 0.35 });
    vids.forEach(function (v) { io.observe(v); });
  }
  vids.forEach(function (v) { v.addEventListener('click', function () { v.paused ? v.play() : v.pause(); }); });

  // ---- copy buttons: the label swaps to "Copied" for a moment
  document.querySelectorAll('.copy').forEach(function (b) {
    var lab = b.querySelector('span') || b;
    b.addEventListener('click', function () {
      var t = b.closest('.code').querySelector('.cmd').textContent, done = function () {
        var o = lab.textContent; lab.textContent = b.dataset.done; b.classList.add('done');
        setTimeout(function () { lab.textContent = o; b.classList.remove('done'); }, 1400);
      };
      if (navigator.clipboard) navigator.clipboard.writeText(t).then(done, function () {});
    });
  });

  // ---- top bar line once scrolled; theme toggle
  var top = document.querySelector('.top');
  addEventListener('scroll', function () { top.classList.toggle('stuck', scrollY > 8); }, { passive: true });
  var tb = document.getElementById('theme');
  if (tb) tb.addEventListener('click', function () {
    var dark = root.dataset.theme ? root.dataset.theme === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches;
    root.dataset.theme = dark ? 'light' : 'dark';
    try { localStorage.setItem('animi-theme', root.dataset.theme); } catch (e) {}
  });
})();
