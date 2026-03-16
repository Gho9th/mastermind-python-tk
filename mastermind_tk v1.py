import tkinter as tk
from tkinter import messagebox
import random

# --- Configuration du jeu --
CODE_LENGTH = 4
COLOR_MIN = 1
COLOR_MAX = 4
MAX_TURNS = 12

def score(secret, guess):
    """Calcule les pions bien placés (noirs) et mal placés (blancs)."""
    bien_places = sum(1 for a, b in zip(secret, guess) if a == b)

    secret_restant = [a for a, b in zip(secret, guess) if a != b]
    guess_restant = [b for a, b in zip(secret, guess) if a != b]

    mal_places = 0
    freq = {}
    for c in secret_restant:
        freq[c] = freq.get(c, 0) + 1
    for g in guess_restant:
        if freq.get(g, 0) > 0:
            mal_places += 1
            freq[g] -= 1

    return bien_places, mal_places

class MastermindBasique(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Mastermind - Version Primitive")
        self.geometry("350x400")
        
        # État du jeu
        self.secret = []
        self.turn = 0
        
        # --- Interface Graphique ---
        tk.Label(self, text=f"Trouvez le code de {CODE_LENGTH} chiffres (de {COLOR_MIN} à {COLOR_MAX})", pady=10).pack()

        # Historique des coups
        self.history_list = tk.Listbox(self, width=45, height=MAX_TURNS)
        self.history_list.pack(pady=10)

        # Zone de saisie
        input_frame = tk.Frame(self)
        input_frame.pack(pady=10)

        self.spinboxes = []
        for _ in range(CODE_LENGTH):
            # De simples compteurs de 1 à 6
            sb = tk.Spinbox(input_frame, from_=COLOR_MIN, to=COLOR_MAX, width=3, font=("Arial", 14))
            sb.pack(side="left", padx=5)
            self.spinboxes.append(sb)

        # Bouton de validation
        tk.Button(self, text="Valider ma proposition", command=self.valider_coup).pack(pady=5)
        
        # Démarrer la première partie
        self.nouvelle_partie()

    def nouvelle_partie(self):
        """Génère un nouveau code et vide l'historique."""
        self.secret = [random.randint(COLOR_MIN, COLOR_MAX) for _ in range(CODE_LENGTH)]
        self.turn = 0
        self.history_list.delete(0, tk.END)

    def valider_coup(self):
        """Récupère la saisie, calcule le score et vérifie la victoire."""
        # Récupérer les 4 valeurs des Spinboxes
        try:
            guess = [int(sb.get()) for sb in self.spinboxes]
        except ValueError:
            messagebox.showerror("Erreur", "Veuillez n'entrer que des nombres valides.")
            return

        self.turn += 1
        bien_places, mal_places = score(self.secret, guess)

        # Afficher dans l'historique
        guess_str = " - ".join(map(str, guess))
        result_text = f"Essai {self.turn} : [ {guess_str} ] -> {bien_places} parfaits, {mal_places} mal placés"
        self.history_list.insert(tk.END, result_text)

        # Vérifier la fin de partie
        if bien_places == CODE_LENGTH:
            messagebox.showinfo("Gagné !", f"Bravo ! Vous avez trouvé en {self.turn} essais.")
            self.nouvelle_partie()
        elif self.turn >= MAX_TURNS:
            messagebox.showinfo("Perdu", f"Dommage... Le code secret était : {self.secret}")
            self.nouvelle_partie()

if __name__ == "__main__":
    app = MastermindBasique()
    app.mainloop()
