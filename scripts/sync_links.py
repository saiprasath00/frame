#!/usr/bin/env python3
"""Refresh FRAME's direct destination list from upstream public catalogues.

This runs in GitHub Actions. Only site/ gets deployed; synchronization code,
source provenance, and upstream addresses stay outside the web root.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import json
import re
import sys
from pathlib import Path
from urllib.error import URLError, HTTPError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'site' / 'links.json'
UPSTREAM_MARKDOWN = 'https://raw.githubusercontent.com/fmhy/edit/main/docs/video.md'
UPSTREAM_SITE = 'https://fmhy.net/video'
BANNED_HOSTS = {
    'rentry.co','rentry.org','paste.to','notebin.de','github.com','raw.githubusercontent.com',
    'www.reddit.com','reddit.com','discord.gg','discord.com','discordapp.com',
    't.me','telegram.me','telegram.dog','cse.google.com','docs.google.com','youtube.com',
    'youtu.be','greasyfork.org','bit.ly','tinyurl.com','linktr.ee','medium.com',
    'archive.org', 'fmhy.net', 'www.fmhy.net', 'fmhy.xyz',
}
SKIP_NAMES = {'note','2','3','4','5','6','7','8','9','status','source','mirror','mirrors',
              'telegram','discord','reddit','subreddit','features','feature','posters',
              'github','tools','wiki','docs','download guide','adblocker','adblock',
              'video download tools','general ddl sites','anime download cse','video torrent cse'}
GROUP_ORDER = {'movies':0,'fourk':1,'anime':2,'anidownload':3}
MARKDOWN_LINK = re.compile(r'\[([^\]]{1,150})\]\((https?://[^\s)]+)\)')
INDIRECT_WORDS = ('encoded', 'base64', 'password-protected', 'b64')


def canonical_name(name):
    return re.sub(r'[^a-z0-9]+', '', name.lower())


def clean_url(raw):
    if not isinstance(raw,str): return None
    raw = raw.strip().strip('<>')
    try:
        u = urlparse(raw)
        hostname = (u.hostname or '').lower().rstrip('.')
    except ValueError:
        return None
    if u.scheme != 'https' or not hostname or '.' not in hostname:
        return None
    if u.username or u.password or u.port not in (None,443):
        return None
    if hostname in BANNED_HOSTS or any(hostname.endswith('.' + host) for host in BANNED_HOSTS):
        return None
    if any(word in (u.path + u.fragment).lower() for word in INDIRECT_WORDS):
        return None
    if u.fragment: # avoid hidden redirect/decoder instructions
        return None
    if len(raw) > 300:
        return None
    return raw


def make_entry(name,url,group):
    name = re.sub(r'[\u200b\u200c\u200d\u2060\ufeff]', '', name or '').strip(' ⁠⭐🌟*\t')
    name = re.sub(r'\s+', ' ', name)
    url = clean_url(url)
    if (not name or len(name) > 55 or not url or group not in GROUP_ORDER
        or canonical_name(name) in SKIP_NAMES or 'fmhy' in canonical_name(name)):
        return None
    return (name,url,group)


def group_for_section(top,sub,line_text=''):
    t = top.lower(); s = sub.lower()
    if 'streaming sites' in t:
        if s == 'anime streaming': return 'anime'
        if s in ('stream aggregators','p-stream forks','dedicated-server') and re.search(r'\b4k\b',line_text,re.I):
            return 'fourk'
    if 'download sites' in t:
        if s == 'anime downloading': return 'anidownload'
        if not s: return 'movies'
    return None


def pick_link_pairs(line):
    """Return the actual websites, not secondary reference/status/mirror links."""
    links = list(MARKDOWN_LINK.finditer(line))
    if not links: return []
    first = links[0]
    pairs = [(first.group(1),first.group(2))]
    # Separate sites joined by 'or', e.g. A or B; never generic mirror [2].
    for idx, item in enumerate(links[1:],start=1):
        gap = line[links[idx-1].end():item.start()]
        if re.search(r'\bor\s+(?:\*\*)?\s*$',gap,re.I):
            pairs.append((item.group(1),item.group(2)))
    return pairs


def parse_markdown(source):
    top = sub = ''
    rows = []
    for raw in source.splitlines():
        heading = re.match(r'^(#{1,3})\s+(.*?)\s*$',raw)
        if heading:
            level,text = len(heading.group(1)), heading.group(2)
            plain = re.sub(r'[^\w\- ]+',' ',text).strip().lower()
            if level == 1:
                top = plain; sub = ''
            elif level == 2:
                sub = plain
            continue
        if not re.match(r'^\s*\*\s+',raw):
            continue
        if raw.lstrip().startswith('* 🌐') or raw.lstrip().startswith('* ↪'):
            continue
        if raw.lstrip().startswith('* **Note**'):
            continue
        category = group_for_section(top,sub,raw)
        if not category:
            continue
        for name,url in pick_link_pairs(raw):
            entry=make_entry(name,url,category)
            if entry: rows.append(entry)
    return unique(rows)


def parse_website(source):
    if BeautifulSoup is None:
        raise RuntimeError('Install beautifulsoup4 before parsing HTML')
    soup = BeautifulSoup(source,'html.parser')
    main = soup.select_one('.vp-doc') or soup.select_one('main')
    if not main:
        raise ValueError('Cannot find the public page content')
    top = sub = ''
    results=[]
    for node in main.find_all(['h2','h3','h4','li']):
        if node.name in ('h2','h3','h4'):
            heading = re.sub(r'[^\w\- ]+',' ',node.get_text(' ',strip=True)).lower().strip()
            if node.name=='h2':top=heading;sub=''
            elif node.name=='h3':sub=heading
            continue
        # Do not process nested list entries twice or navigation links.
        if node.find_parent('li'):
            continue
        raw = node.get_text(' ',strip=True)
        group = group_for_section(top,sub,raw)
        if not group or not node.find('a',href=True):
            continue
        anchors=node.find_all('a',href=True)
        if not anchors:continue
        chosen=[anchors[0]]
        for a in anchors[1:]:
            previous = a.previous_sibling
            # Only clearly marked named alternatives (not mirrors / references).
            if previous and re.search(r'\bor\s*$',str(previous).strip(),re.I):
                chosen.append(a)
        for a in chosen:
            entry=make_entry(a.get_text(' ',strip=True),a.get('href'),group)
            if entry:results.append(entry)
    return unique(results)


def unique(entries):
    seen=set(); output=[]
    for entry in entries:
        key=(entry[2],canonical_name(entry[0]))
        if key not in seen:
            seen.add(key);output.append(entry)
    return output


def fetch(url):
    req = Request(url, headers={'User-Agent':'Mozilla/5.0 (compatible; FRAME link refresh/1.0)','Accept':'text/html,text/plain'})
    with urlopen(req,timeout=25) as response:
        return response.read().decode('utf-8',errors='replace')


def existing():
    if not OUT.exists():return []
    content=json.loads(OUT.read_text(encoding='utf-8'))
    raw=content.get('entries',[]) if isinstance(content,dict) else content
    return unique([entry for e in raw if isinstance(e,list) and len(e)==3
                   if (entry:=make_entry(*e)) is not None])


def merge_sources(repo,site,previous):
    # Compare disagreements against the previous site snapshot. Whichever
    # source has changed relative to the old entry wins, otherwise repo wins.
    pre={(group,canonical_name(name)):(name,url,group) for name,url,group in previous}
    by_repo={(group,canonical_name(name)):(name,url,group) for name,url,group in repo}
    by_site={(group,canonical_name(name)):(name,url,group) for name,url,group in site}
    keys=set(by_repo)|set(by_site)
    final=[]
    for key in keys:
        a,b=by_repo.get(key),by_site.get(key)
        old=pre.get(key)
        if a and b and a[1]!=b[1] and old:
            if a[1]==old[1] and b[1]!=old[1]: final.append(b);continue
        final.append(a or b)
    return sorted(unique(final),key=lambda e:(GROUP_ORDER[e[2]],e[0].casefold()))


def run(args):
    previous=existing()
    repo=site=[]
    errors=[]
    try:
        repo=parse_markdown(Path(args.markdown_file).read_text(encoding='utf-8') if args.markdown_file else fetch(UPSTREAM_MARKDOWN))
        if len(repo)<40:raise ValueError(f'Only {len(repo)} links parsed: probable upstream structure change')
        print(f'Primary catalogue: {len(repo)} usable direct sites')
    except Exception as exc:
        errors.append(f'Primary catalogue: {exc}')
    try:
        site=parse_website(Path(args.html_file).read_text(encoding='utf-8') if args.html_file else fetch(UPSTREAM_SITE))
        if len(site)<40:raise ValueError(f'Only {len(site)} links parsed: probable upstream structure change')
        print(f'Published catalogue: {len(site)} usable direct sites')
    except Exception as exc:
        errors.append(f'Published catalogue: {exc}')
        site=[]
    if not repo and not site:
        raise SystemExit('Both catalogues unavailable. Existing site unchanged. ' + '; '.join(errors))
    fresh=merge_sources(repo,site,previous)
    if len(fresh) < 40 or not any(x[2]=='movies' for x in fresh):
        raise SystemExit('Refusing unusually small/broken update')
    result={'entries':[list(x) for x in fresh]}
    if [list(x) for x in previous] == result['entries']:
        print('No links changed, keeping last snapshot')
        return
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'Wrote {len(fresh)} direct sites to {OUT}')
    for msg in errors:print('Warning:',msg,file=sys.stderr)


if __name__=='__main__':
    cli=argparse.ArgumentParser()
    cli.add_argument('--markdown-file',help='Offline markdown fixture for testing')
    cli.add_argument('--html-file',help='Offline HTML fixture for testing')
    run(cli.parse_args())
