from Events import PiecePlaced, CardDrawn, TurnPassed


# Historial de jugadas ya ejecutadas (sirve para telemetria, depuracion o deshacer a futuro)
class CommandHistory:
    def __init__(self):
        self.Items = []

    def Add(self, Command):
        self.Items.append(Command)

    def Count(self):
        return len(self.Items)

    def Last(self):
        if len(self.Items) == 0:
            return None
        return self.Items[-1]


# Command: una jugada es un objeto que se valida, se ejecuta y se puede enviar por red
class Command:
    Type = ""

    def __init__(self, Player):
        self.Player = Player

    # Comprobaciones comunes: la partida sigue y es el turno de quien juega
    def ValidateTurn(self, Match):
        if Match.Over:
            return False, "La partida ya terminó"
        if Match.CurrentIndex() != self.Player:
            return False, "No es tu turno"
        return True, ""

    def Validate(self, Match):
        return self.ValidateTurn(Match)

    def Execute(self, Match):
        pass

    # Viewer es el jugador que va a recibir el mensaje (para no revelar fichas ocultas)
    def ToDict(self, Viewer = None):
        return {"Type": self.Type, "Player": self.Player}

    @staticmethod
    def FromDict(Data):
        if Data["Type"] == "Place":
            return PlaceCommand(Data["Player"], Data["Upper"], Data["Lower"],
                                Data["Row"], Data["Col"], Data["Orientation"])
        if Data["Type"] == "Generate":
            return GenerateCommand(Data["Player"], Data.get("Card"))
        if Data["Type"] == "Pass":
            return PassCommand(Data["Player"])
        return None


class PlaceCommand(Command):
    Type = "Place"

    def __init__(self, Player, Upper, Lower, Row, Col, Orientation):
        super().__init__(Player)
        self.Upper = Upper
        self.Lower = Lower
        self.Row = Row
        self.Col = Col
        self.Orientation = Orientation

    def Validate(self, Match):
        Ok, Reason = self.ValidateTurn(Match)
        if not Ok:
            return False, Reason
        if not Match.HasCard(self.Player, self.Upper, self.Lower):
            return False, "Esa ficha no está en la mano"
        Plan, Reason = Match.Board.Evaluate(self.Upper, self.Lower, self.Row, self.Col, self.Orientation)
        if Plan is None:
            return False, Reason
        return True, ""

    def Execute(self, Match):
        Plan, Reason = Match.Board.Evaluate(self.Upper, self.Lower, self.Row, self.Col, self.Orientation)
        PlacedCard = Match.TakeFromHand(self.Player, self.Upper, self.Lower)
        Match.Board.Place(PlacedCard, self.Row, self.Col, self.Orientation, self.Player, Plan)
        Match.Bus.Publish(PiecePlaced, Player = self.Player, Cells = [Item["Pos"] for Item in Plan],
                          Upper = self.Upper, Lower = self.Lower)
        Match.Board.Resolve(Plan, self.Player, Match)
        Match.PassCount = 0
        Match.EndTurn()

    # La ficha colocada es publica, se envia completa
    def ToDict(self, Viewer = None):
        return {"Type": self.Type, "Player": self.Player, "Upper": self.Upper, "Lower": self.Lower,
                "Row": self.Row, "Col": self.Col, "Orientation": self.Orientation}


class GenerateCommand(Command):
    Type = "Generate"

    # CardData es (Arriba, Abajo) o None si el que recibe no debe conocerla
    def __init__(self, Player, CardData = None):
        super().__init__(Player)
        if CardData is not None:
            CardData = (CardData[0], CardData[1])
        self.CardData = CardData

    def Validate(self, Match):
        Ok, Reason = self.ValidateTurn(Match)
        if not Ok:
            return False, Reason
        if Match.Deck.Count() == 0:
            return False, "El mazo está vacío"
        return True, ""

    def Execute(self, Match):
        Drawn = Match.Deck.Draw()
        # Quien tiene el mazo real (local o anfitrion) sabe la ficha, el otro la recibe en el comando
        if self.CardData is None:
            self.CardData = Drawn
        Match.AddCardToHand(self.Player, self.CardData)
        Match.PassCount = 0
        Match.Bus.Publish(CardDrawn, Player = self.Player, DeckCount = Match.Deck.Count())
        Match.EndTurn()

    def ToDict(self, Viewer = None):
        Card = None
        if self.CardData is not None and (Viewer is None or Viewer == self.Player):
            Card = list(self.CardData)
        return {"Type": self.Type, "Player": self.Player, "Card": Card}


# Cuando el mazo se acaba, generar ficha se convierte en pasar turno
class PassCommand(Command):
    Type = "Pass"

    def Validate(self, Match):
        Ok, Reason = self.ValidateTurn(Match)
        if not Ok:
            return False, Reason
        if Match.Deck.Count() > 0:
            return False, "Todavía hay fichas en el mazo"
        return True, ""

    def Execute(self, Match):
        Match.PassCount += 1
        Match.Bus.Publish(TurnPassed, Player = self.Player)
        if Match.PassCount >= 2:
            Match.FinishByDeck()
        else:
            Match.EndTurn()