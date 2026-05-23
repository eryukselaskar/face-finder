import os
import shutil
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

try:
    from PIL import Image, ImageDraw, ImageFont, ImageTk
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
AMBER   = '#f59e0b'
TEXT    = '#f1f0f5'
TEXT2   = '#7c7b9d'
TEXT3   = '#3d3c55'

THUMB_W = 200
THUMB_H = 158
COLS    = 4
_FONT   = 'C:/Windows/Fonts/segoeui.ttf'


def _shade(h: str, amt: int) -> str:
    r, g, b = int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16)
    return "#{:02x}{:02x}{:02x}".format(
        min(255, r + amt), min(255, g + amt), min(255, b + amt))


def _hex_rgb(h: str):
    return int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16)


def _badge_color(conf: int) -> str:
    if conf >= 70:
        return GREEN
    if conf >= 50:
        return ACCENT
    return AMBER


def _make_thumb(file_path: str, conf: int) -> "ImageTk.PhotoImage | None":
    if not PIL_OK:
        return None
    try:
        img = Image.open(file_path).convert('RGB')
        img.thumbnail((THUMB_W, THUMB_H))
        canvas = Image.new('RGB', (THUMB_W, THUMB_H), _hex_rgb(CARD))
        x = (THUMB_W - img.width) // 2
        y = (THUMB_H - img.height) // 2
        canvas.paste(img, (x, y))

        # Draw badge on top-right
        draw = ImageDraw.Draw(canvas)
        try:
            font = ImageFont.truetype(_FONT, 12)
        except Exception:
            font = ImageFont.load_default()

        badge_txt = f' {conf}% '
        bbox = draw.textbbox((0, 0), badge_txt, font=font)
        bw = bbox[2] - bbox[0] + 8
        bh = bbox[3] - bbox[1] + 6
        bx = THUMB_W - bw - 6
        by = 6
        r, g, b = _hex_rgb(_badge_color(conf))
        draw.rectangle([bx - 2, by, bx + bw, by + bh],
                       fill=(r, g, b, 220))
        draw.text((bx + 2, by + 3), badge_txt.strip(), fill=(255, 255, 255), font=font)

        return ImageTk.PhotoImage(canvas)
    except Exception:
        return None


class ResultsPanel(tk.Frame):
    def __init__(self, parent, main_window):
        super().__init__(parent, bg=BG)
        self._mw = main_window
        self._results: list = []
        self._photos: list = []
        self._build()

    def _build(self):
        # Header
        hdr = tk.Frame(self, bg=BG)
        hdr.pack(fill='x', pady=(0, 20))

        self._title = tk.Label(hdr, text='Sonuçlar', bg=BG, fg=TEXT,
                               font=('Segoe UI', 18, 'bold'))
        self._title.pack(side='left')

        self._badge = tk.Label(hdr, text='', bg=CARD2, fg=TEXT2,
                                font=('Segoe UI', 9), padx=10, pady=4)
        self._badge.pack(side='left', padx=12, anchor='s', pady=4)

        self._copy_btn = tk.Button(
            hdr, text='  Tümünü Kopyala  ', command=self._copy_all,
            bg=GREEN, fg='white', relief='flat', cursor='hand2',
            padx=0, pady=9, font=('Segoe UI', 10), bd=0,
            activebackground=_shade(GREEN, 15), activeforeground='white',
        )
        self._copy_btn.bind('<Enter>', lambda e: self._copy_btn.config(bg=_shade(GREEN, 22)))
        self._copy_btn.bind('<Leave>', lambda e: self._copy_btn.config(bg=GREEN))
        self._copy_btn.pack(side='right')

        # Scrollable canvas
        wrap = tk.Frame(self, bg=BG)
        wrap.pack(fill='both', expand=True)

        self._canvas = tk.Canvas(wrap, bg=BG, highlightthickness=0)
        sb = ttk.Scrollbar(wrap, orient='vertical', command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=sb.set)
        sb.pack(side='right', fill='y')
        self._canvas.pack(side='left', fill='both', expand=True)

        self._inner = tk.Frame(self._canvas, bg=BG)
        self._win = self._canvas.create_window((0, 0), window=self._inner, anchor='nw')

        self._inner.bind('<Configure>', lambda e: self._canvas.configure(
            scrollregion=self._canvas.bbox('all')))
        self._canvas.bind('<Configure>', lambda e: self._canvas.itemconfig(
            self._win, width=e.width))
        self._canvas.bind('<MouseWheel>', lambda e: self._canvas.yview_scroll(
            int(-1 * (e.delta / 120)), 'units'))

    # ── Data ─────────────────────────────────────────────
    def set_results(self, results: list):
        self._results = results
        self._photos.clear()
        for w in self._inner.winfo_children():
            w.destroy()

        n = len(results)
        self._badge.config(text=f'{n} eşleşme' if n else 'sonuç yok')
        self._copy_btn.config(state='normal' if n else 'disabled')

        if not results:
            tk.Label(self._inner,
                     text='Bu kişiye ait fotoğraf bulunamadı.\nFarklı bir referans fotoğraf veya daha yüksek tolerans deneyin.',
                     bg=BG, fg=TEXT2, font=('Segoe UI', 12),
                     justify='center').pack(pady=80)
            return

        for col in range(COLS):
            self._inner.columnconfigure(col, weight=1)

        for i, (fp, folder, dist) in enumerate(results):
            r, c = divmod(i, COLS)
            self._add_card(fp, folder, dist, r, c)

        self._canvas.yview_moveto(0)

    def _add_card(self, fp: str, folder: str, dist: float, row: int, col: int):
        conf = int((1 - dist) * 100)

        card = tk.Frame(self._inner, bg=CARD, cursor='hand2')
        card.grid(row=row, column=col, padx=7, pady=7, sticky='nw')

        # Hover effect
        def _hover(e):
            card.config(bg=CARD2)
            info.config(bg=CARD2)
            for w in info.winfo_children():
                w.config(bg=CARD2)

        def _leave(e):
            card.config(bg=CARD)
            info.config(bg=CARD)
            for w in info.winfo_children():
                w.config(bg=CARD)

        # Thumbnail
        photo = _make_thumb(fp, conf)
        if photo:
            self._photos.append(photo)
            img_lbl = tk.Label(card, image=photo, bg=CARD, bd=0, cursor='hand2')
            img_lbl.pack()
            img_lbl.bind('<Button-1>', lambda e, p=fp: self._open(p))
            img_lbl.bind('<Enter>', _hover)
            img_lbl.bind('<Leave>', _leave)
        else:
            placeholder = tk.Label(
                card, text=f'%{conf}\n⚠', bg=CARD, fg=_badge_color(conf),
                font=('Segoe UI', 14), width=THUMB_W // 8, height=THUMB_H // 18,
            )
            placeholder.pack()

        # Info strip
        info = tk.Frame(card, bg=CARD)
        info.pack(fill='x', padx=10, pady=(6, 10))

        name = Path(fp).name
        name_d = name if len(name) <= 26 else name[:23] + '…'
        tk.Label(info, text=name_d, bg=CARD, fg=TEXT,
                 font=('Segoe UI', 9, 'bold')).pack(anchor='w')

        fd = Path(folder).name
        fd_d = fd if len(fd) <= 26 else '…' + fd[-23:]
        tk.Label(info, text=fd_d, bg=CARD, fg=TEXT2,
                 font=('Segoe UI', 8)).pack(anchor='w')

        card.bind('<Enter>', _hover)
        card.bind('<Leave>', _leave)
        card.bind('<Button-1>', lambda e, p=fp: self._open(p))

    def _open(self, path: str):
        try:
            os.startfile(path)
        except Exception as e:
            messagebox.showerror('Hata', str(e))

    def _copy_all(self):
        if not self._results:
            return
        dest = filedialog.askdirectory(title='Hedef Klasör Seç')
        if not dest:
            return
        ok = err = 0
        for fp, _, _ in self._results:
            try:
                shutil.copy2(fp, dest)
                ok += 1
            except Exception:
                err += 1
        msg = f'{ok} fotoğraf "{Path(dest).name}" klasörüne kopyalandı.'
        if err:
            msg += f'\n{err} dosya kopyalanamadı.'
        messagebox.showinfo('Kopyalama Tamamlandı', msg)
