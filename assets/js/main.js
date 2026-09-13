(() => {
  document.documentElement.classList.add("js");

  // Mobile navigation drawer
  const nav = document.querySelector("[data-nav]");
  const openBtn = document.querySelector("[data-nav-toggle]");
  const closeBtn = document.querySelector("[data-nav-close]");
  const backdrop = document.querySelector(".nav-backdrop");

  const setNav = (open) => {
    if (!nav) return;
    nav.classList.toggle("is-open", open);
    document.body.classList.toggle("nav-open", open);
    openBtn?.setAttribute("aria-expanded", String(open));
    if (open) closeBtn?.focus();
    else openBtn?.focus({ preventScroll: true });
  };
  openBtn?.addEventListener("click", () => setNav(true));
  closeBtn?.addEventListener("click", () => setNav(false));
  backdrop?.addEventListener("click", () => setNav(false));
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && nav?.classList.contains("is-open")) setNav(false);
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
  if ("IntersectionObserver" in window) {
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
