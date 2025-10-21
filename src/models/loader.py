
## @package model_loader
"""
Charge les modèles et les métadonnées pour la prédiction de tags audio.

Ce module fournit la classe `ModelLoader`, qui gère le chargement des labels de
classe à partir de fichiers de métadonnées JSON et des modèles TensorFlow
(via Essentia) pour l'extraction d'embeddings audio et la prédiction de genre,
humeur, ou autres tags.
"""

import json
import os
from typing import List, Any
import numpy as np

try:
    # Importe les prédicteurs spécifiques d'Essentia
    from essentia.standard import TensorflowPredictEffnetDiscogs, TensorflowPredict2D
    ESSENTIA_TF_AVAILABLE = True
except ImportError:
    ESSENTIA_TF_AVAILABLE = False
    # Crée des substituts pour permettre l'import du module même si Essentia/TF manque
    TensorflowPredictEffnetDiscogs = object # type: ignore[misc,assignment]
    TensorflowPredict2D = object # type: ignore[misc,assignment]


## @class ModelLoader
class ModelLoader:
    """
    Charge les métadonnées et les modèles TensorFlow pour les pipelines de prédiction.

    Fournit des méthodes pour charger les labels de classe depuis des fichiers JSON
    et initialiser les modèles TensorFlow (via les wrappers Essentia) pour
    l'extraction d'embeddings et la classification, facilitant les workflows
    de prédiction de tags audio.

    :raises ImportError: Si les composants Essentia/TensorFlow requis ne sont
                         pas installés ou importables.
    """

    def __init__(self):
        """Initialise le chargeur de modèle."""
        if not ESSENTIA_TF_AVAILABLE:
            raise ImportError(
                "Les composants Essentia TensorFlow (TensorflowPredict*) sont requis "
                "pour ModelLoader mais n'ont pas pu être importés. Assurez-vous "
                "qu'Essentia et TensorFlow sont correctement installés."
            )

    def load_classes(self, json_path: str) -> List[str]:
        """
        Charge les labels de classe depuis un fichier de métadonnées JSON.

        Lit un fichier JSON contenant des métadonnées (généralement fourni avec
        le modèle de prédiction) et extrait la liste des labels de classe
        (par exemple, genres, humeurs) utilisés pour la prédiction, à partir de
        la clé "classes".

        :param json_path: Chemin vers le fichier JSON de métadonnées.
        :type json_path: str
        :return: Liste des labels de classe.
        :rtype: List[str]
        :raises FileNotFoundError: Si le fichier JSON n'est pas trouvé.
        :raises json.JSONDecodeError: Si le fichier JSON est mal formé.
        :raises KeyError: Si la clé "classes" est manquante dans le JSON.
        """
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)
            if "classes" not in metadata:
                raise KeyError(f"La clé 'classes' est manquante dans le fichier "
                               f"de métadonnées JSON : '{json_path}'")
            if not isinstance(metadata["classes"], list):
                 raise TypeError(f"La clé 'classes' dans '{json_path}' doit "
                                 f"contenir une liste.")
            return metadata["classes"]
        except FileNotFoundError:
            print(f"[ERROR] Fichier de métadonnées introuvable: {json_path}")
            raise
        except json.JSONDecodeError as e:
            print(f"[ERROR] Erreur de décodage JSON dans {json_path}: {e}")
            raise
        except KeyError as e:
            print(f"[ERROR] Erreur de clé dans {json_path}: {e}")
            raise
        except TypeError as e:
             print(f"[ERROR] Erreur de type dans {json_path}: {e}")
             raise
        except Exception as e:
            print(f"[ERROR] Erreur inattendue lors du chargement des classes depuis "
                  f"{json_path}: {e}")
            raise

    def load_embedding_model(
        self,
        pb_path: str,
        output_node: str = "PartitionedCall:1" # Défaut pour EffnetDiscogs
    ) -> TensorflowPredictEffnetDiscogs:
        """
        Charge le modèle d'embedding pour l'extraction de caractéristiques audio.

        Initialise un modèle `TensorflowPredictEffnetDiscogs` à partir d'un
        fichier de modèle TensorFlow (.pb) pour extraire les embeddings audio.

        :param pb_path: Chemin vers le fichier du modèle TensorFlow (.pb).
        :type pb_path: str
        :param output_node: Nom du nœud de sortie dans le graphe du modèle qui
                            fournit les embeddings.
                            Défaut à "PartitionedCall:1".
        :type output_node: str
        :return: Instance du modèle `TensorflowPredictEffnetDiscogs`.
        :rtype: TensorflowPredictEffnetDiscogs
        :raises RuntimeError: Si Essentia ne peut pas charger le modèle (fichier
                              non trouvé, format incorrect, etc.).
        """
        if not os.path.exists(pb_path):
            raise FileNotFoundError(f"Fichier modèle d'embedding introuvable: {pb_path}")
        try:
            # Note: Assurez-vous que les noms des paramètres correspondent
            # exactement à ceux attendus par le constructeur d'Essentia.
            model = TensorflowPredictEffnetDiscogs(
                graphFilename=pb_path,
                output=output_node
                # inputs=... # Optionnel si non standard
                # isFrozen=... # Optionnel
            )
            print(f"[INFO] Modèle d'embedding chargé depuis: {pb_path}")
            return model
        except Exception as e:
            print(f"[ERROR] Échec du chargement du modèle d'embedding depuis "
                  f"{pb_path}: {e}")
            # Relever une erreur plus générique ou spécifique si possible
            raise RuntimeError(f"Impossible de charger le modèle TF depuis {pb_path}") from e

    def load_prediction_model(
        self,
        pb_path: str,
        input_node: str, # Typiquement requis pour TensorflowPredict2D
        output_node: str = "PartitionedCall:0" # Défaut pour les têtes de classification
    ) -> TensorflowPredict2D:
        """
        Charge le modèle de prédiction pour la classification (genre, humeur...).

        Initialise un modèle `TensorflowPredict2D` à partir d'un fichier de
        modèle TensorFlow (.pb) pour classifier les embeddings audio en labels.

        :param pb_path: Chemin vers le fichier du modèle TensorFlow (.pb).
        :type pb_path: str
        :param input_node: Nom du nœud d'entrée dans le graphe du modèle qui
                           reçoit les embeddings.
        :type input_node: str
        :param output_node: Nom du nœud de sortie dans le graphe du modèle qui
                            fournit les prédictions (scores/logits).
                            Défaut à "PartitionedCall:0".
        :type output_node: str
        :return: Instance du modèle `TensorflowPredict2D`.
        :rtype: TensorflowPredict2D
        :raises RuntimeError: Si Essentia ne peut pas charger le modèle.
        """
        if not os.path.exists(pb_path):
            raise FileNotFoundError(f"Fichier modèle de prédiction introuvable: {pb_path}")
        try:
            # Vérifie les noms des paramètres pour TensorflowPredict2D
            model = TensorflowPredict2D(
                graphFilename=pb_path,
                input=input_node,
                output=output_node
            )
            print(f"[INFO] Modèle de prédiction chargé depuis: {pb_path}")
            return model
        except Exception as e:
            print(f"[ERROR] Échec du chargement du modèle de prédiction depuis "
                  f"{pb_path}: {e}")
            raise RuntimeError(f"Impossible de charger le modèle TF depuis {pb_path}") from e


