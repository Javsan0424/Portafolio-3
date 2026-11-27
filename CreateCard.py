import pygame
import random
import json
pygame.init()

CELL = 48
EffectCache = {}


def LoadEffect(Name):
    if Name not in EffectCache:
        with open('data.json', 'r', encoding='utf-8') as file:
            data = json.load(file)
        Surf = pygame.image.load(data["EffectSurface"][Name]).convert_alpha()
        EffectCache[Name] = pygame.transform.scale(Surf, (CELL, CELL))
    return EffectCache[Name]


class Card:
    def __init__(self, UpperEffect, LowerEffect):
        self.UpperEffect = UpperEffect
        self.LowerEffect = LowerEffect

        self.UpperEffectSurf = LoadEffect(self.UpperEffect)
        self.LowerEffectSurf = pygame.transform.flip(LoadEffect(self.LowerEffect), 0, 1)

        self.DominoPiece = pygame.Surface((CELL, CELL * 2), pygame.SRCALPHA)
        self.DominoPiece.blit(self.UpperEffectSurf, (0, 0))
        self.DominoPiece.blit(self.LowerEffectSurf, (0, CELL))
        self.DominoPieceRect = self.DominoPiece.get_rect(topleft = (0,0))

        # Las cartas nacen en el centro y la mano las acomoda con la animacion
        self.Pos = [600 - CELL / 2, 400 - CELL]

    def GetSurface(self, Horizontal):
        # Horizontal: el efecto de arriba queda a la izquierda y el de abajo a la derecha
        if Horizontal:
            return pygame.transform.rotate(self.DominoPiece, 90)
        return self.DominoPiece


#Builder
class CreateDeck:
    def __init__(self):
       self.AvailableCombinations = ["Fire", "Impact", "Drain", "Poison"]

    def RandomizeCard(self):
        UpperEffect = random.choice(self.AvailableCombinations)
        LowerEffect = random.choice(self.AvailableCombinations)
        card = Card(UpperEffect, LowerEffect)
        return card