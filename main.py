from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse
import sqlite3
from datetime import datetime
import uvicorn
import os
from PIL import Image
import io

app = FastAPI()

# Veritabanını oluştur
def veritabani_kur():
    conn = sqlite3.connect('yarismacilar.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS puanlar 
                 (isim TEXT, adim_sayisi INTEGER, tarih TEXT)''')
    conn.commit()
    conn.close()

veritabani_kur()

@app.get("/", response_class=HTMLResponse)
async def ana_sayfa():
    conn = sqlite3.connect('yarismacilar.db')
    c = conn.cursor()
    c.execute("SELECT isim, adim_sayisi FROM puanlar ORDER BY adim_sayisi DESC LIMIT 10")
    veriler = c.fetchall()
    conn.close()
    
    liste_html = "".join([f"<li style='margin:10px; font-size:20px;'>🏆 <b>{v[0]}:</b> {v[1]} Adım</li>" for v in veriler])
    
    return f"""
    <html>
        <head><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
        <body style="font-family:sans-serif; text-align:center; background-color:#f4f4f4; padding:20px;">
            <h1 style="color:#2c3e50;">🏃‍♂️ Adım Yarışı</h1>
            <div style="background:white; display:inline-block; padding:20px; border-radius:15px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); min-width:300px;">
                <ul style="list-style:none; padding:0;">{liste_html if liste_html else "Henüz kimse adım atmadı!"}</ul>
            </div>
            <br><br>
            <form action="/analiz-et/" method="post" enctype="multipart/form-data" style="background:#fff; display:inline-block; padding:20px; border-radius:10px; border:1px solid #ddd;">
                <h3>Fotoğraf Yükle</h3>
                <input type="text" name="kullanici_adi" placeholder="Adınız" required style="padding:10px; margin-bottom:10px; width:80% ; border-radius:5px; border:1px solid #ccc;"><br>
                <input type="file" name="file" accept="image/*" required style="padding:10px;"><br>
                <button type="submit" style="padding:12px 25px; background:#27ae60; color:white; border:none; border-radius:5px; cursor:pointer; font-size:16px;">Sıralamaya Gir</button>
            </form>
        </body>
    </html>
    """

@app.post("/analiz-et/")
async def adim_analizi(kullanici_adi: str = Form(...), file: UploadFile = File(...)):
    # Bu kısımda OCR işlemi çok basit bir mantıkla sayıyı yakalar
    # Render'da Pytesseract hatası almamak için metin okuma kısmını geçici olarak manuel veya alternatifle yapıyoruz
    
    # Şimdilik test için rastgele veya basit bir mantık kuruyoruz (Render çökmemesi için)
    # Gerçek OCR için Google Vision veya hafif bir API entegre edilebilir.
    # Şimdilik fotoğraf geldiğini onaylayıp basit bir sayı atayalım ki sistemin çalıştığını gör:
    
    adim_sayisi = 7500 # Test amaçlı, sistemi çalışır görmek için
    
    conn = sqlite3.connect('yarismacilar.db')
    c = conn.cursor()
    c.execute("INSERT INTO puanlar (isim, adim_sayisi, tarih) VALUES (?, ?, ?)", 
              (kullanici_adi, adim_sayisi, datetime.now().strftime("%Y-%m-%d %H:%M")))
    conn.commit()
    conn.close()

    return HTMLResponse(content=f"<h2>Tebrikler {kullanici_adi}! Adımın başarıyla kaydedildi.</h2><a href='/'>Listeye dön ve gör</a>")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)