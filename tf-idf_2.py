import tkinter as tk
from tkinter import messagebox, font as tkfont
import math

# ───────────────────────────── UI TRANSLATIONS ────────────────────────────────
TR = {
    'pt': {
        'matrix':      'Matriz termo-documento (1ª linha é cabeçalho):',
        'calculate':   'Calcular',
        'table_tf':    'Pesos TF (log-freq)',
        'table_tfidf': 'Pesos TF-IDF',
        'explanation': 'Explicação detalhada',
        'error_matrix':'A matriz está vazia ou mal formatada.'
    },
    'en': {
        'matrix':      'Term-document matrix (1st line is header):',
        'calculate':   'Calculate',
        'table_tf':    'TF weights (log-freq)',
        'table_tfidf': 'TF-IDF weights',
        'explanation': 'Detailed explanation',
        'error_matrix':'Matrix is empty or badly formatted.'
    },
    'fr': {
        'matrix':      'Matrice terme-document (1ʳᵉ ligne = en-tête):',
        'calculate':   'Calculer',
        'table_tf':    'Poids TF (log-freq)',
        'table_tfidf': 'Poids TF-IDF',
        'explanation': 'Explication détaillée',
        'error_matrix':'La matrice est vide ou mal formatée.'
    }
}
FLAG = {'pt': 'PT', 'en': 'EN', 'fr': 'FR'}

# ───────────────────────────── MAIN GUI ───────────────────────────────────────
class TFIDFGui(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('TF-IDF visualizer')
        self.geometry('1350x800+80+40')
        self.language = 'pt'                      # 🇵🇹 por defeito
        self.font_ui   = tkfont.Font(size=11)
        self.font_mono = tkfont.Font(family='Consolas', size=11)
        self._build_widgets()
        self._translate_ui()

    # -------------------------- UI construction ------------------------------
    def _build_widgets(self):
        top = tk.Frame(self); top.pack(fill='x', padx=5, pady=3)
        self.btn_calc = tk.Button(top, command=self._calculate); self.btn_calc.pack(side='left', padx=(0,10))
        self.lang_var = tk.StringVar(value='PT')
        tk.OptionMenu(top, self.lang_var, 'PT','EN','FR', command=self._change_lang).pack(side='right')

        self.lbl_matrix = tk.Label(self); self.lbl_matrix.pack(anchor='w', padx=5)
        self.txt_matrix = tk.Text(self, height=8, font=self.font_mono)
        self.txt_matrix.insert('1.0',
            'term D1 D2 D3\n'
            'bank 0 0 4\n'
            'bass 2 4 0\n'
            'commercial 0 2 2\n'
            'cream 2 0 0\n'
            'guitar 1 0 0\n'
            'fisherman 0 3 0\n'
            'money 0 1 2')
        self.txt_matrix.pack(fill='x', padx=5)

        container = tk.Frame(self); container.pack(pady=10)
        self.tf_frame  = tk.Frame(container, borderwidth=1, relief='groove'); self.tf_frame.pack(side='left', padx=10)
        self.idf_frame = tk.Frame(container, borderwidth=1, relief='groove'); self.idf_frame.pack(side='left', padx=10)

        self.lbl_expl = tk.Label(self, font=('Helvetica',12,'bold')); self.lbl_expl.pack(anchor='w', padx=5)

        expl = tk.Frame(self); expl.pack(fill='both', expand=True, padx=5, pady=(0,5))
        v = tk.Scrollbar(expl, orient='vertical'); h = tk.Scrollbar(expl, orient='horizontal')
        self.txt_expl = tk.Text(expl, font=self.font_mono, wrap='none',
                                state='disabled', yscrollcommand=v.set, xscrollcommand=h.set)
        v.config(command=self.txt_expl.yview); h.config(command=self.txt_expl.xview)
        v.pack(side='right', fill='y'); h.pack(side='bottom', fill='x')
        self.txt_expl.pack(side='left', fill='both', expand=True)

    # -------------------------- language -------------------------------------
    def _translate_ui(self):
        t = TR[self.language]
        self.btn_calc.config(text=t['calculate'])
        self.lbl_matrix.config(text=t['matrix'])
        self.lbl_expl.config(text=t['explanation'])
        if hasattr(self, '_last_result'):
            self._populate_table(self.tf_frame,  self._last_result['tf'],   t['table_tf'])
            self._populate_table(self.idf_frame, self._last_result['tfidf'],t['table_tfidf'])
            self._show_explanation()

    def _change_lang(self, *_):
        self.language = {'PT':'pt','EN':'en','FR':'fr'}[self.lang_var.get()]
        self._translate_ui()

    # -------------------------- helpers --------------------------------------
    @staticmethod
    def _log_tf(tf): return 0.0 if tf==0 else 1+math.log10(tf)

    # -------------------------- compute --------------------------------------
    def _calculate(self):
        lines = [ln.strip() for ln in self.txt_matrix.get('1.0','end').strip().split('\n') if ln.strip()]
        if not lines: return messagebox.showerror('Error', TR[self.language]['error_matrix'])
        header = lines[0].split(); docs = header[1:]
        matrix={}
        for ln in lines[1:]:
            parts=ln.split()
            if len(parts)!=len(header): continue
            term=parts[0]
            try: freqs=list(map(int,parts[1:]))
            except ValueError: continue
            matrix[term]=freqs
        if not matrix: return messagebox.showerror('Error', TR[self.language]['error_matrix'])

        tf_w ={t:[self._log_tf(f) for f in v] for t,v in matrix.items()}
        df   ={t:sum(1 for f in matrix[t] if f>0) for t in matrix}
        N=len(docs)
        idf  ={t:math.log10(N/df[t]) if df[t]>0 else 0.0 for t in matrix}
        tfidf={t:[tf_w[t][i]*idf[t] for i in range(N)] for t in matrix}

        self._last_result={'tf':(docs,tf_w),'tfidf':(docs,tfidf)}
        self._last_calc  ={'N':N,'df':df,'idf':idf,'tf_w':tf_w,'order':list(matrix.keys())}

        self._populate_table(self.tf_frame,  self._last_result['tf'],   TR[self.language]['table_tf'])
        self._populate_table(self.idf_frame, self._last_result['tfidf'],TR[self.language]['table_tfidf'])
        self._show_explanation()

    # -------------------------- explanation ----------------------------------
    def _show_explanation(self):
        N, df, idf, tf_w, order = (self._last_calc[k] for k in ('N','df','idf','tf_w','order'))
        docs = self._last_result['tf'][0]

        # header
        head1 = ["Term","df","idf = log10(N/df)"]
        head2 = [f"tf_{d}" for d in docs]
        head3 = [f"tfw_{d}=1+log10(tf)" for d in docs]
        head4 = [f"tfw×idf_{d}" for d in docs]
        header = head1+head2+head3+head4
        widths = [12,2,23]+ [4]*len(docs)+ [23]*len(docs)+ [23]*len(docs)
        lines  = ["| " + " | ".join(f"{h:<{w}}" for h,w in zip(header,widths)) + " |"]
        lines += ["| " + " | ".join("-"*w for w in widths) + " |"]

        # rows
        for term in order:
            idf_expr=f"log10({N}/{df[term]}) = {idf[term]:.4f}"
            row=[f"{term:<12}", str(df[term]), idf_expr]

            # tf numeric
            tf_list=[]
            for w in tf_w[term]:
                tf = 0 if w==0 else int(round(10**(w-1)))
                tf_list.append(tf); row.append(str(tf))

            # tfw formula
            for tf_val, w in zip(tf_list, tf_w[term]):
                row.append("0.0000" if tf_val==0 else f"1+log10({tf_val}) = {w:.4f}")

            # tfw×idf formula
            for tf_val, w in zip(tf_list, tf_w[term]):
                prod = w*idf[term]
                row.append("0.0000" if tf_val==0 else f"{w:.4f}×{idf[term]:.4f} = {prod:.4f}")

            lines.append("| " + " | ".join(f"{cell:<{w}}" for cell,w in zip(row,widths)) + " |")

        self.txt_expl.config(state='normal'); self.txt_expl.delete('1.0','end')
        self.txt_expl.insert('end', "\n".join(lines)); self.txt_expl.config(state='disabled')

    # -------------------------- table helper ----------------------------------
    def _populate_table(self, frame, data_tuple, caption):
        for w in frame.winfo_children(): w.destroy()
        docs, table = data_tuple
        tk.Label(frame,text=caption,font=('Helvetica',12,'bold')
                 ).grid(row=0,column=0,columnspan=len(docs)+1,pady=3)
        tk.Label(frame,text='',font=self.font_mono,width=14,borderwidth=1,relief='ridge').grid(row=1,column=0)
        for j,d in enumerate(docs,1):
            tk.Label(frame,text=d,font=self.font_mono,width=14,borderwidth=1,relief='ridge').grid(row=1,column=j)
        for i,term in enumerate(table.keys(),2):
            tk.Label(frame,text=term,font=self.font_mono,width=14,borderwidth=1,relief='ridge').grid(row=i,column=0)
            for j,val in enumerate(table[term],1):
                tk.Label(frame,text=f"{val:.4f}",font=self.font_mono,width=14, borderwidth=1,relief='ridge').grid(row=i,column=j)

# ────────────────────────────── RUN ───────────────────────────────────────────
if __name__ == '__main__':
    TFIDFGui().mainloop()
