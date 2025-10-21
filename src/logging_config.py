
## @package logging_config
"""
Configuration du logging pour écrire dans un fichier et sur la console.

Ce module met en place un système de logging centralisé qui enregistre les logs
à la fois dans un fichier et sur la console, en assurant la compatibilité avec
la barre de progression `tqdm`. Il inclut un gestionnaire personnalisé pour
`tqdm` et redirige `stdout`/`stderr` vers le système de logging.

**Note:** Ce module est actuellement désactivé dans `main.py` au profit de `print()`.
"""

import logging
import sys
from tqdm import tqdm
import io  # Pour StdoutStderrToLog
import os

DEFAULT_LOG_FILE = "log_global.txt"
DEFAULT_LOG_LEVEL = logging.INFO

## @class TqdmLoggingHandler
class TqdmLoggingHandler(logging.StreamHandler):
    """
    Gestionnaire de logging personnalisé qui s'intègre aux barres `tqdm`.

    Redirige les messages de log vers la console via `tqdm.write`, garantissant
    que la sortie de log n'interfère pas avec le rendu de la barre de progression.
    Utilise `sys.stdout` comme flux sous-jacent.
    """
    def __init__(self, stream=None):
        """
        Initialise le gestionnaire.

        :param stream: Le flux de sortie. Si None, utilise sys.stdout.
                       (Normalement, on le laisse à None pour utiliser tqdm.write)
        """
        # Initialiser avec sys.stdout car tqdm.write écrit sur stdout par défaut
        super().__init__(stream if stream else sys.stdout)

    def emit(self, record: logging.LogRecord):
        """
        Émet un enregistrement de log vers la console via `tqdm`.

        Formate l'enregistrement de log et l'écrit en utilisant `tqdm.write`
        pour éviter les conflits avec les barres de progression, puis vide le flux.

        :param record: L'enregistrement de log à émettre.
        :type record: logging.LogRecord
        """
        try:
            msg = self.format(record)
            # Utilise tqdm.write pour écrire le message sans perturber la barre
            tqdm.write(msg, file=self.stream, end=getattr(self, 'terminator', '\n'))
            self.flush()
        except Exception:
            self.handleError(record)

## @class StdoutStderrToLog
class StdoutStderrToLog(io.TextIOBase):
    """
    Classe semblable à un fichier pour rediriger stdout/stderr vers le logger.

    Capture la sortie écrite sur `sys.stdout` ou `sys.stderr` (par exemple,
    via `print` ou des exceptions non capturées) et l'envoie au système de
    logging Python.
    """
    def __init__(self, logger_instance: logging.Logger, log_level: int = logging.INFO):
        """
        Initialise le redirecteur.

        :param logger_instance: L'instance du logger à utiliser.
        :param log_level: Le niveau de log à utiliser (ex: logging.INFO, logging.ERROR).
        """
        self.logger = logger_instance
        self.log_level = log_level
        self._buffer = "" # Pour gérer les écritures partielles

    def write(self, message: str):
        """
        Écrit un message dans le logger avec le niveau spécifié.

        Les messages vides ou contenant uniquement des espaces sont ignorés.
        Gère les messages contenant des sauts de ligne.

        :param message: Le message à logger.
        """
        self._buffer += message
        lines = self._buffer.splitlines(True) # Garde les délimiteurs
        for line in lines:
            if line.endswith(('\n', '\r')):
                cleaned_line = line.rstrip()
                if cleaned_line: # Ne pas logger les lignes vides
                    self.logger.log(self.log_level, cleaned_line)
            else:
                # Garde la ligne incomplète dans le buffer
                self._buffer = line
                break # Sortir, attendre le reste de la ligne
        else:
             # Si la boucle s'est terminée sans break (pas de ligne incomplète)
             self._buffer = ""


    def flush(self):
        """
        Vide le buffer interne (optionnel, généralement pas nécessaire).

        Peut être utile si des écritures partielles doivent être forcées.
        """
        if self._buffer:
             # Logge ce qui reste dans le buffer même sans saut de ligne final
             self.logger.log(self.log_level, self._buffer)
             self._buffer = ""

    # Méthodes nécessaires pour l'interface TextIOBase
    def readable(self) -> bool: return False
    def seekable(self) -> bool: return False
    def writable(self) -> bool: return True


def setup_logging(
    log_file: str = DEFAULT_LOG_FILE,
    level: int = DEFAULT_LOG_LEVEL,
    redirect_stdout_stderr: bool = True
):
    """
    Configure le système de logging pour la sortie fichier et console (via tqdm).

    Met en place un logger racine avec des gestionnaires pour un fichier de log
    et pour la console (utilisant `TqdmLoggingHandler`).
    Optionnellement, redirige `sys.stdout` et `sys.stderr` vers le logger
    pour capturer les `print()` et les erreurs non gérées.
    Efface les gestionnaires existants sur le logger racine pour éviter les doublons.

    :param log_file: Chemin vers le fichier où les logs seront sauvegardés.
                     Défaut à "log_global.txt".
    :type log_file: str
    :param level: Niveau de log minimal à capturer (ex: logging.INFO, logging.DEBUG).
                  Défaut à logging.INFO.
    :type level: int
    :param redirect_stdout_stderr: Si True, redirige sys.stdout et sys.stderr
                                   vers le logger. Défaut à True.
    :type redirect_stdout_stderr: bool
    """
    # Récupérer le logger racine
    logger = logging.getLogger()
    logger.setLevel(level)

    # Effacer les gestionnaires existants pour éviter les logs dupliqués
    # si cette fonction est appelée plusieurs fois.
    if logger.hasHandlers():
        logger.handlers.clear()

    # Définir le format des logs
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    formatter = logging.Formatter(log_format)

    # --- Gestionnaire pour la console (compatible avec tqdm) ---
    console_handler = TqdmLoggingHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # --- Gestionnaire pour le fichier ---
    try:
        # S'assurer que le répertoire du fichier de log existe
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)

        file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        # Si on ne peut pas créer le fichier de log, on log au moins sur console
        logger.error(f"Impossible de créer le gestionnaire de fichier de log "
                     f"'{log_file}': {e}. Les logs iront seulement sur la console.")

    # --- Redirection optionnelle de stdout/stderr ---
    if redirect_stdout_stderr:
        # Rediriger sys.stdout vers le logger au niveau INFO
        sys.stdout = StdoutStderrToLog(logger, logging.INFO) # type: ignore[assignment]
        # Rediriger sys.stderr vers le logger au niveau ERROR
        sys.stderr = StdoutStderrToLog(logger, logging.ERROR) # type: ignore[assignment]

    logger.info("Système de logging initialisé.")
    if redirect_stdout_stderr:
        logger.info("Redirection de stdout et stderr vers le logger activée.")


