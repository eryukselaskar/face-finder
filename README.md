# Face Finder — Yüz Tanıma Fotoğraf Arama Uygulaması

Referans bir fotoğraf yükleyin; uygulama tüm indekslenmiş klasörlerinizde aynı kişiyi saniyeler içinde bulur.

---

## Gereksinimler

- Python 3.11+
- İnternet bağlantısı (sadece ilk kurulum için)
- Disk alanı: ~3 GB (TensorFlow + modeller)

---

## Kurulum

### Windows

1. [python.org](https://python.org)'dan Python 3.11 indir ve kur

2. PowerShell veya CMD'yi aç:

```powershell
git clone https://github.com/eryukselaskar/face-finder.git
cd face-finder
git checkout mac-deepface
pip install -r requirements.txt
```

3. Çalıştır:

```powershell
python main.py
```

---

### Mac

Sol üst Apple → Bu Mac Hakkında → Chip'e bak.

**Apple Silicon (M1 / M2 / M3):**

```bash
git clone https://github.com/eryukselaskar/face-finder.git
cd face-finder
git checkout mac-deepface
pip3 install -r requirements.txt
pip3 install tensorflow-macos tensorflow-metal
```

**Intel Mac:**

```bash
git clone https://github.com/eryukselaskar/face-finder.git
cd face-finder
git checkout mac-deepface
pip3 install -r requirements.txt
```

Çalıştır:

```bash
python3 main.py
```

---

## İlk Çalıştırma

İlk açılışta ArcFace ve RetinaFace modelleri otomatik indirilir (~300 MB).  
İnternet bağlantısı gerekir, sadece bir kere yapılır.  
Sonraki açılışlarda internet gerekmez.

---

## Kullanım

1. **Klasör Seç → İndeksle** — bir kere yapılır, büyük klasörler birkaç dakika sürebilir
2. **Referans fotoğraf yükle → Ara** — net yüzlü bir fotoğraf seç
3. **Bulunan fotoğrafları görüntüle veya kopyala** — eşleşme yüzdesine göre sıralanır

---

## Notlar

- Desteklenen formatlar: JPG, PNG, BMP, TIFF, WEBP, HEIC (iPhone fotoğrafları dahil)
- Yüzsüz fotoğraflar otomatik atlanır, hata vermez
- İndeksleme bir kere yapılır; tekrar arama anında çalışır
- Veritabanı: `~/.face_finder/index.db`
