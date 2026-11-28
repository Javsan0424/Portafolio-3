import pygame
pygame.init()

ScreenWidth = 1200
ScreenHeight = 800

Font = pygame.font.SysFont("Arial", 22, bold=True)
SmallFont = pygame.font.SysFont("Arial", 17)
BodyFont = pygame.font.SysFont("Arial", 20)
TinyFont = pygame.font.SysFont("Arial", 13, bold=True)
BigFont = pygame.font.SysFont("Arial", 72, bold=True)
TitleFont = pygame.font.SysFont("Arial", 48, bold=True)

# Indice 0 = Jugador 1, indice 1 = Jugador 2
PlayerColors = [(80, 160, 255), (255, 150, 60)]
# Etiqueta para no depender solo del color
PlayerTags = ["J1", "J2"]


def DrawButton(Screen, Rect, Text, Enabled = True, Selected = False):
    Color = (70, 70, 90)
    if not Enabled:
        Color = (45, 45, 50)
    elif Selected:
        Color = (40, 120, 70)
    elif Rect.collidepoint(pygame.mouse.get_pos()):
        Color = (110, 110, 140)

    Border = "white"
    TextColor = "white"
    if not Enabled:
        Border = (110, 110, 110)
        TextColor = (140, 140, 140)

    pygame.draw.rect(Screen, Color, Rect, border_radius=10)
    pygame.draw.rect(Screen, Border, Rect, 2, border_radius=10)
    Label = Font.render(Text, True, TextColor)
    Screen.blit(Label, Label.get_rect(center = Rect.center))


def DrawOverlay(Screen, Alpha = 170):
    Dark = pygame.Surface((ScreenWidth, ScreenHeight), pygame.SRCALPHA)
    Dark.fill((0, 0, 0, Alpha))
    Screen.blit(Dark, (0, 0))


def DrawCentered(Screen, Text, FontToUse, Color, Y):
    Label = FontToUse.render(Text, True, Color)
    Screen.blit(Label, Label.get_rect(center = (ScreenWidth // 2, Y)))


def DrawPanel(Screen, Rect, BorderColor):
    pygame.draw.rect(Screen, (35, 30, 45), Rect, border_radius=10)
    pygame.draw.rect(Screen, BorderColor, Rect, 3, border_radius=10)


# Escribe un texto largo partiendolo en lineas. Devuelve la Y donde termino
def DrawWrapped(Screen, Text, FontToUse, Color, X, Y, MaxWidth, LineHeight = 26):
    Line = ""
    for Word in Text.split(" "):
        Test = Line + Word + " "
        if FontToUse.size(Test)[0] > MaxWidth and Line != "":
            Screen.blit(FontToUse.render(Line, True, Color), (X, Y))
            Y += LineHeight
            Line = Word + " "
        else:
            Line = Test
    if Line != "":
        Screen.blit(FontToUse.render(Line, True, Color), (X, Y))
        Y += LineHeight
    return Y
