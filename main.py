import pygame
import CreateCard
pygame.init()


screen = pygame.display.set_mode((1200,800))
pygame.display.set_caption("Witch Hunt")

running = True

#Join Domino with effects
card = CreateCard.Card(1,"Death", 2, "Shield")


CompletePiece = card.DominoPiece
CompletePieceRect = card.DominoPieceRect



while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            running = False

    #Fondo
    screen.fill("blue")

    screen.blit(CompletePiece,(0,0))

    pygame.display.update()

pygame.quit()
