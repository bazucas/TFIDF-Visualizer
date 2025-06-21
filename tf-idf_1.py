import tkinter as tk
from tkinter import messagebox, font as tkfont
import math
from collections import defaultdict

# ───────────────────────────── UI TRANSLATIONS ────────────────────────────────
TR = {
    'pt': {
        'matrix':      'Matriz termo‑documento (1ª linha é cabeçalho):',
        'calculate':   'Calcular',
        'table_tf':    'Pesos TF (log‑freq)',
        'table_tfidf': 'Pesos TF‑IDF',
        'explanation': 'Explicação',
        'lang':        '🇵🇹 PT',
        'error_matrix':'A matriz está vazia ou mal formatada.'
    },
    'en': {
        'matrix':      'Term‑document matrix (1st line is header):',
        'calculate':   'Calculate',
        'table_tf':    'TF weights (log‑freq)',
        'table_tfidf': 'TF‑IDF weights',
        'explanation': 'Explanation',
        'lang':        '🇬🇧 EN',
        'error_matrix':'Matrix is empty or badly formatted.'
    },
    'fr': {
        'matrix':      'Matrice terme‑document (1ʳᵉ ligne = en‑tête):',
        'calculate':   'Calculer',
        'table_tf':    'Poids TF (log‑freq)',
        'table_tfidf': 'Poids TF‑IDF',
        'explanation': 'Explication',
        'lang':        '🇫🇷 FR',
        'error_matrix':'La matrice est vide ou mal formatée.'
    }
}
FLAG = {c: TR[c]['lang'] for c in TR}

class TFIDFGui(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('TF‑IDF visualizer')
        self.geometry('1350x800+80+40')
        self.language = 'pt'  # default PT

        self.font_ui   = tkfont.Font(size=11)
        self.font_mono = tkfont.Font(family='Consolas', size=11)

        self._build_widgets()
        self._translate_ui()

    # ───────────── build ─────────────
    def _build_widgets(self):
        top = tk.Frame(self); top.pack(fill='x', padx=5, pady=3)
        self.btn_calc = tk.Button(top, command=self._calculate)
        self.btn_calc.pack(side='left', padx=(0, 10))

        self.lang_var = tk.StringVar(value=FLAG[self.language])
        tk.OptionMenu(top, self.lang_var, *FLAG.values(), command=self._change_lang).pack(side='right')

        self.lbl_matrix = tk.Label(self)
        self.lbl_matrix.pack(anchor='w', padx=5)

        self.txt_matrix = tk.Text(self, height=8, font=self.font_mono)
        sample = (
            'term D1 D2 D3\n'
            'bank 0 0 4\n'
            'bass 2 4 0\n'
            'commercial 0 2 2\n'
            'cream 2 0 0\n'
            'guitar 1 0 0\n'
            'fisherman 0 3 0\n'
            'money 0 1 2'
        )
        self.txt_matrix.insert('1.0', sample)
        self.txt_matrix.pack(fill='x', padx=5)

        # frames for two tables side by side
        table_container = tk.Frame(self)
        table_container.pack(pady=10)
        self.tf_frame   = tk.Frame(table_container, borderwidth=1, relief='groove')
        self.idf_frame  = tk.Frame(table_container, borderwidth=1, relief='groove')
        self.tf_frame.pack(side='left', padx=10)
        self.idf_frame.pack(side='left', padx=10)

        # explanation
        self.lbl_expl = tk.Label(self, font=('Helvetica', 12, 'bold'))
        self.lbl_expl.pack(anchor='w', padx=5)
        self.txt_expl = tk.Text(self, height=15, font=self.font_mono, state='disabled')
        self.txt_expl.pack(fill='both', expand=True, padx=5, pady=(0,5))

    # ───────────── language ─────────────
    def _translate_ui(self):
        t = TR[self.language]
        self.btn_calc.config(text=t['calculate'])
        self.lbl_matrix.config(text=t['matrix'])
        self.lbl_expl.config(text=t['explanation'])
        # update table captions if tables already exist
        if hasattr(self, '_last_result'):
            self._populate_table(self.tf_frame, self._last_result['tf'], t['table_tf'])
            self._populate_table(self.idf_frame, self._last_result['tfidf'], t['table_tfidf'])

    def _change_lang(self, *_):
        for code, flag in FLAG.items():
            if self.lang_var.get() == flag:
                self.language = code
                break
        self._translate_ui()

    # ───────────── computation helpers ─────────────
    @staticmethod
    def _log_tf(tf):
        return 0.0 if tf == 0 else 1 + math.log10(tf)

    def _calculate(self):
        lines = [ln.strip() for ln in self.txt_matrix.get('1.0', 'end').strip().split('\n') if ln.strip()]
        if not lines:
            messagebox.showerror('Error', TR[self.language]['error_matrix'])
            return
        header = lines[0].split()
        if len(header) < 2:
            messagebox.showerror('Error', TR[self.language]['error_matrix'])
            return
        docs = header[1:]
        matrix = {}
        for ln in lines[1:]:
            parts = ln.split()
            if len(parts) != len(header):
                continue
            term = parts[0]
            freqs = list(map(int, parts[1:]))
            matrix[term] = freqs
        if not matrix:
            messagebox.showerror('Error', TR[self.language]['error_matrix'])
            return

        # compute TF weights (log‑freq), df, idf, tf‑idf
        tf_weights = {t: [self._log_tf(f) for f in freqs] for t, freqs in matrix.items()}
        df = {t: sum(1 for f in matrix[t] if f > 0) for t in matrix}
        N = len(docs)
        idf = {t: math.log10(N/df[t]) if df[t]>0 else 0.0 for t in matrix}
        tfidf = {t: [tf_weights[t][i]*idf[t] for i in range(N)] for t in matrix}

        # save for language switch
        self._last_result = {'tf': (docs, tf_weights), 'tfidf': (docs, tfidf)}

        # fill tables
        self._populate_table(self.tf_frame, self._last_result['tf'], TR[self.language]['table_tf'])
        self._populate_table(self.idf_frame, self._last_result['tfidf'], TR[self.language]['table_tfidf'])

        # explanation (very brief)
        expl = [f"idf = log10(N / df)  where   N = {N}"]
        for t in matrix:
            expl.append(f"{t}: df={df[t]},  idf={idf[t]:.4f}")
        self.txt_expl.config(state='normal')
        self.txt_expl.delete('1.0', 'end')
        self.txt_expl.insert('end', '\n'.join(expl))
        self.txt_expl.config(state='disabled')

    # ───────────── table generator ─────────────
    def _populate_table(self, parent_frame, data_tuple, caption):
        # clear
        for w in parent_frame.winfo_children():
            w.destroy()

        docs, table = data_tuple  # docs list, dict term → list[float]
        # use grid exclusively inside this frame
        tk.Label(parent_frame, text=caption, font=('Helvetica', 12, 'bold')).grid(row=0, column=0, columnspan=len(docs)+1, pady=(4,2))

        # header
        tk.Label(parent_frame, text='', font=self.font_mono, width=12, borderwidth=1, relief='ridge').grid(row=1, column=0)
        for j, d in enumerate(docs, 1):
            tk.Label(parent_frame, text=d, font=self.font_mono, width=12, borderwidth=1, relief='ridge').grid(row=1, column=j)

        # rows
        for i, term in enumerate(sorted(table.keys()), 2):
            tk.Label(parent_frame, text=term, font=self.font_mono, width=12, borderwidth=1, relief='ridge').grid(row=i, column=0)
            for j, val in enumerate(table[term], 1):
                tk.Label(parent_frame, text=f"{val:.4f}", font=self.font_mono, width=12, borderwidth=1, relief='ridge').grid(row=i, column=j)

if __name__ == '__main__':
    TFIDFGui().mainloop()