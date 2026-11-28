import math
from Events import EffectStarted


# Strategy: cada efecto sabe aplicarse y avanzar un turno. Board solo llama a estos metodos.
class Effect:
    Name = ""
    Letter = ""

    # Se llama al colocar la mitad de la ficha que tiene este efecto
    def Apply(self, Match, Board, Cell, Owner, Chain):
        pass

    # Se llama al empezar el turno de la victima. Devuelve True cuando el efecto termino
    def Tick(self, Match, Fx, Victim):
        return True

    def TurnsLeft(self, Fx):
        return 0


class ImpactEffect(Effect):
    Name = "Impacto"
    Letter = "I"

    def Apply(self, Match, Board, Cell, Owner, Chain):
        Match.DealDamage(1 - Owner, 6 + 5 * (Chain - 1), "Impact")


class DrainEffect(Effect):
    Name = "Drenar"
    Letter = "D"

    def Apply(self, Match, Board, Cell, Owner, Chain):
        Amount = 3 + 2 * (Chain - 1)
        Match.DealDamage(1 - Owner, Amount, "Drain")
        Match.HealPlayer(Owner, Amount, "Drain")


class FireEffect(Effect):
    Name = "Fuego"
    Letter = "F"

    def Apply(self, Match, Board, Cell, Owner, Chain):
        Fx = {"Kind": "Fire", "Owner": Owner, "Value": 12 + 3 * (Chain - 1), "Turns": None}
        Match.DealDamage(1 - Owner, Fx["Value"], "Fire")
        Board.AddEffect(Fx, Cell)
        Match.Bus.Publish(EffectStarted, Owner = Owner, Kind = "Fire", Value = Fx["Value"])

    def Tick(self, Match, Fx, Victim):
        Fx["Value"] -= 4
        if Fx["Value"] <= 0:
            return True
        Match.DealDamage(Victim, Fx["Value"], "Fire")
        return False

    def TurnsLeft(self, Fx):
        # Cuantos golpes mas va a dar antes de apagarse
        return max(0, math.ceil(Fx["Value"] / 4) - 1)


class PoisonEffect(Effect):
    Name = "Veneno"
    Letter = "V"

    def Apply(self, Match, Board, Cell, Owner, Chain):
        Fx = {"Kind": "Poison", "Owner": Owner, "Value": Chain, "Turns": 5}
        Board.AddEffect(Fx, Cell)
        Match.Bus.Publish(EffectStarted, Owner = Owner, Kind = "Poison", Value = Fx["Value"])

    def Tick(self, Match, Fx, Victim):
        Match.DealDamage(Victim, Fx["Value"], "Poison")
        Fx["Value"] += 1
        Fx["Turns"] -= 1
        return Fx["Turns"] <= 0

    def TurnsLeft(self, Fx):
        return Fx["Turns"]


# Registro: nombre del efecto -> estrategia
EffectTypes = {
    "Impact": ImpactEffect(),
    "Drain": DrainEffect(),
    "Fire": FireEffect(),
    "Poison": PoisonEffect()
}
