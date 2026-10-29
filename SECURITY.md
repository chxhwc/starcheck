# Security Policy

## Scope

`starcheck` reads local files and, in remote mode, calls two public GitHub API
endpoints. It stores nothing but a 30-minute metadata cache in
`%LOCALAPPDATA%\starcheck` (or `$XDG_CACHE_HOME/starcheck`).

## What counts as a vulnerability

- Reading files outside the audited repository root.
- Executing anything from the audited repository. `starcheck` **never** runs
  code, hooks, or scripts it finds — it only reads them as text.
- Leaking `GITHUB_TOKEN` / `GH_TOKEN` into output, logs, or the cache file.
- Argument injection through the `target` argument (e.g. a crafted repo name
  that reaches a shell).
- Cache poisoning: a writable cache entry that changes a verdict.

## Reporting

Open a [private security advisory](https://github.com/chxhwc/starcheck/security/advisories/new).
Expect a first reply within 72 hours. Credit given unless you prefer otherwise.

Please do not open a public issue for the above.

## Supported versions

The latest minor release gets fixes. This is a 0.x tool — pin a version in CI.
