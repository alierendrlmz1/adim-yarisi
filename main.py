from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse
import sqlite3
from datetime import datetime
import uvicorn
import os
import pytesseract
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
    c.execute("SELECT isim, adim_sayisi FROM puanlar ORDER BY adim_sayisi DESC")
    veriler = c.fetchall()
    conn.close()
    liste_html = "".join([f"<li style='margin:10px; font-size:20px;'><b>{v[0]}:</b> {v[1]} adım</li>" for v in veriler])
    
    return f"""
    <html>
        <body style="font-family:sans-serif; text-align:center; background-color:#f4f4f4;">
            <h1>🏆 Adım Yarışı Liderlik Tablosu</h1>
            <div style="background:white; display:inline-block; padding:20px; border-radius:15px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
                <ul style="list-style:none; padding:0;">{liste_html if liste_html else "Henüz kayıt yok!"}</ul>
            </div>
            <hr style="margin:40px 0;">
            <form action="/analiz-et/" method="post" enctype="multipart/form-data" style="background:#ecf0f1; display:inline-block; padding:20px; border-radius:10px;">
                <input type="text" name="kullanici_adi" placeholder="Adınız" required style="padding:10px; margin-bottom:10px; width:200px;"><br>
                <input type="file" name="file" accept="image/*" required><br><br>
                <button type="submit" style="padding:10px 20px; background:#27ae60; color:white; border:none; border-radius:5px; cursor:pointer;">Sonucu Gönder</button>
            </form>
        </body>
    </html>
    """

@app.post("/analiz-et/")
async def adim_analizi(kullanici_adi: str = Form(...), file: UploadFile = File(...)):
    # Resmi oku (RAM dostu yöntem)
    request_object_content = await file.read()
    img = Image.open(io.BytesIO(request_object_content))
    
    # Metni oku
    text = pytesseract.image_to_string(img)
    
    # Sayıları ayıkla
    adim_sayisi = 0
    import re
    sayilar = re.findall(r'\d+', text.replace('.', '').replace(',', ''))
    if sayilar:
        # En mantıklı adım sayısını bul (genelde 4-5 haneli olan)
        adim_sayisi = max([int(s) for s in sayilar if 100 < int(s) < 100000], default=0)

    conn = sqlite3.connect('yarismacilar.db')
    c = conn.cursor()
    c.execute("INSERT INTO puanlar (isim, adim_sayisi, tarih) VALUES (?, ?, ?)", 
              (kullanici_adi, adim_sayisi, datetime.now().strftime("%Y-%m-%d %H:%M")))
    conn.commit()
    conn.close()

    return HTMLResponse(content=f"<h2>Tebrikler {kullanici_adi}! {adim_sayisi} adım kaydedildi.</h2><a href='/'>Geri dön</a>")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)