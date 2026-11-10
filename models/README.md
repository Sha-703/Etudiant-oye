# Personnages 3D (.glb) — optionnel

Sans ce dossier, le jeu garde ses personnages en cubes. Pour passer à de vrais personnages :

1. Mets tes fichiers `.glb` ici, dans `models/`.
2. Copie `models.example.json` en **`models.json`** et adapte les noms de fichiers.
3. Recharge le jeu. Si un fichier manque ou est cassé, il est ignoré (on garde les cubes pour celui-là).

## models.json

```json
{
  "players": [
    { "file": "junior.glb" },
    { "file": "bene.glb", "rotY": 3.1416 },
    null,
    { "file": "mwana.glb", "height": 1.65 }
  ],
  "walkers": [ { "file": "pieton1.glb" }, { "file": "pieton2.glb" } ]
}
```

- `players` : 4 entrées, dans l'ordre des étudiants du menu (Junior, Béné, Grâce, Mwana). `null` = garder les cubes.
- `walkers` : les piétons de la ville et du marché (le jeu en tire un au hasard).
- `height` (optionnel) : taille en mètres (1,75 par défaut). Le modèle est mis à l'échelle et posé au sol tout seul.
- `rotY` (optionnel) : rotation en radians si ton modèle ne regarde pas vers l'avant (3.1416 = demi-tour).
- `anims` (optionnel) : fichiers d'animation séparés, ex. `{ "idle": "idle.glb", "walk": "walk.glb", "run": "run.glb" }`.

## Animations
Le jeu cherche dans le .glb des animations dont le nom contient **idle** (repos), **walk** (marche) et **run** (course).
Si un modèle n'a que « walk », il se fige à l'arrêt. Sans aucune animation, il glisse (marche sans bouger les jambes).

## Où trouver / préparer des modèles
- **Mixamo** (compte Adobe gratuit) : personnage + animations (Idle, Walking, Running). Télécharge en FBX puis convertis en .glb (Blender ou `fbx2gltf`).
- **Quaternius**, **Kenney** (licence CC0), **Poly Pizza**, **Sketchfab** (filtre « téléchargeable », vérifie la licence).
- Dans Blender : change la peau, les vêtements et les cheveux pour des personnages congolais crédibles, puis exporte en glTF binaire (.glb).

## Conseils performance (surtout téléphone)
- 3 000 à 8 000 triangles par personnage, textures 512 à 1024 px.
- Compresse avec `gltf-transform optimize` (Draco/Meshopt, WebP) : le jeu sait lire ces formats.
- Bas/Moyen utilisent des matériaux légers ; Haut garde les matériaux réalistes du .glb.
