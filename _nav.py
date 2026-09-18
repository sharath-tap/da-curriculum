# -*- coding: utf-8 -*-
"""One nav bar, injected into every page. Run after rebuilding any page.
Idempotent: strips any nav it previously injected before adding the new one."""
import os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))

PAGES = [("teach","Teach"),("prepare","Prepare"),("reference","Reference"),
         ("interview","Interview"),("august","August B3"),("plan","Plan")]

CSS = """<style id="tapnav-css">
.tapnav{position:sticky;top:0;z-index:70;background:var(--nav-bg,rgba(255,255,255,.9));
 backdrop-filter:blur(14px);border-bottom:1px solid var(--hair,#ececec)}
.tapnav-in{max-width:var(--max,960px);margin:0 auto;padding:11px 28px;display:flex;
 align-items:center;gap:20px;flex-wrap:wrap}
.tapnav-home{font-family:var(--serif,Georgia,serif);font-size:16px;font-weight:600;
 color:var(--ink,#17191c);text-decoration:none;white-space:nowrap}
.tapnav-links{display:flex;gap:4px;flex-wrap:wrap;margin-left:auto}
.tapnav-links a{font-size:13.5px;font-weight:500;color:var(--slate,#777b86);
 text-decoration:none;padding:5px 11px;border-radius:8px}
.tapnav-links a:hover{background:var(--mist,#f2f2f3);color:var(--ink,#17191c)}
.tapnav-links a.on{background:var(--peach,#fbe1d1);color:var(--sienna,#5d2a1a);font-weight:600}
.tapnav a:focus-visible{outline:2px solid var(--sienna,#5d2a1a);outline-offset:2px}
/* a page may carry its own sticky bar (theme toggle, back link); stack it under this one */
nav:not(.tapnav){top:var(--tapnav-h,46px)!important}
@media (max-width:640px){.tapnav-in{padding:10px 18px}.tapnav-links{margin-left:0}}
</style>"""

SYNC = """<script id="tapnav-sync">(function(){function f(){try{
 var n=document.querySelector('.tapnav');
 if(n)document.documentElement.style.setProperty('--tapnav-h',n.offsetHeight+'px');}catch(e){}}
 f();addEventListener('resize',f);addEventListener('load',f);})();</script>"""

def nav_for(slug):
    links = "".join('\n  <a%s href="../%s/">%s</a>' % (' class="on"' if s == slug else "", s, lbl)
                    for s, lbl in PAGES)
    return ('<nav class="tapnav"><div class="tapnav-in">\n'
            ' <a class="tapnav-home" href="../">Data Analytics</a>\n'
            ' <div class="tapnav-links">%s\n </div>\n</div></nav>' % links)

def strip_old(s):
    s = re.sub(r'<style id="tapnav-css">.*?</style>\s*', "", s, flags=re.S)
    s = re.sub(r'<nav class="tapnav">.*?</nav>\s*', "", s, flags=re.S)
    s = re.sub(r'<script id="tapnav-sync">.*?</script>\s*', "", s, flags=re.S)
    # the old three-link bar inside the legacy nav on teach/prepare/plan
    s = re.sub(r'\s*<div class="xnav">.*?</div>\s*(?=\n)', "\n  ", s, flags=re.S)
    return s

changed = []
for slug, _ in PAGES:
    p = os.path.join(HERE, slug, "index.html")
    if not os.path.exists(p):
        print("  MISSING %s — skipped" % slug); continue
    s = open(p, encoding="utf-8").read()
    before = s
    s = strip_old(s)
    if "</head>" not in s: sys.exit("no </head> in %s" % slug)
    s = s.replace("</head>", CSS + "\n</head>", 1)
    m = re.search(r"<body[^>]*>", s)
    if not m: sys.exit("no <body> in %s" % slug)
    # keep any theme-restore script first
    after = s[m.end():]
    # put the nav after the anti-flash theme script (wherever it sits) but always
    # before any nav the page already had, so the two bars stack in the right order
    ins = m.end()
    sc = re.search(r"<script>\s*try\s*\{\s*var _t\s*=\s*localStorage.*?</script>", after, re.S)
    legacy = re.search(r"<nav(?![^>]*tapnav)", after)
    if sc and (legacy is None or sc.end() < legacy.start()):
        ins = m.end() + sc.end()
    s = s[:ins] + "\n" + nav_for(slug) + "\n" + SYNC + s[ins:]
    # validate
    assert s.count('class="tapnav"') == 1, slug
    assert s.count('id="tapnav-css"') == 1, slug
    assert s.count('id="tapnav-sync"') == 1, slug
    assert s.count("<nav") == s.count("</nav>"), "%s nav unbalanced" % slug
    for h in re.findall(r'href="(\.\./[^"]*)"', s):
        t = os.path.normpath(os.path.join(HERE, slug, h))
        if not (os.path.exists(t) or os.path.exists(os.path.join(t, "index.html"))):
            sys.exit("dead link %s in %s" % (h, slug))
    open(p, "w", encoding="utf-8").write(s)
    changed.append("%s (%+d bytes)" % (slug, len(s) - len(before)))
print("nav injected into %d pages:" % len(changed))
for c in changed: print("  -", c)
