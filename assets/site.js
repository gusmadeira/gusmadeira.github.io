/* Shared header and footer for the static site (Live Preview + GitHub Pages). */
(() => {
  async function getComponent(path) {
    const response = await fetch(path);
    if (!response.ok) throw new Error(`Could not load ${path}: HTTP ${response.status}`);
    return response.text();
  }

  function setupMobileNavigation() {
    const toggle = document.querySelector('.menu-toggle');
    const menu = document.querySelector('#site-menu');
    if (!toggle || !menu) return;

    const closeMenu = () => {
      toggle.setAttribute('aria-expanded', 'false');
      toggle.setAttribute('aria-label', 'Open navigation');
      menu.classList.remove('is-open');
    };

    toggle.addEventListener('click', () => {
      const shouldOpen = toggle.getAttribute('aria-expanded') !== 'true';
      toggle.setAttribute('aria-expanded', String(shouldOpen));
      toggle.setAttribute('aria-label', shouldOpen ? 'Close navigation' : 'Open navigation');
      menu.classList.toggle('is-open', shouldOpen);
    });
    menu.addEventListener('click', (event) => {
      if (event.target.closest('a')) closeMenu();
    });
    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape') closeMenu();
    });
    document.addEventListener('click', (event) => {
      if (!toggle.contains(event.target) && !menu.contains(event.target)) closeMenu();
    });
    const desktopQuery = window.matchMedia('(min-width: 901px)');
    if (desktopQuery.addEventListener) {
      desktopQuery.addEventListener('change', (event) => {
        if (event.matches) closeMenu();
      });
    }
  }

  async function initSharedLayout() {
    const headerSlot = document.querySelector('[data-site-header]');
    const footerSlot = document.querySelector('[data-site-footer]');
    if (!headerSlot || !footerSlot) return;

    const active = headerSlot.getAttribute('data-active');
    try {
      const [header, footer] = await Promise.all([
        getComponent('components/header.html'),
        getComponent('components/footer.html')
      ]);
      headerSlot.outerHTML = header;
      footerSlot.outerHTML = footer;

      // Preserve the menu item marked on each page in the previous version.
      if (active) {
        const activeLink = document.querySelector(`.site-nav a[href="${active === 'home' ? 'index' : active}.html"]`);
        if (activeLink) {
          activeLink.classList.add('is-active');
          activeLink.setAttribute('aria-current', 'page');
        }
      }
      setupMobileNavigation();
    } catch (error) {
      console.error('Could not load the shared site header and footer.', error);
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initSharedLayout, { once: true });
  } else {
    initSharedLayout();
  }
})();
