#!/usr/bin/env python3
"""Génère les pages de partage (aperçu WhatsApp, mail, réseaux) et le plan du site.

À relancer après chaque modification du stock dans index.html :
    python3 outils/pages_partage.py
Crée v/<id>.html pour chaque auto non masquée, et sitemap.xml.
"""
import json, re, html, os, datetime

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://mccmotors.fr"

s = open(os.path.join(RACINE, "index.html"), encoding="utf-8").read()
D = json.loads(re.search(r'<script id="donnees" type="application/json">\n(.*?)\n</script>', s, re.S).group(1))

os.makedirs(os.path.join(RACINE, "v"), exist_ok=True)
for f in os.listdir(os.path.join(RACINE, "v")):
    if f.endswith(".html"):
        os.remove(os.path.join(RACINE, "v", f))

GABARIT = """<!DOCTYPE html>
<html lang="fr"><head><meta charset="utf-8">
<title>{titre}</title>
<meta name="description" content="{desc}">
<meta property="og:type" content="product">
<meta property="og:site_name" content="MCC Motors">
<meta property="og:title" content="{titre}">
<meta property="og:description" content="{desc}">
<meta property="og:image" content="{image}">
<meta property="og:url" content="{url}">
<meta name="twitter:card" content="summary_large_image">
<link rel="canonical" href="{cible}">
<link rel="icon" href="/favicon.png" type="image/png">
<meta http-equiv="refresh" content="0; url={cible}">
<script>location.replace({cible_js});</script>
</head><body style="background:#0f241b;color:#ede3cc;font-family:sans-serif">
<p><a style="color:#c49a6c" href="{cible}">{titre}</a></p>
</body></html>
"""

urls = [SITE + "/"]
n = 0
for liste, pref in (("vehicules", "vehicule"), ("projets", "projet")):
    for v in D[liste]:
        if v.get("masque"):
            continue
        nom = " ".join(x for x in (v["marque"], v["modele"], v.get("annee", "")) if x)
        if v["statut"] == "vendu":
            prix = "Vendue"
        else:
            prix = v.get("prix") or "Nous consulter"
        titre = f"{nom} — {prix} | MCC Motors"
        desc = v.get("accroche", "")
        if v.get("prix_note") and v["statut"] != "vendu":
            desc += " " + v["prix_note"]
        image = v.get("vignette") or (v.get("photos") or [None])[0] or D["visuel_generique"]
        url = f"{SITE}/v/{v['id']}.html"
        cible = f"{SITE}/#{pref}-{v['id']}"
        page = GABARIT.format(titre=html.escape(titre), desc=html.escape(desc), image=f"{SITE}/{image}",
                              url=url, cible=cible, cible_js=json.dumps(cible))
        open(os.path.join(RACINE, "v", v["id"] + ".html"), "w", encoding="utf-8").write(page)
        urls.append(url)
        n += 1

jour = datetime.date.today().isoformat()
plan = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
plan += "".join(f"  <url><loc>{u}</loc><lastmod>{jour}</lastmod></url>\n" for u in urls)
plan += "</urlset>\n"
open(os.path.join(RACINE, "sitemap.xml"), "w", encoding="utf-8").write(plan)
print(f"{n} pages de partage, sitemap de {len(urls)} adresses")
