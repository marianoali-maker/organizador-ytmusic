import json
import os
import re
import time
import requests
from ytmusicapi import YTMusic

# ==========================================
# CONFIGURACIÓN
# ==========================================
LASTFM_API_KEY = os.getenv(
    'LASTFM_API_KEY', 'be13c0c8fe2692ce5eb11636925dd592')
LASTFM_API_URL = 'http://ws.audioscrobbler.com/2.0/'
AUTH_FILES = ['browser.json', 'headers_auth.json', 'oauth.json']
CACHE_FILE = 'genre_cache.json'

LASTFM_SLEEP = 0.25
YT_BATCH_SIZE = 50
YT_BATCH_SLEEP = 1.0
MIN_TRACKS_PER_GENRE = 3
CREATE_UNCLASSIFIED_PLAYLIST = False

# Mapeo directo por Artistas (Máxima prioridad)
ARTIST_MAP = {
    # Cumbia y Tropical
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
    'spotify', 'lastfm', 'last.fm', 'youtube', 'youtube music',
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
        params = {**params, 'api_key': self.api_key, 'format': 'json'}
        for attempt in range(max_retries):
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

    # 1. Reglas locales y mapa directo de artistas tienen máxima prioridad
    genre = classify_local(artist, track, album)
    if genre:
        cache[key] = genre
        return genre

    # 2. Si ya está en caché y no es una etiqueta problemática/genérica
    if key in cache and cache[key] not in ['Metal', 'Latin', 'Sin clasificar']:
        return cache[key]

    # 3. Consulta a Last.fm con filtrado estricto por prioridad de etiquetas
    genre = lastfm.lookup_track(artist, track)
    if not genre:
        genre = lastfm.lookup_artist(artist)
    if not genre:
        genre = 'Sin clasificar'

    cache[key] = genre
    return genre


def authenticate():
    # 1. Buscar archivos de autenticación existentes
    for auth_file in AUTH_FILES:
        if os.path.exists(auth_file):
            try:
                return YTMusic(auth_file)
            except Exception:
                pass

    # 2. Si no hay autenticación previa, guiar al usuario
    print("\n" + "=" * 50)
    print("  PRIMERA CONFIGURACIÓN DE YOUTUBE MUSIC")
    print("=" * 50)
    print("No se encontró una sesión activa.")
    print("Se generará un código para vincular la cuenta de YouTube Music.\n")
    try:
        YTMusic.setup_oauth(filepath="oauth.json")
        print("\n¡Cuenta vinculada con éxito!\n")
        return YTMusic("oauth.json")
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

    print(f"{len(tracks)} canciones únicas encontradas.")
    if not tracks:
        return

    genre_map = {}
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

    for genre, ids in sorted(genre_map.items(), key=lambda x: -len(x[1])):
        if genre == 'Sin clasificar' and not CREATE_UNCLASSIFIED_PLAYLIST:
            continue

        if len(ids) < MIN_TRACKS_PER_GENRE:
            print(
                f"'{genre}': omitido ({len(ids)} temas, mínimo requerido: {MIN_TRACKS_PER_GENRE}).")
            continue

        pl_id = get_or_create_playlist(yt, genre, existing)
        current = fetch_existing_playlist_tracks(yt, pl_id)
        new_ids = [v for v in ids if v not in current]

        if not new_ids:
            print(f"'{genre}': sin canciones nuevas.")
            continue

        print(f"'{genre}': agregando {len(new_ids)} canciones...")
        for i in range(0, len(new_ids), YT_BATCH_SIZE):
            batch = new_ids[i:i + YT_BATCH_SIZE]
            try:
                yt.add_playlist_items(pl_id, batch)
            except Exception as e:
                print(f"  Error agregando lote: {e}")
            time.sleep(YT_BATCH_SLEEP)

    print("\nProceso finalizado con éxito.")


if __name__ == "__main__":
    yt_api = authenticate()
    if yt_api:
        lastfm_client = LastFMClient(LASTFM_API_KEY, LASTFM_API_URL)
        try:
            process_library(yt_api, lastfm_client)
        except KeyboardInterrupt:
            print("\nInterrumpido por el usuario.")

    input("\nPresiona ENTER para cerrar...")
