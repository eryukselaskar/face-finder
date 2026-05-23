import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# ── Palette ──────────────────────────────────────────────
BG      = '#0d0d0f'
SB_BG   = '#111115'
PANEL   = '#16161a'
CARD    = '#1c1c22'
CARD2   = '#23232c'
BORDER  = '#2d2d3d'
ACCENT  = '#6366f1'
ACCENTL = '#818cf8'
GREEN   = '#10b981'
RED     = '#ef4444'
AMBER   = '#f59e0b'
TEXT    = '#f1f0f5'
TEXT2   = '#7c7b9d'
TEXT3   = '#3d3c55'


def _shade(h: str, amt: int) -> str:
    r, g, b = int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16)
    return "#{:02x}{:02x}{:02x}".format(
        min(255, r + amt), min(255, g + amt), min(255, b + amt))


def _mk_btn(parent, text, cmd, bg=CARD2, fg=TEXT, px=16, py=8):
    b = tk.Button(parent, text=text, command=cmd, bg=bg, fg=fg,
                  relief='flat', cursor='hand2', padx=px, pady=py,
                  font=('Segoe UI', 10), bd=0,
                  activebackground=_shade(bg, 15), activeforeground=fg)
    b.bind('<Enter>', lambda e: b.config(bg=_shade(bg, 22)))
    b.bind('<Leave>', lambda e: b.config(bg=bg))
    return b


class _Progress(tk.Canvas):
    """Rounded progress bar with centered percentage label."""

    def __init__(self, parent, **kw):
        super().__init__(parent, height=28, bg=PANEL, highlightthickness=0, **kw)
        self._pct = 0.0
        self.bind('<Configure>', lambda e: self._draw())

    def set(self, pct: float):
        self._pct = max(0.0, min(100.0, pct))
        self._draw()

    def _draw(self):
        self.delete('all')
        w, h = self.winfo_width(), self.winfo_height()
        if w < 4:
            return
        r = 5
        self._rr(0, 0, w, h, r, CARD2)
        fw = int(w * self._pct / 100)
        if fw > r * 2:
            self._rr(0, 0, fw, h, r, ACCENT)
        elif fw > 0:
            self.create_rectangle(0, 0, fw, h, fill=ACCENT, outline='')
        if self._pct > 0:
            self.create_text(w // 2, h // 2,
                             text=f'{int(self._pct)} %',
                             fill=TEXT, font=('Segoe UI', 9, 'bold'))

    def _rr(self, x1, y1, x2, y2, r, c):
        self.create_arc(x1, y1, x1+2*r, y1+2*r, start=90,  extent=90,  fill=c, outline='')
        self.create_arc(x2-2*r, y1, x2, y1+2*r, start=0,   extent=90,  fill=c, outline='')
        self.create_arc(x1, y2-2*r, x1+2*r, y2, start=180, extent=90,  fill=c, outline='')
        self.create_arc(x2-2*r, y2-2*r, x2, y2, start=270, extent=90,  fill=c, outline='')
        self.create_rectangle(x1+r, y1, x2-r, y2, fill=c, outline='')
        self.create_rectangle(x1, y1+r, x2, y2-r, fill=c, outline='')


class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Face Finder')
        self.geometry('1080x720')
        self.minsize(860, 600)
        self.configure(bg=BG)

        self._folders: list[str] = []
        self._q: queue.Queue = queue.Queue()
        self._indexing = False
        self._cancel = False
        self._active_nav = 'index'

        self._setup_style()
        self._build()
        self._refresh_stats()

    # ── ttk style ────────────────────────────────────────
    def _setup_style(self):
        s = ttk.Style(self)
        s.theme_use('clam')
        s.configure('.', background=BG, foreground=TEXT, borderwidth=0)
        s.configure('TScrollbar', background=PANEL, troughcolor=BG,
                    arrowcolor=TEXT3, borderwidth=0, relief='flat', width=8)
        s.map('TScrollbar', background=[('active', CARD2)])

    # ── Build ────────────────────────────────────────────
    def _build(self):
        self._build_sidebar()
        tk.Frame(self, bg=BORDER, width=1).pack(side='left', fill='y')

        content = tk.Frame(self, bg=BG)
        content.pack(side='left', fill='both', expand=True)

        from ui.search_panel import SearchPanel
        from ui.results_panel import ResultsPanel

        self._page_index   = self._build_index_page(content)
        self._page_search  = SearchPanel(content, self)
        self._page_results = ResultsPanel(content, self)
        self._pages = [self._page_index, self._page_search, self._page_results]

        self._show_page(self._page_index)

    # ── Sidebar ──────────────────────────────────────────
    def _build_sidebar(self):
        sb = tk.Frame(self, bg=SB_BG, width=196)
        sb.pack(side='left', fill='y')
        sb.pack_propagate(False)

        # Logo
        logo = tk.Frame(sb, bg=SB_BG)
        logo.pack(fill='x', padx=22, pady=(28, 30))
        tk.Label(logo, text='◉', bg=SB_BG, fg=ACCENT,
                 font=('Segoe UI', 22)).pack(side='left')
        lbl_f = tk.Frame(logo, bg=SB_BG)
        lbl_f.pack(side='left', padx=10)
        tk.Label(lbl_f, text='Face', bg=SB_BG, fg=TEXT,
                 font=('Segoe UI', 13, 'bold')).pack(anchor='w')
        tk.Label(lbl_f, text='Finder', bg=SB_BG, fg=ACCENTL,
                 font=('Segoe UI', 13, 'bold')).pack(anchor='w')

        tk.Frame(sb, bg=BORDER, height=1).pack(fill='x', padx=22, pady=(0, 14))

        # Nav items
        self._nav_btns: dict = {}
        items = [
            ('index',   '  İndeksle',  self.go_index),
            ('search',  '  Ara',       self.go_search),
            ('results', '  Sonuçlar',  self._go_results),
        ]
        for key, label, cmd in items:
            wrap = tk.Frame(sb, bg=SB_BG)
            wrap.pack(fill='x', pady=1)

            bar = tk.Frame(wrap, bg=SB_BG, width=3)
            bar.pack(side='left', fill='y')

            btn = tk.Button(
                wrap, text=label, command=lambda k=key, c=cmd: self._nav(k, c),
                bg=SB_BG, fg=TEXT2, relief='flat', bd=0,
                padx=18, pady=11, anchor='w', width=14,
                font=('Segoe UI', 10), cursor='hand2',
                activebackground=CARD, activeforeground=TEXT,
            )
            btn.pack(side='left', fill='x', expand=True)
            btn.bind('<Enter>',
                     lambda e, b=btn, ac=bar: (b.config(bg=CARD), ac.config(bg=BORDER)))
            btn.bind('<Leave>',
                     lambda e, b=btn, ac=bar, k=key: self._nav_leave(b, ac, k))
            self._nav_btns[key] = (wrap, bar, btn)

        # Bottom db stats
        self._sb_stat = tk.Label(
            sb, text='Veritabanı boş', bg=SB_BG, fg=TEXT3,
            font=('Segoe UI', 8), justify='left', wraplength=160,
        )
        self._sb_stat.pack(side='bottom', anchor='w', padx=22, pady=18)

    def _nav_leave(self, btn, bar, key):
        active = self._active_nav == key
        btn.config(bg=CARD if active else SB_BG, fg=TEXT if active else TEXT2)
        bar.config(bg=ACCENT if active else SB_BG)

    def _update_nav(self):
        for k, (_, bar, btn) in self._nav_btns.items():
            if k == self._active_nav:
                btn.config(bg=CARD, fg=TEXT, font=('Segoe UI', 10, 'bold'))
                bar.config(bg=ACCENT)
            else:
                btn.config(bg=SB_BG, fg=TEXT2, font=('Segoe UI', 10))
                bar.config(bg=SB_BG)

    def _nav(self, key, cmd):
        self._active_nav = key
        self._update_nav()
        cmd()

    def _show_page(self, page):
        for p in self._pages:
            p.pack_forget()
        page.pack(fill='both', expand=True, padx=34, pady=28)

    # ── Public navigation ────────────────────────────────
    def go_index(self):
        self._active_nav = 'index'
        self._update_nav()
        self._show_page(self._page_index)
        self._refresh_stats()

    def go_search(self):
        self._active_nav = 'search'
        self._update_nav()
        self._show_page(self._page_search)

    def show_results(self, results):
        self._page_results.set_results(results)
        self._active_nav = 'results'
        self._update_nav()
        self._show_page(self._page_results)

    def _go_results(self):
        self._active_nav = 'results'
        self._update_nav()
        self._show_page(self._page_results)

    # ── Index page ───────────────────────────────────────
    def _build_index_page(self, parent):
        page = tk.Frame(parent, bg=BG)

        # Page title
        hdr = tk.Frame(page, bg=BG)
        hdr.pack(fill='x', pady=(0, 22))
        tk.Label(hdr, text='Klasör İndeksleme', bg=BG, fg=TEXT,
                 font=('Segoe UI', 18, 'bold')).pack(side='left')
        _mk_btn(hdr, '+ Klasör Ekle', self._add_folder,
                bg=ACCENT, fg='white', px=20, py=9).pack(side='right')

        # Two-column layout
        cols = tk.Frame(page, bg=BG)
        cols.pack(fill='both', expand=True)
        cols.columnconfigure(0, weight=3)
        cols.columnconfigure(1, weight=2)

        # ── Left: folder list card
        lcard = tk.Frame(cols, bg=CARD)
        lcard.grid(row=0, column=0, sticky='nsew', padx=(0, 14))

        ch = tk.Frame(lcard, bg=CARD)
        ch.pack(fill='x', padx=16, pady=(14, 10))
        tk.Label(ch, text='KLASÖRLER', bg=CARD, fg=TEXT3,
                 font=('Segoe UI', 8, 'bold')).pack(side='left')
        tk.Button(ch, text='Tümünü Kaldır', command=self._clear_all_folders,
                  bg=CARD, fg=TEXT3, relief='flat', bd=0, cursor='hand2',
                  font=('Segoe UI', 8), padx=0, pady=0).pack(side='right')

        tk.Frame(lcard, bg=BORDER, height=1).pack(fill='x')

        lb_wrap = tk.Frame(lcard, bg=CARD)
        lb_wrap.pack(fill='both', expand=True, padx=1)

        vsb = ttk.Scrollbar(lb_wrap)
        vsb.pack(side='right', fill='y')
        self._folder_lb = tk.Listbox(
            lb_wrap, bg=CARD, fg=TEXT, selectbackground=ACCENT,
            selectforeground='white', relief='flat', borderwidth=0,
            font=('Segoe UI', 10), activestyle='none', yscrollcommand=vsb.set,
            highlightthickness=0, selectborderwidth=0,
        )
        self._folder_lb.pack(fill='both', expand=True)
        vsb.config(command=self._folder_lb.yview)

        la = tk.Frame(lcard, bg=CARD)
        la.pack(fill='x', padx=14, pady=10)
        _mk_btn(la, '− Seçileni Kaldır', self._remove_folder,
                bg=CARD2, fg=TEXT2, px=12, py=6).pack(side='left')

        # ── Right: stat cards
        rcol = tk.Frame(cols, bg=BG)
        rcol.grid(row=0, column=1, sticky='nsew')

        self._var_files = tk.StringVar(value='0')
        self._var_faces = tk.StringVar(value='0')
        self._stat_card(rcol, self._var_files, 'İndekslenen Fotoğraf', GREEN).pack(fill='x', pady=(0, 10))
        self._stat_card(rcol, self._var_faces, 'Kayıtlı Yüz', ACCENT).pack(fill='x')

        tk.Frame(rcol, bg=BG, height=12).pack()
        _mk_btn(rcol, '🗑  İndeksi Temizle', self._clear_index,
                bg=CARD, fg=RED, px=14, py=8).pack(fill='x')

        # ── Progress section
        tk.Frame(page, bg=BORDER, height=1).pack(fill='x', pady=20)

        prog = tk.Frame(page, bg=BG)
        prog.pack(fill='x')

        self._prog_lbl = tk.Label(prog, text='', bg=BG, fg=TEXT2,
                                   font=('Segoe UI', 9))
        self._prog_lbl.pack(anchor='w', pady=(0, 7))

        self._progress = _Progress(prog)
        self._progress.pack(fill='x')

        # Action row
        act = tk.Frame(page, bg=BG)
        act.pack(fill='x', pady=18)

        self._index_btn = _mk_btn(act, '  İndeksle  ', self._start_index,
                                   bg=GREEN, fg='white', px=28, py=12)
        self._index_btn.pack(side='left')

        self._cancel_btn = _mk_btn(act, 'İptal', self._cancel_index,
                                    bg=RED, fg='white', px=16, py=12)
        self._cancel_btn.pack(side='left', padx=10)
        self._cancel_btn.pack_forget()

        return page

    def _stat_card(self, parent, str_var, label, color):
        card = tk.Frame(parent, bg=CARD)
        tk.Frame(card, bg=color, width=3).pack(side='left', fill='y')
        inner = tk.Frame(card, bg=CARD)
        inner.pack(side='left', fill='both', expand=True, padx=18, pady=16)
        tk.Label(inner, textvariable=str_var, bg=CARD, fg=TEXT,
                 font=('Segoe UI', 28, 'bold')).pack(anchor='w')
        tk.Label(inner, text=label, bg=CARD, fg=TEXT2,
                 font=('Segoe UI', 9)).pack(anchor='w')
        return card

    # ── Folder management ────────────────────────────────
    def _add_folder(self):
        f = filedialog.askdirectory(title='Klasör Seç')
        if f and f not in self._folders:
            self._folders.append(f)
            self._folder_lb.insert('end', f)

    def _remove_folder(self):
        sel = self._folder_lb.curselection()
        if sel:
            idx = sel[0]
            self._folders.pop(idx)
            self._folder_lb.delete(idx)

    def _clear_all_folders(self):
        if self._folders and messagebox.askyesno('Onay', 'Klasör listesi temizlensin mi?'):
            self._folders.clear()
            self._folder_lb.delete(0, 'end')

    def _clear_index(self):
        if messagebox.askyesno('Onay', 'Tüm indeks verileri silinecek.\nEmin misin?'):
            from core.database import clear_all
            clear_all()
            self._progress.set(0)
            self._prog_lbl.config(text='')
            self._refresh_stats()

    # ── Indexing ─────────────────────────────────────────
    def _start_index(self):
        if not self._folders:
            messagebox.showwarning('Uyarı', 'Lütfen önce klasör ekleyin.')
            return
        if self._indexing:
            return
        self._indexing = True
        self._cancel = False
        self._index_btn.pack_forget()
        self._cancel_btn.pack(side='left')
        self._progress.set(0)
        self._prog_lbl.config(text='Başlatılıyor…')
        threading.Thread(target=self._worker, daemon=True).start()
        self.after(100, self._poll)

    def _cancel_index(self):
        self._cancel = True
        self._cancel_btn.config(state='disabled')

    def _worker(self):
        from core.indexer import index_folder
        tf = len(self._folders)
        for fi, folder in enumerate(self._folders):
            if self._cancel:
                break

            def _cb(cur, total, name, _fi=fi, _tf=tf):
                pct = (_fi * 100 + cur / max(total, 1) * 100) / _tf
                self._q.put(('p', pct, f'{name}  ({cur} / {total})'))

            index_folder(folder, progress=_cb, cancelled=lambda: self._cancel)
        self._q.put(('done',))

    def _poll(self):
        try:
            while True:
                msg = self._q.get_nowait()
                if msg[0] == 'p':
                    self._progress.set(msg[1])
                    self._prog_lbl.config(text=msg[2])
                elif msg[0] == 'done':
                    self._on_done()
                    return
        except queue.Empty:
            pass
        if self._indexing:
            self.after(100, self._poll)

    def _on_done(self):
        self._indexing = False
        self._cancel_btn.config(state='normal')
        self._cancel_btn.pack_forget()
        self._index_btn.pack(side='left')
        if not self._cancel:
            self._progress.set(100)
            self._prog_lbl.config(text='İndeksleme tamamlandı ✓')
        else:
            self._prog_lbl.config(text='İptal edildi.')
        self._cancel = False
        self._refresh_stats()

    def _refresh_stats(self):
        try:
            from core.database import init, get_stats
            init()
            files, faces = get_stats()
            self._var_files.set(str(files))
            self._var_faces.set(str(faces))
            self._sb_stat.config(
                text=f'{files} fotoğraf\n{faces} yüz kayıtlı' if files else 'Veritabanı boş'
            )
        except Exception:
            pass
