import json
import os
import re
import time
import requests
import streamlit as st
from ytmusicapi import YTMusic

# ==========================================
# CONFIGURACIÓN DE PÁGINA Y ESTILOS YOUTUBE MUSIC
# ==========================================
st.set_page_config(
    page_title="Organizador de YouTube Music",
    page_icon="🔴",
    layout="centered"
)

# Inyección de CSS personalizado (Estilo YouTube Music Dark)
st.markdown("""
<style>
    /* Fondo general */
    .stApp {
        background-color: #0F0F0F !important;
        color: #F1F1F1 !important;
        font-family: 'Roboto', sans-serif;
    }
    
    /* Encabezados */
    h1, h2, h3, h4 {
        color: #FFFFFF !important;
        font-weight: 700 !important;
    }
    
    /* Botones primarios estilo YouTube (Rojo vibrante) */
    .stButton > button {
        background-color: #FF0000 !important;
        color: #FFFFFF !important;
        border-radius: 24px !important;
        font-weight: bold !important;
        border: none !important;
        padding: 0.6rem 1.8rem !important;
        font-size: 1rem !important;
        box-shadow: 0 4px 12px rgba(255, 0, 0, 0.3);
        transition: all 0.2s ease-in-out;
    }
    
    .stButton > button:hover {
        background-color: #CC0000 !important;
        transform: scale(1.03);
    }
    
    /* Tarjetas contenedoras de información */
    .yt-card {
        background-color: #212121;
        border: 1px solid #383838;
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
    }
    
    /* Caja resaltada para el código de inicio de sesión */
    .code-display {
        background-color: #000000;
        color: #FF0000;
        font-size: 2.2rem;
        font-weight: 900;
        letter-spacing: 6px;
        padding: 1rem;
        border-radius: 12px;
        border: 2px dashed #FF0000;
        text-align: center;
        margin: 1rem 0;
    }

    /* Tablas y métricas */
    div[data-testid="stMetricValue"] {
        color: #FF0000 !important;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# PARÁMETROS DE OAUTH Y LAST.FM
# ==========================================
DEVICE_CODE_URL = "https://oauth2.googleapis.com/device/code"
TOKEN_URL = "https://oauth2.googleapis.com/token"
SCOPE = "https://www.googleapis.com/auth/youtube"

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
# FUNCIONES AUXILIARES DE OAUTH
# ==========================================


def request_device_code(client_id):
    res = requests.post(DEVICE_CODE_URL, data={
                        'client_id': client_id, 'scope': SCOPE})
    try:
        return res.json()
    except Exception:
        return {"error": "http_error", "error_description": f"HTTP {res.status_code}: {res.text}"}


def poll_device_token(client_id, client_secret, device_code):
    res = requests.post(TOKEN_URL, data={
        'client_id': client_id,
        'client_secret': client_secret,
        'device_code': device_code,
        'grant_type': 'urn:ietf:params:oauth:grant-type:device_code'
    })
    try:
        return res.json()
    except Exception:
        return {"error": "http_error", "error_description": f"HTTP {res.status_code}: {res.text}"}

# ==========================================
# LÓGICA DE CLASIFICACIÓN
# ==========================================


def clean_title(title):
    t = re.sub(r'\s*[\(\[][^\)\]]*(official\vert{}lyric\vert{}audio\vert{}video\vert{}hd\vert{}hq\vert{}remaster\vert{}remix\vert{}live)[\)\]]', '', title, flags=re.I)
    t = re.sub(
        r'\s*[\(\[]?\s*(feat\.?\vert{}ft\.?\vert{}featuring\vert{}con)\s+[^\)\]]+[\)\]]?', '', t, flags=re.I)
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
# INTERFAZ PRINCIPAL DE LA APP
# ==========================================
st.markdown("""
<div style="display: flex; align-items: center; gap: 16px; margin-bottom: 8px;">
    <img src="https://upload.wikimedia.org/wikipedia/commons/6/6a/Youtube_Music_icon.svg" width="48" height="48" alt="YouTube Music Logo"/>
    <h1 style="margin: 0; font-size: 2.2rem; line-height: 1.2;">YouTube Music Organizer</h1>
</div>
""", unsafe_allow_html=True)

st.write("Clasificá automáticamente tu biblioteca y 'Me gusta' en playlists privadas ordenadas por género musical.")
st.markdown("---")

if "yt_credentials" not in st.session_state:
    st.session_state["yt_credentials"] = None
if "device_info" not in st.session_state:
    st.session_state["device_info"] = None

# ------------------------------------------
# PASO 1: CONEXIÓN CON GOOGLE / YOUTUBE MUSIC
# ------------------------------------------
if not st.session_state["yt_credentials"]:
    st.markdown("### 🔒 Conectar tu cuenta de YouTube Music")

    auth_method = st.radio(
        "Seleccioná el método de autenticación:",
        ["OAuth Google (Código de Dispositivo)",
         "Headers / Cookie del Navegador"],
        horizontal=True
    )

    if auth_method == "OAuth Google (Código de Dispositivo)":
        st.caption(
            "Requiere un Client ID de Google Cloud Console tipo 'TVs and Limited Input devices'.")

        col_c1, col_c2 = st.columns(2)
        with col_c1:
            client_id_input = st.text_input("Client ID", value=os.getenv(
                "YT_CLIENT_ID", ""), type="password", help="Obtenido en Google Cloud Console")
        with col_c2:
            client_secret_input = st.text_input("Client Secret", value=os.getenv(
                "YT_CLIENT_SECRET", ""), type="password", help="Obtenido en Google Cloud Console")

        if not st.session_state["device_info"]:
            if st.button("🔗 Generar Código de Conexión"):
                if not client_id_input:
                    st.error(
                        "Por favor ingresá tu Client ID de Google Cloud Console.")
                else:
                    info = request_device_code(client_id_input)
                    if "user_code" in info:
                        st.session_state["device_info"] = info
                        st.session_state["active_client_id"] = client_id_input
                        st.session_state["active_client_secret"] = client_secret_input
                        st.rerun()
                    else:
                        err_msg = info.get(
                            "error_description", info.get("error", "Desconocido"))
                        st.error(f"Error de Google: {err_msg}")
                        st.info(
                            "💡 Asegurate de que el Client ID sea de tipo 'TVs and Limited Input devices' y que la API 'YouTube Data API v3' esté habilitada en Google Cloud Console.")
        else:
            info = st.session_state["device_info"]

            st.markdown(f"""
            <div class="yt-card">
                <h4>Pasos para vincular tu cuenta:</h4>
                <ol>
                    <li>Hacé clic en el enlace oficial de Google: <a href="https://www.google.com/device" target="_blank" style="color: #FF0000; font-weight: bold;">google.com/device</a></li>
                    <li>Escribí o pegá este código de verificación:</li>
                </ol>
                <div class="code-display">{info["user_code"]}</div>
                <p style="color: #AAAAAA; font-size: 0.9rem;">Una vez ingresado el código en la pantalla de Google, hacé clic en el botón de abajo para verificar.</p>
            </div>
            """, unsafe_allow_html=True)

            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("✅ Ya ingresé el código"):
                    cid = st.session_state.get(
                        "active_client_id", client_id_input)
                    csec = st.session_state.get(
                        "active_client_secret", client_secret_input)
                    token_data = poll_device_token(
                        cid, csec, info["device_code"])
                    if "access_token" in token_data:
                        creds = {
                            "access_token": token_data["access_token"],
                            "refresh_token": token_data.get("refresh_token", ""),
                            "scope": SCOPE,
                            "token_type": "Bearer",
                            "expires_in": token_data.get("expires_in", 3599)
                        }
                        st.session_state["yt_credentials"] = json.dumps(creds)
                        st.session_state["device_info"] = None
                        st.success("¡Cuenta conectada exitosamente!")
                        st.rerun()
                    elif token_data.get("error") == "authorization_pending":
                        st.warning(
                            "Google indica que aún no ingresaste el código. Por favor, aprobalo en google.com/device y reintentá.")
                    else:
                        st.error(
                            f"Error de autorización: {token_data.get('error_description', token_data.get('error', 'Tiempo de espera agotado.'))}")

            with col2:
                if st.button("Cancelar"):
                    st.session_state["device_info"] = None
                    st.rerun()

    else:
        # Método por Headers / Cookie del navegador
        st.caption(
            "Copiá y pegá las cabeceras/cookie de tu sesión activa de YouTube Music.")
        headers_raw = st.text_area(
            "Cabeceras de red (o Cookie) de music.youtube.com:",
            height=150,
            placeholder="accept: */*\naccept-language: es-419,es;q=0.9\ncookie: VISITOR_INFO1_LIVE=...; __Secure-1PSID=...\n..."
        )
        if st.button("🔑 Conectar con Cabeceras"):
            if headers_raw.strip():
                st.session_state["yt_credentials"] = headers_raw.strip()
                st.success("¡Cabeceras guardadas exitosamente!")
                st.rerun()
            else:
                st.error("Por favor pegá tus cabeceras de red o cookie.")

# ------------------------------------------
# PASO 2: ORGANIZAR BIBLIOTECA
# ------------------------------------------
else:
    try:
        yt = YTMusic(st.session_state["yt_credentials"])
    except Exception as e:
        st.error(f"Error al inicializar sesión de YTMusic: {e}")
        if st.button("Reintentar Inicio de Sesión"):
            st.session_state["yt_credentials"] = None
            st.rerun()
        st.stop()

    st.markdown("""
    <div class="yt-card">
        <h4 style="margin:0; color: #4CAF50;">✓ Sesión activa y lista</h4>
        <p style="margin:0; color: #AAAAAA; font-size: 0.9rem;">Tus datos de acceso están resguardados localmente en tu navegador durante esta sesión.</p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Cerrar Sesión"):
        st.session_state["yt_credentials"] = None
        st.rerun()

    st.markdown("### 🚀 Iniciar Organización")
    if st.button("Comenzar a organizar mis Playlists"):
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

        st.markdown(
            f"**Canciones encontradas para procesar:** `{len(tracks)}`")

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
                f"Analizando: {i}/{len(tracks)} - {title} → ({genre})")

        status_text.text(
            "Actualizando playlists en tu cuenta de YouTube Music...")

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

            results.append({"Género": genre, "Canciones agregadas": len(ids)})

        st.success("🎉 ¡Organización completada con éxito!")
        st.table(results)
