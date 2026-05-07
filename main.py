from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse
import sqlite3
from datetime import datetime
import os
import google.generativeai as genai

app = FastAPI()

# --- BURAYA KENDİ API KEY'İNİ YAPIŞTIR ---
API_KEY = "AIzaSyBYAbZeXvsgvY2TDNpGHeHxIDjHX_URIaQ"
genai.configure(api_key=API_KEY)
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
    c.execute("SELECT isim, adim_sayisi FROM puanlar ORDER BY adim_sayisi DESC LIMIT 10")
    veriler = c.fetchall()
    conn.close()
    liste_html = "".join([f"<li style='margin:10px; font-size:18px;'>🏃 <b>{v[0]}:</b> {v[1]} Adım</li>" for v in veriler])
    return f"""
    <html>
    <head><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
    <body style="text-align:center; font-family:sans-serif; background:#f4f4f4; padding-top:50px;">
        <h1>🏆 Adım Yarışı</h1>
        <div style="background:white; display:inline-block; padding:20px; border-radius:10px; min-width:280px;">
            <ul style="list-style:none; padding:0;">{liste_html if liste_html else "Henüz kayıt yok."}</ul>
        </div>
        <hr style="margin:30px;">
        <form action="/analiz-et/" method="post" enctype="multipart/form-data">
            <input type="text" name="kullanici_adi" placeholder="Adınız" required style="padding:10px;"><br><br>
            <input type="file" name="file" required><br><br>
            <button type="submit" style="padding:10px 20px; background:green; color:white; border:none; border-radius:5px;">Fotoğrafı Gönder</button>
        </form>
    </body>
    </html>
    """

@app.post("/analiz-et/")
async def adim_analizi(kullanici_adi: str = Form(...), file: UploadFile = File(...)):
    try:
        img_data = await file.read()
        image_parts = [{"mime_type": "image/jpeg", "data": img_data}]
        
        # Yapay zekaya fotoğrafı soruyoruz
        response = model.generate_content([
            "Bu bir adımsayar ekran görüntüsü. Resimdeki toplam adım sayısını bul ve sadece rakam olarak yaz. Eğer bulamazsan '0' yaz.",
            image_parts[0]
        ])
        
        # Sadece rakamları alıyoruz
        adim_metni = "".join(filter(str.isdigit, response.text))
        adim_sayisi = int(adim_metni) if adim_metni else 0

        # Veritabanına kayıt
        conn = sqlite3.connect('yarismacilar.db')
        c = conn.cursor()
        c.execute("INSERT INTO puanlar (isim, adim_sayisi, tarih) VALUES (?, ?, ?)", 
                  (kullanici_adi, adim_sayisi, datetime.now().strftime("%H:%M")))
        conn.commit()
        conn.close()
        
        return HTMLResponse(content=f"<h2>Başarılı! {adim_sayisi} adım eklendi.</h2><a href='/'>Listeye Dön</a>")
    
    except Exception as e:
        return HTMLResponse(content=f"<h2>Bir hata oluştu:</h2><p>{str(e)}</p><a href='/'>Tekrar Dene</a>")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
