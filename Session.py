from Events import InvalidMove, NetworkError
from Match import Match
from Commands import Command


# Une la partida con la red.
# - Local: ejecuta los comandos directo.
# - En linea el anfitrion es la autoridad: tiene el mazo real, valida y ejecuta todas las jugadas,
#   y le manda al cliente cada jugada ya ejecutada (sin revelar las fichas que no le tocan).
# - El cliente solo pide jugadas (Request) y las ejecuta cuando el anfitrion las confirma.
class Session:
    def __init__(self, Bus, Net = None):
        self.Bus = Bus
        self.Net = Net
        self.Match = None
        self.Pending = False        # el cliente espera respuesta del anfitrion
        self.RematchLocal = False
        self.RematchRemote = False
        self.RivalLeft = False
        self.Dead = False
        self.Role = "local"
        if Net is not None:
            self.Role = Net.Role

    def IsHost(self):
        return self.Role == "host"

    def ResetFlags(self):
        self.Pending = False
        self.RematchLocal = False
        self.RematchRemote = False

    # ---------- Inicio ----------
    def StartLocal(self):
        self.Match = Match(self.Bus, "Local", None, True)
        self.Match.DealNewGame()

    def StartOnlineAsHost(self):
        self.ResetFlags()
        self.Match = Match(self.Bus, "Online", 0, True)
        self.Match.DealNewGame()
        # Al cliente solo se le manda SU mano y cuantas fichas quedan en el mazo
        ClientHand = [[Item.UpperEffect, Item.LowerEffect] for Item in self.Match.Players[1].Hand]
        self.Net.Send({"Type": "Start", "Hand": ClientHand, "DeckCount": self.Match.Deck.Count()})

    def OnStart(self, Data):
        self.ResetFlags()
        self.Match = Match(self.Bus, "Online", 1, False)
        self.Match.LoadStart(Data["Hand"], Data["DeckCount"])

    # ---------- Jugadas locales de la UI ----------
    def Submit(self, Command):
        if self.Match.Mode == "Local":
            return self.Match.TryExecute(Command)

        if self.IsHost():
            Ok, Reason = self.Match.TryExecute(Command)
            if Ok:
                self.Net.Send({"Type": "Command", "Data": Command.ToDict(Viewer = 1)})
            return Ok, Reason

        # Cliente: valida localmente y pide la jugada al anfitrion
        Ok, Reason = self.Match.Validate(Command)
        if Ok:
            self.Net.Send({"Type": "Request", "Data": Command.ToDict()})
            self.Pending = True
        return Ok, Reason

    # ---------- Revancha ----------
    def RequestRematch(self):
        self.RematchLocal = True
        self.Net.Send({"Type": "Rematch"})
        self.TryRematch()

    def TryRematch(self):
        if self.IsHost() and self.RematchLocal and self.RematchRemote:
            self.StartOnlineAsHost()

    # ---------- Mensajes recibidos (se llama una vez por cuadro) ----------
    def Poll(self):
        if self.Net is None:
            return

        while not self.Dead and not self.Net.Inbox.empty():
            Data = self.Net.Inbox.get()
            Type = Data["Type"]

            if Type == "Connected":
                if self.IsHost():
                    self.StartOnlineAsHost()
            elif Type == "Start":
                self.OnStart(Data)
            elif Type == "Request":
                self.OnRequest(Data)
            elif Type == "Command":
                self.OnCommand(Data)
            elif Type == "Reject":
                self.Pending = False
                self.Bus.Publish(InvalidMove, Player = self.Match.LocalIndex, Reason = Data["Reason"])
            elif Type == "Rematch":
                self.RematchRemote = True
                self.TryRematch()
            elif Type == "Error":
                self.Bus.Publish(NetworkError, Text = "No se pudo conectar: " + Data["Text"], Lobby = self.Match is None)
            elif Type == "Disconnected":
                self.OnDisconnected()

    # Anfitrion: el cliente pide una jugada
    def OnRequest(self, Data):
        if self.Match is None or not self.IsHost():
            return
        Cmd = Command.FromDict(Data["Data"])
        if Cmd is None or Cmd.Player != 1:
            self.Net.Send({"Type": "Reject", "Reason": "Jugada no reconocida"})
            return

        Ok, Reason = self.Match.TryExecute(Cmd)
        if Ok:
            self.Net.Send({"Type": "Command", "Data": Cmd.ToDict(Viewer = 1)})
        else:
            self.Net.Send({"Type": "Reject", "Reason": Reason})

    # Cliente: el anfitrion confirma una jugada ya ejecutada
    def OnCommand(self, Data):
        if self.Match is None or self.IsHost() or self.Match.Over:
            return
        Cmd = Command.FromDict(Data["Data"])
        if Cmd is not None and Cmd.Player == self.Match.LocalIndex:
            self.Pending = False

        Ok = False
        Reason = "Jugada no reconocida"
        if Cmd is not None:
            Ok, Reason = self.Match.TryExecute(Cmd)
        if not Ok:
            # Un comando valido para el anfitrion no deberia fallar aqui: el estado se desincronizo
            self.Bus.Publish(NetworkError, Text = "Partida desincronizada (" + Reason + ")", Lobby = False)

    def OnDisconnected(self):
        if self.Match is None:
            self.Bus.Publish(NetworkError, Text = "Se perdió la conexión", Lobby = True)
        elif not self.Match.Over:
            # Gana el jugador que se queda
            self.Match.Forfeit(1 - self.Match.LocalIndex)
            self.RivalLeft = True
        else:
            self.RivalLeft = True

    def Close(self):
        self.Dead = True
        if self.Net is not None:
            self.Net.Close()
