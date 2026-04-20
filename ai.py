# fichier de l'IA

import random
from utils import all_possible_codes, score

class SimpleAI:
    """
    IA basique pour le mode 'IA devine'.
    - garde une liste de possibilités compatibles
    - choisit une proposition au hasard parmi elles
    - après feedback, filtre les possibilités
    Cette IA n'est pas optimale mais fonctionne pour démonstration.
    """
    def __init__(self):
        # initialiser toutes les possibilités
        self.possibilities = all_possible_codes()
        random.shuffle(self.possibilities)  # mélanger pour varier les parties
        self.last_guess = None

    def next_guess(self):
        """Retourne la prochaine proposition de l'IA."""
        if not self.last_guess:
            # première proposition aléatoire
            self.last_guess = random.choice(self.possibilities)
            return self.last_guess
        # proposition suivante aléatoire parmi les possibilités restantes
        self.last_guess = random.choice(self.possibilities)
        return self.last_guess

    def feedback(self, guess, noirs, blancs):
        """
        Filtre la liste des possibilités en ne gardant que celles
        qui donneraient le même feedback si elles étaient le secret.
        """
        nouvelles = []
        for code in self.possibilities:
            n, b = score(code, guess)
            if n == noirs and b == blancs:
                nouvelles.append(code)
        self.possibilities = nouvelles