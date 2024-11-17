import csv
import os
import shutil
import subprocess
import time
import pandas as pd
from glob import glob
from pydub import AudioSegment
from moviepy.editor import VideoFileClip, AudioFileClip
from playwright.sync_api import sync_playwright, TimeoutError
import requests

public_url = None  # Variable global para almacenar la URL pública

def verificar_url_activo(url):
    try:
        response = requests.get(url, timeout=5)
        # Verificamos si el código de estado es 200 (OK)
        return response.status_code == 200
    except requests.RequestException:
        return False

def log_with_time(message):
    print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {message}")

def load_voice_models(csv_path):
    voice_models = {}
    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            voice_models[row['nickname']] = row['URL']  # Asocia el nickname con la URL del modelo
    return voice_models

def convert_audio_with_playwright(nickname, audio_file_path, download_link, output_path, public_url):
    # Lanzar Playwright y configurar el navegador
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, slow_mo=500)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()
        page.goto(public_url)
        
        try:
            # Navegar a la pestaña "Generate"
            print("Navegando a la pestaña 'Generate'...")
            page.click('button[role="tab"]:has-text("Generate")')

            # Hacer clic en "Refresh Models" en la pestaña "Generate"
            print("Haciendo clic en 'Refresh Models' en la pestaña 'Generate'...")
            page.click('button:has-text("Refresh Models 🔁")')

            # Verificar si el modelo está en la lista de "Voice Models"
            print(f"Verificando si el modelo '{nickname}' está disponible en la lista de 'Voice Models'...")
            voice_models_input_selector = 'input[aria-label="Voice Models"]'
            voice_models_input = page.wait_for_selector(voice_models_input_selector, timeout=30000)
            voice_models_input.click()

            # Esperar a que las opciones del menú desplegable estén disponibles
            options_selector = 'ul[role="listbox"] li[role="option"]'
            try:
                page.wait_for_selector(options_selector, timeout=5000)
                options = page.query_selector_all(options_selector)
                # Extraer los nombres de los modelos
                model_names = [option.inner_text().strip() for option in options]
                print(f"Modelos disponibles: {model_names}")
            except TimeoutError:
                # Si no hay opciones en el dropdown, la espera expirará
                print("No se encontraron modelos en el dropdown. Procediendo a agregar el modelo.")
                model_names = []

            if nickname not in model_names:
                print(f"El modelo '{nickname}' no está disponible. Procediendo a agregarlo.")

                # Navegar a la pestaña "Download model"
                print("Navegando a la pestaña 'Download model'...")
                page.click('button[role="tab"]:has-text("Download model")')

                # Esperar a que los campos estén disponibles
                print("Esperando los campos para ingresar el enlace y el nombre del modelo...")
                # Selector para el campo "Download link to model"
                download_link_selector = 'label:has-text("Download link to model") textarea'
                download_link_textarea = page.wait_for_selector(download_link_selector, timeout=30000)
                print("Campo 'Download link to model' encontrado.")

                # Selector para el campo "Name your model"
                model_name_selector = 'label:has-text("Name your model") textarea'
                model_name_textarea = page.wait_for_selector(model_name_selector, timeout=30000)
                print("Campo 'Name your model' encontrado.")

                # Llenar los campos con los datos proporcionados
                print("Escribiendo el enlace de descarga en el campo correspondiente...")
                download_link_textarea.fill(download_link)

                print("Escribiendo el nombre del modelo en el campo correspondiente...")
                model_name_textarea.fill(nickname)

                # Hacer clic en "Download 🌐"
                print("Haciendo clic en 'Download 🌐'...")
                download_button_selector = 'button:has-text("Download 🌐")'
                download_button = page.wait_for_selector(download_button_selector, timeout=30000)
                download_button.click()
                print("Descarga iniciada.")

                # Esperar a que aparezca el mensaje de éxito
                print("Esperando a que el modelo se descargue y cargue...")
                try:
                    page.wait_for_function(
                        f"""(modelName) => {{
                            const textarea = document.querySelector('textarea[data-testid="textbox"][disabled]');
                            return textarea && textarea.value.includes(`[+] {nickname} Model successfully downloaded!`);
                        }}""",
                        timeout=300000,
                        arg=nickname
                    )
                    print("Modelo descargado y cargado exitosamente.")
                except TimeoutError:
                    print("No se recibió mensaje de éxito en el tiempo esperado.")
                    browser.close()
                    return

                # Volver a la pestaña "Generate" y refrescar modelos
                print("Navegando de regreso a la pestaña 'Generate'...")
                page.click('button[role="tab"]:has-text("Generate")')
                print("Haciendo clic en 'Refresh Models' en la pestaña 'Generate'...")
                page.click('button:has-text("Refresh Models 🔁")')

                # Intentar seleccionar el modelo nuevamente
                voice_models_input = page.wait_for_selector(voice_models_input_selector, timeout=30000)
                voice_models_input.click()
                page.wait_for_selector(options_selector, timeout=5000)
                options = page.query_selector_all(options_selector)
                model_names = [option.inner_text().strip() for option in options]

                if nickname in model_names:
                    print(f"El modelo '{nickname}' está disponible después de agregarlo.")
                else:
                    print(f"No se pudo agregar el modelo '{nickname}'.")
                    browser.close()
                    return

            else:
                print(f"El modelo '{nickname}' está disponible. Procediendo con la generación.")

            # Seleccionar el modelo
            voice_models_input.click()
            page.wait_for_selector(options_selector, timeout=5000)
            page.click(f'{options_selector}:has-text("{nickname}")')
            print(f"Opción '{nickname}' seleccionada.")

            # Hacer clic en "Upload file instead" y subir el archivo
            print("Haciendo clic en 'Upload file instead'...")
            upload_file_instead_selector = 'button:has-text("Upload file instead")'
            page.click(upload_file_instead_selector)

            # Esperar un momento para que el input de archivo se cargue
            time.sleep(1)

            print(f"Subiendo el archivo '{audio_file_path}'...")
            file_input_selector = 'input[type="file"][accept="audio/*"]'
            file_input = page.locator(file_input_selector)
            file_input.set_input_files(audio_file_path)
            print("Archivo subido exitosamente.")

            # Esperar unos segundos para asegurar que el archivo se procese
            print("Esperando 5 segundos para asegurar que el archivo se procese...")
            time.sleep(5)

            # Hacer clic en 'Generate' usando el id del botón
            print("Haciendo clic en 'Generate'...")
            generate_button_selector = '#component-55'
            page.wait_for_selector(generate_button_selector, timeout=30000)
            page.click(generate_button_selector)
            print("Generación iniciada.")

            # Esperar a que el audio generado esté disponible
            print("Esperando a que el audio generado esté disponible...")
            # Esperar a que el 'div.empty' desaparezca dentro del componente correspondiente
            page.wait_for_selector('div#component-56 div.empty', state='detached', timeout=600000)
            print("Audio generado y disponible.")

            # Hacer clic en el botón de descarga y manejar la descarga
            print("Haciendo clic en el botón de descarga para descargar el audio generado...")
            download_audio_selector = 'div#component-56 a.download-link'
            with page.expect_download() as download_info:
                page.click(download_audio_selector)
            download = download_info.value
            # Guardar el archivo descargado en una ruta específica
            output_file_path = os.path.join(output_path, f"{nickname}.mp3")
            download.save_as(output_file_path)
            print("Descarga del audio completada.")

        except Exception as e:
            print(f"Error: {e}")
            browser.close()
            return

        print("Proceso completado exitosamente.")
        browser.close()

        return output_file_path


def list_subfolders(directory, exclude=None):
    exclude = exclude or []
    subfolders = [f.name for f in os.scandir(directory) if f.is_dir() and f.name not in exclude]
    return sorted(subfolders)

def find_earliest_run_with_video(directory, used_runs):
    subfolders = [f.path for f in os.scandir(directory) if f.is_dir()]
    for subfolder in sorted(subfolders, key=lambda x: int(os.path.basename(x))):
        run_number = int(os.path.basename(subfolder))
        if run_number not in used_runs:
            mp4_files = glob(os.path.join(subfolder, "*.mp4"))
            if mp4_files:
                return subfolder, mp4_files[0], run_number
    raise FileNotFoundError("No se encontraron subcarpetas con archivos .mp4")

def time_to_ms(time_str):
    h, m, s, ms = map(int, time_str.split(":"))
    return (h * 3600 + m * 60 + s) * 1000 + ms

def create_final_audio(winner_data, normalized_audio, output_path, instrumental_path):
    instrumental_audio = AudioSegment.from_file(instrumental_path)
    instrumental_audio = instrumental_audio.apply_gain(-5)
    max_duration = max(audio.duration_seconds for audio in normalized_audio.values()) * 1000
    output_audio = AudioSegment.silent(duration=max_duration)

    for i, row in winner_data.iterrows():
        start_time = time_to_ms(row['Time'])
        end_time = time_to_ms(winner_data.iloc[i + 1]['Time']) if i + 1 < len(winner_data) else max_duration
        nickname = row['Nickname'].lower()

        if nickname in normalized_audio:
            player_segment = normalized_audio[nickname][start_time:end_time]
            output_audio = output_audio.overlay(player_segment, position=start_time)

    final_audio = instrumental_audio.overlay(output_audio)
    final_audio_path = os.path.join(output_path, "final_output_with_instrumental.mp3")
    final_audio.export(final_audio_path, format="mp3")
    log_with_time(f"Audio final exportado en: {final_audio_path}")

    return final_audio_path

def contar_canciones(csv_path):
    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        return sum(1 for row in reader)

def listar_runs_disponibles(runs_directory):
    return sum(1 for subdir in os.scandir(runs_directory) if subdir.is_dir() and glob(os.path.join(subdir.path, "*.mp4")))

def verificar_archivos_cancion(cancion_folder):
    voz_path_mp3 = os.path.join(cancion_folder, "voz.mp3")
    voz_path_wav = os.path.join(cancion_folder, "voz.wav")
    instrumental_path = os.path.join(cancion_folder, "instrumental.mp3")
    if os.path.exists(voz_path_mp3) or os.path.exists(voz_path_wav):
        if os.path.exists(instrumental_path):
            return True
    return False

def verificar_y_convertir_voces(winner_data, cancion_folder, voice_models):
    global public_url  # Usamos la variable global para almacenar la URL

    # Ruta del archivo donde almacenaremos el URL público
    url_file_path = 'public_url.txt'

    # Verificar si el URL público ya está almacenado y es válido
    if public_url is None:
        if os.path.exists(url_file_path):
            with open(url_file_path, 'r') as f:
                stored_url = f.read().strip()
                if verificar_url_activo(stored_url):
                    public_url = stored_url
                    log_with_time(f"Usando el URL público almacenado: {public_url}")
                else:
                    log_with_time("El URL público almacenado no está activo.")
        else:
            log_with_time("No se encontró un URL público almacenado.")

    # Si el URL público sigue siendo None, solicitar uno nuevo
    if public_url is None:
        public_url = input("Por favor, introduce la URL pública para realizar la conversión: ")
        # Verificar si el URL ingresado es válido
        if verificar_url_activo(public_url):
            # Almacenar el nuevo URL en el archivo
            with open(url_file_path, 'w') as f:
                f.write(public_url)
            log_with_time(f"Nuevo URL público almacenado: {public_url}")
        else:
            log_with_time("El URL público ingresado no es válido. Por favor, verifica y vuelve a intentarlo.")
            return False  # Salir de la función si el URL no es válido

    all_exist = True
    for nickname in winner_data['Nickname'].unique():
        nickname_lower = nickname.lower()
        player_audio_path_mp3 = os.path.join(cancion_folder, f"{nickname_lower}.mp3")
        player_audio_path_wav = os.path.join(cancion_folder, f"{nickname_lower}.wav")
        if nickname_lower in voice_models:
            if not os.path.exists(player_audio_path_mp3) and not os.path.exists(player_audio_path_wav):
                log_with_time(f"Falta el archivo de voz para {nickname}. Generando...")

                # Llamar a la función de conversión con Playwright
                convert_audio_with_playwright(
                    nickname_lower,
                    os.path.join(cancion_folder, "voz.mp3"),
                    voice_models[nickname_lower],  # Esto es el enlace de descarga
                    cancion_folder,
                    public_url
                )
                all_exist = False
            else:
                log_with_time(f"El archivo de voz para {nickname} ya existe.")
    return all_exist


def main():
    log_canciones_path = r"C:\Users\LENOVO\Documents\canicasbrawl\scripts\log_canciones.csv"
    runs_directory = r"D:\canicasbrawl\Runs"
    voice_models_path = r"D:\canicasbrawl\scripts\voices_info.csv"
    voice_models = load_voice_models(voice_models_path)
    raw_production_folder = r"D:\canicasbrawl\raw production"

    num_canciones = contar_canciones(log_canciones_path)
    log_with_time(f"Hay {num_canciones} canciones en la cola")

    num_runs_disponibles = listar_runs_disponibles(runs_directory)
    log_with_time(f"Hay {num_runs_disponibles} runs disponibles para producción")

    used_runs = set()

    with open(log_canciones_path, newline='', encoding='utf-8') as csvfile:

        reader = list(csv.DictReader(csvfile))
        # Tomar solo las primeras 'num_runs_disponibles' canciones
        canciones_a_procesar = reader[:num_runs_disponibles]

        for row in canciones_a_procesar:
            cancion_nombre = row['nombre']
            cancion_folder = os.path.join(r"D:\canicasbrawl\canciones", cancion_nombre)
            
            run_path, mp4_file, run_number = find_earliest_run_with_video(runs_directory, used_runs)
            video_number = run_number + 25
            new_video_name = f"Video{video_number} - Run {run_number} - {cancion_nombre}.mp4"
            new_video_path = os.path.join(raw_production_folder, new_video_name)
            used_runs.add(run_number)
            
            if os.path.exists(new_video_path):
                log_with_time(f"El video {new_video_name} ya se encuentra en raw production.")
                continue

            if verificar_archivos_cancion(cancion_folder):
                log_with_time(f"Todos los archivos necesarios para {cancion_nombre} están presentes")
            else:
                log_with_time(f"Faltan archivos para {cancion_nombre}.")
                continue

            log_with_time(f"Usando {run_path} para producir la canción {cancion_nombre}")

            winner_log_path = os.path.join(run_path, "winner_log.csv")
            if not os.path.exists(winner_log_path):
                raise FileNotFoundError(f"El archivo {winner_log_path} no existe.")
            winner_data = pd.read_csv(winner_log_path)

            if verificar_y_convertir_voces(winner_data, cancion_folder, voice_models):
                log_with_time(f"Todas las voces necesarias para la canción {cancion_nombre} ya existen.")
            else:
                log_with_time(f"Generación de voces para la canción {cancion_nombre} completada.")

            # Producción del video
            log_with_time(f"Produciendo el video para la canción {cancion_nombre} usando el run {run_path}")
            instrumental_file_path = os.path.join(cancion_folder, "instrumental.mp3")
            player_audio_paths = {
                nickname.lower(): (os.path.join(cancion_folder, f"{nickname.lower()}.mp3") if os.path.exists(os.path.join(cancion_folder, f"{nickname.lower()}.mp3")) else os.path.join(cancion_folder, f"{nickname.lower()}.wav"))
                for nickname in winner_data['Nickname'].unique()
            }

            players_audio = {player: AudioSegment.from_file(path) for player, path in player_audio_paths.items() if os.path.exists(path)}

            # Imprimir niveles originales
            for player, audio in players_audio.items():
                log_with_time(f"Nivel original de {player}: {audio.dBFS} dBFS")

            # Ajustar target_dBFS a un nivel específico (en este caso, -20.0 dBFS)
            target_dBFS = -20.0
            normalized_audio = {}

            for player, audio in players_audio.items():
                change_in_dBFS = target_dBFS - audio.dBFS
                normalized_audio[player] = audio.apply_gain(change_in_dBFS)

                # Imprimir niveles después de la normalización
                log_with_time(f"Nivel final de {player} después de normalización: {normalized_audio[player].dBFS} dBFS")

            final_audio_path = create_final_audio(winner_data, normalized_audio, cancion_folder, instrumental_file_path)

            video_path = mp4_file
            if not os.path.exists(video_path):
                raise FileNotFoundError(f"El archivo {video_path} no existe.")
            log_with_time(f"Archivo de video encontrado: {video_path}")

            video_clip = VideoFileClip(video_path)
            audio_clip = AudioFileClip(final_audio_path)

            video_clip = video_clip.subclip(0, audio_clip.duration)

            final_video = video_clip.set_audio(audio_clip)

            final_video_output_path = os.path.join(cancion_folder, "final_video_with_audio.mp4")
            
            # Verificar si el video final ya existe antes de exportar
            if os.path.exists(final_video_output_path):
                log_with_time(f"El video final {final_video_output_path} ya existe. Se omite la exportación.")
                continue

            final_video.write_videofile(final_video_output_path, codec="libx264", audio_codec="aac")

            log_with_time(f"Video final con audio exportado en: {final_video_output_path}")

            os.makedirs(raw_production_folder, exist_ok=True)
            shutil.move(final_video_output_path, new_video_path)
            log_with_time(f"Video movido a: {new_video_path}")

            os.startfile(raw_production_folder)

if __name__ == "__main__":
    main()
