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

Player1 = Player()
Player1HealthBar = pygame.Surface((1200, 30))
Player1HealthBar.fill("red")

Player2 = Player()
Player2HealthBar = pygame.Surface((1200, 30))
Player2HealthBar.fill("red")

clock = pygame.time.Clock()

#Join Domino with effects
deck = CreateCard.CreateDeck()
card = deck.RandomizeCard()


CompletePiece = card.DominoPiece
CompletePieceRect = card.DominoPieceRect


while running:
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

    #Barra de vida Jugador 2
    screen.blit(Player2HealthBar, (0,0))

    #Barra de vida Jugador 1
    screen.blit(Player1HealthBar, (0,770))


    for i in range(len(Player2.Hand)):
        screen.blit(Player2.Hand[i].DominoPiece,(20 + i*96,40))

    for i in range(len(Player1.Hand)):
            screen.blit(Player1.Hand[i].DominoPiece,(20 + i*96,570))

    pygame.display.update()

    clock.tick(60)

pygame.quit()
