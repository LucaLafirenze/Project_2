import json
import pprint
import re
import tkinter as tk
import webbrowser
from datetime import datetime
from PIL import ImageTk, Image
from tkinter import Scrollbar, ttk, messagebox, filedialog
from tkcalendar import DateEntry
from tqdm import tqdm


def calcolo_n_articoli(f, categoria):

    cnt = 0
    cnt_cat = 0
    for elem in f:
        if "category" in elem:
            cnt += 1
        if categoria.upper() == elem['category']:
            cnt_cat += 1
    return cnt, cnt_cat


def categorie_uniche(f):
    categorie_uniche = {cat['category'] for cat in f}
    return categorie_uniche


def check_anno(f):
    return max(f, key=lambda articolo: articolo['date'])


def articoli_recenti(f):
    articoli = []
    data_recente = check_anno(f)['date']
    for articolo in f:
        if articolo['date'] == data_recente:
            articoli.append(articolo)
    return articoli


def autori_massimi(f):
    dizionario_autori = {}
    autori_divisi = autori_cleared_improved(f)
    for autore in autori_divisi:
        if autore in dizionario_autori:
            dizionario_autori[autore] += 1
        else:
            dizionario_autori[autore] = 1
    sorted_autori = sorted(dizionario_autori.items(), key=lambda valore: valore[1], reverse=True)

    return sorted_autori


def autori_cleared(f):
    lista_autori = [elem['authors'] for elem in f]
    lista_notnull_autori = [elem for elem in lista_autori if elem != ""]
    autori_divisi = []
    for autore in lista_notnull_autori:
        autore_parts = autore.split(',')
        autore_cleared = autore_parts[0].strip()
        if ' and ' in autore_cleared or ' AND ' in autore_cleared:
            autori_multipli = autore_cleared.split(' and ')
            autori_divisi.extend([a.strip() for a in autori_multipli])
        elif '/' in autore_cleared:
            autori_multipli = autore_cleared.split('/')
            autori_divisi.extend([a.strip() for a in autori_multipli])
        elif '&' in autore_cleared:
            autori_multipli = autore_cleared.split('&')
            autori_divisi.extend([a.strip() for a in autori_multipli])
        elif '\n' in autore_cleared:
            autori_multipli = autore_cleared.split('\n')
            autori_divisi.extend([a.strip() for a in autori_multipli])
        else:
            autori_divisi.append(autore_cleared)
    return autori_divisi


def autori_cleared_improved(f):
    nomi_indesiderati = {"contributor", "reuters", "author", "writer", "contributorauthor", "founder", "m.d.", "blogger",
                         "contributors", "ap", "...", "ceo", "ph.d.", "speaker", "president",
                         "contributorpresident", "contributorfounder", "md", "contributorwriter"}

    lista_autori = [elem['authors'] for elem in f if elem['authors']]
    autori_divisi = []
    for autore in lista_autori:
        autori_divisi.extend(re.split(',| and | AND |/|&|\n', autore))

    return [a.strip() for a in autori_divisi if a.strip().lower() not in nomi_indesiderati and a != ""]


def ricerca_per_categoria(f, controllo):
    articoli = []
    for diz in f:
        if diz['category'] == controllo.strip().upper():
            articoli.append(diz)
    return articoli


def articoli_per_anno(f, dat, preciso=False):
    articoli = []
    if preciso:
        for art in f:
            data = datetime.strptime(art['date'], "%Y-%m-%d")
            if dat == data:
                articoli.append(art)
    else:
        for art in f:
            data = datetime.strptime(art['date'], "%Y-%m-%d")
            if dat.year == data.year:
                articoli.append(art)
    return articoli


def ricerca_per_anno(f, check_year, data_confronto):
    try:
        dat = datetime.strptime(data_confronto, "%Y-%m-%d")
    except ValueError:
        dat = datetime.strptime("2012-01-01", "%Y-%m-%d")
    if check_year == "si":
        return articoli_per_anno(f, dat, preciso=True)
    else:
        return articoli_per_anno(f, dat)


def ricerca_periodo_anno(f, data_inizio, data_fine):
    try:
        data_inizio = datetime.strptime(data_inizio, '%Y-%m-%d')
        data_fine = datetime.strptime(data_fine, '%Y-%m-%d')
    except ValueError:
        data_inizio = datetime.strptime("2012-01-01", '%Y-%m-%d')
        data_fine = datetime.strptime("2012-01-01", '%Y-%m-%d')
    date_to_headlines = {}
    for elem in f:
        date = elem['date']
        articolo = elem
        if date not in date_to_headlines:
            date_to_headlines[date] = []
        date_to_headlines[date].append(articolo)

    date_selezionate = [data for data in date_to_headlines if
                        data_inizio <= datetime.strptime(data, '%Y-%m-%d') <= data_fine]
    date_ordinate = sorted(date_selezionate, key=lambda x: datetime.strptime(x, '%Y-%m-%d'))
    articoli_per_periodo = []

    for data in date_ordinate:
        headlines = date_to_headlines[data]
        for headline in headlines:
            articoli_per_periodo.append((data, headline))

    return articoli_per_periodo


def ricerca_per_autore(f, check_author):
    articoli_per_autore = []
    nome_autore = check_author.strip()
    for articolo in f:
        if nome_autore in articolo['authors']:
            articoli_per_autore.append(articolo)

    return articoli_per_autore


def ricerca_per_diverse_keyword(f, lista_keyword):
    articoli = []
    for articolo in f:
        if any(elem.strip().lower() in articolo['short_description'].lower() for elem in lista_keyword):
            articoli.append(articolo)
    return articoli


def analisi_per_parola(f):
    dizionario_per_keyword = {}
    lista_descrizioni = []
    for articolo in f:
        lista_descrizioni.append(articolo['short_description'])

    for descrizione in lista_descrizioni:
        for parola in descrizione.split():
            parola_cleaned = parola.strip().lower().strip(",.")
            if parola_cleaned in dizionario_per_keyword:
                dizionario_per_keyword[parola_cleaned] += 1
            else:
                dizionario_per_keyword[parola_cleaned] = 1

    return sorted(dizionario_per_keyword.items(), key=lambda x: x[1], reverse=True)


def ricerca_parametri(f, lista):
    categoria, data_inizio, data_fine, autore, keyword = lista

    if categoria == "Seleziona categoria":
        categoria = None

    if autore == "Nome Autore:":
        autore = None

    if keyword == "Inserisci le keyword separate da una virgola":
        keyword = ""

    try:
        data_inizio = datetime.strptime(data_inizio, "%Y-%m-%d") if data_inizio else None
    except ValueError:
        data_inizio = None

    try:
        data_fine = datetime.strptime(data_fine, "%Y-%m-%d") if data_fine else None
    except ValueError:
        data_fine = None

    keyword_list = [kw.strip().lower() for kw in keyword.split(",")] if keyword else []

    articoli_filtrati = []
    for articolo in f:
        categoria_match = True
        data_match = True
        autore_match = True
        keyword_match = True

        if categoria and articolo.get("category", "").upper() != categoria.upper():
            categoria_match = False

        try:
            articolo_data = datetime.strptime(articolo.get("date", ""), "%Y-%m-%d")
        except ValueError:
            articolo_data = None

        if data_inizio and data_fine:
            if not (articolo_data and data_inizio <= articolo_data <= data_fine):
                data_match = False
        elif data_inizio:
            if not (articolo_data and articolo_data >= data_inizio):
                data_match = False
        elif data_fine:
            if not (articolo_data and articolo_data <= data_fine):
                data_match = False

        if autore and autore not in articolo.get("authors", ""):
            autore_match = False

        if keyword_list and not any(kw in articolo.get("short_description", "").lower() for kw in keyword_list):
            keyword_match = False

        if categoria_match and data_match and autore_match and keyword_match:
            articoli_filtrati.append(articolo)

    return articoli_filtrati


class PlaceholderEntry(ttk.Entry):
    def __init__(self, master=None, placeholder="", color='', **kwargs):
        super().__init__(master, **kwargs)

        self.placeholder = placeholder
        self.placeholder_color = color
        self.default_fg_color = self['foreground']

        self.bind("<FocusIn>", self._clear_placeholder)
        self.bind("<FocusOut>", self._set_placeholder)
        self._set_placeholder()

    def _clear_placeholder(self, _):
        if self.get() == self.placeholder:
            self.delete(0, tk.END)
            self.config(foreground=self.default_fg_color)

    def _set_placeholder(self, _=None):
        if not self.get():
            self.insert(0, self.placeholder)
            self.config(foreground=self.placeholder_color)


class PlaceholderEntryGroup(tk.Frame):
    def __init__(self, master=None, entries_info=None):
        super().__init__(master)
        self.entries = []
        self.create_entries(entries_info)

    def create_entries(self, entries_info):
        if entries_info:
            for info in entries_info:
                if info.get('type') == 'date':
                    entry = DateEntry(self, width=12, background='dark blue', foreground='white', borderwidth=2,
                                      state='readonly')
                elif info.get('type') == 'dropdown':
                    default_text = 'Seleziona categoria'
                    var = tk.StringVar(self, default_text)
                    entry = tk.OptionMenu(self, var, *info.get('options'))
                else:
                    entry = PlaceholderEntry(self, placeholder=info.get('placeholder', ''),
                                             color=info.get('color', ''),
                                             **info.get('kwargs', {}))
                entry.grid(row=len(self.entries), column=0, padx=15, pady=15, sticky='we')
                self.entries.append(entry)

    def get_entries(self):
        formatted_entries = []
        for entry in self.entries:
            if isinstance(entry, DateEntry):
                date_value = entry.get_date()
                formatted_entries.append(date_value.strftime('%Y-%m-%d'))
            elif isinstance(entry, tk.OptionMenu):
                formatted_entries.append(entry.cget('text'))
            else:
                formatted_entries.append(entry.get())
        return formatted_entries


class MainApplication(tk.Tk):
    def __init__(self, json_data):
        super().__init__()
        self.ordine_crescente = None
        self.json_data = json_data
        self.valori = None

        ct_unique_count = categorie_uniche(json_data)

        entries_info = [
            {'placeholder': '', 'color': 'black', 'kwargs': {}, 'type': 'dropdown', 'options': sorted(ct_unique_count)},
            {'type': 'date'},
            {'type': 'date'},
            {'placeholder': 'Nome Autore:', 'color': 'black', 'kwargs': {}},
            {'placeholder': 'Inserisci le keyword separate da una virgola', 'color': 'black', 'kwargs': {'width': 50}}
        ]

        width = 1700
        height = 910
        self.geometry(f"{width}x{height}")
        self.title('Progetto_Lafirenze_Database_Engineer')

        self.bg = ImageTk.PhotoImage(file="wallpaper.jpg")
        self.my_canvas = tk.Canvas(self, width=width, height=height)
        self.my_canvas.pack(fill="both", expand=True)
        self.my_canvas.create_image(0, 0, image=self.bg, anchor="nw")

        self.cornice = tk.Frame(self, bg="black")
        self.cornice.place(x=25, y=100, width=800, height=700)

        self.menu = tk.Frame(self.cornice, bg="#507FAB")
        self.menu.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.menu_temporale = tk.Frame(self.menu, bg="#6699CC", width=200, height=250)
        self.menu_temporale.place(x=10, y=480)

        self.menu_statico = tk.Frame(self.menu, bg="#6699CC", width=200, height=250)
        self.menu_statico.place(x=10, y=220)

        self.menu_dinamico = tk.Frame(self.menu, bg="#6699CC", width=200, height=250)
        self.menu_dinamico.place(x=10, y=10)

        self.entry_group = PlaceholderEntryGroup(self.menu, entries_info=entries_info)
        self.entry_group.place(x=300, y=10)
        self.entry_group.config(bg="#6699CC")

        self.showcase = tk.Frame(self, bg="black")
        self.showcase.place(x=875, y=100, width=800, height=700)

        self.showcase2 = tk.Frame(self.showcase, bg="white")
        self.showcase2.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        scrollbar = Scrollbar(self.showcase2)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.text_widget = tk.Text(self.showcase2, wrap=tk.WORD, bg="white", fg="black", yscrollcommand=scrollbar.set)
        self.text_widget.config(state=tk.DISABLED)
        self.text_widget.pack(fill=tk.BOTH, expand=True)

        scrollbar.config(command=self.text_widget.yview)

        def carica_immagine(path, width, height):
            image = Image.open(path)
            image = image.resize((width, height), Image.LANCZOS)
            return ImageTk.PhotoImage(image)

        self.save_file_icon = carica_immagine("save_file_icon.png", 40, 40)
        self.json_convert = carica_immagine("save_json_icon.png", 40, 40)
        self.research_icon = carica_immagine("research_icon.jpg", 25, 25)
        self.sort_icon = carica_immagine("sort_icon.png", 40, 40)
        self.graphic_icon = carica_immagine("graphic_icon.jpg", 40, 40)

        self.text_widget.config(cursor="arrow")
        self.button_menu()

    def button_menu(self):
        #MENU STATICO
        tk.Button(self.menu_statico, text="Numero totale degli articoli", command=self.show_num_articoli, width=25,
                  relief='groove', cursor="hand2", font=("Comic Sans MS", 9, "italic"), activebackground="lightblue",
                  overrelief='raised').pack(padx=10, pady=10, side=tk.TOP, anchor=tk.W)
        tk.Button(self.menu_statico, text="Categorie uniche", command=self.show_categorie_uniche, width=25,
                  relief='groove', cursor="hand2", font=("Comic Sans MS", 9, "italic"), activebackground="lightblue",
                  overrelief='raised').pack(padx=10, pady=10, anchor=tk.W)
        tk.Button(self.menu_statico, text="Articolo più recente", command=self.show_articolo_recente, width=25,
                  relief='groove', cursor="hand2", font=("Comic Sans MS", 9, "italic"), activebackground="lightblue",
                  overrelief='raised').pack(padx=10, pady=10, anchor=tk.W)
        tk.Button(self.menu_statico, text="Autori più frequenti", command=self.show_autori_massimi, width=25,
                  relief='groove', cursor="hand2", font=("Comic Sans MS", 9, "italic"), activebackground="lightblue",
                  overrelief='raised').pack(padx=10, pady=10, anchor=tk.W)
        tk.Button(self.menu_statico, text="Analisi per parola", command=self.show_analisi_per_parola, width=25,
                  relief='groove', cursor="hand2", font=("Comic Sans MS", 9, "italic"), activebackground="lightblue",
                  overrelief='raised').pack(padx=10, pady=10, anchor=tk.W)

        #MENU DINAMICO
        tk.Button(self.menu_dinamico, text="Ricerca per categoria", command=self.show_ricerca_per_categoria, width=25,
                  relief='groove', cursor="hand2", font=("Comic Sans MS", 9, "italic"), activebackground="lightblue",
                  overrelief='raised').pack(padx=10, pady=10, anchor=tk.W)
        tk.Button(self.menu_dinamico, text="Ricerca tutti parametri", command=self.show_all_conditions, width=25,
                  relief='groove', cursor="hand2", font=("Comic Sans MS", 9, "italic"), activebackground="lightblue",
                  overrelief='raised').pack(padx=10, pady=10, anchor=tk.W)
        tk.Button(self.menu_dinamico, text="Ricerca per autore", command=self.show_ricerca_per_autore, width=25,
                  relief='groove', cursor="hand2", font=("Comic Sans MS", 9, "italic"), activebackground="lightblue",
                  overrelief='raised').pack(padx=10, pady=10, anchor=tk.W)
        tk.Button(self.menu_dinamico, text="Ricerca per keyword", command=self.show_ricerca_per_diverse_keyword,
                  width=25,
                  relief='groove', cursor="hand2", font=("Comic Sans MS", 9, "italic"), activebackground="lightblue",
                  overrelief='raised').pack(padx=10, pady=10, anchor=tk.W)

        #MENU RICERCA TEMPO
        tk.Button(self.menu_temporale, text="Articoli precisi", command=self.show_ricerca_data_precisa, width=25,
                  relief='groove', cursor="hand2", font=("Comic Sans MS", 9, "italic"), activebackground="lightblue",
                  overrelief='raised').pack(padx=10, pady=10, anchor=tk.W)
        tk.Button(self.menu_temporale, text="Ricerca per periodo anno ",
                  image=self.research_icon, compound="right", command=self.show_ricerca_periodo_anno, width=177,
                  relief='groove', cursor="hand2", font=("Comic Sans MS", 9, "italic"), activebackground="lightblue",
                  overrelief='raised').pack(padx=10, pady=10, anchor=tk.W)
        tk.Button(self.menu_temporale, text="Articoli per anno", command=self.show_ricerca_per_anno, width=25,
                  relief='groove', cursor="hand2", font=("Comic Sans MS", 9, "italic"), activebackground="lightblue",
                  overrelief='raised').pack(padx=10, pady=10, anchor=tk.W)

        tk.Button(self.menu, image=self.save_file_icon, command=self.save_results, cursor="hand2").place(x=700, y=590)
        tk.Button(self.menu, image=self.json_convert, command=self.save_results_json, cursor="hand2").place(x=650,
                                                                                                            y=590)
        tk.Button(self.menu, image=self.sort_icon, command=self.ordina_result, cursor="hand2").place(x=650, y=500)
        tk.Button(self.menu, image=self.graphic_icon, command=self.grafico_istogramma, cursor="hand2").place(x=700, y=500)

    def reset_text_widget(self):
        self.text_widget.config(state=tk.NORMAL)
        self.text_widget.delete(1.0, tk.END)
        for widget in self.text_widget.winfo_children():
            widget.destroy()
        self.text_widget.config(state=tk.DISABLED)

    def show_num_articoli(self):
        controllo = self.entry_group.get_entries()
        result = calcolo_n_articoli(self.json_data, controllo[0])
        if controllo[0] != "Seleziona categoria":
            self.display_result(
                f"Numero totale di articoli: {result[0]}\n"
                f"Numero totale di articoli per {controllo[0]}: {result[1]}")
            result_diz = {
                "Numero totale di articoli:": result[0],
                f"numero totale di articoli per {controllo[0]}": result[1]
            }
        else:
            self.display_result(f"Numero totale di articoli: {result[0]}")
            result_diz = {
                "Numero totale di articoli:": result[0]
            }
        self.valori = result_diz

    def show_categorie_uniche(self):
        result = categorie_uniche(self.json_data)
        result_diz = dict()
        for elem in result:
            result_diz[elem] = ""
        self.valori = result_diz
        result_valore = "Le categorie uniche sono\n\n"
        for elem in result:
            result_valore += elem + "\n"
        self.display_result(result_valore)

    def show_articolo_recente(self):
        articolo = check_anno(self.json_data)
        self.valori = dict(articolo)
        self.display_result(f"L'articolo più recente è: \n{pprint.pformat(articolo)}")

    def show_autori_massimi(self):
        result = autori_massimi(self.json_data)
        self.valori = dict(result)
        autori = f"{"AUTORE":<30} {"CONTEGGIO":>20}\n\n"
        for elem in result[:50]:
            autori += f"{elem[0]:<30} {elem[1]:>20}\n"
        self.display_result(f"{autori}")

    def show_ricerca_per_categoria(self):
        controllo = self.entry_group.get_entries()
        articoli = ricerca_per_categoria(self.json_data, controllo[0])
        self.valori = articoli
        self.display_result(f"Articoli nella categoria scelta: \n{pprint.pformat(articoli)}")

    def show_ricerca_data_precisa(self):
        data_confronto = self.entry_group.get_entries()
        articoli = ricerca_per_anno(self.json_data, "si", data_confronto[1])
        self.valori = articoli
        self.display_result(f"Articoli dell'anno scelto: \n{pprint.pformat(articoli)}")

    def show_ricerca_per_anno(self):
        data_confronto = self.entry_group.get_entries()
        articoli = ricerca_per_anno(self.json_data, "no", data_confronto[1])
        self.valori = articoli
        self.display_result(f"Articoli dell'anno scelto: \n{pprint.pformat(articoli)}")

    def show_ricerca_periodo_anno(self):
        controllo = self.entry_group.get_entries()
        date_inizio = controllo[1]
        date_fine = controllo[2]
        articoli = ricerca_periodo_anno(self.json_data, date_inizio, date_fine)
        self.valori = articoli
        self.display_result(f"Articoli nel periodo scelto: \n{pprint.pformat(articoli)}")

    def show_ricerca_per_autore(self):
        controllo = self.entry_group.get_entries()
        articoli = ricerca_per_autore(self.json_data, controllo[3])
        self.valori = articoli
        self.display_result(f"Articoli dell'autore scelto: \n{pprint.pformat(articoli)}")

    def show_ricerca_per_diverse_keyword(self):
        controllo = self.entry_group.get_entries()
        keywords = controllo[4]
        articoli = ricerca_per_diverse_keyword(self.json_data, keywords.split(","))
        self.valori = articoli
        self.display_result(f"Articoli con le keyword scelte: \n{pprint.pformat(articoli)}")

    def show_analisi_per_parola(self):
        result = analisi_per_parola(self.json_data)
        result_valore = f"Analisi per parola:\n\n"
        for elem in tqdm(result[:2000]):
            result_valore += f"{elem[0]:<30} {elem[1]:>20}\n"
        self.valori = dict(result)
        self.display_result(f"{result_valore}")

    def show_all_conditions(self):
        controllo = self.entry_group.get_entries()
        articoli = ricerca_parametri(self.json_data, controllo)
        self.valori = articoli
        self.display_result(f"Articoli filtrati con i parametri scelti: \n{pprint.pformat(articoli)}")

    def ordina_result(self):
        if not hasattr(self, 'ordine_crescente') or self.ordine_crescente:
            try:
                self.valori = sorted(self.valori, key=lambda result: result['date'])
                self.ordine_crescente = False
            except TypeError:
                return None
        else:
            try:
                self.valori = sorted(self.valori, key=lambda result: result['date'], reverse=True)
                self.ordine_crescente = True
            except TypeError:
                return None
        self.display_result(f"Articoli ordinati per data:\n{pprint.pformat(self.valori)}")

    def grafico_istogramma(self):
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

        if isinstance(self.valori, dict):
            keywords = list(self.valori.keys())
            lista_valori = list(self.valori.values())

            fig, ax = plt.subplots(figsize=(10, 15))
            ax.bar(keywords[:20], lista_valori[:20], color='skyblue')
            plt.xticks(rotation=45, ha='right')

            canvas = FigureCanvasTkAgg(fig, master=self.text_widget)
            canvas.draw()

            self.text_widget.config(state=tk.NORMAL)
            self.text_widget.delete(1.0, tk.END)
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            self.text_widget.config(state=tk.DISABLED)
        else:
            messagebox.showerror("Errore", "I dati non sono in un formato valido per creare un grafico.")

    def save_results(self):
        result = self.text_widget.get("1.0", tk.END).strip()
        if result:
            file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
            if file_path:
                with open(file_path, "w", encoding="utf-8") as file:
                    file.write(result)
        else:
            messagebox.showerror("Errore", "Nessun risultato da salvare.")

    def save_results_json(self):
        result = self.valori
        if result:
            file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
            if file_path:
                with open(file_path, "w", encoding="utf-8") as file:
                    json.dump(result, file, indent=4)
        else:
            messagebox.showerror("Errore", "Nessun risultato da salvare.")

    def open_link(self, _):
        link_corrente = self.text_widget.index(tk.CURRENT)

        line_start = self.text_widget.index(f"{link_corrente} linestart")
        line_end = self.text_widget.index(f"{link_corrente} lineend")
        text_line = self.text_widget.get(line_start, line_end)

        controllo = re.search(r"'(https?://\S+)'", text_line)
        if controllo:
            link = controllo.group(1)
            webbrowser.open_new(link)

    def change_cursor(self, _):
        self.text_widget.config(cursor="hand2")

    def restore_cursor(self, _):
        self.text_widget.config(cursor="arrow")

    def display_result(self, result):
        self.reset_text_widget()
        self.text_widget.config(state=tk.NORMAL)
        self.text_widget.delete(1.0, tk.END)
        self.text_widget.insert(tk.INSERT, result)

        self.text_widget.tag_configure("link", foreground="blue", underline=True)
        self.text_widget.tag_bind("link", "<Double-1>", self.open_link)
        self.text_widget.tag_bind("link", "<Enter>", self.change_cursor)
        self.text_widget.tag_bind("link", "<Leave>", self.restore_cursor)

        partenza_indice = "1.0"
        while True:
            partenza_indice = self.text_widget.search(r"'(http[s]?://\S+)'", partenza_indice, stopindex=tk.END, regexp=True)
            if not partenza_indice:
                break
            fine_indice = self.text_widget.index(f"{partenza_indice} lineend")

            link_start = f"{partenza_indice} + 1 char"
            link_end = f"{fine_indice} - 1 char"

            self.text_widget.tag_add("link", link_start, link_end)
            partenza_indice = fine_indice

        self.text_widget.config(state=tk.DISABLED)


if __name__ == "__main__":
    path = 'C://Users/Luca/OneDrive/Documenti/Data_Engineer/Francesco/File di testo/json/News_Category_Dataset.json'
    with open(path, encoding="utf-8") as f:
        json_lines = [json.loads(line) for line in f]

    app = MainApplication(json_lines)
    app.mainloop()
