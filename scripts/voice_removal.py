import yt_dlp
from pydub import AudioSegment
import pandas as pd
import os
import shutil

log_canciones_path = r"C:\Users\LENOVO\Documents\canicasbrawl\scripts\log_canciones.csv"
downloads_dir = os.path.join(os.path.expanduser("~"), "Downloads")

# Función para convertir MM:SS a segundos
def convertir_a_segundos(tiempo):
    minutos, segundos = map(int, tiempo.split(':'))
    return minutos * 60 + segundos

# Leer el archivo de log de canciones
log_canciones = pd.read_csv(log_canciones_path)

# Identificar y mostrar las canciones que no es necesario convertir
no_convertir = log_canciones[(log_canciones['URL'] == 'na') | (log_canciones['inicio'] == 'na')]
if not no_convertir.empty:
    print("Las siguientes canciones no son necesarias convertir:")
    for index, row in no_convertir.iterrows():
        print(f"- {row['nombre']}")

# Filtrar las canciones que tienen URL y minuto de inicio válidos
log_canciones = log_canciones[(log_canciones['URL'] != 'na') & (log_canciones['inicio'] != 'na')]

for index, row in log_canciones.iterrows():
    youtube_url = row['URL']
    start_time = convertir_a_segundos(row['inicio'])
    folder_name = row['nombre']

    # Crear la carpeta si no existe
    output_dir = os.path.join("D:\\canicasbrawl\\canciones", folder_name)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Descargar video de YouTube
    print(f"Descargando audio de {folder_name}...")
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(output_dir, 'temp_audio.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([youtube_url])

    # Convertir a MP3 y cortar el segmento deseado
    print("Procesando audio...")
    audio = AudioSegment.from_file(os.path.join(output_dir, 'temp_audio.mp3'))
    segment = audio[start_time*1000:(start_time + 60)*1000]  # Duración fija de 60 segundos
    output_file = os.path.join(downloads_dir, f"{folder_name}.mp3")
    segment.export(output_file, format="mp3")

    # Eliminar archivo temporal
    os.remove(os.path.join(output_dir, 'temp_audio.mp3'))

    print(f"Segmento guardado como {output_file}")

print("Todos los segmentos han sido descargados y guardados en la carpeta de descargas.")

# Función para verificar archivos
def verificar_archivos():
    archivos_faltantes = []
    for index, row in log_canciones.iterrows():
        folder_name = row['nombre']
        archivos_necesarios = [
            f"{folder_name}.mp3",
            f"{folder_name} [music].mp3",
            f"{folder_name} [vocals].mp3"
        ]

        for archivo in archivos_necesarios:
            if not os.path.exists(os.path.join(downloads_dir, archivo)):
                archivos_faltantes.append(archivo)

    return archivos_faltantes

# Ciclo de verificación
while True:
    archivos_faltantes = verificar_archivos()
    if archivos_faltantes:
        print("Faltan los siguientes archivos:")
        for archivo in archivos_faltantes:
            print(archivo)
        input("Por favor, separa los audios manualmente en la página web. Presiona Enter cuando hayas terminado.")
    else:
        print("Todos los archivos han sido generados con éxito.")
        break

# Mover y copiar archivos
for index, row in log_canciones.iterrows():
    folder_name = row['nombre']
    output_dir = os.path.join("D:\\canicasbrawl\\canciones", folder_name)
    backup_dir = os.path.join(output_dir, "backup")

    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)

    archivos_necesarios = {
        f"{folder_name}.mp3": f"{folder_name}.mp3",
        f"{folder_name} [music].mp3": "instrumental.mp3",
        f"{folder_name} [vocals].mp3": "voz.mp3"
    }

    for archivo, nuevo_nombre in archivos_necesarios.items():
        archivo_path = os.path.join(downloads_dir, archivo)
        nuevo_path_backup = os.path.join(backup_dir, nuevo_nombre)
        nuevo_path_principal = os.path.join(output_dir, nuevo_nombre)

        # Mover y renombrar archivos a la carpeta de backup
        shutil.move(archivo_path, nuevo_path_backup)

        # Copiar archivos a la carpeta principal
        shutil.copy(nuevo_path_backup, nuevo_path_principal)

print("Archivos movidos y copiados correctamente.")
