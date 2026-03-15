import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# --- 1. SETTING HALAMAN ---
st.set_page_config(page_title="Dashboard Ekspansi Bisnis", page_icon="🚀", layout="wide")

# Custom CSS untuk merapikan sedikit jarak antar elemen agar tidak terpotong
st.markdown("""
    <style>
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    </style>
""", unsafe_allow_html=True)

# Header
st.title("🚀 Executive Dashboard: Analisis Ekspansi Toko")
st.markdown("Webinar: **Analisa Data dengan Python & Streamlit** | Oleh: Muhamad Nur Faqi")
st.divider()

# --- Fungsi Helper untuk Format Rupiah Ringkas ---
def format_rupiah(angka):
    if angka >= 1_000_000_000:
        return f"Rp {angka/1_000_000_000:.1f} M"
    elif angka >= 1_000_000:
        return f"Rp {angka/1_000_000:.1f} Jt"
    else:
        return f"Rp {angka:,.0f}"

# --- 2. UPLOAD & PREP DATA ---
uploaded_file = st.file_uploader("Upload Master Data Customer (.csv atau .xlsx)", type=['csv', 'xlsx'])

if uploaded_file:
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    # Generate Dummy Revenue (Khusus Demo)
    if df['REVENUE PERBULAN'].isnull().all():
        np.random.seed(42)
        df['REVENUE PERBULAN'] = np.random.randint(5000000, 150000000, size=len(df))

    # Pastikan data Latitude dan Longitude bersih (tidak ada NaN atau string kosong)
    df = df.dropna(subset=['LAT', 'LONG'])
    df['LAT'] = pd.to_numeric(df['LAT'], errors='coerce')
    df['LONG'] = pd.to_numeric(df['LONG'], errors='coerce')
    df = df.dropna(subset=['LAT', 'LONG'])

    # --- 3. SIDEBAR (SMART FILTERS) ---
    st.sidebar.header("🎯 Parameter Analisis")
    
    selected_area = st.sidebar.multiselect("Pilih Area Operasional:", df['AREA'].dropna().unique(), default=df['AREA'].dropna().unique())
    selected_channel = st.sidebar.multiselect("Pilih Tipe Channel:", df['CHANNEL'].dropna().unique(), default=df['CHANNEL'].dropna().unique())
    
    min_rev, max_rev = st.sidebar.slider(
        "Filter Rentang Revenue:",
        min_value=int(df['REVENUE PERBULAN'].min()),
        max_value=int(df['REVENUE PERBULAN'].max()),
        value=(int(df['REVENUE PERBULAN'].min()), int(df['REVENUE PERBULAN'].max())),
        step=5000000, format="Rp %d" # Format angka di slider
    )
    
    filtered_df = df[
        (df['AREA'].isin(selected_area)) & 
        (df['CHANNEL'].isin(selected_channel)) &
        (df['REVENUE PERBULAN'] >= min_rev) & 
        (df['REVENUE PERBULAN'] <= max_rev)
    ].copy() # Pakai .copy() agar tidak ada warning dari Pandas

    # Format kolom baru khusus untuk label agar rapi
    filtered_df['Revenue_Label'] = filtered_df['REVENUE PERBULAN'].apply(format_rupiah)

    # --- 4. EXECUTIVE SUMMARY (KPI) ---
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Partner Aktif", f"{len(filtered_df):,}")
    with col2:
        st.metric("Total Area (Kecamatan)", f"{filtered_df['KECAMATAN'].nunique()}")
    with col3:
        st.metric("Total Revenue Terfilter", format_rupiah(filtered_df['REVENUE PERBULAN'].sum()))
    with col4:
        st.metric("Rata-rata Revenue/Toko", format_rupiah(filtered_df['REVENUE PERBULAN'].mean()))

    st.divider()

    # --- 5. TABULASI DASHBOARD ---
    tab1, tab2, tab3 = st.tabs(["🗺️ Peta Potensi (Geospatial)", "📈 Analisis Ekspansi (Matrix)", "📊 Kinerja Wilayah"])

    # === TAB 1: PETA POTENSI YANG LEBIH INFORMATIF ===
    with tab1:
        st.subheader("Peta Persebaran Revenue (Interactive Map)")
        st.markdown("Ukuran titik menunjukkan **besar pendapatan**. Warna lebih terang menunjukkan **konsentrasi area potensial**. Arahkan kursor ke titik untuk melihat detail toko.")
        
        # Kita gabungkan Scatter (untuk presisi) dengan ukuran (untuk revenue)
        fig_map = px.scatter_mapbox(
            filtered_df, 
            lat='LAT', 
            lon='LONG', 
            color='REVENUE PERBULAN',     # Warna berdasarkan Revenue
            size='REVENUE PERBULAN',      # Ukuran lingkaran juga berdasarkan Revenue
            hover_name='NAMA TOKO',       # Judul pop-up saat di-hover
            hover_data={                  # Data yang muncul di pop-up
                'LAT': False,             # Sembunyikan kordinat (kurang penting buat bos)
                'LONG': False,
                'NAMA PIC': True,
                'CHANNEL': True,
                'KECAMATAN': True,
                'Revenue_Label': True,    # Tampilkan format rupiah ringkas
                'REVENUE PERBULAN': False # Sembunyikan format angka mentahnya
            },
            color_continuous_scale=px.colors.sequential.Plasma, # Tema warna elegan
            size_max=20,                  # Ukuran maksimal titik
            zoom=9, 
            mapbox_style="carto-darkmatter", # Background gelap agar warna Plasma menyala
            height=700                    # Perbesar tinggi peta
        )
        
        # Rapikan legend dan margin
        fig_map.update_layout(margin={"r":0,"t":40,"l":0,"b":0})
        st.plotly_chart(fig_map, use_container_width=True)

    # === TAB 2: ANALISIS EKSPANSI (KUADRAN YANG DIPERBAIKI) ===
    with tab2:
        st.subheader("Kuadran Strategi Ekspansi (Kecamatan)")
        st.markdown("Cari kecamatan di area **Kiri Atas** (Jumlah Toko Sedikit, Rata-rata Penjualan Tinggi).")
        
        agg_df = filtered_df.groupby('KECAMATAN').agg(
            Jumlah_Toko=('NAMA TOKO', 'count'),
            Avg_Revenue=('REVENUE PERBULAN', 'mean'),
            Total_Revenue=('REVENUE PERBULAN', 'sum')
        ).reset_index()

        # Format label untuk kuadran
        agg_df['Avg_Rev_Label'] = agg_df['Avg_Revenue'].apply(format_rupiah)
        agg_df['Total_Rev_Label'] = agg_df['Total_Revenue'].apply(format_rupiah)

        fig_scatter = px.scatter(
            agg_df, 
            x='Jumlah_Toko', 
            y='Avg_Revenue', 
            size='Total_Revenue', 
            color='Avg_Revenue',
            hover_name='KECAMATAN', 
            text='KECAMATAN',
            hover_data={
                'Avg_Rev_Label': True,
                'Total_Rev_Label': True,
                'Avg_Revenue': False,
                'Total_Revenue': False
            },
            labels={'Jumlah_Toko': 'Jumlah Toko (Saturasi Pasar)', 'Avg_Revenue': 'Rata-rata Revenue per Toko'},
            color_continuous_scale='Viridis', 
            height=650 # Tinggi diperbesar
        )
        
        # Perbaiki masalah teks terpotong: Atur posisi teks, margin, dan rentang sumbu otomatis
        fig_scatter.update_traces(textposition='top center', textfont_size=11)
        # Menambahkan margin 10% di sumbu Y dan X agar nama kecamatan teratas/terluar tidak kepotong batas kotak
        fig_scatter.update_layout(
            margin=dict(l=40, r=40, t=40, b=40),
            yaxis_range=[agg_df['Avg_Revenue'].min() * 0.9, agg_df['Avg_Revenue'].max() * 1.1],
            xaxis_range=[agg_df['Jumlah_Toko'].min() - 2, agg_df['Jumlah_Toko'].max() + 5]
        )
        
        avg_rev_global = agg_df['Avg_Revenue'].mean()
        avg_toko_global = agg_df['Jumlah_Toko'].mean()
        
        fig_scatter.add_hline(y=avg_rev_global, line_dash="dash", line_color="red", annotation_text="Batas Rata-rata Revenue", annotation_position="bottom right")
        fig_scatter.add_vline(x=avg_toko_global, line_dash="dash", line_color="red", annotation_text="Batas Rata-rata Toko", annotation_position="top left")
        
        st.plotly_chart(fig_scatter, use_container_width=True)

    # === TAB 3: KINERJA WILAYAH (BAR CHART RAPI) ===
    with tab3:
        st.subheader("Top 15 Kecamatan (Total Revenue)")
        
        rev_by_kec = filtered_df.groupby('KECAMATAN')['REVENUE PERBULAN'].sum().reset_index().sort_values(by='REVENUE PERBULAN', ascending=False).head(15)
        rev_by_kec['Label_Rupiah'] = rev_by_kec['REVENUE PERBULAN'].apply(format_rupiah)

        fig_bar = px.bar(
            rev_by_kec, 
            x='KECAMATAN', 
            y='REVENUE PERBULAN', 
            text='Label_Rupiah', # Gunakan format ringkas "Rp 1.5 M"
            color='REVENUE PERBULAN', 
            color_continuous_scale='Blues',
            height=500
        )
        # Atur teks agar selalu di luar batang dan rotasi label X agar tidak tumpang tindih
        fig_bar.update_traces(textposition='outside', cliponaxis=False)
        fig_bar.update_layout(xaxis_tickangle=-45, margin=dict(t=30, b=100)) # Margin bawah untuk label miring
        
        st.plotly_chart(fig_bar, use_container_width=True)

else:
    st.info("👋 Menunggu file dataset... Silakan upload file Master Data Customer untuk melihat analisis.")