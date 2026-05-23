import sys

# Windows high-DPI awareness
try:
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass


def main():
    try:
        import face_recognition  # noqa: F401
    except ImportError:
        import tkinter.messagebox as mb
        import tkinter as tk
        tk.Tk().withdraw()
        mb.showerror(
            "Eksik Kütüphane",
            "face_recognition kütüphanesi bulunamadı.\n\n"
            "Kurulum için README.md dosyasını okuyun.",
        )
        sys.exit(1)

    from ui.main_window import MainWindow
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
