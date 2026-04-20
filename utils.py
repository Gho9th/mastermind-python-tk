# Configuration du jeu et fonctions utilitaires

import itertools 

CODE_LENGTH = 4        # nombre de pions dans le code secret
COLOR_MIN = 1          # identifiant minimal pour une couleur
COLOR_MAX = 6          # identifiant maximal pour une couleur
MAX_TURNS = 12         # nombre maximum d'essais autorisés

# Dictionnaire qui associe un identifiant (int) à un code couleur hex
# Vous pouvez ajouter des entrées ici et augmenter COLOR_MAX si besoin.
COLOR_MAP = {
    1: "#e74c3c",  # 1 -> rouge
    2: "#3498db",  # 2 -> bleu
    3: "#f1c40f",  # 3 -> jaune
    4: "#2ecc71",  # 4 -> vert
    5: "#9b59b6",  # 5 -> violet
    6: "#e67e22",  # 6 -> orange
}

# Couleur d'un emplacement vide et taille visuelle d'un pion
EMPTY_COLOR = "#bdc3c7"
PEG_SIZE = 28  # taille en pixels des cases/pions

# -------------------- Fonctions utilitaires --------------------
def score(secret, guess):
    """
    Calcule le feedback entre le code secret et une proposition.
    Retourne un tuple (noirs, blancs).
    - noirs : nombre de pions bonne couleur à la bonne position
    - blancs : nombre de pions bonne couleur mauvaise position
    Méthode :
      1. compter les noirs position par position
      2. construire deux listes sans les noirs
      3. compter les correspondances (blancs) en tenant compte des fréquences
    """
    # 1 compter les noirs
    noirs = sum(1 for a, b in zip(secret, guess) if a == b)

    # 2 construire les listes restantes (exclure les noirs)
    secret_restant = []
    guess_restant = []
    for a, b in zip(secret, guess):
        if a != b:
            secret_restant.append(a)
            guess_restant.append(b)

    # 3 compter les blancs en utilisant un dictionnaire de fréquences
    blancs = 0
    freq = {}
    for c in secret_restant:
        freq[c] = freq.get(c, 0) + 1
    for g in guess_restant:
        if freq.get(g, 0) > 0:
            blancs += 1
            freq[g] -= 1

    return noirs, blancs

def all_possible_codes():
    """
    Génère toutes les combinaisons possibles de codes.
    Utilise itertools.product pour les répétitions autorisées.
    Renvoie une liste de listes, par ex. [[1,1,1,1], [1,1,1,2], ...]
    """
    couleurs = range(COLOR_MIN, COLOR_MAX + 1)
    return [list(p) for p in itertools.product(couleurs, repeat=CODE_LENGTH)]