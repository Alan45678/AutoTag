
# AutoTag : Prédiction et Tagging Automatiques pour Fichiers Audio

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](documentation/LICENSE)
[![Version](https://img.shields.io/badge/version-1.2.0-blue.svg)](documentation/CHANGELOG.md)

## Table des Matières
- [AutoTag : Prédiction et Tagging Automatiques pour Fichiers Audio](#autotag--prédiction-et-tagging-automatiques-pour-fichiers-audio)
  - [Table des Matières](#table-des-matières)
  - [Aperçu](#aperçu)
  - [Fonctionnalités Clés](#fonctionnalités-clés)
  - [Pour Commencer](#pour-commencer)
    - [Prérequis](#prérequis)
    - [Installation](#installation)
    - [Utilisation Rapide](#utilisation-rapide)
  - [Configuration](#configuration)
  - [Structure du Projet](#structure-du-projet)
  - [Documentation Détaillée](#documentation-détaillée)
  - [Contribuer](#contribuer)
  - [Licence](#licence)

## Aperçu

**AutoTag** est un outil en ligne de commande basé sur Python qui analyse des fichiers audio pour prédire et écrire automatiquement des métadonnées (tags) de genre, d'humeur et de contexte. Il s'appuie sur des modèles de Machine Learning TensorFlow, intégrés via la bibliothèque **Essentia**, pour effectuer des classifications multi-labels.

Le système est conçu pour être modulaire et efficace. Il calcule une seule fois des caractéristiques audio profondes (embeddings) pour les partager entre plusieurs analyses (genre, humeur, etc.), optimisant ainsi considérablement le temps de traitement.

## Fonctionnalités Clés

-   **Prédiction Multi-Label** : Classifie les genres (taxonomie Discogs), les humeurs et contextes (MTG-Jamendo), la dansabilité, l'agressivité, et plus encore.
-   **Tagging Automatique** : Écrit les prédictions directement dans les métadonnées des fichiers audio (ID3 pour MP3/WAVE, Vorbis Comments pour FLAC/OGG, Atomes MP4).
-   **Configuration Centralisée** : L'ensemble du processus est piloté par un unique fichier `config.json`, permettant d'activer, désactiver et paramétrer chaque pipeline d'analyse.
-   **Traitement Optimisé** : Les embeddings audio ne sont calculés qu'une seule fois par fichier, même pour plusieurs pipelines d'analyse, réduisant drastiquement le temps d'exécution.
-   **Analyse Fine** : Les résultats sont filtrés selon des seuils de confiance, une fréquence d'apparition et un score moyen pour garantir la pertinence des tags.
-   **Rapports Détaillés** : Génère des fichiers texte pour chaque analyse, offrant une vue transparente des scores de toutes les classes et des résultats finaux.

## Pour Commencer

### Prérequis

-   **Python 3.10+**
-   **FFmpeg** : Nécessaire pour le décodage audio par Essentia. Assurez-vous qu'il est installé et accessible dans le PATH de votre système.

### Installation

1.  **Cloner le dépôt**
    ```bash
    git clone https://github.com/votre-utilisateur/auto_tag.git
    cd auto_tag
    ```

2.  **Créer un environnement virtuel** (recommandé)
    ```bash
    python -m venv env
    source env/bin/activate  # Sur Windows: .\env\Scripts\activate
    ```

3.  **Installer les dépendances**
    Le projet utilise `pyproject.toml` pour une installation simplifiée.
    ```bash
    pip install -e .
    ```

### Utilisation Rapide

1.  **Ajoutez vos fichiers audio** dans le dossier `data/`.
2.  **Activez les pipelines** souhaités dans `config.json` en passant leur champ `"enabled"` à `true`.
3.  **Lancez l'analyse** depuis la racine du projet :
    ```bash
    python main.py
    ```

Les fichiers audio dans `data/` seront mis à jour avec les nouveaux tags, et les rapports détaillés apparaîtront dans le dossier `result/`.

## Configuration

Le comportement d'AutoTag est entièrement contrôlé par le fichier `config.json`. Il contient une liste de "pipelines", où chacun représente une tâche d'analyse (par exemple, "genre").

```json
{
  "pipelines": [
    {
      "name": "genre",
      "enabled": true,
      "data_folder": "data",
      "embedding_model_path": "models/embedding/discogs_effnet/discogs-effnet-bs64-1.pb",
      "prediction_model_path": "models/classification/genre/genre_discogs400-discogs-effnet-1.pb",
      "metadata_path": "models/classification/genre/genre_discogs400-discogs-effnet-1.json",
      "result_file_path": "result/result_main/result_genre.txt",
      "tags_to_write": ["GENRE_AUTO"],
      "threshold": 0.1,
      "min_freq": 2,
      "min_score": 0.05,
      "max_labels": 5
    }
    // ... autres pipelines (mood, danceability, etc.)
  ]
}
```
Vous pouvez modifier ce fichier pour changer les chemins, ajuster les seuils de détection ou activer/désactiver des analyses.

## Structure du Projet

```
auto_tag/
│
├── config.json             # Fichier de configuration principal des pipelines
├── main.py                 # Point d'entrée de l'application
├── pyproject.toml          # Définition du projet et des dépendances
│
├── data/                   # Dossier pour vos fichiers audio
├── models/                 # Modèles de Machine Learning pré-entraînés
├── result/                 # Rapports de prédiction générés
├── src/                    # Code source de l'application
└── documentation/          # Guides, spécifications et autres documents
```

## Documentation Détaillée

Ce document est une vue d'ensemble. Pour des informations plus approfondies, veuillez consulter :

-   **[Guide Utilisateur (USER_GUIDE.md)](documentation/USER_GUIDE.md)** : Pour des instructions détaillées sur l'utilisation, la configuration et le dépannage.
-   **[Spécifications Techniques (TECHNICAL_SPEC.md)](documentation/TECHNICAL_SPEC.md)** : Pour une description de l'architecture, du flux de données et des composants internes.
-   **[Journal des Modifications (CHANGELOG.md)](documentation/CHANGELOG.md)** : Pour suivre l'historique des versions et des changements apportés au projet.
-   **[Feuille de Route (TODO.md)](documentation/TODO.md)** : Pour voir les fonctionnalités prévues et les améliorations futures.

## Contribuer

Les contributions sont les bienvenues. Veuillez forker le dépôt, créer une branche pour vos modifications et soumettre une Pull Request.

## Licence

Ce projet est distribué sous la licence MIT. Voir le fichier [LICENSE](documentation/LICENSE) pour plus de détails.