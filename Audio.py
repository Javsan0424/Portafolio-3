import os
import sys
import pygame
from Events import (
    Damage, Heal, PiecePlaced, TurnChanged, ChainCut, GameOver,
    InvalidMove, CardDrawn, TurnPassed, EffectStarted, GameStarted, StateChanged
)


def _ResourcePath(RelativePath):
    BasePath = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(BasePath, RelativePath)


class AudioHooks:
    def __init__(self, Bus):
        if not pygame.mixer.get_init():
            pygame.mixer.init()

        SoundPaths = {
            "MoveChip": "Assets/SFX/MovePiece.ogg",
            "PlaceChip": "Assets/SFX/PlaceChip.wav",
            "DrawChip": "Assets/SFX/takechip.ogg",
        }

        self.Sounds = {}
        for Key, RelPath in SoundPaths.items():
            FullPath = _ResourcePath(RelPath)
            if os.path.exists(FullPath):
                self.Sounds[Key] = pygame.mixer.Sound(FullPath)
            else:
                self.Sounds[Key] = None

        Bus.Subscribe(Damage, self.OnDamage)
        Bus.Subscribe(Heal, self.OnHeal)
        Bus.Subscribe(PiecePlaced, self.OnPiecePlaced)
        Bus.Subscribe(TurnChanged, self.OnTurnChanged)
        Bus.Subscribe(ChainCut, self.OnChainCut)
        Bus.Subscribe(GameOver, self.OnGameOver)
        Bus.Subscribe(InvalidMove, self.OnInvalidMove)
        Bus.Subscribe(CardDrawn, self.OnCardDrawn)
        Bus.Subscribe(TurnPassed, self.OnTurnPassed)
        Bus.Subscribe(EffectStarted, self.OnEffectStarted)
        Bus.Subscribe(GameStarted, self.OnGameStarted)
        Bus.Subscribe(StateChanged, self.OnStateChanged)

    def _Play(self, Key):
        Sfx = self.Sounds.get(Key)
        if Sfx is not None:
            Sfx.play()

    def OnDamage(self, Target, Amount, Source):
        self._Play("PlaceChip")

    def OnHeal(self, Target, Amount, Source):
        self._Play("DrawChip")

    def OnPiecePlaced(self, Player, Cells, Upper, Lower):
        self._Play("PlaceChip")

    def OnTurnChanged(self, Turn, Player):
        self._Play("MoveChip")

    def OnChainCut(self, Player, Cells):
        self._Play("PlaceChip")

    def OnGameOver(self, Winner, Reason):
        pass

    def OnInvalidMove(self, Player, Reason):
        self._Play("MoveChip")

    def OnCardDrawn(self, Player, DeckCount):
        self._Play("DrawChip")

    def OnTurnPassed(self, Player):
        self._Play("MoveChip")

    def OnEffectStarted(self, Owner, Kind, Value):
        self._Play("PlaceChip")

    def OnGameStarted(self, Mode):
        self._Play("DrawChip")

    def OnStateChanged(self, Name):
        pass