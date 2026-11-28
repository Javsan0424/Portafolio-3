# Nombres de eventos del juego (Observer).
# Quien publica no sabe quien escucha: la UI, la telemetria y el audio se suscriben por separado.
Damage = "Damage"                # Target, Amount, Source
Heal = "Heal"                    # Target, Amount, Source
PiecePlaced = "PiecePlaced"      # Player, Cells, Upper, Lower
TurnChanged = "TurnChanged"      # Turn, Player
ChainCut = "ChainCut"            # Player, Cells
GameOver = "GameOver"            # Winner (None = empate), Reason
InvalidMove = "InvalidMove"      # Player, Reason
CardDrawn = "CardDrawn"          # Player, DeckCount
TurnPassed = "TurnPassed"        # Player
EffectStarted = "EffectStarted"  # Owner, Kind, Value
GameStarted = "GameStarted"      # Mode
StateChanged = "StateChanged"    # Name (cambio de pantalla, util para la musica)
NetworkError = "NetworkError"    # Text, Lobby


class EventBus:
    def __init__(self):
        self.Listeners = {}

    def Subscribe(self, EventName, Callback):
        if EventName not in self.Listeners:
            self.Listeners[EventName] = []
        self.Listeners[EventName].append(Callback)

    def Unsubscribe(self, EventName, Callback):
        if EventName in self.Listeners and Callback in self.Listeners[EventName]:
            self.Listeners[EventName].remove(Callback)

    def Publish(self, EventName, **Data):
        if EventName not in self.Listeners:
            return
        for Callback in list(self.Listeners[EventName]):
            Callback(**Data)
