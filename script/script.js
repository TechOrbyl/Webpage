const toggle = document.querySelector('.menu-toggle');
const nav = document.querySelector('.site-nav');
const yearEl = document.getElementById('year');

if (toggle && nav) {
  toggle.addEventListener('click', () => {
    const isOpen = nav.classList.toggle('is-open');
    toggle.setAttribute('aria-expanded', String(isOpen));
  });
}

if (yearEl) {
  yearEl.textContent = new Date().getFullYear();
}
