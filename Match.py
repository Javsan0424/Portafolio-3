import time
from Events import Damage, Heal, TurnChanged, GameOver, InvalidMove, GameStarted
from Board import Board
from Player import Player
from Deck import Deck
from CreateCard import Card
from Commands import CommandHistory
from Resources import LoadData


# Toda la logica de una partida, sin dibujar nada. La UI solo la lee y le manda comandos.
class Match:
    def __init__(self, Bus, Mode = "Local", LocalIndex = None, IsAuthority = True):
        self.Bus = Bus
        self.Mode = Mode                # "Local" o "Online"
        self.LocalIndex = LocalIndex    # None en local; 0 anfitrion, 1 cliente en linea
        self.IsAuthority = IsAuthority  # quien tiene el mazo real
        self.Players = [Player("Jugador 1"), Player("Jugador 2")]
        self.Board = Board()
        self.Deck = None
        self.Turn = 1
        self.PassCount = 0
        self.Over = False
        self.Winner = None
        self.History = CommandHistory()
        self.StartTime = time.time()

    # ---------- Turnos y vista ----------
    def CurrentIndex(self):
        # Turnos impares: Jugador 1, turnos pares: Jugador 2
        if self.Turn % 2 == 1:
            return 0
        return 1

    def IsMyTurn(self):
        if self.Mode == "Local":
            return True
        return self.CurrentIndex() == self.LocalIndex

    def BottomIndex(self):
        # En linea siempre ves tu mano abajo
        if self.Mode == "Online":
            return self.LocalIndex
        return 0

    def FaceUpIndex(self):
        # En local solo se ve la mano del jugador en turno, en linea solo la tuya
        if self.Mode == "Online":
            return self.LocalIndex
        return self.CurrentIndex()

    # ---------- Inicio de partida ----------
    def MakeCard(self, Data):
        if Data is None:
            return Card(None, None)
        return Card(Data[0], Data[1])

    # Local o anfitrion: baraja el mazo real y reparte
    def DealNewGame(self):
        self.Deck = Deck.Build()
        HandSize = LoadData()["Deck"]["HandSize"]
        for i in range(HandSize):
            for Index in range(2):
                self.Players[Index].Hand.append(self.MakeCard(self.Deck.Draw()))
        self.Started()

    # Cliente en linea: solo conoce su mano y cuantas fichas tiene el mazo
    def LoadStart(self, OwnHand, DeckCount):
        HandSize = LoadData()["Deck"]["HandSize"]
        Other = 1 - self.LocalIndex
        for Data in OwnHand:
            self.Players[self.LocalIndex].Hand.append(self.MakeCard(Data))
        for i in range(HandSize):
            self.Players[Other].Hand.append(self.MakeCard(None))
        self.Deck = Deck.Hidden(DeckCount)
        self.Started()

    def Started(self):
        self.StartTime = time.time()
        self.Bus.Publish(GameStarted, Mode = self.Mode)
        self.Bus.Publish(TurnChanged, Turn = self.Turn, Player = self.CurrentIndex())

    # ---------- Comandos ----------
    def Validate(self, Command):
        Ok, Reason = Command.Validate(self)
        if not Ok:
            self.Bus.Publish(InvalidMove, Player = Command.Player, Reason = Reason)
        return Ok, Reason

    def TryExecute(self, Command):
        Ok, Reason = self.Validate(Command)
        if not Ok:
            return False, Reason
        Command.Execute(self)
        self.History.Add(Command)
        return True, ""

    # ---------- Manos ----------
    def HasCard(self, Index, Upper, Lower):
        for Item in self.Players[Index].Hand:
            if Item.Hidden:
                return True
            if Item.UpperEffect == Upper and Item.LowerEffect == Lower:
                return True
        return False

    def TakeFromHand(self, Index, Upper, Lower):
        Hand = self.Players[Index].Hand
        for Item in Hand:
            if not Item.Hidden and Item.UpperEffect == Upper and Item.LowerEffect == Lower:
                Hand.remove(Item)
                return Item
        for Item in Hand:
            if Item.Hidden:
                Hand.remove(Item)
                return Card(Upper, Lower)
        return Card(Upper, Lower)

    def AddCardToHand(self, Index, CardData):
        self.Players[Index].Hand.append(self.MakeCard(CardData))

    # ---------- Vida ----------
    def DealDamage(self, Target, Amount, Source):
        Real = self.Players[Target].TakeDamage(Amount)
        if Real > 0:
            self.Bus.Publish(Damage, Target = Target, Amount = Real, Source = Source)

    def HealPlayer(self, Target, Amount, Source):
        Real = self.Players[Target].Heal(Amount)
        if Real > 0:
            self.Bus.Publish(Heal, Target = Target, Amount = Real, Source = Source)

    # ---------- Fin de turno y de partida ----------
    def EndTurn(self):
        self.CheckWinner()
        if self.Over:
            return
        self.Turn += 1
        self.Bus.Publish(TurnChanged, Turn = self.Turn, Player = self.CurrentIndex())
        self.Board.Tick(self.CurrentIndex(), self)
        self.CheckWinner()

    def CheckWinner(self):
        if self.Over:
            return
        if self.Players[0].currentHealth <= 0:
            self.Finish(1, "Se acabó la vida de Jugador 1")
        elif self.Players[1].currentHealth <= 0:
            self.Finish(0, "Se acabó la vida de Jugador 2")

    def Finish(self, Winner, Reason):
        if self.Over:
            return
        self.Over = True
        self.Winner = Winner
        self.Bus.Publish(GameOver, Winner = Winner, Reason = Reason)

    # Dos pases seguidos con el mazo vacio: gana quien tenga mas vida
    def FinishByDeck(self):
        Life0 = self.Players[0].currentHealth
        Life1 = self.Players[1].currentHealth
        if Life0 > Life1:
            self.Finish(0, "Mazo agotado: Jugador 1 tiene más vida")
        elif Life1 > Life0:
            self.Finish(1, "Mazo agotado: Jugador 2 tiene más vida")
        else:
            self.Finish(None, "Mazo agotado: misma vida")

    # El jugador que se queda gana si el rival se desconecta
    def Forfeit(self, Loser):
        self.Finish(1 - Loser, "El rival se desconectó")
