import csv
import os
import shutil
import pandas as pd

def limpiar_carpeta(carpeta):
    for archivo in os.listdir(carpeta):
        archivo_path = os.path.join(carpeta, archivo)
        try:
            if os.path.isfile(archivo_path) and archivo_path.endswith('.mp3'):
                os.unlink(archivo_path)
        except Exception as e:
            print(f'Error al borrar {archivo_path}. Razón: {e}')

def obtener_videos(carpeta):
    videos = [f for f in os.listdir(carpeta) if os.path.isfile(os.path.join(carpeta, f)) and f.startswith("Video") and f.endswith(".mp4")]
    return videos

def obtener_numero_video(nombre_video):
    return int(nombre_video.split("Video")[1].split(" - ")[0])

def leer_results_csv(run_folder):
    results_path = os.path.join(run_folder, "results.csv")
    if not os.path.exists(results_path):
        raise FileNotFoundError(f"El archivo {results_path} no existe.")
    return pd.read_csv(results_path)

def crear_soporte_csv(videos, raw_production_path, runs_path, soporte_path):
    soporte_data = []
    for video in videos:
        num_video = obtener_numero_video(video)
        run_num = num_video - 25
        run_folder = os.path.join(runs_path, str(run_num))
        results_data = leer_results_csv(run_folder)
        print(f"Participantes de: {video}")
        for i, nickname in enumerate(results_data['Nickname'], 1):
            print(f"{i}. {nickname}")
        parches = input("¿Qué voces deseas parchar? (ejemplo: 1,2,3 o 0): ").strip()
        parches_validas = [int(p) for p in parches.split(',') if p.isdigit() and 1 <= int(p) <= len(results_data)]
        print(f"parches_validas: {parches_validas}")
        if parches_validas:
            soporte_data.append({"video": video, "parches": parches_validas, "nicknames": results_data['Nickname']})
    with open(soporte_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        for item in soporte_data:
            writer.writerow([item["video"]])
            for index in item["parches"]:
                writer.writerow([item["nicknames"].iloc[index - 1]])
    return soporte_data

def copiar_archivo_voz(cancion, source_path, destination_folder):
    if os.path.exists(source_path):
        destination_path = os.path.join(destination_folder, f"{cancion} - voz.mp3")
        shutil.copy(source_path, destination_path)
        print(f"{source_path} copiado a {destination_path}")
    else:
        print(f"Advertencia: {source_path} no existe. Se omite la copia.")

def copiar_modelos(soporte_data, voices_info, destino_folder):
    voces_requeridas = set()
    for item in soporte_data:
        parches = item["parches"]
        for index in parches:
            nickname = item["nicknames"].iloc[index - 1].lower()
            voces_requeridas.add(nickname)

    # Crear archivo .txt con la estructura requerida
    txt_file_path = os.path.join(destino_folder, "voices_info.txt")
    with open(txt_file_path, mode='w', encoding='utf-8') as txt_file:
        for voz in voces_requeridas:
            if voz in voices_info:
                url = voices_info[voz]
                txt_file.write(f"{voz}\n{url}\n")
            else:
                print(f"Advertencia: {voz} no se encuentra en voices_info.")

def main():
    raw_production_path = r"D:\canicasbrawl\raw production"
    runs_path = r"D:\canicasbrawl\Runs"
    voices_info_path = r"D:\canicasbrawl\scripts\voices_info.csv"
    parche_huggingface_path = r"D:\canicasbrawl\parche huggingface"

    limpiar_carpeta(parche_huggingface_path)

    videos = obtener_videos(raw_production_path)
    if not videos:
        print("No hay videos para procesar.")
        return

    voices_info = {}
    with open(voices_info_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            voices_info[row['nickname'].lower()] = row['URL']

    soporte_path = os.path.join(parche_huggingface_path, "soporte.csv")
    soporte_data = crear_soporte_csv(videos, raw_production_path, runs_path, soporte_path)

    for item in soporte_data:
        video_name = item["video"]
        cancion = video_name.split(" - ")[2].replace(".mp4", "")
        voz_source_path = os.path.join(r"D:\canicasbrawl\canciones", cancion, "voz.mp3")
        copiar_archivo_voz(cancion, voz_source_path, parche_huggingface_path)

    copiar_modelos(soporte_data, voices_info, parche_huggingface_path)

if __name__ == "__main__":
    main()
