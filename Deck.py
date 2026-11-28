import random
from Resources import LoadData


# Mazo finito: cada combinacion (arriba, abajo) aparece las mismas veces.
# Con 4 efectos hay 16 combinaciones, y con 2 copias cada una el mazo tiene 32 fichas.
class Deck:
    def __init__(self, Cards):
        self.Cards = Cards      # lista de (Arriba, Abajo). En el cliente en linea son None

    @staticmethod
    def Build():
        Data = LoadData()["Deck"]
        Cards = []
        for Upper in Data["Effects"]:
            for Lower in Data["Effects"]:
                for i in range(Data["CopiesPerCombination"]):
                    Cards.append((Upper, Lower))
        random.shuffle(Cards)
        return Deck(Cards)

    # Mazo que solo sabe cuantas fichas quedan (lo usa el cliente en linea)
    @staticmethod
    def Hidden(Count):
        return Deck([None] * Count)

    def Count(self):
        return len(self.Cards)

    def Draw(self):
        if len(self.Cards) == 0:
            return None
        return self.Cards.pop()
