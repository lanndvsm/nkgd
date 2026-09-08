import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(
    page_title="📊 Trading Journal",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# GOOGLE SHEET AUTHENTICATION & DATA
# ============================================

@st.cache_resource
def authenticate_gspread():
    """Xác thực với Google Sheets"""
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        st.secrets["gcp_service_account"], scope
    )
    return gspread.authorize(creds)

def get_google_sheet():
    """Lấy worksheet từ Google Sheet"""
    gc = authenticate_gspread()
    sheet = gc.open("Trading_Journal_Cloud").sheet1
    return sheet

def load_data():
    """Tải dữ liệu từ Google Sheet"""
    try:
        sheet = get_google_sheet()
        records = sheet.get_all_records()
        if not records:
            return pd.DataFrame()
        
        df = pd.DataFrame(records)
        
        # Chuyển đổi kiểu dữ liệu
        df['Ngày'] = pd.to_datetime(df['Ngày'], errors='coerce')
        df['Giá vào'] = pd.to_numeric(df['Giá vào'], errors='coerce')
        df['Giá ra'] = pd.to_numeric(df['Giá ra'], errors='coerce')
        df['Số lượng'] = pd.to_numeric(df['Số lượng'], errors='coerce')
        df['pl'] = pd.to_numeric(df['pl'], errors='coerce')
        
        # Tính PL tự động nếu là 0 hoặc NaN
        df['pl'] = df.apply(
            lambda row: (row['Giá ra'] - row['Giá vào']) * row['Số lượng'] 
            if pd.isna(row['pl']) or row['pl'] == 0 else row['pl'],
            axis=1
        )
        
        return df.sort_values('Ngày', ascending=False).reset_index(drop=True)
    except Exception as e:
        st.error(f"❌ Lỗi tải dữ liệu: {str(e)}")
        return pd.DataFrame()

def add_trade(trade_data):
    """Thêm giao dịch mới vào Google Sheet"""
    try:
        sheet = get_google_sheet()
        row = [
            trade_data['Ngày'],
            trade_data['Mã tài sản'],
            trade_data['Vị thế'],
            str(trade_data['Giá vào']),
            str(trade_data['Giá ra']),
            str(trade_data['Số lượng']),
            str(trade_data['pl']),
            trade_data['Ghi chú']
        ]
        sheet.append_row(row)
        return True
    except Exception as e:
        st.error(f"❌ Lỗi thêm giao dịch: {str(e)}")
        return False

# ============================================
# UI - HEADER
# ============================================

st.title("📊 Trading Journal Cloud", anchor=False)
st.markdown("---")

# Tabs chính
tab1, tab2, tab3, tab4 = st.tabs(["📝 Thêm giao dịch", "📋 Danh sách giao dịch", "📈 Thống kê", "🎯 Phân tích"])

# ============================================
# TAB 1: THÊM GIAO DỊCH
# ============================================

with tab1:
    st.subheader("📝 Ghi nhật ký giao dịch mới", anchor=False)
    
    col1, col2 = st.columns(2)
    
    with col1:
        ngay = st.date_input("📅 Ngày giao dịch", value=datetime.now())
        ma_tai_san = st.text_input("🏷️ Mã tài sản (VD: AAPL, EURUSD)")
        vi_the = st.selectbox("📌 Vị thế", ["Long", "Short"])
        gia_vao = st.number_input("💰 Giá vào", min_value=0.0, step=0.01)
    
    with col2:
        gia_ra = st.number_input("💰 Giá ra", min_value=0.0, step=0.01)
        so_luong = st.number_input("📦 Số lượng", min_value=0.0, step=0.1)
        ghi_chu = st.text_area("📝 Ghi chú")
    
    # Tính toán PL tự động
    pl_auto = (gia_ra - gia_vao) * so_luong if so_luong > 0 else 0
    
    st.info(f"💡 **Lãi/Lỗ dự kiến:** {pl_auto:,.2f}")
    
    if st.button("✅ Lưu giao dịch", use_container_width=True, type="primary"):
        if not ma_tai_san or so_luong == 0:
            st.error("❌ Vui lòng điền đầy đủ thông tin!")
        else:
            trade = {
                'Ngày': ngay.strftime("%d/%m/%Y"),
                'Mã tài sản': ma_tai_san.upper(),
                'Vị thế': vi_the,
                'Giá vào': gia_vao,
                'Giá ra': gia_ra,
                'Số lượng': so_luong,
                'pl': pl_auto,
                'Ghi chú': ghi_chu
            }
            
            if add_trade(trade):
                st.success("✅ Giao dịch đã được lưu!")
                st.cache_resource.clear()  # Xóa cache để load dữ liệu mới
            else:
                st.error("❌ Lỗi khi lưu giao dịch!")

# ============================================
# TAB 2: DANH SÁCH GIAO DỊCH
# ============================================

with tab2:
    st.subheader("📋 Danh sách giao dịch", anchor=False)
    
    df = load_data()
    
    if df.empty:
        st.warning("📭 Chưa có giao dịch nào. Hãy thêm giao dịch mới!")
    else:
        # Bộ lọc
        col1, col2, col3 = st.columns(3)
        
        with col1:
            filter_asset = st.multiselect(
                "🏷️ Lọc mã tài sản",
                options=df['Mã tài sản'].unique(),
                default=df['Mã tài sản'].unique()
            )
        
        with col2:
            filter_position = st.multiselect(
                "📌 Lọc vị thế",
                options=["Long", "Short"],
                default=["Long", "Short"]
            )
        
        with col3:
            filter_pl = st.radio(
                "💰 Lọc P&L",
                ["Tất cả", "Lãi", "Lỗ"],
                horizontal=True
            )
        
        # Áp dụng bộ lọc
        df_filtered = df[
            (df['Mã tài sản'].isin(filter_asset)) &
            (df['Vị thế'].isin(filter_position))
        ]
        
        if filter_pl == "Lãi":
            df_filtered = df_filtered[df_filtered['pl'] > 0]
        elif filter_pl == "Lỗ":
            df_filtered = df_filtered[df_filtered['pl'] < 0]
        
        # Hiển thị bảng
        st.dataframe(
            df_filtered[[
                'Ngày', 'Mã tài sản', 'Vị thế', 'Giá vào', 
                'Giá ra', 'Số lượng', 'pl', 'Ghi chú'
            ]].sort_values('Ngày', ascending=False),
            use_container_width=True,
            hide_index=True
        )

# ============================================
# TAB 3: THỐNG KÊ
# ============================================

with tab3:
    st.subheader("📈 Thống kê chi tiết", anchor=False)
    
    df = load_data()
    
    if df.empty:
        st.warning("📭 Chưa có dữ liệu để thống kê!")
    else:
        df_valid = df[df['pl'].notna()]
        
        if len(df_valid) > 0:
            # Metrics
            col1, col2, col3, col4 = st.columns(4)
            
            total_pl = df_valid['pl'].sum()
            win_count = len(df_valid[df_valid['pl'] > 0])
            loss_count = len(df_valid[df_valid['pl'] < 0])
            win_rate = (win_count / len(df_valid) * 100) if len(df_valid) > 0 else 0
            
            with col1:
                st.metric(
                    "💰 Tổng P&L",
                    f"{total_pl:,.2f}",
                    delta="📈" if total_pl > 0 else "📉"
                )
            
            with col2:
                st.metric("🎯 Win Rate", f"{win_rate:.1f}%")
            
            with col3:
                st.metric("✅ Giao dịch lãi", win_count)
            
            with col4:
                st.metric("❌ Giao dịch lỗ", loss_count)
            
            st.markdown("---")
            
            # Biểu đồ
            col1, col2 = st.columns(2)
            
            # Biểu đồ P&L tích lũy
            with col1:
                df_sorted = df_valid.sort_values('Ngày')
                df_sorted['Cum_PL'] = df_sorted['pl'].cumsum()
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=df_sorted['Ngày'],
                    y=df_sorted['Cum_PL'],
                    mode='lines+markers',
                    name='P&L tích lũy',
                    line=dict(color='#1f77b4', width=2),
                    fill='tozeroy'
                ))
                fig.update_layout(
                    title="📈 P&L Tích Lũy",
                    xaxis_title="Ngày",
                    yaxis_title="P&L",
                    hovermode='x unified',
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Biểu đồ Win/Loss
            with col2:
                win_loss_data = pd.DataFrame({
                    'Loại': ['Lãi 📈', 'Lỗ 📉'],
                    'Số lượng': [win_count, loss_count],
                    'Màu': ['#2ecc71', '#e74c3c']
                })
                
                fig = px.pie(
                    win_loss_data,
                    values='Số lượng',
                    names='Loại',
                    title="🎯 Tỷ lệ Lãi/Lỗ",
                    height=400,
                    color='Loại',
                    color_discrete_map={'Lãi 📈': '#2ecc71', 'Lỗ 📉': '#e74c3c'}
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # P&L theo mã tài sản
            st.markdown("---")
            st.subheader("💰 P&L theo mã tài sản", anchor=False)
            
            pl_by_asset = df_valid.groupby('Mã tài sản')['pl'].sum().sort_values(ascending=False)
            
            fig = px.bar(
                x=pl_by_asset.index,
                y=pl_by_asset.values,
                title="P&L theo mã tài sản",
                labels={'x': 'Mã tài sản', 'y': 'P&L'},
                height=400,
                color=pl_by_asset.values,
                color_continuous_scale='RdYlGn'
            )
            st.plotly_chart(fig, use_container_width=True)

# ============================================
# TAB 4: PHÂN TÍCH
# ============================================

with tab4:
    st.subheader("🎯 Phân tích chi tiết", anchor=False)
    
    df = load_data()
    
    if df.empty:
        st.warning("📭 Chưa có dữ liệu để phân tích!")
    else:
        df_valid = df[df['pl'].notna()]
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Top trades lãi nhất
            st.subheader("🏆 Top giao dịch lãi", anchor=False)
            top_wins = df_valid.nlargest(5, 'pl')[['Ngày', 'Mã tài sản', 'Vị thế', 'pl']]
            st.dataframe(top_wins, use_container_width=True, hide_index=True)
        
        with col2:
            # Top trades lỗ nhất
            st.subheader("⚠️ Top giao dịch lỗ", anchor=False)
            top_losses = df_valid.nsmallest(5, 'pl')[['Ngày', 'Mã tài sản', 'Vị thế', 'pl']]
            st.dataframe(top_losses, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        
        # Thống kê Long/Short
        col1, col2 = st.columns(2)
        
        with col1:
            long_trades = df_valid[df_valid['Vị thế'] == 'Long']
            short_trades = df_valid[df_valid['Vị thế'] == 'Short']
            
            st.metric("📊 Long P&L", f"{long_trades['pl'].sum():,.2f}")
            st.metric("📊 Long Win Rate", f"{(len(long_trades[long_trades['pl'] > 0]) / len(long_trades) * 100):.1f}%" if len(long_trades) > 0 else "N/A")
        
        with col2:
            st.metric("📊 Short P&L", f"{short_trades['pl'].sum():,.2f}")
            st.metric("📊 Short Win Rate", f"{(len(short_trades[short_trades['pl'] > 0]) / len(short_trades) * 100):.1f}%" if len(short_trades) > 0 else "N/A")

st.markdown("---")
st.caption("💡 **Mẹo:** Cột PL được tính tự động từ (Giá ra - Giá vào) × Số lượng")

