import pygame
import UI
from CreateCard import CELL
from Effects import EffectTypes
from Events import ChainCut

Cols = 14
Rows = 9
GridRect = pygame.Rect((1200 - Cols * CELL) // 2, 184, Cols * CELL, Rows * CELL)

# Elemento contrario de cada efecto (se usa para cortar)
Opposite = {"Fire": "Poison", "Poison": "Fire", "Impact": "Drain", "Drain": "Impact"}


class Board:
    def __init__(self):
        self.Cells = {}     # (fila, columna) -> datos de la casilla
        self.Pieces = []    # fichas colocadas (para dibujarlas)
        self.Effects = []   # efectos activos (Fuego y Veneno)

    # Devuelve [casilla de la mitad de arriba, casilla de la mitad de abajo] segun la orientacion:
    # 0 = vertical, 1 = horizontal (arriba a la izquierda), 2 = vertical invertida, 3 = horizontal invertida
    # (Row, Col) es siempre la esquina superior izquierda del espacio que ocupa la ficha
    def PieceCells(self, Row, Col, Orientation):
        if Orientation == 0:
            return [(Row, Col), (Row + 1, Col)]
        if Orientation == 1:
            return [(Row, Col), (Row, Col + 1)]
        if Orientation == 2:
            return [(Row + 1, Col), (Row, Col)]
        return [(Row, Col + 1), (Row, Col)]

    # Devuelve (plan, motivo). Si la jugada no es valida el plan es None
    def Evaluate(self, Upper, Lower, Row, Col, Orientation):
        Positions = self.PieceCells(Row, Col, Orientation)
        Effects = [Upper, Lower]

        for Pos in Positions:
            if Pos[0] < 0 or Pos[0] >= Rows or Pos[1] < 0 or Pos[1] >= Cols:
                return None, "La ficha se sale del tablero"
            if Pos in self.Cells:
                return None, "Esa casilla ya está ocupada"

        Plan = []
        Touching = False
        for i in range(2):
            r = Positions[i][0]
            c = Positions[i][1]
            Effect = Effects[i]
            Chain = 1
            Cuts = []

            for Direction in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                Neighbor = (r + Direction[0], c + Direction[1])
                if Neighbor in Positions:
                    continue
                if Neighbor not in self.Cells:
                    continue

                Touching = True
                NeighborCell = self.Cells[Neighbor]
                if NeighborCell["Cut"]:
                    continue

                if NeighborCell["Effect"] == Effect:
                    Chain = max(Chain, NeighborCell["Chain"] + 1)
                elif Opposite[Effect] == NeighborCell["Effect"]:
                    if i == 1:
                        Cuts.append(Neighbor)
                    else:
                        return None, "Para cortar tienes que usar el efecto de abajo"
                else:
                    return None, "Solo puedes encadenar iguales o cortar con el contrario"

            Plan.append({"Pos": Positions[i], "Effect": Effect, "Chain": Chain, "Cuts": Cuts})

        if len(self.Cells) > 0 and not Touching:
            return None, "La ficha debe tocar otra ficha"

        return Plan, ""

    def Place(self, Card, Row, Col, Orientation, Owner, Plan):
        Surf = Card.GetSurface(Orientation)
        Rect = Surf.get_rect(topleft = (GridRect.x + Col * CELL, GridRect.y + Row * CELL))
        self.Pieces.append({"Surf": Surf, "Rect": Rect, "Owner": Owner})

        for Item in Plan:
            self.Cells[Item["Pos"]] = {"Effect": Item["Effect"], "Chain": Item["Chain"],
                                       "Owner": Owner, "Cut": False, "Active": None}

    def AddEffect(self, Fx, Cell):
        self.Effects.append(Fx)
        Cell["Active"] = Fx

    def Resolve(self, Plan, Owner, Match):
        for Item in Plan:
            Cell = self.Cells[Item["Pos"]]

            # Si esta mitad corta, solo corta y no hace dano
            if len(Item["Cuts"]) > 0:
                for CutPos in Item["Cuts"]:
                    Target = self.Cells[CutPos]
                    Target["Cut"] = True
                    if Target["Active"] in self.Effects:
                        self.Effects.remove(Target["Active"])
                    Target["Active"] = None
                Match.Bus.Publish(ChainCut, Player = Owner, Cells = list(Item["Cuts"]))
                continue

            # Strategy: la estrategia del efecto decide que pasa
            EffectTypes[Item["Effect"]].Apply(Match, self, Cell, Owner, Item["Chain"])

    # Se llama al empezar el turno de Victim
    def Tick(self, Victim, Match):
        for Fx in list(self.Effects):
            if Fx["Owner"] == Victim:
                continue
            if EffectTypes[Fx["Kind"]].Tick(Match, Fx, Victim):
                self.Effects.remove(Fx)

    def Draw(self, Screen):
        for Piece in self.Pieces:
            Screen.blit(Piece["Surf"], Piece["Rect"])
            pygame.draw.rect(Screen, UI.PlayerColors[Piece["Owner"]], Piece["Rect"], 2)

            # Etiqueta J1/J2 en la esquina de la ficha
            Tag = UI.TinyFont.render(UI.PlayerTags[Piece["Owner"]], True, "white")
            TagRect = Tag.get_rect(bottomright = (Piece["Rect"].right - 3, Piece["Rect"].bottom - 3))
            pygame.draw.rect(Screen, (0, 0, 0), TagRect.inflate(4, 2))
            Screen.blit(Tag, TagRect)

        for Pos in self.Cells:
            Cell = self.Cells[Pos]
            CellRect = pygame.Rect(GridRect.x + Pos[1] * CELL, GridRect.y + Pos[0] * CELL, CELL, CELL)

            if Cell["Cut"]:
                Dark = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
                Dark.fill((0, 0, 0, 150))
                Screen.blit(Dark, CellRect)
                pygame.draw.line(Screen, "red", CellRect.topleft, CellRect.bottomright, 3)
                pygame.draw.line(Screen, "red", CellRect.topright, CellRect.bottomleft, 3)
            elif Cell["Chain"] > 1:
                Text = UI.SmallFont.render("x" + str(Cell["Chain"]), True, "white")
                Screen.blit(Text, Text.get_rect(center = CellRect.center))