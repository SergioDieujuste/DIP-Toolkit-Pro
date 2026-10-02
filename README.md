# DIP Toolkit Pro

Boîte à outils de diagnostic et de maintenance pour **Dépannage Informatique Plus**.
Application Python / PySide6 (Qt), actuellement pour **Windows**.

## Fonctions actuelles
Tableau de bord, diagnostic système, supervision temps réel (CPU/RAM/disque),
réseau, disques, imprimantes, sécurité, maintenance, rapport PDF, paramètres.

## Lancer en développement
Python **3.12** recommandé (3.14 est trop récent pour garantir PySide6 et PyInstaller).

```bat
py -3.12 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Compiler l'.exe
Double-cliquer sur `build.bat` (ou : `pip install -r requirements-dev.txt`
puis `pyinstaller "DIP Toolkit Pro.spec"`).
Résultat : `dist\DIP Toolkit Pro.exe`, un seul fichier à copier sur la clé USB.

## Où sont rangés les fichiers ?
| Type | En développement | Dans l'.exe |
|---|---|---|
| Logo, icônes, thème (embarqués) | `assets/` | dans l'.exe |
| `settings.json` (modifiable) | racine du projet | **à côté de l'.exe** (mode portable) |
| `company.json` (nom, logo, coordonnées du rapport) | racine du projet | **à côté de l'.exe** |

Si le dossier de l'.exe n'est pas modifiable, repli sur `%APPDATA%\DIP Toolkit Pro`.
Les chemins sont gérés par `src/utils/paths.py` : ne jamais écrire `"assets/..."` en dur.

## Personnaliser les rapports
Au premier rapport, un fichier `company.json` est créé à côté de l'application.
Ouvrez-le avec le Bloc-notes pour renseigner `phone`, `email`, `website`, `address`,
`tagline`, et éventuellement `logo` (chemin d'un autre logo png/jpg). Sans `logo`,
le logo DIP intégré est utilisé.

Le rapport PDF contient : fiche client et technicien, verdict global, synthèse à
voyants (Bon / À surveiller / Critique), recommandations automatiques, puis le détail
technique. Les seuils (disque 80 %/90 %, RAM 80 %/90 %, redémarrage 30 jours...) sont
regroupés en tête de `src/diagnostics/report_analysis.py`.

## Tests de démarrage
```bat
python -m unittest discover -s tests -v
```

## Structure
```
main.py                 point d'entrée
src/diagnostics/        collecte (report_data), analyse (report_analysis), PDF (report_info)
src/gui/                fenêtre, pages, widgets
src/utils/paths.py      chemins (développement / .exe / clé USB)
assets/                 logo, icônes, thème
tests/                  tests de démarrage
```

## Feuille de route
1. ✅ Socle reproductible (dépendances, build, chemins, tests)
2. ✅ Rapport PDF avec les vraies données, logo et voyants
3. Mises à jour, SMART, batterie, journaux d'événements
4. Version Mac (éventuellement)
