
"""
Orchestre l'exécution d'un pipeline de prédiction de tags audio.
Ce module est maintenant conçu pour qu'une instance de Pipeline traite UN type
d'analyse (ex: genre) en utilisant potentiellement des ressources (embeddings)
pré-calculées et fournies par un orchestrateur externe (main.py).
"""

import traceback
from typing import List, Dict, Any, Optional

# Importations des composants du pipeline
from src.config import PipelineConfig
# AudioLoader et FileManager ne sont plus gérés directement par Pipeline
# src.audio.loader import AudioLoader
# src.audio.file_manager import AudioFileManager
from src.models.loader import ModelLoader # Toujours nécessaire pour les modèles de prédiction
from src.prediction.predictor import Predictor # Injecté
from src.prediction.analyzer import PredictionAnalyzer
from src.output.tag_writer import TagWriter
from src.output.result_handler import ResultHandler
import numpy as np

# tqdm n'est plus utilisé directement ici, géré par main.py


class Pipeline:
    """
    Exécute la logique d'un pipeline de prédiction de tags audio spécifique.

    Reçoit une configuration et un prédicteur. Charge ses propres ressources
    de prédiction (modèle de classification, classes) et peut traiter des
    fichiers en utilisant des embeddings pré-calculés.

    :param config: La configuration spécifique pour ce pipeline.
    :type config: PipelineConfig
    :param predictor: Une instance de Predictor, partagée potentiellement.
    :type predictor: Predictor
    """

    def __init__(self, config: PipelineConfig, predictor: Predictor):
        """
        Initialise les composants spécifiques au pipeline.

        Ne charge pas les modèles ici ; ils sont chargés dans `load_prediction_resources`.
        L'AudioLoader et le FileManager sont gérés par l'orchestrateur.

        :param config: L'objet de configuration du pipeline.
        :param predictor: L'instance de Predictor à utiliser.
        """
        if not isinstance(config, PipelineConfig):
            raise TypeError("L'argument 'config' doit être une instance de PipelineConfig.")
        if not isinstance(predictor, Predictor):
            raise TypeError("L'argument 'predictor' doit être une instance de Predictor.")

        self.config: PipelineConfig = config
        self.predictor: Predictor = predictor # Injecté

        print(f"  [Pipeline __init__ INFO] Initialisation des composants pour '{self.config.name}'...", flush=True)

        # Initialisation des composants spécifiques à ce pipeline
        try:
            # Analyzer, TagWriter, ResultHandler sont spécifiques à chaque pipeline
            self.analyzer = PredictionAnalyzer(
                threshold=config.threshold,
                min_freq=config.min_freq,
                min_score=config.min_score,
                max_labels=config.max_labels
            )
            self.tag_writer = TagWriter()
            self.result_handler = ResultHandler(config.result_file_path, config.name)

            # Attributs pour les modèles et classes, seront chargés par load_prediction_resources
            self._prediction_model: Optional[Any] = None # Type Any pour modèle Essentia
            self._classes: Optional[List[str]] = None
            self._is_regression_pipeline: bool = "arousal_valence" in self.config.name.lower()


            print(f"  [Pipeline __init__ INFO] Composants pour '{self.config.name}' initialisés.", flush=True)
        except Exception as e:
            print(f"  [Pipeline __init__ FATAL ERROR] Échec de l'initialisation d'un composant pour '{self.config.name}': {e}", flush=True)
            traceback.print_exc()
            raise RuntimeError(f"Échec de l'initialisation du pipeline {self.config.name}") from e

    def load_prediction_resources(self, model_loader: ModelLoader):
        """
        Charge les ressources spécifiques à la prédiction pour ce pipeline.
        (Modèle de classification et classes associées).
        Doit être appelée avant `process_file`.

        :param model_loader: Une instance de ModelLoader.
        """
        print(f"    [Pipeline LoadPred] Chargement des ressources de prédiction pour '{self.config.name}'...", flush=True)
        try:
            self._classes = model_loader.load_classes(self.config.metadata_path)
            print(f"    [Pipeline LoadPred DEBUG] {len(self._classes) if self._classes else '0'} classes chargées depuis {self.config.metadata_path}", flush=True)
            
            if self._is_regression_pipeline:
                 print(f"    [Pipeline LoadPred INFO] Pipeline '{self.config.name}' identifié comme régression.", flush=True)

            self._prediction_model = model_loader.load_prediction_model(
                self.config.prediction_model_path,
                input_node=self.config.input_node,
                output_node=self.config.output_node
            )
            print(f"    [Pipeline LoadPred DEBUG] Modèle de prédiction chargé depuis {self.config.prediction_model_path}", flush=True)
            print(f"    [Pipeline LoadPred INFO] Ressources de prédiction chargées pour {self.config.name}.", flush=True)
        except Exception as e:
            print(f"    [Pipeline LoadPred FATAL ERROR] Échec du chargement des modèles de prédiction ou classes pour {self.config.name}.", flush=True)
            print(f"    Erreur: {e}", flush=True)
            traceback.print_exc()
            raise RuntimeError(f"Échec du chargement des ressources de prédiction pour {self.config.name}") from e

    def process_file(self, audio_file_name: str, audio_path: str, embeddings: np.ndarray):
        """
        Traite un fichier audio en utilisant des embeddings pré-calculés.

        Effectue la prédiction, l'analyse, l'écriture des tags et la sauvegarde
        des résultats pour ce pipeline spécifique.

        :param audio_file_name: Nom du fichier audio (pour logs/résultats).
        :param audio_path: Chemin complet du fichier audio (pour TagWriter).
        :param embeddings: Embeddings pré-calculés pour ce fichier audio.
        """
        if self._prediction_model is None or self._classes is None:
            # Gérer le cas où _is_regression_pipeline est True et _classes pourrait être vide (mais pas None)
            if not (self._is_regression_pipeline and self._prediction_model is not None and self._classes is not None):
                 print(f"      [Pipeline Process ERROR] Les ressources de prédiction pour '{self.config.name}' ne sont pas chargées. Appel à load_prediction_resources() manquant ?", flush=True)
                 raise RuntimeError(f"Ressources de prédiction non chargées pour {self.config.name}")

        print(f"      [Pipeline Process DEBUG] '{self.config.name}' - Prédiction des tags pour {audio_file_name}...", flush=True)
        predictions = self.predictor.predict_genres(self._prediction_model, embeddings)
        print(f"      [Pipeline Process INFO] '{self.config.name}' - Prédictions (shape: {getattr(predictions, 'shape', 'N/A')}).", flush=True)

        all_class_scores_data = None
        analysis_results: List[tuple[str, int, float, float]] = [] # Initialisation explicite
        final_label_list_for_results: str 
        value_for_tagging: str

        if not self._is_regression_pipeline:
            if predictions.ndim == 2 and predictions.shape[0] > 0 and self._classes:
                mean_scores_all_classes = np.mean(predictions, axis=0)
                # S'assurer que les longueurs correspondent avant de zipper
                if len(self._classes) == len(mean_scores_all_classes):
                    all_class_scores_data = list(zip(self._classes, mean_scores_all_classes))
                else:
                    print(f"      [Pipeline Process WARNING] '{self.config.name}' - Discordance de longueur entre classes ({len(self._classes)}) et scores ({len(mean_scores_all_classes)}) pour {audio_file_name}. Pas d'affichage 'all_class_scores'.")
                    all_class_scores_data = None


                print(f"      [Pipeline Process DEBUG] '{self.config.name}' - Analyse des prédictions (filtrage/tri)...", flush=True)
                analysis_results = self.analyzer.analyze(predictions, self._classes)
                final_label_list_for_results = self.analyzer.format_genres(analysis_results)
                print(f"      [Pipeline Process INFO] '{self.config.name}' - Analyse terminée. Liste pour résultats: '{final_label_list_for_results if final_label_list_for_results else 'Aucun'}'", flush=True)
            else:
                print(f"      [Pipeline Process WARNING] '{self.config.name}' - Prédictions ou classes non valides pour l'analyse de {audio_file_name}. analysis_results sera vide.", flush=True)
                # analysis_results reste vide, final_label_list_for_results sera ""
                final_label_list_for_results = ""
        else: # Cas régression
            print(f"      [Pipeline Process INFO] '{self.config.name}' - Traitement comme modèle de régression.", flush=True)
            if predictions.ndim == 2 and predictions.shape[0] > 0:
                mean_regression_outputs = np.mean(predictions, axis=0)
                output_names = self._classes if self._classes and len(self._classes) == mean_regression_outputs.shape[0] else [f"Output_{i+1}" for i in range(mean_regression_outputs.shape[0])]
                
                temp_final_labels = []
                for i, val in enumerate(mean_regression_outputs):
                    # Remplir analysis_results pour les modèles de régression
                    # (label, count, freq_percent, score)
                    # Pour la régression: count=1, freq=100% (si une seule sortie), score=valeur prédite
                    analysis_results.append((output_names[i], 1, 100.0, float(val))) 
                    temp_final_labels.append(f"{output_names[i]}: {float(val):.4f}")
                final_label_list_for_results = " ; ".join(temp_final_labels)
                print(f"      [Pipeline Process INFO] '{self.config.name}' - Valeurs de régression pour résultats: {final_label_list_for_results}", flush=True)
            else:
                 print(f"      [Pipeline Process WARNING] '{self.config.name}' - Sorties de régression non valides pour {audio_file_name}. analysis_results sera vide.", flush=True)
                 # analysis_results reste vide, final_label_list_for_results sera ""
                 final_label_list_for_results = ""

        # --- MODIFICATION POUR LE TAG "nan" ---
        # Si analysis_results est vide (aucun label trouvé après analyse, que ce soit classification ou régression),
        # alors la valeur à écrire dans le tag sera "nan".
        # Sinon, on utilise la chaîne de labels formatée.
        if not analysis_results:
            value_for_tagging = "nan"
            print(f"      [Pipeline Process INFO] '{self.config.name}' - Aucun résultat d'analyse, le tag sera '{value_for_tagging}'.", flush=True)
        else:
            value_for_tagging = final_label_list_for_results
        # --- FIN DE LA MODIFICATION ---

        print(f"      [Pipeline Process DEBUG] '{self.config.name}' - Tentative d'écriture des tags: {self.config.tags_to_write} avec la valeur '{value_for_tagging}'", flush=True)
        self.tag_writer.write_tags(audio_path, value_for_tagging, self.config.tags_to_write)

        print(f"      [Pipeline Process DEBUG] '{self.config.name}' - Sauvegarde des résultats dans {self.config.result_file_path}", flush=True)
        config_dict_for_results = {
            'threshold': self.config.threshold,
            'min_freq': self.config.min_freq,
            'min_score': self.config.min_score,
            'max_labels': self.config.max_labels
        }
        self.result_handler.save(
            audio_file_name,
            final_label_list_for_results, # Utilise la chaîne originale pour le fichier de résultats
            analysis_results,
            config_details=config_dict_for_results,
            all_class_scores=all_class_scores_data
        )


