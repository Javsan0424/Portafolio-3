import pygame
import CreateCard
from CreateCard import CELL
from Player import Player
from Board import Board, GridRect
from SkyBox import ChangeFrame
pygame.init()

screen = pygame.display.set_mode((1200,800))
pygame.display.set_caption("Witch Hunt")

# MENU, PLAYING, GAMEOVER
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

# Indice 0 = Jugador 1 (abajo), indice 1 = Jugador 2 (arriba)
PlayerColors = [(80, 160, 255), (255, 150, 60)]
HandRects = [pygame.Rect(150, 650, 900, 110), pygame.Rect(150, 40, 900, 110)]

LeftPanel = pygame.Rect(10, 184, 244, 432)
RightPanel = pygame.Rect(946, 184, 244, 432)

PlayButton = pygame.Rect(500, 420, 200, 60)
QuitButton = pygame.Rect(500, 500, 200, 60)
GenerateButton = pygame.Rect(20, 360, 224, 56)
AgainButton = pygame.Rect(500, 450, 200, 60)
MenuButton = pygame.Rect(500, 530, 200, 60)

Players = []
Player1 = None
Player2 = None
Player1DisplayHealth = 0
Player2DisplayHealth = 0
TheBoard = None
Turn = 1
Selected = None
Horizontal = False
Message = ""
Winner = None


def CurrentIndex():
    # Turnos impares: Jugador 1, turnos pares: Jugador 2
    if Turn % 2 == 1:
        return 0
    return 1


def StartNewGame():
    global Players, Player1, Player2, Player1DisplayHealth, Player2DisplayHealth
    global TheBoard, Turn, Selected, Horizontal, Message, Winner, State

    Player1 = Player("Jugador 1")
    Player2 = Player("Jugador 2")
    Players = [Player1, Player2]
    Player1DisplayHealth = Player1.currentHealth
    Player2DisplayHealth = Player2.currentHealth

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

    TheBoard.Place(Selected, Row, Col, Horizontal, Index, Plan)
    TheBoard.Resolve(Plan, Index, Players)
    Players[Index].Hand.remove(Selected)
    Message = ""
    EndTurn()


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


def DrawHand(Index):
    Hand = Players[Index].Hand
    Rect = HandRects[Index]

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
        if State == "PLAYING" and Index == CurrentIndex():
            screen.blit(Hand[i].DominoPiece, CardRect)
            if Hand[i] is Selected:
                pygame.draw.rect(screen, "yellow", CardRect, 3)
        else:
            # Carta boca abajo
            pygame.draw.rect(screen, (90, 40, 110), CardRect)
            pygame.draw.rect(screen, "white", CardRect, 2)


def DrawGhost():
    if Selected is None:
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
    DrawButton(GenerateButton, "Generar ficha")

    Lines = ["Controles",
             "Clic izq - elegir / colocar",
             "R - rotar",
             "Clic der - rotar",
             "Esc - soltar ficha",
             "",
             "Efectos",
             "Fuego - daño explosion que decae",
             "Veneno - daño acumulativo",
             "Impacto - daño fijo",
             "Drenar - dano y cura",
             "",
             "Reglas",
             "Encadenar - mismo efecto",
             "Cortar - efecto de contrario",
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
    pygame.draw.rect(screen, "red", (BarWidth - Player2Width, 0, Player2Width, BarHeight))
    pygame.draw.rect(screen, "red", (0, 770, Player1Width, BarHeight))

    Player2Text = Font.render(str(int(Player2.currentHealth)) + " / " + str(Player2.maxHealt), True, "white")
    screen.blit(Player2Text, Player2Text.get_rect(center=(BarWidth // 2, BarHeight // 2)))

    Player1Text = Font.render(str(int(Player1.currentHealth)) + " / " + str(Player1.maxHealt), True, "white")
    screen.blit(Player1Text, Player1Text.get_rect(center=(BarWidth // 2, 770 + BarHeight // 2)))


while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if State == "MENU":
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if PlayButton.collidepoint(event.pos):
                    StartNewGame()
                elif QuitButton.collidepoint(event.pos):
                    running = False

        elif State == "PLAYING":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    Horizontal = not Horizontal
                if event.key == pygame.K_ESCAPE:
                    Selected = None

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 3:
                    Horizontal = not Horizontal

                if event.button == 1:
                    Clicked = CardUnderMouse(event.pos)
                    if Clicked is not None:
                        Selected = Clicked
                        Message = ""
                    elif GenerateButton.collidepoint(event.pos):
                        GenerateCard()
                    elif Selected is not None and GridRect.collidepoint(event.pos):
                        TryPlace(event.pos)

        elif State == "GAMEOVER":
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if AgainButton.collidepoint(event.pos):
                    StartNewGame()
                elif MenuButton.collidepoint(event.pos):
                    State = "MENU"

    #Fondo
    SkyboxFrame, SkyboxSurf, LastTickUpdate = ChangeFrame(SkyboxFrame, SkyboxSurf, LastTickUpdate, pygame.time.get_ticks(), rateChange)
    SkyboxSurf = pygame.transform.scale(SkyboxSurf, screen.get_size())
    screen.blit(SkyboxSurf, (0,0))

    if State == "MENU":
        DrawOverlay()
        Title = BigFont.render("Witch Hunt", True, "white")
        screen.blit(Title, Title.get_rect(center=(600, 250)))
        Sub = Font.render("Domino de efectos para dos jugadores", True, "white")
        screen.blit(Sub, Sub.get_rect(center=(600, 330)))
        DrawButton(PlayButton, "Modo Practica")
        DrawButton(QuitButton, "Salir")

    else:
        Player1DisplayHealth += (Player1.currentHealth - Player1DisplayHealth) * 0.1
        Player2DisplayHealth += (Player2.currentHealth - Player2DisplayHealth) * 0.1

        Player1Width = int(BarWidth * Player1DisplayHealth / Player1.maxHealt)
        Player2Width = int(BarWidth * Player2DisplayHealth / Player2.maxHealt)

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

        HoverReason = ""
        if State == "PLAYING":
            HoverReason = DrawGhost()
            DrawSidePanels()

            Status = HoverReason
            if Status == "":
                Status = Message
            if Status != "":
                StatusText = Font.render(Status, True, "yellow")
                screen.blit(StatusText, StatusText.get_rect(center=(GridRect.centerx, 633)))

        if State == "GAMEOVER":
            DrawOverlay()
            Text = BigFont.render("Fin del juego", True, "white")
            screen.blit(Text, Text.get_rect(center=(600, 250)))
            Text = BigFont.render("Gana " + Players[Winner].Name, True, PlayerColors[Winner])
            screen.blit(Text, Text.get_rect(center=(600, 350)))
            DrawButton(AgainButton, "Jugar de nuevo")
            DrawButton(MenuButton, "Menu principal")

    pygame.display.update()

    clock.tick(60)

pygame.quit()