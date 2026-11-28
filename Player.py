class Player():
    def __init__(self, Name = "Jugador"):
        self.Name = Name
        self.maxHealt = 100
        self.currentHealth = self.maxHealt

        self.Hand = []

    # Devuelve cuanta vida se perdio de verdad (para los numeros flotantes)
    def TakeDamage(self, amount):
        Before = self.currentHealth
        self.currentHealth = max(0, self.currentHealth - amount)
        return Before - self.currentHealth

    def Heal(self, amount):
        Before = self.currentHealth
        self.currentHealth = min(self.maxHealt, self.currentHealth + amount)
        return self.currentHealth - Before