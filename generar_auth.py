from ytmusicapi import setup

print("--- GENERADOR DE AUTENTICACIÓN YTMUSIC ---")
print("Pegá a continuación todas las cabeceras (Request Headers) que copiaste de DevTools.")
print("Cuando termines de pegar, presioná Enter, luego escribí FIN y volvé a presionar Enter:\n")

lines = []
while True:
    line = input()
    if line.strip() == "FIN":
        break
    lines.append(line)

headers_raw = "\n".join(lines)

try:
    setup(filepath="browser.json", headers_raw=headers_raw)
    print("\n✅ ¡Archivo 'browser.json' generado con éxito!")
except Exception as e:
    print(f"\n❌ Error al procesar las cabeceras: {e}")
