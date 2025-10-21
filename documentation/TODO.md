
# Feuille de Route du Projet (TODO)

Ce document suit les améliorations prévues, la dette technique et les nouvelles fonctionnalités potentielles pour le projet AutoTag.

## Tâches Critiques / Haute Priorité

-   [ ] **Ré-établir une suite de tests logiciels**
    -   *Contexte : Les tests ont été supprimés car ils étaient obsolètes. Leur réintroduction est la priorité absolue pour garantir la stabilité du code et faciliter les contributions futures.*
    -   [ ] Implémenter des tests unitaires (`pytest`) pour les composants fondamentaux (`PredictionAnalyzer`, `TagWriter`, `AudioFileManager`, `ModelLoader`, `ConfigLoader`).
    -   [ ] Ajouter des tests d'intégration pour valider le flux de travail complet d'un pipeline dans `main.py`, y compris la logique de groupement.

-   [ ] **Centraliser et finaliser le système de journalisation (Logging)**
    -   *Contexte : Le code utilise actuellement `print()` pour le feedback, tandis qu'un module `logging` plus robuste existe mais est désactivé. La centralisation est nécessaire pour une meilleure gestion des erreurs et du débogage.*
    -   [ ] Remplacer tous les appels à `print()` dans `main.py` et les autres modules par des appels au logger standard (`logging.getLogger(__name__)`).
    -   [ ] Activer et configurer le module `src/logging_config.py` une seule fois au démarrage de `main.py` pour gérer de manière unifiée la sortie vers la console (compatible `tqdm`) et vers un fichier journal.

## Qualité du Code et Refactorisation

-   [ ] **Améliorer la gestion des exceptions**
    -   [ ] Remplacer les captures d'exceptions génériques (`except Exception`) par des exceptions plus spécifiques (`FileNotFoundError`, `mutagen.MutagenError`, `KeyError`, etc.) là où c'est pertinent. Cela rendra la gestion des erreurs plus précise et robuste.

-   [ ] **Renforcer la gestion des dépendances**
    -   [ ] Figer les versions des dépendances dans `pyproject.toml` (par exemple, `tensorflow==2.12.0` au lieu de `tensorflow>=2.10.0`) pour garantir des installations reproductibles et éviter les ruptures de compatibilité inattendues.

-   [ ] **Améliorer la clarté et les commentaires du code**
    -   [ ] Effectuer une passe de relecture sur l'ensemble de la base de code pour améliorer les commentaires et les docstrings, en s'assurant qu'ils sont à jour, clairs et utiles.

## Nouvelles Fonctionnalités et Améliorations

-   [ ] **Ajouter une interface utilisateur graphique (GUI)**
    -   [ ] Développer une interface simple (par exemple, avec Tkinter, PyQt ou PySide) pour rendre l'outil accessible aux utilisateurs non techniques. L'interface devrait permettre de sélectionner un dossier, de choisir les pipelines à exécuter et de visualiser la progression.

-   [ ] **Permettre le traitement récursif des sous-dossiers**
    -   [ ] Ajouter une option de configuration pour permettre à `AudioFileManager` de scanner récursivement le dossier de données et de traiter les fichiers audio trouvés dans les sous-dossiers.

-   [ ] **Améliorer la flexibilité de la configuration**
    -   [ ] Rendre certains paramètres actuellement codés en dur (comme les extensions de fichiers supportées) configurables via le fichier `config.json`.

## Documentation

-   [ ] **Maintenir la documentation à jour**
    -   [ ] S'assurer que les fichiers `README.md`, `USER_GUIDE.md` et `CHANGELOG.md` sont systématiquement mis à jour lors de l'ajout de nouvelles fonctionnalités ou de modifications importantes.
-   [ ] **Générer et héberger une documentation technique**
    -   [ ] Utiliser Sphinx pour générer une documentation HTML à partir des docstrings du code et l'héberger (par exemple sur Read the Docs ou GitHub Pages) pour fournir une référence d'API complète.