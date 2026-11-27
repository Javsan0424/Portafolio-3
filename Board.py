import pygame
from CreateCard import CELL

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

    def PieceCells(self, Row, Col, Horizontal):
        if Horizontal:
            return [(Row, Col), (Row, Col + 1)]
        return [(Row, Col), (Row + 1, Col)]

    # Devuelve (plan, motivo). Si la jugada no es valida el plan es None
    def Evaluate(self, Card, Row, Col, Horizontal):
        Positions = self.PieceCells(Row, Col, Horizontal)
        Effects = [Card.UpperEffect, Card.LowerEffect]

        for Pos in Positions:
            if Pos[0] < 0 or Pos[0] >= Rows or Pos[1] < 0 or Pos[1] >= Cols:
                return None, "La ficha se sale del tablero"
            if Pos in self.Cells:
                return None, "Esa casilla ya esta ocupada"

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

    def Place(self, Card, Row, Col, Horizontal, Owner, Plan):
        Surf = Card.GetSurface(Horizontal)
        Rect = Surf.get_rect(topleft = (GridRect.x + Col * CELL, GridRect.y + Row * CELL))
        self.Pieces.append({"Surf": Surf, "Rect": Rect, "Owner": Owner})

        for Item in Plan:
            self.Cells[Item["Pos"]] = {"Effect": Item["Effect"], "Chain": Item["Chain"],
                                       "Owner": Owner, "Cut": False, "Active": None}

    def Resolve(self, Plan, Owner, Players):
        Rival = 1 - Owner

        for Item in Plan:
            Cell = self.Cells[Item["Pos"]]
            Chain = Item["Chain"]
            Kind = Item["Effect"]

            # Si esta mitad corta, solo corta y no hace dano
            if len(Item["Cuts"]) > 0:
                for CutPos in Item["Cuts"]:
                    Target = self.Cells[CutPos]
                    Target["Cut"] = True
                    if Target["Active"] in self.Effects:
                        self.Effects.remove(Target["Active"])
                    Target["Active"] = None
                continue

            if Kind == "Impact":
                Players[Rival].TakeDamage(6 + 5 * (Chain - 1))

            elif Kind == "Drain":
                Amount = 3 + 2 * (Chain - 1)
                Players[Rival].TakeDamage(Amount)
                Players[Owner].Heal(Amount)

            elif Kind == "Fire":
                Fx = {"Kind": "Fire", "Owner": Owner, "Value": 12 + 3 * (Chain - 1)}
                Players[Rival].TakeDamage(Fx["Value"])
                self.Effects.append(Fx)
                Cell["Active"] = Fx

            elif Kind == "Poison":
                Fx = {"Kind": "Poison", "Owner": Owner, "Value": Chain, "Turns": 5}
                self.Effects.append(Fx)
                Cell["Active"] = Fx

    # Se llama al empezar el turno de Victim
    def Tick(self, Victim, Players):
        for Fx in list(self.Effects):
            if Fx["Owner"] == Victim:
                continue

            if Fx["Kind"] == "Fire":
                Fx["Value"] -= 4
                if Fx["Value"] <= 0:
                    self.Effects.remove(Fx)
                else:
                    Players[Victim].TakeDamage(Fx["Value"])

            elif Fx["Kind"] == "Poison":
                Players[Victim].TakeDamage(Fx["Value"])
                Fx["Value"] += 1
                Fx["Turns"] -= 1
                if Fx["Turns"] <= 0:
                    self.Effects.remove(Fx)

    def Draw(self, Screen, Font, Colors):
        for Piece in self.Pieces:
            Screen.blit(Piece["Surf"], Piece["Rect"])
            pygame.draw.rect(Screen, Colors[Piece["Owner"]], Piece["Rect"], 2)

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
                Text = Font.render("x" + str(Cell["Chain"]), True, "white")
                Screen.blit(Text, Text.get_rect(center = CellRect.center))