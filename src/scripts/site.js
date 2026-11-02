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
  const years = qsa("[data-publication-year]");
  const yearLinks = qsa("[data-year-link]");
  const count = qs("[data-publication-count]");
  const status = qs("[data-topic-status]");
  const toggle = qs("[data-topic-toggle]");
  const panel = qs("[data-topic-panel]");
  const chips = panel ? qsa("[data-topic]", panel) : [];

  // Text query and topic are kept in the URL (?q=…&topic=…) so a filtered view can be shared.
  const params = new URLSearchParams(window.location.search);
  let topic = params.get("topic") || "";
  if (params.get("q")) input.value = params.get("q");

  const update = () => {
    const query = input.value.trim().toLowerCase();
    let visible = 0;
    rows.forEach((row) => {
      const topics = (row.dataset.topics || "").split(" ");
      const matches = (!query || row.dataset.search.includes(query)) && (!topic || topics.includes(topic));
      row.hidden = !matches;
      if (matches) visible += 1;
    });
    years.forEach((section) => {
      const shown = qsa("[data-publication-row]", section).filter((row) => !row.hidden).length;
      section.hidden = shown === 0;
      const link = yearLinks.find((item) => item.dataset.yearLink === section.dataset.publicationYear);
      if (link) link.hidden = shown === 0;
      const yearCount = qs("[data-year-count]", section);
      if (yearCount) yearCount.textContent = `${shown} reference${shown === 1 ? "" : "s"}`;
    });
    if (count) count.textContent = `${visible} reference${visible === 1 ? "" : "s"}`;
    let activeLabel = "";
    chips.forEach((chip) => {
      const active = chip.dataset.topic === topic;
      chip.setAttribute("aria-pressed", active ? "true" : "false");
      if (active && topic) activeLabel = chip.dataset.topicLabel || topic;
    });
    if (status) status.textContent = activeLabel ? ` · Topic: ${activeLabel}` : "";
    const url = new URL(window.location.href);
    if (query) url.searchParams.set("q", input.value.trim());
    else url.searchParams.delete("q");
    if (topic) url.searchParams.set("topic", topic);
    else url.searchParams.delete("topic");
    window.history.replaceState({}, "", url);
  };

  input.addEventListener("input", update);
  if (toggle && panel) {
    toggle.addEventListener("click", () => {
      const open = panel.hidden;
      panel.hidden = !open;
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
    if (topic) {
      panel.hidden = false;
      toggle.setAttribute("aria-expanded", "true");
    }
  }
  chips.forEach((chip) =>
    chip.addEventListener("click", () => {
      topic = chip.dataset.topic === topic ? "" : chip.dataset.topic;
      update();
    })
  );
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

setupNavigation();
setupPeopleFilter();
setupPublicationFilter();
setupSearchPage();
