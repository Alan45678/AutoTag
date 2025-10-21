## @package file_manager
"""
Gestion de la découverte et du filtrage des fichiers audio.

Ce module fournit la classe `AudioFileManager` pour rechercher des fichiers audio
dans un répertoire spécifié et accéder à leurs chemins complets.
"""

import os
from typing import List, Generator

## @class AudioFileManager
class AudioFileManager:
    """
    Gère la découverte et la résolution des chemins des fichiers audio.

    Fournit des méthodes pour lister les fichiers audio dans un répertoire donné
    et récupérer leurs chemins complets, facilitant le traitement des fichiers
    audio dans un pipeline.

    :param data_folder: Chemin vers le répertoire contenant les fichiers audio.
    :type data_folder: str
    """
    def __init__(self, data_folder: str):
        """
        Initialise le gestionnaire de fichiers audio avec un dossier de données.

        Stocke le chemin vers le répertoire contenant les fichiers audio pour
        la découverte ultérieure des fichiers et la résolution des chemins.

        :param data_folder: Chemin vers le répertoire contenant les fichiers audio.
        :type data_folder: str
        """
        if not os.path.isdir(data_folder):
            # Lève une erreur tôt si le dossier n'existe pas/pas un dossier
            raise FileNotFoundError(
                f"Le dossier de données spécifié n'existe pas ou n'est pas un "
                f"répertoire : '{data_folder}'"
            )
        ## @var data_folder
        # Chemin vers le répertoire contenant les fichiers audio.
        self.data_folder: str = data_folder
        ## @var _supported_extensions
        # Tuple des extensions de fichiers audio supportées (en minuscules).
        self._supported_extensions: tuple[str, ...] = (
            ".mp3", ".wav", ".flac", ".mp4", ".m4a", ".ogg" # Ajout m4a, ogg
        )

    def get_audio_files(self) -> List[str]:
        """
        Récupère une liste des noms de fichiers audio dans le dossier de données.

        Scanne le `data_folder` et retourne une liste de noms de fichiers
        (sans le chemin complet) ayant des extensions audio supportées.
        Seuls les fichiers directement dans le dossier spécifié sont inclus.
        La recherche est insensible à la casse pour les extensions.

        :return: Liste des noms de fichiers audio (ex: "song.mp3").
        :rtype: List[str]
        :raises FileNotFoundError: Si `data_folder` n'existe pas lors de l'appel.
                                   (Normalement attrapé dans __init__)
        :raises NotADirectoryError: Si `data_folder` n'est pas un répertoire.
                                    (Normalement attrapé dans __init__)
        """
        try:
            return [
                f for f in os.listdir(self.data_folder)
                if os.path.isfile(os.path.join(self.data_folder, f)) and
                f.lower().endswith(self._supported_extensions)
            ]
        except FileNotFoundError:
            # Redondant si __init__ vérifie, mais sécurité supplémentaire
            print(f"[ERROR] Dossier non trouvé lors de la recherche de fichiers: "
                  f"{self.data_folder}")
            raise
        except NotADirectoryError:
            print(f"[ERROR] Le chemin spécifié n'est pas un dossier: "
                  f"{self.data_folder}")
            raise
        except Exception as e:
            print(f"[ERROR] Erreur inattendue lors de la liste des fichiers dans "
                  f"{self.data_folder}: {e}")
            raise # Re-lever l'erreur pour la gestion en amont

    def get_full_path(self, filename: str) -> str:
        """
        Construit le chemin complet vers un fichier audio.

        Combine le chemin `data_folder` avec le nom de fichier fourni pour
        retourner le chemin d'accès complet au fichier.

        :param filename: Nom du fichier audio (par exemple, "song.mp3").
        :type filename: str
        :return: Chemin complet vers le fichier audio.
        :rtype: str
        """
        return os.path.join(self.data_folder, filename)

    def yield_audio_files(self) -> Generator[str, None, None]:
        """
        Génère les chemins complets des fichiers audio un par un.

        Alternative à `get_audio_files` pour itérer sur les fichiers sans
        charger toute la liste en mémoire, utile pour les très grands dossiers.

        :yield: Chemin complet vers le prochain fichier audio trouvé.
        :rtype: Generator[str, None, None]
        """
        try:
            for filename in os.listdir(self.data_folder):
                full_path = os.path.join(self.data_folder, filename)
                if os.path.isfile(full_path) and \
                   filename.lower().endswith(self._supported_extensions):
                    yield full_path
        except FileNotFoundError:
            print(f"[ERROR] Dossier non trouvé lors de la recherche de fichiers: "
                  f"{self.data_folder}")
            raise
        except NotADirectoryError:
            print(f"[ERROR] Le chemin spécifié n'est pas un dossier: "
                  f"{self.data_folder}")
            raise
        except Exception as e:
            print(f"[ERROR] Erreur inattendue lors de la génération des fichiers "
                  f"depuis {self.data_folder}: {e}")
            raise


