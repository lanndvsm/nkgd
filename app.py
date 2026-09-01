import streamlit as st
import pandas as pd
import plotly.express as px
from database import DatabaseManager # Import lớp ta vừa viết ở Gđ 2

# Khởi tạo database
db = DatabaseManager()

st.set_page_config(page_title="Trading Journal", layout="wide")
st.title("📈 Hệ Thống Nhật Ký Giao Dịch Chuyên Nghiệp")

# --- SIDEBAR: NHẬP LIỆU ---
st.sidebar.header("➕ Thêm Lệnh Mới")
with st.sidebar.form("trade_form", clear_on_submit=True):
    date = st.date_input("Ngày")
    asset = st.text_input("Mã tài sản (VD: BTC/USDT)")
    side = st.selectbox("Vị thế", ["Buy", "Sell"])
    entry = st.number_input("Giá vào", format="%.4f")
    exit_p = st.number_input("Giá ra", format="%.4f")
    qty = st.number_input("Số lượng", format="%.4f")
    notes = st.text_area("Ghi chú/Bài học")
    submit = st.form_submit_button("Lưu Giao Dịch")

    if submit:
        # Tính P/L tự động
        pl = (exit_p - entry) * qty if side == "Buy" else (entry - exit_p) * qty
        db.add_trade(str(date), asset, side, entry, exit_p, qty, pl, notes)
        st.sidebar.success("Đã lưu vào SQLite!")

# --- MAIN PAGE: DASHBOARD ---
df = db.get_all_trades()

if not df.empty:
    # 1. Chỉ số tổng quát
    stats = db.get_stats()
    total_pl = stats['total_pl'][0] or 0
    
    c1, c2 = st.columns(2)
    c1.metric("Tổng Lợi Nhuận", f"${total_pl:,.2f}")
    c2.metric("Tổng số lệnh", len(df))

    # 2. Biểu đồ tăng trưởng
    st.subheader("Đường cong lợi nhuận (Equity Curve)")
    df['Cum_PL'] = df['pl'].iloc[::-1].cumsum().iloc[::-1] # Tính tổng tích lũy
    fig = px.line(df, x=df.index, y='Cum_PL', title="Sự tăng trưởng tài khoản")
    st.plotly_chart(fig, use_container_width=True)

    # 3. Bảng chi tiết
    st.subheader("📜 Lịch sử giao dịch")
    st.dataframe(df, use_container_width=True)
else:
    st.info("Hãy nhập giao dịch đầu tiên ở cột bên trái!")
