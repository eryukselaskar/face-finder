# Face Finder

Yüz tanıma tabanlı fotoğraf arama masaüstü uygulaması.  
Referans bir fotoğraf yükleyin; uygulama tüm indekslenmiş klasörlerinizde aynı kişiyi arar.

---

## Özellikler

- **İki aşamalı sistem**: Klasörler bir kez indekslenir, arama saniyeler içinde sonuç verir
- **Offline çalışır**: İnternet bağlantısı gerektirmez
- **SQLite veritabanı**: Yüz vektörleri `~/.face_finder/index.db` dosyasında saklanır
- **Thumbnail galeri**: Bulunan fotoğraflar grid görünümünde, eşleşme yüzdesiyle gösterilir
- **Toplu kopyalama**: Tüm bulunan fotoğrafları tek tıkla seçilen klasöre kopyalar

---

## Kurulum

### Yöntem 1 — Conda (Windows için önerilen)

```bash
conda create -n face-finder python=3.10
conda activate face-finder
conda install -c conda-forge dlib
pip install face-recognition Pillow numpy
```

### Yöntem 2 — pip (derleme araçları gerektirir)

1. **CMake** yükleyin: https://cmake.org/download/
2. **Visual Studio Build Tools** yükleyin (C++ iş yükü seçin):  
   https://visualstudio.microsoft.com/tr/visual-cpp-build-tools/
3. Paketleri yükleyin:

```bash
pip install cmake dlib
pip install -r requirements.txt
```

### Yöntem 3 — Hazır dlib wheel (en hızlı)

`dlib`'in önceden derlenmiş wheel dosyasını indirip yükleyin:  
https://github.com/z-mahmud22/Dlib_Windows_Python3.x

```bash
pip install dlib-<versiyon>-cp310-cp310-win_amd64.whl
pip install -r requirements.txt
```

---

## Çalıştırma

```bash
python main.py
```

---

## Kullanım

### 1. İndeksleme

1. **Ana Sayfa**'da **"+ Klasör Ekle"** butonuna tıklayın
2. Fotoğraflarınızın bulunduğu klasörü seçin (birden fazla klasör ekleyebilirsiniz)
3. **"İndeksle"** butonuna tıklayın — progress bar ilerlemeyi gösterir
4. İndeksleme tamamlandığında istatistikler güncellenir

> Büyük klasörler için ilk indeksleme birkaç dakika sürebilir.  
> Bir sonraki arama işleminde veritabanı kullanıldığından sonuçlar anında gelir.

### 2. Arama

1. **"Yüz Ara →"** butonuna tıklayın
2. **"Fotoğraf Seç"** ile referans fotoğrafı yükleyin (aranacak kişinin net yüz fotoğrafı)
3. Hassasiyet kaydırıcısını ayarlayın (varsayılan `0.55` çoğu durumda uygundur)
4. **"Ara"** butonuna tıklayın

### 3. Sonuçlar

- Bulunan fotoğraflar eşleşme yüzdesiyle birlikte grid görünümde listelenir
- Fotoğrafa tıklayarak varsayılan görüntüleyicide açabilirsiniz
- **"Tümünü Kopyala"** ile tüm eşleşen fotoğrafları istediğiniz klasöre kopyalayabilirsiniz

---

## Hassasiyet Rehberi

| Tolerans | Açıklama |
|----------|----------|
| 0.30 – 0.45 | Çok sıkı — neredeyse birebir benzerlik gerekir |
| 0.45 – 0.55 | Sıkı — aynı kişi, farklı açılar |
| 0.55 – 0.65 | **Orta (önerilen)** — genel kullanım için ideal |
| 0.65 – 0.80 | Geniş — daha fazla sonuç, yanlış pozitifler artabilir |

---

## Proje Yapısı

```
face-finder/
├── main.py                 # Uygulama giriş noktası
├── core/
│   ├── database.py         # SQLite işlemleri
│   ├── indexer.py          # Klasör tarama ve vektör kaydetme
│   └── searcher.py         # Yüz eşleştirme
├── ui/
│   ├── main_window.py      # Ana pencere ve indeksleme ekranı
│   ├── search_panel.py     # Arama ekranı
│   └── results_panel.py    # Sonuç galerisi
├── requirements.txt
└── README.md
```

---

## Notlar

- Uygulama tamamen **CPU** üzerinde çalışır, GPU gerekmez
- Veritabanı dosyası: `C:\Users\<kullanıcı>\.face_finder\index.db`
- Desteklenen formatlar: JPG, JPEG, PNG, BMP, TIFF, WEBP
- Yüz bulunamayan fotoğraflar indeksleme sırasında atlanır
