import pygame
import Network
import UI
from Events import EventBus, GameStarted, GameOver, NetworkError
from Session import Session
from SkyBox import SkyBox
from Hud import Hud
from Telemetry import Telemetry
from Audio import AudioHooks
from States import StateMachine, MenuState, SetupState, MultiState, LobbyState, HowToPlayState, CreditsState
from GameStates import PlayingState, PauseState, PassDeviceState, GameOverState


# Junta todas las piezas: bus de eventos, pantallas, sesion de juego y bucle principal
class App:
    def __init__(self):
        pygame.init()
        self.Screen = pygame.display.set_mode((UI.ScreenWidth, UI.ScreenHeight))
        pygame.display.set_caption("Magick Domino")
        self.Clock = pygame.time.Clock()
        self.Running = True

        self.Bus = EventBus()
        self.Session = None
        self.MenuMessage = ""

        self.SkyBox = SkyBox((UI.ScreenWidth, UI.ScreenHeight))
        self.Hud = Hud(self)
        self.Telemetry = Telemetry(self.Bus)
        self.Audio = AudioHooks(self.Bus)

        self.Machine = StateMachine(self.Bus)
        self.Machine.Add("Menu", MenuState(self))
        self.Machine.Add("Setup", SetupState(self))
        self.Machine.Add("Multi", MultiState(self))
        self.Machine.Add("Lobby", LobbyState(self))
        self.Machine.Add("HowToPlay", HowToPlayState(self))
        self.Machine.Add("Credits", CreditsState(self))
        self.Machine.Add("Playing", PlayingState(self))
        self.Machine.Add("Pause", PauseState(self))
        self.Machine.Add("PassDevice", PassDeviceState(self))
        self.Machine.Add("GameOver", GameOverState(self))

        self.Bus.Subscribe(GameStarted, self.OnGameStarted)
        self.Bus.Subscribe(GameOver, self.OnGameOver)
        self.Bus.Subscribe(NetworkError, self.OnNetworkError)

        self.Machine.Change("Menu")

    # ---------- Reacciones a eventos ----------
    def OnGameStarted(self, Mode):
        self.Machine.Change("Playing")

    def OnGameOver(self, Winner, Reason):
        self.Machine.Change("GameOver", Winner = Winner, Reason = Reason)

    def OnNetworkError(self, Text, Lobby):
        self.CloseNetwork()
        self.MenuMessage = Text
        if Lobby:
            self.Machine.Change("Multi")
        else:
            self.Machine.Change("Menu")

    # ---------- Acciones de las pantallas ----------
    def StartLocal(self):
        self.CloseNetwork()
        self.Session = Session(self.Bus)
        self.Session.StartLocal()

    def HostGame(self):
        self.CloseNetwork()
        Net = Network.Connection()
        Net.Host()
        self.Session = Session(self.Bus, Net)
        self.MenuMessage = ""
        self.Machine.Change("Lobby", Text = "Esperando rival...", Host = True)

    def JoinGame(self, Address):
        self.CloseNetwork()
        Net = Network.Connection()
        Net.Join(Address)
        self.Session = Session(self.Bus, Net)
        self.MenuMessage = ""
        self.Machine.Change("Lobby", Text = "Conectando a " + Address + "...", Host = False)

    def CloseNetwork(self):
        if self.Session is not None:
            self.Session.Close()
        self.Session = None

    def GoToMenu(self):
        self.CloseNetwork()
        self.MenuMessage = ""
        self.Machine.Change("Menu")

    # ---------- Bucle principal ----------
    def Run(self):
        while self.Running:
            for Event in pygame.event.get():
                if Event.type == pygame.QUIT:
                    self.Running = False
                else:
                    self.Machine.Current.HandleEvent(Event)

            if self.Session is not None:
                self.Session.Poll()

            self.Hud.Update()
            self.SkyBox.Update(pygame.time.get_ticks())
            self.Machine.Current.Update()

            self.SkyBox.Draw(self.Screen)
            self.Machine.Current.Draw(self.Screen)
            pygame.display.update()

            self.Clock.tick(60)

        self.CloseNetwork()
        pygame.quit()
