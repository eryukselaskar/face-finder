import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

try:
    from PIL import Image, ImageTk
    PIL_OK = True
except ImportError:
    PIL_OK = False

BG      = '#0d0d0f'
PANEL   = '#16161a'
CARD    = '#1c1c22'
CARD2   = '#23232c'
BORDER  = '#2d2d3d'
ACCENT  = '#6366f1'
ACCENTL = '#818cf8'
GREEN   = '#10b981'
RED     = '#ef4444'
TEXT    = '#f1f0f5'
TEXT2   = '#7c7b9d'
TEXT3   = '#3d3c55'

PREVIEW_SIZE = 290


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


class SearchPanel(tk.Frame):
    def __init__(self, parent, main_window):
        super().__init__(parent, bg=BG)
        self._mw = main_window
        self._ref_path: str | None = None
        self._photo = None
        self._build()

    def _build(self):
        # Title
        tk.Label(self, text='Yüz Ara', bg=BG, fg=TEXT,
                 font=('Segoe UI', 18, 'bold')).pack(anchor='w', pady=(0, 22))

        # Two columns
        cols = tk.Frame(self, bg=BG)
        cols.pack(fill='both', expand=True)
        cols.columnconfigure(0, weight=2)
        cols.columnconfigure(1, weight=3)

        # ── Left: photo upload card
        lcard = tk.Frame(cols, bg=CARD)
        lcard.grid(row=0, column=0, sticky='nsew', padx=(0, 14))

        tk.Label(lcard, text='REFERANS FOTOĞRAF', bg=CARD, fg=TEXT3,
                 font=('Segoe UI', 8, 'bold')).pack(anchor='w', padx=18, pady=(16, 12))
        tk.Frame(lcard, bg=BORDER, height=1).pack(fill='x')

        # Dashed preview area (simulated with Canvas)
        prev_outer = tk.Frame(lcard, bg=CARD)
        prev_outer.pack(padx=20, pady=18)

        self._prev_canvas = tk.Canvas(
            prev_outer, width=PREVIEW_SIZE, height=PREVIEW_SIZE,
            bg=CARD2, highlightthickness=1, highlightbackground=BORDER,
            cursor='hand2',
        )
        self._prev_canvas.pack()
        self._prev_text = self._prev_canvas.create_text(
            PREVIEW_SIZE // 2, PREVIEW_SIZE // 2,
            text='Tıklayarak fotoğraf seçin',
            fill=TEXT3, font=('Segoe UI', 11),
        )
        self._prev_canvas.bind('<Button-1>', lambda e: self._pick())

        _mk_btn(lcard, 'Fotoğraf Seç', self._pick,
                bg=ACCENT, fg='white', px=24, py=10).pack(pady=(0, 8))

        self._name_lbl = tk.Label(lcard, text='', bg=CARD, fg=TEXT2,
                                   font=('Segoe UI', 9))
        self._name_lbl.pack(pady=(0, 18))

        # ── Right: settings card
        rcard = tk.Frame(cols, bg=CARD)
        rcard.grid(row=0, column=1, sticky='nsew')

        tk.Label(rcard, text='ARAMA AYARLARI', bg=CARD, fg=TEXT3,
                 font=('Segoe UI', 8, 'bold')).pack(anchor='w', padx=18, pady=(16, 12))
        tk.Frame(rcard, bg=BORDER, height=1).pack(fill='x')

        # Tolerance
        tol_wrap = tk.Frame(rcard, bg=CARD)
        tol_wrap.pack(fill='x', padx=20, pady=22)

        tol_hdr = tk.Frame(tol_wrap, bg=CARD)
        tol_hdr.pack(fill='x', pady=(0, 10))
        tk.Label(tol_hdr, text='Eşleşme Hassasiyeti', bg=CARD, fg=TEXT,
                 font=('Segoe UI', 11, 'bold')).pack(side='left')
        self._tol_val_lbl = tk.Label(tol_hdr, text='0.55', bg=CARD, fg=ACCENTL,
                                      font=('Segoe UI', 11, 'bold'))
        self._tol_val_lbl.pack(side='right')

        self._tol_var = tk.DoubleVar(value=0.55)
        tk.Scale(
            tol_wrap, from_=0.30, to=0.80, resolution=0.05,
            variable=self._tol_var, orient='horizontal',
            bg=CARD, fg=TEXT2, troughcolor=CARD2, highlightthickness=0,
            sliderlength=20, showvalue=False, command=self._on_tol,
        ).pack(fill='x')

        self._tol_desc = tk.Label(tol_wrap, text='Orta', bg=CARD, fg=TEXT2,
                                   font=('Segoe UI', 9))
        self._tol_desc.pack(anchor='w', pady=(6, 0))

        # Reference table
        tk.Frame(rcard, bg=BORDER, height=1).pack(fill='x', padx=20, pady=(0, 18))

        tbl = tk.Frame(rcard, bg=CARD)
        tbl.pack(fill='x', padx=20)

        rows = [
            ('0.30 – 0.45', 'Çok Sıkı  —  en az yanlış pozitif', TEXT3),
            ('0.45 – 0.55', 'Sıkı  —  güvenilir eşleşme',         TEXT2),
            ('0.55 – 0.65', 'Orta  ★  —  önerilen',               ACCENTL),
            ('0.65 – 0.80', 'Geniş  —  fazla ama belirsiz sonuç', TEXT2),
        ]
        for val, desc, color in rows:
            r = tk.Frame(tbl, bg=CARD)
            r.pack(fill='x', pady=5)
            tk.Label(r, text=val, bg=CARD, fg=TEXT3,
                     font=('Courier New', 9), width=13, anchor='w').pack(side='left')
            tk.Label(r, text=desc, bg=CARD, fg=color,
                     font=('Segoe UI', 9)).pack(side='left', padx=10)

        # ── Search button
        bottom = tk.Frame(self, bg=BG)
        bottom.pack(pady=24)

        self._search_btn = _mk_btn(bottom, '     Ara     ', self._do_search,
                                    bg=ACCENT, fg='white', px=40, py=14)
        self._search_btn.config(font=('Segoe UI', 11, 'bold'))
        self._search_btn.pack()

        self._status_lbl = tk.Label(bottom, text='', bg=BG, fg=TEXT2,
                                     font=('Segoe UI', 9))
        self._status_lbl.pack(pady=(8, 0))

    # ── Handlers ─────────────────────────────────────────
    def _on_tol(self, val):
        v = float(val)
        self._tol_val_lbl.config(text=f'{v:.2f}')
        descs = [(0.45, 'Çok Sıkı'), (0.50, 'Sıkı'),
                 (0.65, 'Orta'), (0.75, 'Geniş'), (1.0, 'Çok Geniş')]
        self._tol_desc.config(text=next(n for t, n in descs if v < t))

    def _pick(self):
        path = filedialog.askopenfilename(
            title='Referans Fotoğraf Seç',
            filetypes=[('Görüntü', '*.jpg *.jpeg *.png *.bmp *.tiff *.webp *.heic')],
        )
        if not path:
            return
        self._ref_path = path
        self._name_lbl.config(text=Path(path).name)
        self._load_preview(path)

    def _load_preview(self, path: str):
        self._prev_canvas.delete('all')
        if not PIL_OK:
            self._prev_canvas.create_text(
                PREVIEW_SIZE // 2, PREVIEW_SIZE // 2,
                text=Path(path).name, fill=TEXT2, font=('Segoe UI', 10))
            return
        try:
            img = Image.open(path)
            img.thumbnail((PREVIEW_SIZE - 4, PREVIEW_SIZE - 4))
            self._photo = ImageTk.PhotoImage(img)
            x = PREVIEW_SIZE // 2
            y = PREVIEW_SIZE // 2
            self._prev_canvas.create_image(x, y, image=self._photo, anchor='center')
        except Exception:
            self._prev_canvas.create_text(
                PREVIEW_SIZE // 2, PREVIEW_SIZE // 2,
                text='Önizleme yüklenemedi', fill=RED, font=('Segoe UI', 10))

    def _do_search(self):
        if not self._ref_path:
            messagebox.showwarning('Uyarı', 'Lütfen referans fotoğraf seçin.')
            return

        from core.database import get_stats
        _, faces = get_stats()
        if faces == 0:
            messagebox.showwarning(
                'Uyarı',
                'Veritabanı boş.\nÖnce İndeksle sekmesinden klasörlerinizi indeksleyin.',
            )
            return

        self._status_lbl.config(text='Aranıyor…')
        self._search_btn.config(state='disabled')
        self.update()

        try:
            from core.searcher import get_encoding, search

            enc = get_encoding(self._ref_path)
            if enc is None:
                messagebox.showerror('Hata', 'Referans fotoğrafta yüz algılanamadı.')
                self._status_lbl.config(text='')
                return

            results = search(enc, tolerance=self._tol_var.get())
            self._status_lbl.config(text=f'{len(results)} fotoğraf bulundu')
            self._mw.show_results(results)
        except Exception as e:
            messagebox.showerror('Hata', str(e))
            self._status_lbl.config(text='')
        finally:
            self._search_btn.config(state='normal')
