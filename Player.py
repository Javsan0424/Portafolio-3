class Player():
    def __init__(self, Name = "Jugador"):
        self.Name = Name
        self.maxHealt = 100
        self.currentHealth = self.maxHealt

        self.Hand = []

    def TakeDamage(self, amount):
        self.currentHealth = max(0, self.currentHealth - amount)

    def Heal(self, amount):
        self.currentHealth = min(self.maxHealt, self.currentHealth + amount)