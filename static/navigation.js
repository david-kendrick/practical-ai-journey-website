document.addEventListener('DOMContentLoaded', () => {
  const mobileMenus = document.querySelectorAll('.mobile-menu');

  if (!mobileMenus.length) return;

  document.addEventListener('click', (event) => {
    mobileMenus.forEach((menu) => {
      if (!menu.open) return;
      if (menu.contains(event.target)) return;
      menu.open = false;
    });
  });

  document.addEventListener('keydown', (event) => {
    if (event.key !== 'Escape') return;

    mobileMenus.forEach((menu) => {
      menu.open = false;
    });
  });

  mobileMenus.forEach((menu) => {
    menu.querySelectorAll('a').forEach((link) => {
      link.addEventListener('click', () => {
        menu.open = false;
      });
    });
  });
});
