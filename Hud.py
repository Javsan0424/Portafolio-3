import random
import pygame
import UI
from Events import Damage, Heal, TurnChanged, InvalidMove
from Effects import EffectTypes

BannerFont = pygame.font.SysFont("Arial", 44, bold=True)


# Observer de la UI: se suscribe a los eventos y dibuja la retroalimentacion visual
class Hud:
    def __init__(self, App):
        self.App = App
        self.Floating = []      # numeros de dano y curacion que suben y se desvanecen
        self.Banner = None      # aviso de cambio de turno
        self.Message = None     # mensaje corto (jugada invalida)

        App.Bus.Subscribe(Damage, self.OnDamage)
        App.Bus.Subscribe(Heal, self.OnHeal)
        App.Bus.Subscribe(TurnChanged, self.OnTurnChanged)
        App.Bus.Subscribe(InvalidMove, self.OnInvalidMove)

    def GetMatch(self):
        if self.App.Session is None:
            return None
        return self.App.Session.Match

    def AddFloating(self, Target, Text, Color):
        Match = self.GetMatch()
        if Match is None:
            return
        # Sale cerca de la barra de vida del jugador afectado
        Y = 60
        if Target == Match.BottomIndex():
            Y = 735
        X = 600 + random.randint(-140, 140)
        self.Floating.append({"Text": Text, "Color": Color, "X": X, "Y": Y, "Life": 70})

    def OnDamage(self, Target, Amount, Source):
        Letter = EffectTypes[Source].Letter
        self.AddFloating(Target, "-" + str(Amount) + " " + Letter, (255, 90, 90))

    def OnHeal(self, Target, Amount, Source):
        Letter = EffectTypes[Source].Letter
        self.AddFloating(Target, "+" + str(Amount) + " " + Letter, (110, 255, 130))

    def OnTurnChanged(self, Turn, Player):
        Match = self.GetMatch()
        if Match is None:
            return
        if Match.Mode == "Online":
            if Player == Match.LocalIndex:
                Text = "Turno " + str(Turn) + ": tu turno"
            else:
                Text = "Turno " + str(Turn) + ": turno del rival"
        else:
            Text = "Turno " + str(Turn) + ": " + Match.Players[Player].Name
        self.Banner = {"Text": Text, "Color": UI.PlayerColors[Player], "Life": 100}

    def OnInvalidMove(self, Player, Reason):
        Match = self.GetMatch()
        if Match is None:
            return
        # En linea solo mostramos tus propias jugadas invalidas
        if Match.Mode == "Online" and Player != Match.LocalIndex:
            return
        self.Message = {"Text": Reason, "Life": 160}

    def Update(self):
        for Item in list(self.Floating):
            Item["Y"] -= 1
            Item["Life"] -= 1
            if Item["Life"] <= 0:
                self.Floating.remove(Item)

        if self.Banner is not None:
            self.Banner["Life"] -= 1
            if self.Banner["Life"] <= 0:
                self.Banner = None

        if self.Message is not None:
            self.Message["Life"] -= 1
            if self.Message["Life"] <= 0:
                self.Message = None

    def CurrentMessage(self):
        if self.Message is None:
            return ""
        return self.Message["Text"]

    def Clear(self):
        self.Floating = []
        self.Banner = None
        self.Message = None

    def Draw(self, Screen):
        for Item in self.Floating:
            Label = UI.Font.render(Item["Text"], True, Item["Color"])
            Shadow = UI.Font.render(Item["Text"], True, (0, 0, 0))
            Alpha = min(255, Item["Life"] * 8)
            Label.set_alpha(Alpha)
            Shadow.set_alpha(Alpha)
            Screen.blit(Shadow, (Item["X"] + 2, Item["Y"] + 2))
            Screen.blit(Label, (Item["X"], Item["Y"]))

        if self.Banner is not None:
            Label = BannerFont.render(self.Banner["Text"], True, self.Banner["Color"])
            Shadow = BannerFont.render(self.Banner["Text"], True, (0, 0, 0))
            Alpha = min(255, self.Banner["Life"] * 6)
            Label.set_alpha(Alpha)
            Shadow.set_alpha(Alpha)
            Center = (UI.ScreenWidth // 2, 400)
            Screen.blit(Shadow, Shadow.get_rect(center = (Center[0] + 3, Center[1] + 3)))
            Screen.blit(Label, Label.get_rect(center = Center))

    # Efectos activos sobre cada jugador (lee Board.Effects). Fuego y Veneno con valor y turnos restantes
    def DrawEffects(self, Screen, Match, X, Y):
        for Index in range(2):
            Header = UI.SmallFont.render("Efectos sobre " + UI.PlayerTags[Index], True, UI.PlayerColors[Index])
            Screen.blit(Header, (X, Y))
            Y += 20

            # Un efecto del rival hace dano a este jugador
            OnPlayer = [Fx for Fx in Match.Board.Effects if Fx["Owner"] != Index]
            if len(OnPlayer) == 0:
                Screen.blit(UI.TinyFont.render("Sin efectos", True, (160, 160, 160)), (X + 8, Y))
                Y += 18

            for i in range(len(OnPlayer)):
                if i == 3:
                    More = UI.TinyFont.render("+" + str(len(OnPlayer) - 3) + " más", True, "white")
                    Screen.blit(More, (X + 8, Y))
                    Y += 18
                    break
                Fx = OnPlayer[i]
                Strategy = EffectTypes[Fx["Kind"]]
                Text = Strategy.Letter + " " + Strategy.Name + " " + str(Fx["Value"]) + " | " + str(Strategy.TurnsLeft(Fx)) + " turnos"
                Screen.blit(UI.TinyFont.render(Text, True, "white"), (X + 8, Y))
                Y += 18
            Y += 8
