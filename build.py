#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "markdown>=3.5",
#     "pyyaml>=6.0",
# ]
# ///
"""
Build the Memex vault into a static site.

Everything about *what* gets built is declared in memex.config.yml.
Nothing about the vault's shape is hardcoded here — adding a section means
editing the config, not this file.

Outputs (default ./_site):
  <section>/<note>.html   rendered page
  <section>/<note>.md     original markdown, for agents to fetch directly
  index.html              browsable index with client-side search
  search.json             full-text index, also agent-readable
  manifest.json           machine-readable map of the whole vault

Usage:
  python build.py                  # publish build — honours publish/search flags
  python build.py --all            # local build — includes unpublished sections
  python build.py --out ./preview  # write somewhere else
  python build.py --check          # lint: frontmatter, links, orphans, immutability
  python build.py --seal           # record hashes of immutable sections
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import markdown
import yaml

ROOT = Path(__file__).parent
CONFIG_PATH = ROOT / "memex.config.yml"

SORTERS = {
    "updated_desc": lambda ns: sorted(ns, key=lambda n: n.updated, reverse=True),
    "updated_asc": lambda ns: sorted(ns, key=lambda n: n.updated),
    "title": lambda ns: sorted(ns, key=lambda n: n.title.lower()),
    "manual": lambda ns: ns,
}

REQUIRED_FRONTMATTER = ("title", "updated", "tags", "status")


# --------------------------------------------------------------------------- #
# Config
# --------------------------------------------------------------------------- #


@dataclass
class Section:
    path: str
    title: str
    description: str = ""
    publish: bool = True
    publish_raw: bool = True
    index: bool = True
    search: bool = True
    passthrough: bool = True
    sort: str = "updated_desc"
    immutable: bool = False  # contents are append-only; edits are reported by --check
    cite_required: bool = False  # files here must be linked from somewhere


@dataclass
class Config:
    site: dict[str, Any]
    sections: list[Section]

    @classmethod
    def load(cls, path: Path) -> "Config":
        if not path.exists():
            sys.exit(f"Missing config: {path}")
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        defaults = raw.get("defaults") or {}
        sections = []
        for entry in raw.get("sections") or []:
            merged = {**defaults, **entry}
            merged.setdefault("title", str(merged["path"]).replace("-", " ").title())
            known = {f.name for f in Section.__dataclass_fields__.values()}
            sections.append(Section(**{k: v for k, v in merged.items() if k in known}))
        return cls(site=raw.get("site") or {}, sections=sections)


# --------------------------------------------------------------------------- #
# Notes
# --------------------------------------------------------------------------- #


@dataclass
class Note:
    src: Path
    rel: Path
    section: Section
    frontmatter: dict[str, Any]
    body: str
    warnings: list[str] = field(default_factory=list)

    @property
    def title(self) -> str:
        return self.frontmatter.get("title") or self.src.stem.replace("-", " ").title()

    @property
    def updated(self) -> str:
        return str(self.frontmatter.get("updated") or "")

    @property
    def tags(self) -> list[str]:
        tags = self.frontmatter.get("tags") or []
        return [str(t) for t in tags] if isinstance(tags, list) else [str(tags)]

    @property
    def url(self) -> str:
        return self.rel.with_suffix(".html").as_posix()

    @property
    def raw_url(self) -> str:
        return self.rel.as_posix()


def split_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    try:
        fm = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError:
        fm = {}
    return (fm if isinstance(fm, dict) else {}), parts[2]


def collect(config: Config, include_unpublished: bool) -> tuple[list[Note], list[Path]]:
    """Return every note plus every non-markdown file to copy verbatim."""
    notes: list[Note] = []
    assets: list[Path] = []
    for section in config.sections:
        src_dir = ROOT / section.path
        if not src_dir.is_dir():
            continue
        if include_unpublished:
            # local preview: show everything, whatever the publish rules say
            section = replace(section, publish=True, publish_raw=True,
                              search=True, index=True)
        elif not section.publish:
            continue
        for path in sorted(src_dir.rglob("*")):
            if path.is_dir() or path.name.startswith("."):
                continue
            rel = path.relative_to(ROOT)
            if path.suffix.lower() != ".md":
                if section.passthrough:
                    assets.append(rel)
                continue
            fm, body = split_frontmatter(path.read_text(encoding="utf-8"))
            note = Note(src=path, rel=rel, section=section, frontmatter=fm, body=body)
            note.warnings = [
                f"missing frontmatter key: {k}"
                for k in REQUIRED_FRONTMATTER
                if k not in fm
            ]
            notes.append(note)
    return notes, assets


# --------------------------------------------------------------------------- #
# Theme — files in theme/ win; these are the fallbacks
# --------------------------------------------------------------------------- #

FALLBACK_CSS = """
:root { --bg:#faf9f7; --fg:#23211e; --muted:#6b665e;
        --rule:#ddd8d0; --link:#7a4b2a; --code-bg:#f0ede8; }
@media (prefers-color-scheme: dark) {
  :root { --bg:#16150f; --fg:#e8e4dc; --muted:#9a948a;
          --rule:#332f28; --link:#d9a66c; --code-bg:#221f1a; } }
*{box-sizing:border-box} body{background:var(--bg);color:var(--fg);margin:0;
  font:17px/1.65 -apple-system,BlinkMacSystemFont,"Segoe UI",Georgia,serif;
  -webkit-text-size-adjust:100%}
.wrap{max-width:42rem;margin:0 auto;padding:2rem 1.25rem 6rem}
header.site{border-bottom:1px solid var(--rule);margin-bottom:2rem;padding-bottom:1rem}
header.site a.home{font-weight:700;letter-spacing:.02em;text-decoration:none;color:var(--fg)}
a{color:var(--link)} h1{font-size:1.9rem;line-height:1.2;margin:.2em 0 .3em}
h2{font-size:1.25rem;margin-top:2.2em;border-bottom:1px solid var(--rule);padding-bottom:.25em}
h3{font-size:1.05rem;margin-top:1.8em;color:var(--muted)}
.meta{color:var(--muted);font-size:.85rem;margin-bottom:2rem}
.tag{display:inline-block;background:var(--code-bg);border-radius:3px;
     padding:.1em .5em;margin-right:.3em;font-size:.8rem}
code{background:var(--code-bg);padding:.1em .35em;border-radius:3px;font-size:.88em}
pre{background:var(--code-bg);padding:1rem;overflow-x:auto;border-radius:5px}
pre code{background:none;padding:0}
table{border-collapse:collapse;width:100%;font-size:.92rem}
th,td{border:1px solid var(--rule);padding:.45em .6em;text-align:left;vertical-align:top}
blockquote{border-left:3px solid var(--rule);margin-left:0;padding-left:1rem;color:var(--muted)}
input#q{width:100%;padding:.7em .9em;font-size:1rem;border:1px solid var(--rule);
        border-radius:6px;background:var(--bg);color:var(--fg);margin-bottom:1.5rem}
ul.notes{list-style:none;padding:0}
ul.notes li{padding:.55em 0;border-bottom:1px solid var(--rule)}
ul.notes .desc{display:block;color:var(--muted);font-size:.85rem}
.section-label{text-transform:uppercase;letter-spacing:.08em;font-size:.72rem;
               color:var(--muted);margin-top:2.5rem}
.section-desc{color:var(--muted);font-size:.85rem;margin:.3em 0 .6em}
footer{margin-top:4rem;padding-top:1rem;border-top:1px solid var(--rule);
       color:var(--muted);font-size:.8rem}
"""

FALLBACK_PAGE = """<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
{robots}<title>{title} · {site_title}</title>
<link rel="stylesheet" href="{root}style.css">
</head><body><div class="wrap">
<header class="site"><a class="home" href="{root}index.html">{site_title}</a></header>
{body}
<footer>Built {built}{raw_link}</footer>
</div></body></html>"""

SEARCH_JS = """<script>
const q=document.getElementById('q'),r=document.getElementById('results'),a=document.getElementById('all');
let idx=[];fetch('search.json').then(x=>x.json()).then(d=>idx=d);
q.addEventListener('input',()=>{const v=q.value.toLowerCase().trim();
if(!v){r.innerHTML='';a.style.display='';return}a.style.display='none';
const hits=idx.filter(n=>(n.title+' '+n.tags.join(' ')+' '+n.text).toLowerCase().includes(v)).slice(0,40);
r.innerHTML=hits.length?'<ul class="notes">'+hits.map(n=>{
const i=n.text.toLowerCase().indexOf(v);const s=i<0?'':n.text.slice(Math.max(0,i-60),i+90);
return `<li><a href="${n.url}">${n.title}</a><span class="desc">…${s}…</span></li>`}).join('')+'</ul>'
:'<p>No matches.</p>'});
</script>"""


def load_theme(config: Config) -> tuple[str, str]:
    theme_dir = ROOT / str(config.site.get("theme_dir") or "theme")
    css_file, page_file = theme_dir / "style.css", theme_dir / "page.html"
    css = css_file.read_text(encoding="utf-8") if css_file.exists() else FALLBACK_CSS
    page = page_file.read_text(encoding="utf-8") if page_file.exists() else FALLBACK_PAGE
    return css, page


# --------------------------------------------------------------------------- #
# Render
# --------------------------------------------------------------------------- #


def strip_markdown(text: str) -> str:
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    text = re.sub(r"[#*`>\[\]()|_-]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def build(config: Config, out: Path, include_unpublished: bool) -> int:
    notes, assets = collect(config, include_unpublished)
    css, page_tmpl = load_theme(config)
    site_title = str(config.site.get("title") or "memex")
    robots_meta = (
        '<meta name="robots" content="noindex, nofollow">\n'
        if config.site.get("noindex")
        else ""
    )
    built = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    md = markdown.Markdown(extensions=["extra", "toc", "sane_lists", "nl2br"])

    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    (out / "style.css").write_text(css, encoding="utf-8")

    def render(title: str, body: str, depth: int, raw: str | None) -> str:
        return page_tmpl.format(
            title=title,
            site_title=site_title,
            robots=robots_meta,
            root="../" * depth,
            body=body,
            built=built,
            raw_link=f' · <a href="{raw}">raw markdown</a>' if raw else "",
        )

    search: list[dict[str, Any]] = []
    manifest: list[dict[str, Any]] = []

    for note in notes:
        section = note.section
        target = out / note.rel
        target.parent.mkdir(parents=True, exist_ok=True)

        if section.publish:
            md.reset()
            meta_bits = [b for b in (note.updated and f"Updated {note.updated}",
                                     note.frontmatter.get("status")) if b]
            meta_html = (
                f'<div class="meta">{" · ".join(str(b) for b in meta_bits)}<br>'
                + "".join(f'<span class="tag">{t}</span>' for t in note.tags)
                + "</div>"
            )
            target.with_suffix(".html").write_text(
                render(
                    note.title,
                    f"<h1>{note.title}</h1>{meta_html}{md.convert(note.body)}",
                    depth=len(note.rel.parts) - 1,
                    raw=note.src.name if section.publish_raw else None,
                ),
                encoding="utf-8",
            )
        if section.publish_raw:
            shutil.copy2(note.src, target)
        if section.search:
            search.append({
                "title": note.title, "url": note.url, "raw": note.raw_url,
                "tags": note.tags, "section": section.path,
                "updated": note.updated, "text": strip_markdown(note.body)[:6000],
            })
        manifest.append({
            "title": note.title, "section": section.path, "path": note.rel.as_posix(),
            "url": note.url if section.publish else None,
            "tags": note.tags, "updated": note.updated,
            "status": str(note.frontmatter.get("status") or ""),
        })

    for rel in assets:
        dest = out / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / rel, dest)

    # index page
    by_section: dict[str, list[Note]] = {}
    for note in notes:
        if note.section.index and note.section.publish:
            by_section.setdefault(note.section.path, []).append(note)

    blocks = ""
    for section in config.sections:
        group = by_section.get(section.path)
        if not group:
            continue
        ordered = SORTERS.get(section.sort, SORTERS["updated_desc"])(group)
        items = "".join(
            f'<li><a href="{n.url}">{n.title}</a><span class="desc">{n.updated}'
            + "".join(f" · {t}" for t in n.tags)
            + "</span></li>"
            for n in ordered
        )
        desc = f'<div class="section-desc">{section.description.strip()}</div>' if section.description else ""
        blocks += (
            f'<div class="section-label">{section.title}</div>{desc}'
            f'<ul class="notes">{items}</ul>'
        )

    (out / "index.html").write_text(
        render(
            "Index",
            f"<h1>{site_title}</h1>"
            '<input id="q" type="search" placeholder="Search notes…" autocomplete="off">'
            f'<div id="results"></div><div id="all">{blocks}</div>{SEARCH_JS}',
            depth=0,
            raw="search.json",
        ),
        encoding="utf-8",
    )
    (out / "search.json").write_text(json.dumps(search, indent=1), encoding="utf-8")
    (out / "manifest.json").write_text(
        json.dumps(
            {
                "site": site_title,
                "built": built,
                "sections": [
                    {"path": s.path, "title": s.title,
                     "description": s.description.strip(), "published": s.publish}
                    for s in config.sections
                ],
                "notes": manifest,
            },
            indent=1,
        ),
        encoding="utf-8",
    )
    if config.site.get("noindex"):
        (out / "robots.txt").write_text("User-agent: *\nDisallow: /\n", encoding="utf-8")

    print(f"Built {len(notes)} notes, {len(assets)} assets → {out}")
    return 0


# --------------------------------------------------------------------------- #
# Check
# --------------------------------------------------------------------------- #


INTEGRITY_PATH = ROOT / ".integrity.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def immutable_files(config: Config) -> list[Path]:
    """Every file inside a section marked immutable, relative to ROOT."""
    out = []
    for section in config.sections:
        if not section.immutable:
            continue
        src = ROOT / section.path
        if not src.is_dir():
            continue
        out += [
            p.relative_to(ROOT)
            for p in sorted(src.rglob("*"))
            if p.is_file() and not p.name.startswith(".")
        ]
    return out


def seal(config: Config) -> int:
    """Record hashes of immutable files so later edits can be detected."""
    record = {p.as_posix(): digest(ROOT / p) for p in immutable_files(config)}
    INTEGRITY_PATH.write_text(json.dumps(record, indent=1, sort_keys=True), encoding="utf-8")
    print(f"Sealed {len(record)} file(s) → {INTEGRITY_PATH.name}")
    return 0


def check(config: Config) -> int:
    """Mechanical lint. Content-level lint — contradictions, staleness of claims —
    is an agent's job; see CLAUDE.md. This catches only what a script can prove."""
    notes, assets = collect(config, include_unpublished=True)
    by_path = {n.rel.as_posix(): n for n in notes}
    known_stems = {n.rel.stem: n.rel.as_posix() for n in notes}

    # every outbound reference in the vault, wikilinks and relative markdown links
    referenced: set[str] = set()
    problems = 0

    def report(where: str, issues: list[str]) -> None:
        nonlocal problems
        if not issues:
            return
        problems += len(issues)
        print(where)
        for issue in issues:
            print(f"  - {issue}")

    for note in notes:
        issues = list(note.warnings)
        for target in re.findall(r"\[\[([^\]|#]+)", note.body):
            stem = Path(target.strip()).stem
            if stem in known_stems:
                referenced.add(known_stems[stem])
            else:
                issues.append(f"wikilink to missing note: [[{target.strip()}]]")
        for target in re.findall(r"\]\(([^)\s]+)\)", note.body):
            if "://" in target or target.startswith("#"):
                continue
            resolved = (note.rel.parent / target).as_posix()
            resolved = Path(resolved).resolve().relative_to(ROOT.resolve()).as_posix() \
                if (ROOT / note.rel.parent / target).resolve().is_relative_to(ROOT.resolve()) \
                else resolved
            referenced.add(resolved)
            if not (ROOT / resolved).exists():
                issues.append(f"broken relative link: {target}")
        report(str(note.rel), issues)

    # sections that require citation: flag anything nothing points at
    for section in config.sections:
        if not section.cite_required:
            continue
        prefix = section.path + "/"
        orphans = [
            p for p in list(by_path) + [a.as_posix() for a in assets]
            if p.startswith(prefix) and p not in referenced
        ]
        if orphans:
            problems += len(orphans)
            print(f"{section.path}/ — captured but never cited "
                  f"(a source isn't in the vault until a note links it)")
            for p in sorted(orphans):
                print(f"  - {p}")

    # immutability drift
    if INTEGRITY_PATH.exists():
        sealed = json.loads(INTEGRITY_PATH.read_text(encoding="utf-8"))
        current = {p.as_posix(): digest(ROOT / p) for p in immutable_files(config)}
        changed = [p for p, h in current.items() if p in sealed and sealed[p] != h]
        missing = [p for p in sealed if p not in current]
        unsealed = [p for p in current if p not in sealed]
        if changed or missing:
            problems += len(changed) + len(missing)
            print("immutable content changed (raw captures are append-only):")
            for p in changed:
                print(f"  - modified: {p}")
            for p in missing:
                print(f"  - deleted:  {p}")
        if unsealed:
            print(f"\n{len(unsealed)} new immutable file(s) not yet sealed. "
                  f"Run: python build.py --seal")
    else:
        print("No .integrity.json yet. Run: python build.py --seal\n")

    print(f"\n{len(notes)} notes checked, {problems} issue(s).")
    return 1 if problems else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the Memex vault.")
    parser.add_argument("--config", type=Path, default=CONFIG_PATH)
    parser.add_argument("--out", type=Path, default=ROOT / "_site")
    parser.add_argument("--all", action="store_true",
                        help="include sections marked publish: false")
    parser.add_argument("--check", action="store_true",
                        help="lint frontmatter, links, orphans, immutability; build nothing")
    parser.add_argument("--seal", action="store_true",
                        help="record hashes of immutable sections so edits get caught")
    args = parser.parse_args()

    config = Config.load(args.config)
    if args.seal:
        return seal(config)
    if args.check:
        return check(config)
    return build(config, args.out, args.all)


if __name__ == "__main__":
    raise SystemExit(main())
