(() => {
  document.documentElement.classList.add("js");

  // Mobile navigation drawer
  const nav = document.querySelector("[data-nav]");
  const openBtn = document.querySelector("[data-nav-toggle]");
  const closeBtn = document.querySelector("[data-nav-close]");
  const backdrop = document.querySelector(".nav-backdrop");
  let inerted = [];

  // While the drawer is open, everything outside it is inert, so Tab and screen readers stay inside.
  // The backdrop is left alone so a click outside still closes the drawer.
  const setOutsideInert = (on) => {
    if (!on) {
      inerted.forEach((el) => (el.inert = false));
      inerted = [];
      return;
    }
    for (let el = nav; el.parentElement && el !== document.body; el = el.parentElement) {
      for (const sibling of el.parentElement.children) {
        if (sibling === el || sibling === backdrop || sibling.inert || sibling.tagName === "SCRIPT") continue;
        sibling.inert = true;
        inerted.push(sibling);
      }
    }
  };
  const isOpen = () => nav?.classList.contains("is-open");

  const setNav = (open) => {
    if (!nav) return;
    nav.classList.toggle("is-open", open);
    document.body.classList.toggle("nav-open", open);
    openBtn?.setAttribute("aria-expanded", String(open));
    setOutsideInert(open); // release before focusing the toggle, which sits outside the drawer
    if (open) closeBtn?.focus();
    else openBtn?.focus({ preventScroll: true });
  };
  openBtn?.addEventListener("click", () => setNav(true));
  closeBtn?.addEventListener("click", () => setNav(false));
  backdrop?.addEventListener("click", () => setNav(false));
  document.addEventListener("keydown", (e) => {
    if (!isOpen()) return;
    if (e.key === "Escape") return setNav(false);
    if (e.key !== "Tab") return;
    // Wrap Tab / Shift+Tab around the drawer's own links and buttons.
    const items = [...nav.querySelectorAll("a[href], button:not([disabled])")].filter((el) => el.getClientRects().length);
    const first = items[0], last = items[items.length - 1];
    if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
    else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
  });
  // Widening past the drawer breakpoint (e.g. rotating a tablet) must not leave the page inert.
  window.matchMedia("(max-width: 1200px)").addEventListener("change", (e) => {
    if (!e.matches && isOpen()) setNav(false);
  });
  nav?.querySelectorAll("a").forEach((a) =>
    a.addEventListener("click", () => nav.classList.contains("is-open") && setNav(false))
  );

  // Header shadow once the page scrolls
  const header = document.querySelector("[data-header]");
  const onScroll = () => header?.classList.toggle("is-scrolled", window.scrollY > 8);
  onScroll();
  window.addEventListener("scroll", onScroll, { passive: true });

  // Reveal on scroll
  const reveal = document.querySelectorAll("[data-reveal]");
  // If this script arrived after the CSS failsafe (2s) already showed everything, don't hide it again.
  const arrivedLate = performance.now() > 1900;
  if (!arrivedLate && "IntersectionObserver" in window) {
    const io = new IntersectionObserver(
      (entries) => entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-in");
          io.unobserve(entry.target);
        }
      }),
      { rootMargin: "0px 0px -8% 0px", threshold: 0.08 }
    );
    reveal.forEach((el) => io.observe(el));
  } else {
    reveal.forEach((el) => el.classList.add("is-in"));
  }
  document.documentElement.classList.add("reveal-ready");

  // Programme filters
  const filters = document.querySelectorAll("[data-filter]");
  const cards = document.querySelectorAll("[data-school]");
  filters.forEach((btn) =>
    btn.addEventListener("click", () => {
      const value = btn.dataset.filter;
      filters.forEach((b) => b.setAttribute("aria-pressed", String(b === btn)));
      cards.forEach((card) => {
        card.hidden = value !== "all" && !card.dataset.school.split(" ").includes(value);
      });
    })
  );

  // Gallery lightbox
  const lightbox = document.querySelector("[data-lightbox]");
  if (lightbox && typeof lightbox.showModal === "function") {
    const img = lightbox.querySelector("img");
    const caption = lightbox.querySelector("p");
    document.querySelectorAll("[data-zoom]").forEach((btn) =>
      btn.addEventListener("click", () => {
        const source = btn.querySelector("img");
        img.src = source.currentSrc || source.src;
        img.alt = source.alt;
        caption.textContent = btn.dataset.zoom;
        lightbox.showModal();
      })
    );
    lightbox.querySelector("[data-lightbox-close]").addEventListener("click", () => lightbox.close());
    lightbox.addEventListener("click", (e) => { if (e.target === lightbox) lightbox.close(); });
  }

  // Admission enquiry: no backend on a static site, so compose an email to the admissions office.
  document.querySelectorAll("[data-enquiry]").forEach((form) =>
    form.addEventListener("submit", (e) => {
      e.preventDefault();
      if (!form.reportValidity()) return;
      const data = new FormData(form);
      const subject = `Admission enquiry: ${data.get("programme")}`;
      const body = [
        `Name: ${data.get("name")}`,
        `Phone: ${data.get("phone")}`,
        `Email: ${data.get("email") || "-"}`,
        `Programme: ${data.get("programme")}`,
        "",
        data.get("message") || "",
      ].join("\n");
      window.location.href = `mailto:info@madhaarts.in?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
      const status = form.querySelector(".form-status");
      if (status) {
        status.hidden = false;
        status.textContent = "Thank you. Your email app should open with the enquiry ready to send. You can also call +91 81818 15379.";
      }
    })
  );

  document.querySelectorAll("[data-year]").forEach((el) => (el.textContent = new Date().getFullYear()));
})();
