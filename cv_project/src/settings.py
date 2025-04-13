import pygame

class Settings:
    """Manages game settings including volume and sensitivity."""
    def __init__(self):
        self.volume = 0.5
        self.sensitivity = 20

    def adjust_settings(self, screen):
        font = pygame.font.Font(None, 36)
        while True:
            screen.fill((0, 0, 0))
            text = font.render("Settings", True, (255, 255, 255))
            screen.blit(text, (350, 50))
            pygame.draw.rect(screen, (255, 0, 0), (300, 150, self.sensitivity * 2, 20))
            pygame.draw.rect(screen, (0, 255, 0), (300, 150, 40, 20), 2)
            pygame.draw.rect(screen, (255, 0, 0), (300, 250, int(self.volume * 200), 20))
            pygame.draw.rect(screen, (0, 255, 0), (300 + int(self.volume * 200) - 5, 250, 10, 20), 2)
            for event in pygame.event.get():
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if 300 <= event.pos[0] <= 500 and 150 <= event.pos[1] <= 170:
                        self.sensitivity = max(10, min(50, (event.pos[0] - 300) // 2))
                    if 300 <= event.pos[0] <= 500 and 250 <= event.pos[1] <= 270:
                        self.volume = max(0, min(1, (event.pos[0] - 300) / 200))
                    pygame.mixer.music.set_volume(self.volume)
                if event.type == pygame.MOUSEBUTTONUP:
                    return
            pygame.display.flip()