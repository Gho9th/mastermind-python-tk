import tkinter as tk
from tkinter import messagebox, simpledialog
import random

from utils import *
from ai import SimpleAI


class MastermindApp(tk.Tk):
    """
    Classe principale de l'application Tkinter.
    Elle contient l'état du jeu et les méthodes pour construire
    et mettre à jour l'interface.
    """
    def __init__(self):
        super().__init__()
        self.title("Mastermind")
        self.resizable(False, False)

        # état du jeu
        self.mode = tk.StringVar(value="joueur_devine")  # mode sélectionné
        self.secret = None               # code secret (liste d'entiers)
        self.current_guess = []          # proposition en cours
        self.history = []                # historique des essais [(guess, (noirs, blancs)), ...]
        self.ai = None                   # instance de l'IA si utilisée
        self.turn = 0                    # numéro d'essai courant

        # construire l'interface graphique
        self._build_ui()

    def _build_ui(self):
        """Crée et place tous les widgets de l'interface."""
        # zone supérieure pour les contrôles
        top = tk.Frame(self, padx=10, pady=10)
        top.pack(fill="x")

        # cadre pour choisir le mode de jeu
        mode_frame = tk.LabelFrame(top, text="Mode", padx=6, pady=6)
        mode_frame.pack(side="left", padx=6)
        # trois modes : joueur devine, IA devine, deux joueurs
        tk.Radiobutton(mode_frame, text="Joueur devine (IA choisit)", variable=self.mode,
                       value="joueur_devine", command=self.reset_game).pack(anchor="w")
        tk.Radiobutton(mode_frame, text="IA devine (vous choisissez)", variable=self.mode,
                       value="ia_devine", command=self.reset_game).pack(anchor="w")
        tk.Radiobutton(mode_frame, text="2 joueurs", variable=self.mode,
                       value="deux_joueurs", command=self.reset_game).pack(anchor="w")

        # cadre pour les boutons de contrôle
        ctrl_frame = tk.Frame(top)
        ctrl_frame.pack(side="right", padx=6)
        tk.Button(ctrl_frame, text="Nouvelle partie", command=self.reset_game).pack(fill="x")
        tk.Button(ctrl_frame, text="Afficher règles", command=self.show_rules).pack(fill="x", pady=4)
        tk.Button(ctrl_frame, text="Quitter", command=self.quit).pack(fill="x")

        # zone principale du jeu
        game_frame = tk.Frame(self, padx=10, pady=6)
        game_frame.pack()

        # affichage du code secret (cases vides ou masquées)
        self.secret_frame = tk.LabelFrame(game_frame, text="Code secret", padx=6, pady=6)
        self.secret_frame.grid(row=0, column=0, sticky="n")
        self.secret_pegs = []
        for i in range(CODE_LENGTH):
            # chaque "peg" est un Canvas carré ; on change son bg pour afficher la couleur
            c = tk.Canvas(self.secret_frame, width=PEG_SIZE, height=PEG_SIZE,
                          bg=EMPTY_COLOR, highlightthickness=1)
            c.grid(row=0, column=i, padx=4, pady=4)
            self.secret_pegs.append(c)

        # historique des propositions et feedbacks
        hist_frame = tk.LabelFrame(game_frame, text="Historique", padx=6, pady=6)
        hist_frame.grid(row=0, column=1, padx=10)
        self.hist_canvas = tk.Canvas(hist_frame, width=420, height=300)
        self.hist_canvas.pack()
        self.hist_items = []  # liste pour suivre les lignes dessinées

        # zone pour composer la proposition courante
        sel_frame = tk.LabelFrame(self, text="Composer votre proposition", padx=6, pady=6)
        sel_frame.pack(padx=10, pady=6, fill="x")
        self.guess_slots = []
        for i in range(CODE_LENGTH):
            # slots cliquables pour faire défiler les couleurs
            c = tk.Canvas(sel_frame, width=PEG_SIZE, height=PEG_SIZE,
                          bg=EMPTY_COLOR, highlightthickness=1)
            c.grid(row=0, column=i, padx=6, pady=6)
            # bind pour gérer le clic et changer la couleur du slot
            c.bind("<Button-1>", lambda e, idx=i: self.cycle_slot(idx))
            self.guess_slots.append(c)

        # boutons de couleurs pour remplir rapidement la proposition
        color_btn_frame = tk.Frame(sel_frame)
        color_btn_frame.grid(row=1, column=0, columnspan=CODE_LENGTH)
        for color_id in range(COLOR_MIN, COLOR_MAX + 1):
            # chaque bouton a un fond de la couleur correspondante
            b = tk.Button(color_btn_frame, bg=COLOR_MAP[color_id], width=3,
                          command=lambda cid=color_id: self.add_color_to_guess(cid))
            b.pack(side="left", padx=4, pady=4)

        # boutons d'action : valider, effacer, révéler
        action_frame = tk.Frame(self)
        action_frame.pack(pady=6)
        tk.Button(action_frame, text="Valider proposition", command=self.submit_guess).pack(side="left", padx=6)
        tk.Button(action_frame, text="Effacer proposition", command=self.clear_guess).pack(side="left", padx=6)
        tk.Button(action_frame, text="Révéler code", command=self.reveal_code).pack(side="left", padx=6)

        # démarrer une nouvelle partie
        self.reset_game()

    # -------------------- Fonctions utilitaires d'interface --------------------
    def show_rules(self):
        """Affiche une boîte avec les règles du jeu."""
        msg = (f"Mastermind\nCode de longueur {CODE_LENGTH}, couleurs {COLOR_MIN} à {COLOR_MAX}\n"
               f"Doublons autorisés\nFeedback: noirs = bonne couleur & position, blancs = bonne couleur mauvaise position\n"
               f"Vous avez {MAX_TURNS} essais")
        messagebox.showinfo("Règles", msg)

    def reset_game(self):
        """
        Réinitialise l'état du jeu selon le mode sélectionné.
        - joueur_devine : l'ordinateur génère un secret aléatoire
        - ia_devine : le joueur saisit un secret, l'IA commence à jouer
        - deux_joueurs : le joueur 1 saisit le secret, joueur 2 devine
        """
        # réinitialiser les structures
        self.history.clear()
        self.turn = 0
        self.current_guess = [None] * CODE_LENGTH
        self.clear_history_canvas()
        self.clear_guess()
        self.ai = None
        self.secret = None

        mode = self.mode.get()
        if mode == "joueur_devine":
            # générer un secret aléatoire et masquer l'affichage
            self.secret = [random.randint(COLOR_MIN, COLOR_MAX) for _ in range(CODE_LENGTH)]
            for c in self.secret_pegs:
                c.configure(bg=EMPTY_COLOR)
        elif mode == "ia_devine":
            # demander au joueur d'entrer le secret via une boîte de dialogue
            code = self.ask_secret_dialog()
            if code is None:
                # si annulation, fallback à un secret aléatoire
                self.secret = [random.randint(COLOR_MIN, COLOR_MAX) for _ in range(CODE_LENGTH)]
            else:
                self.secret = code
            for c in self.secret_pegs:
                c.configure(bg=EMPTY_COLOR)
            # initialiser l'IA et lancer son premier coup après un court délai
            self.ai = SimpleAI()
            self.after(500, self.ai_make_move)
        elif mode == "deux_joueurs":
            # joueur 1 saisit le secret (masqué)
            code = self.ask_secret_dialog(hidden=True)
            if code is None:
                self.secret = [random.randint(COLOR_MIN, COLOR_MAX) for _ in range(CODE_LENGTH)]
            else:
                self.secret = code
            for c in self.secret_pegs:
                c.configure(bg=EMPTY_COLOR)

    def ask_secret_dialog(self, hidden=False):
        """
        Ouvre une boîte de dialogue pour saisir le code secret.
        Format attendu : chiffres séparés par des espaces, ex. "1 3 4 2".
        Si hidden==False on affiche le code dans la zone 'Code secret'.
        """
        prompt = f"Entrez le code secret ({CODE_LENGTH} chiffres séparés par espaces, {COLOR_MIN}-{COLOR_MAX})"
        s = simpledialog.askstring("Code secret", prompt, parent=self)
        if s is None:
            return None  # utilisateur a annulé
        parts = s.strip().split()
        if len(parts) != CODE_LENGTH:
            messagebox.showerror("Erreur", "Nombre de valeurs incorrect.")
            return None
        try:
            nums = [int(x) for x in parts]
        except ValueError:
            messagebox.showerror("Erreur", "Entrée invalide.")
            return None
        # validation des bornes
        for n in nums:
            if n < COLOR_MIN or n > COLOR_MAX:
                messagebox.showerror("Erreur", f"Valeurs doivent être entre {COLOR_MIN} et {COLOR_MAX}.")
                return None
        # si on ne masque pas, afficher les couleurs dans la zone secret
        if not hidden:
            for i, val in enumerate(nums):
                self.secret_pegs[i].configure(bg=COLOR_MAP[val])
        return nums

    def clear_guess(self):
        """Remet la proposition courante à vide (None) et met à jour l'affichage."""
        self.current_guess = [None] * CODE_LENGTH
        for c in self.guess_slots:
            c.configure(bg=EMPTY_COLOR)

    def cycle_slot(self, idx):
        """
        Permet de cliquer sur un slot pour faire défiler les couleurs.
        - None -> COLOR_MIN -> COLOR_MIN+1 -> ... -> None
        """
        cur = self.current_guess[idx]
        if cur is None:
            nxt = COLOR_MIN
        else:
            nxt = cur + 1
            if nxt > COLOR_MAX:
                nxt = None
        self.current_guess[idx] = nxt
        color = EMPTY_COLOR if nxt is None else COLOR_MAP[nxt]
        self.guess_slots[idx].configure(bg=color)

    def add_color_to_guess(self, color_id):
        """
        Ajoute la couleur sélectionnée dans le premier emplacement vide.
        Si tous les emplacements sont pleins, remplace le dernier.
        """
        for i in range(CODE_LENGTH):
            if self.current_guess[i] is None:
                self.current_guess[i] = color_id
                self.guess_slots[i].configure(bg=COLOR_MAP[color_id])
                return
        # si plein, remplacer le dernier
        self.current_guess[-1] = color_id
        self.guess_slots[-1].configure(bg=COLOR_MAP[color_id])

    def submit_guess(self):
        """
        Valide la proposition du joueur.
        - calcule le feedback
        - l'ajoute à l'historique et l'affiche
        - vérifie victoire ou dépassement du nombre d'essais
        """
        if None in self.current_guess:
            messagebox.showwarning("Attention", "Complétez votre proposition avant de valider.")
            return
        guess = list(self.current_guess)
        mode = self.mode.get()

        if mode == "joueur_devine":
            self.turn += 1
            noirs, blancs = score(self.secret, guess)
            self.history.append((guess, (noirs, blancs)))
            self.draw_history_row(guess, noirs, blancs)
            if noirs == CODE_LENGTH:
                messagebox.showinfo("Gagné", f"Bravo ! Vous avez trouvé le code en {self.turn} essais.")
                self.reveal_code(show_msg=False)
                return
            if self.turn >= MAX_TURNS:
                messagebox.showinfo("Perdu", f"Vous avez épuisé vos essais. Le code était {' '.join(map(str,self.secret))}.")
                self.reveal_code(show_msg=False)
                return
            self.clear_guess()

        elif mode == "deux_joueurs":
            self.turn += 1
            noirs, blancs = score(self.secret, guess)
            self.history.append((guess, (noirs, blancs)))
            self.draw_history_row(guess, noirs, blancs)
            if noirs == CODE_LENGTH:
                messagebox.showinfo("Gagné", f"Joueur 2 a trouvé le code en {self.turn} essais.")
                self.reveal_code(show_msg=False)
                return
            if self.turn >= MAX_TURNS:
                messagebox.showinfo("Perdu", f"Joueur 2 a épuisé ses essais. Le code était {' '.join(map(str,self.secret))}.")
                self.reveal_code(show_msg=False)
                return
            self.clear_guess()

        elif mode == "ia_devine":
            # en mode IA devine, l'utilisateur n'envoie pas de propositions manuelles
            messagebox.showinfo("Info", "Mode IA devine: l'IA joue automatiquement. Utilisez 'Révéler code' si nécessaire.")
            return

    def draw_history_row(self, guess, noirs, blancs):
        """
        Dessine une ligne dans la zone historique :
        - les pions de la proposition (carrés colorés)
        - les petits pions de feedback (noirs/blancs)
        Les positions sont calculées en fonction du nombre d'éléments déjà affichés.
        """
        y = 10 + len(self.hist_items) * 40  # position verticale selon le nombre de lignes
        x = 10
        # dessiner les pions de la proposition en carrés
        for i, val in enumerate(guess):
            self.hist_canvas.create_rectangle(x, y, x+30, y+30, fill=COLOR_MAP[val], outline="black")
            x += 40
        # dessiner les pions de feedback (petits carrés)
        fx = x + 10
        fy = y + 5
        for i in range(noirs):
            self.hist_canvas.create_rectangle(fx, fy, fx+10, fy+10, fill="black", outline="black")
            fx += 12
        for i in range(blancs):
            self.hist_canvas.create_rectangle(fx, fy, fx+10, fy+10, fill="white", outline="black")
            fx += 12
        # mémoriser la ligne ajoutée
        self.hist_items.append((guess, noirs, blancs))

    def clear_history_canvas(self):
        """Efface la zone historique et réinitialise la liste interne."""
        self.hist_canvas.delete("all")
        self.hist_items.clear()

    def reveal_code(self, show_msg=True):
        """Affiche le code secret dans la zone prévue et optionnellement un message."""
        for i, val in enumerate(self.secret):
            self.secret_pegs[i].configure(bg=COLOR_MAP[val])
        if show_msg:
            messagebox.showinfo("Code révélé", "Le code secret a été affiché.")

    def ai_make_move(self):
        """
        Boucle de jeu de l'IA (mode ia_devine) :
        - l'IA propose un code
        - on calcule le feedback et on l'affiche
        - on filtre les possibilités de l'IA
        - on relance après un délai si nécessaire
        """
        if self.mode.get() != "ia_devine":
            return
        if self.ai is None:
            self.ai = SimpleAI()
        if self.turn >= MAX_TURNS:
            messagebox.showinfo("Fin", "L'IA n'a pas trouvé le code dans le nombre d'essais autorisés.")
            return
        guess = self.ai.next_guess()
        self.turn += 1
        noirs, blancs = score(self.secret, guess)
        self.history.append((guess, (noirs, blancs)))
        self.draw_history_row(guess, noirs, blancs)
        if noirs == CODE_LENGTH:
            messagebox.showinfo("IA a gagné", f"L'IA a trouvé le code en {self.turn} essais.")
            self.reveal_code(show_msg=False)
            return
        # fournir le feedback à l'IA pour qu'elle filtre ses possibilités
        self.ai.feedback(guess, noirs, blancs)
        if not self.ai.possibilities:
            messagebox.showwarning("Erreur", "L'IA n'a plus de possibilités compatibles. Vérifiez le code ou les retours.")
            return
        # planifier le prochain coup de l'IA après 700 ms (pour voir l'évolution)
        self.after(700, self.ai_make_move)