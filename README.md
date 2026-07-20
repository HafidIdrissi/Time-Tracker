# Local Time Tracker

Application Windows de suivi du temps, locale et respectueuse de la vie privée.
Elle observe l’application et la fenêtre au premier plan, détecte l’inactivité,
classe les usages et produit des analyses détaillées sans compte, serveur ou
télémétrie.

![Aperçu du rapport HTML](assets/report-preview.svg)

## Points forts

- interface Windows avec suivi en direct ;
- application, titre de fenêtre, durée courante et inactivité visibles en temps réel ;
- analyse pour aujourd’hui ou les 7 derniers jours ;
- histogramme d’utilisation par heure ou par jour ;
- classement des catégories, applications et onglets de navigateur ;
- détection des sessions continues et de la session la plus longue ;
- rapports HTML autonomes utilisables hors ligne ;
- stockage local dans SQLite ;
- catégories personnalisables avec un simple fichier JSON ;
- aucune création de compte et aucune transmission de données.

## Ce que l’application mesure

Le tracker lit régulièrement la fenêtre Windows au premier plan :

1. il relève le nom du processus, par exemple `Code.exe`, `chrome.exe` ou
   `TslGame.exe` ;
2. il relève le titre de la fenêtre ou de l’onglet actif ;
3. il prolonge la période en cours tant que la même fenêtre reste active ;
4. il crée une nouvelle période lors d’un changement de fenêtre ;
5. il classe la période comme inactive après le seuil configuré sans clavier ni
   souris.

> Le temps actif signifie que la fenêtre était au premier plan et que Windows
> détectait une activité clavier ou souris. Cela ne garantit pas que la personne
> regardait réellement l’écran. Déplacer la souris vers un autre moniteur sans
> cliquer ne change pas nécessairement la fenêtre active.

## Interface Windows

L’interface contient trois espaces principaux.

### Tableau de bord

- application et fenêtre actuellement détectées ;
- durée de la fenêtre courante ;
- temps écoulé depuis la dernière entrée clavier/souris ;
- heure de la dernière mesure ;
- temps actif et inactif du jour ;
- nombre d’applications et de périodes ;
- liste des activités récentes.

### Analyse d’utilisation

- sélection **Aujourd’hui** ou **7 derniers jours** ;
- temps actif total et moyenne quotidienne ;
- session continue la plus longue ;
- histogramme empilé avec les couleurs des catégories ;
- types d’usage les plus importants ;
- applications les plus utilisées ;
- onglets Chrome, Edge, Firefox, Brave, Opera ou Vivaldi les plus utilisés.

Les suffixes comme `- Google Chrome` sont retirés avant de regrouper les titres,
afin que plusieurs périodes sur le même onglet soient additionnées.

### Rapports et données

- génération d’un rapport pour une date choisie ;
- ouverture du dossier des rapports ;
- réinitialisation complète de l’historique après confirmation.

Les rapports déjà générés ne sont pas supprimés lors d’une réinitialisation.

## Prérequis

- Windows 10 ou Windows 11 ;
- Python 3.10 ou plus récent ;
- PowerShell.

## Installation

Dans PowerShell, depuis le dossier du projet :

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item config.example.json config.json
```

Si PowerShell bloque temporairement l’activation de l’environnement :

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## Démarrage rapide

Double-cliquez sur :

```text
Lancer Time Tracker.cmd
```

Ou lancez directement l’interface :

```powershell
.\.venv\Scripts\python.exe windows_app.py
```

Le suivi démarre automatiquement. Il continue lorsque la fenêtre est réduite et
s’arrête proprement lorsque l’application est fermée.

Par défaut, l’interface effectue une mesure par seconde pour rendre l’affichage
direct réactif. La fréquence et le seuil d’inactivité peuvent être modifiés avant
de démarrer le suivi.

> Ne lancez pas simultanément `track.py`, `windows_app.py` et l’exécutable :
> plusieurs trackers enregistreraient les mêmes périodes.

## Créer l’exécutable Windows

```powershell
.\build_windows.ps1
```

Le script installe PyInstaller si nécessaire et produit :

```text
dist\LocalTimeTracker\LocalTimeTracker.exe
```

Il faut conserver le dossier `LocalTimeTracker` complet, pas seulement le fichier
`.exe`.

Lorsqu’il est exécuté depuis ce projet, l’exécutable réutilise `data/activity.db`,
`reports/` et `config.json` à la racine. S’il est copié comme application
indépendante, les données sont placées dans :

```text
%LOCALAPPDATA%\LocalTimeTracker
```

## Créer un installateur distribuable

Pour obtenir un fichier d’installation unique avec assistant Windows,
raccourcis et désinstallation :

1. installez [Inno Setup 6](https://jrsoftware.org/isinfo.php) ;
2. lancez la construction de la release.

```powershell
winget install JRSoftware.InnoSetup
.\build_release.ps1
```

Le résultat est placé dans :

```text
release\LocalTimeTracker-Setup-1.0.0-x64.exe
release\SHA256SUMS.txt
```

L’installateur :

- installe l’application pour l’utilisateur courant sans exiger les droits
  administrateur ;
- affiche les informations de licence et de confidentialité ;
- crée un raccourci dans le menu Démarrer ;
- propose un raccourci Bureau facultatif ;
- ajoute une désinstallation Windows standard ;
- supprime les données locales lors de la désinstallation complète.

## Publier une version téléchargeable

Le workflow `.github/workflows/release.yml` construit automatiquement
l’installateur lorsqu’un tag de version est poussé :

```powershell
git tag v1.0.0
git push origin v1.0.0
```

GitHub Actions exécute les tests, construit l’application et l’installateur,
calcule son SHA-256 puis joint les fichiers à une GitHub Release. Les visiteurs
peuvent alors télécharger un véritable installateur depuis la page **Releases**.

Le dossier `packaging/` contient également un dossier de soumission prêt à
compléter pour Softonic.

Pour une diffusion publique, consultez [SIGNING.md](SIGNING.md). Un certificat
de signature reconnu est nécessaire pour présenter un éditeur vérifié et
répondre aux exigences des principaux catalogues Windows.

## Utilisation en ligne de commande

L’interface graphique est recommandée, mais le moteur peut fonctionner seul :

```powershell
python track.py
```

Valeurs par défaut du mode terminal :

- mesure toutes les 5 secondes ;
- inactivité après 180 secondes ;
- base `data/activity.db` ;
- mode SQLite WAL permettant de générer un rapport pendant le suivi.

Exemple personnalisé :

```powershell
python track.py --interval 10 --idle-after 300 --database data/mon-activite.db
```

Arrêtez le tracker avec `Ctrl+C`.

## Personnaliser les catégories

Copiez puis modifiez `config.example.json` :

```powershell
Copy-Item config.example.json config.json
```

Exemple :

```json
{
  "default_category": "Autre",
  "default_color": "#64748b",
  "categories": [
    {
      "name": "Travail",
      "color": "#4f46e5",
      "keywords": ["code.exe", "github", "gmail"]
    },
    {
      "name": "Jeux",
      "color": "#ec4899",
      "keywords": ["tslgame.exe", "pubg", "steam.exe"]
    }
  ]
}
```

Les mots-clés sont comparés sans tenir compte des majuscules avec le nom de
l’application et le titre de la fenêtre. La première catégorie correspondante
est utilisée : placez les règles les plus précises en premier.

`config.json` reste privé et est ignoré par Git. Seul `config.example.json` sert
de modèle public.

## Générer un rapport HTML

Rapport du jour :

```powershell
python report.py
```

Jour précis :

```powershell
python report.py --date 2026-07-20
```

Période inclusive :

```powershell
python report.py --from 2026-07-01 --to 2026-07-20
```

Chemins personnalisés :

```powershell
python report.py --date 2026-07-20 `
  --database data/activity.db `
  --config config.json `
  --output reports/journee.html
```

Le rapport contient :

- le temps actif et inactif ;
- les totaux par catégorie ;
- une chronologie visuelle ;
- les applications et leur part du temps actif ;
- les titres complets des fenêtres ;
- la timeline détaillée de toutes les périodes.

Le fichier HTML est autonome et ne charge aucune ressource externe.

## Données et vie privée

La base SQLite est stockée dans :

```text
data/activity.db
```

Les titres de fenêtres peuvent contenir des noms de documents, recherches,
messages ou sujets sensibles. Les éléments suivants sont donc exclus par
`.gitignore` :

```text
data/
*.db
config.json
reports/
build/
dist/
```

Avant chaque publication, vérifiez toujours `git status` afin de confirmer
qu’aucune donnée personnelle n’est incluse.

## Démarrage automatique avec Windows

La méthode recommandée utilise le Planificateur de tâches :

1. ouvrez **Planificateur de tâches** puis **Créer une tâche** ;
2. choisissez le déclencheur **À l’ouverture de session** ;
3. ajoutez l’action **Démarrer un programme** ;
4. utilisez `.venv\Scripts\pythonw.exe` comme programme ;
5. utilisez le chemin absolu de `windows_app.py` comme argument ;
6. utilisez le dossier du projet dans **Démarrer dans**.

`pythonw.exe` lance l’interface sans console supplémentaire.

## Tests

Les tests utilisent des bases temporaires et ne lisent pas les fenêtres Windows :

```powershell
python -m unittest discover -v
```

Ils couvrent notamment :

- les changements de fenêtre et l’inactivité ;
- le stockage SQLite et la réinitialisation ;
- la validation des catégories ;
- le regroupement des applications et onglets ;
- les agrégations et rapports HTML.

## Architecture

```text
Fenêtre Windows au premier plan
             |
             v
WindowsActivityProvider
             |
             v
ActivityTracker --> SQLite --> Analyse graphique
                           \--> Rapport HTML
```

## Structure du projet

```text
.
├── windows_app.py              # interface Windows et tableau de bord
├── Lancer Time Tracker.cmd     # lancement graphique par double-clic
├── build_windows.ps1           # création de l’exécutable
├── track.py                    # suivi en mode terminal
├── report.py                   # génération des rapports HTML
├── timetracker/
│   ├── windows.py              # fenêtre active et inactivité Windows
│   ├── tracker.py              # périodes continues et transitions
│   ├── database.py             # persistance SQLite
│   ├── categories.py           # règles de classement JSON
│   ├── analytics.py            # statistiques d’utilisation
│   └── reporting.py            # agrégations et rendu HTML
├── tests/                      # tests automatisés
├── assets/report-preview.svg   # aperçu du rapport
├── config.example.json         # catégories publiques par défaut
├── requirements.txt
├── LICENSE
└── .gitignore
```

## Limites connues

- le tracker mesure la fenêtre au premier plan, pas la position du curseur sur
  plusieurs écrans ;
- les navigateurs fournissent généralement le titre de l’onglet, pas son URL ;
- une activité plus courte que la fréquence de mesure peut ne pas être observée ;
- certaines fenêtres exécutées avec des privilèges élevés peuvent masquer leur
  titre à une application non élevée ;
- l’application est actuellement destinée à Windows.

## Licence MIT

Ce projet est distribué sous la [licence MIT](LICENSE). Elle autorise notamment
l’utilisation personnelle ou commerciale, la modification et la redistribution,
à condition de conserver la notice de copyright et le texte de la licence dans
les copies substantielles. Le logiciel est fourni sans garantie.

La licence MIT est adaptée si l’objectif est de permettre une réutilisation très
large du projet avec peu de contraintes.
