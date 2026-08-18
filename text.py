import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go  # Thêm thư viện này để vẽ biểu đồ Combo
import os
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import streamlit.components.v1 as components
import math

# ==============================================================================
# 1. CẤU HÌNH & CSS (GIAO DIỆN)
# ==============================================================================
st.set_page_config(
    page_title="Dashboard BHYT",
    layout="wide",
    page_icon="🏥",
    initial_sidebar_state="collapsed"
)
st.markdown("""
    <style>
    .login-card {
        background-color: #ffffff;
        padding: 30px 40px;
        border-radius: 15px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.08);
        border: 1px solid #e2e8f0;
    }
    </style>
""", unsafe_allow_html=True)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; color: #1e293b; }
    .stApp { background-color: #f8fafc; }
    div[data-testid="stMetric"] { background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); text-align: center; }
    .dashboard-title { font-size: 32px; font-weight: 800; color: #0f172a; margin-bottom: 5px; }
    .custom-table { width: 100%; border-collapse: collapse; font-size: 13px; }
    .custom-table th { background-color: #d1e7dd !important; color: #0f5132 !important; padding: 12px !important; border: 1px solid #e2e8f0; }
    .custom-table td { text-align: center !important; padding: 10px !important; border: 1px solid #e2e8f0; }
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        color: #1e293b;
    }
    .stApp { background-color: #f8fafc; }

    /* Card KPI */
    div[data-testid="stMetric"] {
        background-color: #ffffff;  
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        text-align: center;
    }
    div[data-testid="stMetricLabel"] { color: #64748b; font-weight: 600; font-size: 14px; }
    div[data-testid="stMetricValue"] { color: #0f172a; font-weight: 800; font-size: 32px; }

    /* Chỉnh màu Sticker */
    div[data-testid="stMetricDelta"] { font-weight: 600; font-size: 13px; }

    /* Tiêu đề bên trong Tab */
    .dashboard-title { font-size: 32px; font-weight: 800; color: #0f172a; margin-bottom: 5px; letter-spacing: -0.5px; }
    .dashboard-subtitle { font-size: 15px; color: #64748b; margin-bottom: 30px; }
    .chart-header { font-weight: 700; font-size: 18px; color: #334155; margin-bottom: 15px; text-align: center; }

    /* Cảnh báo lỗi */
    .alert-box {
        background-color: #FEF2F2;
        border-left: 5px solid #EF4444;
        color: #991B1B;
        padding: 15px 20px;
        border-radius: 8px;
        font-weight: 600;
        margin-top: 20px;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
    }

    /* Style cho đoạn văn báo cáo */
    .report-text {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        padding: 15px;
        border-radius: 6px;
        color: #334155;
        font-size: 15px;
        line-height: 1.6;
        margin-top: 10px;
    }

    /* Tab lớn (Cấp 1) */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        height: 60px;
        white-space: pre-wrap;
        background-color: #f1f5f9;
        border-radius: 8px 8px 0 0;
        padding: 10px 20px;
        font-weight: 700 !important;
        font-size: 18px !important;
        color: #64748b;
    }
    .stTabs [aria-selected="true"] {
        background-color: #ffffff !important;
        color: #0f172a !important;
        border-top: 3px solid #3b82f6;
    }

    /* --- CSS CHO BẢNG HTML TÙY CHỈNH --- */
    .custom-table {
        width: 100%;
        border-collapse: collapse;
        margin-bottom: 1rem;
        font-family: 'Inter', sans-serif;
        font-size: 13px;
    }
    .custom-table th {
        background-color: #d1e7dd !important;
        color: #0f5132 !important;
        font-weight: bold !important;
        text-align: center !important;
        padding: 12px !important;
        border: 1px solid #e2e8f0;
    }
    .custom-table td {
        text-align: center !important;
        padding: 10px !important;
        border: 1px solid #e2e8f0;
        vertical-align: middle;
    }
    /* Dòng cuối (Tổng cộng) nếu có sẽ style riêng trong code Python nếu cần, hoặc dùng class */
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 1.1. CẤU HÌNH DATABASE & XÁC THỰC
# ==============================================================================
DB_FILE = "data.db"


def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Tạo bảng và tài khoản admin mặc định nếu chưa có"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    """)
    conn.commit()

    # Kiểm tra xem đã có tài khoản admin chưa, nếu chưa thì tạo mặc định
    cursor.execute("SELECT * FROM users WHERE username = 'Myntk'")
    if not cursor.fetchone():
        hashed_pw = generate_password_hash("KM220902@")  # Mật khẩu mặc định
        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                       ("Myntk", hashed_pw, "Myntk"))
        conn.commit()
    conn.close()


def verify_user(username, password):
    """Xác thực tài khoản và mật khẩu"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    if user and check_password_hash(user['password'], password):
        return {"username": user['username'], "role": user['role']}
    return None


def add_new_user(username, password, role):
    """Admin thêm tài khoản mới"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        hashed_pw = generate_password_hash(password)
        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                       (username, hashed_pw, role))
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        success = False  # Trùng tên đăng nhập
    conn.close()
    return success


def get_all_users():
    """Lấy danh sách tài khoản hiện tại"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, role FROM users")
    users = cursor.fetchall()
    conn.close()
    return users


# Khởi tạo Database khi chạy app
init_db()
# ==============================================================================
# 2. XỬ LÝ DỮ LIỆU
# ==============================================================================

@st.cache_data
def process_dataframe(df):
    try:
        # Bỏ các dòng trống toàn bộ
        df.dropna(how='all', inplace=True)

        # Chuẩn hóa tên cột thành chữ hoa, dạng chuỗi
        df.columns = [str(c).strip().upper() for c in df.columns]

        cols = {
            'danh_gia': None, 'phan_loc': None, 'noi_dung': None,
            'ngay_ra': None, 'ma_loaikcb': None,
            'raw_tongchi_gbv': None, 'raw_tongchi_bh': None,
            'raw_bncct': None, 'raw_bhtt': None, 'raw_bntt': None
        }

        # Ép toàn bộ dataframe sang string an toàn để tránh lỗi float found
        df_str = df.astype(str)

        for col in df.columns:
            # Ép chắc chắn danh sách các phần tử sang chuỗi trước khi join
            sample = " ".join([str(x) for x in df_str[col].head(50).tolist()]).lower()
            c_name = str(col).lower().strip()

            # Nhận diện cột đánh giá / kết quả giám định linh hoạt
            if not cols['danh_gia'] and (
                    "đủ điều kiện" in sample or "thanh toán" in sample or "trang_thai" in c_name or "giam_dinh" in c_name or "ket_qua" in c_name):
                cols['danh_gia'] = col
            if not cols['phan_loc']:
                if "phân lọc" in c_name or "phan_loc" in c_name or "ma_loai_rv" in c_name:
                    cols['phan_loc'] = col
            if not cols['noi_dung'] and ("nội dung" in c_name or "ghi chú" in c_name or "lỗi" in c_name):
                cols['noi_dung'] = col
            if not cols['ngay_ra'] and ("ngay_ra" in c_name or "ngày ra" in c_name):
                cols['ngay_ra'] = col
            if not cols['ma_loaikcb'] and ("ma_loaikcb" in c_name or "mã loại kcb" in c_name):
                cols['ma_loaikcb'] = col
            if not cols['raw_tongchi_gbv'] and c_name in ['t_tongchi_bv', 't_tong_chi_gbv', 't_tongchi_gbv',
                                                          'thanh_tien', 't_tongchi']:
                cols['raw_tongchi_gbv'] = col
            if not cols['raw_tongchi_bh'] and c_name in ['t_tongchi_bh', 't_tong_chi_bh']:
                cols['raw_tongchi_bh'] = col
            if not cols['raw_bncct'] and c_name in ['t_bncct']:
                cols['raw_bncct'] = col
            if not cols['raw_bhtt'] and c_name in ['t_bhtt']:
                cols['raw_bhtt'] = col
            if not cols['raw_bntt'] and c_name in ['t_bntt']:
                cols['raw_bntt'] = col

        # Fallback an toàn tìm kiếm cột đánh giá
        if not cols['danh_gia']:
            for col in df.columns:
                col_text = " ".join([str(x) for x in df[col].dropna().tolist()]).lower()
                if "đủ điều kiện" in col_text:
                    cols['danh_gia'] = col
                    break

        if not cols['danh_gia']:
            df['TRANG_THAI_CUOI'] = "Đủ điều kiện thanh toán"
        else:
            def danh_gia_ho_so(val):
                val_str = str(val).lower()
                if "không đủ điều kiện" in val_str:
                    return "Không đủ điều kiện thanh toán"
                elif "đủ điều kiện" in val_str:
                    return "Đủ điều kiện thanh toán"
                else:
                    return "Đủ điều kiện thanh toán"

            df['TRANG_THAI_CUOI'] = df[cols['danh_gia']].apply(danh_gia_ho_so)

        # Xử lý phân loại KCB
        if cols['phan_loc']:
            def chuan_hoa_loai(val):
                val_str = str(val).lower().strip()
                if val_str in ['1', 'khám bệnh', 'ra viện']: return "Khám bệnh/Ra viện"
                if val_str in ['2', 'chuyển viện']: return "Chuyển viện"
                if val_str in ['3', 'trốn viện']: return "Trốn viện"
                if val_str in ['5', 'tử vong']: return "Tử vong"
                if "trốn" in val_str: return "Trốn viện"
                if "chuyển" in val_str: return "Chuyển viện"
                if "tử vong" in val_str: return "Tử vong"
                return "Khám bệnh/Ra viện"

            df['LOAI_CHUNG_TU_GOP'] = df[cols['phan_loc']].apply(chuan_hoa_loai)
        else:
            df['LOAI_CHUNG_TU_GOP'] = "Khám bệnh/Ra viện"

        # Xử lý Ngày ra
        if cols['ngay_ra']:
            def parse_date_custom(val):
                s = str(val).strip()
                if s.isdigit() and len(s) >= 8:
                    return pd.to_datetime(s[:8], format='%Y%m%d', errors='coerce')
                return pd.to_datetime(val, errors='coerce')

            df['NGAY_RA_FMT'] = df[cols['ngay_ra']].apply(parse_date_custom)

        # Xử lý cột tiền
        money_mapping = {
            'T_TONG CHI_GBV': cols['raw_tongchi_gbv'],
            'T_TONG CHI_BH': cols['raw_tongchi_bh'],
            'T_BNCCT': cols['raw_bncct'],
            'T_BHTT': cols['raw_bhtt'],
            'T_BNTT': cols['raw_bntt']
        }
        for std_name, raw_col in money_mapping.items():
            if raw_col and raw_col in df.columns:
                df[std_name] = pd.to_numeric(df[raw_col], errors='coerce').fillna(0)
            else:
                df[std_name] = 0
        df['TONG_CHI_PHI'] = df['T_TONG CHI_GBV']

        # Xử lý Mã loại KCB
        if cols['ma_loaikcb'] and cols['ma_loaikcb'] in df.columns:
            def format_ma_kcb(val):
                s = str(val).strip()
                if not s or s.lower() == 'nan': return "01"
                if s.endswith('.0'): s = s[:-2]
                if s.isdigit(): return f"{int(s):02d}"
                return s

            df['MA_LOAIKCB_CLEAN'] = df[cols['ma_loaikcb']].apply(format_ma_kcb)
        else:
            df['MA_LOAIKCB_CLEAN'] = "01"

        return df, cols

    except Exception as e:
        return None, f"Lỗi xử lý dữ liệu: {str(e)}"
def render_html_table(df):
    html = df.to_html(index=False, classes='custom-table', border=0)
    st.markdown(html, unsafe_allow_html=True)

# NẠP DỮ LIỆU TỰ ĐỘNG (THAY THẾ UPLOADER)
# ==============================================================================
st.sidebar.markdown("### 🔐 Hệ thống Đăng nhập")

# Khởi tạo giá trị mặc định cho user nếu chưa tồn tại trong session
if st.session_state.get('user') is None:
    # Chia cột căn giữa
    col1, col2, col3 = st.columns([1, 1.2, 1])

    with col2:
        # Tạo khoảng cách đẩy form xuống giữa trang
        st.markdown("<div style='height: 10vh;'></div>", unsafe_allow_html=True)

        # Dùng container chuẩn có sẵn border của Streamlit (vừa khít, không lỗi khung trắng)
        with st.container(border=True):
            st.markdown("<h3 style='text-align: center; color: #1e293b;'>🏥 ĐĂNG NHẬP HỆ THỐNG</h3>",
                        unsafe_allow_html=True)
            st.write("")  # Tạo khoảng cách nhỏ

            with st.form("login_form"):
                username_input = st.text_input("👤 Tên đăng nhập")
                password_input = st.text_input("🔑 Mật khẩu", type="password")

                submit_login = st.form_submit_button("Đăng nhập", use_container_width=True)

                if submit_login:
                    user_info = verify_user(username_input, password_input)
                    if user_info:
                        st.session_state['user'] = user_info
                        st.rerun()
                    else:
                        st.error("❌ Sai tên đăng nhập hoặc mật khẩu!")

    st.stop()
else:
    # Khi đã đăng nhập thành công, hiển thị thông tin ở sidebar kèm nút Đăng xuất
    current_user = st.session_state.get('user')
    if current_user:
        st.sidebar.write(f"👤 Xin chào: **{current_user.get('username')}** ({current_user.get('role')})")
        if st.sidebar.button("Đăng xuất"):
            st.session_state['user'] = None
            st.rerun()
with st.sidebar.expander("⚙️ Cấu hình file & Chọn Sheet", expanded=False):
    uploaded_file = st.file_uploader("Tải lên file Excel tùy chọn", type=['xlsx', 'xls', 'csv'])

    df = None
    info = None
    excel_file_to_read = None

    # Đường dẫn file mặc định của bạn
    DEFAULT_FILENAME = "95078 DLBD 79A HD_Kieu My.xlsx"

st.sidebar.markdown("### ⚙️ Nhập dữ liệu")
uploaded_file = st.sidebar.file_uploader("Tải lên file Excel (Tùy chọn)", type=['xlsx', 'xls', 'csv'])

df = None
excel_file_to_read = None

# 2. Kiểm tra nguồn file (Ưu tiên file user tải lên, nếu không có thì lấy file cố định trên GitHub)
if uploaded_file is not None:
    excel_file_to_read = uploaded_file
    st.success("✅ Đang dùng file tải lên.")
else:
    import glob
    found_files = glob.glob("*.xlsx")
    if found_files:
        excel_file_to_read = found_files[0]
        st.info(f"📂 Đang dùng file cố định: {excel_file_to_read}")
    else:
        st.error("❌ Không tìm thấy file Excel nào trong thư mục!")
        st.stop()

# 3. Đọc dữ liệu vào DataFrame
try:
    # Tự động lấy tên sheet đầu tiên trong file nếu chưa có biến selected_sheet
    xl = pd.ExcelFile(excel_file_to_read)
    sheet_names = xl.sheet_names
    
    # Nếu chưa cóselectbox chọn sheet ở phía trên, ta mặc định lấy sheet đầu tiên hoặc dùng biến có sẵn
    sheet_to_use = selected_sheet if 'selected_sheet' in locals() else sheet_names[0]
    
    df = pd.read_excel(excel_file_to_read, sheet_name=sheet_to_use)
    st.success(f"Đã tải thành công {len(df):,} dòng dữ liệu từ sheet '{sheet_to_use}'!")
except Exception as e:
    st.error(f"Lỗi đọc dữ liệu: {e}")
    st.stop()

# ==========================================
# 4. GIAO DIỆN CHÍNH (Các bảng, biểu đồ, bộ lọc của bạn tiếp tục ở đây)
# ==========================================
# 1. TRƯỜNG HỢP: Người dùng đã tải file lên
if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith(('.xlsx', '.xls')):
            df_raw = pd.read_excel(uploaded_file)
        else:
            df_raw = pd.read_csv(uploaded_file)
        df, info = process_dataframe(df_raw)
        st.sidebar.success("✅ Đang dùng file đã tải lên.")
    except Exception as e:
        st.error(f"Lỗi file tải lên: {e}")

# 2. TRƯỜNG HỢP: Chưa tải file, tự động lấy file từ đường dẫn cố định
# ==============================================================================
# 4. TAB CẤP 1 (NAVIGATION BAR)
# ==============================================================================
tab_ks, tab_dt = st.tabs(["KIỂM SOÁT HỒ SƠ BHYT NGOẠI TRÚ", "DOANH THU KCB NGOẠI TRÚ"])

# ==============================================================================
# TAB 1: KIỂM SOÁT
# ==============================================================================
with tab_ks:
    st.markdown('<div class="dashboard-title">KIỂM SOÁT HỒ SƠ BHYT NGOẠI TRÚ</div>', unsafe_allow_html=True)

    # Thêm đoạn kiểm tra này để chặn đứng lỗi nếu df hoặc info bị None
    if df is None or df.empty:
        st.warning("⚠️ Dữ liệu đang trống hoặc không đọc được cấu trúc file. Vui lòng kiểm tra lại file Excel.")
        st.stop()

    cols = info

    # Tính toán số liệu an toàn
    df_dat = df[
        df['TRANG_THAI_CUOI'] == "Đủ điều kiện thanh toán"] if 'TRANG_THAI_CUOI' in df.columns else pd.DataFrame()
    df_chua_dat = df[
        df['TRANG_THAI_CUOI'] == "Không đủ điều kiện thanh toán"] if 'TRANG_THAI_CUOI' in df.columns else pd.DataFrame()

    st.markdown(
        f'<div class="dashboard-subtitle">Báo cáo tổng hợp tình hình giám định • Tổng số: {len(df):,} hồ sơ</div>',
        unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("TỔNG HỒ SƠ", f"{len(df):,}", delta="Dữ liệu gốc")
    with c2:
        st.metric("ĐỦ ĐIỀU KIỆN", f"{len(df_dat):,}", delta="Chấp nhận")
    with c3:
        st.metric("KHÔNG ĐỦ ĐIỀU KIỆN", f"{len(df_chua_dat):,}", delta="-Cần xử lý" if not df_chua_dat.empty else "Tốt",
                  delta_color="inverse")
    with c4:
        rate = (len(df_dat) / len(df) * 100) if len(df) > 0 else 0
        st.metric("TỶ LỆ ĐẠT", f"{rate:.1f}%", delta="Hiệu suất")

    sub_tab1, sub_tab2 = st.tabs(["📊 TỔNG QUAN & KẾT QUẢ", "📅 THỐNG KÊ THEO NGÀY"])

    with sub_tab1:
        col_chart1, col_chart2 = st.columns([1, 2])
        with col_chart1:
            st.markdown('<div class="chart-header">1. Tỷ lệ kết quả giám định</div>', unsafe_allow_html=True)
            chart_data = df['ĐÁNH GIÁ'].value_counts().reset_index()
            chart_data.columns = ['Trạng thái', 'Số lượng']

            # --- ĐOẠN ĐIỀU CHỈNH MÀU SẮC ---
            fig_pie = px.pie(chart_data, values='Số lượng', names='Trạng thái', color='Trạng thái',
                             color_discrete_map={
                                 'Đủ điều kiện thanh toán': '#205AA7',  # Xanh lá chuẩn hình
                                 'Không đủ điều kiện thanh toán': '#ff3333',  # Đỏ chuẩn hình
                                 'Chưa xác định': '#cbd5e1'  # Xám nhạt
                             },
                             hole=0.6)
            # -------------------------------

            fig_pie.update_layout(showlegend=True, legend=dict(orientation="h", y=-0.2),
                                  margin=dict(t=0, b=0, l=0, r=0))
            st.plotly_chart(fig_pie, use_container_width=True)

        with col_chart2:
            st.markdown('<div class="chart-header">2. Thống kê theo loại hình KCB</div>', unsafe_allow_html=True)
            pl_stats = df['LOAI_CHUNG_TU_GOP'].value_counts().reset_index()
            pl_stats.columns = ['Phân loại', 'Số lượng']

            # --- ĐOẠN ĐIỀU CHỈNH MÀU SẮC ---
            fig_bar = px.bar(pl_stats, x='Số lượng', y='Phân loại', orientation='h', text='Số lượng',
                             color='Phân loại',
                             color_discrete_map={
                                 'Khám bệnh/Ra viện': '#205AA7',  # Xanh dương đậm
                                 'Chuyển viện': '#BFCAE6 ',  # Xanh dương nhạt
                                 'Trốn viện': '#27a4f2',  # Hồng nhạt
                                 'Tử vong': '#334155'  # Xám đậm
                             })
            # -------------------------------

            fig_bar.update_layout(xaxis_title="", yaxis_title="", showlegend=False,
                                  margin=dict(t=0, b=0, l=0, r=0),
                                  plot_bgcolor='rgba(0,0,0,0)')  # Nền trong suốt
            fig_bar.update_traces(textposition='outside')
            st.plotly_chart(fig_bar, use_container_width=True)

        if not df_chua_dat.empty:
            st.markdown(
                f'<div class="alert-box">⚠️ CẢNH BÁO: Phát hiện {len(df_chua_dat)} hồ sơ không đủ điều kiện thanh toán</div>',
                unsafe_allow_html=True)
            cols_show = ['MA_LK', 'HO_TEN', 'TRANG_THAI_CUOI', 'LOAI_CHUNG_TU_GOP']
            if cols['noi_dung']: cols_show.append(cols['noi_dung'])
            final_cols = [c for c in cols_show if c in df.columns]
            rename_map = {'TRANG_THAI_CUOI': 'TRANG THAI', 'LOAI_CHUNG_TU_GOP': 'LOAI CHUNG TU'}
            if cols['noi_dung']: rename_map[cols['noi_dung']] = 'NOI DUNG LOI'
            df_display = df_chua_dat[final_cols].copy()
            df_display.rename(columns=rename_map, inplace=True)
            col_tool1, col_tool2 = st.columns([3, 1])
            with col_tool2:
                csv = df_display.to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 Tải Xuất CSV", csv, "ds_loi_thuc_te.csv", "text/csv", use_container_width=True,
                                   type="primary")


            def highlight_status(val):
                if val == 'Không đủ điều kiện thanh toán': return 'background-color: #FEF2F2; color: #DC2626; font-weight: bold;'
                return ''


            st.dataframe(df_display.style.map(highlight_status), use_container_width=True, hide_index=True)
        else:
            st.success("✅ Tuyệt vời! Dữ liệu thực tế cho thấy không có hồ sơ nào bị lỗi.")

    # TAB CON 2: THỐNG KÊ THEO NGÀY
    with sub_tab2:
        if 'NGAY_RA_FMT' in df.columns:
            df_clean = df.dropna(subset=['NGAY_RA_FMT']).copy()
            df_clean = df_clean.sort_values('NGAY_RA_FMT')
            df_clean['Ngày ra viện'] = df_clean['NGAY_RA_FMT'].dt.strftime('%d/%m/%Y')

            if not df_clean.empty:
                # 1. SortKey chuẩn
                unique_dates = df_clean['NGAY_RA_FMT'].dt.date.unique()
                sorted_dates = sorted(unique_dates)
                sorted_date_strs = [d.strftime('%d/%m/%Y') for d in sorted_dates]

                # 2. Xử lý dữ liệu
                col_phan_tich = 'LOAI_CHUNG_TU_GOP'
                color_map = {'Trốn viện': '#F97316', 'Chuyển viện': '#EAB308', 'Khám bệnh/Ra viện': '#3B82F6',
                             'Tử vong': '#475569', 'Khác': '#94A3B8'}

                df_line = df_clean.groupby(['Ngày ra viện', col_phan_tich]).size().reset_index(name='Số lượng')
                df_line['Ngày ra viện'] = pd.Categorical(df_line['Ngày ra viện'], categories=sorted_date_strs,
                                                         ordered=True)
                df_line = df_line.sort_values('Ngày ra viện')

                df_daily = df_clean.groupby(['Ngày ra viện', col_phan_tich]).size().reset_index(name='Số lượng')
                df_daily['Ngày ra viện'] = pd.Categorical(df_daily['Ngày ra viện'], categories=sorted_date_strs,
                                                          ordered=True)
                df_daily = df_daily.sort_values('Ngày ra viện')

                pivot_daily = df_clean.pivot_table(index='Ngày ra viện', columns=col_phan_tich, aggfunc='size',
                                                   fill_value=0)
                pivot_daily = pivot_daily.reindex(sorted_date_strs, fill_value=0)
                pivot_daily.index.name = "Ngày ra viện"


                def xac_dinh_trang_thai(group_data):
                    if (group_data == 'Đủ điều kiện thanh toán').all():
                        return "Hoàn thành"
                    else:
                        return "Chưa hoàn thành"


                status_series = df_clean.groupby('Ngày ra viện')['TRANG_THAI_CUOI'].apply(xac_dinh_trang_thai)
                status_series = status_series.reindex(sorted_date_strs, fill_value="N/A")

                pivot_daily_display = pivot_daily.copy()
                status_series.name = "Trạng thái"
                pivot_daily_display = pivot_daily_display.join(status_series)
                pivot_daily_display['Tổng cộng'] = pivot_daily_display.sum(axis=1, numeric_only=True)

                st.markdown('<div class="chart-header">📈 Xu hướng biến động số lượng hồ sơ theo ngày</div>',
                            unsafe_allow_html=True)

                fig_line = px.line(df_line, x='Ngày ra viện', y='Số lượng', color=col_phan_tich, markers=True,
                                   labels={'Số lượng': 'Số hồ sơ', col_phan_tich: 'Phân loại'},
                                   color_discrete_map=color_map)
                fig_line.update_xaxes(type='category', categoryorder='array', categoryarray=sorted_date_strs,
                                      tickangle=-45)
                fig_line.update_layout(margin=dict(t=10, b=0, l=0, r=0), height=350, xaxis_title="", yaxis_title="")
                st.plotly_chart(fig_line, use_container_width=True)

                with st.expander("📝 Phân tích & Đánh giá chi tiết", expanded=True):
                    total_days = len(pivot_daily_display)
                    completed_days = len(pivot_daily_display[pivot_daily_display['Trạng thái'] == 'Hoàn thành'])
                    incomplete_days = len(pivot_daily_display[pivot_daily_display['Trạng thái'] == 'Chưa hoàn thành'])

                    if not pivot_daily_display.empty:
                        max_row = pivot_daily_display.loc[pivot_daily_display['Tổng cộng'].idxmax()]
                        max_date = max_row.name
                        max_val = max_row['Tổng cộng']
                    else:
                        max_date, max_val = "N/A", 0

                    top_category = df_clean[col_phan_tich].mode()[0] if not df_clean.empty else "N/A"
                    top_cat_count = len(df_clean[df_clean[col_phan_tich] == top_category])

                    c_a1, c_a2 = st.columns(2)
                    with c_a1:
                        st.markdown(f"""
                        **1. Tình hình hoàn thành:**
                        - Tổng số ngày thống kê: **{total_days} ngày**
                        - Số ngày hoàn thành tốt (100% đạt): <span style='color:green; font-weight:bold'>{completed_days} ngày</span>
                        - Số ngày còn tồn đọng lỗi: <span style='color:red; font-weight:bold'>{incomplete_days} ngày</span>
                        """, unsafe_allow_html=True)

                    with c_a2:
                        st.markdown(f"""
                        **2. Điểm nhấn dữ liệu:**
                        - Ngày cao điểm nhất: **{max_date}** với **{max_val:,}** hồ sơ.
                        - Nhóm hồ sơ chủ yếu: **{top_category}** ({top_cat_count:,} hồ sơ).
                        """, unsafe_allow_html=True)

                    st.markdown("---")
                    st.markdown("**3. Báo cáo biến động ngày gần nhất:**")
                    if len(pivot_daily) >= 2:
                        last_day = pivot_daily.iloc[-1]
                        prev_day = pivot_daily.iloc[-2]
                        last_date_str = pivot_daily.index[-1]
                        tang_list = []
                        giam_list = []
                        for col in last_day.index:
                            delta = last_day[col] - prev_day[col]
                            if delta > 0:
                                tang_list.append(f"{col} tăng {delta} ca")
                            elif delta < 0:
                                giam_list.append(f"{col} giảm {abs(delta)} ca")

                        text_parts = [f"Ngày **{last_date_str}**:"]
                        if tang_list: text_parts.append(f"Xu hướng **tăng**: {', '.join(tang_list)}.")
                        if giam_list: text_parts.append(f"Xu hướng **giảm**: {', '.join(giam_list)}.")
                        if not tang_list and not giam_list: text_parts.append("Các chỉ số ổn định.")
                        st.markdown(f'<div class="report-text">{" ".join(text_parts)}</div>', unsafe_allow_html=True)
                    else:
                        st.caption("Dữ liệu chưa đủ 2 ngày để thực hiện so sánh xu hướng.")

                st.markdown("---")
                col_left, col_right = st.columns([2, 1])
                with col_left:
                    st.markdown(f'<div class="chart-header">Biểu đồ số liệu chi tiết</div>', unsafe_allow_html=True)
                    max_y = df_daily['Số lượng'].max() if not df_daily.empty else 10
                    fig_daily = px.bar(df_daily, x='Ngày ra viện', y='Số lượng', color=col_phan_tich, barmode='group',
                                       text='Số lượng', color_discrete_map=color_map)
                    fig_daily.update_traces(textposition='outside', cliponaxis=False)
                    fig_daily.update_xaxes(type='category', categoryorder='array', categoryarray=sorted_date_strs,
                                           tickangle=-45)
                    fig_daily.update_layout(yaxis_range=[0, max_y * 1.15], legend=dict(orientation="h", y=1.1),
                                            margin=dict(t=50, b=0, l=0, r=0), height=450)
                    st.plotly_chart(fig_daily, use_container_width=True)

                with col_right:
                    st.markdown('<div class="chart-header">Chi tiết số liệu</div>', unsafe_allow_html=True)
                    styled_df = pivot_daily_display.style.set_properties(
                        **{'font-weight': 'bold', 'font-size': '13px', 'vertical-align': 'middle'})
                    styled_df = styled_df.set_table_styles([
                        {'selector': 'thead th',
                         'props': [('background-color', '#d1e7dd'), ('color', '#0f5132'), ('font-weight', 'bold'),
                                   ('text-align', 'center !important')]},
                        {'selector': 'tbody th', 'props': [('background-color', 'white'), ('text-align', 'center')]}
                    ])
                    styled_df = styled_df.set_properties(subset=['Trạng thái'], **{'text-align': 'center !important'})
                    st.table(styled_df)
            else:
                st.warning("Không có dữ liệu ngày hợp lệ.")
        else:
            st.warning("Không tìm thấy cột 'Ngày ra viện'.")

# ==============================================================================
# TAB 2: DOANH THU
# ==============================================================================
with tab_dt:
    st.markdown('<div class="dashboard-title">DOANH THU KCB NGOẠI TRÚ</div>', unsafe_allow_html=True)

    money_cols = ['T_TONG CHI_GBV', 'T_TONG CHI_BH', 'T_BNCCT', 'T_BHTT', 'T_BNTT']
    rename_cols = {
        'T_TONG CHI_GBV': 'Tổng chi (VNĐ)',
        'T_TONG CHI_BH': 'Tổng chi BH (VNĐ)',
        'T_BNCCT': 'BN cùng chi trả (VNĐ)',
        'T_BHTT': 'BH thanh toán (VNĐ)',
        'T_BNTT': 'BN tự trả (VNĐ)',
        'LOAI_CHUNG_TU_GOP': 'Loại hình KCB',
        'MA_LOAIKCB_CLEAN': 'Mã loại KCB'
    }

    if 'T_TONG CHI_BH' in df.columns:
        # 1. Tính toán các chỉ số dựa trên cột T_TONG CHI_BH theo yêu cầu
        total_rev = df['T_TONG CHI_BH'].sum()
        total_count = len(df)
        avg_rev = df['T_TONG CHI_BH'].mean()
        max_rev = df['T_TONG CHI_BH'].max()

        st.markdown(f'<div class="dashboard-subtitle">Phân tích chi phí KCB • Đơn vị: VNĐ</div>',
                    unsafe_allow_html=True)

        # Chia 4 cột chỉ số
        k1, k2, k3, k4 = st.columns(4)
        with k1:
            st.metric("TỔNG HỒ SƠ", f"{total_count:,.0f}", delta="Hồ sơ")
        with k2:
            # Sửa tên hiển thị thành TỔNG CHI PHÍ
            st.metric("TỔNG CHI PHÍ", f"{total_rev:,.0f} VNĐ", delta="Tổng chi BH")
        with k3:
            st.metric("TRUNG BÌNH/HỒ SƠ", f"{avg_rev:,.0f} VNĐ", delta="Bình quân BH")
        with k4:
            st.metric("CHI PHÍ CAO NHẤT", f"{max_rev:,.0f} VNĐ", delta="Cao nhất BH")

        st.markdown("---")
        sub_tab_dt_1, sub_tab_dt_2 = st.tabs(["📊 PHÂN TÍCH CHI PHÍ", "📅 PHÂN TÍCH ĐÁNH GIÁ"])

        with sub_tab_dt_1:
            st.markdown('<div class="chart-header">1. Thống kê theo loại hình KCB</div>', unsafe_allow_html=True)
            col_t1, col_c1 = st.columns([1, 1])
            df_group1 = df.groupby('LOAI_CHUNG_TU_GOP')[money_cols].sum().reset_index()
            sum_row1 = df_group1[money_cols].sum()
            sum_row_df1 = pd.DataFrame([['TỔNG CỘNG'] + sum_row1.tolist()], columns=['LOAI_CHUNG_TU_GOP'] + money_cols)
            df_show1 = pd.concat([df_group1, sum_row_df1], ignore_index=True)
            df_show1.rename(columns=rename_cols, inplace=True)
            money_display_cols = [rename_cols[c] for c in money_cols]
            for c in money_display_cols:
                df_show1[c] = df_show1[c].apply(lambda x: f"{x:,.0f}")

            with col_t1:
                st.write("**Bảng số liệu chi tiết:**")
                render_html_table(df_show1)
            with col_c1:
                st.write("**Biểu đồ tương ứng:**")
                df_melt1 = df_group1.melt(id_vars=['LOAI_CHUNG_TU_GOP'], value_vars=money_cols, var_name='Loại Tiền',
                                          value_name='Giá Trị')
                df_melt1['Loại Tiền'] = df_melt1['Loại Tiền'].map(rename_cols)

                # Thêm tham số text để hiển thị số liệu
                fig1 = px.bar(df_melt1, x='LOAI_CHUNG_TU_GOP', y='Giá Trị', color='Loại Tiền', barmode='group',
                              text='Giá Trị',  # Hiển thị giá trị
                              labels={'Giá Trị': 'Số tiền (VNĐ)', 'LOAI_CHUNG_TU_GOP': 'Loại hình KCB',
                                      'Loại Tiền': 'Khoản mục'})

                # Định dạng hiển thị số (viết tắt như 1.2M, 500k) và vị trí
                fig1.update_traces(texttemplate='%{text:.2s}', textposition='outside')
                fig1.update_layout(legend=dict(orientation="h", y=-0.2), margin=dict(t=50))
                st.plotly_chart(fig1, use_container_width=True)

            st.markdown("---")
            st.markdown('<div class="chart-header">2. Thống kê theo mã loại KCB</div>', unsafe_allow_html=True)
            col_t2, col_c2 = st.columns([1, 1])
            if 'MA_LOAIKCB_CLEAN' in df.columns:
                df_group2 = df.groupby('MA_LOAIKCB_CLEAN')[money_cols].sum().reset_index()
                sum_row2 = df_group2[money_cols].sum()
                sum_row_df2 = pd.DataFrame([['TỔNG CỘNG'] + sum_row2.tolist()],
                                           columns=['MA_LOAIKCB_CLEAN'] + money_cols)
                df_show2 = pd.concat([df_group2, sum_row_df2], ignore_index=True)
                df_show2.rename(columns=rename_cols, inplace=True)
                for c in money_display_cols:
                    df_show2[c] = df_show2[c].apply(lambda x: f"{x:,.0f}")
                with col_t2:
                    st.write("**Bảng số liệu chi tiết:**")
                    render_html_table(df_show2)
                with col_c2:
                    st.write("**Biểu đồ tương ứng:**")
                    df_melt2 = df_group2.melt(id_vars=['MA_LOAIKCB_CLEAN'], value_vars=money_cols, var_name='Loại Tiền',
                                              value_name='Giá Trị')
                    df_melt2['Loại Tiền'] = df_melt2['Loại Tiền'].map(rename_cols)

                    # Thêm tham số text để hiển thị số liệu
                    fig2 = px.bar(df_melt2, x='MA_LOAIKCB_CLEAN', y='Giá Trị', color='Loại Tiền', barmode='group',
                                  text='Giá Trị',  # Hiển thị giá trị
                                  labels={'Giá Trị': 'Số tiền (VNĐ)', 'MA_LOAIKCB_CLEAN': 'Mã loại KCB',
                                          'Loại Tiền': 'Khoản mục'})

                    # Định dạng hiển thị số và vị trí
                    fig2.update_traces(texttemplate='%{text:.2s}', textposition='outside')
                    fig2.update_layout(legend=dict(orientation="h", y=-0.2), margin=dict(t=50))
                    st.plotly_chart(fig2, use_container_width=True)
            else:
                st.warning("Không tìm thấy cột MA_LOAIKCB trong dữ liệu.")

        # --- SUB TAB 2: PHÂN TÍCH ĐÁNH GIÁ (MỚI) ---
        with sub_tab_dt_2:
            st.markdown('<div class="chart-header">SO SÁNH & ĐỐI CHIẾU DOANH THU (TỔNG CHI BH)</div>',
                        unsafe_allow_html=True)
            if 'NGAY_RA_FMT' in df.columns:
                # 1. BỘ LỌC
                col_f1, col_f2 = st.columns(2)
                with col_f1:
                    view_mode = st.radio("Chọn chế độ xem:", ["So sánh theo Ngày", "So sánh theo Tháng"],
                                         horizontal=True)

                df_filtered = df.copy()
                df_filtered = df_filtered.sort_values('NGAY_RA_FMT')
                df_filtered['Thang'] = df_filtered['NGAY_RA_FMT'].dt.strftime('Tháng %m/%Y')
                df_filtered['Ngay'] = df_filtered['NGAY_RA_FMT'].dt.strftime('%d/%m/%Y')

                # Filter Thời gian
                if view_mode == "So sánh theo Ngày":
                    with col_f2:
                        min_d = df['NGAY_RA_FMT'].min().date()
                        max_d = df['NGAY_RA_FMT'].max().date()
                        date_range = st.date_input("Chọn khoảng thời gian:", value=(min_d, max_d), min_value=min_d,
                                                   max_value=max_d)
                    if len(date_range) == 2:
                        start_d, end_d = date_range
                        df_filtered = df_filtered[(df_filtered['NGAY_RA_FMT'].dt.date >= start_d) & (
                                    df_filtered['NGAY_RA_FMT'].dt.date <= end_d)]
                        group_col = 'Ngay'
                        x_label = "Ngày"
                    else:
                        st.stop()
                else:  # Tháng
                    with col_f2:
                        # Fix sort thang
                        all_months_dt = sorted(df_filtered['NGAY_RA_FMT'].dt.to_period('M').unique())
                        all_months = [d.strftime('Tháng %m/%Y') for d in all_months_dt]
                        selected_months = st.multiselect("Chọn tháng để so sánh:", all_months, default=all_months)
                    if selected_months:
                        df_filtered = df_filtered[df_filtered['Thang'].isin(selected_months)]
                        group_col = 'Thang'
                        x_label = "Tháng"
                    else:
                        st.stop()

                # 2. FILTER MÃ KCB
                if 'MA_LOAIKCB_CLEAN' in df_filtered.columns:
                    all_kcb = sorted(df_filtered['MA_LOAIKCB_CLEAN'].unique().astype(str))
                    # Ưu tiên mặc định chọn các mã phổ biến
                    default_kcb = [k for k in ['01', '02', '05', '08'] if k in all_kcb]
                    if not default_kcb: default_kcb = all_kcb

                    selected_kcb = st.multiselect("Chọn Mã Loại KCB:", all_kcb, default=default_kcb)
                    if selected_kcb:
                        df_filtered = df_filtered[df_filtered['MA_LOAIKCB_CLEAN'].isin(selected_kcb)]
                    else:
                        st.warning("Vui lòng chọn ít nhất 1 Mã loại KCB.")
                        st.stop()

                # 3. XỬ LÝ & VẼ BIỂU ĐỒ COMBO
                if not df_filtered.empty:
                    # Data cho Bar (Breakdown)
                    df_bar = df_filtered.groupby([group_col, 'MA_LOAIKCB_CLEAN'])['T_TONG CHI_BH'].sum().reset_index()

                    # Data cho Line (Total)
                    df_line_total = df_filtered.groupby(group_col)['T_TONG CHI_BH'].sum().reset_index()


                    # Fix sort
                    def apply_sort(dframe, col_name):
                        if view_mode == "So sánh theo Ngày":
                            dframe['SortKey'] = pd.to_datetime(dframe[col_name], format='%d/%m/%Y', errors='coerce')
                        else:
                            clean_str = dframe[col_name].astype(str).str.replace('Tháng ', '')
                            dframe['SortKey'] = pd.to_datetime(clean_str, format='%m/%Y', errors='coerce')
                        return dframe.sort_values('SortKey').drop(columns=['SortKey'])


                    df_bar = apply_sort(df_bar, group_col)
                    df_line_total = apply_sort(df_line_total, group_col)

                    # VẼ BIỂU ĐỒ (Go)
                    fig = go.Figure()

                    # Bar traces
                    unique_codes = sorted(df_bar['MA_LOAIKCB_CLEAN'].unique())
                    for code in unique_codes:
                        d = df_bar[df_bar['MA_LOAIKCB_CLEAN'] == code]
                        fig.add_trace(go.Bar(
                            x=d[group_col], y=d['T_TONG CHI_BH'],
                            name=f"Mã {code}",
                            text=d['T_TONG CHI_BH'], textposition='auto', texttemplate='%{text:.2s}'
                        ))

                    # Line trace (Tổng)
                    fig.add_trace(go.Scatter(
                        x=df_line_total[group_col], y=df_line_total['T_TONG CHI_BH'],
                        name='Tổng chi BH (Line)',
                        mode='lines+markers',
                        line=dict(color='red', width=2),
                        yaxis='y'
                    ))

                    fig.update_layout(barmode='stack', xaxis_title=x_label, yaxis_title="Tổng chi BH (VNĐ)",
                                      bargap=0.5,
                                      legend=dict(orientation="h", y=1.1), height=500, hovermode="x unified")
                    fig.update_xaxes(type='category')

                    st.write("**Biểu đồ Cột (Chi tiết Mã KCB) kết hợp Đường (Tổng xu hướng):**")
                    st.plotly_chart(fig, use_container_width=True)
                    # --- BIỂU ĐỒ THÁC NƯỚC (WATERFALL) CẬP NHẬT ---
                    st.markdown("---")
                    st.markdown('<div class="chart-header">Biến động của chi phí KCB Ngoại trú</div>',
                                unsafe_allow_html=True)

                    if 'NGAY_RA_FMT' in df.columns:
                        # --- 1. THIẾT LẬP BỘ LỌC TÁCH BIỆT ---
                        col_wf_f1, col_wf_f2 = st.columns(2)
                        with col_wf_f1:
                            view_mode_wf = st.radio("Chế độ xem (Waterfall):", ["Ngày", "Tháng"],
                                                    key="mode_wf", horizontal=True)

                        # Chuẩn bị dữ liệu gốc cho Waterfall
                        df_wf_base = df.copy()
                        df_wf_base = df_wf_base.sort_values('NGAY_RA_FMT')
                        df_wf_base['Thang'] = df_wf_base['NGAY_RA_FMT'].dt.strftime('Tháng %m/%Y')
                        df_wf_base['Ngay'] = df_wf_base['NGAY_RA_FMT'].dt.strftime('%d/%m/%Y')

                        if view_mode_wf == "Ngày":
                            with col_wf_f2:
                                min_d_wf = df['NGAY_RA_FMT'].min().date()
                                max_d_wf = df['NGAY_RA_FMT'].max().date()
                                date_range_wf = st.date_input("Khoảng thời gian (Waterfall):",
                                                              value=(min_d_wf, max_d_wf),
                                                              key="date_wf")
                            if len(date_range_wf) == 2:
                                start_wf, end_wf = date_range_wf
                                df_wf_filtered = df_wf_base[(df_wf_base['NGAY_RA_FMT'].dt.date >= start_wf) &
                                                            (df_wf_base['NGAY_RA_FMT'].dt.date <= end_wf)]
                                group_col_wf = 'Ngay'
                            else:
                                st.stop()
                        else:
                            with col_wf_f2:
                                all_months_wf = sorted(df_wf_base['NGAY_RA_FMT'].dt.to_period('M').unique())
                                month_opts = [d.strftime('Tháng %m/%Y') for d in all_months_wf]
                                selected_months_wf = st.multiselect("Chọn tháng (Waterfall):",
                                                                    month_opts, default=month_opts, key="month_wf")
                            df_wf_filtered = df_wf_base[df_wf_base['Thang'].isin(selected_months_wf)]
                            group_col_wf = 'Thang'

                        # --- 2. XỬ LÝ DỮ LIỆU BIỂU ĐỒ ---
                        if not df_wf_filtered.empty:
                            # Group dữ liệu theo thời gian đã chọn
                            df_wf_final = df_wf_filtered.groupby(group_col_wf)['T_TONG CHI_BH'].sum().reset_index()

                            # Sắp xếp lại theo thời gian thực tế
                            if view_mode_wf == "Ngày":
                                df_wf_final['SortKey'] = pd.to_datetime(df_wf_final[group_col_wf], format='%d/%m/%Y')
                            else:
                                df_wf_final['SortKey'] = pd.to_datetime(
                                    df_wf_final[group_col_wf].str.replace('Tháng ', ''), format='%m/%Y')
                            df_wf_final = df_wf_final.sort_values('SortKey').drop(columns=['SortKey'])

                            # Tính Delta cho Waterfall
                            y_values_wf = []
                            for i in range(len(df_wf_final)):
                                if i == 0:
                                    y_values_wf.append(df_wf_final['T_TONG CHI_BH'].iloc[i])
                                else:
                                    diff = df_wf_final['T_TONG CHI_BH'].iloc[i] - df_wf_final['T_TONG CHI_BH'].iloc[
                                        i - 1]
                                    y_values_wf.append(diff)

                            # Cấu hình biểu đồ Waterfall (Chiếm 7 phần)
                            fig_wf = go.Figure(go.Waterfall(
                                name="Biến động",
                                orientation="v",
                                measure=["absolute"] + ["relative"] * (len(df_wf_final) - 1),
                                x=df_wf_final[group_col_wf],
                                y=y_values_wf,
                                text=[f"{x:,.0f}" for x in df_wf_final['T_TONG CHI_BH']],  # Hiện số tổng trên cột
                                textposition="outside",
                                connector={"line": {"width": 1, "color": "rgb(166, 166, 166)", "dash": "dot"}},
                                increasing={"marker": {"color": "#0056b3"}},  # Xanh dương đậm
                                decreasing={"marker": {"color": "#ee2d2d"}},  # Đỏ
                                totals={"marker": {"color": "#84b4c8"}}  # Xanh dương nhạt
                            ))

                            fig_wf.update_layout(
                                yaxis_title="Chi phí (VNĐ)",
                                height=550,
                                waterfallgap=0.4,
                                plot_bgcolor='white',
                                margin=dict(t=10, b=510, l=0, r=0),
                                showlegend=False,  # Ẩn legend ở biểu đồ vì đã có bảng bên cạnh
                                xaxis=dict(type='category')
                            )

                            # --- CHIA CỘT 7:3 ĐỂ HIỂN THỊ ---
                            col_left, col_right = st.columns([7, 3])

                            with col_left:
                                st.plotly_chart(fig_wf, use_container_width=True)

                            with col_right:
                                # Chuẩn bị dữ liệu cho bảng biến động
                                df_summary = df_wf_final.copy()
                                df_summary['Chênh lệch'] = df_summary['T_TONG CHI_BH'].diff().fillna(0)
                                df_summary['%'] = (df_summary['T_TONG CHI_BH'].pct_change().fillna(0) * 100)

                                st.markdown(
                                    '<div style="text-align: center; font-weight: bold; margin-bottom: 10px;">📊 Chi tiết biến động</div>',
                                    unsafe_allow_html=True)


                                # Hàm đổi màu chữ
                                def style_delta(val):
                                    color = '#ee2d2d' if val < 0 else '#0056b3' if val > 0 else '#64748b'
                                    return f'color: {color}; font-weight: bold'


                                st.dataframe(
                                    df_summary[[group_col_wf, 'Chênh lệch', '%']]
                                    .style.format({'Chênh lệch': '{:+,.0f}', '%': '{:+.1f}%'})
                                    .map(style_delta, subset=['Chênh lệch', '%']),
                                    use_container_width=True,
                                    hide_index=True,
                                    height=500
                                )

                        else:
                            st.warning("Không có dữ liệu trong khoảng thời gian đã chọn cho biểu đồ Waterfall.")
                    # -------------------------------------
                    st.markdown("---")

                    # 4. BẢNG PIVOT
                    st.write("**Bảng đối chiếu số liệu (VNĐ):**")
                    df_pivot = df_bar.pivot(index=group_col, columns='MA_LOAIKCB_CLEAN', values='T_TONG CHI_BH').fillna(
                        0)
                    df_pivot['TỔNG CỘNG'] = df_pivot.sum(axis=1)  # Thêm cột tổng

                    df_pivot_show = df_pivot.copy()

                    # Định dạng số có dấu phẩy
                    for c in df_pivot_show.columns:
                        df_pivot_show[c] = df_pivot_show[c].apply(lambda x: f"{x:,.0f}")

                    df_pivot_show = df_pivot_show.reset_index()

                    # Đổi tên cột thời gian
                    df_pivot_show.rename(columns={group_col: f"Thời gian ({x_label})"}, inplace=True)

                    # --- PHẦN THAY ĐỔI: Xóa tên index của cột để mất chữ MA_LOAIKCB_CLEAN ---
                    df_pivot_show.columns.name = None
                    # ---------------------------------------------------------------------

                    render_html_table(df_pivot_show)

                else:
                    st.warning("Không có dữ liệu trong khoảng thời gian đã chọn.")
            else:
                st.warning("Dữ liệu không có cột 'Ngày ra viện'.")
    else:
        st.warning("⚠️ Không tìm thấy đủ các cột tiền (T_TONGCHI_BV, v.v.) trong file dữ liệu.")
