import json
import os
import re
import time

import requests
import streamlit as st

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
# PARÁMETROS DE OAUTH, YOUTUBE Y LAST.FM
# ==========================================
DEVICE_CODE_URL = "https://oauth2.googleapis.com/device/code"
TOKEN_URL = "https://oauth2.googleapis.com/token"
SCOPE = "https://www.googleapis.com/auth/youtube"
YT_API_BASE = "https://www.googleapis.com/youtube/v3"


def get_server_secret(name):
    try:
        value = st.secrets.get(name)
    except Exception:
        value = None
    return value or os.getenv(name, "")


YT_CLIENT_ID = get_server_secret("YT_CLIENT_ID")
YT_CLIENT_SECRET = get_server_secret("YT_CLIENT_SECRET")

LASTFM_API_KEY = get_server_secret("LASTFM_API_KEY")
LASTFM_API_URL = 'https://ws.audioscrobbler.com/2.0/'

LASTFM_SLEEP = 0.25
YT_INSERT_SLEEP = 0.3
MIN_TRACKS_PER_GENRE = 3
DEFAULT_MAX_ADDS = 150
MAX_CONSECUTIVE_FAILURES = 5

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
    ('tango', 'Tango'),
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

OMIT_LABEL = "— Omitir —"
EXTRA_GENRES = ["Folklore", "Electrónica", "Hip Hop", "Jazz", "Reggae",
                "Indie", "Salsa", "Baladas", "Clásica", "Otros"]
GENRE_CHOICES = [OMIT_LABEL] + sorted(
    {g for _, g in GENRE_PRIORITY} | set(ARTIST_MAP.values()) | set(EXTRA_GENRES))

# ==========================================
# FUNCIONES AUXILIARES DE OAUTH
# ==========================================


def request_oauth_response(url, data):
    try:
        response = requests.post(url, data=data, timeout=15)
    except requests.RequestException as exc:
        return {"error": "network_error", "error_description": str(exc)}
    try:
        return response.json()
    except ValueError:
        return {
            "error": "http_error",
            "error_description": f"HTTP {response.status_code}: respuesta inválida de Google.",
        }


def request_device_code(client_id):
    return request_oauth_response(DEVICE_CODE_URL, {
        'client_id': client_id,
        'scope': SCOPE,
    })


def poll_device_token(client_id, client_secret, device_code):
    return request_oauth_response(TOKEN_URL, {
        'client_id': client_id,
        'client_secret': client_secret,
        'device_code': device_code,
        'grant_type': 'urn:ietf:params:oauth:grant-type:device_code'
    })


# ==========================================
# CLIENTE DE LA API OFICIAL DE YOUTUBE (Data API v3)
# ==========================================


class YouTubeAPIError(Exception):
    def __init__(self, status, reason, message):
        super().__init__(message)
        self.status = status
        self.reason = reason
        self.message = message


class QuotaExceeded(YouTubeAPIError):
    pass


def get_access_token(force_refresh=False):
    """Devuelve un access token válido; lo renueva con el refresh token si vence."""
    creds = json.loads(st.session_state["yt_credentials"])
    if force_refresh or int(creds.get("expires_at", 0)) - 60 <= time.time():
        data = request_oauth_response(TOKEN_URL, {
            "client_id": YT_CLIENT_ID,
            "client_secret": YT_CLIENT_SECRET,
            "refresh_token": creds.get("refresh_token", ""),
            "grant_type": "refresh_token",
        })
        if not data.get("access_token"):
            detail = data.get("error_description", data.get(
                "error", "error desconocido"))
            raise YouTubeAPIError(
                401, "auth", f"No se pudo renovar la sesión de Google: {detail}")
        expires_in = int(data.get("expires_in") or 3599)
        creds["access_token"] = data["access_token"]
        creds["expires_at"] = int(time.time()) + expires_in
        st.session_state["yt_credentials"] = json.dumps(creds)
    return creds["access_token"]


def yt_request(method, path, params=None, body=None):
    resp = None
    for attempt in range(2):
        token = get_access_token(force_refresh=(attempt == 1))
        try:
            resp = requests.request(
                method, f"{YT_API_BASE}/{path}", params=params, json=body,
                headers={"Authorization": f"Bearer {token}"}, timeout=30)
        except requests.RequestException as exc:
            raise YouTubeAPIError(0, "network", f"Error de red: {exc}")
        if resp.status_code == 401 and attempt == 0:
            continue  # reintenta una vez con un token renovado
        break

    if resp.ok:
        return resp.json()

    try:
        err = resp.json().get("error", {})
    except ValueError:
        err = {}
    reasons = [e.get("reason", "") for e in err.get("errors", [])]
    message = err.get("message") or f"HTTP {resp.status_code}"
    reason = reasons[0] if reasons else ""
    if resp.status_code == 403 and any(
            r in ("quotaExceeded", "dailyLimitExceeded") for r in reasons):
        raise QuotaExceeded(resp.status_code, reason, message)
    raise YouTubeAPIError(resp.status_code, reason, message)


def yt_list_all(path, params):
    items, page_token = [], None
    while True:
        page_params = dict(params)
        if page_token:
            page_params["pageToken"] = page_token
        data = yt_request("GET", path, page_params)
        items.extend(data.get("items", []))
        page_token = data.get("nextPageToken")
        if not page_token:
            return items


def video_to_track(item):
    """Convierte un video con 'Me gusta' en una canción; devuelve None si no es música."""
    snippet = item.get("snippet", {})
    channel = (snippet.get("channelTitle") or "").strip()
    title = (snippet.get("title") or "").strip()
    video_id = item.get("id")
    is_topic = channel.endswith(" - Topic")
    is_music = snippet.get("categoryId") == "10" or is_topic
    if not video_id or not title or not is_music:
        return None

    if is_topic:
        artist = channel[:-len(" - Topic")].strip()
    elif " - " in title:
        artist, title = [p.strip() for p in title.split(" - ", 1)]
    else:
        artist = re.sub(r'\s*VEVO$', '', channel, flags=re.I).strip()

    if not artist:
        return None
    return {"videoId": video_id, "title": title, "artist": artist}


def fetch_liked_music():
    items = yt_list_all("videos", {
        "part": "snippet", "myRating": "like", "maxResults": 50})
    tracks, seen = [], set()
    for item in items:
        track = video_to_track(item)
        if track and track["videoId"] not in seen:
            seen.add(track["videoId"])
            tracks.append(track)
    return tracks, len(items)


def fetch_my_playlists():
    items = yt_list_all("playlists", {
        "part": "snippet", "mine": "true", "maxResults": 50})
    return {it["snippet"]["title"]: it["id"] for it in items}


def fetch_playlist_video_ids(playlist_id):
    items = yt_list_all("playlistItems", {
        "part": "contentDetails", "playlistId": playlist_id, "maxResults": 50})
    return {it["contentDetails"]["videoId"]
            for it in items if it.get("contentDetails", {}).get("videoId")}


def create_playlist(title, description):
    data = yt_request(
        "POST", "playlists", {"part": "snippet,status"},
        {"snippet": {"title": title, "description": description},
         "status": {"privacyStatus": "private"}})
    return data["id"]


def add_video_to_playlist(playlist_id, video_id):
    yt_request(
        "POST", "playlistItems", {"part": "snippet"},
        {"snippet": {"playlistId": playlist_id,
                     "resourceId": {"kind": "youtube#video", "videoId": video_id}}})


# ==========================================
# LÓGICA DE CLASIFICACIÓN
# ==========================================


def clean_title(title):
    t = re.sub(
        r'\s*[\(\[][^\)\]]*(official|lyric|audio|video|hd|hq|remaster|remix|live)[^\)\]]*[\)\]]',
        '', title, flags=re.I
    )
    t = re.sub(
        r'\s*[\(\[]?\s*(feat\.?|ft\.?|featuring|con)\s+[^\)\]]+[\)\]]?',
        '', t, flags=re.I
    )
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


def genre_from_text(text):
    text = text.lower()
    for keyword, canonical in GENRE_PRIORITY:
        if re.search(r'\b' + re.escape(keyword) + r'\b', text):
            return canonical
    return None


def new_lastfm_stats():
    return {"requests": 0, "errors": 0, "last_error": "",
            "classified": 0, "artist_tags": {}}


def lastfm_get_tags(params, stats):
    """Consulta Last.fm y devuelve la lista de etiquetas (vacía si no hay o falla)."""
    stats["requests"] += 1
    try:
        data = requests.get(LASTFM_API_URL, params=params, timeout=8).json()
    except Exception as exc:
        stats["errors"] += 1
        stats["last_error"] = f"{type(exc).__name__}: {exc}"[:150]
        return []
    if "error" in data:
        if data.get("error") != 6:  # 6 = no encontrado (normal en temas poco conocidos)
            stats["errors"] += 1
            stats["last_error"] = f"Last.fm {data.get('error')}: {data.get('message', '')}"[
                :150]
        return []
    container = data.get("track") or data
    tags = container.get("toptags", {}).get("tag", [])
    if isinstance(tags, dict):
        tags = [tags]
    return [(t.get("name") or "").lower() for t in tags]


def lookup_lastfm(artist, track, stats):
    """Devuelve (género, etiquetas vistas). Prueba primero la canción y luego el artista."""
    if not LASTFM_API_KEY:
        return 'Sin clasificar', []
    base = {'api_key': LASTFM_API_KEY, 'format': 'json', 'autocorrect': 1}
    track_tags = lastfm_get_tags(
        {**base, 'method': 'track.getInfo', 'artist': artist, 'track': track}, stats)
    time.sleep(LASTFM_SLEEP)
    seen = list(track_tags)
    genre = genre_from_text(" ".join(track_tags))
    if not genre:
        key = artist.lower()
        if key not in stats["artist_tags"]:
            stats["artist_tags"][key] = lastfm_get_tags(
                {**base, 'method': 'artist.getTopTags', 'artist': artist}, stats)
            time.sleep(LASTFM_SLEEP)
        artist_tags = stats["artist_tags"][key]
        seen += artist_tags
        genre = genre_from_text(" ".join(artist_tags))
    if genre:
        stats["classified"] += 1
    return genre or 'Sin clasificar', seen[:6]


# ==========================================
# PROCESO DE ORGANIZACIÓN
# ==========================================


def sync_playlists(genre_map, max_adds, status_text, results, summary,
                   min_tracks=MIN_TRACKS_PER_GENRE):
    """Agrega las canciones de cada género a su playlist (la crea si no existe)."""
    status_text.text("Revisando tus playlists...")
    existing = fetch_my_playlists()
    remaining = int(max_adds)
    consecutive_failures = 0

    for genre, ids in genre_map.items():
        if genre == 'Sin clasificar' or len(ids) < min_tracks:
            continue
        if remaining <= 0:
            summary["limit_reached"] = True
            break

        playlist_id = existing.get(genre)
        current_ids = fetch_playlist_video_ids(
            playlist_id) if playlist_id else set()
        new_ids = [v for v in ids if v not in current_ids]
        results.setdefault(genre, 0)
        if not new_ids:
            continue

        if not playlist_id:
            playlist_id = create_playlist(genre, f"Auto-generada ({genre})")
            existing[genre] = playlist_id

        for n, video_id in enumerate(new_ids, 1):
            if remaining <= 0:
                summary["limit_reached"] = True
                break
            status_text.text(
                f"Agregando a '{genre}': {n}/{len(new_ids)} "
                f"(quedan {remaining} en este máximo)")
            try:
                add_video_to_playlist(playlist_id, video_id)
            except QuotaExceeded:
                raise
            except YouTubeAPIError as exc:
                summary["failed"] += 1
                summary["last_error"] = exc.message
                consecutive_failures += 1
                if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                    raise
                continue
            consecutive_failures = 0
            results[genre] += 1
            remaining -= 1
            time.sleep(YT_INSERT_SLEEP)


def organizar(max_adds, progress_bar, status_text, results):
    """Clasifica los 'Me gusta' y los agrega a playlists por género.

    Va completando `results` (género -> canciones agregadas) a medida que avanza,
    así que si se agota la cuota a mitad de camino el avance queda registrado.
    """
    summary = {"limit_reached": False, "failed": 0, "last_error": "",
               "unclassified": 0, "tracks": 0,
               "unclassified_list": [], "lastfm": new_lastfm_stats()}

    status_text.text("Obteniendo tus videos con 'Me gusta'...")
    tracks, total_liked = fetch_liked_music()
    summary["tracks"] = len(tracks)
    st.markdown(
        f"**Canciones encontradas para procesar:** `{len(tracks)}` "
        f"(de {total_liked} videos con 'Me gusta')")
    if not tracks:
        return summary

    genre_map = {}
    lastfm_stats = new_lastfm_stats()
    unclassified_list = []
    for i, track in enumerate(tracks, 1):
        clean_t = clean_title(track["title"])
        genre = classify_local(track["artist"], clean_t, "")
        if not genre:
            genre, seen_tags = lookup_lastfm(
                track["artist"], clean_t, lastfm_stats)
            if genre == 'Sin clasificar':
                unclassified_list.append({
                    "videoId": track["videoId"],
                    "artist": track["artist"],
                    "title": track["title"],
                    "tags": ", ".join(seen_tags)})
        genre_map.setdefault(genre, []).append(track["videoId"])
        progress_bar.progress(int(i / len(tracks) * 100))
        status_text.text(
            f"Analizando: {i}/{len(tracks)} - {track['title']} → ({genre})")

    summary["unclassified"] = len(genre_map.get('Sin clasificar', []))
    summary["unclassified_list"] = unclassified_list
    st.session_state["pending_unclassified"] = unclassified_list
    summary["lastfm"] = lastfm_stats

    sync_playlists(genre_map, max_adds, status_text, results, summary)
    return summary


# ==========================================
# INTERFAZ PRINCIPAL DE LA APP
# ==========================================
st.markdown("""
<div style="display: flex; align-items: center; gap: 16px; margin-bottom: 8px;">
    <img src="https://upload.wikimedia.org/wikipedia/commons/6/6a/Youtube_Music_icon.svg" width="48" height="48" alt="YouTube Music Logo"/>
    <h1 style="margin: 0; font-size: 2.2rem; line-height: 1.2;">YouTube Music Organizer</h1>
</div>
""", unsafe_allow_html=True)

st.write("Clasificá automáticamente tus canciones con 'Me gusta' en playlists privadas ordenadas por género musical.")
st.markdown("---")

if "yt_credentials" not in st.session_state:
    st.session_state["yt_credentials"] = None
if "device_info" not in st.session_state:
    st.session_state["device_info"] = None

# ------------------------------------------
# PASO 1: CONEXIÓN CON GOOGLE / YOUTUBE
# ------------------------------------------
if not st.session_state["yt_credentials"]:
    st.markdown("### 🔒 Conectar tu cuenta de YouTube")
    st.caption(
        "Vas a iniciar sesión en Google para autorizar el acceso. No ingreses tu contraseña en esta app.")

    if not YT_CLIENT_ID or not YT_CLIENT_SECRET:
        st.error("La app todavía no está configurada con sus credenciales OAuth.")
    else:
        if not st.session_state["device_info"]:
            if st.button("🔗 Conectar con Google"):
                info = request_device_code(YT_CLIENT_ID)
                if "user_code" in info:
                    st.session_state["device_info"] = info
                    st.rerun()
                else:
                    err_msg = info.get(
                        "error_description", info.get("error", "Desconocido"))
                    st.error(f"Error de Google: {err_msg}")
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
                <p style="color: #AAAAAA; font-size: 0.85rem;">Abrí ese enlace en el navegador (no en la app de YouTube del celular).</p>
            </div>
            """, unsafe_allow_html=True)

            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("✅ Ya ingresé el código"):
                    token_data = poll_device_token(
                        YT_CLIENT_ID, YT_CLIENT_SECRET, info["device_code"])
                    if token_data.get("access_token") and token_data.get("refresh_token"):
                        expires_in = int(token_data.get("expires_in") or 3599)
                        creds = {
                            "access_token": token_data["access_token"],
                            "refresh_token": token_data.get("refresh_token", ""),
                            "scope": SCOPE,
                            "token_type": "Bearer",
                            "expires_in": expires_in,
                            "expires_at": int(time.time()) + expires_in,
                        }
                        st.session_state["yt_credentials"] = json.dumps(creds)
                        st.session_state["device_info"] = None
                        st.success("¡Cuenta conectada exitosamente!")
                        st.rerun()
                    elif token_data.get("access_token"):
                        st.error(
                            "Google no devolvió un refresh token. Revocá el acceso de esta app en tu cuenta de Google y volvé a autorizar.")
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

# ------------------------------------------
# PASO 2: ORGANIZAR PLAYLISTS
# ------------------------------------------
else:
    st.markdown("""
    <div class="yt-card">
        <h4 style="margin:0; color: #4CAF50;">✓ Sesión activa y lista</h4>
        <p style="margin:0; color: #AAAAAA; font-size: 0.9rem;">La autorización se mantiene durante esta sesión.</p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Cerrar Sesión"):
        st.session_state["yt_credentials"] = None
        st.rerun()

    st.markdown("### 🚀 Iniciar Organización")
    st.caption(
        "Se leen tus videos de música con 'Me gusta' y se agregan a playlists privadas por género. "
        "Cada canción agregada consume cuota de la API de YouTube (unas 50 unidades; el tope diario "
        "por defecto es de 10.000 y se comparte entre todos los usuarios de la app). "
        "Si no alcanza en un día, volvé a ejecutar al siguiente: la app salta lo que ya está en cada playlist.")
    if LASTFM_API_KEY:
        st.caption("Last.fm: clave detectada ✓")
    else:
        st.warning(
            "No se detectó LASTFM_API_KEY en los Secrets: solo se clasificará por la lista de "
            "artistas y las palabras del título.")
    max_adds = st.number_input(
        "Máximo de canciones a agregar en esta ejecución",
        min_value=10, max_value=1000, value=DEFAULT_MAX_ADDS, step=10)

    if st.button("Comenzar a organizar mis Playlists"):
        progress_bar = st.progress(0)
        status_text = st.empty()
        results = {}
        summary = None

        try:
            summary = organizar(max_adds, progress_bar, status_text, results)
        except QuotaExceeded:
            st.warning(
                "Se alcanzó la cuota diaria de la API de YouTube. Lo que ya se agregó quedó guardado. "
                "Volvé a ejecutar mañana (la cuota se reinicia a medianoche, hora del Pacífico) "
                "y la app seguirá desde donde quedó.")
        except YouTubeAPIError as exc:
            st.error(
                f"Error de YouTube ({exc.status} {exc.reason}): {exc.message}")

        status_text.empty()

        if summary is not None:
            if not summary["tracks"]:
                st.info(
                    "No se encontraron canciones de música entre tus videos con 'Me gusta'.")
            else:
                if LASTFM_API_KEY:
                    lf = summary["lastfm"]
                    detail = f" Último error: {lf['last_error']}" if lf["errors"] else ""
                    st.caption(
                        f"Last.fm: {lf['requests']} consultas, {lf['classified']} canciones "
                        f"clasificadas con sus etiquetas, {lf['errors']} errores.{detail}")
                if summary["unclassified"]:
                    st.caption(
                        f"{summary['unclassified']} canciones quedaron 'Sin clasificar' "
                        "y todavía no se agregaron a ninguna playlist. "
                        "Más abajo podés elegir su género a mano.")
                if summary["failed"]:
                    st.warning(
                        f"{summary['failed']} canciones no se pudieron agregar "
                        f"(por ejemplo, videos no disponibles). Último error: {summary['last_error']}")
                if summary["limit_reached"]:
                    st.info(
                        "Llegaste al máximo de canciones de esta ejecución. "
                        "Volvé a tocar el botón para seguir con el resto.")
                else:
                    st.success("🎉 ¡Organización completada!")

        if results:
            st.table([{"Género": g, "Canciones agregadas": n}
                      for g, n in results.items()])
            st.caption(
                "Un 0 significa que esas canciones ya estaban en la playlist.")

    # ------------------------------------------
    # ASIGNACIÓN MANUAL DE LO QUE QUEDÓ SIN CLASIFICAR
    # ------------------------------------------
    report = st.session_state.pop("manual_report", None)
    if report:
        for level, text in report["messages"]:
            getattr(st, level)(text)
        if report["results"]:
            st.table(report["results"])
        if report["snippet"]:
            st.caption(
                "Para que la próxima vez se clasifiquen solas, pegá estas líneas "
                "dentro de ARTIST_MAP en app.py:")
            st.code(report["snippet"], language="python")

    pending = st.session_state.get("pending_unclassified") or []
    if pending:
        by_artist = {}
        for item in pending:
            by_artist.setdefault(item["artist"], []).append(item)

        st.markdown("### 🧩 Elegí el género de lo que quedó sin clasificar")
        st.caption(
            "Asigná un género a cada artista (o dejá 'Omitir'). Sus canciones se agregan a la "
            "playlist de ese género, que se crea si no existe. Cuenta para el máximo de arriba.")
        with st.form("manual_genres"):
            for artist, items in by_artist.items():
                tags = items[0]["tags"] or "sin etiquetas"
                st.selectbox(
                    f"{artist} · {len(items)} canción(es) · Last.fm: {tags}",
                    GENRE_CHOICES, key=f"manual_genre::{artist}")
            submitted = st.form_submit_button("Agregar a mis playlists")

        if submitted:
            genre_map, assigned = {}, {}
            for artist, items in by_artist.items():
                genre = st.session_state.get(
                    f"manual_genre::{artist}", OMIT_LABEL)
                if genre != OMIT_LABEL:
                    genre_map.setdefault(genre, []).extend(
                        i["videoId"] for i in items)
                    assigned[artist] = genre

            if not assigned:
                st.info("No elegiste ningún género todavía.")
            else:
                messages, manual_results = [], {}
                manual_summary = {"limit_reached": False,
                                  "failed": 0, "last_error": ""}
                holder = st.empty()
                done = False
                try:
                    sync_playlists(genre_map, max_adds, holder, manual_results,
                                   manual_summary, min_tracks=1)
                    done = not manual_summary["limit_reached"]
                except QuotaExceeded:
                    messages.append((
                        "warning",
                        "Se alcanzó la cuota diaria de la API de YouTube. Lo que ya se agregó quedó "
                        "guardado; volvé a enviar mañana y la app salta lo que ya está."))
                except YouTubeAPIError as exc:
                    messages.append(
                        ("error", f"Error de YouTube ({exc.status} {exc.reason}): {exc.message}"))
                holder.empty()
                if manual_summary["failed"]:
                    messages.append((
                        "warning",
                        f"{manual_summary['failed']} canciones no se pudieron agregar. "
                        f"Último error: {manual_summary['last_error']}"))
                if manual_summary["limit_reached"]:
                    messages.append((
                        "info",
                        "Llegaste al máximo de canciones de esta ejecución. "
                        "Volvé a enviar para seguir con el resto."))
                if done:
                    messages.append(
                        ("success", "¡Listo! Las canciones se agregaron a sus playlists."))
                    assigned_ids = {i["videoId"]
                                    for a in assigned for i in by_artist[a]}
                    st.session_state["pending_unclassified"] = [
                        i for i in pending if i["videoId"] not in assigned_ids]
                st.session_state["manual_report"] = {
                    "messages": messages,
                    "results": [{"Género": g, "Canciones agregadas": n}
                                for g, n in manual_results.items()],
                    "snippet": "\n".join(
                        f"    {a.lower()!r}: {g!r}," for a, g in assigned.items()),
                }
                st.rerun()
