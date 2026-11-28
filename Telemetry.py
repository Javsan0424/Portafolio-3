import csv
import os
import time
from Events import GameStarted, TurnChanged, InvalidMove, CardDrawn, GameOver
from Resources import WritablePath

Columns = ["Fecha", "Modalidad", "DuracionSegundos", "Turnos", "JugadasInvalidas",
           "FichasGeneradas", "Ganador", "Motivo"]


# Observer: solo escucha eventos y al terminar la partida guarda una fila en Telemetry/partidas.csv
class Telemetry:
    def __init__(self, Bus):
        self.Mode = "Local"
        self.StartTime = time.time()
        self.Turns = 0
        self.Invalid = 0
        self.Generated = 0

        Bus.Subscribe(GameStarted, self.OnStarted)
        Bus.Subscribe(TurnChanged, self.OnTurn)
        Bus.Subscribe(InvalidMove, self.OnInvalid)
        Bus.Subscribe(CardDrawn, self.OnCard)
        Bus.Subscribe(GameOver, self.OnOver)

    def OnStarted(self, Mode):
        self.Mode = Mode
        self.StartTime = time.time()
        self.Turns = 0
        self.Invalid = 0
        self.Generated = 0

    def OnTurn(self, Turn, Player):
        self.Turns = Turn

    def OnInvalid(self, Player, Reason):
        self.Invalid += 1

    def OnCard(self, Player, DeckCount):
        self.Generated += 1

    def OnOver(self, Winner, Reason):
        if Winner is None:
            WinnerText = "Empate"
        else:
            WinnerText = "Jugador " + str(Winner + 1)

        ModeText = "Local"
        if self.Mode == "Online":
            ModeText = "En línea"

        Row = [time.strftime("%Y-%m-%d %H:%M:%S"), ModeText, round(time.time() - self.StartTime, 1),
               self.Turns, self.Invalid, self.Generated, WinnerText, Reason]
        self.Save(Row)

    def Save(self, Row):
        try:
            Folder = WritablePath("Telemetry")
            os.makedirs(Folder, exist_ok = True)
            Path = os.path.join(Folder, "partidas.csv")
            IsNew = not os.path.exists(Path)
            with open(Path, "a", newline = "", encoding = "utf-8-sig") as file:
                Writer = csv.writer(file)
                if IsNew:
                    Writer.writerow(Columns)
                Writer.writerow(Row)
        except OSError:
            # La telemetria nunca debe tumbar el juego
            pass
