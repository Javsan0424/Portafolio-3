import pygame
pygame.init()


screen = pygame.display.set_mode((1200,800))
pygame.display.set_caption("Witch Hunt")

running = True


#Join card
death = pygame.image.load("Assets/Effects/Death-effect.png")
exchange = pygame.image.load("Assets/Effects/Exchange-effect.png")
combined = death.copy()
combined.blit(exchange, (12,0))
combined = pygame.transform.scale(combined,(100,100))

#Join Domino
UpperPiece = pygame.image.load("Assets/Numbers/1.png")
UpperPiece = pygame.transform.flip(UpperPiece,0,1)
LowerPiece = pygame.image.load("Assets/Numbers/2.png")

CompletePiece = pygame.Surface((UpperPiece.get_width(), UpperPiece.get_height() *2))
CompletePiece.blit(UpperPiece, (0,0))
CompletePiece.blit(LowerPiece, (0,UpperPiece.get_height()))

#Join Domino with effects
death = pygame.image.load("Assets/Effects/Death-effect.png")
exchange = pygame.image.load("Assets/Effects/Exchange-effect.png")
exchange = pygame.transform.flip(exchange,0,1)

UpperPiece = pygame.image.load("Assets/Numbers/1.png")
LowerPiece = pygame.image.load("Assets/Numbers/2.png")
LowerPiece = pygame.transform.flip(LowerPiece,0,1)

CompletePiece = pygame.Surface((UpperPiece.get_width(), UpperPiece.get_height() *2), pygame.SRCALPHA)
CompletePiece.blit(UpperPiece, (0,1))
CompletePiece.blit(death, (4, 4))

CompletePiece.blit(LowerPiece, (0,UpperPiece.get_height()))
CompletePiece.blit(exchange, (3, 36))

CompletePiece = pygame.transform.scale(CompletePiece, (CompletePiece.get_width()*3, CompletePiece.get_height()*3 ))



while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            running = False

    #Fondo
    screen.fill("white")

    screen.blit(CompletePiece,(0,0))

    pygame.display.update()

pygame.quit()
