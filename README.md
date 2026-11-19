# FRAME — retired copy

This repository is no longer the published site. It is kept for history only.

- **Live directory:** <https://frame-links-directory.vercel.app>
- **Canonical repository:** `Dailyverse0001/frame-links-directory` (private)

Vercel builds the live site from that canonical repository on every push to
`main`, including the six-hourly catalogue commits made by GitHub Actions. No
deploy token is involved.

The old Vercel project for this repository (`site`) now serves a redirect page
to the live directory, so existing links keep working:

- <https://site-dailyverse0001.vercel.app>
- <https://site-lyart-omega-65.vercel.app>

## What was removed

The `Refresh directory and deploy` workflow used to deploy with a
`VERCEL_TOKEN` secret. That token expired, so every scheduled run failed with
`The token provided via the --token option is not valid`. The deploy step is
gone, the workflow is disabled, and deployment now belongs to the canonical
repository.

## Catalogue maintenance

The parser, tests and maintenance scripts in `scripts/` still work:

```bash
python -m unittest discover -s tests -v
python scripts/sync_links.py
```

Any future work on the directory should happen in
`Dailyverse0001/frame-links-directory`, not here.

The website hosts no streams or copyrighted files; it lists third-party
destinations whose security, legality and reliability are not verified.
