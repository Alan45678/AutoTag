
## @package result_handler
"""
Gère la sauvegarde et l'affichage des résultats de prédiction.

Ce module fournit la classe `ResultHandler` qui gère le stockage des résultats
de prédiction (pour genre, humeur, etc.) dans un fichier spécifié. Elle formate
et sauvegarde les résultats détaillés, incluant les labels, comptes, fréquences,
et scores, adaptés au type de pipeline.
"""

import os
from typing import List, Tuple, Dict, Optional, Any # Ajout de Dict, Optional, Any
import numpy as np # Ajout de numpy pour les scores

## @class ResultHandler
class ResultHandler:
    """
    Gère la sauvegarde des résultats de prédiction dans un fichier.

    S'occupe du formatage et du stockage des sorties de prédiction, supportant
    différents formats (ex: pour les pipelines "genre" vs "mood"), et ajoute
    les résultats au fichier de sortie spécifié.

    :param result_file_path: Chemin complet vers le fichier où les résultats
                             seront sauvegardés. Le répertoire sera créé si
                             nécessaire.
    :type result_file_path: str
    :param pipeline_name: Nom du pipeline (ex: "mood_happy", "genre").
                          Utilisé pour adapter le formatage.
    :type pipeline_name: str
    """
    # Noms des pipelines pour lesquels afficher toutes les probabilités
    MOOD_CONTEXT_PIPELINE_NAMES = {
        "approachability",
        "engagement",
        "danceability",
        "mood_aggressive",
        "mood_happy",
        "mood_party",
        "mood_relaxed",
        "mood_sad"
        # "arousal_valence_deam" est une régression, pas de probabilités de classe ici
        # "moodtheme_jamendo" a beaucoup de classes, on pourrait l'exclure ou l'inclure selon le besoin.
        # Pour l'instant, on se base sur les pipelines listés dans le dossier moods_and_context
        # et qui sont des classifications (pas régression).
    }

    def __init__(self, result_file_path: str, pipeline_name: str): # Ajout de pipeline_name
        """
        Initialise le gestionnaire de résultats avec le chemin du fichier de sortie
        et le nom du pipeline.

        Stocke le chemin du fichier et le nom du pipeline, et s'assure que le
        répertoire parent existe.

        :param result_file_path: Chemin vers le fichier pour stocker les résultats.
        :param pipeline_name: Nom du pipeline.
        """
        ## @var result_file_path
        # Chemin vers le fichier où les résultats de prédiction sont sauvegardés.
        self.result_file_path: str = result_file_path
        ## @var pipeline_name
        # Nom du pipeline, utilisé pour un formatage spécifique.
        self.pipeline_name: str = pipeline_name

        # Créer le répertoire parent si nécessaire
        try:
            result_dir = os.path.dirname(self.result_file_path)
            if result_dir and not os.path.exists(result_dir):
                os.makedirs(result_dir)
                print(f"[INFO] Répertoire de résultats créé : {result_dir}")
        except OSError as e:
            print(f"[ERROR] Impossible de créer le répertoire pour le fichier "
                  f"de résultats '{self.result_file_path}': {e}")
            # Ne pas lever d'erreur ici, l'erreur se produira lors de l'écriture

    def save(
        self,
        audio_file: str,
        final_label_list: str,
        analysis_results: List[Tuple[str, int, float, float]],
        # pipeline_type est maintenant self.pipeline_name
        config_details: Optional[Dict[str, Any]] = None, # Rendu Optionnel et type hint amélioré
        all_class_scores: Optional[List[Tuple[str, float]]] = None # Nouveau paramètre
    ):
        """
        Sauvegarde les résultats de prédiction formatés dans le fichier de sortie.

        Ajoute les résultats formatés au fichier spécifié lors de l'initialisation.
        Inclut le nom du fichier audio analysé, les résultats détaillés (labels,
        comptes, fréquences, scores) et la liste finale des labels assignés.
        Le format de sortie s'adapte en fonction du `self.pipeline_name`.
        Pour certains types de pipelines (ex: moods_and_context), les probabilités
        de toutes les classes peuvent également être affichées si fournies.

        :param audio_file: Nom du fichier audio analysé (ex: "song.mp3").
        :type audio_file: str
        :param final_label_list: Chaîne des labels finaux assignés, séparés par " ; ".
                                 Ex: "Rock ; Pop".
        :type final_label_list: str
        :param analysis_results: Liste de tuples contenant les détails de l'analyse
                                 pour chaque label pertinent. Format attendu :
                                 `(label: str, count: int, freq_percent: float, score: float)`
        :type analysis_results: List[Tuple[str, int, float, float]]
        :param config_details: Dictionnaire optionnel contenant des détails de la
                               configuration du pipeline (ex: seuils utilisés).
        :type config_details: Optional[Dict[str, Any]]
        :param all_class_scores: Liste optionnelle de tuples `(nom_classe, score_moyen)`
                                 pour toutes les classes du modèle.
                                 Utilisé pour les pipelines "moods_and_context".
        :type all_class_scores: Optional[List[Tuple[str, float]]]
        """
        try:
            # Utiliser 'a' pour ajouter au fichier (append mode)
            with open(self.result_file_path, 'a', encoding='utf-8') as f:
                f.write(f"\n\n--- Fichier Analysé: {audio_file} ---\n")

                # Ajout optionnel des paramètres de filtrage utilisés
                if config_details:
                     f.write(f"Paramètres (threshold={config_details.get('threshold', 'N/A')}, "
                             f"min_freq={config_details.get('min_freq', 'N/A')}, "
                             f"min_score={config_details.get('min_score', 'N/A')}, "
                             f"max_labels={config_details.get('max_labels', 'N/A')}):\n")

                # Adapte l'en-tête et le format en fonction du type de pipeline
                header_label_category = self.pipeline_name.capitalize()

                if not analysis_results:
                    f.write("Aucun label pertinent trouvé selon les critères de filtrage.\n")
                else:
                    f.write("Labels pertinents (après filtrage et tri) :\n")
                    f.write("=" * 80 + "\n")
                    f.write(f"{'Label':<40} | {'Segments > Thr':>15} | {'Freq (%)':>9} | {'Score Moyen':>12}\n")
                    f.write("-" * 80 + "\n")
                    for label, count, freq_percent, score in analysis_results:
                        f.write(f"{label:<40} | {count:>15} | {freq_percent:>9.2f} | {score:>12.4f}\n")
                    f.write("=" * 80 + "\n")

                # Écrit la liste finale des labels assignés
                assigned_label_title = f"{header_label_category} assigné(s)"
                f.write(f"{assigned_label_title:<25}: {final_label_list if final_label_list else 'Aucun'}\n")
                
                # Nouvelle section pour afficher toutes les probabilités des classes pour les modèles moods_and_context
                if self.pipeline_name in self.MOOD_CONTEXT_PIPELINE_NAMES and all_class_scores:
                    f.write("\nProbabilités moyennes de toutes les classes (triées par score) :\n")
                    f.write("-" * 80 + "\n")
                    # Trie les scores par probabilité décroissante
                    sorted_all_class_scores = sorted(all_class_scores, key=lambda item: item[1], reverse=True)
                    for class_name, score in sorted_all_class_scores:
                        f.write(f"{class_name:<40} : {score:.4f}\n")
                    f.write("-" * 80 + "\n")

                f.write("=" * (len(f"--- Fichier Analysé: {audio_file} ---")) + "\n") # Ligne de fin

        except IOError as e:
            print(f"[ERROR] Erreur d'écriture dans le fichier de résultats "
                  f"'{self.result_file_path}': {e}")
        except Exception as e:
            print(f"[ERROR] Erreur inattendue lors de la sauvegarde des résultats "
                  f"pour {audio_file}: {e}")
            # Optionnel: lever une exception personnalisée si nécessaire

