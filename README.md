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
| `company.json` + `logo_entreprise.png` (en-tête des rapports) | racine du projet | **à côté de l'.exe** |
| `historique.json` (liste des rapports générés) | racine du projet | **à côté de l'.exe** |

Si le dossier de l'.exe n'est pas modifiable, repli sur `%APPDATA%\DIP Toolkit Pro`.
Les chemins sont gérés par `src/utils/paths.py` : ne jamais écrire `"assets/..."` en dur.

## Personnaliser les rapports
**Paramètres > Informations de l'entreprise (rapports clients)** : nom, titre du rapport,
téléphone, e-mail, site web, adresse et logo (PNG ou JPG). Le logo choisi est *copié* à côté de
l'application : il continue de fonctionner si l'image d'origine est déplacée ou si la clé USB change
de lettre de lecteur. « Revenir au logo DIP » rétablit le logo intégré.
(Le fichier `company.json` reste modifiable à la main si besoin.)

Le rapport PDF contient : fiche client et technicien, verdict global, synthèse à voyants
(Bon / À surveiller / Critique), recommandations automatiques, puis le détail technique.
Les seuils (disque 80 %/90 %, RAM 80 %/90 %, redémarrage 30 jours...) sont regroupés en tête de
`src/diagnostics/report_analysis.py`.

## Historique et classement des rapports
- Chaque PDF généré est classé automatiquement dans `<dossier d'export>/<Nom du client>/`.
- La page **Historique** liste tous les rapports (date, client, poste, verdict, technicien), avec
  recherche, ouverture du PDF ou de son dossier, et retrait de la liste (avec ou sans suppression du PDF).
- Un client déjà connu est proposé à la saisie, et ses coordonnées sont pré-remplies. Cela marche à partir
  du **nom**, du **téléphone** ou de l'**e-mail** : taper l'un des trois suffit à retrouver les deux autres
  (les champs déjà remplis ne sont jamais écrasés). Le téléphone est reconnu quelle que soit son écriture
  (`06 12 34 56 78`, `06.12.34.56.78`, `+33 6 12 34 56 78`).
- `historique.json` contient des données de clients : sur une clé USB, pensez à la chiffrer (BitLocker).

## Santé, mises à jour et stabilité
Trois cases de la page Rapport (cochées par défaut) ajoutent :
- **Santé matérielle** : état SMART des disques internes, usure SSD, température, batterie (capacité restante, cycles) ;
- **Mises à jour Windows & pilotes** : mises à jour en attente (dont sécurité et pilotes), redémarrage en attente, périphériques en erreur. Cette recherche interroge Microsoft : jusqu'à 2 minutes ;
- **Stabilité** : écrans bleus et arrêts inattendus des 7 derniers jours.

Toutes les collectes tournent en parallèle, et une vérification impossible (pas d'Internet, droits insuffisants) apparaît « Non vérifié » sans bloquer le rapport.
Certaines données SMART (usure, température) exigent les droits administrateur : l'.exe les demande, pas un lancement depuis VS Code.

**Dépannage :** pour voir ce que chaque collecteur renvoie réellement sur un PC :
```bat
python -m src.diagnostics.health_info
python -m src.diagnostics.report_data
```

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
src/utils/company.py    informations et logo de l'entreprise
src/diagnostics/history.py  historique des rapports
assets/                 logo, icônes, thème
tests/                  tests de démarrage
```

## Feuille de route
1. ✅ Socle reproductible (dépendances, build, chemins, tests)
2. ✅ Rapport PDF avec les vraies données, logo et voyants
3. ✅ Mises à jour, SMART, batterie, journaux d'événements (à valider sur PC réels)
4. Version Mac (éventuellement)
