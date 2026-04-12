---
name: Build or test failure
about: Report a build, validation, or test failure
title: "[build] "
labels: build, ci
assignees: ''
---

## What failed?

- [ ] `just fetch`
- [ ] `just build` (one of the transformer stages)
- [ ] `just validate` (schema validation)
- [ ] `just test` (pytest)
- [ ] `just ci` (end-to-end)
- [ ] `just stats`
- [ ] Other:

## Environment

```
$ .venv/bin/python --version
(paste output)

$ just --version
(paste output)

$ uname -sr
(paste output)
```

## Command and output

The exact command you ran:

```
$ just <command>
```

Full output (or the relevant error section). **Please include the full traceback for Python errors**, not just the final line:

```
(paste full output here)
```

## Git state

```
$ git rev-parse --short HEAD
(paste)

$ git status
(paste — only if you have local modifications)
```

## Reproduction

- [ ] Fresh clone
- [ ] Existing checkout, clean tree
- [ ] Existing checkout, local modifications (explain)

Any specific version of upstream sources? (check `manifest.json`)

## What did you expect?

What you expected to happen instead of the failure.
