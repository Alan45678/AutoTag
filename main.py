

# -*- coding: utf-8 -*-
"""
Point d'entrée principal pour les pipelines de prédiction de tags audio.

Ce script charge la configuration, groupe les pipelines pour optimiser
le calcul des embeddings, et exécute les analyses.
Il supprime également les fichiers de résultats précédents au démarrage.
"""

import sys
import json
import traceback
import os # AJOUTÉ : Pour la suppression des fichiers
from collections import defaultdict
from typing import List, Dict, Tuple, Any

# Imports des modules locaux de l'application
from src.config_loader import load_config_from_json
from src.config import PipelineConfig, Config
from src.pipeline import Pipeline
from src.audio.file_manager import AudioFileManager
from src.audio.loader import AudioLoader
from src.models.loader import ModelLoader
from src.prediction.predictor import Predictor
# from src.logging_config import setup_logging # Logging standard désactivé

# Chemin vers le fichier de configuration principal
CONFIG_FILE = "config.json"

def group_pipeline_configs(
    pipeline_configs: List[PipelineConfig]
) -> Dict[Tuple[str, str, int], List[PipelineConfig]]:
    """
    Groupe les configurations de pipeline par (data_folder, embedding_model_path, sample_rate).
    Ces pipelines peuvent partager le même calcul d'embedding pour les mêmes fichiers.
    """
    grouped_configs = defaultdict(list)
    for p_config in pipeline_configs:
        # La sample_rate est cruciale car l'embedding model attend une sr spécifique
        group_key = (
            p_config.data_folder,
            p_config.embedding_model_path,
            p_config.sample_rate # Assumer que c'est la SR pour l'embedding
        )
        grouped_configs[group_key].append(p_config)
    return grouped_configs

# Point d'entrée du script
if __name__ == "__main__":
    print("=" * 30 + " Démarrage de l'application AutoTag " + "=" * 30, flush=True)

    # Initialisation des composants qui peuvent être partagés globalement
    # ou par groupe de pipelines
    model_loader = ModelLoader()
    predictor = Predictor() # Le predictor est sans état

    try:
        # 1. Chargement de la configuration globale
        print(f"[INFO] Chargement de la configuration depuis {CONFIG_FILE}...", flush=True)
        global_config: Config = load_config_from_json(CONFIG_FILE)
        print("[INFO] Configuration globale chargée.", flush=True)

        if not global_config or not global_config.pipelines:
            print("[WARNING] Aucun pipeline activé n'a été chargé. Arrêt.", flush=True)
            sys.exit(0)

        print(f"[INFO] {len(global_config.pipelines)} pipeline(s) activé(s) trouvé(s).", flush=True)

        # --- DÉBUT DE L'AJOUT : Suppression des fichiers de résultats ---
        print("\n[INFO] Nettoyage des fichiers de résultats précédents des pipelines activés...", flush=True)
        cleaned_any_file = False
        for p_config in global_config.pipelines:
            # On ne nettoie que si le pipeline est bien dans ceux chargés (donc activé)
            result_file_to_clean = p_config.result_file_path
            try:
                if os.path.exists(result_file_to_clean):
                    os.remove(result_file_to_clean)
                    print(f"  [INFO] Fichier de résultats '{result_file_to_clean}' supprimé.", flush=True)
                    cleaned_any_file = True
                else:
                    # Pas une erreur, le fichier n'existait simplement pas
                    print(f"  [INFO] Fichier de résultats '{result_file_to_clean}' non trouvé, pas de suppression nécessaire.", flush=True)
            except (IOError, OSError) as e_clean:
                print(f"  [WARNING] Impossible de supprimer le fichier de résultats '{result_file_to_clean}': {e_clean}", flush=True)
                # On continue même si un fichier ne peut être supprimé
        if not cleaned_any_file and global_config.pipelines:
             print("  [INFO] Aucun fichier de résultats existant n'a été trouvé pour les pipelines activés, ou aucun n'a été supprimé.", flush=True)
        elif not global_config.pipelines: # Devrait être couvert par le sys.exit plus haut, mais par sécurité
            print("  [INFO] Aucun pipeline configuré, donc aucun fichier de résultat à nettoyer.", flush=True)
        print("[INFO] Nettoyage des fichiers de résultats terminé.\n", flush=True)
        # --- FIN DE L'AJOUT ---

        # 2. Groupement des pipelines pour optimisation
        grouped_pipelines = group_pipeline_configs(global_config.pipelines)
        print(f"[INFO] Pipelines groupés en {len(grouped_pipelines)} groupe(s) pour optimisation.", flush=True)

        # 3. Exécution par groupe de pipelines
        for group_key, configs_in_group in grouped_pipelines.items():
            data_folder, embedding_model_path_shared, sample_rate_shared = group_key
            pipeline_names_in_group = [cfg.name for cfg in configs_in_group]
            print(f"\n=== [INFO] Traitement du groupe de pipelines partageant : ===", flush=True)
            print(f"    Dossier de données: {data_folder}", flush=True)
            print(f"    Modèle d'embedding: {embedding_model_path_shared}", flush=True)
            print(f"    Sample rate: {sample_rate_shared} Hz", flush=True)
            print(f"    Pipelines dans ce groupe: {', '.join(pipeline_names_in_group)}", flush=True)

            try:
                # 3a. Chargement des ressources partagées pour le groupe
                print(f"[GROUP INFO] Chargement du modèle d'embedding partagé: {embedding_model_path_shared}", flush=True)
                shared_embedding_model = model_loader.load_embedding_model(embedding_model_path_shared)
                print("[GROUP INFO] Modèle d'embedding partagé chargé.", flush=True)

                audio_file_manager = AudioFileManager(data_folder)
                # Utilise resample_quality du 1er pipeline du groupe pour AudioLoader
                audio_loader = AudioLoader(sample_rate=sample_rate_shared, resample_quality=configs_in_group[0].resample_quality)

                # 3b. Préparation de chaque pipeline dans le groupe (chargement des modèles de prédiction)
                prepared_pipelines: List[Pipeline] = []
                for p_config_item in configs_in_group: # Renommé p_config en p_config_item pour éviter conflit avec la boucle externe
                    print(f"\n  --- [PIPELINE PREP] Préparation du pipeline: {p_config_item.name} ---", flush=True)
                    try:
                        # Le Predictor est maintenant injecté
                        pipeline_instance = Pipeline(p_config_item, predictor)
                        # Nouvelle méthode pour charger uniquement les ressources de prédiction
                        pipeline_instance.load_prediction_resources(model_loader)
                        prepared_pipelines.append(pipeline_instance)
                        print(f"  --- [PIPELINE PREP] Pipeline {p_config_item.name} préparé. ---", flush=True)
                    except Exception as e_prep:
                        print(f"  --- [CRITICAL ERROR] Erreur lors de la préparation du pipeline {p_config_item.name}: {e_prep}", flush=True)
                        traceback.print_exc()
                        # On pourrait choisir de skipper ce pipeline spécifique et continuer avec les autres du groupe

                if not prepared_pipelines:
                    print(f"[GROUP WARNING] Aucun pipeline n'a pu être préparé pour le groupe {group_key}. Passage au groupe suivant.", flush=True)
                    continue

                # 3c. Traitement des fichiers audio pour ce groupe
                audio_files = audio_file_manager.get_audio_files()
                if not audio_files:
                    print(f"[GROUP WARNING] Aucun fichier audio trouvé dans {data_folder} pour ce groupe.", flush=True)
                    continue
                
                print(f"[GROUP INFO] Début du traitement de {len(audio_files)} fichier(s) pour le groupe '{', '.join(p.config.name for p in prepared_pipelines)}'...", flush=True)
                
                # Importation de tqdm pour la barre de progression (déplacé ici pour être local au besoin)
                try:
                    from tqdm import tqdm
                    TQDM_AVAILABLE = True
                except ImportError:
                    TQDM_AVAILABLE = False
                    def tqdm(iterable, *args, **kwargs): # type: ignore[misc]
                        print("[WARN] tqdm non trouvé. La barre de progression sera désactivée pour ce groupe.")
                        yield from iterable # type: ignore[misc]
                
                progress_bar_desc = f"Groupe ({'/'.join(p.config.name for p in prepared_pipelines[:2])})"
                if len(prepared_pipelines) > 2:
                    progress_bar_desc += "..."

                for audio_file_name in tqdm(audio_files, desc=progress_bar_desc, unit="fichier", leave=False):
                    audio_path = audio_file_manager.get_full_path(audio_file_name)
                    print(f"\n    --- [FILE INFO] Traitement du fichier: {audio_file_name} (Groupe: {group_key[0]}) ---", flush=True)
                    
                    try:
                        # i. Charger l'audio (une seule fois par fichier pour le groupe)
                        print(f"    [FILE DEBUG] Chargement audio: {audio_path}", flush=True)
                        audio_data = audio_loader.load(audio_path)
                        # print(f"    [FILE INFO] Audio chargé (durée approx: {len(audio_data) / sample_rate_shared:.2f}s).", flush=True)

                        # ii. Extraire les embeddings (une seule fois par fichier pour le groupe)
                        print("    [FILE DEBUG] Extraction des embeddings partagés...", flush=True)
                        shared_embeddings = predictor.extract_embeddings(shared_embedding_model, audio_data)
                        print(f"    [FILE INFO] Embeddings partagés extraits (shape: {getattr(shared_embeddings, 'shape', 'N/A')}).", flush=True)

                        # iii. Exécuter chaque pipeline préparé avec les embeddings partagés
                        for pipeline in prepared_pipelines:
                            print(f"\n      --- [SUB-PIPELINE] Exécution de {pipeline.config.name} pour {audio_file_name} ---", flush=True)
                            try:
                                # Nouvelle méthode pour traiter avec des embeddings pré-calculés
                                pipeline.process_file(
                                    audio_file_name=audio_file_name,
                                    audio_path=audio_path,
                                    embeddings=shared_embeddings
                                )
                                print(f"      --- [SUB-PIPELINE] {pipeline.config.name} terminé pour {audio_file_name}. ---", flush=True)
                            except Exception as e_pipe_run:
                                print(f"      --- [ERROR] Erreur dans le pipeline {pipeline.config.name} pour {audio_file_name}: {e_pipe_run}", flush=True)
                                traceback.print_exc() # Traceback pour ce sous-pipeline
                        
                    except Exception as e_file:
                        print(f"    !!! [FILE ERROR] Erreur majeure lors du traitement du fichier {audio_file_name} pour le groupe: {e_file} !!!", flush=True)
                        traceback.print_exc() # Traceback pour ce fichier
                
                # Correction: tqdm(audio_files) crée une nouvelle instance. Il faut utiliser l'instance existante ou ne pas l'appeler.
                # Si tqdm est importé, il est utilisé dans la boucle. S'il n'est pas importé, tqdm est une fonction factice.
                # On ne peut pas appeler .close() sur la fonction factice si tqdm n'est pas là.
                if TQDM_AVAILABLE and audio_files: # S'assurer qu'il y a des fichiers pour que la barre ait été utilisée
                    # Tentative de fermeture propre si tqdm a été utilisé
                    # Il est préférable de gérer la barre de progression dans un contexte `with` si possible,
                    # mais ici, nous allons la fermer manuellement après la boucle.
                    # Une approche plus sûre serait de stocker l'objet tqdm et de le fermer.
                    # Pour l'instant, on assume que la barre se ferme d'elle-même à la fin de l'itération.
                    # La ligne `tqdm(audio_files).close()` était incorrecte car elle créait une nouvelle instance.
                    # On va la retirer car la barre de progression de la boucle `for` devrait se fermer automatiquement.
                    pass


            except Exception as e_group:
                print(f"\n--- [CRITICAL GROUP ERROR] Erreur lors du traitement du groupe de pipelines {group_key}: {e_group}", flush=True)
                traceback.print_exc()
                # Continue avec le prochain groupe

    except (FileNotFoundError, json.JSONDecodeError, KeyError, ValueError) as e:
        print(f"\n--- [CRITICAL ERROR] Erreur lors du chargement/validation de la configuration depuis {CONFIG_FILE}. Arrêt.", flush=True)
        print(f"--- Erreur: {e} ---", flush=True)
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print("\n--- [CRITICAL ERROR] Erreur inattendue au niveau principal de l'application. ---", flush=True)
        print(f"--- Erreur: {e} ---", flush=True)
        traceback.print_exc()
        sys.exit(1)

    print("\n" + "=" * 30 + " Application AutoTag terminée " + "=" * 30, flush=True)


