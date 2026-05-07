from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse
import sqlite3
from datetime import datetime
import os
import google.generativeai as genai
from PIL import Image
import io

app = FastAPI()

# --- GOOGLE AI AYARI ---
genai.configure(api_key="AIzaSyBYAbZeXvsgvY2TDNpGHeHxIDjHX_URIaQ")
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
    liste_html = "".join([f"<li style='margin:10px; font-size:20px;'><b>{v[0]}:</b> {v[1]} Adım</li>" for v in veriler])
    return f"<html><body style='text-align:center; font-family:sans-serif;'><h1>🏆 Liderlik Tablosu</h1><ul>{liste_html}</ul><hr><form action='/analiz-et/' method='post' enctype='multipart/form-data'><input type='text' name='kullanici_adi' placeholder='Adınız' required><br><input type='file' name='file' required><br><button type='submit'>Gönder</button></form></body></html>"

@app.post("/analiz-et/")
async def adim_analizi(kullanici_adi: str = Form(...), file: UploadFile = File(...)):
    img_data = await file.read()
    img = Image.open(io.BytesIO(img_data))
    
    # Gemini'ye fotoğrafı gönderip sadece sayıyı sorma
    response = model.generate_content(["Bu bir adım sayar ekran görüntüsü. Resimdeki toplam adım sayısını sadece rakam olarak yaz. Başka hiçbir şey yazma.", img])
    
    try:
        # Gelen cevaptaki rakamları ayıkla
        adim_sayisi = int(''.join(filter(str.isdigit, response.text)))
    except:
        adim_sayisi = 0

    conn = sqlite3.connect('yarismacilar.db')
    c = conn.cursor()
    c.execute("INSERT INTO puanlar (isim, adim_sayisi, tarih) VALUES (?, ?, ?)", (kullanici_adi, adim_sayisi, datetime.now().strftime("%Y-%m-%d %H:%M")))
    conn.commit()
    conn.close()
    return HTMLResponse(content=f"<h2>Kaydedildi: {adim_sayisi} Adım</h2><a href='/'>Geri Dön</a>")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
