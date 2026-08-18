# Memex — Agent Instructions

Brent's personal knowledge vault. Plain markdown, version-controlled, read in Obsidian
and published read-only to a password-protected site.

The wiki is the product; the chat is just the interface. A conversation that ends
without changing a file has produced nothing.

---

## Before you write anything

1. **Read `memex.config.yml`.** It is the authoritative definition of the vault —
   which sections exist, what they're for, which get published, which are immutable.
   If this file and the config disagree, the config wins.
2. **List what's already here.** `python build.py --check` prints a full inventory
   alongside every structural problem. Do this before deciding where content goes.
3. **Prefer appending over creating.** The failure mode is fragmentation — forty
   half-notes on one topic. Append a dated section to an existing note unless the
   material is genuinely new territory.
4. **One note per topic, never one per conversation.** A single conversation may
   update several notes. That's correct.

## Sections

Defined in `memex.config.yml`. At time of writing:

| Section | Role |
|---|---|
| `projects/` | Active work. One hub note per project. |
| `research/` | Brent's own synthesis on a subject. Cites `sources/`. |
| `people-places/` | Genealogy, family, locations, organisations, contacts. |
| `sessions/` | Raw session logs that don't map onto a topic. Not indexed. |
| `sources/` | Raw captures. **Immutable. Local only — never published.** |
| `templates/` | Note templates. Never put content here. |

## The three layers

The vault distinguishes material by **role**, not by origin. This is the rule that
keeps it from collapsing into a pile.

**1. Sources — input, immutable.**
Web clippings, article excerpts, PDFs, transcripts, other people's words. You *read*
these and never edit them. Not for typos, not for tidying. Once captured, a source is
a fixed point that everything else can safely cite. `python build.py --seal` records
their hashes; `--check` reports any drift.

Use `templates/source-note.md`. Keep Brent's annotations visually separate from the
captured text — future readers must be able to tell whose words are whose.

`sources/` is excluded from the published site by config: volume would swamp the index,
and full-text captures of other people's writing shouldn't be pushed to a web server.
Don't flip that flag without being asked.

**2. Wiki — synthesis, rewritten freely.**
`research/`, `projects/`, `people-places/`. This is where you do the work: read the
sources, extract what matters, connect it to what's already here, resolve or flag
contradictions. These notes get rewritten as understanding improves. That's the point.

**3. Index — the map.**
`tags.md`, the hub notes in `projects/`, and the generated `manifest.json`. Keep the
hub notes' link lists current when you add something they should point at.

### Citation is what admits a source to the vault

A capture nothing links to is a reading pile, not a knowledge base. `sources/` is
marked `cite_required`, so `--check` will list every orphan. When you add a source,
either link it from a note in the same commit, or say plainly that it's unlinked and
why it's worth keeping anyway.

## Questions become pages

When Brent asks the vault something and the answer is worth keeping, **write it down
as a note**. The vault should grow from what he asks, not only from what he saves.

Use `templates/answer-note.md`. Before answering any substantive question, search the
wiki first, then `sources/`, then go external — and say which layer the answer came
from. If the answer came from outside the vault, that's a signal to capture the source
and write the answer up.

## Naming

- Topic notes: lowercase, hyphenated, no date in the filename.
  `research/vitamin-d-supplementation.md`, `projects/sb2-architecture.md`
- Dates live in headings **inside** the note.
- Source captures may carry a date: `sources/2026-08-18-mna-land-protection.md`
- Artifacts sit beside their note: `projects/sb2-architecture-2026-08-18-schema.sql`

## The "archive this" workflow

When Brent says **"archive this"**:

1. Identify every distinct topic the conversation touched.
2. For each, find the existing note or create one from `templates/topic-note.md`.
3. Save artifacts as their own files, in the same folder, linked from the note.
4. Capture any external sources that mattered into `sources/`, and cite them.
5. Append a **companion summary** under `## Log` as a new dated section:
   - What was decided
   - What was considered and rejected, and why
   - Open questions / next actions
   - Sources, with URLs
6. Add rows to `## Decisions` for anything settled.
7. Update `updated:` in the frontmatter; add new tags to `tags.md` in the same commit.
8. Run `python build.py --check` and fix what it reports. Run `--seal` if new sources
   were added.
9. **One commit** covering everything touched:
   `archive: <comma-separated topic slugs> (YYYY-MM-DD)`
10. Push. Deploy is automatic.

The artifact is the *what*. The companion summary is the *why*. Keep both. Never
transcribe the conversation verbatim.

## Lint

Two kinds, and only one of them is a script.

**Mechanical — `python build.py --check`.** Missing frontmatter keys, broken wikilinks
and relative links, uncited sources, edits to immutable files. Run it before every
commit.

**Content — your job, on request.** When Brent asks for a lint, or every few weeks of
accumulation, read across the wiki and report:

- **Contradictions.** Two notes asserting incompatible things. Never silently pick a
  winner — surface both, with dates and sources, and let Brent decide.
- **Staleness.** Claims resting on sources now well out of date, or `status: active`
  notes with no log entry in months.
- **Drift.** Two notes that have grown into the same topic and should merge, or one
  note that's become three topics and should split.
- **Thin synthesis.** Sources cited but never actually digested — a `## Key findings`
  section that's just a link list.

Report first. Make changes only after Brent agrees.

## Frontmatter

Required on every note: `title`, `updated`, `tags`, `status`.
`status` ∈ `active` | `parked` | `done` | `reference`. `--check` fails on omissions.

## Extending the vault

Add a section by editing `memex.config.yml` — `build.py` needs no changes:

```yaml
  - path: recipes
    title: Recipes
    description: What it's for.
    publish: false
```

Per-section flags: `publish`, `publish_raw`, `index`, `search`, `passthrough`, `sort`,
`immutable`, `cite_required`. Defaults live under `defaults:`. Theme overrides go in
`theme/style.css` and `theme/page.html`; absent those, the build uses its built-ins.

## Style

- Write for Brent reading this in three years with no memory of the conversation.
- Sources inline with URLs, so a citation can be pulled fast.
- No filler, no restating the prompt, no "as we discussed".
- Health and medical notes: record each source's strength — study type, sample size,
  date. Never present research as advice.

## Don't

- Don't edit anything under `sources/`. Ever.
- Don't rewrite or delete previous dated `## Log` sections. Append only.
- Don't resolve a contradiction by deleting one side of it.
- Don't reorganise sections or flip publish flags unasked.
- Don't paste long verbatim extracts into `sources/`. Link, excerpt briefly, annotate.
- Don't commit anything under `private/` or matching `.gitignore`.
