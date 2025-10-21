
## @package audio_loader
"""
Charge les fichiers audio en mono en utilisant Essentia.

Ce module fournit la classe `AudioLoader` qui gère le chargement des fichiers
audio en format mono via `essentia.standard.MonoLoader`, avec une fréquence
d'échantillonnage et une qualité de rééchantillonnage configurables.
"""

import numpy as np
try:
    from essentia.standard import MonoLoader
    ESSENTIA_AVAILABLE = True
except ImportError:
    ESSENTIA_AVAILABLE = False
    # Définir un substitut si Essentia n'est pas installé
    # pour permettre l'import du module sans erreur immédiate.
    # Les appels réels échoueront si Essentia est nécessaire.
    MonoLoader = object  # type: ignore[misc,assignment]

DEFAULT_SAMPLE_RATE = 16000
DEFAULT_RESAMPLE_QUALITY = 4

## @class AudioLoader
class AudioLoader:
    """
    Charge les fichiers audio en format mono avec des paramètres spécifiés.

    Encapsule la fonctionnalité de chargement de fichiers audio en utilisant
    `essentia.standard.MonoLoader`, permettant la personnalisation de la
    fréquence d'échantillonnage et de la qualité de rééchantillonnage pour
    un traitement audio cohérent.

    :param sample_rate: Fréquence d'échantillonnage cible pour l'audio chargé,
                        en Hz. Défaut à 16000.
    :type sample_rate: int
    :param resample_quality: Niveau de qualité pour le rééchantillonnage
                             (0 à 4, plus élevé est mieux). Défaut à 4.
    :type resample_quality: int
    :raises ImportError: Si la bibliothèque Essentia n'est pas installée.
    """
    def __init__(
        self,
        sample_rate: int = DEFAULT_SAMPLE_RATE,
        resample_quality: int = DEFAULT_RESAMPLE_QUALITY
    ):
        """
        Initialise le chargeur audio avec la fréquence d'échantillonnage
        et la qualité de rééchantillonnage.

        Stocke les paramètres pour les utiliser lors du chargement des fichiers.

        :param sample_rate: Fréquence d'échantillonnage cible en Hz.
        :param resample_quality: Niveau de qualité pour le rééchantillonnage.
        :raises ImportError: Si Essentia n'est pas disponible.
        """
        if not ESSENTIA_AVAILABLE:
            raise ImportError(
                "La bibliothèque Essentia est requise pour AudioLoader mais "
                "n'a pas pu être importée."
            )
        ## @var sample_rate
        # Fréquence d'échantillonnage cible pour l'audio chargé, en Hz.
        self.sample_rate: int = sample_rate
        ## @var resample_quality
        # Niveau de qualité pour le rééchantillonnage (0 à 4).
        self.resample_quality: int = resample_quality

    def load(self, file_path: str) -> np.ndarray:
        """
        Charge un fichier audio en format mono.

        Utilise `essentia.standard.MonoLoader` pour charger le fichier audio
        spécifié, en appliquant la fréquence d'échantillonnage et la qualité
        de rééchantillonnage configurées.

        :param file_path: Chemin vers le fichier audio à charger.
        :type file_path: str
        :return: Signal audio sous forme de tableau NumPy en format mono (float32).
        :rtype: np.ndarray
        :raises RuntimeError: Si Essentia rencontre une erreur lors du chargement
                              (fichier non trouvé, format non supporté, etc.).
        :raises EssentiaException: Pour les erreurs spécifiques à Essentia.
        """
        try:
            # Initialisation de MonoLoader avec les paramètres
            loader = MonoLoader(
                filename=file_path,
                sampleRate=self.sample_rate,
                resampleQuality=self.resample_quality
            )
            # Exécution du chargement
            audio = loader()
            # Essentia retourne un np.array de float32
            return audio
        except Exception as e:
            # Capturer les erreurs potentielles d'Essentia ou autres
            print(f"[ERROR] Erreur lors du chargement du fichier audio "
                  f"'{file_path}' avec Essentia: {e}")
            # Relever l'exception pour que le pipeline puisse la gérer
            raise RuntimeError(f"Échec du chargement de {file_path}") from e

