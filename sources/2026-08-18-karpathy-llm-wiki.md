---
title: Karpathy — llm-wiki (idea file)
source_url: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
author: Andrej Karpathy
published: 2026-04-04
captured: 2026-08-18
created: 2026-08-18
updated: 2026-08-18
tags: [memex, technical, reference]
status: reference
cited_by: [projects/memex-vault-system.md]
---

# Karpathy — llm-wiki (idea file)

> **Source:** [gist.github.com/karpathy/442a6bf555914893e9891c11519de94f](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) · Andrej Karpathy · 2026-04-04

## Why I kept this

The pattern memex is built on, published as prose rather than code. Worth re-reading
whenever the vault's conventions feel arbitrary — most of them descend from here.

## Notes

- Three of its ideas were folded into this vault on 2026-08-18: immutable sources,
  lint as a named operation, and questions becoming pages.
- Deliberately abstract — a pattern, not an implementation. The agent is expected to
  instantiate it per-user. Our `CLAUDE.md` is that instantiation.
- Explicitly descends from Bush's Memex, which is where this repo's name comes from.

## Capture

Argues that the usual LLM-and-documents pattern is RAG: chunks retrieved at query
time, answer generated, nothing retained — the model rediscovers the same knowledge on
every question. The alternative is to compile sources once into a persistent
interlinked wiki that the agent maintains, then query the wiki. Knowledge compounds
rather than being re-derived. Bush's original failed on maintenance cost; the claim
here is that an LLM drops that cost close to zero.

Architecture is three layers — immutable raw sources, an agent-written wiki, an index
over both — and three operations: ingest, query, lint.

Full text at the source link; not reproduced here.
