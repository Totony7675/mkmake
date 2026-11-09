#!/usr/bin/env python3
"""Checks all shop items. Run from the repository root: python3 _tools/check-shop.py"""
import glob
import os
import re
import sys

errors = []
warnings = []


def err(f, msg):
    errors.append("ERROR  %s: %s" % (f, msg))


def warn(f, msg):
    warnings.append("WARN   %s: %s" % (f, msg))


TITLE_RE = re.compile(r'^[^\"]+ - [0-9]{1,3}(\.[0-9]{3})* HUF$')
MESKA_RE = re.compile(r'^https://[A-Za-z0-9.-]*meska\.hu/\S+$')
PHOTO_RE = re.compile(r'^/assets/img/shop/[A-Za-z0-9._/-]+\.jpg$')


def parse(path):
    text = open(path, encoding="utf-8").read()
    m = re.match(r'^---\n(.*?)\n---\n?(.*)$', text, re.S)
    if not m:
        return None, None
    fm = {}
    cur = None
    for line in m.group(1).split("\n"):
        if not line.strip():
            continue
        item = re.match(r'^\s+-\s+(.*)$', line)
        if item and cur is not None and isinstance(fm.get(cur), list):
            fm[cur].append(item.group(1).strip().strip('"'))
            continue
        kv = re.match(r'^([A-Za-z_][A-Za-z0-9_-]*):\s*(.*)$', line)
        if not kv:
            continue
        cur = kv.group(1)
        val = kv.group(2).strip()
        if val == "":
            fm[cur] = []
        else:
            if len(val) >= 2 and val[0] == '"' and val[-1] == '"':
                val = val[1:-1]
            fm[cur] = val
    return fm, m.group(2).strip()


LANGS = [("hu", "_portfolio", "/shop/"), ("en", "_portfolio/en", "/en/shop/")]
items = {}   # (lang, slug) -> (frontmatter, body)
used_photos = set()

for lang, folder, prefix in LANGS:
    for path in sorted(glob.glob(os.path.join(folder, "*.md"))):
        slug = os.path.basename(path)[:-3]
        fm, body = parse(path)
        if fm is None:
            err(path, "no front matter (the file must start with --- and have a closing ---)")
            continue
        items[(lang, slug)] = (fm, body)
        if not re.match(r'^[a-z0-9]+(-[a-z0-9]+)*$', slug):
            err(path, "file name must be a lowercase ASCII slug with hyphens")
        if fm.get("layout") != "shop-item":
            err(path, "layout must be exactly: shop-item")
        if fm.get("lang") != lang:
            err(path, "lang must be: %s" % lang)
        if fm.get("translation_id") != slug:
            err(path, "translation_id must be exactly the slug: %s" % slug)
        if fm.get("permalink") != "%s%s/" % (prefix, slug):
            err(path, "permalink must be exactly: %s%s/" % (prefix, slug))
        title = fm.get("title")
        if not isinstance(title, str) or not TITLE_RE.match(title):
            err(path, 'title must look like "Name - 45.000 HUF" (see title format rule)')
        order = fm.get("order")
        if not isinstance(order, str) or not order.isdigit():
            err(path, "order must be a whole number")
        images = fm.get("images")
        if not isinstance(images, list) or len(images) == 0:
            err(path, "images: list is missing or empty (list every photo, one per line, starting with '  - ')")
            images = []
        img = fm.get("img")
        if images and img != images[0]:
            err(path, "img must be exactly the first entry of images")
        for photo in images:
            used_photos.add(photo)
            if not PHOTO_RE.match(photo):
                err(path, "photo path must start with /assets/img/shop/ and end with .jpg: %s" % photo)
            elif not os.path.isfile("." + photo):
                err(path, "photo file does not exist: %s" % photo)
        if len(images) != len(set(images)):
            err(path, "the same photo is listed twice")
        if "meska_url" in fm:
            url = fm["meska_url"]
            if not isinstance(url, str) or not MESKA_RE.match(url):
                err(path, "meska_url must be a full https://...meska.hu/... link in double quotes (or remove the line)")
            if not body:
                err(path, "Meska item without a description in the body")
        if "![" in body:
            err(path, "the body must contain only the description text, no image lines (the layout shows the photos)")
        if "{{" in body or "{%" in body:
            err(path, "the body must not contain {{ or {%")
        for bad in ("date", "feature-img", "tags"):
            if bad in fm:
                warn(path, "unexpected front matter field: %s" % bad)

# pairs
for (lang, slug) in sorted(items):
    other = "en" if lang == "hu" else "hu"
    folder = "_portfolio" if other == "hu" else "_portfolio/en"
    if (other, slug) not in items:
        err("%s/%s.md" % (folder, slug), "missing: every item needs a file with the same name in both languages")
        continue
    if lang != "hu":
        continue
    fm_hu, body_hu = items[("hu", slug)]
    fm_en, body_en = items[("en", slug)]
    where = "_portfolio/%s.md vs _portfolio/en/%s.md" % (slug, slug)
    if fm_hu.get("order") != fm_en.get("order"):
        err(where, "order must be the same in both languages")
    if fm_hu.get("images") != fm_en.get("images"):
        err(where, "images lists must be the same in both languages")
    if fm_hu.get("meska_url") != fm_en.get("meska_url"):
        err(where, "meska_url must be the same in both languages (both present and equal, or both absent)")
    if bool(body_hu) != bool(body_en):
        err(where, "one language has a description and the other has none")
    if body_hu and body_hu == body_en and len(body_hu) > 60:
        err(where, "NOT TRANSLATED: the descriptions are identical")
    if fm_hu.get("title") == fm_en.get("title") and len(str(fm_hu.get("title"))) > 40:
        warn(where, "the titles are identical; check that the name was translated")

# photos not used by any item
for root, _dirs, files in os.walk("assets/img/shop"):
    for name in files:
        p = "/" + os.path.join(root, name).replace(os.sep, "/")
        if p not in used_photos:
            warn(p, "photo is not used by any shop item")

for line in errors + warnings:
    print(line)
if errors:
    print("FAILED: %d error(s). Fix them and run the checker again." % len(errors))
    sys.exit(1)
count = len([k for k in items if k[0] == "hu"])
print("OK: %d item(s) checked, no errors." % count)