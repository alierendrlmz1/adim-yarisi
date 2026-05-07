import easyocr
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse
import sqlite3
from datetime import datetime
import uvicorn
import os

app = FastAPI()

# OCR okuyucusunu başlat
reader = easyocr.Reader(['en'])

# Veritabanını oluştur ve tabloyu hazırla
def veritabani_kur():
    conn = sqlite3.connect('yarismacilar.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS puanlar 
                 (isim TEXT, adim_sayisi INTEGER, tarih TEXT)''')
    conn.commit()
    conn.close()

veritabani_kur()

# ANA SAYFA (Arayüz - Tarayıcıda görünen kısım)
@app.get("/", response_class=HTMLResponse)
async def ana_sayfa():
    conn = sqlite3.connect('yarismacilar.db')
    c = conn.cursor()
    c.execute("SELECT isim, adim_sayisi FROM puanlar ORDER BY adim_sayisi DESC")
    veriler = c.fetchall()
    conn.close()

    liste_html = "".join([f"<li style='margin:10px; font-size:20px;'><b>{v[0]}:</b> {v[1]} adım</li>" for v in veriler])
    
    return f"""
    <html>
        <head><title>Adım Yarışı</title></head>
        <body style="font-family:sans-serif; text-align:center; background-color:#f4f4f4;">
            <h1 style="color:#2c3e50;">🏆 Adım Yarışı Liderlik Tablosu</h1>
            <div style="background:white; display:inline-block; padding:20px; border-radius:15px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
                <ul style="list-style:none; padding:0;">{liste_html if liste_html else "Henüz kayıt yok!"}</ul>
            </div>
            <hr style="margin:40px 0;">
            <h2>Fotoğraf Yükle ve Katıl</h2>
            <form action="/analiz-et/" method="post" enctype="multipart/form-data" style="background:#ecf0f1; display:inline-block; padding:20px; border-radius:10px;">
                <input type="text" name="kullanici_adi" placeholder="Adınız" required style="padding:10px; margin-bottom:10px; width:200px;"><br>
                <input type="file" name="file" accept="image/*" required style="padding:10px;"><br><br>
                <button type="submit" style="padding:10px 20px; background:#27ae60; color:white; border:none; border-radius:5px; cursor:pointer;">Sonucu Gönder</button>
            </form>
        </body>
    </html>
    """

@app.post("/analiz-et/")
async def adim_analizi(kullanici_adi: str = Form(...), file: UploadFile = File(...)):
    # Dosyayı oku
    contents = await file.read()
    results = reader.readtext(contents)
    
    adim_sayisi = 0
    for (bbox, text, prob) in results:
        temiz_metin = "".join(filter(str.isdigit, text))
        if temiz_metin:
            sayi = int(temiz_metin)
            if 100 < sayi < 100000 and sayi > adim_sayisi:
                adim_sayisi = sayi

    # Veritabanına kaydet
    conn = sqlite3.connect('yarismacilar.db')
    c = conn.cursor()
    c.execute("INSERT INTO puanlar (isim, adim_sayisi, tarih) VALUES (?, ?, ?)", 
              (kullanici_adi, adim_sayisi, datetime.now().strftime("%Y-%m-%d %H:%M")))
    conn.commit()
    conn.close()

    return HTMLResponse(content=f"""
        <div style="text-align:center; font-family:sans-serif; margin-top:50px;">
            <h2>Tebrikler {kullanici_adi}!</h2>
            <p style="font-size:24px;">{adim_sayisi} adım başarıyla kaydedildi.</p>
            <a href="/" style="text-decoration:none; color:blue; font-weight:bold;">Sıralamaya geri dön</a>
        </div>
    """)

if __name__ == "__main__":
    # Render ve diğer sunucular için port ayarı
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)