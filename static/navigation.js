document.addEventListener('DOMContentLoaded', () => {
  const mobileMenus = document.querySelectorAll('.mobile-menu');

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

  const sectionNavLinks = Array.from(
    document.querySelectorAll('.secondary-links a[href^="#"]'),
  );

  if (!sectionNavLinks.length || !('IntersectionObserver' in window)) return;

  const sections = sectionNavLinks
    .map((link) => {
      const sectionId = decodeURIComponent(link.hash.slice(1));
      const element = document.getElementById(sectionId);
      return element ? { id: sectionId, element } : null;
    })
    .filter(Boolean);

  if (!sections.length) return;

  const sectionLinks = Array.from(
    document.querySelectorAll(
      '.secondary-links a[href^="#"], .mobile-menu-panel nav[aria-label="Page sections"] a[href^="#"]',
    ),
  );

  const setActiveSection = (activeId) => {
    sectionLinks.forEach((link) => {
      const isActive = decodeURIComponent(link.hash.slice(1)) === activeId;
      link.classList.toggle('is-active', isActive);

      if (isActive) {
        link.setAttribute('aria-current', 'true');
      } else {
        link.removeAttribute('aria-current');
      }
    });
  };

  const visibleSectionIds = new Set();
  const headerOffset = 132;

  const updateActiveSection = () => {
    const documentBottom = document.documentElement.scrollHeight - 2;
    const viewportBottom = window.scrollY + window.innerHeight;

    if (viewportBottom >= documentBottom) {
      setActiveSection(sections[sections.length - 1].id);
      return;
    }

    const currentOrPastSections = sections.filter(
      ({ element }) => element.getBoundingClientRect().top <= headerOffset + 4,
    );
    const currentOrPastSection = currentOrPastSections[currentOrPastSections.length - 1];

    if (currentOrPastSection) {
      setActiveSection(currentOrPastSection.id);
      return;
    }

    const visibleSections = sections
      .filter(({ id }) => visibleSectionIds.has(id))
      .sort(
        (a, b) =>
          Math.abs(a.element.getBoundingClientRect().top - headerOffset) -
          Math.abs(b.element.getBoundingClientRect().top - headerOffset),
      );

    if (visibleSections.length) {
      setActiveSection(visibleSections[0].id);
    }
  };

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          visibleSectionIds.add(entry.target.id);
        } else {
          visibleSectionIds.delete(entry.target.id);
        }
      });

      updateActiveSection();
    },
    {
      rootMargin: '-132px 0px -60% 0px',
      threshold: 0,
    },
  );

  let scrollUpdateQueued = false;
  const requestActiveSectionUpdate = () => {
    if (scrollUpdateQueued) return;

    scrollUpdateQueued = true;
    window.requestAnimationFrame(() => {
      scrollUpdateQueued = false;
      updateActiveSection();
    });
  };

  sections.forEach(({ element }) => observer.observe(element));
  window.addEventListener('scroll', requestActiveSectionUpdate, { passive: true });
  window.addEventListener('resize', requestActiveSectionUpdate);
  window.addEventListener('hashchange', requestActiveSectionUpdate);
  updateActiveSection();
});
