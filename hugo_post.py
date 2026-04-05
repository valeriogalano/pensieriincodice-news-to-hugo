import re
from datetime import datetime

def slugify(text):
    text = text.lower()
    for src, dst in [
        ('àáâãäå', 'a'), ('èéêë', 'e'), ('ìíîï', 'i'),
        ('òóôõö', 'o'), ('ùúûü', 'u'), ('ç', 'c'), ('ñ', 'n'),
    ]:
        for ch in src:
            text = text.replace(ch, dst)
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'\s+', '-', text.strip())
    text = re.sub(r'-+', '-', text)
    return text[:80]


def _blockquote(text):
    lines = text.strip().splitlines()
    return '\n'.join(f'> {line}' if line.strip() else '>' for line in lines)


def generate_post(document, highlights, source_url, doc_tags, date=None):
    title = document['title']
    notes = (document.get('notes') or '').strip()
    if date is None:
        date = datetime.now().astimezone()
    date_iso = date.isoformat(timespec='seconds')

    all_tags = ['news', 'repost'] + [t for t in doc_tags if t != 'hugo-news']
    tags_yaml = '\n'.join(f'  - {t}' for t in all_tags)

    escaped_title = title.replace('"', '\\"')

    front_matter = f"""\
---
title: "{escaped_title}"
date: {date_iso}
featureImage: /images/pensieriincodice-locandina.png
categories:
  - News
tags:
{tags_yaml}
type: blog
author: Valerio Galano
source_url: {source_url}
draft: false
---"""

    body_parts = []

    if source_url:
        body_parts.append(f"*Fonte: [{source_url}]({source_url})*\n")

    if notes:
        body_parts.append(notes + "\n")

    visible_highlights = [h for h in highlights if (h.get('text') or '').strip()]
    for h in visible_highlights:
        body_parts.append(_blockquote(h['text']) + "\n")
        note = (h.get('note') or '').strip()
        if note:
            body_parts.append(note + "\n")

    body = '\n'.join(body_parts)
    content = f"{front_matter}\n\n{body}"

    date_prefix = date.strftime('%Y-%m-%d')
    filename = f"{date_prefix}-{slugify(title)}.md"

    return filename, content
