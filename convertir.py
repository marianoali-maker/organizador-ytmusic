import ytmusicapi

# Lee el archivo headers.txt
with open("headers.txt", "r", encoding="utf-8") as f:
    headers_raw = f.read()

# Genera el archivo browser.json correctamente
ytmusicapi.setup(filepath="browser.json", headers_raw=headers_raw)

print("¡Listo! Se creó el archivo browser.json correctamente.")
