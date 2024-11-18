using UnityEngine;

public class WinnerDetector : MonoBehaviour
{
	public static WinnerDetector Instance { get; private set; }
	public Camera mainCamera;
	public float smoothSpeed = 0.125f;
	public float minYPosition = 0f;
	public float yOffset = 5f;
	public Transform Winner { get; private set; }  // Propiedad Winner
	public Transform FirstWinner { get; set; } // Variable para guardar al primer ganador

	private Transform[] players;

	void Awake()
	{
		if (Instance == null)
		{
			Instance = this;
			DontDestroyOnLoad(gameObject);
			Debug.Log("WinnerDetector Instance creada con éxito.");
		}
		else
		{
			Debug.Log("Instancia duplicada de WinnerDetector detectada y destruida.");
			Destroy(gameObject);
		}
	}

	void Start()
	{
		players = FindPlayers();
	}

	void Update()
	{
		if (FirstWinner == null) // Solo actualizar el ganador si no hay un primer ganador
		{
			Winner = GetWinner(); // Actualizar la propiedad Winner
			if (Winner != null)
			{
				FollowWinner(Winner);
			}
		}
		else
		{
			FollowWinner(FirstWinner); // Seguir al primer ganador
		}
	}

	Transform[] FindPlayers()
	{
		int playerCount = 0;
		while (GameObject.Find("Player" + (playerCount + 1)) != null)
		{
			playerCount++;
		}

		Transform[] foundPlayers = new Transform[playerCount];
		for (int i = 0; i < playerCount; i++)
		{
			foundPlayers[i] = GameObject.Find("Player" + (i + 1)).transform;
			// Debug.Log("Jugador encontrado: " + foundPlayers[i].name);
		}

		return foundPlayers;
	}

	Transform GetWinner()
	{
		if (players.Length == 0)
			return null;

		Transform winner = players[0];
		float minHeight = players[0].position.y;

		foreach (Transform player in players)
		{
			if (player.position.y < minHeight)
			{
				minHeight = player.position.y;
				winner = player;
			}
		}

		// Debug.Log("Ganador actual: " + winner.name);
		return winner;
	}

	void FollowWinner(Transform winner)
	{
		Vector3 desiredPosition = mainCamera.transform.position;
		desiredPosition.y = Mathf.Max(winner.position.y + yOffset, minYPosition);
		Vector3 smoothedPosition = Vector3.Lerp(mainCamera.transform.position, desiredPosition, smoothSpeed);
		mainCamera.transform.position = smoothedPosition;
	}
}
