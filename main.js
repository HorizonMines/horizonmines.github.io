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
