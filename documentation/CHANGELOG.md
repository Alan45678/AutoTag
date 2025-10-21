
# Changelog

Toutes les modifications notables apportées à ce projet seront documentées dans ce fichier.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/), et ce projet adhère au [Versionnage Sémantique](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2025-05-25

### Removed

-   Suppression de l'intégralité de la suite de tests (`/tests`).
    -   *Note : Les tests étaient devenus obsolètes et ne reflétaient plus la logique actuelle du code. Ils devront être réintroduits à l'avenir pour garantir la stabilité et faciliter la maintenance.*

### Fixed

-   Correction des instructions d'installation contradictoires dans le `README.md`. La seule méthode recommandée est désormais `pip install -e .`, qui s'appuie sur `pyproject.toml` et garantit l'installation de toutes les dépendances nécessaires.

### Changed

-   Mise à jour majeure du fichier `README.md` pour refléter la structure actuelle du projet, corriger les incohérences et clarifier son utilisation.

## [1.1.3] - 2025-05-21

### Changed

-   Amélioration du calibrage des modèles via l'ajustement des seuils (`threshold`) par défaut dans la configuration.

## [1.1.2] - 2025-05-16

### Added

-   **Optimisation majeure du traitement** : Les pipelines partageant le même modèle d'embedding calculent désormais cet embedding une seule fois pour tous les fichiers, réduisant significativement le temps d'exécution global.

### Changed

-   Standardisation du nommage des tags d'humeur en utilisant le préfixe `MOOD_` pour une meilleure identification dans les logiciels de gestion de tags.

## [1.1.1] - 2025-05-16

### Changed

-   Les fichiers de résultats pour les classifications de type "moods and context" affichent désormais les scores de probabilité pour **toutes les classes**, et non plus seulement la classe gagnante, afin d'améliorer la transparence et l'analyse des prédictions.

## [1.1.0] - 2025-05-16

### Added

-   Ajout de nouveaux modèles de classification pour les tags suivants :
    -   Approachability
    -   Engagement
    -   Arousal/Valence (DEAM)
    -   Danceability
    -   Mood Aggressive
    -   Mood Happy
    -   Mood Party
    -   Mood Relaxed
    -   Mood Sad

## [1.0.4] - 2025-05-12

### Added

-   Intégration de la documentation au format Sphinx pour générer un site de documentation complet à partir des docstrings du code.

## [1.0.3] - 2025-05-12

### Added

-   Ajout d'une suite de tests logiciels (basée sur `pytest`).
-   Création d'un fichier `pyproject.toml` pour une gestion moderne du projet et de ses dépendances.

## [1.0.2] - 2025-05-12

### Added

-   Introduction des fichiers `config.json` et `src/config_loader.py` pour centraliser et externaliser la configuration des pipelines d'inférence.

## [1.0.1] - 2025-04-12

### Added

-   Ajout d'un pipeline de prédiction pour l'humeur (mood).
-   Amélioration de la journalisation avec une barre de progression `tqdm` pour suivre le traitement des fichiers.

## [1.0.0] - 2025-04-11

### Added

-   Version initiale du projet.
-   Prédiction de genre musical.
-   Support pour l'écriture des métadonnées (tags) dans les fichiers MP3.