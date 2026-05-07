from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse
import sqlite3
from datetime import datetime
import os
import google.generativeai as genai

app = FastAPI()

# --- API KEY'İNİ BURAYA YAPIŞTIR ---
API_KEY = "AIzaSyCE49GFye67YmZvZFUIeNwywWPdVYerVK4"
genai.configure(api_key=API_KEY)

# En basit model ismini deniyoruz
model = genai.GenerativeModel('gemini-1.5-flash')

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
    c.execute("SELECT isim, adim_sayisi FROM puanlar ORDER BY adim_sayisi DESC LIMIT 15")
    veriler = c.fetchall()
    conn.close()
    
    liste_html = "".join([f"<li style='margin:10px; font-size:18px;'><b>{v[0]}:</b> {v[1]} Adım</li>" for v in veriler])
    
    return f"""
    <html>
    <head><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
    <body style="text-align:center; font-family:sans-serif; background:#f4f4f4; padding:20px;">
        <h1>🏆 Liderlik Tablosu</h1>
        <div style="background:white; padding:20px; border-radius:15px; display:inline-block; min-width:280px;">
            <ul style="list-style:none; padding:0;">{liste_html if liste_html else "Henüz kayıt yok!"}</ul>
        </div>
        <hr>
        <form action="/analiz-et/" method="post" enctype="multipart/form-data">
            <input type="text" name="kullanici_adi" placeholder="İsminiz" required style="padding:10px; margin-bottom:10px;"><br>
            <input type="file" name="file" accept="image/*" required><br><br>
            <button type="submit" style="padding:10px 20px; background:green; color:white; border:none; border-radius:5px;">Gönder</button>
        </form>
    </body>
    </html>
    """

@app.post("/analiz-et/")
async def adim_analizi(kullanici_adi: str = Form(...), file: UploadFile = File(...)):
    try:
        img_data = await file.read()
        
        # Google'a resmi ve soruyu gönderiyoruz
        response = model.generate_content([
            "Resimdeki toplam adım sayısını sadece sayı olarak yaz.", 
            {"mime_type": "image/jpeg", "data": img_data}
        ])
        
        # Sayı ayıklama
        import re
        adim_sayisi = 0
        sayi_listesi = re.findall(r'\d+', response.text.replace('.', '').replace(',', ''))
        if sayi_listesi:
            adim_sayisi = int(sayi_listesi[0])

        conn = sqlite3.connect('yarismacilar.db')
        c = conn.cursor()
        c.execute("INSERT INTO puanlar (isim, adim_sayisi, tarih) VALUES (?, ?, ?)", 
                  (kullanici_adi, adim_sayisi, datetime.now().strftime("%H:%M")))
        conn.commit()
        conn.close()
        
        return HTMLResponse(content=f"<h2>{adim_sayisi} adım başarıyla kaydedildi!</h2><a href='/'>Geri Dön</a>")
    
    except Exception as e:
        # Hata mesajını daha anlaşılır basıyoruz
        return HTMLResponse(content=f"<h2>Hata:</h2><p>{str(e)}</p><a href='/'>Tekrar Dene</a>")
