import pygame
import CreateCard
import Network
from CreateCard import CELL
from Player import Player
from Board import Board, GridRect
from SkyBox import ChangeFrame
pygame.init()

screen = pygame.display.set_mode((1200,800))
pygame.display.set_caption("Witch Hunt")

# MENU, MULTI, LOBBY, PLAYING, GAMEOVER
State = "MENU"

running = True
SkyboxFrame = 1
rateChange = 100
LastTickUpdate = pygame.time.get_ticks()
SkyboxSurf = pygame.image.load("Assets/SkyBox/0001.png")

BarWidth = 1200
BarHeight = 30

clock = pygame.time.Clock()

deck = CreateCard.CreateDeck()

Font = pygame.font.SysFont("Arial", 22, bold=True)
SmallFont = pygame.font.SysFont("Arial", 17)
BigFont = pygame.font.SysFont("Arial", 72, bold=True)

CardSpeed = 0.12
CardSpacing = 64

# Indice 0 = Jugador 1, indice 1 = Jugador 2
PlayerColors = [(80, 160, 255), (255, 150, 60)]

# Posicion en pantalla: la mano de abajo y la de arriba
BottomHandRect = pygame.Rect(150, 650, 900, 110)
TopHandRect = pygame.Rect(150, 40, 900, 110)

LeftPanel = pygame.Rect(10, 184, 244, 432)
RightPanel = pygame.Rect(946, 184, 244, 432)

PlayButton = pygame.Rect(500, 400, 200, 60)
MultiButton = pygame.Rect(500, 480, 200, 60)
QuitButton = pygame.Rect(500, 560, 200, 60)

IPBox = pygame.Rect(450, 320, 300, 45)
HostButton = pygame.Rect(500, 400, 200, 60)
JoinButton = pygame.Rect(500, 480, 200, 60)
BackButton = pygame.Rect(500, 560, 200, 60)
CancelButton = pygame.Rect(500, 520, 200, 60)

ResumeButton = pygame.Rect(500, 340, 200, 60)
RestartButton = pygame.Rect(500, 420, 200, 60)
PauseQuitButton = pygame.Rect(500, 500, 200, 60)
PauseQuitOnlineButton = pygame.Rect(500, 420, 200, 60)

GenerateButton = pygame.Rect(20, 360, 224, 56)
AgainButton = pygame.Rect(500, 450, 200, 60)
MenuButton = pygame.Rect(500, 530, 200, 60)

Players = []
Player1 = None
Player2 = None
DisplayHealth = [100, 100]
TheBoard = None
Turn = 1
Selected = None
Horizontal = False
Message = ""
Winner = None
Paused = False

# Multijugador
Online = False
LocalIndex = 0
Net = None
MenuMessage = ""
IPText = "127.0.0.1"
LobbyText = ""
HostIP = ""


def CurrentIndex():
    # Turnos impares: Jugador 1, turnos pares: Jugador 2
    if Turn % 2 == 1:
        return 0
    return 1


def MyTurn():
    if not Online:
        return True
    return CurrentIndex() == LocalIndex


def BottomIndex():
    # En linea siempre ves tu mano abajo
    if Online:
        return LocalIndex
    return 0


def FaceUpIndex():
    # En local solo se ve la mano del jugador en turno, en linea solo la tuya
    if Online:
        return LocalIndex
    return CurrentIndex()


def HandRectOf(Index):
    if Index == BottomIndex():
        return BottomHandRect
    return TopHandRect


def StartNewGame(IsOnline = False, Local = 0):
    global Players, Player1, Player2, DisplayHealth
    global TheBoard, Turn, Selected, Horizontal, Message, Winner, State
    global Online, LocalIndex, Paused

    Online = IsOnline
    LocalIndex = Local
    Paused = False

    Player1 = Player("Jugador 1")
    Player2 = Player("Jugador 2")
    Players = [Player1, Player2]
    DisplayHealth = [Player1.currentHealth, Player2.currentHealth]

    TheBoard = Board()
    Turn = 1
    Selected = None
    Horizontal = False
    Message = ""
    Winner = None

    for i in range(7):
        Player1.Hand.append(deck.RandomizeCard())
        Player2.Hand.append(deck.RandomizeCard())

    State = "PLAYING"


def CloseNetwork():
    global Net, Online
    if Net is not None:
        Net.Close()
    Net = None
    Online = False


def StartHost():
    global Net, State, LobbyText, HostIP, MenuMessage
    CloseNetwork()
    Net = Network.Connection()
    Net.Host()
    HostIP = Network.GetLocalIP()
    LobbyText = "Esperando rival..."
    MenuMessage = ""
    State = "LOBBY"


def StartJoin():
    global Net, State, LobbyText, MenuMessage
    CloseNetwork()
    Net = Network.Connection()
    Net.Join(IPText.strip())
    LobbyText = "Conectando a " + IPText.strip() + "..."
    MenuMessage = ""
    State = "LOBBY"


def CheckWinner():
    global Winner, State
    if Player1.currentHealth <= 0:
        Winner = 1
        State = "GAMEOVER"
    elif Player2.currentHealth <= 0:
        Winner = 0
        State = "GAMEOVER"


def EndTurn():
    global Turn, Selected
    Selected = None
    CheckWinner()
    if State == "GAMEOVER":
        return
    Turn += 1
    TheBoard.Tick(CurrentIndex(), Players)
    CheckWinner()


def GenerateCard():
    global Message
    if Online:
        Net.Send({"Type": "Generate"})
    Players[CurrentIndex()].Hand.append(deck.RandomizeCard())
    Message = ""
    EndTurn()


def CardUnderMouse(MousePos):
    Hand = Players[CurrentIndex()].Hand
    for i in range(len(Hand) - 1, -1, -1):
        CardRect = pygame.Rect(int(Hand[i].Pos[0]), int(Hand[i].Pos[1]), CELL, CELL * 2)
        if CardRect.collidepoint(MousePos):
            return Hand[i]
    return None


def TryPlace(MousePos):
    global Message
    Col = (MousePos[0] - GridRect.x) // CELL
    Row = (MousePos[1] - GridRect.y) // CELL
    Index = CurrentIndex()

    Plan, Reason = TheBoard.Evaluate(Selected, Row, Col, Horizontal)
    if Plan is None:
        Message = Reason
        return

    if Online:
        Net.Send({"Type": "Place", "Upper": Selected.UpperEffect, "Lower": Selected.LowerEffect,
                  "Row": int(Row), "Col": int(Col), "Horizontal": Horizontal})

    TheBoard.Place(Selected, Row, Col, Horizontal, Index, Plan)
    TheBoard.Resolve(Plan, Index, Players)
    Players[Index].Hand.remove(Selected)
    Message = ""
    EndTurn()


def ApplyRemotePlace(Data):
    Index = CurrentIndex()
    if Index == LocalIndex:
        return

    RemoteCard = CreateCard.Card(Data["Upper"], Data["Lower"])
    Plan, Reason = TheBoard.Evaluate(RemoteCard, Data["Row"], Data["Col"], Data["Horizontal"])
    if Plan is None:
        return

    TheBoard.Place(RemoteCard, Data["Row"], Data["Col"], Data["Horizontal"], Index, Plan)
    TheBoard.Resolve(Plan, Index, Players)
    # La mano del rival esta boca abajo, solo importa cuantas cartas le quedan
    if len(Players[Index].Hand) > 0:
        Players[Index].Hand.pop()
    EndTurn()


def ApplyRemoteGenerate():
    Index = CurrentIndex()
    if Index == LocalIndex:
        return
    Players[Index].Hand.append(deck.RandomizeCard())
    EndTurn()


def ProcessNetwork():
    global State, MenuMessage
    if Net is None:
        return

    while not Net.Inbox.empty():
        Data = Net.Inbox.get()
        Type = Data["Type"]

        if Type == "Connected":
            if Net.Role == "host":
                StartNewGame(True, 0)
                Net.Send({"Type": "Start"})

        elif Type == "Start":
            StartNewGame(True, 1)

        elif Type == "Place" and State == "PLAYING":
            ApplyRemotePlace(Data)

        elif Type == "Generate" and State == "PLAYING":
            ApplyRemoteGenerate()

        elif Type == "Error":
            if State == "LOBBY":
                MenuMessage = "No se pudo conectar: " + Data["Text"]
                CloseNetwork()
                State = "MULTI"

        elif Type == "Disconnected":
            if State == "PLAYING" or State == "LOBBY":
                MenuMessage = "El rival se desconecto"
                CloseNetwork()
                State = "MENU"


def DrawButton(Rect, Text):
    Color = (70, 70, 90)
    if Rect.collidepoint(pygame.mouse.get_pos()):
        Color = (110, 110, 140)
    pygame.draw.rect(screen, Color, Rect, border_radius=10)
    pygame.draw.rect(screen, "white", Rect, 2, border_radius=10)
    Label = Font.render(Text, True, "white")
    screen.blit(Label, Label.get_rect(center = Rect.center))


def DrawOverlay():
    Dark = pygame.Surface((1200, 800), pygame.SRCALPHA)
    Dark.fill((0, 0, 0, 170))
    screen.blit(Dark, (0, 0))


def DrawCentered(Text, FontToUse, Color, Y):
    Label = FontToUse.render(Text, True, Color)
    screen.blit(Label, Label.get_rect(center = (600, Y)))


def DrawHand(Index):
    Hand = Players[Index].Hand
    Rect = HandRectOf(Index)

    pygame.draw.rect(screen, (35, 30, 45), Rect, border_radius=10)
    pygame.draw.rect(screen, PlayerColors[Index], Rect, 3, border_radius=10)

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
        if State == "PLAYING" and Index == FaceUpIndex():
            screen.blit(Hand[i].DominoPiece, CardRect)
            if Hand[i] is Selected:
                pygame.draw.rect(screen, "yellow", CardRect, 3)
        else:
            # Carta boca abajo
            pygame.draw.rect(screen, (90, 40, 110), CardRect)
            pygame.draw.rect(screen, "white", CardRect, 2)


def DrawGhost():
    if Selected is None or not MyTurn():
        return ""
    MousePos = pygame.mouse.get_pos()
    if not GridRect.collidepoint(MousePos):
        return ""

    Col = (MousePos[0] - GridRect.x) // CELL
    Row = (MousePos[1] - GridRect.y) // CELL
    Plan, Reason = TheBoard.Evaluate(Selected, Row, Col, Horizontal)

    Surf = Selected.GetSurface(Horizontal).copy()
    Tint = pygame.Surface(Surf.get_size(), pygame.SRCALPHA)
    if Plan is None:
        Tint.fill((255, 0, 0, 110))
    else:
        Tint.fill((0, 255, 0, 70))
    Surf.blit(Tint, (0, 0))
    Surf.set_alpha(200)
    screen.blit(Surf, (GridRect.x + Col * CELL, GridRect.y + Row * CELL))
    return Reason


def DrawSidePanels():
    Index = CurrentIndex()

    for PanelRect in (LeftPanel, RightPanel):
        pygame.draw.rect(screen, (35, 30, 45), PanelRect, border_radius=10)
        pygame.draw.rect(screen, PlayerColors[Index], PanelRect, 3, border_radius=10)

    Text = Font.render("Turno " + str(Turn), True, "white")
    screen.blit(Text, (22, 220))
    Text = Font.render("Juega: " + Players[Index].Name, True, PlayerColors[Index])
    screen.blit(Text, (22, 255))

    if Online:
        Text = SmallFont.render("Eres " + Players[LocalIndex].Name, True, PlayerColors[LocalIndex])
        screen.blit(Text, (22, 295))
        if MyTurn():
            Text = SmallFont.render("Es tu turno", True, "yellow")
        else:
            Text = SmallFont.render("Esperando al rival...", True, "white")
        screen.blit(Text, (22, 320))

    DrawButton(GenerateButton, "Generar ficha")

    Lines = ["Controles",
             "Clic izq - elegir / colocar",
             "R - rotar",
             "Clic der - rotar",
             "Esc - pausa",
             "",
             "Efectos",
             "Fuego - explosion que decae",
             "Veneno - dano acumulativo",
             "Impacto - dano fijo",
             "Drenar - dano y cura",
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
        Line = SmallFont.render(Lines[i], True, Color)
        screen.blit(Line, (960, 198 + i * 22))


def DrawBars():
    Bottom = BottomIndex()
    Top = 1 - Bottom

    for Item in ((Top, 0), (Bottom, 770)):
        Who = Players[Item[0]]
        Width = int(BarWidth * DisplayHealth[Item[0]] / Who.maxHealt)
        if Item[1] == 0:
            # Barra de arriba: se acorta de izquierda a derecha
            pygame.draw.rect(screen, "red", (BarWidth - Width, 0, Width, BarHeight))
        else:
            # Barra de abajo: se acorta de derecha a izquierda
            pygame.draw.rect(screen, "red", (0, 770, Width, BarHeight))

        Label = Font.render(str(int(Who.currentHealth)) + " / " + str(Who.maxHealt), True, "white")
        screen.blit(Label, Label.get_rect(center=(BarWidth // 2, Item[1] + BarHeight // 2)))


while running:
    ProcessNetwork()

    if State != "PLAYING":
        Paused = False

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if State == "MENU":
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if PlayButton.collidepoint(event.pos):
                    MenuMessage = ""
                    StartNewGame()
                elif MultiButton.collidepoint(event.pos):
                    MenuMessage = ""
                    State = "MULTI"
                elif QuitButton.collidepoint(event.pos):
                    running = False

        elif State == "MULTI":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKSPACE:
                    IPText = IPText[:-1]
                elif event.unicode != "" and event.unicode.isprintable() and len(IPText) < 25:
                    IPText += event.unicode

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if HostButton.collidepoint(event.pos):
                    StartHost()
                elif JoinButton.collidepoint(event.pos):
                    StartJoin()
                elif BackButton.collidepoint(event.pos):
                    MenuMessage = ""
                    State = "MENU"

        elif State == "LOBBY":
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if CancelButton.collidepoint(event.pos):
                    CloseNetwork()
                    State = "MULTI"

        elif State == "PLAYING":
            if Paused:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    Paused = False

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if ResumeButton.collidepoint(event.pos):
                        Paused = False
                    elif not Online and RestartButton.collidepoint(event.pos):
                        StartNewGame()
                    elif Online and PauseQuitOnlineButton.collidepoint(event.pos):
                        CloseNetwork()
                        Paused = False
                        State = "MENU"
                    elif not Online and PauseQuitButton.collidepoint(event.pos):
                        Paused = False
                        State = "MENU"
            else:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    Paused = True

                if MyTurn():
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_r:
                            Horizontal = not Horizontal

                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if event.button == 3:
                            Horizontal = not Horizontal

                        if event.button == 1:
                            Clicked = CardUnderMouse(event.pos)
                            if Clicked is not None:
                                # Clic en la ficha elegida la suelta
                                if Clicked is Selected:
                                    Selected = None
                                else:
                                    Selected = Clicked
                                Message = ""
                            elif GenerateButton.collidepoint(event.pos):
                                GenerateCard()
                            elif Selected is not None and GridRect.collidepoint(event.pos):
                                TryPlace(event.pos)

        elif State == "GAMEOVER":
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if not Online and AgainButton.collidepoint(event.pos):
                    StartNewGame()
                elif MenuButton.collidepoint(event.pos):
                    CloseNetwork()
                    State = "MENU"

    #Fondo
    SkyboxFrame, SkyboxSurf, LastTickUpdate = ChangeFrame(SkyboxFrame, SkyboxSurf, LastTickUpdate, pygame.time.get_ticks(), rateChange)
    SkyboxSurf = pygame.transform.scale(SkyboxSurf, screen.get_size())
    screen.blit(SkyboxSurf, (0,0))

    if State == "MENU":
        DrawOverlay()
        DrawCentered("Witch Hunt", BigFont, "white", 220)
        DrawCentered("Domino de efectos para dos jugadores", Font, "white", 300)
        if MenuMessage != "":
            DrawCentered(MenuMessage, Font, "yellow", 360)
        DrawButton(PlayButton, "Jugar")
        DrawButton(MultiButton, "Multijugador")
        DrawButton(QuitButton, "Salir")

    elif State == "MULTI":
        DrawOverlay()
        DrawCentered("Multijugador", BigFont, "white", 160)
        DrawCentered("IP del anfitrion (para unirte)", SmallFont, "white", 300)

        pygame.draw.rect(screen, (35, 30, 45), IPBox, border_radius=8)
        pygame.draw.rect(screen, "white", IPBox, 2, border_radius=8)
        Cursor = ""
        if (pygame.time.get_ticks() // 500) % 2 == 0:
            Cursor = "|"
        IPLabel = Font.render(IPText + Cursor, True, "white")
        screen.blit(IPLabel, IPLabel.get_rect(midleft = (IPBox.x + 10, IPBox.centery)))

        if MenuMessage != "":
            DrawCentered(MenuMessage, SmallFont, "yellow", 385)
        DrawButton(HostButton, "Crear partida")
        DrawButton(JoinButton, "Unirse")
        DrawButton(BackButton, "Volver")

    elif State == "LOBBY":
        DrawOverlay()
        DrawCentered("Multijugador", BigFont, "white", 220)
        DrawCentered(LobbyText, Font, "white", 340)
        if Net is not None and Net.Role == "host":
            DrawCentered("Comparte tu IP: " + HostIP + "  (puerto " + str(Network.DefaultPort) + ")", Font, "yellow", 400)
        DrawButton(CancelButton, "Cancelar")

    else:
        for i in range(2):
            DisplayHealth[i] += (Players[i].currentHealth - DisplayHealth[i]) * 0.1

        DrawBars()

        # Grid donde van las fichas
        pygame.draw.rect(screen, (15, 70, 35), GridRect)
        for i in range(0, GridRect.width + 1, CELL):
            pygame.draw.line(screen, (30, 100, 55), (GridRect.x + i, GridRect.y), (GridRect.x + i, GridRect.bottom))
        for i in range(0, GridRect.height + 1, CELL):
            pygame.draw.line(screen, (30, 100, 55), (GridRect.x, GridRect.y + i), (GridRect.right, GridRect.y + i))
        pygame.draw.rect(screen, "white", GridRect, 2)

        TheBoard.Draw(screen, SmallFont, PlayerColors)

        DrawHand(1)
        DrawHand(0)

        if State == "PLAYING":
            HoverReason = DrawGhost()
            DrawSidePanels()

            Status = HoverReason
            if Status == "":
                Status = Message
            if Status != "":
                StatusText = Font.render(Status, True, "yellow")
                screen.blit(StatusText, StatusText.get_rect(center=(GridRect.centerx, 633)))

            if Paused:
                DrawOverlay()
                DrawCentered("Pausa", BigFont, "white", 220)
                DrawButton(ResumeButton, "Continuar")
                if Online:
                    DrawButton(PauseQuitOnlineButton, "Salir al menu")
                    DrawCentered("En linea la partida sigue para el rival", SmallFont, "yellow", 590)
                else:
                    DrawButton(RestartButton, "Reiniciar")
                    DrawButton(PauseQuitButton, "Menu principal")

        if State == "GAMEOVER":
            DrawOverlay()
            DrawCentered("Fin del juego", BigFont, "white", 250)
            DrawCentered("Gana " + Players[Winner].Name, BigFont, PlayerColors[Winner], 350)
            if not Online:
                DrawButton(AgainButton, "Jugar de nuevo")
            DrawButton(MenuButton, "Menu principal")

    pygame.display.update()

    clock.tick(60)

CloseNetwork()
pygame.quit()