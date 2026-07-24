// Click a server address to copy it. No boxes to click — the whole
// row is the target, and the "copy" hint confirms the action in place.

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
