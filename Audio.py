from Events import (Damage, Heal, PiecePlaced, TurnChanged, ChainCut, GameOver,
                    InvalidMove, CardDrawn, TurnPassed, EffectStarted, GameStarted, StateChanged)


# Modulo de audio pendiente. Ya esta suscrito a todos los eventos del juego sin tocar la logica:
# solo hay que cargar los sonidos en __init__ y llamar a .play() dentro de cada metodo.
class AudioHooks:
    def __init__(self, Bus):
        # pygame.mixer.init() y la carga de sonidos van aqui cuando los tengas
        self.Sounds = {}

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

    # Source es "Impact", "Drain", "Fire" o "Poison": un sonido distinto por efecto
    def OnDamage(self, Target, Amount, Source):
        pass

    def OnHeal(self, Target, Amount, Source):
        pass

    def OnPiecePlaced(self, Player, Cells, Upper, Lower):
        pass

    def OnTurnChanged(self, Turn, Player):
        pass

    def OnChainCut(self, Player, Cells):
        pass

    def OnGameOver(self, Winner, Reason):
        pass

    def OnInvalidMove(self, Player, Reason):
        pass

    def OnCardDrawn(self, Player, DeckCount):
        pass

    def OnTurnPassed(self, Player):
        pass

    def OnEffectStarted(self, Owner, Kind, Value):
        pass

    def OnGameStarted(self, Mode):
        pass

    # Name es el nombre de la pantalla ("Menu", "Playing", "GameOver"...): sirve para cambiar la musica
    def OnStateChanged(self, Name):
        pass
