# -*- coding: utf-8 -*-
"""Parse les extraits OSM de Mbanza-Ngungu et genere roads.js pour le jeu Luvaka."""
import xml.etree.ElementTree as ET
import json, math, os

HERE = os.path.dirname(os.path.abspath(__file__))
FILES = ["mbanza.xml", "mbanza_b.xml", "mbanza_c.xml"]

# Origine locale (metres) au centre de la zone de jeu
LON0, LAT0 = 14.85, -5.2585
MPD_LAT = 110574.0
MPD_LON = 111320.0 * math.cos(math.radians(LAT0))

def xy(lon, lat):
    return ((lon - LON0) * MPD_LON, (LAT0 - lat) * MPD_LAT)

nodes = {}      # id -> (lon, lat, tags)
ways = {}       # id -> (refs, tags)

def parse(f):
    tree = ET.parse(os.path.join(HERE, f))
    for el in tree.getroot():
        if el.tag == "node":
            tags = {t.get("k"): t.get("v") for t in el.findall("tag")}
            nodes[el.get("id")] = (float(el.get("lon")), float(el.get("lat")), tags)
        elif el.tag == "way":
            refs = [nd.get("ref") for nd in el.findall("nd")]
            tags = {t.get("k"): t.get("v") for t in el.findall("tag")}
            ways[el.get("id")] = (refs, tags)

for f in FILES:
    parse(f)

print("nodes:", len(nodes), "ways:", len(ways))

WIDTHS = {
    "primary": 13, "primary_link": 8, "secondary": 11, "secondary_link": 7,
    "tertiary": 9, "tertiary_link": 6, "residential": 7.5, "unclassified": 7,
    "living_street": 6, "service": 5, "pedestrian": 5, "footway": 2.5,
    "path": 2, "track": 4, "steps": 2.5, "cycleway": 2.5, "bridleway": 2,
    "motorway": 14, "trunk": 13, "trunk_link": 8, "busway": 8,
}
SKIP = {"proposed", "construction", "raceway", "escape", "corridor", "platform"}

roads = []
for wid, (refs, tags) in ways.items():
    hw = tags.get("highway")
    if not hw or hw in SKIP:
        continue
    pts = []
    for r in refs:
        if r in nodes:
            lon, lat, _ = nodes[r]
            x, z = xy(lon, lat)
            pts.append((round(x, 1), round(z, 1)))
    if len(pts) < 2:
        continue
    # longueur mini 8 m
    L = sum(math.dist(pts[i], pts[i+1]) for i in range(len(pts)-1))
    if L < 8:
        continue
    roads.append({
        "name": tags.get("name", ""),
        "type": hw,
        "w": WIDTHS.get(hw, 6),
        "pts": pts,
    })

print("routes retenues:", len(roads))

# ---------- Points d'interet ----------
POI_CATS = {"marketplace": "marche", "place_of_worship": "culte", "school": "ecole",
            "hospital": "sante", "clinic": "sante", "pharmacy": "pharmacy",
            "university": "universite", "college": "universite", "kindergarten": "ecole"}

pois = []
seen = set()

def add_poi(name, cat, lon, lat, desc=""):
    x, z = xy(lon, lat)
    key = (name.lower()[:20], round(x/80), round(z/80))
    if key in seen:
        return
    seen.add(key)
    pois.append({"name": name, "cat": cat, "x": round(x, 1), "z": round(z, 1), "desc": desc})

for wid, (refs, tags) in ways.items():
    cat = POI_CATS.get(tags.get("amenity"))
    nm = tags.get("name")
    if cat and nm and refs:
        pts = [nodes[r] for r in refs if r in nodes]
        if pts:
            lon = sum(p[0] for p in pts) / len(pts)
            lat = sum(p[1] for p in pts) / len(pts)
            add_poi(nm, cat, lon, lat)

for nid, (lon, lat, tags) in nodes.items():
    cat = POI_CATS.get(tags.get("amenity"))
    nm = tags.get("name")
    if cat and nm:
        add_poi(nm, cat, lon, lat)

# ---------- Lieux manuels (une "evocation", comme Moto Wewa) ----------
def find_poi(sub, cat=None):
    for p in pois:
        if sub.lower() in p["name"].lower() and (cat is None or p["cat"] == cat):
            return p
    return None

uk = None
for wid, (refs, tags) in ways.items():
    if tags.get("name", "").startswith("Universit") and tags.get("amenity") == "university":
        pts = [nodes[r] for r in refs if r in nodes]
        if pts:
            lon = sum(p[0] for p in pts) / len(pts)
            lat = sum(p[1] for p in pts) / len(pts)
            uk = (lon, lat)
            break

manual = []
if uk:
    manual.append({"name": "Université Kongo — Nouveau Campus", "cat": "universite",
                   "lon": uk[0], "lat": uk[1],
                   "desc": "9 facultés, siège administratif de l'UK. Résidences estudiantines."})
    # Résidence du joueur : à côté du campus
    manual.append({"name": "Résidence — chez l'oncle", "cat": "maison",
                   "lon": uk[0] + 0.0018, "lat": uk[1] + 0.0012,
                   "desc": "Ton lit, ta moustiquaire, ton petit courant d'air."})

# ISP : pas encore sur OSM -> on la place au centre-ville (evocation)
manual.append({"name": "ISP Mbanza-Ngungu", "cat": "universite",
               "lon": 14.8685, "lat": -5.2505,
               "desc": "Institut Supérieur Pédagogique, ouvert en 1981 : le premier établissement supérieur du Kongo-Central."})
manual.append({"name": "Cyber Café MwegISA", "cat": "cyber",
               "lon": 14.8678, "lat": -5.2512,
               "desc": "Impressions, forfaits 1h, et le ventilateur qui grince."})
if uk:
    manual.append({"name": "Cantina du campus", "cat": "cantina",
                   "lon": uk[0] + 0.0011, "lat": uk[1] + 0.0009,
                   "desc": "Foufou, poisson sec, et le thé à 200 francs."})

for m in manual:
    add_poi(m["name"], m["cat"], m["lon"], m["lat"], m["desc"])

# descriptions pour certains POI reels
DESCS = {
    "marche central": "Le cœur commerçant de Mbanza-Ngungu : tomates, pagnes, crédit de la semaine.",
    "lycée bankazi": "Grand lycée de la ville, classes bondées, réputation solide.",
    "tribunal de paix": "Le tribunal du territoire, juste à côté de la place.",
    "parking central": "Les taxis et motos s'y garent en désordre.",
}
for p in pois:
    low = p["name"].lower()
    for k, v in DESCS.items():
        if k in low and not p["desc"]:
            p["desc"] = v

print("POI:", len(pois))
for p in pois[:40]:
    print("   -", p["name"], "|", p["cat"])

out = {"roads": roads, "pois": pois, "origin": [LON0, LAT0]}
with open(os.path.join(HERE, "roads.js"), "w", encoding="utf-8") as f:
    f.write("window.WEWA_DATA = ")
    json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    f.write(";\n")
print("ecrit:", os.path.join(HERE, "roads.js"))
