// static/js/auth_tabs.js
(function () {
  function qs(sel, root) { return (root || document).querySelector(sel); }
  function qsa(sel, root) { return Array.from((root || document).querySelectorAll(sel)); }

  function showTab(name) {
    var isLogin = name !== 'register';
    var loginPanel = qs('#panel-login');
    var registerPanel = qs('#panel-register');
    if (loginPanel) loginPanel.classList.toggle('is-hidden', !isLogin);
    if (registerPanel) registerPanel.classList.toggle('is-hidden', isLogin);

    var tLogin = qs('#tab-login');
    var tReg = qs('#tab-register');
    if (tLogin && tReg) {
      tLogin.classList.toggle('is-active', isLogin);
      tReg.classList.toggle('is-active', !isLogin);
      tLogin.setAttribute('aria-selected', isLogin ? 'true' : 'false');
      tReg.setAttribute('aria-selected', !isLogin ? 'true' : 'false');
    }

    try {
      var u = new URL(window.location.href);
      u.searchParams.set('tab', name);
      window.history.replaceState({}, '', u.toString());
    } catch (e) {}
  }

  function getInitialTab() {
    try {
      var p = new URLSearchParams(window.location.search).get('tab');
      if (p === 'register' || p === 'login') return p;
    } catch (e) {}
    var regPanel = qs('#panel-register');
    if (regPanel && !regPanel.classList.contains('is-hidden')) return 'register';
    return 'login';
  }

  function wirePasswordToggles() {
    qsa('[data-toggle-password]').forEach(function (btn) {
      var sel = btn.getAttribute('data-toggle-password');
      if (!sel) return;
      var input = qs(sel);
      if (!input) return;
      btn.addEventListener('click', function (e) {
        e.preventDefault();
        var type = input.getAttribute('type') === 'password' ? 'text' : 'password';
        input.setAttribute('type', type);
        btn.innerHTML = type === 'password' ? '<i class="bi bi-eye"></i>' : '<i class="bi bi-eye-slash"></i>';
        input.focus();
      });
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    var initial = getInitialTab();
    if (qs('[data-auth-tab]')) showTab(initial);

    qsa('[data-auth-tab]').forEach(function (btn) {
      btn.addEventListener('click', function (e) {
        e.preventDefault();
        var tab = btn.getAttribute('data-auth-tab');
        if (tab) showTab(tab);
      });
    });

    qsa('[data-switch-tab]').forEach(function (lnk) {
      lnk.addEventListener('click', function (e) {
        e.preventDefault();
        var tab = lnk.getAttribute('data-switch-tab');
        if (tab) showTab(tab);
      });
    });

    wirePasswordToggles();
  });
})();
