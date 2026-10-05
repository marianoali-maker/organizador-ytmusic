import os
from ytmusicapi import YTMusic

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

def authenticate():
    for auth_file in AUTH_FILES:
        if os.path.exists(auth_file):
            try:
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
    
    deleted_count = 0
    for pl in playlists:
        title = pl.get('title')
        pl_id = pl.get('playlistId')
        
        if title in GENRES_TO_DELETE:
            print(f"  - Eliminando playlist desactualizada: {title}")
            try:
                yt.delete_playlist(pl_id)
                deleted_count += 1
            except Exception as e:
                print(f"    Error borrando {title}: {e}")
                
    print(f"\nSe eliminaron {deleted_count} playlists con información anterior.")

if __name__ == "__main__":
    reset_playlists()