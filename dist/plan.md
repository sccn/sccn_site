# SCCN Website — Proposed Restructure (Plan)

Status: **planning only** — no files changed yet.
Date: 2026-07-03

Goal: modernize the information architecture of the SCCN site so it reads like a
current research-lab site: a small, flat top menu; obsolete pages removed; EEGLAB
delegated to `eeglab.org`; News and Events unified with only upcoming/recent items
public and the long tail archived behind an intranet login.

---

## 1. Design principles

- **Flat, small top nav** — 6 primary items max; avoid deep dropdowns.
- **One canonical home for each topic** — no duplicate/legacy pages competing.
- **Delegate, don't duplicate** — EEGLAB lives at `eeglab.org`; we link, not mirror.
- **Time-aware content** — events/news surface what's current; history is archived,
  not deleted.
- **Public vs. internal split** — outward-facing pages public; operational/historical
  material behind an intranet login.
- **No dead ends** — every retired URL 301-redirects to its new home (SEO + old links).

---

## 2. Proposed top-level navigation

```
Home
Research ▾
    ├─ Overview            (was: About → Vision)
    ├─ Projects
    ├─ Publications        (Abstracts folded in as a section)
    └─ MoBI Lab            → /facilities/mobi.php (public; rest of Facilities gated under Login)
Tools ▾                    (parent link → /tools/ ecosystem overview)
    ├─ EEGLAB             → /tools/#eeglab   (on-site summary + Visit ↗ eeglab.org)
    ├─ EEGPrep            → /tools/#eegprep  (summary + Visit ↗)
    ├─ NEMAR              → /tools/#nemar    (summary + Visit ↗ nemar.org)
    ├─ EEGDash            → /tools/#eegdash  (summary + Visit ↗)
    └─ HED                → /tools/#hed      (summary + Visit ↗ hedtags.org)
People ▾
    ├─ Current members
    └─ Alumni              (was: people/former.html)
News & Events             (merged; upcoming + recent highlighted)
Visit                     (public directions + map; page at /visit/)

Utility (top-right + footer):  Login   (was: Intranet)
Footer:                         Contact info (address, phone) + Visit link — see 3.5
```

Order: **Tools comes immediately after Research** (grouping "what we study" with
"what we build"). The standalone **EEGLAB** menu item is removed — EEGLAB is now one
entry under Tools.

Rationale:
- "About" as a label is vague; the lab's identity is its **Research**, **Tools**, and
  **People**. Vision/mission becomes *Research → Overview*.
- **Facilities** moves under Research (research infrastructure), freeing a slot.
- **Abstracts** becomes a section inside Publications, not a peer.
- **Tools** consolidates all externally-hosted SCCN software/data platforms behind one
  menu; each item is an external link (new tab, external-link icon).
- **Contact** is demoted from a nav item to footer info (see 3.5).

---

## 3. Section-by-section changes

### 3.1 Research (new grouping)
| New page | Source today | Change |
|----------|--------------|--------|
| Research → Overview | `/about` (`about.html`, title "Vision") | Rename "Vision" → "Overview"; keep mission/vision content. |
| Research → Projects | `/projects` (`projects.html`) | Keep. Consider theme-based grouping later. |
| Research → Publications | `/publications` (`publications.html`) | Keep as canonical list. |
| Research → Publications (Abstracts tab) | `/abstracts` (`abstracts.html`) | Merge into Publications as a "Conference abstracts" section; retire standalone menu item. |
| Research → MoBI Lab | `/facilities/mobi.php` | ✅ **DONE.** Facilities is now **internal**: the entire `/facilities` section is gated behind Login **except the MoBI lab** (public showcase) and the shared `/facilities/images/` (so MoBI's photos load). The Research menu item was relabeled **"Facilities" → "MoBI Lab"** (→ `/facilities/mobi.php`) across all 107 pages; the full gated Facilities index is linked from the Login landing. Implemented via `access.conf`: `gated_prefixes:["/facilities"]`, `allow_prefixes:["/facilities/mobi","/facilities/images"]`. |

### 3.2 People
| New page | Source today | Change |
|----------|--------------|--------|
| People → Current | `/people` (`people/index.html`) | Keep. |
| People → Alumni | `people/former.html` | Promote to a clear "Alumni" sub-item. |

### 3.3 News & Events (MERGED) — key change
Merge `/news/` and `/events/` into a single **News & Events** section with one
reverse-chronological feed and a clear time policy.

**Public landing shows:**
- **Upcoming** — any event dated ≥ today (currently none; most recent is 2025-11-19).
- **Recent** — news items and past events from a rolling window (proposed: last
  **18 months**). Tunable.

**Archived (moved behind Login):** every event **not shown in the current public
News & Events tab** lives in the Login archive.
- All older event microsites and dated pages:
  - `events/`: `sloan-swartz-2007`, `sloan-swartz-2012`,
    `BrainConnectivityWorkshop2015`, `cta`, `headit`, and the dated folders
    2001–2010 (`2001-11-16` … `2010-03-04`).
  - `news/`: dated folders older than the rolling window
    (`2001-11-16`, `2010-03-03`, `2011-05-16`, `2012-01-27`, `2012-02-23`, …).
- Rule of thumb: **public = upcoming + last 18 months; everything older = intranet archive.**

**Data model (proposed):** a single list of entries `{date, type: news|event,
title, blurb, link, visibility: public|intranet}` driving the landing page, so the
18-month window is a query, not a manual edit.

### 3.4 Tools — on-site summaries of the SCCN ecosystem (replaces EEGLAB menu)
Replace the old EEGLAB dropdown with a **Tools** menu covering SCCN's software and data
platforms. The standalone top-level **EEGLAB** menu is removed — EEGLAB becomes one
Tools entry.

**Decision: keep a short summary layer on-site rather than linking straight out.**
A pure-external menu would make the lab site a thin launcher and lose the story that
these are one integrated SCCN ecosystem. Instead:

- A **Tools landing page** (`/tools/`): 1-paragraph ecosystem intro + a card per tool
  (logo, 1–2 sentence summary, prominent **"Visit ↗"** button to the tool's own site).
- Each tool has a **brief on-site summary** (anchored section on `/tools/`, or its own
  short page): what it is (2–3 sentences), screenshot/logo, 3–5 capability bullets, how
  it fits the others, canonical citation, and the external CTA.
- Dropdown items link to the **on-site summary**; the external jump is the CTA button,
  not the menu.
- We **summarize, never re-mirror** — full content always lives on each tool's own site
  (consistent with "EEGLAB content moved to eeglab.org").
- Maintenance: ~1 landing page + 5 short, rarely-changing sections.

| Tool | External site (confirm) | On-site summary covers |
|------|-------------------------|------------------------|
| EEGLAB | https://eeglab.org | EEG analysis toolbox; content already migrated off this site. |
| EEGPrep | (confirm URL) | EEG preprocessing pipeline. |
| NEMAR | https://nemar.org | Open EEG/MEG/iEEG data archive + compute. |
| EEGDash | (confirm URL) | EEG data access / dashboard. |
| HED | https://www.hedtags.org | Hierarchical Event Descriptors annotation standard. |

Retire and 301-redirect the local EEGLAB pages (full content now on eeglab.org):
| Old URL | Redirect target |
|---------|-----------------|
| `/eeglab/`, `/eeglab/index.php` | https://eeglab.org |
| `/eeglab/ressources.php` | https://eeglab.org (requirements page) |
| `/eeglab/download.php` | https://eeglab.org/download |
| `/wiki/EEGLAB`, `#EEGLAB_Workshops`, `#..Tutorial_Outline` | eeglab.org docs/workshops/tutorial |
| `/eeglab/EEGLAB_Newsletter.php` | eeglab.org newsletter (or retire) |

(Exact deep-link URLs for each tool to be confirmed — see Open Questions.)

### 3.5 Contact — do we need it? (recommendation: footer only)
A research lab does **not** need Contact as a top-level menu item. Modern lab sites put
contact essentials in the **footer** (and optionally on Research → Overview): postal
address, general email, map/directions, social links.

- **Remove the contact form** (`/contact/form.php`) — obsolete; email suffices and a
  form needs a live backend the static site can't provide.
- **Remove the Contact nav item**; move its info to the site-wide footer.
- The map + driving/parking/airport **directions** (the genuinely public part of the
  old contact page) now live at a public **`/visit/`** page, reachable from a top-nav
  **Visit** item and the footer.
- 301 `/contact`, `/contact/*` (incl. `form.php`) → **`/visit/`**.
- ✅ Done. Also: the **Facilities dropdown button** was removed from the (public) MoBI
  lab page, since it linked to the now-gated facility sub-pages.

### 3.6 Login (password-gated area, was "Intranet")
Menu label: **Login**. A password-gated area for internal + historical material. Scope:
- Full **events archive** — **every event not shown in the current public News &
  Events tab** (all pre-window microsites; see 3.3).
- Internal **facilities**: the whole `/facilities` section (main page, CES Lab, Floor
  Plan, SCCN Meeting Room & Library, INC Conference Room, Computing). **Only the MoBI
  lab** (`/facilities/mobi.php`) and shared `/facilities/images/` stay public.
- Any internal wiki content under `/wiki/` not meant to be public.

**Credentials (as specified):** username `sccn`, password `sccn` — a single shared
login via HTTP basic-auth (reverse-proxy / host `.htpasswd`).

Placement: top-right utility link ("Login") + footer.

> Note: a shared, guessable credential is **soft gating only** — it declutters the
> public site, it is not real access control. Acceptable here because the gated
> content is historical, already-public event pages. Do **not** put anything sensitive
> behind it, and store the credential in server config (`.htpasswd` / env) — **not** in
> any file inside the served docroot (this `plan.md` included).

---

## 4. Old → New URL map (redirects to implement)

| Old | New / Target | Type |
|-----|--------------|------|
| `/about` | `/research/overview` (or keep `/about`, relabel) | rename |
| `/facilities` | `/research/facilities` | move |
| `/abstracts` | `/publications#abstracts` | merge |
| `/projects`, `/publications`, `/people` | unchanged (regrouped in menu only) | — |
| `/news/`, `/events/` | `/news-events/` | merge |
| old event/news microsites | `/intranet/archive/…` | gate |
| `/eeglab/*`, `/wiki/EEGLAB*` | `https://eeglab.org/*` | external 301 (now under Tools) |
| `/contact/`, `/contact/index.php`, `/contact/form.php` | `/` (footer contact) | retire |

Keep redirects so external inbound links and search results don't 404.

---

## 5. Site-wide modernization notes (out of menu scope, for later)

- Front-end stack is dated (Bootstrap 4 + jQuery + flexslider + popper). A modern
  rebuild would drop jQuery/flexslider; but that is a separate effort from IA.
- Consider a static-site generator (the content is nearly all static) so the
  news/events feed, redirects, and intranet gating are config-driven rather than
  hand-maintained HTML.
- Homepage: lead with mission + current research highlights + latest news, and a
  prominent EEGLAB → eeglab.org call-to-action.

---

## 6. Open questions (need user decision before implementation)

1. **Recent window**: is 18 months the right public cutoff for news/events? (12 / 24?)
2. **Abstracts**: fold into Publications (proposed) or drop entirely if superseded?
3. **Facilities**: public showcase (MoBI, CES labs) under Research; internal pages
   (Floor Plan, Meeting Room, INC Conference Room, **Computing** — decided internal) →
   Login. Remaining: drop the public section entirely if MoBI/CES content is stale?
4. **Login auth mechanism**: RESOLVED — shared HTTP basic-auth, user `sccn` / pass
   `sccn`. (Upgrade to per-user creds or UCSD SSO later if the area ever holds
   sensitive material.)
5. **Tools URLs**: confirm canonical links for **EEGPrep** and **EEGDash** (EEGLAB =
   eeglab.org, NEMAR = nemar.org, HED = hedtags.org assumed); plus eeglab.org deep
   links for the redirects.
5b. **Tools summary format**: anchored sections on one `/tools/` page (proposed) vs. a
   short separate page per tool? Both keep the summary on-site.
6. **Contact**: drop the page entirely and keep only footer info (recommended), or keep
   a minimal footer-linked `/contact/` page?
7. **Keep `/about` label** or rename to `/research/overview`? (redirect either way)
8. Legacy standalone pages (`nft.html`, `science2002.html`, `VisionOverview.html`,
   `sloan-swartz-2007/`) — archive to Login area, redirect, or keep public?

---

## 7. Suggested implementation phases (when approved)

1. **Menu + labels** — ✅ **DONE.** New top nav (Research / Tools / People /
   News & Events / Login) applied to all 103 pages; standalone EEGLAB & Contact
   dropdowns and the Abstracts item removed. Minimal stub pages created for
   `/tools/`, `/news-events/`, `/login/` so no menu target 404s. Interim link
   targets pending later phases: Tools → `/tools/#anchor` (summaries = Phase 3;
   EEGPrep & EEGDash external URLs still TBD, see Q5); News & Events → `/news-events/`
   stub links to `/news/` + `/events/` (merge = Phase 2); Login → placeholder
   (auth = Phase 5).
2. **Merge News & Events** — ✅ **DONE.** Parsed the two curated index pages into one
   dated feed (45 entries). Generated public `/news-events/` (interleaved Upcoming +
   Recent) and gated `/login/archive/` (older items, grouped by year), linked from
   `/login/`. Window = 18 mo (cutoff 2025-01-03) yields only 1 in-window item given
   stale content, so a `MIN_RECENT = 6` floor governs the public feed (6 recent, 39
   archived). Both constants tunable (Q1). NOT done here: physically relocating the
   detail folders and gating them (that is Phase 5); `/news/` + `/events/` still exist
   and are redirected in Phase 6.
3. **Tools menu** — ✅ **DONE.** `/tools/` rebuilt with per-tool summaries + "Visit ↗"
   CTAs. EEGLAB / NEMAR / HED linked (eeglab.org / nemar.org / hedtags.org); EEGPrep &
   EEGDash summaries + links marked "to confirm" (still need URLs, Q5 — not fabricated).
   EEGLAB 301s added in `serve.py`: `/eeglab`, `/eeglab/`, `/eeglab.html`, `/eeglab/*`,
   `/wiki/EEGLAB` → eeglab.org (verified; other `/wiki/*` untouched).
4. **Contact** — ✅ **DONE.** `/contact`, `/contact/*` (incl. `form.php`) 301 → `/`.
   Site-wide footer injected into 107 nav-bearing pages with the real contact info
   pulled from the old page (address 9500 Gilman Dr # 0559; Office 858-822-7534; Fax
   858-822-7556). No email existed on the site, so none was invented.
5. **Login area** — ✅ **DONE.** HTTP basic-auth (`sccn`/`sccn`, env-overridable) gates
   `/login/*` **and** the 23 archived detail pages (derived from the archive listing so
   the set never drifts) — no folder relocation needed, so nothing broke. `serve.py`
   and `plan.md` are now blocked from being served (404) so the credential/notes can't
   leak over HTTP. Recent public detail pages stay open. Verified.
6. **Redirects + QA** — ✅ **DONE.** Added `/news`, `/news/`, `/events`, `/events/`
   → `/news-events/` 301s (index only; detail pages stay public/gated). Kept
   `/about`, `/facilities`, `/projects`, `/publications`, `/people` URLs as-is
   (Research is a menu grouping — resolves Q6/Q7); `/abstracts` left reachable but
   unlinked, pending the Q2 content merge. Also redirected stray EEGLAB doc paths
   (`/tutorials`, `/workshops`, `/plugins`, `/others`) → eeglab.org.
   **QA crawl** (authenticated, 682 URLs): **0 restructure-introduced breakages**;
   all restructure pages return 200. Broken links fell 276 → **57**, and every one of
   the 57 is a PRE-EXISTING gap in the partial wget mirror (un-downloaded PDFs under
   `/papers` (23) and `/events` (13), a jekyll theme's `/assets` (4), and misc stray
   old links) — none on the new pages, none caused by the restructure. Fixing them
   would require obtaining the original files (out of scope).
