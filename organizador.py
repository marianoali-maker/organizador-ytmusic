import json
import os
import random
import re
import time
import requests
import musicbrainzngs
from ytmusicapi import OAuthCredentials, YTMusic, setup_oauth

# ==========================================
# CONFIGURACIÓN
# ==========================================
LASTFM_API_KEY = os.getenv(
    'LASTFM_API_KEY', '')
LASTFM_API_URL = 'https://ws.audioscrobbler.com/2.0/'
AUTH_FILES = ['browser.json', 'headers_auth.json', 'oauth.json']
CACHE_FILE = 'genre_cache.json'

LASTFM_SLEEP = 0.25
YT_BATCH_SIZE = 50
YT_BATCH_SLEEP = 1.0
MIN_TRACKS_PER_GENRE = 3
CREATE_UNCLASSIFIED_PLAYLIST = False
MIX_PLAYLIST_TITLE = 'Mix por género'

MUSICBRAINZ_CONTACT = os.getenv(
    "MUSICBRAINZ_CONTACT_EMAIL",
    "https://github.com/marianoali-maker/organizador-ytmusic",
)
musicbrainzngs.set_useragent(
    "OrganizadorYTMusic", "1.0", MUSICBRAINZ_CONTACT)
musicbrainzngs.set_rate_limit(1.0)
MUSICBRAINZ_ARTIST_CACHE = {}

# Mapeo directo por Artistas (Máxima prioridad)
ARTIST_MAP = {
    # Cumbia y Tropical
    'los angeles azules': 'Cumbia',
    'koli arce': 'Cumbia',
    'malagata': 'Cumbia',
    'aclamado amistad': 'Cumbia',
    'los del maranaho': 'Cumbia',
    'los dora 2': 'Cumbia',
    'grupo trinidad': 'Cumbia',
    'siete lunas': 'Cumbia',
    'media naranja': 'Cumbia',
    'la nueva luna': 'Cumbia',
    'los del fuego': 'Cumbia',
    'el combo loco': 'Cumbia',
    'tinta roja': 'Cumbia',
    'santa marta': 'Cumbia',
    'santamarta': 'Cumbia',
    'grupo sombras': 'Cumbia',
    'sombras': 'Cumbia',
    'amar azul': 'Cumbia',
    'rafaga': 'Cumbia',
    'la cumbia': 'Cumbia',
    'tamba': 'Cumbia',
    'los palmeras': 'Cumbia',
    'damas gratis': 'Cumbia',
    'ke personajes': 'Cumbia',
    'gilda': 'Cumbia',
    'yerba brava': 'Cumbia',
    'mala fama': 'Cumbia',
    'la champions liga': 'Cumbia',
    'grupo karicia': 'Cumbia',
    'karicia': 'Cumbia',
    'red': 'Cumbia',
    'grupo red': 'Cumbia',
    'green': 'Cumbia',
    'grupo green': 'Cumbia',
    'pibes chorros': 'Cumbia',
    'daniel cardozo': 'Cumbia',

    # Cuarteto
    'la k\'onga': 'Cuarteto',
    'la konga': 'Cuarteto',
    'q\' lokura': 'Cuarteto',
    'q lokura': 'Cuarteto',
    'ulises bueno': 'Cuarteto',
    'rodrigo': 'Cuarteto',
    'walter olmos': 'Cuarteto',
    'la barra': 'Cuarteto',
    'tru-la-la': 'Cuarteto',
    'trulala': 'Cuarteto',

    # House / Afro House / Electrónica
    'dj andres cruz': 'Deep House',
    'yamore': 'Afro House',
    'salif keita': 'Afro House',
    'cesaria evora': 'Afro House',
    'francis mercier': 'Afro House',
    'wakyin': 'Afro House',
    'zerb': 'Afro House',
    'nitefreak': 'Afro House',
    'moblack': 'Afro House',
    'pauza': 'Afro House',
    'samuel cosmic': 'Afro House',
    'idd aziz': 'Afro House',
    'faul & wad': 'Afro House',
    'black coffee': 'Afro House',
    'keinemusik': 'Afro House',
    'adam port': 'Afro House',
    'rampa': 'Afro House',
    'f4st': 'Afro House',
    'cornetto': 'Afro House',
}

# Géneros ordenados por especificidad (los más específicos van arriba)
GENRE_PRIORITY = [
    # Géneros específicos (Prioridad 1)
    ('afro house', 'Afro House'),
    ('afrohouse', 'Afro House'),
    ('organic house', 'Organic House'),
    ('melodic house', 'Melodic House'),
    ('progressive house', 'Progressive House'),
    ('deep house', 'Deep House'),
    ('tech house', 'Tech House'),
    ('cumbia villera', 'Cumbia'),
    ('cumbia', 'Cumbia'),
    ('cuarteto', 'Cuarteto'),
    ('bossa nova', 'Bossa Nova'),
    ('bossa', 'Bossa Nova'),
    ('pagode', 'Samba'),
    ('samba', 'Samba'),
    ('mpb', 'Música Brasilera'),
    ('drum and bass', 'Drum & Bass'),
    ('drum & bass', 'Drum & Bass'),
    ('dnb', 'Drum & Bass'),
    ('heavy metal', 'Metal'),
    ('hard rock', 'Hard Rock'),
    ('indie rock', 'Indie Rock'),
    ('synthpop', 'Synthpop'),
    ('banda sonora', 'Bandas Sonoras'),
    ('soundtrack', 'Bandas Sonoras'),
    # Subgéneros específicos
    ('k-pop', 'K-Pop'),
    ('j-pop', 'J-Pop'),
    ('k-rap', 'Hip-Hop'),

    # Géneros intermedios (Prioridad 2)
    ('techno', 'Techno'),
    ('trance', 'Trance'),
    ('minimal', 'Minimal'),
    ('dubstep', 'Dubstep'),
    ('ambient', 'Ambient'),
    ('downtempo', 'Downtempo'),
    ('house', 'House'),
    ('edm', 'EDM'),
    ('electronica', 'Electrónica'),
    ('electronic', 'Electrónica'),
    ('reggaeton', 'Reggaetón'),
    ('reggaetón', 'Reggaetón'),
    ('bachata', 'Bachata'),
    ('salsa', 'Salsa'),
    ('merengue', 'Merengue'),
    ('bolero', 'Bolero'),
    ('tango', 'Tango'),
    ('milonga', 'Tango'),
    ('folklore', 'Folklore'),
    ('folclore', 'Folklore'),
    ('metal', 'Metal'),
    ('punk', 'Punk'),
    ('indie', 'Indie'),
    ('hip hop', 'Hip-Hop'),
    ('hip-hop', 'Hip-Hop'),
    ('rap', 'Hip-Hop'),
    ('trap', 'Trap'),
    ('r&b', 'R&B'),
    ('rnb', 'R&B'),
    ('soul', 'Soul'),
    ('funk', 'Funk'),
    ('jazz', 'Jazz'),
    ('blues', 'Blues'),
    ('reggae', 'Reggae'),
    ('ska', 'Ska'),
    ('folk', 'Folk'),
    ('country', 'Country'),
    ('classical', 'Clásica'),
    ('clasica', 'Clásica'),
    ('opera', 'Ópera'),
    ('rock', 'Rock'),
    ('pop', 'Pop'),

    # Géneros genéricos (Última opción / Fallback)
    ('latino', 'Latin'),
    ('latin', 'Latin'),
]

BLACKLIST_TAGS = {
    'seen live', 'favorites', 'favourite', 'favorite', 'love', 'loved',
    'awesome', 'amazing', 'cool', 'good', 'great', 'beautiful', 'best',
    'lastfm', 'last.fm', 'youtube', 'youtube music',
    'my music', 'my favorites', 'chill', 'chillout', 'relax', 'mellow',
    'party', 'dance', 'happy', 'sad', 'summer', 'winter', 'night',
    'male vocalists', 'female vocalists', 'vocal', 'instrumental',
    '00s', '10s', '20s', '80s', '90s', '70s', '60s', '50s',
    'american', 'british', 'argentina', 'argentinian', 'spanish',
    'español', 'ingles', 'english', 'cover', 'covers',
}


def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_cache(cache):
    try:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[Caché] No pude guardar: {e}")


class LastFMClient:
    def __init__(self, api_key, api_url):
        self.api_key = api_key
        self.api_url = api_url
        self.last_call = 0.0

    def _throttle(self):
        elapsed = time.time() - self.last_call
        if elapsed < LASTFM_SLEEP:
            time.sleep(LASTFM_SLEEP - elapsed)
        self.last_call = time.time()

    def get(self, params, max_retries=3):
        if not self.api_key:
            return {}
        params = {**params, 'api_key': self.api_key, 'format': 'json'}
        for _ in range(max_retries):
            self._throttle()
            try:
                r = requests.get(self.api_url, params=params, timeout=10)
                if r.status_code == 429:
                    time.sleep(5)
                    continue
                r.raise_for_status()
                return r.json()
            except Exception:
                pass
        return {}

    def extract_genre_from_tags(self, tags):
        if not tags:
            return None
        if isinstance(tags, dict):
            tags = [tags]

        valid_tags = []
        for tag in tags:
            name = (tag.get('name') or '').lower().strip()
            if name and name not in BLACKLIST_TAGS:
                valid_tags.append(name)

        all_tags_text = " ".join(valid_tags)
        if not all_tags_text:
            return None

        for keyword, canonical in GENRE_PRIORITY:
            if re.search(r'\b' + re.escape(keyword) + r'\b', all_tags_text):
                return canonical
        return None

    def lookup_track(self, artist, track):
        data = self.get({
            'method': 'track.getInfo',
            'artist': artist,
            'track': track,
            'autocorrect': 0,
        })
        tags = data.get('track', {}).get('toptags', {}).get('tag', [])
        return self.extract_genre_from_tags(tags)

    def lookup_artist(self, artist):
        data = self.get({
            'method': 'artist.getInfo',
            'artist': artist,
            'autocorrect': 0,
        })
        tags = data.get('artist', {}).get('tags', {}).get('tag', [])
        return self.extract_genre_from_tags(tags)


def lookup_musicbrainz_genre(artist):
    """Consulta las etiquetas del artista en MusicBrainz como respaldo."""
    if not artist:
        return None
    artist_key = artist.casefold()
    if artist_key in MUSICBRAINZ_ARTIST_CACHE:
        return MUSICBRAINZ_ARTIST_CACHE[artist_key]

    clean_artist = re.sub(r"[\(\[].*?[\)\]]", "", artist).strip()
    if not clean_artist:
        return None

    try:
        resultado = musicbrainzngs.search_artists(
            artist=clean_artist, limit=5)
    except (musicbrainzngs.WebServiceError, musicbrainzngs.NetworkError,
            musicbrainzngs.UsageError) as e:
        print(f"[MusicBrainz] Error consultando '{artist}': {e}")
        MUSICBRAINZ_ARTIST_CACHE[artist_key] = None
        return None

    items = resultado.get('artist-list', [])
    genre = None
    if items:
        normalized_artist = re.sub(r"\W+", "", clean_artist.casefold())
        matching_artist = next(
            (
                item for item in items
                if re.sub(r"\W+", "", (item.get("name") or "").casefold())
                == normalized_artist
            ),
            items[0],
        )
        tags = matching_artist.get('tag-list') or []
        tag_names = [
            tag.get('name', '').strip().lower()
            for tag in tags
            if isinstance(tag, dict) and tag.get('name')
        ]
        all_tags_text = " ".join(tag_names)
        for keyword, canonical in GENRE_PRIORITY:
            if re.search(r'\b' + re.escape(keyword) + r'\b', all_tags_text):
                genre = canonical
                break
        if not genre and tag_names:
            genre = tag_names[0].title()

    MUSICBRAINZ_ARTIST_CACHE[artist_key] = genre
    return genre


def clean_title(title):
    t = re.sub(
        r'\s*[\(\[][^\)\]]*(official|lyric|audio|video|hd|hq|remaster|'
        r'remix|live|visualizer|mv|m/v|4k)[^\)\]]*[\)\]]',
        '', title, flags=re.I
    )
    t = re.sub(
        r'\s*[\(\[]?\s*(feat\.?|ft\.?|featuring|con)\s+[^\)\]]+[\)\]]?',
        '', t, flags=re.I
    )
    return t.strip(' -–—')


def classify_local(artist, title, album):
    artist_lower = artist.lower()

    # 1. Búsqueda por artista conocido
    for art_key, canonical in ARTIST_MAP.items():
        if art_key in artist_lower:
            return canonical

    # 2. Búsqueda por palabra clave en título / álbum / artista
    combined_text = f"{artist} {title} {album}".lower()
    for keyword, canonical in GENRE_PRIORITY:
        if re.search(r'\b' + re.escape(keyword) + r'\b', combined_text):
            return canonical
    return None


def classify(lastfm, artist, track, album, cache):
    key = f"{artist.lower()}||{track.lower()}"

    manual_genre = cache.get(key)
    if isinstance(manual_genre, str) and manual_genre.startswith('manual::'):
        return manual_genre.removeprefix('manual::')

    # 1. Reglas locales y mapa directo de artistas tienen máxima prioridad
    genre = classify_local(artist, track, album)
    if genre:
        cache[key] = genre
        return genre

    # 2. Si ya está en caché y no es una etiqueta problemática/genérica
    if key in cache and cache[key] not in ['Metal', 'Latin', 'Sin clasificar']:
        return cache[key]

    # 3. Consulta a Last.fm
    genre = lastfm.lookup_track(artist, track)
    if not genre:
        genre = lastfm.lookup_artist(artist)

    # 4. Si Last.fm falla, consultar MusicBrainz como respaldo
    if not genre:
        genre = lookup_musicbrainz_genre(artist)

    if not genre:
        genre = 'Sin clasificar'

    cache[key] = genre
    return genre


def authenticate():
    client_id = os.getenv('YT_CLIENT_ID', '')
    client_secret = os.getenv('YT_CLIENT_SECRET', '')

    # 1. Buscar archivos de autenticación existentes
    for auth_file in AUTH_FILES:
        if os.path.exists(auth_file):
            try:
                if auth_file == 'oauth.json':
                    if not client_id or not client_secret:
                        continue
                    return YTMusic(
                        auth_file,
                        oauth_credentials=OAuthCredentials(
                            client_id, client_secret),
                    )
                return YTMusic(auth_file)
            except Exception:
                pass

    # 2. Si no hay autenticación previa, guiar al usuario
    print("\n" + "=" * 50)
    print("  PRIMERA CONFIGURACIÓN DE YOUTUBE MUSIC")
    print("=" * 50)
    print("No se encontró una sesión activa.")
    if not client_id or not client_secret:
        print("Definí YT_CLIENT_ID y YT_CLIENT_SECRET para usar OAuth.")
        return None
    print("Se generará un código para vincular la cuenta de YouTube Music.\n")
    try:
        setup_oauth(client_id, client_secret, filepath="oauth.json")
        print("\n¡Cuenta vinculada con éxito!\n")
        return YTMusic(
            "oauth.json",
            oauth_credentials=OAuthCredentials(client_id, client_secret),
        )
    except Exception as e:
        print(f"\nError al autenticar: {e}")
        return None


def fetch_existing_playlist_tracks(yt, playlist_id):
    try:
        pl = yt.get_playlist(playlist_id, limit=None)
        return {t['videoId'] for t in pl.get('tracks', []) if t.get('videoId')}
    except Exception:
        return set()


def get_or_create_playlist(yt, title, existing_playlists):
    if title in existing_playlists:
        return existing_playlists[title]
    print(f"  + Creando playlist: {title}")
    pl_id = yt.create_playlist(
        title,
        f"Auto-generada por género musical ({title})",
        privacy_status="PRIVATE",
    )
    existing_playlists[title] = pl_id
    return pl_id


def create_mix_playlist(yt, genre_names, existing_playlists):
    mix_ids = []
    seen_ids = set()
    for genre in genre_names:
        playlist_id = existing_playlists.get(genre)
        if not playlist_id:
            continue
        try:
            playlist = yt.get_playlist(playlist_id, limit=None)
        except Exception as e:
            print(f"  Error leyendo playlist '{genre}' para el mix: {e}")
            continue
        for track in playlist.get('tracks', [])[:3]:
            video_id = track.get('videoId')
            if video_id and video_id not in seen_ids:
                seen_ids.add(video_id)
                mix_ids.append(video_id)

    if not mix_ids:
        print("No hay canciones disponibles para crear el mix.")
        return

    random.shuffle(mix_ids)
    mix_id = get_or_create_playlist(yt, MIX_PLAYLIST_TITLE, existing_playlists)
    current_ids = fetch_existing_playlist_tracks(yt, mix_id)
    new_ids = [video_id for video_id in mix_ids if video_id not in current_ids]
    if not new_ids:
        print(f"'{MIX_PLAYLIST_TITLE}': sin canciones nuevas.")
        return

    print(f"'{MIX_PLAYLIST_TITLE}': agregando {len(new_ids)} canciones...")
    for start in range(0, len(new_ids), YT_BATCH_SIZE):
        batch = new_ids[start:start + YT_BATCH_SIZE]
        try:
            result = yt.add_playlist_items(mix_id, batch)
        except Exception as e:
            print(f"  Error agregando canciones al mix: {e}")
            continue
        if not isinstance(result, dict) or 'SUCCEEDED' not in result.get('status', ''):
            print(f"  YouTube no confirmó la adición al mix: {result}")
        time.sleep(YT_BATCH_SLEEP)


def process_library(yt, lastfm):
    cache = load_cache()

    print("Obteniendo canciones de 'Música que me gusta' y de la biblioteca...")

    liked_data = yt.get_liked_songs(limit=None)
    liked_tracks = liked_data.get(
        'tracks', []) if isinstance(liked_data, dict) else []

    library_tracks = yt.get_library_songs(limit=None) or []

    seen_ids = set()
    tracks = []
    for track in liked_tracks + library_tracks:
        vid = track.get('videoId')
        if vid and vid not in seen_ids:
            seen_ids.add(vid)
            tracks.append(track)
    liked_ids = {
        track.get('videoId') for track in liked_tracks if track.get('videoId')
    }

    print(f"{len(tracks)} canciones únicas encontradas.")
    if not tracks:
        return

    genre_map = {}
    manual_genre_ids = set()
    for i, track in enumerate(tracks, 1):
        title = track.get('title') or ''
        artists = track.get('artists') or []
        artist = artists[0]['name'] if artists else ''
        album_obj = track.get('album') or {}
        album = album_obj.get('name') if isinstance(album_obj, dict) else ''
        vid = track.get('videoId')

        if not vid or not title or not artist:
            continue

        genre = classify(lastfm, artist, clean_title(title), album, cache)
        if genre == 'Sin clasificar' and vid in liked_ids:
            print(
                f"\nNo se detectó el género de '{artist} - {title}'. "
                "El like se conservará hasta que se asigne un género.")
            manual_genre = input(
                "Ingresá el género (ENTER para dejarlo pendiente): ").strip()
            if manual_genre and manual_genre.casefold() != 'sin clasificar':
                genre = manual_genre
                cache[f"{artist.lower()}||{clean_title(title).lower()}"] = (
                    f"manual::{genre}")
                manual_genre_ids.add(vid)
                save_cache(cache)
        genre_map.setdefault(genre, []).append(vid)

        if i % 25 == 0 or i == len(tracks):
            print(f"  Clasificadas {i}/{len(tracks)}...")
            save_cache(cache)

    print("\nClasificación completada.\n")

    print("Resumen por género:")
    for g, ids in sorted(genre_map.items(), key=lambda x: -len(x[1])):
        print(f"  • {g:<20} {len(ids)} canciones")
    print()

    playlists = yt.get_library_playlists()
    existing = {pl['title']: pl['playlistId'] for pl in playlists}
    placed_ids = set()
    included_genres = []

    for genre, ids in sorted(genre_map.items(), key=lambda x: -len(x[1])):
        if genre == 'Sin clasificar' and not CREATE_UNCLASSIFIED_PLAYLIST:
            print(f"'{genre}': se conserva el like hasta asignar un género.")
            continue

        manually_assigned = set(ids) & manual_genre_ids
        if len(ids) < MIN_TRACKS_PER_GENRE and not manually_assigned:
            print(
                f"'{genre}': omitido ({len(ids)} temas, mínimo requerido: {MIN_TRACKS_PER_GENRE}).")
            continue

        pl_id = get_or_create_playlist(yt, genre, existing)
        current = fetch_existing_playlist_tracks(yt, pl_id)
        placed_ids.update(set(ids) & current)
        new_ids = [v for v in ids if v not in current]

        if not new_ids:
            print(f"'{genre}': sin canciones nuevas.")
            included_genres.append(genre)
            continue

        print(f"'{genre}': agregando {len(new_ids)} canciones...")
        genre_added = False
        for i in range(0, len(new_ids), YT_BATCH_SIZE):
            batch = new_ids[i:i + YT_BATCH_SIZE]
            try:
                result = yt.add_playlist_items(pl_id, batch)
            except Exception as e:
                print(f"  Error agregando lote: {e}")
                continue
            if isinstance(result, dict) and 'SUCCEEDED' in result.get('status', ''):
                placed_ids.update(batch)
                genre_added = True
            else:
                print(f"  YouTube no confirmó el lote: {result}")
            time.sleep(YT_BATCH_SLEEP)
        if genre_added or set(ids).issubset(placed_ids):
            included_genres.append(genre)

    create_mix_playlist(yt, included_genres, existing)

    liked_to_remove = liked_ids & placed_ids
    if liked_to_remove:
        print(f"\nQuitando likes de {len(liked_to_remove)} canciones ya guardadas por género...")
        for video_id in liked_to_remove:
            try:
                yt.rate_song(video_id, 'INDIFFERENT')
            except Exception as e:
                print(f"  No se pudo quitar el like de {video_id}: {e}")
    unclassified_liked = liked_ids - placed_ids
    if unclassified_liked:
        print(
            f"Se conservaron {len(unclassified_liked)} likes porque esas canciones "
            "no quedaron agregadas a una playlist de género.")

    print("\nProceso finalizado.")


if __name__ == "__main__":
    yt_api = authenticate()
    if yt_api:
        lastfm_client = LastFMClient(LASTFM_API_KEY, LASTFM_API_URL)
        try:
            process_library(yt_api, lastfm_client)
        except KeyboardInterrupt:
            print("\nInterrumpido por el usuario.")

    input("\nPresiona ENTER para cerrar...")
