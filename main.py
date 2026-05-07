from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse
import sqlite3
from datetime import datetime
import os
import requests
import re

app = FastAPI()

# Veritabanını hazırla
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
    # En yüksek adımdan aşağıya doğru sırala
    c.execute("SELECT isim, adim_sayisi FROM puanlar ORDER BY adim_sayisi DESC LIMIT 30")
    veriler = c.fetchall()
    conn.close()
    
    liste_html = "".join([f"<li style='margin:10px; font-size:18px;'>🏃 <b>{v[0]}:</b> {v[1]} Adım</li>" for v in veriler])
    
    return f"""
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Adım Yarışı</title>
    </head>
    <body style="text-align:center; font-family:sans-serif; background:#f0f2f5; padding:20px;">
        <h1 style="color:#1a73e8;">🏆 Grup Adım Yarışı</h1>
        <div style="background:white; padding:20px; border-radius:15px; display:inline-block; min-width:300px; box-shadow:0 2px 10px rgba(0,0,0,0.1);">
            <ul style="list-style:none; padding:0; text-align:left;">{liste_html if liste_html else "Henüz kimse veri yüklemedi."}</ul>
        </div>
        <br><br>
        <div style="background:#fff; display:inline-block; padding:20px; border-radius:10px; border:1px solid #ddd;">
            <h3>Puanını Gönder</h3>
            <form action="/analiz-et/" method="post" enctype="multipart/form-data">
                <input type="text" name="kullanici_adi" placeholder="Adınız" required style="padding:10px; width:200px; margin-bottom:10px;"><br>
                <input type="file" name="file" accept="image/*" required><br><br>
                <button type="submit" style="padding:10px 25px; background:#28a745; color:white; border:none; border-radius:5px; cursor:pointer;">Yükle</button>
            </form>
        </div>
    </body>
    </html>
    """

@app.post("/analiz-et/")
async def adim_analizi(kullanici_adi: str = Form(...), file: UploadFile = File(...)):
    try:
        # Fotoğrafı oku
        image_content = await file.read()
        
        # OCR Servisine gönder (apikey 'helloworld' demo içindir)
        payload = {'apikey': 'helloworld', 'language': 'eng', 'isOverlayRequired': False}
        files = [('file', ('image.jpg', image_content, 'image/jpeg'))]
        
        response = requests.post('https://api.ocr.space/parse/image', data=payload, files=files)
        data = response.json()
        
        # Gelen metni temizle ve sayıları bul
        text = data.get("ParsedResults")[0].get("ParsedText")
        sayilar = re.findall(r'\d+', text.replace('.', '').replace(',', ''))
        
        # Genelde en uzun rakam dizisi adım sayısıdır (Örn: 12500)
        adim_sayisi = int(max(sayilar, key=len)) if sayilar else 0

        # Veritabanına işle
        conn = sqlite3.connect('yarismacilar.db')
        c = conn.cursor()
        c.execute("INSERT INTO puanlar (isim, adim_sayisi, tarih) VALUES (?, ?, ?)", 
                  (kullanici_adi, adim_sayisi, datetime.now().strftime("%H:%M")))
        conn.commit()
        conn.close()
        
        return HTMLResponse(content=f"<h2>Başarılı! {adim_sayisi} adım kaydedildi.</h2><a href='/'>Sıralamaya Dön</a>")
    
    except:
        return HTMLResponse(content="<h2>Hata!</h2><p>Resim okunamadı. Lütfen ekran görüntüsünü daha net çekin.</p><a href='/'>Tekrar Dene</a>")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
