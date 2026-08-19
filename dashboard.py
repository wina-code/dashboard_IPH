import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from PIL import Image
import base64
from io import BytesIO

# =============================================================================
# 🎨 1. KONFIGURASI HALAMAN & CUSTOM STYLING (ICON PNG)
# =============================================================================
try:
    icon_img = Image.open('logo BPS.png')
except Exception:
    icon_img = "📈"

st.set_page_config(
    page_title="Dashboard Indeks Perubahan Harga",
    page_icon=icon_img,
    layout="wide"
)

# Fungsi untuk konversi gambar lokal ke base64 agar bisa masuk ke dalam HTML
def get_image_base64(path):
    try:
        with open(path, "rb") as image_file:
            encoded = base64.b64encode(image_file.read()).decode()
            return f"data:image/png;base64,{encoded}"
    except Exception:
        return ""

logo_base64 = get_image_base64('logo BPS.png')

# Custom CSS 
st.markdown("""
    <style>
        .stApp {
            background-color: #f8f9fa;
        }
        [data-testid="stSidebar"] {
            background-color: #ffffff;
            border-right: 1px solid #e9ecef;
        }
        .main-header {
            background: linear-gradient(90deg, #1f77b4 0%, #0d47a1 100%);
            padding: 20px;
            border-radius: 12px;
            color: white;
            margin-bottom: 25px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.07);
        }
        .main-header h1 {
            color: #ffffff !important;
            margin: 0;
            font-size: 26px;
            font-weight: 700;
        }
        .main-header p {
            color: #e0e0e0 !important;
            margin: 5px 0 0 0;
            font-size: 14px;
        }
        div[data-testid="stMetric"] {
            background-color: #ffffff;
            border: 1px solid #000080;
            padding: 15px 20px;
            border-radius: 12px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.04);
        }
    </style>
""", unsafe_allow_html=True)

# Header 
if logo_base64:
    header_content = f"""
        <div class="main-header">
            <div style="display: flex; align-items: center; gap: 15px;">
                <img src="{logo_base64}" style="width: 120px; height: 90px; object-fit: contain;">
                <div>
                    <h1>Dashboard Indeks Perubahan Harga (IPH) 2026</h1>
                    <p>Monitoring IPH, Komoditas Andil Perubahan Harga, dan Fluktuasi Harga Tertinggi (<b>Kab. Kuningan</b> dan <b>Prov. Jawa Barat</b>)</p>
                </div>
            </div>
        </div>
    """
else:
    header_content = """
        <div class="main-header">
            <h1>📈 Dashboard Indeks Perubahan Harga (IPH) 2026</h1>
            <p>Monitoring IPH, Komoditas Andil Perubahan Harga, dan Fluktuasi Harga Tertinggi (<b>Kab. Kuningan</b> dan <b>Prov. Jawa Barat</b>)</p>
        </div>
    """

st.markdown(header_content, unsafe_allow_html=True)

# =============================================================================
# 2. LINK CSV GOOGLE SHEET
# =============================================================================
LINK_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRT6pXSi9_pf7voqO06lfD8KgTvF4uqwRI8eb254EemJS5pg9WnLcZFjHHq7HmPsSYdHj8TZK0zePZX/pub?output=csv"  

@st.cache_data(ttl=60)
def load_data():
    df_raw = pd.read_csv(LINK_CSV, header=None)
    
    row0 = df_raw.iloc[0].ffill().fillna('')
    row1 = df_raw.iloc[1].fillna('')
    
    raw_cols = []
    for idx, (r0, r1) in enumerate(zip(row0, row1)):
        r0_str = str(r0).strip()
        r1_str = str(r1).strip()
        
        if idx == 0:
            raw_cols.append("SERIES")
            continue
            
        if r0_str and r1_str and r0_str != r1_str:
            name = f"{r0_str} - {r1_str}"
        elif r0_str:
            name = r0_str
        else:
            name = r1_str
            
        raw_cols.append(name)
        
    seen_names = {}
    unique_cols = []
    
    for c in raw_cols:
        if c in seen_names:
            seen_names[c] += 1
            if "Kuningan" not in c and "Jawa Barat" not in c:
                unique_name = f"{c} (Prov. Jawa Barat)" if seen_names[c] == 1 else f"{c} ({seen_names[c]})"
            else:
                unique_name = f"{c} ({seen_names[c]})"
        else:
            seen_names[c] = 0
            if c != "SERIES" and "Kuningan" not in c and "Jawa Barat" not in c:
                unique_name = f"{c} (Kab. Kuningan)"
            else:
                unique_name = c
                
        unique_cols.append(unique_name)
        
    df = df_raw.iloc[2:].copy()
    df.columns = unique_cols
    return df.dropna(how='all')

# =============================================================================
# 3. PROSES PEMBACAAN & VISUALISASI DATA
# =============================================================================
try:
    df = load_data()

    # --- SIDEBAR FILTER PERIODE & WILAYAH ---
    st.sidebar.header("🔍 Filter Tampilan")
    
    filter_wilayah = st.sidebar.radio(
        "Pilih Wilayah Tampilan:",
        options=["Semua (Perbandingan)", "Kab. Kuningan", "Prov. Jawa Barat"],
        index=0
    )
    
    st.sidebar.markdown("---")
    
    col_series = "SERIES"
    df[col_series] = df[col_series].astype(str).str.strip().replace(["", "nan", "None", "<NA>"], None).ffill()
    df = df.dropna(subset=[col_series])
    
    list_series = [s for s in df[col_series].unique() if s and s != "None"]
    selected_series = st.sidebar.multiselect(
        "Pilih Periode / Minggu (SERIES):",
        options=list_series,
        default=list_series
    )
    
    df_filtered = df[df[col_series].isin(selected_series)].copy()

    # --- TAB INTERAKTIF ---
    tab1, tab2, tab3 = st.tabs([
        "📊 Perubahan Indikator IPH (%)", 
        "🌾 Komoditas Andil", 
        "⚠️ Fluktuasi Harga Tertinggi"
    ])

    # =========================================================================
    # TAB 1: INDIKATOR IPH
    # =========================================================================
    with tab1:
        cols_iph = [c for c in df_filtered.columns if "Perubahan Indikator" in c or "IPH" in c]
        if len(cols_iph) > 2:
            cols_iph = cols_iph[:2]
        
        if cols_iph:
            col_kun = cols_iph[0] if len(cols_iph) > 0 else None
            col_jab = cols_iph[1] if len(cols_iph) > 1 else None

            # Filter Kolom Tabel
            if filter_wilayah == "Kab. Kuningan" and col_kun:
                cols_tabel_tampil = [col_series, col_kun]
            elif filter_wilayah == "Prov. Jawa Barat" and col_jab:
                cols_tabel_tampil = [col_series, col_jab]
            else:
                cols_tabel_tampil = [col_series] + cols_iph

            # Ekstraksi angka asli per periode
            df_chart_list = []
            for period in selected_series:
                sub_df = df_filtered[df_filtered[col_series] == period]
                row_data = {col_series: period}
                
                def get_val(col):
                    if not col: return None
                    for val in sub_df[col]:
                        try:
                            return float(str(val).replace(',', '.').replace('%', '').strip())
                        except ValueError:
                            continue
                    return None
                
                row_data['Kab. Kuningan'] = get_val(col_kun)
                row_data['Prov. Jawa Barat'] = get_val(col_jab)
                df_chart_list.append(row_data)
                
            df_chart = pd.DataFrame(df_chart_list)
            df_chart = df_chart.dropna(subset=['Kab. Kuningan', 'Prov. Jawa Barat'], how='all')

            # 💡 1. KOTAK KPI METRIC CARDS (SELISIH & TERBARU)
            df_chart_valid = df_chart.dropna(subset=['Kab. Kuningan', 'Prov. Jawa Barat'])
            if not df_chart_valid.empty:
                latest = df_chart_valid.iloc[-1]
                val_kun_latest = latest['Kab. Kuningan']
                val_jab_latest = latest['Prov. Jawa Barat']
                selisih = val_kun_latest - val_jab_latest
                
                if filter_wilayah == "Kab. Kuningan":
                    st.metric("IPH Terbaru (Kab. Kuningan)", f"{val_kun_latest:.2f}%")
                elif filter_wilayah == "Prov. Jawa Barat":
                    st.metric("IPH Terbaru (Prov. Jawa Barat)", f"{val_jab_latest:.2f}%")
                else:
                    m1, m2, m3 = st.columns(3)
                    m1.metric("IPH Terbaru (Kab. Kuningan)", f"{val_kun_latest:.2f}%")
                    m2.metric("IPH Terbaru (Prov. Jawa Barat)", f"{val_jab_latest:.2f}%")
                    m3.metric("Selisih (Kuningan vs Jabar)", f"{selisih:+.2f}%")
                
                st.markdown("<br>", unsafe_allow_html=True)

            # 📋 2. TABEL DATA MENTAH
            st.subheader(f"📋 Tabel Data Perubahan Indikator IPH (%) - {filter_wilayah}")
            st.dataframe(df_filtered[cols_tabel_tampil].fillna("-"), use_container_width=True)
            st.markdown("---")
            
            # 📈 3. GRAFIK TREN GARIS RAPIH DENGAN ANGKA PERSENTASE DI TITIKNYA
            st.subheader(f"📈 Visualisasi Grafik Tren IPH Waktu ke Waktu ({filter_wilayah})")
            
            if not df_chart.empty:
                fig_line = go.Figure()
                
                # Garis Kab. Kuningan (Biru Solid)
                if filter_wilayah in ["Semua (Perbandingan)", "Kab. Kuningan"] and 'Kab. Kuningan' in df_chart.columns:
                    val_series_kun = df_chart['Kab. Kuningan']
                    fig_line.add_trace(go.Scatter(
                        x=df_chart[col_series],
                        y=val_series_kun,
                        mode='lines+markers+text',
                        name='Kab. Kuningan',
                        text=[f"{v:.2f}%" if pd.notna(v) else "" for v in val_series_kun],
                        textposition="top center",
                        line=dict(color='#1f77b4', width=3.5),
                        marker=dict(size=8, color='#1f77b4')
                    ))
                
                # Garis Prov. Jawa Barat (Oranye Putus-Putus)
                if filter_wilayah in ["Semua (Perbandingan)", "Prov. Jawa Barat"] and 'Prov. Jawa Barat' in df_chart.columns:
                    val_series_jab = df_chart['Prov. Jawa Barat']
                    fig_line.add_trace(go.Scatter(
                        x=df_chart[col_series],
                        y=val_series_jab,
                        mode='lines+markers+text',
                        name='Prov. Jawa Barat',
                        text=[f"{v:.2f}%" if pd.notna(v) else "" for v in val_series_jab],
                        textposition="bottom center",
                        line=dict(color='#ff7f0e', width=3, dash='dash'),
                        marker=dict(size=8, color='#ff7f0e')
                    ))
                
                # Garis Acuan Nol (0%)
                fig_line.add_hline(y=0, line_dash="dot", line_color="gray", annotation_text="Batas Netral (0%)")
                
                fig_line.update_layout(
                    title=f"<b>Grafik Pergerakan Tren IPH ({filter_wilayah})</b>",
                    xaxis_title="Periode / Minggu",
                    yaxis_title="Indeks Perubahan (%)",
                    hovermode="x unified",
                    template="plotly_white",
                    height=480,
                    margin=dict(l=20, r=20, t=50, b=20),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                
                st.plotly_chart(fig_line, use_container_width=True)
            else:
                st.warning("⚠️ Tidak ada data angka IPH yang valid untuk digambar di grafik.")
            
        else:
            st.dataframe(df_filtered, use_container_width=True)

    # =========================================================================
    # TAB 2: KOMODITAS ANDIL (TERFILTER WILAYAH)
    # =========================================================================
    with tab2:
        st.subheader(f"🌾 Komoditas Andil Perubahan Harga - {filter_wilayah}")
        cols_andil = [c for c in df_filtered.columns if "Komoditas" in c or "Andil" in c]
        
        if cols_andil:
            if filter_wilayah == "Kab. Kuningan":
                cols_andil_tampil = [c for c in cols_andil if "Kuningan" in c]
            elif filter_wilayah == "Prov. Jawa Barat":
                cols_andil_tampil = [c for c in cols_andil if "Jawa Barat" in c or "Jabar" in c]
            else:
                cols_andil_tampil = cols_andil
                
            if not cols_andil_tampil:
                cols_andil_tampil = cols_andil
                
            st.dataframe(df_filtered[[col_series] + cols_andil_tampil].fillna("-"), use_container_width=True)
        else:
            st.dataframe(df_filtered.fillna("-"), use_container_width=True)

    # =========================================================================
    # TAB 3: FLUKTUASI HARGA TERTINGGI (TERFILTER WILAYAH)
    # =========================================================================
    with tab3:
        st.subheader(f"⚠️ Fluktuasi Harga Tertinggi - {filter_wilayah}")
        cols_fluk = [c for c in df_filtered.columns if "Fluktuasi" in c]
        
        if cols_fluk:
            if filter_wilayah == "Kab. Kuningan":
                cols_fluk_tampil = [c for c in cols_fluk if "Kuningan" in c]
            elif filter_wilayah == "Prov. Jawa Barat":
                cols_fluk_tampil = [c for c in cols_fluk if "Jawa Barat" in c or "Jabar" in c]
            else:
                cols_fluk_tampil = cols_fluk
                
            if not cols_fluk_tampil:
                cols_fluk_tampil = cols_fluk
                
            st.dataframe(df_filtered[[col_series] + cols_fluk_tampil].fillna("-"), use_container_width=True)
        else:
            st.dataframe(df_filtered.fillna("-"), use_container_width=True)

except Exception as e:
    st.warning("⚠️ Pastikan kamu sudah memasukkan Link CSV Google Sheet yang benar pada variabel `LINK_CSV` di dalam kode Python.")
    st.error(f"Pesan Error Detail: {e}")
