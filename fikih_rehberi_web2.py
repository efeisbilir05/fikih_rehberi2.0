import streamlit as st
import json
import requests
from datetime import datetime

# 1. Sayfa Yapılandırması
st.set_page_config(
    page_title="Hanefi Fıkhı Rehberi & Asistanı",
    page_icon="📖",
    layout="wide"
)

# 2. JSON Verisini Yükleme Fonksiyonu
@st.cache_data
def veriyi_yukle():
    try:
        with open("fikihrehberi.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"JSON dosyası yüklenemedi: {e}")
        return None

# 3. Namaz Vakitleri API Fonksiyonu
def namaz_vakitlerini_getir(sehir="Istanbul", ulke="Turkey"):
    # Method 13: Türkiye Cumhuriyeti Diyanet İşleri Başkanlığı yöntemidir.
    url = f"http://api.aladhan.com/v1/timingsByCity?city={sehir}&country={ulke}&method=13"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.json()["data"]["timings"]
    except:
        return None

# Veriyi Hazırla
data = veriyi_yukle()

# --- ARAYÜZ BAŞLANGICI ---
st.title("📖 Dijital Fıkıh Ansiklopedisi ve Asistanı")

if data:
    # Sekmeleri Oluştur
    tab1, tab2, tab3 = st.tabs(["📚 Fıkıh Rehberi", "🧮 Zekat Hesaplayıcı", "🕒 Namaz Vakitleri"])

    # --- TAB 1: FIKIH REHBERİ (JSON Arama & Listeleme) ---
    with tab1:
        st.header(f"{data.get('kitap_adi')} - Rehber")
        
        arama = st.text_input("🔍 Arama yapın (Örn: Sehiv Secdesi, İmsak, Mehir...)", placeholder="Kavram giriniz...")

        if arama:
            terim = arama.lower()
            bulundu = False
            for bolum in data["icerik"]:
                for alt in bolum.get("alt_konular", []):
                    if terim in alt["baslik"].lower() or any(terim in m.lower() for m in alt["maddeler"]):
                        with st.expander(f"📌 {bolum['bolum']} > {alt['baslik']}", expanded=True):
                            for madde in alt["maddeler"]:
                                if terim in madde.lower():
                                    st.markdown(f"✅ **{madde}**")
                                else:
                                    st.write(f"• {madde}")
                        bulundu = True
            if not bulundu:
                st.warning("Aradığınız terimle ilgili bir sonuç bulunamadı.")
        else:
            # Arama yoksa yan panelden seçilen bölümü göster
            secilen_bolum_adi = st.sidebar.selectbox("Hızlı Erişim: Bölüm Seçin", [b["bolum"] for b in data["icerik"]])
            for bolum in data["icerik"]:
                if bolum["bolum"] == secilen_bolum_adi:
                    st.subheader(f"📍 {bolum['bolum']}")
                    for alt in bolum.get("alt_konular", []):
                        with st.container():
                            st.markdown(f"### {alt['baslik']}")
                            for madde in alt["maddeler"]:
                                st.write(f"🔹 {madde}")
                            st.divider()

    # --- TAB 2: ZEKAT HESAPLAYICI ---
    with tab2:
        st.header("🧮 Zekat Hesaplama Modülü")
        st.info("Hanefi mezhebine göre 80.18 gram altın nisabı esas alınmıştır.")
        
        col1, col2 = st.columns(2)
        with col1:
            altin_gr_fiyati = st.number_input("Güncel Gram Altın Fiyatı (TL):", value=7254, min_value=1)
        
        nisap_siniri = 80.18 * altin_gr_fiyati
        with col2:
            st.metric("Nisap Sınırı (TL)", f"{nisap_siniri:,.2f}")

        with st.form("zekat_form"):
            n1 = st.number_input("Nakit Para ve Banka Mevduatı (TL):", min_value=0)
            n2 = st.number_input("Ziynet Eşyası ve Altın Birikimi (TL):", min_value=0)
            n3 = st.number_input("Ticari Mal Varlığı (TL):", min_value=0)
            n4 = st.number_input("Ödenmesi Gereken Borçlar (TL):", min_value=0)
            
            hesapla_btn = st.form_submit_button("Zekatı Hesapla")
            
            if hesapla_btn:
                toplam_matrah = (n1 + n2 + n3) - n4
                if toplam_matrah >= nisap_siniri:
                    zekat_miktari = toplam_matrah * 0.025
                    st.success(f"Zekat vermeniz farzdır. Ödenecek miktar: **{zekat_miktari:,.2f} TL**")
                else:
                    st.warning(f"Varlığınız nisap sınırının altında kalıyor ({toplam_matrah:,.2f} TL). Zekat farz değildir.")

    # --- TAB 3: NAMAZ VAKİTLERİ (API) ---
    with tab3:
        st.header("🕒 Canlı Namaz Vakitleri")
        sehir_input = st.text_input("Şehir adını girin (İngilizce karakterlerle):", "Istanbul")
        
        vakit_verileri = namaz_vakitlerini_getir(sehir_input)
        
        if vakit_verileri:
            st.write(f"### {sehir_input.capitalize()} İçin Bugünün Vakitleri")
            v_cols = st.columns(6)
            mapping = {
                "Fajr": "İmsak", "Sunrise": "Güneş", "Dhuhr": "Öğle",
                "Asr": "İkindi", "Maghrib": "Akşam", "Isha": "Yatsı"
            }
            for i, (key, tr_label) in enumerate(mapping.items()):
                v_cols[i].metric(tr_label, vakit_verileri[key])
            
            st.caption("Veriler Aladhan API (Diyanet Yöntemi) üzerinden anlık çekilmektedir.")
        else:
            st.error("Hata: Vakit bilgileri alınamadı. İnternet bağlantınızı veya şehir ismini kontrol edin.")

else:
    st.warning("Veri tabanı (fikihrehberi.json) bulunamadı. Lütfen dosyanın aynı dizinde olduğundan emin olun.")