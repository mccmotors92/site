#!/usr/bin/env python3
"""Génère une page par auto (v/<id>.html) et le plan du site.

À relancer après chaque modification du stock dans index.html :
    python3 outils/pages_partage.py

Chaque page v/<id>.html contient la fiche en texte (titre, prix, description,
caractéristiques, travaux, photos) et des données structurées : c'est elle que
Google indexe. Un visiteur humain est aussitôt renvoyé vers la fiche complète
du site (/#vehicule-<id> ou /#projet-<id>) ; les robots restent sur la page.
Sert aussi d'aperçu pour les partages (WhatsApp, mail, réseaux).
"""
import json, re, html, os, datetime

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://mccmotors.fr"
e = html.escape

s = open(os.path.join(RACINE, "index.html"), encoding="utf-8").read()
D = json.loads(re.search(r'<script id="donnees" type="application/json">\n(.*?)\n</script>', s, re.S).group(1))
C = D["contact"]

os.makedirs(os.path.join(RACINE, "v"), exist_ok=True)
for f in os.listdir(os.path.join(RACINE, "v")):
    if f.endswith(".html"):
        os.remove(os.path.join(RACINE, "v", f))

BOTS = r"bot|crawl|spider|slurp|google|bing|yandex|duckduck|facebookexternalhit|whatsapp|telegram|twitter|linkedin|preview"

GABARIT = """<!DOCTYPE html>
<html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{titre}</title>
<meta name="description" content="{desc}">
<meta property="og:type" content="product">
<meta property="og:site_name" content="MCC Motors">
<meta property="og:title" content="{titre}">
<meta property="og:description" content="{desc}">
<meta property="og:image" content="{image}">
<meta property="og:url" content="{url}">
<meta name="twitter:card" content="summary_large_image">
<link rel="canonical" href="{url}">
<link rel="icon" href="/favicon.png" type="image/png">
<script>if(!/{bots}/i.test(navigator.userAgent||''))location.replace({cible_js});</script>
<script type="application/ld+json">{ld}</script>
<style>
body{{margin:0;background:#0f241b;color:#ede3cc;font:16px/1.6 Georgia,serif}}
main{{max-width:900px;margin:0 auto;padding:40px 22px 70px}}
a{{color:#c49a6c}} .sur{{font:12px sans-serif;letter-spacing:.25em;text-transform:uppercase;color:#c4b99f}}
h1{{font-size:40px;font-weight:400;margin:8px 0 6px}} .acc{{font-style:italic;color:#cdc3ab;font-size:19px}}
.prix{{font-size:30px;margin:22px 0 2px}} .note{{font:13px sans-serif;color:#a3ad9c;margin:4px 0}}
img{{width:100%;height:auto;display:block;margin:0 0 10px}} .photos{{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:26px 0}}
table{{border-collapse:collapse;width:100%;margin:20px 0}} td{{border-top:1px solid #2b4537;padding:8px 10px 8px 0;vertical-align:top}}
td:first-child{{font:12px sans-serif;letter-spacing:.18em;text-transform:uppercase;color:#a3ad9c;width:38%}}
h2{{font-weight:400;font-size:24px;margin:34px 0 8px}} li{{margin:3px 0}}
.bouton{{display:inline-block;margin:26px 0;padding:14px 26px;border:1px solid #c49a6c;text-decoration:none;font:12px sans-serif;letter-spacing:.24em;text-transform:uppercase}}
</style>
</head><body><main>
<p class="sur"><a href="{site}/">MCC Motors</a> · {rubrique}</p>
<h1>{nom}</h1>
<p class="acc">{accroche}</p>
<p class="prix">{prix}</p>{notes}
<p><a class="bouton" href="{cible}">Voir la fiche complète</a></p>
{photo1}
{description}
{carac}
{travaux}
{photos}
<h2>Avec cette auto</h2>
<ul>{services}</ul>
<h2>Contact</h2>
<p>Téléphone : <a href="tel:+33185500242">{tel}</a> · E-mail : <a href="mailto:{mail}">{mail}</a><br>Siège : {siege}. Atelier dans les Yvelines, sur rendez-vous, après un premier échange.</p>
<p><a href="{site}/">Toutes nos voitures</a></p>
</main></body></html>
"""

def travaux_html(tv):
    out = []
    for x in tv or []:
        if isinstance(x, dict):
            out.append(f"<li>{e(x.get('titre',''))} : " + " ; ".join(e(p) for p in x.get("points", [])) + "</li>")
        else:
            out.append(f"<li>{e(x)}</li>")
    return "".join(out)

def prix_num(p):
    d = re.sub(r"[^\d]", "", p or "")
    return int(d) if d else None

urls = [SITE + "/"]
n = 0
for liste, pref, rub, ttrav in (("vehicules", "vehicule", "Nos voitures", "Travaux réalisés"),
                                 ("projets", "projet", "Autos à restaurer", "Travaux à prévoir")):
    for v in D[liste]:
        if v.get("masque"):
            continue
        nom = " ".join(x for x in (v["marque"], v["modele"], v.get("annee", "")) if x)
        vendu = v["statut"] == "vendu"
        prix = "Vendue" if vendu else (v.get("prix") or "Nous consulter")
        pn = None if vendu else prix_num(v.get("prix"))
        titre = f"{nom} à vendre — {prix} | MCC Motors" if not vendu else f"{nom} — vendue | MCC Motors"
        desc = v.get("accroche", "")
        if v.get("prix_note") and not vendu:
            desc += " " + v["prix_note"]
        image = v.get("vignette") or (v.get("photos") or [None])[0] or D["visuel_generique"]
        image = image.split("?")[0]
        url = f"{SITE}/v/{v['id']}.html"
        cible = f"{SITE}/#{pref}-{v['id']}"
        photos = [p.split("?")[0] for p in (v.get("photos") or [])]
        notes = ""
        if pn:
            notes += '<p class="note">Prix toutes taxes comprises, hors frais d\'immatriculation.</p>'
        if v.get("prix_note") and not vendu:
            notes += f'<p class="note">{e(v["prix_note"])}</p>'
        car = v.get("caracteristiques") or {}
        carac = "<table>" + "".join(f"<tr><td>{e(k)}</td><td>{e(str(x))}</td></tr>" for k, x in car.items()) + "</table>" if car else ""
        tv = travaux_html(v.get("travaux"))
        srv = ["Présentation de l'auto sur pont.", "Livraison à tarif préférentiel.", "Logistique dans le monde entier, en porte-à-porte."] if pref == "projet" else \
              ["Essai possible, et présentation de l'auto sur pont.", "Garantie possible, en option.", "Livraison à tarif préférentiel.", "Logistique dans le monde entier, en porte-à-porte."]
        alt = e(nom)
        ld = {"@context": "https://schema.org", "@type": "Car", "name": nom, "brand": {"@type": "Brand", "name": v["marque"]},
              "model": v["modele"], "description": desc, "url": url,
              "image": [f"{SITE}/{p}" for p in (photos[:6] or [image])]}
        if v.get("annee"): ld["vehicleModelDate"] = v["annee"]
        if v.get("couleur"): ld["color"] = v["couleur"]
        if pn:
            ld["offers"] = {"@type": "Offer", "price": pn, "priceCurrency": "EUR", "availability": "https://schema.org/InStock",
                            "itemCondition": "https://schema.org/UsedCondition", "url": url,
                            "seller": {"@type": "AutoDealer", "name": "MCC Motors", "telephone": "+33185500242", "url": SITE + "/"}}
        page = GABARIT.format(
            titre=e(titre), desc=e(desc), image=f"{SITE}/{image}", url=url, bots=BOTS, cible=cible, cible_js=json.dumps(cible),
            ld=json.dumps(ld, ensure_ascii=False).replace("</", "<\\/"), site=SITE, rubrique=rub, nom=e(nom),
            accroche=e(v.get("accroche", "")), prix=e(prix), notes=notes,
            photo1=f'<img src="{SITE}/{photos[0] if photos else image}" alt="{alt}">',
            description="".join(f"<p>{e(p)}</p>" for p in v.get("description", [])),
            carac=carac, travaux=(f"<h2>{ttrav}</h2><ul>{tv}</ul>" if tv else ""),
            photos=('<div class="photos">' + "".join(f'<img loading="lazy" src="{SITE}/{p}" alt="{alt}">' for p in photos[1:9]) + "</div>") if len(photos) > 1 else "",
            services="".join(f"<li>{x}</li>" for x in srv), tel=e(C.get("telephone", "")), mail=e(C.get("email", "")), siege=e(C.get("siege", "")))
        open(os.path.join(RACINE, "v", v["id"] + ".html"), "w", encoding="utf-8").write(page)
        urls.append(url)
        n += 1

jour = datetime.date.today().isoformat()
plan = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
plan += "".join(f"  <url><loc>{u}</loc><lastmod>{jour}</lastmod></url>\n" for u in urls)
plan += "</urlset>\n"
open(os.path.join(RACINE, "sitemap.xml"), "w", encoding="utf-8").write(plan)
print(f"{n} pages d'autos, sitemap de {len(urls)} adresses")
