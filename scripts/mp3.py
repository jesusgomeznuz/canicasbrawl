import yt_dlp
import os

# Definir la carpeta de descargas
downloads_dir = os.path.join(os.path.expanduser("~"), "Downloads")

# Pedir la URL del video de YouTube
youtube_url = input("Introduce la URL del video de YouTube: ")

# Descargar el audio en formato MP3
def descargar_audio(url):
    print(f"Descargando audio de {url}...")

    # Configurar opciones de descarga
    ydl_opts = {
        'format': 'bestaudio/best',  # Descargar la mejor calidad de audio disponible
        'outtmpl': os.path.join(downloads_dir, '%(title)s.%(ext)s'),  # Guardar en la carpeta de descargas con el título del video
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',  # Extraer el audio usando FFmpeg
            'preferredcodec': 'mp3',  # Convertir a mp3
            'preferredquality': '192',  # Calidad del mp3
        }],
    }

    # Descargar el audio usando yt-dlp
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

# Ejecutar la función de descarga
descargar_audio(youtube_url)

print(f"Audio descargado en formato MP3 en la carpeta de descargas: {downloads_dir}")
