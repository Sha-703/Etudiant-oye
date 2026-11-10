# -*- coding: utf-8 -*-
"""Parse les extraits OSM de Mbanza-Ngungu et genere roads.js pour le jeu Luvaka."""
import xml.etree.ElementTree as ET
import json, math, os

HERE = os.path.dirname(os.path.abspath(__file__))
FILES = ["mbanza.xml", "mbanza_b.xml", "mbanza_c.xml", "mbanza_d.xml", "mbanza_e.xml", "mbanza_f.xml"]

# Origine locale (metres) au centre de la zone de jeu
LON0, LAT0 = 14.85, -5.2585
MPD_LAT = 110574.0
MPD_LON = 111320.0 * math.cos(math.radians(LAT0))

def xy(lon, lat):
    return ((lon - LON0) * MPD_LON, (LAT0 - lat) * MPD_LAT)

nodes = {}      # id -> (lon, lat, tags)
ways = {}       # id -> (refs, tags)
rels = {}       # id -> (way_refs, tags)

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
        elif el.tag == "relation":
            mrefs = [m.get("ref") for m in el.findall("member") if m.get("type") == "way"]
            tags = {t.get("k"): t.get("v") for t in el.findall("tag")}
            rels[el.get("id")] = (mrefs, tags)

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

# ---------- Chemin de fer Matadi-Kinshasa (vraie ligne OSM) ----------
rails = []
for wid, (refs, tags) in ways.items():
    if tags.get("railway") not in ("rail", "light_rail"):
        continue
    pts = []
    for r in refs:
        if r in nodes:
            lon, lat, _ = nodes[r]
            x, z = xy(lon, lat)
            pts.append((round(x, 1), round(z, 1)))
    if len(pts) < 2:
        continue
    L = sum(math.dist(pts[i], pts[i+1]) for i in range(len(pts)-1))
    if L < 20:
        continue
    rails.append({"name": tags.get("name", ""), "pts": pts})
print("segments de voie:", len(rails),
      "| longueur totale:", round(sum(
          sum(math.dist(r["pts"][i], r["pts"][i+1]) for i in range(len(r["pts"])-1))
          for r in rails) / 1000, 1), "km")

stations = []
for wid, (refs, tags) in ways.items():
    if tags.get("railway") != "station":
        continue
    pts = [nodes[r] for r in refs if r in nodes]
    if len(pts) < 2:
        continue
    lon = sum(p[0] for p in pts) / len(pts)
    lat = sum(p[1] for p in pts) / len(pts)
    x, z = xy(lon, lat)
    a0 = xy(pts[0][0], pts[0][1])
    a1 = xy(pts[1][0], pts[1][1])
    ang = math.atan2(a1[0] - a0[0], a1[1] - a0[1])
    length = sum(math.dist(xy(pts[i][0], pts[i][1]), xy(pts[i+1][0], pts[i+1][1]))
                 for i in range(len(pts)-1))
    stations.append({"name": tags.get("name", ""), "x": round(x, 1), "z": round(z, 1),
                     "ang": round(ang, 3), "len": round(length, 1)})
print("stations:", [(s["name"], s["x"], s["z"]) for s in stations])

crossings = []
for nid, (lon, lat, tags) in nodes.items():
    if tags.get("railway") == "level_crossing":
        x, z = xy(lon, lat)
        crossings.append({"x": round(x, 1), "z": round(z, 1)})
print("passages a niveau:", len(crossings))

# ---------- Batiments reels (empreintes OSM) : la vraie architecture ----------
# On garde les polygones fermes pres de la ville (bbox des routes + 250 m)
rx = [p[0] for r in roads for p in r["pts"]]
rz = [p[1] for r in roads for p in r["pts"]]
RX0, RX1 = min(rx) - 250, max(rx) + 250
RZ0, RZ1 = min(rz) - 250, max(rz) + 250

blds = []
for wid, (refs, tags) in ways.items():
    if "building" not in tags:
        continue
    pts = []
    for r in refs:
        if r in nodes:
            lon, lat, _ = nodes[r]
            x, z = xy(lon, lat)
            pts.append((round(x, 1), round(z, 1)))
    if len(pts) < 4:
        continue
    if pts[0] == pts[-1]:          # polygone ferme : on retire le point duplique
        pts = pts[:-1]
    if len(pts) < 3:
        continue
    xs = [p[0] for p in pts]
    zs = [p[1] for p in pts]
    cx, cz = sum(xs) / len(xs), sum(zs) / len(zs)
    if not (RX0 < cx < RX1 and RZ0 < cz < RZ1):
        continue
    if max(xs) - min(xs) > 130 or max(zs) - min(zs) > 130:   # tres grands blocs : ignores
        continue
    flat = []
    for p in pts:
        flat.extend(p)
    blds.append(flat)
print("batiments reels:", len(blds))

# ---------- Batiments nommes (pancartes / lieux reconnus) ----------
bldNames = []
for wid, (refs, tags) in ways.items():
    if "building" not in tags:
        continue
    nm = tags.get("name")
    if not nm or len(nm) < 3 or len(nm) > 80:
        continue
    pts = []
    for r in refs:
        if r in nodes:
            lon, lat, _ = nodes[r]
            x, z = xy(lon, lat)
            pts.append((round(x, 1), round(z, 1)))
    if len(pts) < 4:
        continue
    if pts[0] == pts[-1]:
        pts = pts[:-1]
    if len(pts) < 3:
        continue
    flat = []
    for p in pts:
        flat.extend(p)
    bldNames.append({"name": nm, "kind": tags.get("building", ""), "pts": flat})
print("batiments nommes:", len(bldNames))

# ---------- Points d'interet ----------
POI_CATS = {"marketplace": "marche", "place_of_worship": "culte", "school": "ecole",
            "hospital": "sante", "clinic": "sante", "pharmacy": "pharmacy",
            "library": "universite",
            "university": "universite", "college": "universite", "kindergarten": "ecole",
            "stadium": "stade", "sports_centre": "stade", "park": "parc"}

BUILDING_CATS = {"hospital": "sante", "clinic": "sante", "school": "ecole",
                 "university": "universite", "church": "culte", "chapel": "culte"}

def poi_cat(tags):
    return (POI_CATS.get(tags.get("amenity")) or POI_CATS.get(tags.get("leisure"))
            or BUILDING_CATS.get(tags.get("building")))

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
    cat = poi_cat(tags)
    nm = tags.get("name")
    if cat and nm and refs:
        pts = [nodes[r] for r in refs if r in nodes]
        if pts:
            lon = sum(p[0] for p in pts) / len(pts)
            lat = sum(p[1] for p in pts) / len(pts)
            add_poi(nm, cat, lon, lat)

for nid, (lon, lat, tags) in nodes.items():
    cat = poi_cat(tags)
    nm = tags.get("name")
    if cat and nm:
        add_poi(nm, cat, lon, lat)

# relations (ex : Hôpital Nsona-Nkulu = multipolygone building=hospital)
for rid, (mrefs, tags) in rels.items():
    cat = poi_cat(tags)
    nm = tags.get("name")
    if not (cat and nm):
        continue
    pts = []
    for wr in mrefs:
        if wr in ways:
            for r in ways[wr][0]:
                if r in nodes:
                    pts.append(nodes[r])
    if len(pts) < 3:
        continue
    lon = sum(p[0] for p in pts) / len(pts)
    lat = sum(p[1] for p in pts) / len(pts)
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
               "lon": 14.857064, "lat": -5.268728,   # ROND-POINT I.S.P. -- entree du campus (map.osm)
               "desc": "Institut Supérieur Pédagogique, le premier établissement supérieur du Kongo-Central. Le campus : home ISP, home étudiant, rectorat."})
manual.append({"name": "Cyber Café MwegISA", "cat": "cyber",
               "lon": 14.8678, "lat": -5.2512,
               "desc": "Impressions, forfaits 1h, et le ventilateur qui grince."})
if uk:
    manual.append({"name": "Cantina du campus", "cat": "cantina",
                   "lon": uk[0] + 0.0011, "lat": uk[1] + 0.0009,
                   "desc": "Foufou, poisson sec, et le thé à 200 francs."})

# Stade : non tagge dans le rayon -> vraies coord Nominatim (avenue Nsasa)
if not any(p["cat"] == "stade" for p in pois):
    manual.append({"name": "Stade de Mbanza-Ngungu", "cat": "stade",
                   "lon": 14.8594804, "lat": -5.2490186,
                   "desc": "Le stade de la ville, avenue Nsasa : matchs et fêtes de la ligue du Kongo-Central."})

for m in manual:
    add_poi(m["name"], m["cat"], m["lon"], m["lat"], m["desc"])

# Les gares deviennent des POI (pour « Où est la gare ? »)
for st in stations:
    if st["name"]:
        lon = LON0 + st["x"] / MPD_LON
        lat = LAT0 - st["z"] / MPD_LAT
        add_poi(st["name"], "gare", lon, lat)

# descriptions pour certains POI reels
DESCS = {
    "gare centrale": "Gare de Mbanza-Ngungu (ex-Thysville), étape principale de la ligne Matadi-Kinshasa, en service depuis 1898.",
    "hôpital nsona": "Hôpital général de référence de la ville, quartier Mvela.",
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

out = {"roads": roads, "pois": pois, "rails": rails, "stations": stations,
       "crossings": crossings, "blds": blds, "bldNames": bldNames, "origin": [LON0, LAT0]}
with open(os.path.join(HERE, "roads.js"), "w", encoding="utf-8") as f:
    f.write("window.WEWA_DATA = ")
    json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    f.write(";\n")
print("ecrit:", os.path.join(HERE, "roads.js"))
