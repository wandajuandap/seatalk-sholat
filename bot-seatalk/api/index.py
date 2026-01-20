from flask import Flask, request, jsonify
import requests
import datetime
import os

app = Flask(__name__)

APP_ID = os.environ.get("APP_ID", "NDAwNzUwNzc4MDg4")
APP_SECRET = os.environ.get("APP_SECRET", "XqVrdxqVtUzmbityfKzEvdrAUdh7FYdr")

def get_seatalk_token():
    url = "https://openapi.seatalk.io/auth/app_access_token"
    payload = {"app_id": APP_ID, "app_secret": APP_SECRET}
    try:
        resp = requests.post(url, json=payload, timeout=10)
        if resp.status_code == 200:
            return resp.json().get("app_access_token")
    except:
        pass
    return None

def get_jadwal_sholat():
    now = datetime.datetime.now()
    # Menyesuaikan waktu server Vercel (UTC) ke WIB (UTC+7) secara manual
    # Atau gunakan library pytz jika ingin lebih rapi, tapi ini cara simpel tanpa nambah library berat
    wib_time = now + datetime.timedelta(hours=7)
    
    tahun = wib_time.year
    bulan = wib_time.month
    tanggal = wib_time.day
    
    # ID 1638 = Kota Yogyakarta
    url = f"https://api.myquran.com/v2/sholat/jadwal/1638/{tahun}/{bulan}/{tanggal}"
    
    try:
        resp = requests.get(url, timeout=5)
        data = resp.json()
        if data['status']:
            jadwal = data['data']['jadwal']
            return (
                f"🕌 **Jadwal Sholat Yogyakarta**\n"
                f"📅 {jadwal['date']}\n\n"
                f"🔹 Imsak: {jadwal['imsak']}\n"
                f"🔹 Subuh: {jadwal['subuh']}\n"
                f"🔹 Dzuhur: {jadwal['dzuhur']}\n"
                f"🔹 Ashar: {jadwal['ashar']}\n"
                f"🔹 Maghrib: {jadwal['maghrib']}\n"
                f"🔹 Isya: {jadwal['isya']}"
            )
    except Exception as e:
        return "Gagal mengambil data jadwal sholat."
    
    return "Data tidak ditemukan."

def reply_seatalk(content, group_id):
    token = get_seatalk_token()
    if not token: return

    url = "https://openapi.seatalk.io/webhook/group/v2/chat/send"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {
        "group_id": group_id,
        "message": {"text": {"content": content}}
    }
    requests.post(url, headers=headers, json=payload)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>', methods=['GET', 'POST'])
def handler(path):
    # Verifikasi Webhook SeaTalk (Challenge)
    if request.method == 'POST':
        data = request.json
        if data and data.get('event_type') == 'event_verification':
            return jsonify({"challenge": data.get('event_id')})
        
        # Logic Pesan
        try:
            event = data.get('event', {})
            message = event.get('message', {})
            text = message.get('text', {}).get('content', '').strip()
            
            if text == "/info":
                info = get_jadwal_sholat()
                group_id = message.get('group_id')
                if group_id:
                    reply_seatalk(info, group_id)
        except Exception as e:
            print(f"Error: {e}")
            
    return "SeaTalk Bot is Running 24/7 on Vercel!"
