import os
from ytmusicapi import OAuthCredentials, YTMusic

AUTH_FILES = ['browser.json', 'headers_auth.json', 'oauth.json']

# Lista de géneros que pudo haber creado el script
GENRES_TO_DELETE = {
    'Metal', 'Cumbia', 'Bossa Nova', 'Samba', 'Música Brasilera', 'Cuarteto',
    'Tango', 'Reggaetón', 'Bachata', 'Salsa', 'Merengue', 'Bolero', 'Folklore',
    'Latin', 'Afro House', 'Organic House', 'Melodic House', 'Progressive House',
    'Deep House', 'Tech House', 'Minimal', 'Techno', 'Trance', 'Drum & Bass',
    'Dubstep', 'EDM', 'Electrónica', 'Ambient', 'Downtempo', 'House', 'Hard Rock',
    'Punk', 'Indie Rock', 'Indie', 'Alternativo', 'Rock', 'Synthpop', 'Pop',
    'Hip-Hop', 'Trap', 'R&B', 'Soul', 'Funk', 'Jazz', 'Blues', 'Reggae', 'Ska',
    'Folk', 'Country', 'Clásica', 'Ópera', 'Bandas Sonoras'
}
GENERATED_DESCRIPTION_PREFIXES = (
    'Auto-generada (',
    'Auto-generada por género musical (',
)


def authenticate():
    client_id = os.getenv('YT_CLIENT_ID', '')
    client_secret = os.getenv('YT_CLIENT_SECRET', '')
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
    return None


def reset_playlists():
    yt = authenticate()
    if not yt:
        print("Error de autenticación.")
        return

    print("Buscando playlists creadas para eliminar...")
    playlists = yt.get_library_playlists()

    targets = [
        pl for pl in playlists
        if pl.get('title') in GENRES_TO_DELETE
        and any(
            (pl.get('description') or '').startswith(prefix)
            for prefix in GENERATED_DESCRIPTION_PREFIXES
        )
    ]
    if not targets:
        print("No se encontraron playlists generadas por este organizador.")
        return

    print("Se eliminarán estas playlists:")
    for pl in targets:
        print(f"  - {pl.get('title')}")
    if input("Escribí BORRAR para confirmar: ").strip() != "BORRAR":
        print("Operación cancelada.")
        return

    deleted_count = 0
    for pl in targets:
        title = pl.get('title')
        try:
            yt.delete_playlist(pl['playlistId'])
            deleted_count += 1
        except Exception as e:
            print(f"    Error borrando {title}: {e}")

    print(
        f"\nSe eliminaron {deleted_count} playlists con información anterior.")


if __name__ == "__main__":
    reset_playlists()
