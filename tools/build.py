"""Turns the Markdown posts in devlog/ into the site.

    python3 tools/build.py

Reads site.json and every devlog/*.md, writes index.html, one page per post
at devlog/<slug>/index.html, feed.xml and sitemap.xml. No dependencies. A post
starts with a front matter block:

    ---
    title: Why a farming game about a village that is emptying out
    date: 2026-09-09
    summary: One sentence for the list and the feed.
    ---

and the body is Markdown of the plain kind: paragraphs, ## headings, lists,
quotes, links, emphasis, images on their own line.
"""

import datetime
import html
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = json.load(open(os.path.join(ROOT, "site.json")))
POSTS_DIR = os.path.join(ROOT, "devlog")


def inline(text):
    text = html.escape(text, quote=False)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    return text


def markdown(src):
    out = []
    block = []
    kind = None

    def flush():
        nonlocal block, kind
        if not block:
            return
        if kind == "p":
            out.append("<p>%s</p>" % inline(" ".join(block)))
        elif kind == "ul":
            out.append("<ul>%s</ul>" % "".join("<li>%s</li>" % inline(b) for b in block))
        elif kind == "quote":
            out.append("<blockquote><p>%s</p></blockquote>" % inline(" ".join(block)))
        block, kind = [], None

    for line in src.split("\n"):
        stripped = line.strip()
        if not stripped:
            flush()
            continue
        m = re.match(r"^(#{2,3}) (.+)$", stripped)
        if m:
            flush()
            level = len(m.group(1))
            out.append("<h%d>%s</h%d>" % (level, inline(m.group(2)), level))
            continue
        m = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)$", stripped)
        if m:
            flush()
            alt, src_path = m.group(1), m.group(2)
            caption = "<figcaption>%s</figcaption>" % inline(alt) if alt else ""
            out.append('<figure><img src="%s" alt="%s" loading="lazy">%s</figure>'
                       % (src_path, html.escape(alt, quote=True), caption))
            continue
        if stripped.startswith("- "):
            if kind != "ul":
                flush()
                kind = "ul"
            block.append(stripped[2:])
            continue
        if stripped.startswith("> "):
            if kind != "quote":
                flush()
                kind = "quote"
            block.append(stripped[2:])
            continue
        if kind not in (None, "p"):
            flush()
        kind = "p"
        block.append(stripped)
    flush()
    return "\n".join(out)


def read_post(path):
    text = open(path, encoding="utf-8").read()
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not m:
        raise SystemExit("%s has no front matter" % path)
    meta = {}
    for line in m.group(1).split("\n"):
        key, _, value = line.partition(":")
        meta[key.strip()] = value.strip()
    for key in ("title", "date", "summary"):
        if key not in meta:
            raise SystemExit("%s is missing %s" % (path, key))
    slug = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", os.path.basename(path)[:-3])
    date = datetime.date.fromisoformat(meta["date"])
    return {
        "slug": slug,
        "title": meta["title"],
        "summary": meta["summary"],
        "date": date,
        "body": markdown(m.group(2).strip()),
        "url": "%s/devlog/%s/" % (SITE["url"], slug),
    }


def long_date(d):
    return "%d %s %d" % (d.day, d.strftime("%B"), d.year)


def shell(title, description, canonical, body, depth=0, kind="website"):
    base = "../" * depth
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%(title)s</title>
<meta name="description" content="%(description)s">
<link rel="canonical" href="%(canonical)s">
<meta property="og:type" content="%(kind)s">
<meta property="og:url" content="%(canonical)s">
<meta property="og:title" content="%(title)s">
<meta property="og:description" content="%(description)s">
<meta property="og:image" content="%(site)s/assets/img/og-image.png">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#f3ebda">
<link rel="icon" href="%(base)sfavicon-32.png" sizes="32x32">
<link rel="icon" href="%(base)sfavicon-16.png" sizes="16x16">
<link rel="apple-touch-icon" href="%(base)sassets/apple-touch-icon.png">
<link rel="alternate" type="application/rss+xml" title="%(name)s devlog" href="%(site)s/feed.xml">
<link rel="stylesheet" href="%(base)sassets/css/style.css">
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="top">
  <a class="home" href="%(base)s">%(name)s</a>
  <nav><a href="%(base)s#devlog">Devlog</a><a href="%(base)sfeed.xml">Feed</a></nav>
</header>
<main id="main">
%(body)s
</main>
<footer class="foot">
  <p>Made by <a href="%(author_url)s">%(author)s</a> in Slavonia, Croatia.</p>
  <p><a href="%(base)sfeed.xml">RSS feed</a> · <a href="%(github)s">Source on GitHub</a></p>
</footer>
</body>
</html>
""" % {
        "title": html.escape(title, quote=True),
        "description": html.escape(description, quote=True),
        "canonical": canonical,
        "kind": kind,
        "site": SITE["url"],
        "name": SITE["name"],
        "base": base,
        "body": body,
        "author": SITE["author"],
        "author_url": SITE["author_url"],
        "github": SITE["github"],
    }


def home(posts):
    items = "\n".join(
        '<li><time datetime="%s">%s</time><div><a href="devlog/%s/">%s</a><p>%s</p></div></li>'
        % (p["date"].isoformat(), long_date(p["date"]), p["slug"],
           html.escape(p["title"]), html.escape(p["summary"]))
        for p in posts)
    pitch = "\n".join("<p>%s</p>" % html.escape(p) for p in SITE["pitch"])
    body = """<section class="hero">
  <img class="scene" src="assets/img/hero.png" alt="A pixel-art farm: a tilled plot with onions, cabbages, tomatoes, peppers and corn, a pond, oaks, and the farmer standing between them." width="320" height="94">
  <h1>%(tagline)s</h1>
  <img class="crops" src="assets/img/crops.png" alt="" width="160" height="32">
</section>
<section class="pitch">
%(pitch)s
  <p class="status">%(status)s</p>
</section>
<section class="devlog" id="devlog">
  <h2>Devlog</h2>
  <ul class="posts">
%(items)s
  </ul>
</section>""" % {
        "tagline": html.escape(SITE["tagline"]),
        "pitch": pitch,
        "status": html.escape(SITE["status"]),
        "items": items,
    }
    return shell(SITE["name"], SITE["tagline"], SITE["url"] + "/", body)


def post_page(p):
    body = """<article class="post">
  <header>
    <h1>%(title)s</h1>
    <p class="meta"><time datetime="%(iso)s">%(date)s</time></p>
  </header>
%(body)s
  <p class="back"><a href="../../#devlog">All posts</a></p>
</article>""" % {
        "title": html.escape(p["title"]),
        "iso": p["date"].isoformat(),
        "date": long_date(p["date"]),
        "body": p["body"],
    }
    return shell("%s · %s" % (p["title"], SITE["name"]), p["summary"], p["url"], body,
                 depth=2, kind="article")


def feed(posts):
    entries = "\n".join("""  <item>
    <title>%s</title>
    <link>%s</link>
    <guid isPermaLink="true">%s</guid>
    <pubDate>%s</pubDate>
    <description>%s</description>
    <content:encoded><![CDATA[%s]]></content:encoded>
  </item>""" % (html.escape(p["title"]), p["url"], p["url"],
                datetime.datetime.combine(p["date"], datetime.time(9)).strftime("%a, %d %b %Y %H:%M:%S +0000"),
                html.escape(p["summary"]), p["body"].replace("]]>", "]]]]><![CDATA[>"))
                        for p in posts)
    return """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:content="http://purl.org/rss/1.0/modules/content/">
<channel>
  <title>%s devlog</title>
  <link>%s/</link>
  <atom:link href="%s/feed.xml" rel="self" type="application/rss+xml"/>
  <description>%s</description>
  <language>en</language>
%s
</channel>
</rss>
""" % (html.escape(SITE["name"]), SITE["url"], SITE["url"], html.escape(SITE["tagline"]), entries)


def sitemap(posts):
    urls = [SITE["url"] + "/"] + [p["url"] for p in posts]
    return '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + \
        "\n".join("  <url><loc>%s</loc></url>" % u for u in urls) + "\n</urlset>\n"


def write(rel, text):
    path = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    print(rel)


def main():
    posts = sorted((read_post(os.path.join(POSTS_DIR, n))
                    for n in os.listdir(POSTS_DIR) if n.endswith(".md")),
                   key=lambda p: p["date"], reverse=True)
    write("index.html", home(posts))
    for p in posts:
        write("devlog/%s/index.html" % p["slug"], post_page(p))
    write("feed.xml", feed(posts))
    write("sitemap.xml", sitemap(posts))


if __name__ == "__main__":
    main()
