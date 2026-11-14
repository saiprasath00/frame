# FRAME — Movie-first links directory

A static, searchable links-only website. Its public `site/` folder contains no
upstream-source labels or addresses. The maintenance code lives outside the
published folder. No streams, downloads or copyrighted files are hosted.

## Launch on GitHub Pages

1. Create a new **public GitHub repository** and upload this project's files,
   preserving the `site/`, `scripts/`, and `.github/workflows/` directories.
   Keep the default branch named `main`, or update the branch name in the workflow.
2. Go to **Settings → Pages → Build and deployment → Source: GitHub Actions**.
3. Open **Actions → Refresh directory and publish → Run workflow**. If Actions
   are disabled, enable them in the repository settings first.
4. Open the Pages URL provided by the deployment. Put a custom domain in
   Settings → Pages if you want your own domain.

## How updates work

- A GitHub Actions workflow runs at minute 17 every 6 hours (UTC), and manually
  whenever you click **Run workflow**. It also runs on updates to the project files.
- It checks the maintained [editorial GitHub markdown](https://github.com/fmhy/edit/blob/main/docs/video.md)
  and [published directory](https://fmhy.net/video), selecting only direct HTTPS
  destination links for **Movie downloads**, **4K streaming**, **Anime streaming**
  and **Anime downloads**, in that order.
- A change to a site's name or address is picked up by comparing the fresh
  sources to the last snapshot. Broken source downloads cannot overwrite the
  site with an empty catalogue. Rentry, pastes, encoded URLs, mirrors labelled
  `2`, status pages, Discord/Telegram links and other intermediate destinations
  are excluded.
- The refresh workflow rewrites `site/links.json` when listings change and
  deploys **only** the `site/` folder. A visiting browser checks the JSON on
  load, every 15 minutes and when the tab regains focus. Favorites follow URL
  changes when a site's name remains the same.
- If the update services are down, visitors see the most recent good snapshot.

### Important limitations

Updates are **not instantaneous**: GitHub scheduled Actions can run late or be
skipped. GitHub may disable schedules in public repositories after **60 days of
inactivity**. Check Actions periodically and re-enable the schedule if needed.

The **website** contains no indication of those sources, but if you use a
**public GitHub repository**, anyone can inspect the public repository's
workflow and synchronizer. To keep that server-side provenance private as well,
use private build infrastructure with a separate public static hosting target.

The service links are third-party destinations. Their security, legality and
reliability are not independently verified. The synchronizer doesn't bypass
encoded links or passwords; it drops them.

## Local preview

Open `site/index.html`. It includes the 120-item seed list and works without a
server. To test loading the JSON feed locally, from the project root run
`python -m http.server 8000 --directory site` and open
`http://localhost:8000`.

## Tests

Run `python -m unittest discover -s tests -v`.
The test suite uses offline markdown and HTML fixtures. Live upstream requests
were **not** run in the build environment, which has no internet access.
