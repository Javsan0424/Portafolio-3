import json
import pygame

pygame.init()



def ChangeFrame(SkyboxFrame, Image, LastTickUpdate, Tickcount, rateChange ):
    with open('data.json', 'r', encoding='utf-8') as file:
        data = json.load(file)

    if Tickcount - LastTickUpdate >= rateChange:

        SkyboxFrame += 1
        if SkyboxFrame > 64:
            SkyboxFrame = 1

        Image = pygame.image.load(data["SkyBox"][str(SkyboxFrame)])
        LastTickUpdate = Tickcount
        
    return SkyboxFrame, Image, LastTickUpdate