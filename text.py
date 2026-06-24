import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

# ==============================================================================
# 0. CẤU HÌNH CƠ SỞ DỮ LIỆU SQLITE & QUẢN LÝ TÀI KHOẢN
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
    cursor.execute("SELECT * FROM users WHERE username = 'admin'")
    if not cursor.fetchone():
        hashed_pw = generate_password_hash("admin123@")  # Mật khẩu mặc định
        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                       ("admin", hashed_pw, "admin"))
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


# Khởi tạo database ngay khi chạy ứng dụng
init_db()

# ==============================================================================
# 1. CẤU HÌNH GIAO DIỆN & CSS ĐỊNH DẠNG DÒNG TIÊU ĐỀ
# ==============================================================================
st.set_page_config(page_title="Hệ thống Giám định KCB BHYT", layout="wide", page_icon="🏥")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif; color: #334155; }
    .stApp { background-color: #f1f5f9; }

    /* Tiêu đề Dashboard chính */
    .app-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        padding: 24px;
        border-radius: 16px;
        text-align: center;
        margin-bottom: 28px;
        box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.15);
    }
    .app-title { font-size: 26px; font-weight: 800; color: #ffffff; letter-spacing: 0.5px; margin: 0; }
    .app-subtitle { font-size: 13px; color: #94a3b8; font-weight: 500; margin-top: 6px; }

    /* KPI Cards tổng hợp chỉ số */
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 22px 18px;
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.03);
    }
    [data-testid="stMetric"]:nth-child(1) { border-left: 6px solid #0d9488; } 
    [data-testid="stMetric"]:nth-child(2) { border-left: 6px solid #f43f5e; } 
    [data-testid="stMetric"]:nth-child(3) { border-left: 6px solid #f59e0b; } 
    [data-testid="stMetric"]:nth-child(4) { border-left: 6px solid #8b5cf6; } 

    /* Khung chứa bảng HTML có thanh cuộn dọc cố định */
    .report-table-container {
        max-height: 550px;
        overflow-y: auto;
        border: 1px solid #cbd5e1;
        border-radius: 12px;
        background-color: #ffffff;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }

    .report-table-container table {
        width: 100%;
        border-collapse: collapse;
        font-size: 13px;
    }

    .report-table-container th {
        background-color: #0d9488 !important; 
        color: #ffffff !important;            
        text-align: center !important;        
        vertical-align: middle !important;
        font-weight: 800 !important;          
        padding: 14px 10px !important;
        position: sticky;                     
        top: 0;
        z-index: 10;
        border: 1px solid #0b7a70 !important;
    }

    .report-table-container td {
        text-align: center !important;
        vertical-align: middle !important;
        padding: 12px 10px !important;
        border: 1px solid #e2e8f0 !important;
        color: #334155;
    }

    .report-table-container tr:nth-child(even) {
        background-color: #f8fafc;
    }
    </style>
""", unsafe_allow_html=True)


# ==============================================================================
# 2. LOGIC TÍNH TOÁN & PHÂN TÍCH GIÁM ĐỊNH CHI PHÍ (GIỮ NGUYÊN LOGIC CỦA BẠN)
# ==============================================================================
def perform_bh_audit(df):
    df.columns = [str(col).strip().upper() for col in df.columns]

    df = df.dropna(how='all')
    if 'MA_LK' in df.columns:
        df = df[df['MA_LK'].notna()]
        df = df[df['MA_LK'].astype(str).str.strip() != '']
        df = df[~df['MA_LK'].astype(str).str.contains('MA_LK|Tổng|Cộng', case=False, na=False)]

    if 'MA_BN' in df.columns:
        df['USER_ID_KEY'] = df['MA_BN'].astype(str).str.strip()
    else:
        df['USER_ID_KEY'] = df['HO_TEN'].astype(str) + "_" + df['NGAY_SINH'].astype(str)

    def parse_datetime_flexible(val):
        s = str(val).split('.')[0].strip()
        if s == 'nan' or not s or len(s) < 8: return None
        if len(s) == 8:
            return pd.to_datetime(s, format='%Y%m%d', errors='coerce')
        elif len(s) >= 12:
            return pd.to_datetime(s[:12], format='%Y%m%d%H%M', errors='coerce')
        else:
            return pd.to_datetime(s[:8], format='%Y%m%d', errors='coerce')

    df['DT_VAO'] = df['NGAY_VAO'].apply(parse_datetime_flexible)
    df['DT_RA'] = df['NGAY_RA'].apply(parse_datetime_flexible)
    df['DT_TU'] = df['GT_TU'].apply(parse_datetime_flexible)
    df['DT_DEN'] = df['GT_DEN'].apply(parse_datetime_flexible)

    df['DATE_VAO_STR'] = df['NGAY_VAO'].astype(str).str[:8]
    df['NGAY_VAO_DISP'] = df['DT_VAO'].dt.strftime('%d/%m/%Y %H:%M')
    df['NGAY_RA_DISP'] = df['DT_RA'].dt.strftime('%d/%m/%Y %H:%M')

    def check_date(r):
        if r['DT_VAO'] is pd.NaT or r['DT_RA'] is pd.NaT or r['DT_TU'] is pd.NaT or r['DT_DEN'] is pd.NaT:
            return "⚠️ Thiếu thông tin"
        return "✅ Trong hạn thẻ" if (r['DT_VAO'].date() >= r['DT_TU'].date() and r['DT_RA'].date() <= r[
            'DT_DEN'].date()) else "❌ Thẻ hết hạn"

    df['KIEM_TRA_HAN_THE'] = df.apply(check_date, axis=1)
    df['T_TONGCHI_BH'] = pd.to_numeric(df['T_TONGCHI_BH'], errors='coerce').fillna(0)
    df['T_BHTT'] = pd.to_numeric(df['T_BHTT'], errors='coerce').fillna(0)

    def check_benefit(r):
        ma_the = str(r['MA_THE']).strip()
        tong_chi_bh = float(r['T_TONGCHI_BH'])
        bhtt_bao_cao = float(r['T_BHTT'])
        char3 = ma_the[2] if len(ma_the) >= 3 else ""

        if tong_chi_bh <= 351000:
            bhtt_chuan = tong_chi_bh
        else:
            if char3 in ['1', '2', '5']:
                bhtt_chuan = tong_chi_bh
            elif char3 == '3':
                bhtt_chuan = tong_chi_bh * 0.95
            elif char3 == '4':
                bhtt_chuan = tong_chi_bh * 0.80
            else:
                bhtt_chuan = 0

        bhtt_chuan = round(bhtt_chuan, 0)
        status = "✅ Đúng mức hưởng" if abs(bhtt_bao_cao - bhtt_chuan) <= 2 else "❌ Sai tỷ lệ thanh toán"
        return pd.Series([bhtt_chuan, status])

    df[['BHTT_CHUAN', 'KIEM_TRA_MUC_HUONG']] = df.apply(check_benefit, axis=1)
    df['KIEM_TRA_TRUNG_HO_SO'] = "✅ Hồ sơ chuẩn"
    kcb_col = 'MA_LOAIKCB' if 'MA_LOAIKCB' in df.columns else ('MA_LOAI_RV' if 'MA_LOAI_RV' in df.columns else None)

    df_sorted = df.sort_values(by=['USER_ID_KEY', 'DT_VAO']).copy()
    duplicate_indices = set()

    for user_id, group in df_sorted.groupby('USER_ID_KEY'):
        records = group.to_dict('records')
        for i in range(len(records)):
            curr_rec = records[i]
            if curr_rec['DT_VAO'] is pd.NaT or curr_rec['DT_VAO'] is None: continue

            if kcb_col:
                raw_val = str(curr_rec.get(kcb_col, '')).strip()
                if raw_val.endswith('.0'): raw_val = raw_val[:-2]
                curr_kcb_val = raw_val.zfill(2)

                if curr_kcb_val in ['01', '1']:
                    same_day_outpatient = []
                    for r in records:
                        if r['DT_VAO'] is pd.NaT or r['DT_VAO'] is None: continue
                        r_raw = str(r.get(kcb_col, '')).strip()
                        if r_raw.endswith('.0'): r_raw = r_raw[:-2]
                        r_kcb_val = r_raw.zfill(2)

                        if r['DATE_VAO_STR'] == curr_rec['DATE_VAO_STR'] and r_kcb_val in ['01', '1']:
                            same_day_outpatient.append(r)

                    if len(same_day_outpatient) >= 2:
                        duplicate_indices.add(curr_rec['MA_LK'])
                        continue

            for j in range(len(records)):
                if i == j: continue
                other_rec = records[j]
                if other_rec['DT_VAO'] is pd.NaT or other_rec['DT_RA'] is pd.NaT: continue

                if other_rec['DT_VAO'] < curr_rec['DT_VAO'] < other_rec['DT_RA']:
                    duplicate_indices.add(curr_rec['MA_LK'])
                    break

    df.loc[df['MA_LK'].isin(duplicate_indices), 'KIEM_TRA_TRUNG_HO_SO'] = "❌ Phát hiện hồ sơ trùng"
    return df


# ==============================================================================
# 3. QUY TRÌNH XỬ LÝ ĐĂNG NHẬP & PHÂN QUYỀN GIAO DIỆN
# ==============================================================================

# Khởi tạo trạng thái đăng nhập nếu chưa tồn tại
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['username'] = ""
    st.session_state['role'] = ""

# --- TRƯỜNG HỢP CHƯA ĐĂNG NHẬP: Hiển thị form đăng nhập ---
if not st.session_state['logged_in']:
    st.markdown("<h2 style='text-align: center; color: #1e293b;'>ĐĂNG NHẬP HỆ THỐNG GIÁM ĐỊNH</h2>",
                unsafe_allow_html=True)

    col_l, col_m, col_r = st.columns([1, 2, 1])
    with col_m:
        with st.form("login_form"):
            username_input = st.text_input("Tên đăng nhập")
            password_input = st.text_input("Mật khẩu", type="password")
            submit_login = st.form_submit_button("Đăng nhập")

            if submit_login:
                user_info = verify_user(username_input, password_input)
                if user_info:
                    st.session_state['logged_in'] = True
                    st.session_state['username'] = user_info['username']
                    st.session_state['role'] = user_info['role']
                    st.rerun()
                else:
                    st.error("❌ Sai tên đăng nhập hoặc mật khẩu!")

# --- TRƯỜNG HỢP ĐÃ ĐĂNG NHẬP THÀNH CÔNG ---
else:
    # Thanh bên quản lý tài khoản và thông tin đăng nhập
    st.sidebar.image("https://upload.wikimedia.org/wikipedia/vi/1/1b/Logo_BHXH.png", width=80)
    st.sidebar.markdown(f"👤 Tài khoản: **{st.session_state['username']}** (`{st.session_state['role'].upper()}`)")

    if st.sidebar.button("🔓 Đăng xuất"):
        st.session_state['logged_in'] = False
        st.session_state['username'] = ""
        st.session_state['role'] = ""
        st.rerun()

    st.sidebar.markdown("---")

    # Kiểm tra xem người dùng chọn chức năng nào (Nếu là Admin mới hiện thanh Quản lý tài khoản)
    menu_options = ["🔍 Công cụ Giám định BHYT"]
    if st.session_state['role'] == 'admin':
        menu_options.append("⚙️ Quản lý & Cấp tài khoản")

    choice = st.sidebar.radio("CHỨC NĂNG HỆ THỐNG", menu_options)

    # --------------------------------------------------------------------------
    # CHỨC NĂNG 1: QUẢN LÝ TÀI KHOẢN (CHỈ ADMIN THẤY)
    # --------------------------------------------------------------------------
    if choice == "⚙️ Quản lý & Cấp tài khoản" and st.session_state['role'] == 'admin':
        st.markdown("### ⚙️ HỆ THỐNG QUẢN LÝ VÀ CẤP TÀI KHOẢN")

        c1, c2 = st.columns([1, 1.5])
        with c1:
            st.markdown("##### ➕ Cấp tài khoản mới")
            with st.form("create_user_form", clear_on_submit=True):
                new_user = st.text_input("Tên tài khoản mới")
                new_pass = st.text_input("Mật khẩu", type="password")
                new_role = st.selectbox("Quyền hạn", ["user", "admin"], format_func=lambda
                    x: "User thường (Chỉ xem tool)" if x == "user" else "Admin (Toàn quyền)")
                submit_create = st.form_submit_button("Tạo tài khoản")

                if submit_create:
                    if new_user.strip() == "" or new_pass.strip() == "":
                        st.warning("⚠️ Vui lòng điền đầy đủ thông tin!")
                    else:
                        success = add_new_user(new_user, new_pass, new_role)
                        if success:
                            st.success(f"✅ Đã tạo thành công tài khoản: {new_user}")
                        else:
                            st.error("❌ Tên tài khoản này đã tồn tại trên hệ thống!")
        with c2:
            st.markdown("##### 📋 Danh sách tài khoản hiện hành")
            users_list = get_all_users()
            # Chuyển đổi dữ liệu SQLite sang DataFrame để hiện bảng đẹp mắt
            df_users = pd.DataFrame([dict(u) for u in users_list])
            df_users.columns = ['ID Hệ thống', 'Tên đăng nhập', 'Quyền hạn']
            st.dataframe(df_users, use_container_width=True, hide_index=True)

    # --------------------------------------------------------------------------
    # CHỨC NĂNG 2: GIAO DIỆN TOOL GIÁM ĐỊNH CHÍNH (CẢ USER VÀ ADMIN ĐỀU DÙNG ĐƯỢC)
    # --------------------------------------------------------------------------
    elif choice == "🔍 Công cụ Giám định BHYT":
        st.sidebar.markdown("### 🏢 CỔNG TIẾP NHẬN DỮ LIỆU")
        uploaded_file = st.sidebar.file_uploader("Chọn file báo cáo chi phí (79a HD)", type=['xlsx', 'csv'])

        if uploaded_file:
            df_raw = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
            df = perform_bh_audit(df_raw)

            st.markdown("""
                <div class="app-header">
                    <div class="app-title">GIÁM ĐỊNH & KIỂM SOÁT XUẤT TOÁN BHYT</div>
                    <div class="app-subtitle">Hệ thống rà soát tự động quy trình phân phối chi phí khám chữa bệnh ngoại trú</div>
                </div>
            """, unsafe_allow_html=True)

            total_hoso = len(df)
            loi_han_the = len(df[df['KIEM_TRA_HAN_THE'] == "❌ Thẻ hết hạn"])
            loi_muc_huong = len(df[df['KIEM_TRA_MUC_HUONG'] == "❌ Sai tỷ lệ thanh toán"])
            loi_trung_hoso = len(df[df['KIEM_TRA_TRUNG_HO_SO'] == "❌ Phát hiện hồ sơ trùng"])

            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.metric("📋 TỔNG SỐ TIẾP NHẬN", f"{total_hoso:,}")
            with m2:
                st.metric("🛑 SAI THỜI HẠN THẺ", f"{loi_han_the:,}", delta=f"{loi_han_the} hồ sơ lỗi",
                          delta_color="inverse")
            with m3:
                st.metric("💸 SAI TỶ LỆ CHI TRẢ", f"{loi_muc_huong:,}", delta=f"{loi_muc_huong} hồ sơ lỗi",
                          delta_color="inverse")
            with m4:
                st.metric("🧬 HỒ SƠ TRÙNG LẶP", f"{loi_trung_hoso:,}", delta=f"{loi_trung_hoso} đợt trùng",
                          delta_color="inverse")

            tab_kiem_soat, tab_bieu_do = st.tabs(
                ["🔍 CHI TIẾT DỮ LIỆU GIÁM ĐỊNH (CHỈ HIỂN THỊ CA LỖI)", "📊 THỐNG KÊ XU HƯỚNG & BIẾN ĐỘNG"])

            is_error_mask = (df['KIEM_TRA_HAN_THE'].str.contains("❌")) | \
                            (df['KIEM_TRA_MUC_HUONG'].str.contains("❌")) | \
                            (df['KIEM_TRA_TRUNG_HO_SO'].str.contains("❌"))

            df_only_errors = df[is_error_mask].copy()

            with tab_kiem_soat:
                st.subheader(f"📋 Danh sách cảnh báo xuất toán (Tìm thấy {len(df_only_errors)} ca lỗi cần xử lý)")

                df_only_errors['NGAY_VAO'] = df_only_errors['NGAY_VAO_DISP']
                df_only_errors['NGAY_RA'] = df_only_errors['NGAY_RA_DISP']

                cols_view = [
                    'STT', 'MA_LK', 'HO_TEN', 'MA_THE', 'NGAY_VAO', 'NGAY_RA',
                    'T_TONGCHI_BH', 'T_BHTT', 'KIEM_TRA_MUC_HUONG',
                    'KIEM_TRA_TRUNG_HO_SO', 'KIEM_TRA_HAN_THE'
                ]

                if not df_only_errors.empty:
                    df_only_errors['STT'] = range(1, len(df_only_errors) + 1)

                    styled_html = df_only_errors[cols_view].style.format({
                        'T_TONGCHI_BH': '{:,.0f}',
                        'T_BHTT': '{:,.0f}'
                    }).set_properties(**{
                        'text-align': 'center',
                        'vertical-align': 'middle'
                    }).applymap(
                        lambda val: 'background-color: #fee2e2; color: #991b1b; font-weight: bold;'
                        if isinstance(val, str) and "❌" in val else ''
                    ).hide(axis='index').to_html()

                    st.markdown(f'<div class="report-table-container">{styled_html}</div>', unsafe_allow_html=True)

                    internal_cols = ['USER_ID_KEY', 'DT_VAO', 'DT_RA', 'DT_TU', 'DT_DEN', 'DATE_VAO_STR',
                                     'NGAY_VAO_DISP',
                                     'NGAY_RA_DISP', 'NGAY_VAO', 'NGAY_RA', 'BHTT_CHUAN']
                    export_df = df_only_errors.drop(columns=[c for c in internal_cols if c in df_only_errors.columns])

                    csv_data = export_df.to_csv(index=False).encode('utf-8-sig')
                    st.write("")
                    st.download_button(
                        label="📥 Xuất tệp dữ liệu ca lỗi đầy đủ cột (.CSV)",
                        data=csv_data,
                        file_name="Danh_Sach_Ho_So_Loi_BHYT.csv",
                        mime="text/csv"
                    )
                else:
                    st.success("🎉 Tệp báo cáo hoàn hảo! Không phát hiện hồ sơ dính lỗi nào trong đợt rà soát này.")

            with tab_bieu_do:
                c_left, c_right = st.columns(2)
                with c_left:
                    st.markdown("##### 📌 Tỷ trọng cơ cấu danh mục lỗi phát hiện")
                    pie_data = pd.DataFrame({
                        'Tiêu chí đánh giá': ['Hồ sơ chuẩn khớp', 'Lỗi thời hạn thẻ', 'Lỗi tỷ lệ thanh toán',
                                              'Lỗi trùng lặp hồ sơ'],
                        'Số lượng ca': [total_hoso - len(df_only_errors), loi_han_the, loi_muc_huong, loi_trung_hoso]
                    })
                    fig_pie = px.pie(pie_data, values='Số lượng ca', names='Tiêu chí đánh giá',
                                     color='Tiêu chí đánh giá',
                                     color_discrete_map={'Hồ sơ chuẩn khớp': '#0d9488', 'Lỗi thời hạn thẻ': '#f43f5e',
                                                         'Lỗi tỷ lệ thanh toán': '#f59e0b',
                                                         'Lỗi trùng lặp hồ sơ': '#8b5cf6'},
                                     hole=0.5)
                    fig_pie.update_layout(margin=dict(t=20, b=20, l=20, r=20), legend=dict(orientation="h", y=-0.1))
                    st.plotly_chart(fig_pie, use_container_width=True)

                with c_right:
                    st.markdown("##### 📌 Phân tích dòng chảy chi phí theo ngày ra viện")
                    df['NGAY_RA_STR'] = df['NGAY_RA'].astype(str).str[:8]
                    daily_rev = df.groupby('NGAY_RA_STR')['T_TONGCHI_BH'].sum().reset_index()
                    daily_rev = daily_rev.sort_values('NGAY_RA_STR')
                    daily_rev['Ngày ra viện'] = pd.to_datetime(daily_rev['NGAY_RA_STR'], format='%Y%m%d',
                                                               errors='coerce').dt.strftime('%d/%m/%Y')

                    fig_line = px.line(daily_rev, x='Ngày ra viện', y='T_TONGCHI_BH', markers=True)
                    fig_line.update_traces(line=dict(color='#0f172a', width=3))
                    fig_line.update_layout(xaxis_title="Thời gian (Ngày)", yaxis_title="Tổng chi phí (VNĐ)",
                                           margin=dict(t=20, b=20, l=20, r=20))
                    st.plotly_chart(fig_line, use_container_width=True)

        else:
            st.info(
                "👋 Chào mừng bạn đến với Hệ thống Giám định. Vui lòng tải dữ liệu báo cáo ở thanh bên trái để thực hiện rà soát.")