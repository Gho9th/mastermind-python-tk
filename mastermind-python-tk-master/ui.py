import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog
import random
import json

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
        self.mode = tk.StringVar(value="joueur_devine")
        self.secret = None
        self.current_guess = []
        self.history = []
        self.ai = None
        self.turn = 0

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
        tk.Radiobutton(mode_frame, text="Joueur devine (IA choisit)", variable=self.mode, value="joueur_devine", command=self.reset_game).pack(anchor="w")
        tk.Radiobutton(mode_frame, text="IA devine (vous choisissez)", variable=self.mode, value="ia_devine", command=self.reset_game).pack(anchor="w")
        tk.Radiobutton(mode_frame, text="2 joueurs", variable=self.mode, value="deux_joueurs", command=self.reset_game).pack(anchor="w")

        # cadre pour les boutons de contrôle
        ctrl_frame = tk.Frame(top)
        ctrl_frame.pack(side="right", padx=6)

        tk.Button(ctrl_frame, text="Nouvelle partie", command=self.reset_game).pack(fill="x")
        tk.Button(ctrl_frame, text="Sauvegarder", command=self.save_game).pack(fill="x", pady=2)
        tk.Button(ctrl_frame, text="Charger", command=self.load_game).pack(fill="x", pady=2)
        tk.Button(ctrl_frame, text="Afficher règles", command=self.show_rules).pack(fill="x", pady=2)
        tk.Button(ctrl_frame, text="Quitter", command=self.quit).pack(fill="x")

        # zone principale du jeu
        game_frame = tk.Frame(self, padx=10, pady=6)
        game_frame.pack()

        # affichage du code secret
        self.secret_frame = tk.LabelFrame(game_frame, text="Code secret", padx=6, pady=6)
        self.secret_frame.grid(row=0, column=0, sticky="n")

        self.secret_pegs = []

        for i in range(CODE_LENGTH):
            c = tk.Canvas(self.secret_frame, width=PEG_SIZE, height=PEG_SIZE, bg=EMPTY_COLOR, highlightthickness=1)
            c.grid(row=0, column=i, padx=4, pady=4)
            self.secret_pegs.append(c)

        # historique des propositions et feedbacks
        hist_frame = tk.LabelFrame(game_frame, text="Historique", padx=6, pady=6)
        hist_frame.grid(row=0, column=1, padx=10)

        # scrollbar verticale
        scrollbar = tk.Scrollbar(hist_frame, orient="vertical")
        scrollbar.pack(side="right", fill="y")

        # canvas principal
        self.hist_canvas = tk.Canvas(hist_frame, width=420, height=300, yscrollcommand=scrollbar.set)
        self.hist_canvas.pack(side="left", fill="both", expand=True)

        # connecter scrollbar <-> canvas
        scrollbar.config(command=self.hist_canvas.yview)

        # frame interne scrollable
        self.hist_inner = tk.Frame(self.hist_canvas)

        # ajouter le frame dans le canvas
        self.hist_canvas.create_window((0, 0), window=self.hist_inner, anchor="nw")

        # mise à jour automatique de la zone scrollable
        self.hist_inner.bind(
            "<Configure>",
            lambda e: self.hist_canvas.configure(
                scrollregion=self.hist_canvas.bbox("all")
            )
        )

        # scroll molette souris
        self.hist_canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.hist_items = []

        # zone pour composer la proposition courante
        sel_frame = tk.LabelFrame(self, text="Composer votre proposition", padx=6, pady=6)
        sel_frame.pack(padx=10, pady=6, fill="x")

        self.guess_slots = []

        for i in range(CODE_LENGTH):
            c = tk.Canvas(sel_frame, width=PEG_SIZE, height=PEG_SIZE, bg=EMPTY_COLOR, highlightthickness=1)
            c.grid(row=0, column=i, padx=6, pady=6)
            c.bind("<Button-1>", lambda e, idx=i: self.cycle_slot(idx))
            self.guess_slots.append(c)

        # boutons de couleurs
        color_btn_frame = tk.Frame(sel_frame)
        color_btn_frame.grid(row=1, column=0, columnspan=CODE_LENGTH)

        for color_id in range(COLOR_MIN, COLOR_MAX + 1):
            b = tk.Button(color_btn_frame, bg=COLOR_MAP[color_id], width=3, command=lambda cid=color_id: self.add_color_to_guess(cid))
            b.pack(side="left", padx=4, pady=4)

        # boutons d'action
        action_frame = tk.Frame(self)
        action_frame.pack(pady=6)

        tk.Button(action_frame, text="Valider", command=self.submit_guess).pack(side="left", padx=4)
        tk.Button(action_frame, text="Effacer", command=self.clear_guess).pack(side="left", padx=4)
        tk.Button(action_frame, text="Annuler le coup", command=self.undo_move).pack(side="left", padx=4)
        tk.Button(action_frame, text="Aide", command=self.give_hint).pack(side="left", padx=4)
        tk.Button(action_frame, text="Révéler code", command=self.reveal_code).pack(side="left", padx=4)

        # démarrer une nouvelle partie
        self.reset_game()

    # -------------------- Fonctions utilitaires --------------------

    def _on_mousewheel(self, event):
        """Permet le scroll avec la molette."""
        self.hist_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def show_rules(self):
        """Affiche les règles du jeu."""
        msg = (
            f"Mastermind\n"
            f"Code de longueur {CODE_LENGTH}, couleurs {COLOR_MIN} à {COLOR_MAX}\n"
            f"Doublons autorisés\n"
            f"Feedback: noirs = bonne couleur & position, "
            f"blancs = bonne couleur mauvaise position\n"
            f"Vous avez {MAX_TURNS} essais"
        )
        messagebox.showinfo("Règles", msg)

    def reset_game(self):
        """
        Réinitialise l'état du jeu selon le mode sélectionné.
        """
        self.history.clear()
        self.turn = 0
        self.current_guess = [None] * CODE_LENGTH
        self.clear_history_canvas()
        self.clear_guess()
        self.ai = None
        self.secret = None

        mode = self.mode.get()
        
        if mode == "joueur_devine":
            self.secret = [
                random.randint(COLOR_MIN, COLOR_MAX)
                for _ in range(CODE_LENGTH)
            ]

            for c in self.secret_pegs:
                c.configure(bg=EMPTY_COLOR)

        elif mode == "ia_devine":
            code = self.ask_secret_dialog()
            if code is None:
                self.secret = [
                    random.randint(COLOR_MIN, COLOR_MAX)
                    for _ in range(CODE_LENGTH)
                ]
            else:
                self.secret = code
            for c in self.secret_pegs:
                c.configure(bg=EMPTY_COLOR)

            self.ai = SimpleAI()
            self.after(500, self.ai_make_move)
            
        elif mode == "deux_joueurs":
            code = self.ask_secret_dialog(hidden=True)
            if code is None:
                self.secret = [
                    random.randint(COLOR_MIN, COLOR_MAX)
                    for _ in range(CODE_LENGTH)
                ]
            else:
                self.secret = code

            for c in self.secret_pegs:
                c.configure(bg=EMPTY_COLOR)

    def ask_secret_dialog(self, hidden=False):
        """
        Ouvre une boîte de dialogue pour saisir le code secret.
        """
        prompt = (
            f"Entrez le code secret "
            f"({CODE_LENGTH} chiffres séparés par espaces, "
            f"{COLOR_MIN}-{COLOR_MAX})"
        )
        s = simpledialog.askstring("Code secret", prompt, parent=self)
        
        if s is None:
            return None
            
        parts = s.strip().split()

        if len(parts) != CODE_LENGTH:
            messagebox.showerror("Erreur", "Nombre de valeurs incorrect.")
            return None

        try:
            nums = [int(x) for x in parts]

        except ValueError:
            messagebox.showerror("Erreur", "Entrée invalide.")
            return None

        for n in nums:
            if n < COLOR_MIN or n > COLOR_MAX:
                messagebox.showerror(
                    "Erreur",
                    f"Valeurs doivent être entre {COLOR_MIN} et {COLOR_MAX}."
                )
                return None
                
        if not hidden:
            for i, val in enumerate(nums):
                self.secret_pegs[i].configure(bg=COLOR_MAP[val]
        return nums

    def clear_guess(self):
        """Remet la proposition courante à vide."""
        self.current_guess = [None] * CODE_LENGTH
        for c in self.guess_slots:
            c.configure(bg=EMPTY_COLOR)

    def cycle_slot(self, idx):
        """
        Permet de cliquer sur un slot pour faire défiler les couleurs.
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
        Ajoute une couleur dans le premier emplacement vide.
        """
        for i in range(CODE_LENGTH):
            if self.current_guess[i] is None:
                self.current_guess[i] = color_id
                self.guess_slots[i].configure(bg=COLOR_MAP[color_id])
                return

        self.current_guess[-1] = color_id
        self.guess_slots[-1].configure(bg=COLOR_MAP[color_id])

    def submit_guess(self):
        """
        Valide la proposition du joueur.
        """
        if None in self.current_guess:
            messagebox.showwarning(
                "Attention",
                "Complétez votre proposition avant de valider."
            )
            return
            
        guess = list(self.current_guess)
        mode = self.mode.get()

        if mode == "joueur_devine":
            self.turn += 1
            noirs, blancs = score(self.secret, guess)
            self.history.append((guess, (noirs, blancs)))
            self.draw_history_row(guess, noirs, blancs)

            if noirs == CODE_LENGTH:
                messagebox.showinfo(
                    "Gagné",
                    f"Bravo ! Vous avez trouvé le code en {self.turn} essais."
                )
                self.reveal_code(show_msg=False)
                return

            if self.turn >= MAX_TURNS:
                messagebox.showinfo(
                    "Perdu",
                    f"Vous avez épuisé vos essais. "
                    f"Le code était {' '.join(map(str, self.secret))}."
                )
                self.reveal_code(show_msg=False)
                return
            self.clear_guess()

        elif mode == "deux_joueurs":
            self.turn += 1
            noirs, blancs = score(self.secret, guess)
            self.history.append((guess, (noirs, blancs)))
            self.draw_history_row(guess, noirs, blancs)

            if noirs == CODE_LENGTH:
                messagebox.showinfo(
                    "Gagné", f"Joueur 2 a trouvé le code en {self.turn} essais.")
                self.reveal_code(show_msg=False)
                return

            if self.turn >= MAX_TURNS:
                messagebox.showinfo(
                    "Perdu",
                    f"Joueur 2 a épuisé ses essais. "
                    f"Le code était {' '.join(map(str, self.secret))}."
                )
                self.reveal_code(show_msg=False)
                return
            self.clear_guess()

        elif mode == "ia_devine":
            messagebox.showinfo(
                "Info",
                "Mode IA devine: l'IA joue automatiquement."
            )

    def draw_history_row(self, guess, noirs, blancs):
        """
        Dessine une ligne dans la zone historique.
        """
        y = 10 + len(self.hist_items) * 40
        x = 10
        # proposition
        for i, val in enumerate(guess):
            self.hist_canvas.create_rectangle(x, y, x + 30, y + 30, fill=COLOR_MAP[val], outline="black")
            x += 40

        # feedback
        fx = x + 10
        fy = y + 5

        # noirs
        for i in range(noirs):

            self.hist_canvas.create_rectangle(fx, fy, fx + 10, fy + 10, fill="red", outline="black")
            fx += 12

        # blancs
        for i in range(blancs):

            self.hist_canvas.create_rectangle(fx, fy, fx + 10, fy + 10, fill="white", outline="black")
            fx += 12

        # mémoriser
        self.hist_items.append((guess, noirs, blancs))

        # update scroll
        self.hist_canvas.configure(
            scrollregion=self.hist_canvas.bbox("all")
        )

        # scroll auto
        self.hist_canvas.yview_moveto(1.0)

    def clear_history_canvas(self):
        """Efface la zone historique."""
        self.hist_canvas.delete("all")
        self.hist_inner = tk.Frame(self.hist_canvas)
        self.hist_canvas.create_window(
            (0, 0), window=self.hist_inner, anchor="nw")
        self.hist_items.clear()
        self.hist_canvas.configure(scrollregion=self.hist_canvas.bbox("all"))

    def reveal_code(self, show_msg=True):
        """Affiche le code secret."""
        for i, val in enumerate(self.secret):
            self.secret_pegs[i].configure(bg=COLOR_MAP[val])

        if show_msg:
            messagebox.showinfo(
                "Code révélé",
                "Le code secret a été affiché."
            )

    def ai_make_move(self):
        """
        Boucle de jeu de l'IA.
        """
        if self.mode.get() != "ia_devine":
            return

        if self.ai is None:
            self.ai = SimpleAI()

        if self.turn >= MAX_TURNS:

            messagebox.showinfo(
                "Fin",
                "L'IA n'a pas trouvé le code."
            )
            return

        guess = self.ai.next_guess()
        self.turn += 1
        noirs, blancs = score(self.secret, guess)
        self.history.append((guess, (noirs, blancs)))
        self.draw_history_row(guess, noirs, blancs)

        if noirs == CODE_LENGTH:
            messagebox.showinfo(
                "IA a gagné",
                f"L'IA a trouvé le code en {self.turn} essais."
            )
            self.reveal_code(show_msg=False)
            return
        self.ai.feedback(guess, noirs, blancs)

        if not self.ai.possibilities:
            messagebox.showwarning(
                "Erreur",
                "L'IA n'a plus de possibilités compatibles."
            )
            return
        self.after(700, self.ai_make_move)

    def save_game(self):
        """Sauvegarde l'état de la partie."""
        if self.secret is None:
            messagebox.showwarning(
                "Attention",
                "Aucune partie en cours."
            )
            return

        data = {
            "mode": self.mode.get(),
            "secret": self.secret,
            "history": self.history,
            "turn": self.turn
        }
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("Fichiers JSON", "*.json")]
        )

        if filepath:
            with open(filepath, "w") as f:
                json.dump(data, f)
            messagebox.showinfo(
                "Sauvegarde",
                "La partie a été sauvegardée avec succès."
            )

    def load_game(self):
        """Charge une partie depuis un fichier JSON."""
        filepath = filedialog.askopenfilename(
            filetypes=[("Fichiers JSON", "*.json")]
        )
        if filepath:
            with open(filepath, "r") as f:
                data = json.load(f)
            self.mode.set(data["mode"])
            self.secret = data["secret"]
            self.history = data["history"]
            self.turn = data["turn"]

            # restaurer affichage
            self.clear_guess()
            self.clear_history_canvas()

            for c in self.secret_pegs:
                c.configure(bg=EMPTY_COLOR)

            for guess, (noirs, blancs) in self.history:
                self.draw_history_row(guess, noirs, blancs)

            messagebox.showinfo(
                "Chargement",
                "La partie a été chargée avec succès."
            )

    def undo_move(self):
        """Annule le dernier essai."""
        if not self.history:
            messagebox.showinfo(
                "Info",
                "Aucun coup à annuler."
            )
            return

        self.history.pop()
        self.turn -= 1
        self.clear_history_canvas()

        for guess, (noirs, blancs) in self.history:
            self.draw_history_row(guess, noirs, blancs)

    def give_hint(self):
        """Fournit un code compatible avec les indices précédents."""

        if self.mode.get() == "ia_devine":
            messagebox.showinfo(
                "Aide",
                "L'IA joue toute seule dans ce mode."
            )
            return
        helper_ai = SimpleAI()

        for past_guess, (n, b) in self.history:
            helper_ai.feedback(past_guess, n, b)

        if not helper_ai.possibilities:
            messagebox.showwarning(
                "Aide",
                "Aucune combinaison possible trouvée."
            )
            return

        hint = random.choice(helper_ai.possibilities)
        hint_colors = [COLOR_MAP[c] for c in hint]

        messagebox.showinfo(
            "Aide",
            f"Un code compatible serait : {hint}\n"
            f"(Couleurs: {', '.join(hint_colors)})"
        )
