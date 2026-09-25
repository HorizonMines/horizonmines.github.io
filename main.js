// Click a server address row to copy it. The hint in the row swaps to
// "copied" for a moment, and the same message goes to a live region.

(function () {
  'use strict';

  var status = document.getElementById('copy-status');

  function copyText(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      return navigator.clipboard.writeText(text);
    }
    return new Promise(function (resolve, reject) {
      var ta = document.createElement('textarea');
      ta.value = text;
      ta.style.position = 'fixed';
      ta.style.opacity = '0';
      document.body.appendChild(ta);
      ta.select();
      var ok = false;
      try { ok = document.execCommand('copy'); } catch (e) { ok = false; }
      document.body.removeChild(ta);
      ok ? resolve() : reject();
    });
  }

  document.querySelectorAll('.row').forEach(function (row) {
    var hint = row.querySelector('.hint');
    var address = row.dataset.copy;
    var timer;

    function confirm() {
      row.classList.add('copied');
      hint.textContent = 'copied';
      if (status) status.textContent = address + ' copied to clipboard';
      clearTimeout(timer);
      timer = setTimeout(function () {
        row.classList.remove('copied');
        hint.textContent = 'copy';
      }, 1900);
    }

    row.addEventListener('click', function () {
      copyText(address).then(confirm, function () {
        hint.textContent = 'failed';
        clearTimeout(timer);
        timer = setTimeout(function () { hint.textContent = 'copy'; }, 1900);
      });
    });
  });
})();

// Server status: ask a public status API whether the Java server answers
// on its Minecraft port, and colour the bubble green or red. If the
// status service itself can't be reached, the indicator stays hidden. Browsers
// can't open raw TCP sockets, so the ping goes through api.mcstatus.io
// (which caches each result for up to a minute).

(function () {
  'use strict';

  var el = document.getElementById('server-status');
  if (!el) return;

  var label = el.querySelector('.status-label');
  var API = 'https://api.mcstatus.io/v2/status/java/HorizonMines.net:25565';
  var INTERVAL = 10000;
  var timer;

  function show(state, players) {
    el.hidden = false;
    el.dataset.state = state;
    if (state !== 'online') {
      label.textContent = 'Offline';
    } else if (players && typeof players.online === 'number') {
      label.textContent = 'Online \u00b7 ' + players.online +
        (players.online === 1 ? ' player' : ' players');
    } else {
      label.textContent = 'Online';
    }
    el.title = 'HorizonMines.net: ' + label.textContent;
  }

  function check() {
    clearTimeout(timer);
    fetch(API, { cache: 'no-store' })
      .then(function (res) { return res.ok ? res.json() : Promise.reject(); })
      .then(function (data) { show(data.online ? 'online' : 'offline', data.players); })
      // Service unreachable: we don't know the server's state, so hide.
      .catch(function () { el.hidden = true; })
      .then(function () {
        if (!document.hidden) timer = setTimeout(check, INTERVAL);
      });
  }

  // Stop polling while the tab is in the background; catch up on return.
  document.addEventListener('visibilitychange', function () {
    if (document.hidden) clearTimeout(timer);
    else check();
  });

  check();
})();
