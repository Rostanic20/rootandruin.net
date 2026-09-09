# rootandruin.net

The devlog for Root and Ruin, a farming game about a Slavonian village and the
forest beyond it. Static site, no dependencies: plain HTML and CSS, generated
from Markdown by one Python script.

## Publish a post

1. Write `devlog/YYYY-MM-DD-slug.md` with a front matter block:

   ```
   ---
   title: What the river looks like now
   date: 2026-10-04
   summary: One sentence for the list and the feed.
   ---
   ```

   then the post in plain Markdown: paragraphs, `##` headings, `-` lists,
   `>` quotes, `**bold**`, `*italic*`, `[links](url)`, and images on their
   own line as `![caption](../../assets/img/river.png)`. Put images in
   `assets/img/`; pixel art is shown crisp at any size, so save it at 1x.

2. `python3 tools/build.py` writes `index.html`, `devlog/<slug>/index.html`,
   `feed.xml` and `sitemap.xml`.

3. Commit and push. Cloudflare Pages deploys `main`.

The line under the pitch ("Right now: ...") lives in `site.json` as `status`;
change it when the milestone changes and rebuild.

## Run locally

```bash
python3 -m http.server 8000     # then http://localhost:8000
```

## Assets

`assets/img/hero.png`, `crops.png`, the favicons and `og-image.png` are cut
from the game's own generated art by a one-off script in the game repo's
tools; regenerate them there when the art changes. Fonts are Alegreya under
the OFL, latin and latin-ext subsets only.
