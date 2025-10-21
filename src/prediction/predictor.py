
"""
Gère l'extraction d'embeddings et la prédiction de tags à partir de modèles.

Ce module fournit la classe `Predictor` qui encapsule l'utilisation des modèles
TensorFlow (via Essentia wrappers) pour deux étapes clés :
1. Extraire des vecteurs d'embedding à partir de données audio brutes.
2. Prédire des scores de classification (ex: genre, humeur) à partir de ces embeddings.
"""

import numpy as np
# Importations de types pour l'annotation (si Essentia est typé, sinon utiliser Any)
from typing import Any # Remplacer par les types Essentia si disponibles

# Utilisation de Any car les types spécifiques d'Essentia ne sont pas importés ici
# pour éviter la dépendance directe dans ce module simple. L'appelant (Pipeline)
# passera les objets Essentia corrects.
EssentiaEmbeddingModel = Any
EssentiaPredictionModel = Any

class Predictor:
    """
    Gère l'extraction d'embeddings et la prédiction de classes audio.

    Fournit des méthodes distinctes pour utiliser un modèle d'embedding afin de
    transformer l'audio en vecteurs de caractéristiques, et pour utiliser un
    modèle de classification afin d'obtenir des scores de prédiction à partir
    de ces vecteurs. Conçu pour être utilisé au sein d'un pipeline de traitement.
    """

    def extract_embeddings(
        self,
        embedding_model: EssentiaEmbeddingModel,
        audio_data: np.ndarray
    ) -> np.ndarray:
        """
        Extrait les embeddings audio à partir d'un signal audio brut.

        Utilise le modèle d'embedding fourni (typiquement un modèle Essentia
        comme `TensorflowPredictEffnetDiscogs`) pour traiter le signal audio
        et retourne les embeddings résultants.

        :param embedding_model: L'instance du modèle d'embedding pré-chargé.
        :type embedding_model: EssentiaEmbeddingModel (par ex., TensorflowPredictEffnetDiscogs)
        :param audio_data: Le signal audio sous forme de tableau NumPy (typiquement float32).
        :type audio_data: numpy.ndarray
        :return: Les embeddings extraits sous forme de tableau NumPy. La forme dépend
                 du modèle (ex: `(nombre_de_frames, dimension_embedding)`).
        :rtype: numpy.ndarray
        :raises Exception: Peut lever des exceptions spécifiques à Essentia/TensorFlow
                           si le modèle rencontre une erreur lors de l'inférence.
        """
        print("[Predictor DEBUG] Appel du modèle d'embedding...", flush=True)
        try:
            # L'appel direct `embedding_model(audio_data)` exécute l'inférence dans Essentia
            embeddings = embedding_model(audio_data)
            print(f"[Predictor DEBUG] Embeddings obtenus (shape: {getattr(embeddings, 'shape', 'N/A')})", flush=True)
            return embeddings
        except Exception as e:
            print(f"[Predictor ERROR] Erreur lors de l'extraction des embeddings: {e}", flush=True)
            # Relever l'exception pour que le pipeline puisse la gérer
            raise RuntimeError("Échec de l'extraction des embeddings") from e

    def predict_genres(
        self,
        prediction_model: EssentiaPredictionModel,
        embeddings: np.ndarray
    ) -> np.ndarray:
        """
        Prédit les scores de classe (genre, humeur...) à partir des embeddings.

        Utilise le modèle de prédiction fourni (typiquement un modèle Essentia
        comme `TensorflowPredict2D`) pour traiter les embeddings et retourne
        les scores de probabilité pour chaque classe.

        :param prediction_model: L'instance du modèle de prédiction pré-chargé.
        :type prediction_model: EssentiaPredictionModel (par ex., TensorflowPredict2D)
        :param embeddings: Les embeddings audio sous forme de tableau NumPy,
                           typiquement la sortie de `extract_embeddings()`.
        :type embeddings: numpy.ndarray
        :return: Tableau NumPy des scores de prédiction. La forme est généralement
                 `(nombre_de_frames, nombre_de_classes)`.
        :rtype: numpy.ndarray
        :raises Exception: Peut lever des exceptions spécifiques à Essentia/TensorFlow
                           si le modèle rencontre une erreur lors de l'inférence.
        """
        print("[Predictor DEBUG] Appel du modèle de prédiction...", flush=True)
        try:
            # L'appel direct `prediction_model(embeddings)` exécute l'inférence
            predictions = prediction_model(embeddings)
            print(f"[Predictor DEBUG] Prédictions obtenues (shape: {getattr(predictions, 'shape', 'N/A')})", flush=True)
            return predictions
        except Exception as e:
            print(f"[Predictor ERROR] Erreur lors de la prédiction des classes: {e}", flush=True)
            # Relever l'exception
            raise RuntimeError("Échec de la prédiction des classes") from e



