const qs = (selector, scope = document) => scope.querySelector(selector);
const qsa = (selector, scope = document) => Array.from(scope.querySelectorAll(selector));

// Site URL prefix (e.g. "/sccn_site2" on GitHub Pages project hosting),
// derived from this script's own src so it works baked or unbaked.
const BASE = (qs('script[src$="assets-site.js"]')?.getAttribute("src") || "")
  .replace(/\/assets-site\.js$/, "");

function setupNavigation() {
  const navToggle = qs("[data-nav-toggle]");
  const nav = qs("[data-primary-nav]");
  if (navToggle && nav) {
    navToggle.addEventListener("click", () => {
      const isOpen = nav.classList.toggle("is-open");
      navToggle.setAttribute("aria-expanded", String(isOpen));
    });
  }

  const search = qs("[data-header-search]");
  const searchButton = qs("[data-search-toggle]");
  const searchInput = qs("[data-search-input]");
  if (search && searchButton && searchInput) {
    const closeSearch = () => {
      search.classList.remove("is-open");
      searchButton.setAttribute("aria-expanded", "false");
      searchInput.value = searchInput.value.trim();
    };

    searchButton.addEventListener("click", () => {
      const isOpen = search.classList.toggle("is-open");
      searchButton.setAttribute("aria-expanded", String(isOpen));
      if (isOpen) {
        window.setTimeout(() => searchInput.focus(), 30);
      }
    });

    searchInput.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        event.preventDefault();
        closeSearch();
        searchButton.focus();
      }
    });
  }
}

function setupPeopleFilter() {
  const input = qs("[data-people-search]");
  if (!input) return;
  const cards = qsa("[data-person-card]");
  const count = qs("[data-people-count]");
  const update = () => {
    const query = input.value.trim().toLowerCase();
    let visible = 0;
    cards.forEach((card) => {
      const matches = !query || card.dataset.search.includes(query);
      card.hidden = !matches;
      if (matches) visible += 1;
    });
    if (count) count.textContent = `${visible} shown`;
  };
  input.addEventListener("input", update);
  update();
}

function setupPublicationFilter() {
  const input = qs("[data-publication-search]");
  if (!input) return;
  const rows = qsa("[data-publication-row]");
  const count = qs("[data-publication-count]");
  const update = () => {
    const query = input.value.trim().toLowerCase();
    let visible = 0;
    rows.forEach((row) => {
      const matches = !query || row.dataset.search.includes(query);
      row.hidden = !matches;
      if (matches) visible += 1;
    });
    if (count) count.textContent = `${visible} references`;
  };
  input.addEventListener("input", update);
  update();
}

async function setupSearchPage() {
  const results = qs("[data-search-results]");
  if (!results) return;
  const form = qs("[data-site-search-form]");
  const input = qs("[data-site-search-input]");
  const params = new URLSearchParams(window.location.search);
  const initialQuery = params.get("q") || "";
  input.value = initialQuery;

  let index = [];
  try {
    const response = await fetch(`${BASE}/search-index.json`, { cache: "no-store" });
    index = await response.json();
  } catch {
    results.innerHTML = "<p>Search index is unavailable.</p>";
    return;
  }

  const render = (query) => {
    const terms = query.trim().toLowerCase().split(/\s+/).filter(Boolean);
    if (!terms.length) {
      results.innerHTML = "<p>Enter a search term to search the SCCN site.</p>";
      return;
    }
    const matches = index
      .map((item) => {
        const haystack = `${item.title} ${item.text}`.toLowerCase();
        const score = terms.reduce((sum, term) => sum + (haystack.includes(term) ? 1 : 0), 0);
        return { item, score };
      })
      .filter(({ score }) => score > 0)
      .sort((a, b) => b.score - a.score)
      .slice(0, 40);

    if (!matches.length) {
      results.innerHTML = "<p>No matches found.</p>";
      return;
    }

    results.innerHTML = matches
      .map(({ item }) => `
        <article class="legacy-card">
          <h3><a href="${BASE}${item.url}">${item.title}</a></h3>
          <p>${item.excerpt}</p>
        </article>
      `)
      .join("");
  };

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const query = input.value.trim();
    const url = query ? `${BASE}/search/?q=${encodeURIComponent(query)}` : `${BASE}/search/`;
    window.history.replaceState({}, "", url);
    render(query);
  });

  render(initialQuery);
}

function setupCarousel() {
  const carousel = qs("[data-carousel]");
  if (!carousel) return;
  const slides = qsa("[data-carousel-slide]", carousel);
  if (slides.length < 2) return;
  const track = qs("[data-carousel-track]", carousel);
  const dots = qsa("[data-carousel-dot]", carousel);
  const toggle = qs("[data-carousel-toggle]", carousel);
  const ROTATE_MS = 6000;
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  let current = Math.max(0, slides.findIndex((slide) => slide.classList.contains("is-active")));
  let timer = null;
  let stopped = reduceMotion; // user-controlled (pause button, or OS reduced-motion preference)
  let hovering = false;
  let focused = false;

  const show = (index) => {
    current = (index + slides.length) % slides.length;
    slides.forEach((slide, i) => {
      const active = i === current;
      slide.classList.toggle("is-active", active);
      slide.setAttribute("aria-hidden", active ? "false" : "true");
      qsa("a", slide).forEach((link) => link.setAttribute("tabindex", active ? "0" : "-1"));
    });
    dots.forEach((dot, i) => {
      if (i === current) dot.setAttribute("aria-current", "true");
      else dot.removeAttribute("aria-current");
    });
  };

  const halt = () => {
    if (timer) clearInterval(timer);
    timer = null;
  };
  const schedule = () => {
    halt();
    if (stopped || hovering || focused || document.hidden) return;
    timer = setInterval(() => show(current + 1), ROTATE_MS);
  };
  const syncToggle = () => {
    carousel.classList.toggle("is-paused", stopped);
    if (toggle) {
      toggle.setAttribute("aria-label", stopped ? "Start automatic slide rotation" : "Stop automatic slide rotation");
    }
    // Announce slide changes only when the user is driving the carousel.
    if (track) track.setAttribute("aria-live", stopped ? "polite" : "off");
  };

  qs("[data-carousel-prev]", carousel)?.addEventListener("click", () => {
    show(current - 1);
    schedule();
  });
  qs("[data-carousel-next]", carousel)?.addEventListener("click", () => {
    show(current + 1);
    schedule();
  });
  dots.forEach((dot, i) =>
    dot.addEventListener("click", () => {
      show(i);
      schedule();
    })
  );
  toggle?.addEventListener("click", () => {
    stopped = !stopped;
    syncToggle();
    schedule();
  });
  carousel.addEventListener("mouseenter", () => {
    hovering = true;
    halt();
  });
  carousel.addEventListener("mouseleave", () => {
    hovering = false;
    schedule();
  });
  carousel.addEventListener("focusin", () => {
    focused = true;
    halt();
  });
  carousel.addEventListener("focusout", (event) => {
    if (carousel.contains(event.relatedTarget)) return;
    focused = false;
    schedule();
  });
  carousel.addEventListener("keydown", (event) => {
    if (event.key === "ArrowLeft") {
      event.preventDefault();
      show(current - 1);
    } else if (event.key === "ArrowRight") {
      event.preventDefault();
      show(current + 1);
    }
  });
  document.addEventListener("visibilitychange", schedule);

  carousel.classList.add("is-ready");
  show(current);
  syncToggle();
  schedule();
}

setupNavigation();
setupPeopleFilter();
setupPublicationFilter();
setupSearchPage();
setupCarousel();
