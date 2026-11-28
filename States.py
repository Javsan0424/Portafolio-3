import pygame
import UI
import Network
from Resources import LoadData
from CreateCard import Card, LoadEffect, CELL
from Events import StateChanged


# State: cada pantalla es una clase con Enter, HandleEvent, Update y Draw
class State:
    def __init__(self, App):
        self.App = App

    def Enter(self, **Args):
        pass

    def HandleEvent(self, Event):
        pass

    def Update(self):
        pass

    def Draw(self, Screen):
        pass


# Guarda las pantallas y cambia entre ellas
class StateMachine:
    def __init__(self, Bus):
        self.Bus = Bus
        self.States = {}
        self.Current = None
        self.CurrentName = ""

    def Add(self, Name, StateObject):
        self.States[Name] = StateObject

    def Change(self, Name, **Args):
        self.Current = self.States[Name]
        self.CurrentName = Name
        self.Current.Enter(**Args)
        self.Bus.Publish(StateChanged, Name = Name)


def LeftClick(Event):
    return Event.type == pygame.MOUSEBUTTONDOWN and Event.button == 1


class MenuState(State):
    def __init__(self, App):
        super().__init__(App)
        self.Buttons = [("Jugar", pygame.Rect(500, 390, 200, 56)),
                        ("Cómo jugar", pygame.Rect(500, 460, 200, 56)),
                        ("Créditos", pygame.Rect(500, 530, 200, 56)),
                        ("Salir", pygame.Rect(500, 600, 200, 56))]

    def HandleEvent(self, Event):
        if not LeftClick(Event):
            return
        for Item in self.Buttons:
            if Item[1].collidepoint(Event.pos):
                self.App.MenuMessage = ""
                if Item[0] == "Jugar":
                    self.App.Machine.Change("Setup", Mode = "Local")
                elif Item[0] == "Cómo jugar":
                    self.App.Machine.Change("HowToPlay")
                elif Item[0] == "Créditos":
                    self.App.Machine.Change("Credits")
                elif Item[0] == "Salir":
                    self.App.Running = False

    def Draw(self, Screen):
        UI.DrawOverlay(Screen)
        UI.DrawCentered(Screen, "Magick Domino", UI.BigFont, "white", 190)
        UI.DrawCentered(Screen, "Dominó de efectos para dos jugadores", UI.Font, "white", 270)
        if self.App.MenuMessage != "":
            UI.DrawCentered(Screen, self.App.MenuMessage, UI.Font, "yellow", 325)
        for Item in self.Buttons:
            UI.DrawButton(Screen, Item[1], Item[0])


# Configuracion de partida: modalidad y numero de jugadores
class SetupState(State):
    def __init__(self, App):
        super().__init__(App)
        self.Mode = "Local"
        self.Players = 2
        self.LocalButton = pygame.Rect(400, 250, 190, 50)
        self.OnlineButton = pygame.Rect(610, 250, 190, 50)
        self.PlayerButtons = [(2, pygame.Rect(400, 370, 120, 50)),
                              (3, pygame.Rect(540, 370, 120, 50)),
                              (4, pygame.Rect(680, 370, 120, 50))]
        self.ContinueButton = pygame.Rect(500, 520, 200, 56)
        self.BackButton = pygame.Rect(500, 590, 200, 56)

    def Enter(self, Mode = "Local"):
        self.Mode = Mode
        self.Players = 2

    def HandleEvent(self, Event):
        if not LeftClick(Event):
            return
        if self.LocalButton.collidepoint(Event.pos):
            self.Mode = "Local"
        elif self.OnlineButton.collidepoint(Event.pos):
            self.Mode = "Online"
        elif self.ContinueButton.collidepoint(Event.pos):
            if self.Mode == "Local":
                self.App.StartLocal()
            else:
                self.App.Machine.Change("Multi")
        elif self.BackButton.collidepoint(Event.pos):
            self.App.Machine.Change("Menu")

        # Solo esta habilitado el modo de 2 jugadores
        for Item in self.PlayerButtons:
            if Item[0] == 2 and Item[1].collidepoint(Event.pos):
                self.Players = 2

    def Draw(self, Screen):
        UI.DrawOverlay(Screen)
        UI.DrawCentered(Screen, "Configuración de partida", UI.TitleFont, "white", 130)

        UI.DrawCentered(Screen, "Modalidad", UI.Font, "yellow", 220)
        UI.DrawButton(Screen, self.LocalButton, "Local", True, self.Mode == "Local")
        UI.DrawButton(Screen, self.OnlineButton, "En línea", True, self.Mode == "Online")
        if self.Mode == "Local":
            UI.DrawCentered(Screen, "Dos jugadores en el mismo dispositivo", UI.SmallFont, "white", 325)
        else:
            UI.DrawCentered(Screen, "Dos dispositivos conectados por red (uno crea la partida y otro se une)", UI.SmallFont, "white", 325)

        UI.DrawCentered(Screen, "Número de jugadores", UI.Font, "yellow", 345)
        for Item in self.PlayerButtons:
            Enabled = Item[0] == 2
            UI.DrawButton(Screen, Item[1], str(Item[0]), Enabled, Item[0] == self.Players)
        UI.DrawCentered(Screen, "Por ahora solo está disponible el modo de 2 jugadores", UI.SmallFont, "white", 445)

        UI.DrawButton(Screen, self.ContinueButton, "Continuar")
        UI.DrawButton(Screen, self.BackButton, "Volver")


class MultiState(State):
    def __init__(self, App):
        super().__init__(App)
        self.IPText = "127.0.0.1"
        self.IPBox = pygame.Rect(450, 320, 300, 45)
        self.HostButton = pygame.Rect(500, 400, 200, 60)
        self.JoinButton = pygame.Rect(500, 480, 200, 60)
        self.BackButton = pygame.Rect(500, 560, 200, 60)

    def HandleEvent(self, Event):
        if Event.type == pygame.KEYDOWN:
            if Event.key == pygame.K_BACKSPACE:
                self.IPText = self.IPText[:-1]
            elif Event.unicode != "" and Event.unicode.isprintable() and len(self.IPText) < 25:
                self.IPText += Event.unicode

        if LeftClick(Event):
            if self.HostButton.collidepoint(Event.pos):
                self.App.HostGame()
            elif self.JoinButton.collidepoint(Event.pos):
                self.App.JoinGame(self.IPText.strip())
            elif self.BackButton.collidepoint(Event.pos):
                self.App.MenuMessage = ""
                self.App.Machine.Change("Setup", Mode = "Online")

    def Draw(self, Screen):
        UI.DrawOverlay(Screen)
        UI.DrawCentered(Screen, "Multijugador", UI.BigFont, "white", 160)
        UI.DrawCentered(Screen, "IP del anfitrión (para unirte)", UI.SmallFont, "white", 300)

        pygame.draw.rect(Screen, (35, 30, 45), self.IPBox, border_radius=8)
        pygame.draw.rect(Screen, "white", self.IPBox, 2, border_radius=8)
        Cursor = ""
        if (pygame.time.get_ticks() // 500) % 2 == 0:
            Cursor = "|"
        IPLabel = UI.Font.render(self.IPText + Cursor, True, "white")
        Screen.blit(IPLabel, IPLabel.get_rect(midleft = (self.IPBox.x + 10, self.IPBox.centery)))

        if self.App.MenuMessage != "":
            UI.DrawCentered(Screen, self.App.MenuMessage, UI.SmallFont, "yellow", 385)
        UI.DrawButton(Screen, self.HostButton, "Crear partida")
        UI.DrawButton(Screen, self.JoinButton, "Unirse")
        UI.DrawButton(Screen, self.BackButton, "Volver")


class LobbyState(State):
    def __init__(self, App):
        super().__init__(App)
        self.Text = ""
        self.IsHost = False
        self.HostIP = ""
        self.CancelButton = pygame.Rect(500, 520, 200, 60)

    def Enter(self, Text = "", Host = False):
        self.Text = Text
        self.IsHost = Host
        if Host:
            self.HostIP = Network.GetLocalIP()

    def HandleEvent(self, Event):
        if LeftClick(Event) and self.CancelButton.collidepoint(Event.pos):
            self.App.CloseNetwork()
            self.App.Machine.Change("Multi")

    def Draw(self, Screen):
        UI.DrawOverlay(Screen)
        UI.DrawCentered(Screen, "Multijugador", UI.BigFont, "white", 220)
        UI.DrawCentered(Screen, self.Text, UI.Font, "white", 340)
        if self.IsHost:
            UI.DrawCentered(Screen, "Comparte tu IP: " + self.HostIP + "  (puerto " + str(Network.DefaultPort) + ")", UI.Font, "yellow", 400)
        UI.DrawButton(Screen, self.CancelButton, "Cancelar")


# Tutorial de 4 paginas
class HowToPlayState(State):
    def __init__(self, App):
        super().__init__(App)
        self.Page = 0
        self.PageCount = 4
        self.PrevButton = pygame.Rect(300, 710, 150, 50)
        self.NextButton = pygame.Rect(750, 710, 150, 50)
        self.MenuButton = pygame.Rect(525, 710, 150, 50)
        self.Sample = None

    def Enter(self):
        self.Page = 0
        if self.Sample is None:
            self.Sample = Card("Fire", "Poison")

    def Move(self, Step):
        self.Page = max(0, min(self.PageCount - 1, self.Page + Step))

    def HandleEvent(self, Event):
        if Event.type == pygame.KEYDOWN:
            if Event.key == pygame.K_RIGHT:
                self.Move(1)
            elif Event.key == pygame.K_LEFT:
                self.Move(-1)
            elif Event.key == pygame.K_ESCAPE:
                self.App.Machine.Change("Menu")

        if LeftClick(Event):
            if self.PrevButton.collidepoint(Event.pos):
                self.Move(-1)
            elif self.NextButton.collidepoint(Event.pos):
                self.Move(1)
            elif self.MenuButton.collidepoint(Event.pos):
                self.App.Machine.Change("Menu")

    def DrawTexts(self, Screen, Texts, Y):
        for Text in Texts:
            Y = UI.DrawWrapped(Screen, Text, UI.BodyFont, "white", 150, Y, 900, 25) + 10
        return Y

    def Draw(self, Screen):
        UI.DrawOverlay(Screen, 200)
        Titles = ["Las fichas", "Encadenar y cortar", "Los 4 efectos", "Turnos y controles"]
        UI.DrawCentered(Screen, Titles[self.Page], UI.TitleFont, "yellow", 70)
        UI.DrawCentered(Screen, "Página " + str(self.Page + 1) + " de " + str(self.PageCount), UI.SmallFont, "white", 115)

        if self.Page == 0:
            self.DrawPageTiles(Screen)
        elif self.Page == 1:
            self.DrawPageChain(Screen)
        elif self.Page == 2:
            self.DrawPageEffects(Screen)
        else:
            self.DrawPageControls(Screen)

        UI.DrawButton(Screen, self.PrevButton, "Anterior", self.Page > 0)
        UI.DrawButton(Screen, self.NextButton, "Siguiente", self.Page < self.PageCount - 1)
        UI.DrawButton(Screen, self.MenuButton, "Menú")

    def DrawPageTiles(self, Screen):
        Screen.blit(pygame.transform.scale(self.Sample.DominoPiece, (CELL * 2, CELL * 4)), (150, 170))
        UI.DrawWrapped(Screen, "Mitad de arriba (F)", UI.SmallFont, "white", 260, 185, 300)
        UI.DrawWrapped(Screen, "Mitad de abajo (V)", UI.SmallFont, "white", 260, 340, 300)
        Y = 190
        for Text in ["Cada ficha es un dominó con dos mitades y cada mitad lleva un efecto: Fuego (F), Veneno (V), Impacto (I) o Drenar (D). La letra siempre aparece sobre la ficha.",
                     "Empiezas con 7 fichas. El mazo tiene 32 fichas: las 16 combinaciones de arriba y abajo, dos veces cada una. El contador del mazo está en el panel izquierdo.",
                     "En tu turno haces UNA acción: poner una ficha en el tablero o generar una ficha del mazo. Después el turno pasa al rival.",
                     "Gana quien deje la vida del rival en 0."]:
            Y = UI.DrawWrapped(Screen, Text, UI.BodyFont, "white", 420, Y, 640, 25) + 14

    def DrawPageChain(self, Screen):
        Y = self.DrawTexts(Screen, [
            "Una ficha nueva debe tocar otra ficha del tablero. La primera ficha puede ir en cualquier lugar.",
            "ENCADENAR: si una mitad toca el mismo efecto, sube el nivel de la cadena (x2, x3...) y el efecto pega más fuerte.",
            "CORTAR: solo la mitad de ABAJO puede cortar, y lo hace tocando el efecto contrario. El efecto cortado se cancela (se marca con una X) y esa mitad no hace daño. Gira la ficha con R hasta que su mitad de abajo (la de la letra inferior) quede junto al efecto que quieres cortar.",
            "Si la mitad de arriba toca un efecto contrario, o cualquier mitad toca un efecto que no es igual ni contrario, la jugada no es válida."], 150)

        Fire = LoadEffect("Fire")
        Poison = LoadEffect("Poison")
        Screen.blit(Fire, (250, 470))
        Screen.blit(Fire, (250 + CELL, 470))
        UI.DrawWrapped(Screen, "Encadenar: Fuego junto a Fuego", UI.BodyFont, "white", 200, 530, 300)

        Screen.blit(Fire, (700, 470))
        Screen.blit(Poison, (700 + CELL, 470))
        UI.DrawWrapped(Screen, "Cortar: Veneno (mitad de abajo) toca Fuego", UI.BodyFont, "white", 650, 530, 360)

    def DrawPageEffects(self, Screen):
        Items = [("Fire", "F  Fuego: daño explosivo al colocar (12) que baja 4 por turno hasta apagarse."),
                 ("Poison", "V  Veneno: sin daño inmediato; después 1, 2, 3... por turno durante 5 turnos."),
                 ("Impact", "I  Impacto: daño fijo de 6. Escala mejor al encadenar (+5 por nivel)."),
                 ("Drain", "D  Drenar: daño de 3 (+2 por nivel) y te curas lo mismo.")]
        Y = 150
        for Item in Items:
            Screen.blit(LoadEffect(Item[0]), (150, Y - 6))
            UI.DrawWrapped(Screen, Item[1], UI.BodyFont, "white", 215, Y, 840, 25)
            Y += 58

        Y = 400
        Screen.blit(UI.Font.render("¿Por qué son contrarios?", True, "yellow"), (150, Y))
        self.DrawTexts(Screen, [
            "Fuego vs Veneno: son opuestos en el tiempo. El fuego es daño rápido que se apaga, el veneno es daño lento que crece. En el juego el fuego quema el veneno y por eso lo corta.",
            "Impacto vs Drenar: son opuestos en la dirección de la vida. El impacto solo golpea, el drenar absorbe y devuelve vida. Un golpe seco rompe la absorción, y por eso se cortan."], Y + 35)

    def DrawPageControls(self, Screen):
        Texts = ["Turnos: el turno 1 es del Jugador 1 y los impares son suyos. El Jugador 2 juega los turnos pares.",
                 "Clic izquierdo: elegir una ficha y colocarla en el tablero. Clic otra vez sobre la ficha elegida: soltarla.",
                 "R o clic derecho: rotar la ficha en 4 posiciones (así la mitad de abajo puede quedar arriba, abajo, a la izquierda o a la derecha). Esc: pausa.",
                 "Si el mazo se acaba, el botón pasa a ser Pasar turno. Si los dos jugadores pasan seguidos, gana quien tenga más vida (si hay empate, es empate).",
                 "En local aparece una pantalla para pasar el dispositivo y que no se vea tu mano. En línea solo ves tu mano.",
                 "En el panel izquierdo ves los efectos activos (Fuego y Veneno) con su valor y los turnos que les quedan."]
        self.DrawTexts(Screen, Texts, 150)


class CreditsState(State):
    def __init__(self, App):
        super().__init__(App)
        self.BackButton = pygame.Rect(500, 700, 200, 56)

    def HandleEvent(self, Event):
        if LeftClick(Event) and self.BackButton.collidepoint(Event.pos):
            self.App.Machine.Change("Menu")
        if Event.type == pygame.KEYDOWN and Event.key == pygame.K_ESCAPE:
            self.App.Machine.Change("Menu")

    def Draw(self, Screen):
        UI.DrawOverlay(Screen, 200)
        UI.DrawCentered(Screen, "Créditos y fuentes", UI.TitleFont, "yellow", 70)

        Credits = LoadData()["Credits"]
        Sections = [("Assets propios", Credits["Own"]),
                    ("Assets de terceros", Credits["ThirdParty"]),
                    ("Contenido generado con IA", Credits["AI"])]
        Y = 130
        for Section in Sections:
            Screen.blit(UI.Font.render(Section[0], True, "yellow"), (120, Y))
            Y += 34
            for Line in Section[1]:
                Y = UI.DrawWrapped(Screen, "- " + Line, UI.BodyFont, "white", 140, Y, 940, 24)
            Y += 18
        UI.DrawButton(Screen, self.BackButton, "Volver")