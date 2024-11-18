using UnityEngine;
using System.IO;
using System;
using System.Collections.Generic;

public class WinnerTracker : MonoBehaviour
{
	private WinnerDetector winnerDetector;
	private string currentWinner;
	private float startTime;
	private float lastChangeTime;
	private string finishOrderPath;
	private string winnerLogPath;
	private string winnersListPath;
	private HashSet<string> winnersSet;
	private Dictionary<string, string> playerNicknames;
	private Dictionary<string, float> playerTimes;
	private GameUIManager gameUIManager;
	private List<string> finishOrder = new List<string>();
	public static WinnerTracker Instance { get; private set; }
	private string dualWinnerLogPath;
	[SerializeField] private float h = 10f; // Rango predeterminado

	void Start()
	{
		// Inicializamos la ruta del nuevo archivo
		dualWinnerLogPath = Path.Combine(Application.persistentDataPath, "dual_winner_log.csv");

		// Se genera el nuevo archivo dual_winner_log.csv
		using (StreamWriter writer = new StreamWriter(dualWinnerLogPath, false))
		{
			writer.WriteLine("Time,Winner,Nickname,SecondPlace,SecondNickname");
		}

		winnerDetector = FindObjectOfType<WinnerDetector>();
		gameUIManager = FindObjectOfType<GameUIManager>();

		if (winnerDetector == null)
		{
			return;
		}

		startTime = Time.time;
		lastChangeTime = startTime;
		currentWinner = winnerDetector.Winner != null ? winnerDetector.Winner.name : "Ninguno";
		winnerLogPath = Path.Combine(Application.persistentDataPath, "winner_log.csv");
		winnersListPath = Path.Combine(Application.persistentDataPath, "winners_list.csv");
		finishOrderPath = Path.Combine(Application.persistentDataPath, "finish_order.csv");
		winnersSet = new HashSet<string>();
		playerNicknames = new Dictionary<string, string>();
		playerTimes = new Dictionary<string, float>();

		using (StreamWriter writer = new StreamWriter(winnerLogPath, false))
		{
			writer.WriteLine("Time,Winner,Nickname");
		}
		using (StreamWriter writer = new StreamWriter(winnersListPath, false))
		{
			writer.WriteLine("winners,nickname,totaltime");
		}

		Debug.Log("Winner log file path: " + winnerLogPath);
		Debug.Log("Winners list file path: " + winnersListPath);
	}

	void Update()
	{
		if (winnerDetector.Winner != null && winnerDetector.Winner.name != currentWinner)
		{
			float currentTime = Time.time;
			float timeAtHead = currentTime - lastChangeTime;
			lastChangeTime = currentTime;

			// Se actualiza el tiempo de liderazgo en playerTimes
			if (playerTimes.ContainsKey(currentWinner))
			{
				playerTimes[currentWinner] += timeAtHead;
			}
			else
			{
				playerTimes[currentWinner] = timeAtHead;
			}

			// Detectamos el nuevo ganador
			currentWinner = winnerDetector.Winner.name;
			string nickname = GetNickname(winnerDetector.Winner);

			// Obtenemos el segundo lugar dentro del rango h
			string secondPlace = GetSecondPlaceWithinRange(h); // Retorna "None" si no hay segundo lugar
			string secondNickname = GetNicknameByName(secondPlace); // Obtiene el nickname o "None"

			// Se escribe en el archivo original winner_log.csv
			LogWinnerChange($"{FormatTime(currentTime - startTime)},{currentWinner},{nickname.Trim()}");

			// Se escribe en el nuevo archivo dual_winner_log.csv
			LogDualWinnerChange($"{FormatTime(currentTime - startTime)},{currentWinner},{nickname.Trim()},{secondPlace},{secondNickname.Trim()}");

			if (!winnersSet.Contains(currentWinner))
			{
				winnersSet.Add(currentWinner);
				playerNicknames[currentWinner] = nickname.Trim();
			}
		}

	}

	// Método que retorna el segundo lugar dentro del rango h (sin lista de Players)
	private string GetSecondPlaceWithinRange(float h)
	{
		string secondPlace = "None";  // Valor predeterminado es "None"
		float minDistance = float.MaxValue;

		// Encuentra todos los objetos con el componente Player
		Player[] allPlayers = FindObjectsOfType<Player>();

		// Recorre todos los jugadores que no son el actual ganador
		foreach (var player in allPlayers)
		{
			if (player.name != currentWinner)
			{
				float distance = Vector3.Distance(player.transform.position, winnerDetector.Winner.transform.position);
				if (distance < h && distance < minDistance)
				{
					secondPlace = player.name;  // Actualiza si está dentro del rango y más cercano
					minDistance = distance;
				}
			}
		}

		return secondPlace;  // Si no se encuentra ningún jugador en el rango, retorna "None"
	}

	// Método que obtiene el nickname a partir del nombre del jugador
	private string GetNicknameByName(string playerName)
	{
		if (playerNicknames.ContainsKey(playerName))
		{
			return playerNicknames[playerName];
		}
		return playerName; // Devuelve el nombre si no hay nickname registrado
	}
	void OnTriggerEnter(Collider other)
	{
		if (finishOrder.Count >= 3)
		{
			return;
		}

		Player player = other.GetComponent<Player>();
		if (player != null)
		{
			string nickname = GetNickname(player.transform);
			finishOrder.Add(nickname);

			if (finishOrder.Count == 3)
			{
				SaveFinishOrder();
			}
		}
	}

	// Método para registrar los cambios en el nuevo archivo dual_winner_log.csv
	private void LogDualWinnerChange(string logEntry)
	{
		using (StreamWriter writer = new StreamWriter(dualWinnerLogPath, true))
		{
			writer.WriteLine(logEntry);
		}
	}

	private void SaveFinishOrder()
	{
		using (StreamWriter writer = new StreamWriter(finishOrderPath, true))
		{
			writer.WriteLine($"1st: {finishOrder[0]}, 2nd: {finishOrder[1]}, 3rd: {finishOrder[2]}");
		}
	}

	private string GetNickname(Transform player)
	{
		Player playerScript = player.GetComponent<Player>();
		return playerScript != null ? playerScript.nickname : player.name;
	}

	private string FormatTime(float time)
	{
		TimeSpan timeSpan = TimeSpan.FromSeconds(time);
		return string.Format("{0:D2}:{1:D2}:{2:D2}:{3:D3}", timeSpan.Hours, timeSpan.Minutes, timeSpan.Seconds, timeSpan.Milliseconds);
	}

	private void LogWinnerChange(string logEntry)
	{
		using (StreamWriter writer = new StreamWriter(winnerLogPath, true))
		{
			writer.WriteLine(logEntry);
		}
	}

	void OnDisable()
	{
		if (winnersSet == null || winnersSet.Count == 0)
		{
			return;
		}

		if (playerNicknames == null || playerTimes == null)
		{
			return;
		}

		try
		{
			using (StreamWriter writer = new StreamWriter(winnersListPath, true))
			{
				foreach (var winner in winnersSet)
				{
					if (playerNicknames.ContainsKey(winner) && playerTimes.ContainsKey(winner))
					{
						float totalTime = playerTimes[winner];
						string nickname = playerNicknames[winner];
						writer.WriteLine($"{winner},{nickname},{totalTime}");
					}
				}

				if (winnerDetector != null && winnerDetector.FirstWinner != null)
				{
					string firstWinnerNickname = GetNickname(winnerDetector.FirstWinner);
					writer.WriteLine("\nFirstWinner");
					writer.WriteLine(firstWinnerNickname);
				}
			}

			if (File.Exists(winnersListPath))
			{
				Debug.Log($"Archivo {winnersListPath} actualizado exitosamente.");
			}
			else
			{
				Debug.LogError($"No se pudo actualizar el archivo {winnersListPath}.");
			}

			// Mostrar el jugador con más tiempo en pantalla
			if (playerTimes.Count > 0)
			{
				string topPlayer = null;
				float maxTime = 0f;

				foreach (var player in playerTimes)
				{
					if (player.Value > maxTime)
					{
						maxTime = player.Value;
						topPlayer = player.Key;
					}
				}

				Debug.Log($"Ranking Finish Line: {playerNicknames[topPlayer]} ({topPlayer}) fue el jugador con más tiempo en pantalla: {maxTime} segundos.");
			}
		}
		catch (Exception ex)
		{
			Debug.LogError($"Excepción al intentar guardar los datos en {winnersListPath}: {ex.Message}");
		}
	}
}
