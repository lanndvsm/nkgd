import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

# ==========================================
# PHẦN 1: QUẢN LÝ GOOGLE SHEETS
# ==========================================
class GoogleSheetManager:
    def __init__(self, sheet_name):
        self.sheet_name = sheet_name
        self.client = self.authenticate()
        self.sheet = self.client.open(self.sheet_name).sheet1

    def authenticate(self):
        # Lấy thông tin bảo mật từ Streamlit Secrets
        secrets = st.secrets["gcp_service_account"]
        # Chuyển dictionary từ secrets thành định dạng mà oauth2client hiểu
        info = json.loads(json.dumps(secrets)) 
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(info, scope)
        return gspread.authorize(creds)

    def load_data(self):
        """Đọc dữ liệu từ Google Sheet"""
        data = self.sheet.get_all_records()
        return pd.DataFrame(data)

    def add_trade(self, row_list):
        """Thêm một dòng mới vào Google Sheet"""
        self.sheet.append_row(row_list)

# ==========================================
# PHẦN 2: GIAO DIỆN STREAMLIT
# ==========================================
st.set_page_config(page_title="Trading Journal Cloud", layout="wide")
st.title("☁️ Trading Journal Cloud (Google Sheets)")

# Thay "Trading_Journal_Cloud" bằng tên chính xác file Sheet của bạn
try:
    db = GoogleSheetManager("Trading_Journal_Cloud")
except Exception as e:
    st.error(f"Lỗi kết nối Google Sheet: {e}")
    st.stop()

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
    submit = st.form_submit_button("Lưu lên Cloud")

    if submit:
        pl = (exit_p - entry) * qty if side == "Buy" else (entry - exit_p) * qty
        # Tạo danh sách để gửi lên Google Sheet (phải đúng thứ tự cột)
        row = [str(date), asset, side, entry, exit_p, qty, pl, notes]
        db.add_trade(row)
        st.sidebar.success("Đã đồng bộ lên Google Sheets!")

# --- MAIN PAGE: DASHBOARD ---
df = db.load_data()

if not df.empty:
    # Ép kiểu dữ liệu số vì Google Sheet trả về dạng text/object
    df['pl'] = pd.to_numeric(df['pl'])
    
    total_pl = df['pl'].sum()
    win_rate = (df['pl'] > 0).sum() / len(df) * 100
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Tổng Lợi Nhuận", f"${total_pl:,.2f}")
    c2.metric("Tỉ lệ Thắng", f"{win_rate:.2f}%")
    c3.metric("Tổng số lệnh", len(df))

    st.subheader("Đường cong lợi nhuận (Equity Curve)")
    df['Cum_PL'] = df['pl'].cumsum()
    fig = px.line(df, x=df.index, y='Cum_PL', title="Tăng trưởng tài khoản")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("📜 Lịch sử giao dịch")
    st.dataframe(df, use_container_width=True)
else:
    st.info("Hãy nhập giao dịch đầu tiên ở cột bên trái!")
