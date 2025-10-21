# src/output/tag_writer.py
import traceback
from typing import List, Dict, Callable, Type, Optional, Union

# --- Importations Mutagen ---
try:
    from mutagen import File as MutagenFile, MutagenError
    from mutagen.mp3 import MP3  # Explicitly import MP3
    from mutagen.id3 import ID3, TXXX, ID3NoHeaderError, PictureType, APIC
    from mutagen.flac import FLAC, Picture as FlacPicture
    from mutagen.mp4 import MP4, MP4Tags, MP4Cover, MP4FreeForm, AtomDataType
    from mutagen.wave import WAVE
    from mutagen.oggvorbis import OggVorbis
    from mutagen.oggopus import OggOpus
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False
    # Créer des substituts pour que le module puisse être importé
    class MutagenError(Exception): pass
    class ID3NoHeaderError(MutagenError): pass
    MutagenFile = object
    MP3 = object
    WAVE = object
    FLAC = object
    MP4 = object
    OggVorbis = object
    OggOpus = object
    ID3 = object
    TXXX = object
    MP4Tags = object
    MP4FreeForm = object
    print("[WARN] Bibliothèque Mutagen non trouvée. L'écriture des tags sera désactivée.")
# --- Fin Importations Mutagen ---

# Type hinting pour les objets Mutagen potentiellement mockés
MutagenFileType = Type[Union[MP3, FLAC, MP4, WAVE, OggVorbis, OggOpus, object]]

class TagWriter:
    """
    Gère l'écriture des tags (genre, humeur, instrument) dans les métadonnées
    des fichiers audio en utilisant `mutagen`. Utilise `print` pour le débogage.

    Supporte les formats MP3 (ID3), FLAC (Vorbis Comment), MP4 (iTunes-style),
    et WAVE (ID3 dans RIFF).
    """

    def __init__(self):
        """Initialise le TagWriter."""
        if not MUTAGEN_AVAILABLE:
            print("[TagWriter WARN] Mutagen non disponible, TagWriter ne fonctionnera pas.")
        # Dictionnaire associant les types Mutagen aux méthodes de gestion des tags
        self._TAG_HANDLERS: Dict[MutagenFileType, Callable] = {}
        if MUTAGEN_AVAILABLE:
            self._TAG_HANDLERS = {
                MP3: self._write_id3_tags,
                WAVE: lambda audio, tag, value: self._write_id3_tags(audio, tag, value, is_wave=True),
                FLAC: self._write_vorbis_comment_tags,  # FLAC utilise Vorbis Comments
                MP4: self._write_mp4_tags,
                OggVorbis: self._write_vorbis_comment_tags,  # Ogg Vorbis aussi
                OggOpus: self._write_vorbis_comment_tags,  # Ogg Opus aussi
            }

    def write_tags(self, filename: str, value_list_str: str, tags_to_write: List[str]):
        """
        Tente d'écrire les tags spécifiés dans un fichier audio.

        Ouvre le fichier avec `mutagen`, détermine le type de fichier, nettoie
        la chaîne de valeurs, appelle le gestionnaire de tags approprié pour
        chaque tag à écrire, et sauvegarde les modifications.

        :param filename: Chemin complet vers le fichier audio.
        :type filename: str
        :param value_list_str: Chaîne contenant les valeurs à écrire, séparées
                               par " ; " (ex: "Rock ; Electronic---Techno").
                               Sera nettoyée avant écriture.
        :type value_list_str: str
        :param tags_to_write: Liste des identifiants de tags à écrire (ex:
                              ["GENRE_AUTO", "TXXX:MOOD", "INSTRUMENT"]).
        :type tags_to_write: List[str]
        """
        if not MUTAGEN_AVAILABLE:
            print(f"[TagWriter INFO] Mutagen non disponible, impossible d'écrire des tags pour {filename}", flush=True)
            return
        if not tags_to_write:
            print(f"[TagWriter INFO] Aucune clé de tag fournie pour {filename}, écriture ignorée.", flush=True)
            return

        print(f"[TagWriter INFO] Tentative d'écriture des tags {tags_to_write} pour le fichier: {filename}", flush=True)
        audio: Optional[MutagenFile] = None  # Initialiser à None

        try:
            # Ouvrir le fichier avec Mutagen, easy=False pour obtenir l'objet spécifique au format
            print(f"[TagWriter DEBUG] Ouverture du fichier avec Mutagen: {filename}", flush=True)
            audio = MutagenFile(filename, easy=False)

            if audio is None:
                # Mutagen peut retourner None si le type n'est pas reconnu ou erreur mineure
                print(f"[TagWriter ERROR] Mutagen a retourné None pour {filename}. Format non supporté ou erreur à l'ouverture.", flush=True)
                return

            file_type = type(audio)
            print(f"[TagWriter DEBUG] Fichier ouvert. Type détecté: {file_type.__name__}", flush=True)

            # Trouver le bon handler pour le type de fichier
            handler = self._TAG_HANDLERS.get(file_type)
            if not handler:
                print(f"[TagWriter WARNING] Type de fichier non géré pour l'écriture de tags: {file_type.__name__} pour le fichier {filename}", flush=True)
                return

            if audio.tags is None:
                print(f"[TagWriter INFO] Conteneur de tags absent pour {filename}. Tentative d'initialisation...", flush=True)
                try:
                    audio.add_tags()
                    if audio.tags is not None:
                        print(f"[TagWriter INFO] Conteneur de tags initialisé pour {filename} (Type: {type(audio.tags).__name__})", flush=True)
                    else:
                        print(f"[TagWriter ERROR] Échec de l'initialisation du conteneur de tags pour {filename} après appel à add_tags().", flush=True)
                        return
                except MutagenError as tag_init_error:
                    print(f"[TagWriter ERROR] Échec de l'initialisation du conteneur de tags pour {filename}: {tag_init_error}", flush=True)
                    return

            print(f"[TagWriter DEBUG] Nettoyage de la chaîne de valeurs d'entrée: '{value_list_str}'", flush=True)
            cleaned_value_str = self._clean_and_format_value_list(value_list_str)
            print(f"[TagWriter DEBUG] Chaîne de valeurs nettoyée pour l'écriture: '{cleaned_value_str}'", flush=True)

            if not cleaned_value_str and value_list_str: # Si l'entrée n'était pas vide mais est devenue vide
                print(f"[TagWriter WARNING] La chaîne de valeurs '{value_list_str}' est devenue vide après nettoyage. Tags '{tags_to_write}' ne seront pas écrits.", flush=True)
                return
            elif not cleaned_value_str and not value_list_str: # Si l'entrée était vide
                 print(f"[TagWriter INFO] Chaîne de valeurs vide fournie. Aucun tag ne sera écrit pour '{tags_to_write}'.", flush=True)
                 return


            tags_were_modified = False
            print(f"[TagWriter DEBUG] Traitement des tags à écrire: {tags_to_write}", flush=True)
            for tag_id in tags_to_write:
                print(f"[TagWriter DEBUG] Traitement du tag '{tag_id}'...", flush=True)
                try:
                    modified = handler(audio, tag_id, cleaned_value_str)
                    if modified:
                        tags_were_modified = True
                except Exception as write_err:
                    print(f"[TagWriter ERROR] Échec de l'écriture du tag '{tag_id}' dans {filename}: {write_err}", flush=True)
                    traceback.print_exc()

            if tags_were_modified:
                try:
                    print(f"[TagWriter DEBUG] Tentative de sauvegarde des modifications dans {filename}", flush=True)
                    audio.save()
                    print(f"[TagWriter INFO] Tags sauvegardés avec succès dans {filename}", flush=True)
                except MutagenError as save_err:
                    print(f"[TagWriter ERROR] Échec de la sauvegarde des tags pour {filename}: {save_err}", flush=True)
                    traceback.print_exc()
                except Exception as generic_save_err:
                    print(f"[TagWriter ERROR] Erreur générique lors de la sauvegarde des tags pour {filename}: {generic_save_err}", flush=True)
                    traceback.print_exc()
            else:
                print(f"[TagWriter INFO] Aucune modification de tag détectée, sauvegarde ignorée pour {filename}.", flush=True)

        except ID3NoHeaderError:
            print(f"[TagWriter WARNING] Le fichier {filename} n'a pas d'en-tête ID3. Impossible d'écrire les tags ID3.", flush=True)
        except MutagenError as e:
            print(f"[TagWriter ERROR] Erreur Mutagen lors du traitement du fichier ${filename}: {e}", flush=True)
            traceback.print_exc()
        except FileNotFoundError:
            print(f"[TagWriter ERROR] Fichier non trouvé pour l'écriture de tags: {filename}", flush=True)
        except PermissionError:
            print(f"[TagWriter ERROR] Permission refusée pour écrire les tags dans le fichier: {filename}", flush=True)
        except Exception as e:
            print(f"[TagWriter ERROR] Erreur inattendue lors de la gestion du fichier {filename} pour l'écriture de tags: {e}", flush=True)
            traceback.print_exc()

    def _write_id3_tags(self, audio: Union[MP3, WAVE], tag_id: str, value: str, is_wave: bool = False) -> bool:
        file_format = "WAVE (ID3)" if is_wave else "MP3"
        print(f"[TagWriter DEBUG] _write_id3_tags ({file_format}) appelé pour le tag '{tag_id}'", flush=True)

        if not isinstance(audio.tags, ID3):
            print(f"[TagWriter ERROR] Impossible d'écrire les tags ID3: audio.tags n'est pas une instance ID3 pour {audio.filename}", flush=True)
            return False

        desc = None
        if tag_id.startswith("TXXX:"):
            desc = tag_id.split(":", 1)[1]
            if not desc:
                print(f"[TagWriter WARNING] Ignorer le tag TXXX invalide '{tag_id}' (description vide) pour {audio.filename}", flush=True)
                return False
        elif tag_id == "GENRE_AUTO":
            desc = "GENRE_AUTO"
        elif tag_id == "INSTRUMENT":
            desc = "INSTRUMENT"
        else:
            print(f"[TagWriter WARNING] Tag ID3 non supporté '{tag_id}' spécifié dans la configuration pour {audio.filename}.", flush=True)
            return False

        new_tag = TXXX(encoding=3, desc=desc, text=value)
        existing_tags = audio.tags.getall(f"TXXX:{desc}")
        if existing_tags and any(t.text == [value] for t in existing_tags):
            print(f"[TagWriter DEBUG] Le tag TXXX:{desc} existe déjà avec la même valeur ('{value}') pour {audio.filename}. Pas de modification.", flush=True)
            return False

        print(f"[TagWriter DEBUG] Écriture/Mise à jour du tag {file_format}: desc='{desc}', value='{value}'", flush=True)
        audio.tags.setall(f"TXXX:{desc}", [new_tag])
        print(f"[TagWriter DEBUG] Tag TXXX:{desc} ajouté/mis à jour.", flush=True)
        return True

    def _write_vorbis_comment_tags(self, audio: Union[FLAC, OggVorbis, OggOpus], tag_id: str, value: str) -> bool:
        file_format = type(audio).__name__
        print(f"[TagWriter DEBUG] _write_vorbis_comment_tags ({file_format}) appelé pour le tag '{tag_id}'", flush=True)

        if audio.tags is None:
            print(f"[TagWriter ERROR] Impossible d'écrire les tags Vorbis Comment: audio.tags est None pour {audio.filename}", flush=True)
            return False

        tag_key = ""
        if tag_id.startswith("TXXX:"):
            tag_key = tag_id.split(":", 1)[1].upper()
        elif tag_id == "GENRE_AUTO":
            tag_key = "GENRE_AUTO"
        elif tag_id == "INSTRUMENT":
            tag_key = "INSTRUMENT"
        else:
            print(f"[TagWriter WARNING] Tag Vorbis Comment non supporté '{tag_id}' spécifié pour {audio.filename}.", flush=True)
            return False

        if not tag_key:
            print(f"[TagWriter WARNING] Clé de tag Vorbis Comment invalide dérivée de '{tag_id}' pour {audio.filename}.", flush=True)
            return False

        new_value_list = [value]
        if tag_key in audio.tags and audio.tags[tag_key] == new_value_list:
            print(f"[TagWriter DEBUG] Le tag Vorbis Comment '{tag_key}' existe déjà avec la même valeur ('{value}') pour {audio.filename}. Pas de modification.", flush=True)
            return False

        print(f"[TagWriter DEBUG] Écriture/Mise à jour du tag {file_format} '{tag_key}' avec la valeur '{value}' pour {audio.filename}", flush=True)
        audio.tags[tag_key] = new_value_list
        print(f"[TagWriter DEBUG] Tag Vorbis Comment '{tag_key}' écrit.", flush=True)
        return True

    def _write_mp4_tags(self, audio: MP4, tag_id: str, value: str) -> bool:
        print(f"[TagWriter DEBUG] _write_mp4_tags appelé pour le tag '{tag_id}'", flush=True)

        if not isinstance(audio.tags, MP4Tags):
            print(f"[TagWriter ERROR] Impossible d'écrire les tags MP4: audio.tags n'est pas une instance MP4Tags pour {audio.filename}", flush=True)
            return False

        desc = ""
        if tag_id.startswith("TXXX:"):
            desc = tag_id.split(":", 1)[1]
        elif tag_id == "GENRE_AUTO":
            desc = "GENRE_AUTO"
        elif tag_id == "INSTRUMENT":
            desc = "INSTRUMENT"
        else:
            print(f"[TagWriter WARNING] Tag MP4 non supporté '{tag_id}' spécifié pour {audio.filename}.", flush=True)
            return False

        if not desc:
            print(f"[TagWriter WARNING] Description de tag MP4 invalide dérivée de '{tag_id}' pour {audio.filename}.", flush=True)
            return False

        tag_key = f"----:com.apple.iTunes:{desc}"
        print(f"[TagWriter DEBUG] Clé de tag MP4 construite: {tag_key}", flush=True)

        encoded_value = value.encode('utf-8')
        new_tag_data = [MP4FreeForm(encoded_value, dataformat=AtomDataType.UTF8)]

        if tag_key in audio.tags:
            existing_tags_data = audio.tags[tag_key]
            if isinstance(existing_tags_data, list) and \
               len(existing_tags_data) == 1 and \
               isinstance(existing_tags_data[0], bytes) and \
               existing_tags_data[0] == encoded_value:
                print(f"[TagWriter DEBUG] Le tag MP4 '{tag_key}' existe déjà avec la même valeur pour {audio.filename}. Pas de modification.", flush=True)
                return False

        print(f"[TagWriter DEBUG] Écriture/Mise à jour du tag MP4 '{tag_key}' avec la valeur '{value}' pour {audio.filename}", flush=True)
        audio.tags[tag_key] = new_tag_data
        print(f"[TagWriter DEBUG] Tag MP4 '{tag_key}' écrit.", flush=True)
        return True

    def _custom_title_case(self, text: str) -> str:
        """
        Applies title case to each word, preserving hyphens and capitalizing
        parts of hyphenated words.
        e.g., "jazzy hip-hop" -> "Jazzy Hip-Hop", "boom bap" -> "Boom Bap"
        """
        if not text:
            return ""
        
        words = text.split(' ')
        cased_words = []
        for word in words:
            # Remove leading/trailing hyphens before processing parts
            stripped_word = word.strip('-')
            if '-' in stripped_word:
                # Capitalize each part of a hyphenated segment
                cased_words.append('-'.join(p.capitalize() for p in stripped_word.split('-')))
            elif stripped_word: # Ensure word is not empty after stripping
                cased_words.append(stripped_word.capitalize())
            # If word was just hyphens or became empty, it's effectively skipped unless it was the only "word"
        
        if not cased_words and text.strip(): # Handle cases like input "---" resulting in empty list
            return text # Or decide on specific handling, e.g. empty string or original
            
        return ' '.join(cased_words)

    def _clean_and_format_value_list(self, input_string: Optional[str]) -> str:
        """
        Nettoie et formate une chaîne de valeurs séparées par des points-virgules,
        en respectant l'ordre d'origine des genres/sous-genres uniques
        et en appliquant une capitalisation de type "Titre".

        Exemple: "Hip Hop---Instrumental ; Hip Hop---Boom Bap"
        Devient: "Hip Hop ; Instrumental ; Boom Bap"
        """
        print(f"[TagWriter DEBUG] _clean_and_format_value_list entrée: '{input_string}'", flush=True)
        if not isinstance(input_string, str) or not input_string.strip():
            print("[TagWriter DEBUG] _clean_and_format_value_list: Entrée vide ou invalide, retour d'une chaîne vide.", flush=True)
            return ""

        # La chaîne d'entrée vient de `analyzer.format_genres`, qui respecte déjà l'ordre de pertinence.
        # Ex: "Hip Hop---Instrumental ; Hip Hop---Boom Bap ; Electronic---Dubstep"
        elements_from_analysis = [e.strip() for e in input_string.split(';') if e.strip()]
        print(f"[TagWriter DEBUG] _clean_and_format_value_list: Éléments après division: {elements_from_analysis}", flush=True)

        final_tag_parts_ordered = []
        seen_tags_lower = set() # Pour gérer l'unicité insensible à la casse tout en préservant l'ordre

        for element in elements_from_analysis:
            try:
                current_element_parts_to_add_this_iteration = []
                if '---' in element:
                    # Cas "Genre---SousGenre"
                    main_part_raw, sub_part_raw = [p.strip() for p in element.split('---', 1)]
                    
                    main_part_cased = self._custom_title_case(main_part_raw)
                    if main_part_cased and main_part_cased.lower() not in seen_tags_lower:
                        current_element_parts_to_add_this_iteration.append(main_part_cased)
                        seen_tags_lower.add(main_part_cased.lower())
                    
                    sub_part_cased = self._custom_title_case(sub_part_raw)
                    # Le sous-genre doit être distinct du genre principal pour être ajouté séparément
                    if sub_part_cased and sub_part_cased.lower() not in seen_tags_lower:
                        current_element_parts_to_add_this_iteration.append(sub_part_cased)
                        seen_tags_lower.add(sub_part_cased.lower())
                    
                    print(f"[TagWriter DEBUG] Split '{element}': main_raw='{main_part_raw}', sub_raw='{sub_part_raw}' -> main_cased='{main_part_cased}', sub_cased='{sub_part_cased}'. Parts to add: {current_element_parts_to_add_this_iteration}", flush=True)

                else: # Cas "GenreSeul"
                    single_part_cased = self._custom_title_case(element)
                    if single_part_cased and single_part_cased.lower() not in seen_tags_lower:
                        current_element_parts_to_add_this_iteration.append(single_part_cased)
                        seen_tags_lower.add(single_part_cased.lower())
                    print(f"[TagWriter DEBUG] Single element '{element}': cased='{single_part_cased}'. Parts to add: {current_element_parts_to_add_this_iteration}", flush=True)
                
                final_tag_parts_ordered.extend(current_element_parts_to_add_this_iteration)

            except Exception as e:
                print(f"[TagWriter WARNING] _clean_and_format_value_list: Impossible de traiter l'élément '{element}': {e}", flush=True)
                traceback.print_exc()
        
        # `final_tag_parts_ordered` maintient l'ordre de découverte (basé sur analysis_results)
        # et l'unicité (grâce à seen_tags_lower).
        final_string = " ; ".join(final_tag_parts_ordered)
        print(f"[TagWriter INFO] _clean_and_format_value_list: Sortie nettoyée: '{final_string}'", flush=True)
        return final_string