# memex

Personal knowledge vault. Plain markdown, version controlled, published read-only to
a private URL. Named for Vannevar Bush's 1945 device — the one that failed because
nobody could maintain the cross-references by hand.

- **Source of truth:** this repo
- **Editing:** Obsidian on the Mac, vault root = repo root
- **Reading on the road:** the published site, behind basic auth
- **Agents:** read `CLAUDE.md` first

---

## Layout

```
memex.config.yml   defines every section and how it's published — edit this, not build.py
CLAUDE.md          instructions for any agent working in the vault
tags.md            canonical tag list

projects/          active work — one hub note per project
research/          synthesised notes on a subject
people-places/     genealogy, family, locations, organisations
sessions/          raw session logs that don't map onto a topic
sources/           raw captures — immutable, local-only, never published
templates/         note templates
theme/             optional style.css / page.html overrides

build.py           markdown → static site, plus lint
.integrity.json    hashes of immutable files, written by --seal
```

### Three layers

**sources/** is input — clippings, articles, PDFs. Read, never edited. Once captured,
a source is a fixed point everything else can cite. `--check` reports any edit.

**research/, projects/, people-places/** are synthesis. Rewritten freely as
understanding improves.

**tags.md and the hub notes** are the map.

A capture isn't in the vault until a note links to it. `sources/` is marked
`cite_required`, so `--check` lists the orphans.

---

## One-time setup

### 1. Obsidian
*Open folder as vault* → this repo. Then Settings → Files & Links:
**New note location** `research/`, **Template folder** `templates/`.

Optional: the **Obsidian Git** community plugin auto-commits on a timer if you'd
rather not use the terminal.

For clipping, install Obsidian's **Web Clipper** extension and point it at `sources/`
with `templates/source-note.md` as its template — consistent frontmatter from day one.

### 2. Password-protect the published folder
Do this **on the server, before the first deploy**:

1. In Hosting.com cPanel, create a subdomain or folder, e.g. `memex.funbyus.com`
   → `/home/<user>/memex_public`.
2. Open **Directory Privacy**, select it, tick *Password protect this directory*,
   create a user.

cPanel writes `.htaccess` and `.htpasswd` there. The workflow never deletes them.

### 3. GitHub secrets
Settings → Secrets and variables → Actions:

| Secret | Value |
|---|---|
| `FTP_SERVER` | e.g. `ftp.funbyus.com` |
| `FTP_USERNAME` | FTP account username |
| `FTP_PASSWORD` | FTP account password |
| `FTP_TARGET_DIR` | remote path with trailing slash, e.g. `/memex_public/` |

Use a dedicated FTP account scoped to that one directory, not your main cPanel login.

### 4. First push
```bash
pip install markdown pyyaml
python build.py --check
git add . && git commit -m "chore: scaffold vault" && git push
```

---

## Commands

```bash
python build.py             # publish build — honours publish/search flags
python build.py --all       # local build, includes sources/ and other unpublished
python build.py --check     # lint: frontmatter, links, orphans, immutability drift
python build.py --seal      # record hashes of sources/ after adding captures
python build.py --out ./tmp # build somewhere else
```

`--check` catches what a script can prove. Contradictions, stale claims, and notes
that have drifted into each other are an agent's job — ask for a content lint. The
procedure is in `CLAUDE.md`.

---

## Daily use

**Locally:** edit in Obsidian, commit, push. The site updates itself.

**From an agent:** say *"archive this"*. It reads `CLAUDE.md`, finds or creates the
right notes, appends a dated section, saves artifacts, lints, and makes one commit.

**Asking the vault things:** when an answer is worth keeping, it becomes a note —
`templates/answer-note.md`. The vault grows from your questions, not just your saves.

---

## Agent access to the published copy

Every published note ships twice: `.html` for you, and the original `.md` for
machines. So an agent that can fetch URLs reads
`https://memex.funbyus.com/research/some-topic.md` directly.

- `search.json` — full text of every published note, one request
- `manifest.json` — the vault's structure: sections, titles, tags, status, paths

Both sit behind basic auth. `sources/` is not published, so anything an agent needs
must live in the wiki layer.
