
"""
Charge la configuration des pipelines depuis un fichier JSON.

Ce module fournit la fonction `load_config_from_json` pour lire un fichier JSON
contenant les définitions des pipelines et créer des objets `Config` et
`PipelineConfig` correspondants. Seuls les pipelines marqués comme
`"enabled": true` (ou sans clé `"enabled"`, considéré comme activé par défaut)
seront chargés.
"""

import json
import logging
import os
from typing import Dict, Any
from src.config import Config, PipelineConfig

# Utilise le logger standard, la configuration se fera dans main ou logging_config
logger = logging.getLogger(__name__)
# Pour utiliser print à la place (comme dans main.py), remplacer logger.info etc. par print
USE_PRINT_INSTEAD_OF_LOGGER = True # Mettre à True pour correspondre à main.py

def _log_or_print(level: str, message: str):
    """Helper pour utiliser soit logger soit print."""
    if USE_PRINT_INSTEAD_OF_LOGGER:
        # Ajoute un préfixe simple pour simuler les niveaux de log
        print(f"[{level.upper()}] {message}", flush=True)
    else:
        if level == "info":
            logger.info(message)
        elif level == "warning":
            logger.warning(message)
        elif level == "error":
            logger.error(message)
        elif level == "debug":
            logger.debug(message)
        else:
            logger.info(message) # Fallback

def load_config_from_json(filepath: str = "config.json") -> Config:
    """
    Charge la configuration des pipelines depuis un fichier JSON.

    Lit le fichier JSON spécifié, valide sa structure de base et crée un
    objet `Config` contenant une liste de `PipelineConfig` pour chaque pipeline
    marqué comme activé (`"enabled": true` ou clé absente).

    :param filepath: Chemin vers le fichier de configuration JSON.
                     Défaut à "config.json".
    :type filepath: str
    :return: Un objet Config contenant la liste des `PipelineConfig` activées.
    :rtype: Config
    :raises FileNotFoundError: Si le fichier de configuration n'est pas trouvé.
    :raises json.JSONDecodeError: Si le fichier JSON est mal formé.
    :raises ValueError: Si la structure du JSON est incorrecte (ex: "pipelines"
                        manquant ou n'est pas une liste).
    :raises KeyError: Si une clé obligatoire est manquante dans la configuration
                      d'un *pipeline activé*.
    """
    _log_or_print("info", f"Chargement de la configuration depuis {filepath}...")
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data: Dict[str, Any] = json.load(f)

        # --- Validation de la structure globale ---
        if "pipelines" not in data:
            raise ValueError("La clé racine 'pipelines' est manquante dans le "
                             f"fichier de configuration '{filepath}'.")
        if not isinstance(data["pipelines"], list):
            raise ValueError("La clé 'pipelines' doit contenir une liste "
                             f"(array JSON) dans '{filepath}'.")

        pipeline_configs: list[PipelineConfig] = []
        total_pipelines_in_file = len(data["pipelines"])
        _log_or_print("debug", f"{total_pipelines_in_file} pipeline(s) trouvé(s) "
                      "dans le fichier JSON.")

        # --- Itération et traitement de chaque pipeline défini ---
        for i, pipeline_data in enumerate(data["pipelines"]):
            if not isinstance(pipeline_data, dict):
                _log_or_print("warning",
                              f"Élément non-dictionnaire trouvé dans la liste "
                              f"'pipelines' à l'index {i}. Ignoré.")
                continue

            pipeline_name = pipeline_data.get('name', f'PipelineSansNom_{i+1}')

            # --- Vérification du statut "enabled" ---
            # Si la clé "enabled" n'existe pas, on la considère True par défaut.
            is_enabled = pipeline_data.get("enabled", True)
            if not isinstance(is_enabled, bool):
                 _log_or_print("warning",
                              f"La clé 'enabled' pour le pipeline '{pipeline_name}' "
                              "n'est pas un booléen. Considéré comme activé "
                              "(True) par défaut.")
                 is_enabled = True

            if not is_enabled:
                _log_or_print("info",
                              f"Pipeline '{pipeline_name}' désactivé "
                              "('enabled': false). Ignoré.")
                continue  # Passe au pipeline suivant

            # --- Traitement du pipeline activé ---
            _log_or_print("debug", f"Traitement de la configuration pour le "
                          f"pipeline activé: {pipeline_name}")
            try:
                # Vérification des clés obligatoires pour un pipeline activé
                required_keys = [
                    "name", "data_folder", "embedding_model_path",
                    "prediction_model_path", "metadata_path", "result_file_path"
                ]
                for key in required_keys:
                    if key not in pipeline_data:
                        raise KeyError(
                            f"Clé obligatoire '{key}' manquante dans la "
                            f"configuration du pipeline activé '{pipeline_name}'."
                        )

                # Création de l'instance PipelineConfig en utilisant les données
                # et les valeurs par défaut pour les clés optionnelles
                config_instance = PipelineConfig(
                    name=pipeline_data["name"],
                    data_folder=pipeline_data["data_folder"],
                    embedding_model_path=pipeline_data["embedding_model_path"],
                    prediction_model_path=pipeline_data["prediction_model_path"],
                    metadata_path=pipeline_data["metadata_path"],
                    result_file_path=pipeline_data["result_file_path"],
                    # Utilisation de .get() pour les clés optionnelles
                    tags_to_write=pipeline_data.get("tags_to_write"), # Défaut géré dans PipelineConfig
                    threshold=pipeline_data.get("threshold", 0.1),
                    min_freq=pipeline_data.get("min_freq", 0),
                    min_score=pipeline_data.get("min_score", 0.0),
                    max_labels=pipeline_data.get("max_labels"), # Défaut None géré dans PipelineConfig
                    sample_rate=pipeline_data.get("sample_rate", 16000),
                    resample_quality=pipeline_data.get("resample_quality", 4),
                    input_node=pipeline_data.get(
                        "input_node", "serving_default_model_Placeholder"
                    ),
                    output_node=pipeline_data.get(
                        "output_node", "PartitionedCall"
                    )
                )
                pipeline_configs.append(config_instance)
                _log_or_print("debug", f"Configuration chargée pour le pipeline "
                              f"activé: {pipeline_name}")

            except KeyError as e:
                # Erreur si clé obligatoire manquante dans ce pipeline activé
                _log_or_print("error", f"Erreur de clé dans la configuration "
                              f"du pipeline activé '{pipeline_name}': {e}")
                raise # Re-lève l'exception pour arrêter le chargement complet
            except Exception as e:
                _log_or_print("error", f"Erreur inattendue lors du traitement "
                              f"de la config du pipeline '{pipeline_name}': {e}")
                raise # Re-lève l'exception

        # --- Finalisation ---
        global_config = Config(pipelines=pipeline_configs)
        num_enabled = len(pipeline_configs)
        _log_or_print("info",
                      f"Configuration chargée avec succès ({num_enabled} "
                      f"pipeline(s) activé(s) sur {total_pipelines_in_file} "
                      "trouvé(s) dans le fichier).")
        return global_config

    # --- Gestion des erreurs globales (ouverture fichier, JSON mal formé) ---
    except FileNotFoundError:
        _log_or_print("error", f"Erreur: Fichier de configuration introuvable: "
                      f"{filepath}")
        raise
    except json.JSONDecodeError as e:
        _log_or_print("error", f"Erreur: Format JSON invalide dans {filepath}: {e}")
        raise
    except ValueError as e: # Pour les erreurs de structure personnalisées
        _log_or_print("error", f"Erreur de structure dans le fichier de "
                      f"configuration: {e}")
        raise
    except Exception as e:
        _log_or_print("error", f"Erreur inattendue lors du chargement de la "
                      f"configuration depuis {filepath}: {e}")
        raise


