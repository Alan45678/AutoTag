

"""
Analyse les résultats bruts de prédiction pour extraire les labels pertinents.

Ce module fournit la classe `PredictionAnalyzer` qui traite les sorties
numériques des modèles de classification (scores de probabilité par segment)
pour identifier et classer les labels (genres, humeurs, etc.) les plus
probables en fonction de critères configurables (seuil de confiance, fréquence
minimale, score moyen minimal, nombre maximal de labels).
"""

import numpy as np
from typing import List, Tuple, Optional

class PredictionAnalyzer:
    """
    Analyse et filtre les résultats de prédiction pour la classification audio.

    Traite les tableaux de prédictions brutes pour extraire des labels
    significatifs, en appliquant des critères de filtrage tels que le seuil de
    confiance par segment, la fréquence minimale d'apparition d'un label
    au-dessus du seuil, le score moyen minimal du label sur tous les segments,
    et une limite sur le nombre maximal de labels à retourner. Formate également
    les résultats finaux.

    :param threshold: Score de confiance minimal (0 à 1) pour qu'une prédiction
                      sur un segment soit considérée comme valide pour ce label.
                      Défaut à 0.1.
    :type threshold: float
    :param min_freq: Nombre minimum de segments où un label doit dépasser le
                     `threshold` pour être inclus dans les résultats finaux.
                     Défaut à 0 (pas de filtre de fréquence minimale).
    :type min_freq: int
    :param min_score: Score moyen minimal (0 à 1) qu'un label doit avoir sur
                      *tous* les segments pour être inclus dans les résultats.
                      Défaut à 0.0 (pas de filtre de score minimal).
    :type min_score: float
    :param max_labels: Nombre maximum de labels à retourner, triés par pertinence.
                       Si `None`, aucun nombre maximal n'est appliqué. Défaut à `None`.
    :type max_labels: Optional[int]
    """

    #: Score de confiance minimal pour les prédictions valides par segment.
    threshold: float
    #: Fréquence minimale (nombre de segments) pour inclure un label.
    min_freq: int
    #: Score moyen minimal pour inclure un label.
    min_score: float
    #: Nombre maximum de labels à retourner (None pour illimité).
    max_labels: Optional[int]

    def __init__(
        self,
        threshold: float = 0.1,
        min_freq: int = 0,
        min_score: float = 0.0,
        max_labels: Optional[int] = None
    ):
        """
        Initialise l'analyseur avec les paramètres de filtrage.

        Stocke les critères qui seront utilisés par la méthode `analyze`.
        """
        # Validation simple des paramètres (optionnelle mais recommandée)
        if not 0.0 <= threshold <= 1.0:
            raise ValueError("Le seuil (threshold) doit être entre 0.0 et 1.0")
        if min_freq < 0:
            raise ValueError("La fréquence minimale (min_freq) ne peut pas être négative")
        if not 0.0 <= min_score <= 1.0:
            raise ValueError("Le score minimal (min_score) doit être entre 0.0 et 1.0")
        if max_labels is not None and max_labels < 0:
             raise ValueError("Le nombre maximal de labels (max_labels) ne peut pas être négatif")

        self.threshold = threshold
        self.min_freq = min_freq
        self.min_score = min_score
        self.max_labels = max_labels

    def analyze(
        self,
        predictions: np.ndarray,
        classes: List[str]
    ) -> List[Tuple[str, int, float, float]]:
        """
        Analyse les prédictions pour extraire les labels pertinents.

        Calcule le score moyen et le nombre de détections (fréquence) pour
        chaque classe à travers les segments de prédiction. Filtre ensuite les
        classes en fonction des critères `threshold`, `min_freq`, et `min_score`.
        Trie les classes restantes par fréquence puis par score (décroissant).
        Limite le nombre de résultats si `max_labels` est défini. Calcule
        la fréquence en pourcentage pour les résultats finaux.

        :param predictions: Tableau NumPy des scores de prédiction bruts.
                            Doit avoir la forme (nombre_de_segments, nombre_de_classes).
        :type predictions: numpy.ndarray
        :param classes: Liste des noms de labels (classes) correspondant aux
                        colonnes du tableau `predictions`. La longueur doit
                        correspondre à la deuxième dimension de `predictions`.
        :type classes: List[str]
        :return: Liste de tuples pour chaque label filtré et trié. Chaque tuple
                 contient: `(label, count, freq_percent, mean_score)`.
                 `count` est le nombre de segments où le score > threshold.
                 `freq_percent` est le pourcentage de ce count par rapport au
                 count total des labels retournés.
                 `mean_score` est le score moyen sur tous les segments.
                 La liste est vide si aucune prédiction ne satisfait les critères.
        :rtype: List[Tuple[str, int, float, float]]
        :raises ValueError: Si les dimensions de `predictions` et `classes` ne
                            correspondent pas, ou si `predictions` est vide et
                            que `classes` ne l'est pas (ou vice versa, géré
                            par les opérations numpy).
        """
        if predictions.ndim != 2 or predictions.shape[1] != len(classes):
             if predictions.size == 0 and not classes: # Cas spécial: tout est vide
                 return []
             raise ValueError(f"Incohérence entre la forme des prédictions "
                              f"{predictions.shape} et le nombre de classes {len(classes)}.")

        num_segments = predictions.shape[0]
        if num_segments == 0:
            return [] # Pas de segments à analyser

        # Calculer le score moyen pour chaque classe sur tous les segments
        mean_scores = np.mean(predictions, axis=0)

        # Calculer le nombre de segments où le score dépasse le seuil pour chaque classe
        label_counts = np.sum(predictions > self.threshold, axis=0)

        # Combiner les informations pour chaque classe
        # (label, count, mean_score)
        class_data = list(zip(classes, label_counts, mean_scores))

        # Filtrer les labels basés sur min_freq et min_score
        filtered_data = [
            (label, count, score)
            for label, count, score in class_data
            if count >= self.min_freq and score >= self.min_score
        ]

        # Trier les labels filtrés:
        # Clé primaire: count (décroissant)
        # Clé secondaire: score (décroissant)
        sorted_data = sorted(
            filtered_data,
            key=lambda item: (item[1], item[2]), # item[1] = count, item[2] = score
            reverse=True
        )

        # Limiter le nombre de labels si spécifié
        if self.max_labels is not None:
            final_data = sorted_data[:self.max_labels]
        else:
            final_data = sorted_data

        # Calculer le pourcentage de fréquence basé sur le compte total des labels *retenus*
        total_retained_count = sum(count for _, count, _ in final_data)
        # Éviter la division par zéro si aucun label n'est retenu ou si les comptes sont nuls
        denominator = total_retained_count if total_retained_count > 0 else 1

        # Construire les résultats finaux avec le pourcentage
        results: List[Tuple[str, int, float, float]] = [
            (label, count, (count / denominator) * 100.0, score)
            for label, count, score in final_data
        ]

        return results

    def format_genres(self, analysis_results: List[Tuple[str, int, float, float]]) -> str:
        """
        Formate les résultats d'analyse en une chaîne de labels séparés par " ; ".

        Extrait uniquement les noms des labels de la liste de résultats fournie
        par la méthode `analyze` et les joint en une seule chaîne de caractères.

        :param analysis_results: Liste de tuples `(label, count, freq_percent, score)`
                                 retournée par `analyze()`.
        :type analysis_results: List[Tuple[str, int, float, float]]
        :return: Chaîne contenant les labels joints par " ; ", ou une chaîne
                 vide si la liste `analysis_results` est vide.
        :rtype: str
        """
        # Extrait le premier élément (le label) de chaque tuple dans la liste
        labels = [result[0] for result in analysis_results]
        # Joint les labels avec " ; " comme séparateur
        return " ; ".join(labels) if labels else ""


