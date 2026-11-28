import pygame
import UI
from States import State, LeftClick
from CreateCard import CELL
from Board import GridRect
from Commands import PlaceCommand, GenerateCommand, PassCommand
from Events import GameStarted, TurnChanged

BarWidth = 1200
BarHeight = 30
CardSpeed = 0.12
CardSpacing = 64

BottomHandRect = pygame.Rect(150, 650, 900, 110)
TopHandRect = pygame.Rect(150, 40, 900, 110)
LeftPanel = pygame.Rect(10, 184, 244, 432)
RightPanel = pygame.Rect(946, 184, 244, 432)


class PlayingState(State):
    def __init__(self, App):
        super().__init__(App)
        self.Selected = None
        self.Orientation = 0
        self.PendingPass = False
        self.DisplayHealth = [100, 100]
        self.GenerateButton = pygame.Rect(20, 340, 224, 52)

        App.Bus.Subscribe(GameStarted, self.OnGameStarted)
        App.Bus.Subscribe(TurnChanged, self.OnTurnChanged)

    def GetMatch(self):
        return self.App.Session.Match

    def OnGameStarted(self, Mode):
        self.Selected = None
        self.Orientation = 0
        self.PendingPass = False
        self.DisplayHealth = [100, 100]
        self.App.Hud.Clear()

    def OnTurnChanged(self, Turn, Player):
        self.Selected = None
        # En local, entre turnos se muestra la pantalla de pasar el dispositivo
        if Turn > 1 and self.GetMatch().Mode == "Local":
            self.PendingPass = True

    def HandRectOf(self, Index):
        if Index == self.GetMatch().BottomIndex():
            return BottomHandRect
        return TopHandRect

    # ---------- Entrada ----------
    def CardUnderMouse(self, MousePos):
        Match = self.GetMatch()
        Hand = Match.Players[Match.CurrentIndex()].Hand
        for i in range(len(Hand) - 1, -1, -1):
            CardRect = pygame.Rect(int(Hand[i].Pos[0]), int(Hand[i].Pos[1]), CELL, CELL * 2)
            if CardRect.collidepoint(MousePos):
                return Hand[i]
        return None

    def HandleEvent(self, Event):
        Session = self.App.Session
        Match = Session.Match

        if Event.type == pygame.KEYDOWN and Event.key == pygame.K_ESCAPE:
            self.App.Machine.Change("Pause")
            return

        if Match.Over or not Match.IsMyTurn() or Session.Pending:
            return

        if Event.type == pygame.KEYDOWN and Event.key == pygame.K_r:
            self.Orientation = (self.Orientation + 1) % 4

        if Event.type == pygame.MOUSEBUTTONDOWN:
            if Event.button == 3:
                self.Orientation = (self.Orientation + 1) % 4

            if Event.button == 1:
                Clicked = self.CardUnderMouse(Event.pos)
                if Clicked is not None:
                    # Clic en la ficha elegida la suelta
                    if Clicked is self.Selected:
                        self.Selected = None
                    else:
                        self.Selected = Clicked
                    self.App.Hud.Message = None
                elif self.GenerateButton.collidepoint(Event.pos):
                    self.GenerateOrPass()
                elif self.Selected is not None and GridRect.collidepoint(Event.pos):
                    self.TryPlace(Event.pos)

    def GenerateOrPass(self):
        Match = self.GetMatch()
        Index = Match.CurrentIndex()
        if Match.Deck.Count() > 0:
            Command = GenerateCommand(Index)
        else:
            Command = PassCommand(Index)
        self.App.Session.Submit(Command)

    def TryPlace(self, MousePos):
        Match = self.GetMatch()
        Col = (MousePos[0] - GridRect.x) // CELL
        Row = (MousePos[1] - GridRect.y) // CELL
        Command = PlaceCommand(Match.CurrentIndex(), self.Selected.UpperEffect, self.Selected.LowerEffect,
                               int(Row), int(Col), self.Orientation)
        Ok, Reason = self.App.Session.Submit(Command)
        if Ok:
            self.Selected = None

    # ---------- Actualizar ----------
    def Update(self):
        Match = self.GetMatch()
        for i in range(2):
            self.DisplayHealth[i] += (Match.Players[i].currentHealth - self.DisplayHealth[i]) * 0.1

        if self.PendingPass:
            self.PendingPass = False
            if not Match.Over:
                self.App.Machine.Change("PassDevice")

    # ---------- Dibujo ----------
    def Draw(self, Screen, ShowHands = True):
        Match = self.GetMatch()

        self.DrawBars(Screen, Match)

        # Grid donde van las fichas
        pygame.draw.rect(Screen, (15, 70, 35), GridRect)
        for i in range(0, GridRect.width + 1, CELL):
            pygame.draw.line(Screen, (30, 100, 55), (GridRect.x + i, GridRect.y), (GridRect.x + i, GridRect.bottom))
        for i in range(0, GridRect.height + 1, CELL):
            pygame.draw.line(Screen, (30, 100, 55), (GridRect.x, GridRect.y + i), (GridRect.right, GridRect.y + i))
        pygame.draw.rect(Screen, "white", GridRect, 2)

        Match.Board.Draw(Screen)

        self.DrawHand(Screen, Match, 1, ShowHands)
        self.DrawHand(Screen, Match, 0, ShowHands)

        HoverReason = ""
        if ShowHands:
            HoverReason = self.DrawGhost(Screen, Match)
        self.DrawSidePanels(Screen, Match)

        Status = HoverReason
        if Status == "":
            Status = self.App.Hud.CurrentMessage()
        if Status != "":
            StatusText = UI.Font.render(Status, True, "yellow")
            Screen.blit(StatusText, StatusText.get_rect(center = (GridRect.centerx, 633)))

        self.App.Hud.Draw(Screen)

    def DrawBars(self, Screen, Match):
        Bottom = Match.BottomIndex()
        Top = 1 - Bottom

        for Item in ((Top, 0), (Bottom, 770)):
            Who = Match.Players[Item[0]]
            Width = int(BarWidth * self.DisplayHealth[Item[0]] / Who.maxHealt)
            if Item[1] == 0:
                # Barra de arriba: se acorta de izquierda a derecha
                pygame.draw.rect(Screen, "red", (BarWidth - Width, 0, Width, BarHeight))
            else:
                # Barra de abajo: se acorta de derecha a izquierda
                pygame.draw.rect(Screen, "red", (0, 770, Width, BarHeight))

            Text = UI.PlayerTags[Item[0]] + "  " + str(int(Who.currentHealth)) + " / " + str(Who.maxHealt)
            Label = UI.Font.render(Text, True, "white")
            Screen.blit(Label, Label.get_rect(center = (BarWidth // 2, Item[1] + BarHeight // 2)))

    def DrawHand(self, Screen, Match, Index, ShowHands):
        Hand = Match.Players[Index].Hand
        Rect = self.HandRectOf(Index)

        UI.DrawPanel(Screen, Rect, UI.PlayerColors[Index])

        # Etiqueta a la izquierda de la mano
        Tag = UI.Font.render(UI.PlayerTags[Index], True, UI.PlayerColors[Index])
        Screen.blit(Tag, (16, Rect.centery - 30))
        Count = UI.SmallFont.render(str(len(Hand)) + " fichas", True, "white")
        Screen.blit(Count, (16, Rect.centery - 2))

        if len(Hand) == 0:
            return

        Spacing = CardSpacing
        if len(Hand) > 1:
            Spacing = min(CardSpacing, (Rect.width - 20 - CELL) / (len(Hand) - 1))

        HandWidth = (len(Hand) - 1) * Spacing + CELL
        StartX = Rect.centerx - HandWidth / 2
        TargetY = Rect.y + (Rect.height - CELL * 2) / 2

        for i in range(len(Hand)):
            Hand[i].Pos[0] += (StartX + i * Spacing - Hand[i].Pos[0]) * CardSpeed
            Hand[i].Pos[1] += (TargetY - Hand[i].Pos[1]) * CardSpeed

            CardRect = pygame.Rect(int(Hand[i].Pos[0]), int(Hand[i].Pos[1]), CELL, CELL * 2)
            if ShowHands and Index == Match.FaceUpIndex() and not Hand[i].Hidden:
                Screen.blit(Hand[i].DominoPiece, CardRect)
                if Hand[i] is self.Selected:
                    pygame.draw.rect(Screen, "yellow", CardRect, 3)
            else:
                # Carta boca abajo
                pygame.draw.rect(Screen, (90, 40, 110), CardRect)
                pygame.draw.rect(Screen, "white", CardRect, 2)

    def DrawGhost(self, Screen, Match):
        if self.Selected is None or not Match.IsMyTurn():
            return ""
        MousePos = pygame.mouse.get_pos()
        if not GridRect.collidepoint(MousePos):
            return ""

        Col = (MousePos[0] - GridRect.x) // CELL
        Row = (MousePos[1] - GridRect.y) // CELL
        Plan, Reason = Match.Board.Evaluate(self.Selected.UpperEffect, self.Selected.LowerEffect,
                                            Row, Col, self.Orientation)

        Surf = self.Selected.GetSurface(self.Orientation).copy()
        Tint = pygame.Surface(Surf.get_size(), pygame.SRCALPHA)
        if Plan is None:
            Tint.fill((255, 0, 0, 110))
        else:
            Tint.fill((0, 255, 0, 70))
        Surf.blit(Tint, (0, 0))
        Surf.set_alpha(200)
        Screen.blit(Surf, (GridRect.x + Col * CELL, GridRect.y + Row * CELL))
        return Reason

    def DrawSidePanels(self, Screen, Match):
        Index = Match.CurrentIndex()

        for PanelRect in (LeftPanel, RightPanel):
            UI.DrawPanel(Screen, PanelRect, UI.PlayerColors[Index])

        # Contador del mazo
        DeckText = "Mazo: " + str(Match.Deck.Count()) + " fichas"
        if Match.Deck.Count() == 0:
            DeckText = "Mazo vacío"
        Screen.blit(UI.SmallFont.render(DeckText, True, "white"), (22, 194))

        Screen.blit(UI.Font.render("Turno " + str(Match.Turn), True, "white"), (22, 220))
        Text = UI.Font.render("Juega: " + UI.PlayerTags[Index], True, UI.PlayerColors[Index])
        Screen.blit(Text, (22, 252))

        if Match.Mode == "Online":
            Text = UI.SmallFont.render("Eres " + UI.PlayerTags[Match.LocalIndex], True, UI.PlayerColors[Match.LocalIndex])
            Screen.blit(Text, (22, 286))
            if Match.IsMyTurn():
                Text = UI.SmallFont.render("Es tu turno", True, "yellow")
            else:
                Text = UI.SmallFont.render("Esperando al rival...", True, "white")
            Screen.blit(Text, (22, 308))

        ButtonText = "Generar ficha"
        if Match.Deck.Count() == 0:
            ButtonText = "Pasar turno"
        Enabled = Match.IsMyTurn() and not self.App.Session.Pending and not Match.Over
        UI.DrawButton(Screen, self.GenerateButton, ButtonText, Enabled)

        self.App.Hud.DrawEffects(Screen, Match, 22, 410)

        Lines = ["Controles",
                 "Clic izq - elegir / colocar",
                 "R - rotar",
                 "Clic der - rotar",
                 "Esc - pausa",
                 "",
                 "Efectos",
                 "F Fuego - explosión que decae",
                 "V Veneno - daño acumulativo",
                 "I Impacto - daño fijo",
                 "D Drenar - daño y cura",
                 "",
                 "Reglas",
                 "Encadenar - mismo efecto",
                 "Cortar - efecto de abajo",
                 "contra su contrario",
                 "Fuego - Veneno",
                 "Impacto - Drenar"]
        for i in range(len(Lines)):
            Color = "white"
            if Lines[i] == "Controles" or Lines[i] == "Efectos" or Lines[i] == "Reglas":
                Color = "yellow"
            Line = UI.SmallFont.render(Lines[i], True, Color)
            Screen.blit(Line, (960, 198 + i * 22))


class PauseState(State):
    def __init__(self, App):
        super().__init__(App)
        self.ResumeButton = pygame.Rect(500, 340, 200, 60)
        self.RestartButton = pygame.Rect(500, 420, 200, 60)
        self.QuitButton = pygame.Rect(500, 500, 200, 60)
        self.QuitOnlineButton = pygame.Rect(500, 420, 200, 60)

    def IsOnline(self):
        return self.App.Session.Match.Mode == "Online"

    def HandleEvent(self, Event):
        if Event.type == pygame.KEYDOWN and Event.key == pygame.K_ESCAPE:
            self.App.Machine.Change("Playing")

        if LeftClick(Event):
            if self.ResumeButton.collidepoint(Event.pos):
                self.App.Machine.Change("Playing")
            elif not self.IsOnline() and self.RestartButton.collidepoint(Event.pos):
                self.App.StartLocal()
            elif not self.IsOnline() and self.QuitButton.collidepoint(Event.pos):
                self.App.GoToMenu()
            elif self.IsOnline() and self.QuitOnlineButton.collidepoint(Event.pos):
                self.App.GoToMenu()

    def Draw(self, Screen):
        self.App.Machine.States["Playing"].Draw(Screen)
        UI.DrawOverlay(Screen)
        UI.DrawCentered(Screen, "Pausa", UI.BigFont, "white", 220)
        UI.DrawButton(Screen, self.ResumeButton, "Continuar")
        if self.IsOnline():
            UI.DrawButton(Screen, self.QuitOnlineButton, "Salir al menú")
            UI.DrawCentered(Screen, "En línea la partida sigue para el rival", UI.SmallFont, "yellow", 520)
        else:
            UI.DrawButton(Screen, self.RestartButton, "Reiniciar")
            UI.DrawButton(Screen, self.QuitButton, "Menú principal")


# Pantalla entre turnos en local: oculta el tablero y las manos hasta que el siguiente jugador este listo
class PassDeviceState(State):
    def __init__(self, App):
        super().__init__(App)
        self.Player = 0
        self.ReadyButton = pygame.Rect(500, 450, 200, 60)

    def Enter(self):
        self.Player = self.App.Session.Match.CurrentIndex()

    def HandleEvent(self, Event):
        if LeftClick(Event) and self.ReadyButton.collidepoint(Event.pos):
            self.App.Machine.Change("Playing")
        if Event.type == pygame.KEYDOWN and Event.key == pygame.K_RETURN:
            self.App.Machine.Change("Playing")

    def Draw(self, Screen):
        UI.DrawOverlay(Screen, 245)
        Name = self.App.Session.Match.Players[self.Player].Name
        UI.DrawCentered(Screen, "Pasa el dispositivo a", UI.TitleFont, "white", 260)
        UI.DrawCentered(Screen, Name, UI.BigFont, UI.PlayerColors[self.Player], 350)
        UI.DrawButton(Screen, self.ReadyButton, "Estoy listo")


class GameOverState(State):
    def __init__(self, App):
        super().__init__(App)
        self.Winner = None
        self.Reason = ""
        self.AgainButton = pygame.Rect(500, 480, 200, 60)
        self.MenuButton = pygame.Rect(500, 560, 200, 60)

    def Enter(self, Winner = None, Reason = ""):
        self.Winner = Winner
        self.Reason = Reason

    def HandleEvent(self, Event):
        if not LeftClick(Event):
            return
        Session = self.App.Session
        Online = Session.Match.Mode == "Online"

        if self.MenuButton.collidepoint(Event.pos):
            self.App.GoToMenu()
        elif self.AgainButton.collidepoint(Event.pos):
            if not Online:
                self.App.StartLocal()
            elif not Session.RivalLeft and not Session.RematchLocal:
                Session.RequestRematch()

    def Draw(self, Screen):
        Session = self.App.Session
        Online = Session.Match.Mode == "Online"

        self.App.Machine.States["Playing"].Draw(Screen, False)
        UI.DrawOverlay(Screen)
        UI.DrawCentered(Screen, "Fin del juego", UI.BigFont, "white", 210)

        if self.Winner is None:
            UI.DrawCentered(Screen, "Empate", UI.BigFont, "white", 300)
        else:
            UI.DrawCentered(Screen, "Gana " + Session.Match.Players[self.Winner].Name, UI.BigFont, UI.PlayerColors[self.Winner], 300)
        UI.DrawCentered(Screen, self.Reason, UI.Font, "yellow", 375)

        if not Online:
            UI.DrawButton(Screen, self.AgainButton, "Jugar de nuevo")
        else:
            if Session.RivalLeft:
                UI.DrawButton(Screen, self.AgainButton, "Revancha", False)
                UI.DrawCentered(Screen, "El rival ya no está conectado", UI.SmallFont, "white", 450)
            elif Session.RematchLocal:
                UI.DrawButton(Screen, self.AgainButton, "Esperando...", False)
            else:
                Text = "Revancha"
                if Session.RematchRemote:
                    Text = "Aceptar revancha"
                UI.DrawButton(Screen, self.AgainButton, Text)
                if Session.RematchRemote:
                    UI.DrawCentered(Screen, "El rival quiere revancha", UI.SmallFont, "white", 450)
        UI.DrawButton(Screen, self.MenuButton, "Menú principal")