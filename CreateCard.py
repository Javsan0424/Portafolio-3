import pygame
import json
pygame.init()

class Card:
    def __init__(self, UpperNumer, UpperEffect, LowerNumber, LowerEffect):
        with open('data.json', 'r', encoding='utf-8') as file:
            data = json.load(file)

        self.UpperNumer =  str(UpperNumer)
        self.UpperEffect = UpperEffect
        self.LowerNumber = str(LowerNumber)
        self.LowerEffect = LowerEffect

        self.UpperNumerSurf = pygame.image.load(data["Number"][self.UpperNumer])
        self.UpperEffectSurf = pygame.image.load(data["EffectSurface"][self.UpperEffect])
        self.UpperNumerSurf.blit(self.UpperEffectSurf, (data["DominoBuildReference"][UpperEffect][0], data["DominoBuildReference"][UpperEffect][1] ))
        
        self.LowerNumberSurf = pygame.image.load(data["Number"][self.LowerNumber])
        self.LowerEffectSurf = pygame.image.load(data["EffectSurface"][self.LowerEffect])
        self.LowerNumberSurf.blit(self.LowerEffectSurf, (data["DominoBuildReference"][LowerEffect][0], data["DominoBuildReference"][LowerEffect][1]))

        self.LowerNumberSurf = pygame.transform.flip(self.LowerNumberSurf ,0,1)
        self.LowerEffectSurf = pygame.transform.flip(self.LowerEffectSurf,0,1)
        
        self.DominoPiece = pygame.Surface((self.UpperNumerSurf.get_width(), self.LowerNumberSurf.get_height() *2), pygame.SRCALPHA)
        self.DominoPiece.blit(self.UpperNumerSurf, (0,0))
        self.DominoPiece.blit(self.LowerNumberSurf, (0, self.UpperNumerSurf.get_height()))

        self.DominoPiece = pygame.transform.scale(self.DominoPiece, (self.DominoPiece.get_width()*3, self.DominoPiece.get_height()*3 ))
        self.DominoPieceRect = self.DominoPiece.get_rect(topleft = (0,0))


#Builder
class CreateDeck:
    AvailableCombinations = ["Death", "ForcePlay","ForcePlay","ForcePlay","ForcePlay",  "Exchange",  "Exchange", "Exchange",  "Exchange", "Discard", "Discard", "Discard", "Discard", "Discard", "Discard", "Shield", "Shield", "Shield", "Shield", "Shield", "Shield", "Compare", "Compare", "Compare", "Compare", "Compare", "Compare",  "Pry", "Pry", "Pry","Pry","Pry","Pry", "Investigate", "Investigate", "Investigate", "Investigate", "Investigate", "Investigate", "Investigate", "Investigate", "Investigate", "Investigate", "Investigate", "Investigate", "Investigate", "Investigate", "Investigate"]

    DominoBuildReference = {
        "Investigate":(4,4),
        "Pry": (4,4),
        "Compare": (3, 4),
        "Shield": (4,4),
        "Discard": (4, 4),
        "Exchange": (3, 4),
        "ForcePlay":  (9, 4),
        "Death" : (4, 4),
    }

    def __init__(self):
        self.RandomizeDeck = []

    def CreateCard(UpperPart, UpperEffect, LowerPart, LowerEffect):
        pass

    def RandomizeCards():
        pass
