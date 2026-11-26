import pygame
import CreateCard
from Player import Player
from SkyBox import ChangeFrame
pygame.init()

screen = pygame.display.set_mode((1200,800))
pygame.display.set_caption("Witch Hunt")

StartingGame = True

running = True
SkyboxFrame = 1
rateChange = 100
LastTickUpdate = pygame.time.get_ticks()
SkyboxSurf = pygame.image.load("Assets/SkyBox/0001.png")

BarWidth = 1200
BarHeight = 30

Player1 = Player()
Player1DisplayHealth = Player1.currentHealth

Player2 = Player()
Player2DisplayHealth = Player2.currentHealth


clock = pygame.time.Clock()

#Join Domino with effects
deck = CreateCard.CreateDeck()
card = deck.RandomizeCard()


CompletePiece = card.DominoPiece
CompletePieceRect = card.DominoPieceRect


Font = pygame.font.SysFont("Arial", 22, bold=True)

while running:
    Player1DisplayHealth += (Player1.currentHealth - Player1DisplayHealth) * 0.1
    Player2DisplayHealth += (Player2.currentHealth - Player2DisplayHealth) * 0.1

    Player1Width = int(BarWidth * Player1DisplayHealth / Player1.maxHealt)
    Player2Width = int(BarWidth * Player2DisplayHealth / Player2.maxHealt)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            running = False

    if StartingGame:
        for i in range(7):
            Player1.Hand.append(deck.RandomizeCard())
            Player2.Hand.append(deck.RandomizeCard())
        StartingGame = False

    #Fondo
    SkyboxFrame, SkyboxSurf, LastTickUpdate = ChangeFrame(SkyboxFrame, SkyboxSurf, LastTickUpdate, pygame.time.get_ticks(), rateChange)
    SkyboxSurf = pygame.transform.scale(SkyboxSurf, screen.get_size())
    screen.blit(SkyboxSurf, (0,0))

    # Barra de vida Jugador 2 (arriba): se acorta de izquierda a derecha
    pygame.draw.rect(screen, "red", (BarWidth - Player2Width, 0, Player2Width, BarHeight))

    # Barra de vida Jugador 1 (abajo): se acorta de derecha a izquierda
    pygame.draw.rect(screen, "red", (0, 770, Player1Width, BarHeight))

    Player2Text = Font.render(str(int(Player2.currentHealth)) + " / " + str(Player2.maxHealt), True, "white")
    screen.blit(Player2Text, Player2Text.get_rect(center=(BarWidth // 2, BarHeight // 2)))

    Player1Text = Font.render(str(int(Player1.currentHealth)) + " / " + str(Player1.maxHealt), True, "white")
    screen.blit(Player1Text, Player1Text.get_rect(center=(BarWidth // 2, 770 + BarHeight // 2)))


    for i in range(len(Player2.Hand)):
        screen.blit(Player2.Hand[i].DominoPiece,(20 + i*64,40))

    for i in range(len(Player1.Hand)):
            screen.blit(Player1.Hand[i].DominoPiece,(20 + i*64,630))



    pygame.display.update()

    clock.tick(60)

pygame.quit()
