import pygame
import random
import json
pygame.init()

class Card:
    def __init__(self, UpperEffect, LowerEffect):
        with open('data.json', 'r', encoding='utf-8') as file:
            data = json.load(file)

        self.UpperEffect = UpperEffect
        self.LowerEffect = LowerEffect

        self.UpperEffectSurf = pygame.image.load(data["EffectSurface"][self.UpperEffect])
        self.LowerEffectSurf = pygame.image.load(data["EffectSurface"][self.LowerEffect])

        self.LowerEffectSurf = pygame.transform.flip(self.LowerEffectSurf,0,1)
        
        self.DominoPiece = pygame.Surface((self.UpperEffectSurf.get_width(), self.LowerEffectSurf.get_height() *2), pygame.SRCALPHA)
        self.DominoPiece.blit(self.UpperEffectSurf, (0,0))
        self.DominoPiece.blit(self.LowerEffectSurf, (0, self.UpperEffectSurf.get_height()))

        self.DominoPiece = pygame.transform.scale(self.DominoPiece, (self.DominoPiece.get_width()*3, self.DominoPiece.get_height()*3 ))
        self.DominoPieceRect = self.DominoPiece.get_rect(topleft = (0,0))


#Builder
class CreateDeck:
    def __init__(self):
       self.AvailableCombinations = ["Fire", "Impact", "Drain", "Poison"]

    def RandomizeCard(self):
        UpperEffect = random.choice(self.AvailableCombinations)
        LowerEffect = random.choice(self.AvailableCombinations)
        card = Card(UpperEffect, LowerEffect)
        return card
