#!/usr/bin/env python3
"""Build index.html from data/apps.json.

Edit data/apps.json (apps, links, privacy pages), then run:

    python3 tools/build.py

To open an app's public TestFlight beta, set "testflightLive": true on it.
Until then the card shows "iOS soon" and no link, because Apple's join page
says "Not Found" until a build passes beta review.
"""
import html
import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = json.loads((ROOT / 'data' / 'apps.json').read_text())

PLATFORM = {
    'android': ('fa-brands fa-android', 'Android'),
    'ios': ('fa-brands fa-apple', 'iOS'),
    'windows': ('fa-brands fa-windows', 'Windows'),
    'web': ('fa-solid fa-globe', 'Web'),
}


def e(text):
    return html.escape(str(text), quote=True)


def ext(url):
    return ' target="_blank" rel="noopener"' if url.startswith('http') else ''


def short_name(name):
    return name.split(':')[0].split(' - ')[0].strip()


def icon(app, cls='app-icon', size=60):
    if app.get('icon'):
        return f'<img class="{cls}" src="{e(app["icon"])}" alt="" width="{size}" height="{size}" loading="lazy" />'
    letter = e(short_name(app['name'])[:1])
    return f'<span class="{cls} app-icon-letter" style="width:{size}px;height:{size}px" aria-hidden="true">{letter}</span>'


def actions(app):
    links = app['links']
    out = []
    if links.get('play'):
        out.append(f'<a class="btn-store play" href="{e(links["play"])}"{ext(links["play"])}>'
                   '<i class="fa-brands fa-google-play"></i> Google Play</a>')
    if links.get('msstore'):
        out.append(f'<a class="btn-store ms" href="{e(links["msstore"])}"{ext(links["msstore"])}>'
                   '<i class="fa-brands fa-microsoft"></i> Microsoft Store</a>')
    if links.get('testflight'):
        if app.get('testflightLive'):
            out.append(f'<a class="btn-store tf" href="{e(links["testflight"])}" target="_blank" rel="noopener">'
                       '<i class="fa-brands fa-apple"></i> TestFlight beta</a>')
        else:
            out.append('<span class="btn-store soon" title="The iOS version is in review. A public beta link will appear here.">'
                       '<i class="fa-brands fa-apple"></i> iOS · soon</span>')
    if links.get('web'):
        out.append(f'<a class="btn-store web" href="{e(links["web"])}"{ext(links["web"])}>'
                   '<i class="fa-solid fa-arrow-up-right-from-square"></i> Open</a>')
    if links.get('github'):
        out.append(f'<a class="btn-store gh" href="{e(links["github"])}" target="_blank" rel="noopener">'
                   '<i class="fa-brands fa-github"></i> Source</a>')
    small = []
    if links.get('details'):
        small.append(f'<a href="{e(links["details"])}">Details</a>')
    if links.get('privacy'):
        small.append(f'<a href="{e(links["privacy"])}">Privacy</a>')
    if links.get('terms'):
        small.append(f'<a href="{e(links["terms"])}">Terms</a>')
    if links.get('support'):
        small.append(f'<a href="{e(links["support"])}">Support</a>')
    return '\n'.join(out), ' · '.join(small)


def card(app):
    stores, small = actions(app)
    plats = ''.join(f'<span class="plat" title="{PLATFORM[p][1]}"><i class="{PLATFORM[p][0]}"></i> {PLATFORM[p][1]}</span>'
                    for p in app['platforms'])
    hl = ''.join(f'<li>{e(h)}</li>' for h in app['highlights'])
    tags = ' '.join(app['tags'])
    search = e(' '.join([app['name'], app['category'], app['description'], tags, *app['highlights']]).lower())
    filters = ' '.join([app['type'], *app['platforms']])
    return f'''
      <article class="app" data-filter="{filters}" data-search="{search}">
        <div class="app-head">
          {icon(app)}
          <div class="app-title">
            <h3>{e(app["name"])}</h3>
            <p class="app-cat">{e(app["category"])}</p>
          </div>
        </div>
        <div class="plats">{plats}</div>
        <p class="app-desc">{e(app["description"])}</p>
        <ul class="app-hl">{hl}</ul>
        <div class="app-actions">
          {stores}
        </div>
        {f'<p class="app-small">{small}</p>' if small else ''}
      </article>'''


def legal_row(name, icon_html, privacy, second):
    return f'''
        <li class="legal-row">
          {icon_html}
          <span class="legal-name">{e(name)}</span>
          <span class="legal-links"><a href="{e(privacy)}">Privacy</a>{second}</span>
        </li>'''


def legal(apps):
    rows = []
    for app in apps:
        links = app['links']
        if not links.get('privacy'):
            continue
        second = ''
        if links.get('terms'):
            second = f'<a href="{e(links["terms"])}">Terms</a>'
        elif links.get('support'):
            second = f'<a href="{e(links["support"])}">Support</a>'
        rows.append(legal_row(short_name(app['name']), icon(app, 'legal-icon', 32), links['privacy'], second))
    for item in DATA.get('legalOnly', []):
        rows.append(legal_row(item['name'], f'<img class="legal-icon" src="{e(item["icon"])}" alt="" width="32" height="32" loading="lazy" />',
                              item['privacy'], f'<a href="{e(item["terms"])}">Terms</a>'))
    return ''.join(rows)


def build():
    apps = DATA['apps']
    count = len(apps)
    on_play = sum(1 for a in apps if a['links'].get('play'))
    on_ms = sum(1 for a in apps if a['links'].get('msstore'))
    on_ios = sum(1 for a in apps if 'ios' in a['platforms'])
    games = sum(1 for a in apps if a['type'] == 'game')
    filters = [
        ('all', 'All', count), ('game', 'Games', games), ('tool', 'Tools', count - games),
        ('android', 'Android', sum(1 for a in apps if 'android' in a['platforms'])),
        ('ios', 'iOS', on_ios),
        ('windows', 'Windows', sum(1 for a in apps if 'windows' in a['platforms'])),
        ('web', 'Web', sum(1 for a in apps if 'web' in a['platforms'])),
    ]
    pills = ''.join(f'<button class="pill{" active" if k == "all" else ""}" data-key="{k}" aria-pressed="{"true" if k == "all" else "false"}">'
                    f'{label} <span>{n}</span></button>' for k, label, n in filters)
    cards = ''.join(card(a) for a in apps)
    page = (ROOT / 'tools' / 'template.html').read_text()
    for key, value in {
        '{{COUNT}}': str(count), '{{ON_PLAY}}': str(on_play), '{{ON_MS}}': str(on_ms), '{{ON_IOS}}': str(on_ios),
        '{{PILLS}}': pills, '{{CARDS}}': cards, '{{LEGAL}}': legal(apps), '{{YEAR}}': str(date.today().year),
        '{{EMAIL}}': e(DATA['email']), '{{PLAY_DEV}}': e(DATA['playDeveloper']), '{{GITHUB}}': e(DATA['github']),
        '{{PORTFOLIO}}': e(DATA['portfolio']),
    }.items():
        page = page.replace(key, value)
    assert '{{' not in page, page[page.index('{{'):page.index('{{') + 40]
    (ROOT / 'index.html').write_text(page)
    print(f'index.html: {count} apps')


if __name__ == '__main__':
    build()
