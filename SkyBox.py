import pygame
from Resources import ResourcePath, LoadData

pygame.init()

# Los frames se guardan a la mitad del tamano de pantalla para que 64 frames no ocupen demasiada memoria.
# Se escalan a pantalla completa solo cuando cambia el frame (10 veces por segundo).
PreloadFactor = 0.5


class SkyBox:
    def __init__(self, ScreenSize, RateChange = 100):
        Data = LoadData()["SkyBox"]
        SmallSize = (int(ScreenSize[0] * PreloadFactor), int(ScreenSize[1] * PreloadFactor))

        # Se carga todo una sola vez al abrir el juego
        self.Frames = []
        for i in range(1, Data["frames"] + 1):
            Image = pygame.image.load(ResourcePath(Data[str(i)])).convert()
            self.Frames.append(pygame.transform.scale(Image, SmallSize))

        self.ScreenSize = ScreenSize
        self.RateChange = RateChange
        self.Index = 0
        self.LastTickUpdate = pygame.time.get_ticks()
        self.Current = pygame.transform.scale(self.Frames[0], ScreenSize)

    def Update(self, Tickcount):
        if Tickcount - self.LastTickUpdate >= self.RateChange:
            self.Index = (self.Index + 1) % len(self.Frames)
            self.Current = pygame.transform.scale(self.Frames[self.Index], self.ScreenSize)
            self.LastTickUpdate = Tickcount

    def Draw(self, Screen):
        Screen.blit(self.Current, (0, 0))