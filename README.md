# Organizador de YouTube Music

Aplicación Streamlit que clasifica canciones de la biblioteca autorizada y crea playlists privadas por género.

## Despliegue en Streamlit Community Cloud

1. Subí el repositorio a GitHub sin incluir credenciales ni archivos de autenticación.
2. En Streamlit Community Cloud, elegí `app.py` como archivo principal.
3. En **App settings > Secrets**, configurá las credenciales OAuth de la aplicación:

```toml
YT_CLIENT_ID = ""
YT_CLIENT_SECRET = ""
LASTFM_API_KEY = ""
MUSICBRAINZ_CONTACT_EMAIL = "tu_email@example.com"
```

`YT_CLIENT_ID` y `YT_CLIENT_SECRET` se configuran una sola vez para la aplicación. Cada usuario autoriza su propia cuenta desde Google con el código que muestra la app. No debe ingresar su contraseña ni copiar cookies en Streamlit.

El flujo usa un cliente OAuth de Google tipo **TVs and Limited Input devices**. Configurá la pantalla de consentimiento OAuth; mientras permanezca en modo de prueba, agregá las cuentas de prueba permitidas.

La clave de Last.fm es opcional. Si Last.fm no encuentra un género compatible, la app consulta las etiquetas públicas de MusicBrainz. Configurá `MUSICBRAINZ_CONTACT_EMAIL` con un correo válido de contacto (también podés definir la variable de entorno con ese nombre al ejecutar `organizador.py`). MusicBrainz limita las consultas a una por segundo; los resultados de artistas se reutilizan durante cada ejecución. Sin etiquetas compatibles, las canciones quedan disponibles para asignarles un género manualmente.

## Ejecución local

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

Para secretos locales, creá `.streamlit/secrets.toml` con el mismo formato del ejemplo. Ese archivo está excluido de Git. Luego ejecutá:

```powershell
.venv\Scripts\python -m streamlit run app.py
```

## Seguridad

No subas `secrets.toml`, `.env`, `browser.json`, `headers.txt`, `headers_auth.json` ni `oauth.json` al repositorio. Si una clave real ya fue publicada, revocala y generá una nueva.