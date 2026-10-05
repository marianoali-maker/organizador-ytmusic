import json
import os
import re
import time
import requests
import streamlit as st
from ytmusicapi import YTMusic

# ==========================================
# CONFIGURACIÓN DE LA PÁGINA
# ==========================================
st.set_page_config(
    page_title="Organizador de YouTube Music",
    page_icon="🎵",
    layout="centered"
)

LASTFM_API_KEY = os.getenv(
    'LASTFM_API_KEY', 'be13c0c8fe2692ce5eb11636925dd592')
LASTFM_API_URL = 'http://ws.audioscrobbler.com/2.0/'

LASTFM_SLEEP = 0.25
YT_BATCH_SIZE = 50
YT_BATCH_SLEEP = 1.0
MIN_TRACKS_PER_GENRE = 3

ARTIST_MAP = {
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
    'la k\'onga': 'Cuarteto',
    'la konga': 'Cuarteto',
    'q\' lokura': 'Cuarteto',
    'q lokura': 'Cuarteto',
    'ulises bueno': 'Cuarteto',
    'yamore': 'Afro House',
    'salif keita': 'Afro House',
    'cesaria evora': 'Afro House',
    'francis mercier': 'Afro House',
    'wakyin': 'Afro House',
    'zerb': 'Afro House',
    'nitefreak': 'Afro House',
    'moblack': 'Afro House',
    'pauza': 'Afro House',
}

GENRE_PRIORITY = [
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
    ('heavy metal', 'Metal'),
    ('hard rock', 'Hard Rock'),
    ('house', 'House'),
    ('techno', 'Techno'),
    ('trance', 'Trance'),
    ('reggaeton', 'Reggaetón'),
    ('rock', 'Rock'),
    ('pop', 'Pop'),
    ('latino', 'Latin'),
    ('latin', 'Latin'),
]

# ==========================================
# LÓGICA DE CLASIFICACIÓN
# ==========================================


def clean_title(title):
    t = re.sub(r'\s*[\(\[][^\)\]]*(official|lyric|audio|video|hd|hq|remaster|remix|live)[\)\]]',
               '', title, flags=re.I)
    t = re.sub(
        r'\s*[\(\[]?\s*(feat\.?|ft\.?|featuring|con)\s+[^\)\]]+[\)\]]?', '', t, flags=re.I)
    return t.strip(' -–—')


def classify_local(artist, title, album):
    artist_lower = artist.lower()
    for art_key, canonical in ARTIST_MAP.items():
        if art_key in artist_lower:
            return canonical
    combined_text = f"{artist} {title} {album}".lower()
    for keyword, canonical in GENRE_PRIORITY:
        if re.search(r'\b' + re.escape(keyword) + r'\b', combined_text):
            return canonical
    return None


def lookup_lastfm(artist, track):
    try:
        params = {'method': 'track.getInfo', 'artist': artist, 'track': track,
                  'api_key': LASTFM_API_KEY, 'format': 'json', 'autocorrect': 0}
        r = requests.get(LASTFM_API_URL, params=params, timeout=5)
        if r.status_code == 200:
            data = r.json()
            tags = data.get('track', {}).get('toptags', {}).get('tag', [])
            if isinstance(tags, dict):
                tags = [tags]
            tag_names = " ".join([(t.get('name') or '').lower() for t in tags])
            for keyword, canonical in GENRE_PRIORITY:
                if re.search(r'\b' + re.escape(keyword) + r'\b', tag_names):
                    return canonical
    except Exception:
        pass
    return 'Sin clasificar'


# ==========================================
# INTERFAZ GRÁFICA EN STREAMLIT
# ==========================================
st.title("🎵 Organizador de YouTube Music")
st.write("Organizá tus canciones en playlists privadas clasificadas por género musical.")

# Estado de autenticación por usuario
if "yt_credentials" not in st.session_state:
    st.session_state["yt_credentials"] = None

if not st.session_state["yt_credentials"]:
    st.subheader("1. Conectar tu cuenta de YouTube Music")
    st.info("Para vincular tu cuenta, necesitás copiar tu credencial o generar un inicio de sesión OAuth.")

    auth_code_input = st.text_area(
        "Pegá el contenido de tu archivo oauth.json o headers_auth.json aquí:", height=150)
    if st.button("Iniciar Sesión"):
        try:
            creds = json.loads(auth_code_input)
            yt = YTMusic(json.dumps(creds))
            st.session_state["yt_credentials"] = json.dumps(creds)
            st.success("¡Cuenta autenticada con éxito!")
            st.rerun()
        except Exception as e:
            st.error(f"Error al autenticar credenciales: {e}")
else:
    yt = YTMusic(st.session_state["yt_credentials"])
    st.success("✓ Cuenta de YouTube Music conectada.")

    if st.button("Cerrar Sesión"):
        st.session_state["yt_credentials"] = None
        st.rerun()

    st.subheader("2. Comenzar Organización")
    if st.button("🚀 Organizar mi Biblioteca y Me Gusta", type="primary"):
        progress_bar = st.progress(0)
        status_text = st.empty()

        status_text.text("Obteniendo canciones de YouTube Music...")
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

        st.write(f"**Canciones encontradas:** {len(tracks)}")

        genre_map = {}
        for i, track in enumerate(tracks, 1):
            title = track.get('title') or ''
            artists = track.get('artists') or []
            artist = artists[0]['name'] if artists else ''
            album_obj = track.get('album') or {}
            album = album_obj.get('name') if isinstance(
                album_obj, dict) else ''
            vid = track.get('videoId')

            if not vid or not title or not artist:
                continue

            clean_t = clean_title(title)
            genre = classify_local(artist, clean_t, album)
            if not genre:
                genre = lookup_lastfm(artist, clean_t)
                time.sleep(LASTFM_SLEEP)

            genre_map.setdefault(genre, []).append(vid)

            percent = int((i / len(tracks)) * 100)
            progress_bar.progress(percent)
            status_text.text(
                f"Clasificando: {i}/{len(tracks)} - {title} ({genre})")

        status_text.text("Creando playlists en tu cuenta...")

        playlists = yt.get_library_playlists()
        existing = {pl['title']: pl['playlistId'] for pl in playlists}

        results = []
        for genre, ids in genre_map.items():
            if genre == 'Sin clasificar' or len(ids) < MIN_TRACKS_PER_GENRE:
                continue

            if genre in existing:
                pl_id = existing[genre]
            else:
                pl_id = yt.create_playlist(
                    genre, f"Auto-generada ({genre})", privacy_status="PRIVATE")
                existing[genre] = pl_id

            pl_data = yt.get_playlist(pl_id, limit=None)
            current_ids = {t['videoId']
                           for t in pl_data.get('tracks', []) if t.get('videoId')}
            new_ids = [v for v in ids if v not in current_ids]

            if new_ids:
                for j in range(0, len(new_ids), YT_BATCH_SIZE):
                    yt.add_playlist_items(pl_id, new_ids[j:j + YT_BATCH_SIZE])
                    time.sleep(YT_BATCH_SLEEP)

            results.append({"Género": genre, "Canciones": len(ids)})

        st.success("🎉 ¡Organización completada con éxito!")
        st.table(results)