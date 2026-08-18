---
title: Memex — vault system
created: 2026-08-18
updated: 2026-08-18
tags: [memex, technical, decision-record]
status: active
---

# Memex — vault system

## What this is

A personal knowledge vault: research, project history, and decisions kept as plain
markdown in a private Git repo, edited in Obsidian, and published read-only to a
password-protected corner of funbyus so it's reachable while travelling and readable
by an agent that isn't running locally.

## Current state

Repo created. Scaffold committed, then extended with `sources/`, config-driven structure, and lint. Server-side password protection and GitHub secrets
still to configure before the first successful deploy.

## Key findings

- Obsidian is a reading/editing layer over plain files, not a storage format — so
  there's no lock-in and nothing to migrate if it's abandoned later.
- Obsidian mobile on iOS has no native Git. Bridging it requires Working Copy or a
  paid Obsidian Sync subscription.
- A published static site can't serve as an Obsidian mobile source — Obsidian needs
  local files, not a URL. Reading and editing on mobile are separate problems.
- Publishing raw `.md` alongside rendered `.html` makes the site directly consumable
  by agents as well as humans, at no extra cost.

## Decisions

| Date | Decision | Why | Rejected alternatives |
|---|---|---|---|
| 2026-08-18 | Private GitHub repo as source of truth | Sync, version history, and agent access in one thing already used daily | Obsidian Sync as primary; hosting as primary |
| 2026-08-18 | Obsidian as editing layer only | Links, graph, and search without owning the data | Notion — API-gated, not plain files |
| 2026-08-18 | Publish to funbyus via GitHub Actions on push | Read access anywhere without exposing the repo | Manual FTP upload; GitHub Pages |
| 2026-08-18 | Mobile is read-only via the website | Editing on the road will happen through an agent that commits, not by hand | Working Copy; paid Obsidian Sync |
| 2026-08-18 | One note per topic, append dated sections | Prevents fragmentation across many short conversations | One note per conversation |
| 2026-08-18 | Archive artifact **plus** companion summary | Artifact holds the *what*, summary holds the *why* — rejected options and reasoning | Verbatim conversation transcripts |
| 2026-08-18 | Repo named `memex` | Vannevar Bush, 1945 — the direct ancestor of this idea | `trailhead` (kept in reserve), `vault`, `commonplace`, `mentat` |
| 2026-08-18 | One vault, not two | Splitting clippings from notes breaks the links that make the vault worth having; Obsidian opens one vault at a time | Separate vault for web clippings |
| 2026-08-18 | Structure declared in `memex.config.yml` | Adding a section shouldn't mean editing the build script | Hardcoded folder list in `build.py` |
| 2026-08-18 | `sources/` immutable and local-only | Fixed points can be safely cited; full-text captures of others' writing shouldn't be published | Editable captures; publishing sources behind auth |
| 2026-08-18 | Sources must be cited to count | An uncited capture is a reading pile, not a knowledge base | Keep everything, sort it out later |
| 2026-08-18 | Lint split into mechanical and content | A script can prove broken links; only a reader can spot contradictions | Single lint command doing both |
| 2026-08-18 | Good answers become notes | The vault should grow from questions asked, not only material saved | Answers stay in chat |

## Open questions

- [ ] Create subdomain or folder on Hosting.com and enable Directory Privacy
- [ ] Create a scoped FTP account, add the four GitHub secrets
- [ ] First push, confirm Actions run succeeds
- [ ] Backfill: pick 5–6 conversations worth keeping (health research, Wisconsin trip,
      sb2 multi-archive design, Michigan civics, marker app dataset)
- [ ] Decide whether Obsidian Git plugin is worth it vs. committing from the terminal
- [ ] Test whether an agent can authenticate through basic auth to fetch `search.json`
- [ ] Set up Obsidian Web Clipper pointed at `sources/` with the source template
- [ ] Run the first content lint once there's enough material to contradict itself

## Sources

- [Karpathy — llm-wiki (idea file)](../sources/2026-08-18-karpathy-llm-wiki.md) —
  the pattern this vault descends from. Captured 2026-08-18.
- [Obsidian Git plugin](https://github.com/Vinzent03/obsidian-git) — community plugin,
  auto-commit on a timer.
- [FTP-Deploy-Action](https://github.com/SamKirkland/FTP-Deploy-Action) — the Action
  used in `.github/workflows/deploy.yml`.
- Vannevar Bush, *As We May Think*, The Atlantic, July 1945 — origin of "memex".

## Artifacts

- [`../CLAUDE.md`](../CLAUDE.md) — agent instructions, including the "archive this" workflow.
- [`../build.py`](../build.py) — markdown → static site build.
- [`../.github/workflows/deploy.yml`](../.github/workflows/deploy.yml) — deploy on push.
- [`../templates/topic-note.md`](../templates/topic-note.md) — the standard note shape.
- [`../templates/source-note.md`](../templates/source-note.md) — shape for raw captures.
- [`../templates/answer-note.md`](../templates/answer-note.md) — shape for question-derived notes.
- [`../memex.config.yml`](../memex.config.yml) — section definitions and publish rules.

---

## Log

### 2026-08-18

Worked out the whole architecture in one sitting. Started from the question of how to
keep research accessible outside of Claude conversations, and landed on Git-as-truth
with Obsidian and a published site as two different doors onto the same files.

The clarifying insight was separating reading from editing on mobile — once editing is
delegated to an agent that commits, the phone only ever needs a read-only URL, which
removes the entire Working Copy / Obsidian Sync question.

Repo scaffolded with folder structure, note template, `CLAUDE.md`, tag list, build
script, and deploy workflow.

Then reworked it twice in the same session. First, the question of where non-conversation
material goes — web clippings and the like. Landed on one vault with a role-based split
rather than a second archive: `sources/` for input, `research/` for synthesis. Structure
moved out of `build.py` and into `memex.config.yml` at the same time, so future sections
are a config entry rather than a code change.

Second, after reading Karpathy's llm-wiki gist, three of its ideas were folded in — they
turned out to sharpen conventions this vault had already half-committed to. Sources became
immutable and hash-sealed. Lint became a named operation, split into what a script can
prove and what only a reader can spot. And answers to good questions now become notes in
their own right, so the vault grows from what gets asked, not only what gets saved.

Next session: server config and the first deploy.
