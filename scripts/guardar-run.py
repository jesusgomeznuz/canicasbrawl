import pandas as pd
from openpyxl import load_workbook
import os
import shutil
from glob import glob

def guardar_run():
    # Paso 1: Crear una nueva carpeta en "C:\Users\LENOVO\Documents\canicasbrawl\Runs"
    runs_path = r"D:\canicasbrawl\Runs"
    existing_folders = [int(folder) for folder in os.listdir(runs_path) if folder.isdigit()]
    new_folder_number = max(existing_folders, default=0) + 1
    new_folder_path = os.path.join(runs_path, str(new_folder_number))
    os.makedirs(new_folder_path)    
    print(f"Carpeta creada: {new_folder_path}")

    # Paso 2: Buscar el video de run más reciente en "C:\Users\LENOVO\HowToMakeAVideoGame\HowToMakeAVideoGame\Recordings"
    recordings_path = r"D:\canicasbrawl\CanicasBrawl\Recordings"
    video_files = glob(os.path.join(recordings_path, "Movie_*.mp4"))
    latest_video = max(video_files, key=os.path.getctime)
    print(f"Video más reciente encontrado: {latest_video}")

    # Paso 3: Copiar y pegar el video en la nueva subcarpeta
    shutil.copy(latest_video, new_folder_path)
    print(f"Video copiado a: {new_folder_path}")

    # Paso 4: Borrar el archivo winner_log.csv en "C:\Users\LENOVO\Documents\canicasbrawl\scripts" si existe
    scripts_path = r"D:\canicasbrawl\scripts"
    winner_log_script_path = os.path.join(scripts_path, "winner_log.csv")
    if os.path.exists(winner_log_script_path):
        os.remove(winner_log_script_path)
        print(f"Archivo eliminado: {winner_log_script_path}")

    # Paso 5: Copiar el archivo winner_log.csv a la nueva subcarpeta y a "C:\Users\LENOVO\Documents\canicasbrawl\scripts"
    winner_log_source_path = r"C:\Users\LENOVO\AppData\LocalLow\CanicasBrawl\CanicasBrawl\winner_log.csv"
    shutil.copy(winner_log_source_path, new_folder_path)
    shutil.copy(winner_log_source_path, scripts_path)
    print(f"Archivo winner_log.csv copiado a: {new_folder_path} y {scripts_path}")
    
    # Copiar el archivo dual_winner_log.csv a la nueva subcarpeta y a "scripts"
    dual_winner_log_source_path = r"C:\Users\LENOVO\AppData\LocalLow\CanicasBrawl\CanicasBrawl\dual_winner_log.csv"
    if os.path.exists(dual_winner_log_source_path):
        shutil.copy(dual_winner_log_source_path, new_folder_path)
        shutil.copy(dual_winner_log_source_path, scripts_path)
        print(f"Archivo dual_winner_log.csv copiado a: {new_folder_path} y {scripts_path}")
    else:
        print(f"Archivo dual_winner_log.csv no encontrado.")

# Ejecutar la función para guardar el run
guardar_run()

# Leer el archivo CSV
file_path = r"D:\canicasbrawl\scripts\winner_log.csv"
df = pd.read_csv(file_path)

# Eliminar duplicados
df = df.drop_duplicates()

# Convertir las columnas de tiempo a milisegundos para facilitar los cálculos
def time_to_ms(time_str):
    h, m, s, ms = map(int, time_str.split(':'))
    return ((h * 60 + m) * 60 + s) * 1000 + ms

df['Time_ms'] = df['Time'].apply(time_to_ms)

# Determinar el ganador basado en el último registro de tiempo más alto
max_time_row = df.loc[df['Time_ms'].idxmax()]
winner = max_time_row['Nickname']

# Guardar el archivo winner.csv
winner_file_path = r"D:\canicasbrawl\scripts\winner.csv"
with open(winner_file_path, 'w') as f:
    f.write('nickname\n')
    f.write(winner)

# Calcular el tiempo en que cada jugador estuvo a la cabeza
next_time_ms = list(df['Time_ms'][1:]) + [df['Time_ms'].iloc[-1]]
df['NextTime_ms'] = next_time_ms
df['LeadTime_ms'] = df['NextTime_ms'] - df['Time_ms']

# Filtrar los registros válidos
df = df.iloc[:-1]  # Eliminamos el último registro que no tiene siguiente tiempo

# Agrupar por Nickname y sumar los tiempos
total_times = {}
for idx, row in df.iterrows():
    nickname = row['Nickname']
    lead_time = row['LeadTime_ms']
    if nickname in total_times:
        total_times[nickname] += lead_time
    else:
        total_times[nickname] = lead_time

# Convertir a segundos y preparar los resultados
results = pd.DataFrame(list(total_times.items()), columns=['Nickname', 'TotalTime'])
results['TotalTime'] = results['TotalTime'] / 1000

# Verificar que el archivo winner.csv existe y contiene datos
if not os.path.exists(winner_file_path) or os.path.getsize(winner_file_path) == 0:
    raise FileNotFoundError(f"El archivo {winner_file_path} no existe o está vacío.")

# Leer el archivo winner.csv para obtener el nombre del ganador
winner_df = pd.read_csv(winner_file_path, encoding='latin1')
winner = winner_df.loc[0, 'nickname']

# Sumar 10 segundos al ganador
results.loc[results['Nickname'] == winner, 'TotalTime'] += 10

# Guardar el archivo results.csv
results_file_path = r"D:\canicasbrawl\scripts\results.csv"
results.to_csv(results_file_path, index=False)

print("Archivos 'results.csv' y 'winner.csv' generados correctamente.")

def procesar_resultados():
    try:
        # Leer el archivo de preferencias para obtener la lista de jugadores y el número de jugadores
        preferencias_path = r"D:\canicasbrawl\scripts\preferencias.csv"
        preferencias_df = pd.read_csv(preferencias_path)
        num_jugadores = len(preferencias_df)
        last_player = preferencias_df['nickname'].iloc[-1].strip().lower()  # Último jugador en la lista

        # Leer el archivo results.csv
        results_path = r"D:\canicasbrawl\scripts\results.csv"
        results_df = pd.read_csv(results_path)

        # Convertir los nombres a minúsculas en results_df
        results_df['Nickname'] = results_df['Nickname'].str.strip().str.lower()

        # Leer el archivo Excel existente
        excel_path = r"D:\canicasbrawl\historico_runs.xlsx"
        workbook = load_workbook(excel_path)
        sheet = workbook.active

        # Determinar la columna para el nuevo run
        run_col = sheet.max_column + 1
        run_col_letter = chr(ord('A') + run_col - 1)
        run_col_header = f"Run{run_col - 1}"
        sheet.cell(row=1, column=run_col, value=run_col_header)
        print(f"Procesando resultados en la columna {run_col_letter} ({run_col_header}).")

        # Crear un diccionario para buscar rápidamente los tiempos por nickname
        results_dict = dict(zip(results_df['Nickname'], results_df['TotalTime']))

        # Depuración: Verificar que los nombres y tiempos de results.csv estén correctos
        print(f"Resultados obtenidos: {results_dict}")

        # Actualizar los tiempos de los jugadores en el Excel
        last_player_row = None
        for row in range(2, sheet.max_row + 1):
            nickname = sheet.cell(row=row, column=1).value.strip().lower()
            if nickname in results_dict:
                total_time = results_dict[nickname]
                sheet.cell(row=row, column=run_col, value=total_time)
                print(f"Escribiendo {total_time} para {nickname} en la fila {row}.")
            else:
                sheet.cell(row=row, column=run_col, value=0)
                print(f"Escribiendo 0 para {nickname} en la fila {row}.")

            # Actualizar la fila del último jugador procesado
            if nickname == last_player:
                last_player_row = row

        # Confirmar que todos los jugadores recibieron un tiempo
        if last_player_row is not None:
            print(f"Último jugador procesado: {last_player} en la fila {last_player_row}.")
        else:
            print("Error: No se encontró al último jugador en el Excel.")

        # Leer el archivo winner.csv para obtener el nombre del ganador
        winner_path = r"D:\canicasbrawl\scripts\winner.csv"
        with open(winner_path, 'r', encoding='latin1') as f:
            winner = f.readlines()[1].strip().lower()
        print(f"Ganador obtenido: {winner.capitalize()}.")

        # Colocar el ganador justo debajo del último jugador procesado
        if last_player_row is not None:
            winner_row = last_player_row + 1
            sheet.cell(row=winner_row, column=1, value='Winner')
            sheet.cell(row=winner_row, column=run_col, value=winner.capitalize())
            print(f"Escribiendo {winner.capitalize()} como ganador en la fila {winner_row}.")

        # Guardar el archivo Excel actualizado
        workbook.save(excel_path)
        print(f"Resultados guardados exitosamente en {excel_path}.")

    except Exception as e:
        print(f"Error al procesar los resultados: {e}")

# Ejecutar la función para procesar los resultados
procesar_resultados()


def mover_mas_archivos():
    # Definir el path de la carpeta runs
    runs_path = r"D:\canicasbrawl\Runs"
    
    # Buscar la subcarpeta con el número más grande
    existing_folders = [int(folder) for folder in os.listdir(runs_path) if folder.isdigit()]
    if not existing_folders:
        print("No hay carpetas en el directorio runs.")
        return

    latest_folder_number = max(existing_folders)
    latest_folder_path = os.path.join(runs_path, str(latest_folder_number))
    print(f"Carpeta más reciente encontrada: {latest_folder_path}")

    # Definir el path de la carpeta scripts
    scripts_path = r"D:\canicasbrawl\scripts"
    
    # Definir los paths de los archivos a copiar
    winner_csv_path = os.path.join(scripts_path, "winner.csv")
    results_csv_path = os.path.join(scripts_path, "results.csv")
    dual_winner_log_path = os.path.join(scripts_path, "dual_winner_log.csv")  # Añadir path para dual_winner_log.csv
    
    # Copiar los archivos a la carpeta de destino
    if os.path.exists(winner_csv_path):
        shutil.copy(winner_csv_path, latest_folder_path)
        print(f"Archivo winner.csv copiado a: {latest_folder_path}")
    if os.path.exists(results_csv_path):
        shutil.copy(results_csv_path, latest_folder_path)
        print(f"Archivo results.csv copiado a: {latest_folder_path}")
    if os.path.exists(dual_winner_log_path):
        shutil.copy(dual_winner_log_path, latest_folder_path)
        print(f"Archivo dual_winner_log.csv copiado a: {latest_folder_path}")

# Ejecutar la función para mover los archivos
mover_mas_archivos()
