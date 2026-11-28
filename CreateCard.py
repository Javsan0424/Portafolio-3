import pygame
from Resources import ResourcePath, LoadData
from Effects import EffectTypes
pygame.init()

CELL = 48
EffectCache = {}
LetterFont = None


def LoadEffect(Name):
    if Name not in EffectCache:
        Path = ResourcePath(LoadData()["EffectSurface"][Name])
        Surf = pygame.image.load(Path).convert_alpha()
        EffectCache[Name] = pygame.transform.scale(Surf, (CELL, CELL))
    return EffectCache[Name]


# Letra de cada efecto sobre la ficha, para no depender solo del color
def DrawLetter(Surf, Letter, X, Y):
    global LetterFont
    if LetterFont is None:
        LetterFont = pygame.font.SysFont("Arial", 16, bold=True)

    Shadow = LetterFont.render(Letter, True, (0, 0, 0))
    for Offset in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        Surf.blit(Shadow, (X + Offset[0], Y + Offset[1]))
    Surf.blit(LetterFont.render(Letter, True, (255, 255, 255)), (X, Y))


class Card:
    def __init__(self, UpperEffect, LowerEffect):
        self.UpperEffect = UpperEffect
        self.LowerEffect = LowerEffect

        # Una carta oculta es la del rival en linea: no se conoce su contenido
        self.Hidden = UpperEffect is None
        self.Pos = [600 - CELL / 2, 400 - CELL]

        if self.Hidden:
            self.Surfaces = {}
            self.DominoPiece = None
            return

        self.UpperEffectSurf = LoadEffect(self.UpperEffect)
        self.LowerEffectSurf = pygame.transform.flip(LoadEffect(self.LowerEffect), 0, 1)

        Plain = pygame.Surface((CELL, CELL * 2), pygame.SRCALPHA)
        Plain.blit(self.UpperEffectSurf, (0, 0))
        Plain.blit(self.LowerEffectSurf, (0, CELL))

        UpperLetter = EffectTypes[self.UpperEffect].Letter
        LowerLetter = EffectTypes[self.LowerEffect].Letter

        # Casilla (columna, fila) de la mitad de arriba y de la de abajo en cada orientacion
        Corners = [((0, 0), (0, 1)), ((0, 0), (1, 0)), ((0, 1), (0, 0)), ((1, 0), (0, 0))]
        self.Surfaces = {}
        for Orientation in range(4):
            Surf = pygame.transform.rotate(Plain, 90 * Orientation).copy()
            Upper = Corners[Orientation][0]
            Lower = Corners[Orientation][1]
            DrawLetter(Surf, UpperLetter, Upper[0] * CELL + 4, Upper[1] * CELL + 2)
            DrawLetter(Surf, LowerLetter, Lower[0] * CELL + 4, Lower[1] * CELL + 2)
            self.Surfaces[Orientation] = Surf

        self.DominoPiece = self.Surfaces[0]
        self.DominoPieceRect = self.DominoPiece.get_rect(topleft = (0,0))

    def GetSurface(self, Orientation):
        return self.Surfaces[Orientation]