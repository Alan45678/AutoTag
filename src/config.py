## @package config
"""
Configuration centralisée pour les pipelines de prédiction.

Ce module définit les classes de configuration utilisées pour paramétrer
et gérer les pipelines de prédiction (ex: genre, humeur). Inclut la
configuration globale (`Config`) et les configurations individuelles de
pipeline (`PipelineConfig`).
Utilise des annotations de type pour une meilleure clarté.
"""

from typing import List, Optional, Dict, Any

## @class Config
class Config:
    """
    Configuration globale pour gérer plusieurs configurations de pipeline.

    Stocke une liste d'objets `PipelineConfig`, permettant la gestion
    centralisée de différents pipelines (par exemple, genre, humeur).

    :param pipelines: Liste d'objets PipelineConfig définissant les paramètres
                      individuels des pipelines.
    :type pipelines: List[PipelineConfig]
    """
    def __init__(self, pipelines: List['PipelineConfig']):
        """
        Initialise la configuration globale avec une liste de pipelines.

        :param pipelines: Liste d'objets PipelineConfig.
        """
        ## @var pipelines
        # Liste des configurations de pipeline individuelles.
        self.pipelines: List[PipelineConfig] = pipelines

## @class PipelineConfig
class PipelineConfig:
    """
    Configuration pour un unique pipeline de prédiction.

    Définit tous les paramètres requis pour exécuter un pipeline, incluant
    les chemins des modèles, les seuils, les paramètres de traitement audio, etc.

    :param name: Nom unique identifiant le pipeline (ex: "genre", "mood").
    :type name: str
    :param data_folder: Chemin vers le dossier contenant les fichiers audio
                        d'entrée.
    :type data_folder: str
    :param embedding_model_path: Chemin vers le fichier du modèle d'embedding
                                 pré-entraîné (ex: TensorFlow .pb).
    :type embedding_model_path: str
    :param prediction_model_path: Chemin vers le fichier du modèle de prédiction
                                  pour la classification (ex: TensorFlow .pb).
    :type prediction_model_path: str
    :param metadata_path: Chemin vers le fichier JSON de métadonnées associé
                          au modèle de prédiction (contenant les classes).
    :type metadata_path: str
    :param result_file_path: Chemin vers le fichier de sortie où les résultats
                             de prédiction seront sauvegardés.
    :type result_file_path: str
    :param tags_to_write: Liste des noms de tags de métadonnées à écrire dans les
                          fichiers audio. Si `None`, utilise ["GENRE_AUTO"].
                          Ex: ["GENRE_AUTO", "TXXX:MOOD", "INSTRUMENT"].
    :type tags_to_write: Optional[List[str]]
    :param threshold: Score de confiance minimal (entre 0 et 1) pour qu'une
                      prédiction de segment soit comptée. Défaut à 0.1.
    :type threshold: float
    :param min_freq: Nombre minimum de segments où un label doit dépasser le
                     `threshold` pour être inclus dans les résultats finaux.
                     Défaut à 0.
    :type min_freq: int
    :param min_score: Score moyen minimal (entre 0 et 1) qu'un label doit avoir
                      sur tous les segments pour être inclus dans les résultats.
                      Défaut à 0.0.
    :type min_score: float
    :param max_labels: Nombre maximum de labels à retourner par fichier audio.
                       Si `None`, pas de limite. Défaut à `None`.
    :type max_labels: Optional[int]
    :param sample_rate: Fréquence d'échantillonnage cible pour le traitement
                        audio, en Hz. Défaut à 16000.
    :type sample_rate: int
    :param resample_quality: Qualité du rééchantillonnage audio (0-4, plus élevé
                             est mieux). Défaut à 4.
    :type resample_quality: int
    :param input_node: Nom du nœud d'entrée dans le graphe computationnel du
                       modèle de *prédiction*. Requis par Essentia TF Predictor.
                       Défaut à "serving_default_model_Placeholder".
    :type input_node: str
    :param output_node: Nom du nœud de sortie dans le graphe computationnel du
                        modèle de *prédiction*. Requis par Essentia TF Predictor.
                        Défaut à "PartitionedCall".
    :type output_node: str
    """
    def __init__(
        self,
        name: str,
        data_folder: str,
        embedding_model_path: str,
        prediction_model_path: str,
        metadata_path: str,
        result_file_path: str,
        # --- Paramètres Optionnels ---
        tags_to_write: Optional[List[str]] = None,
        threshold: float = 0.1,
        min_freq: int = 0,
        min_score: float = 0.0,
        max_labels: Optional[int] = None,
        sample_rate: int = 16000,
        resample_quality: int = 4,
        input_node: str = "serving_default_model_Placeholder",
        output_node: str = "PartitionedCall"
    ):
        """
        Initialise une configuration de pipeline avec les paramètres spécifiés.

        Gère les valeurs par défaut pour les paramètres optionnels et assure
        une initialisation correcte.
        """
        ## @var name
        # Nom du pipeline (ex: "genre", "mood").
        self.name: str = name
        ## @var data_folder
        # Dossier contenant les fichiers audio d'entrée.
        self.data_folder: str = data_folder
        ## @var embedding_model_path
        # Chemin vers le fichier du modèle d'embedding.
        self.embedding_model_path: str = embedding_model_path
        ## @var prediction_model_path
        # Chemin vers le fichier du modèle de prédiction.
        self.prediction_model_path: str = prediction_model_path
        ## @var metadata_path
        # Chemin vers le fichier JSON de métadonnées.
        self.metadata_path: str = metadata_path
        ## @var result_file_path
        # Chemin vers le fichier où les résultats seront sauvegardés.
        self.result_file_path: str = result_file_path
        ## @var tags_to_write
        # Liste des tags de métadonnées à écrire dans le fichier audio.
        self.tags_to_write: List[str] = tags_to_write if tags_to_write is not None else ["GENRE_AUTO"]
        ## @var threshold
        # Seuil de confiance minimal pour les prédictions par segment.
        self.threshold: float = threshold
        ## @var min_freq
        # Fréquence minimale (nombre de segments) pour inclure un label.
        self.min_freq: int = min_freq
        ## @var min_score
        # Score moyen minimal pour inclure un label.
        self.min_score: float = min_score
        ## @var max_labels
        # Nombre maximum de labels à retourner.
        self.max_labels: Optional[int] = max_labels
        ## @var sample_rate
        # Fréquence d'échantillonnage audio en Hz.
        self.sample_rate: int = sample_rate
        ## @var resample_quality
        # Qualité du rééchantillonnage audio.
        self.resample_quality: int = resample_quality
        ## @var input_node
        # Nom du nœud d'entrée du modèle de prédiction.
        self.input_node: str = input_node
        ## @var output_node
        # Nom du nœud de sortie du modèle de prédiction.
        self.output_node: str = output_node

    def to_dict(self) -> Dict[str, Any]:
        """
        Convertit la configuration du pipeline en dictionnaire.

        Utile pour la sérialisation ou l'affichage.

        :return: Dictionnaire représentant la configuration.
        :rtype: Dict[str, Any]
        """
        return self.__dict__