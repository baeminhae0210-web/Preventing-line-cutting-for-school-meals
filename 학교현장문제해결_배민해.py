import streamlit as st
import pandas as pd
import os

# 1. 페이지 및 기본 설정
st.set_page_config(page_title="스마트 급식실 패스", layout="wide")

# 학생 신고 데이터를 저장할 엑셀(CSV) 파일 생성
CSV_FILE = 'report_data.csv'
if not os.path.exists(CSV_FILE):
    df_init = pd.DataFrame(columns=['학번', '신고횟수'])
    df_init.to_csv(CSV_FILE, index=False, encoding='utf-8-sig')

# 상태 저장을 위한 세션 설정
if 'allowed_classes' not in st.session_state:
    st.session_state.allowed_classes = [1, 2, 3, 4, 5]  # 기본 입장: 1~5반
if 'siren' not in st.session_state:
    st.session_state.siren = False

# 2. 🚨 핵심 기능: 새치기 적발 시 밈(Meme) 페널티 화면 발동
if st.session_state.siren:
    # 웹페이지 배경을 빨강/검정으로 미친듯이 깜빡이게 만드는 CSS 코드
    st.markdown("""
        <style>
        .stApp {
            background-color: red;
            animation: blinker 0.2s linear infinite;
        }
        @keyframes blinker {
            50% { background-color: black; }
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown(
        "<h1 style='text-align: center; color: yellow; font-size: 100px; margin-top: 15%;'>🚨 새치기!!!!! 🚨<br>순서가 아닙니다!</h1>",
        unsafe_allow_html=True)

    # 끄기 버튼
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("경고 끄기 (교실로 돌아가세요)", use_container_width=True):
            st.session_state.siren = False
            st.rerun()
    st.stop()  # 경고 중에는 아래의 정상 화면을 그리지 않음

# 3. 정상 화면 UI (학생용 화면과 교사용 대시보드 반반 나누기)
st.title("🏫 급식실 새치기 제로: 스마트 패스")
col_student, col_teacher = st.columns(2)

# --- 왼쪽: 학생용 스캔 및 신고 ---
with col_student:
    st.subheader("📱 [학생용] 바코드 스캔 (입장)")
    st.info(f"🟢 현재 입장 가능 반: {min(st.session_state.allowed_classes)}반 ~ {max(st.session_state.allowed_classes)}반")

    student_id = st.text_input("본인의 학번 5자리 입력 (예: 30101)", max_chars=5)

    if st.button("바코드 찍기 (입장 확인)", use_container_width=True):
        if len(student_id) == 5 and student_id.isdigit():
            student_class = int(student_id[1:3])

            # 신고 3회 누적자 페널티 체크
            df = pd.read_csv(CSV_FILE, encoding='utf-8-sig')
            penalty_check = df[df['학번'] == int(student_id)]

            if not penalty_check.empty and penalty_check.iloc[0]['신고횟수'] >= 3:
                st.error(f"❌ 학번 {student_id} 학생은 신고 누적 3회 이상으로 맨 마지막 조 배정 대상입니다!")
            else:
                # 입장 가능 반인지 체크
                if student_class in st.session_state.allowed_classes:
                    st.success(f"✅ {student_class}반 학생 확인되었습니다. 맛있게 드세요!")
                else:
                    # 새치기 발동!
                    st.session_state.siren = True
                    st.rerun()
        else:
            st.warning("정확한 5자리 학번을 입력하세요.")

    st.divider()

    st.subheader("🤫 [학생용] 익명 신고 시스템")
    target_id = st.text_input("새치기한 얄미운 학생의 학번 입력:", max_chars=5)
    if st.button("익명 신고하기", type="primary", use_container_width=True):
        if len(target_id) == 5 and target_id.isdigit():
            df = pd.read_csv(CSV_FILE, encoding='utf-8-sig')
            target_id_int = int(target_id)
            if target_id_int in df['학번'].values:
                df.loc[df['학번'] == target_id_int, '신고횟수'] += 1
            else:
                new_row = pd.DataFrame([{'학번': target_id_int, '신고횟수': 1}])
                df = pd.concat([df, new_row], ignore_index=True)
            df.to_csv(CSV_FILE, index=False, encoding='utf-8-sig')
            st.success("신고가 접수되었습니다. (선생님 대시보드에 반영됨)")
        else:
            st.warning("정확한 5자리 학번을 입력하세요.")

# --- 오른쪽: 교사용 대시보드 ---
with col_teacher:
    st.subheader("👨‍🏫 [교사용] 관리자 대시보드")
    st.markdown("**수동 제어 (Override)**")

    if st.button("⚡ 자리가 비었습니다! 다음 그룹(6~10반) 조기 입장 허용", use_container_width=True):
        st.session_state.allowed_classes.extend([6, 7, 8, 9, 10])
        st.success("지금부터 6~10반 입장을 조기 허용합니다!")
        st.rerun()

    st.divider()
    st.markdown("**📌 실시간 신고 누적 명단 (3회 이상 페널티)**")

    df = pd.read_csv(CSV_FILE, encoding='utf-8-sig')
    if not df.empty:
        # 신고 횟수가 높은 순으로 정렬하여 표로 보여줌
        st.dataframe(df.sort_values(by='신고횟수', ascending=False), use_container_width=True, hide_index=True)
    else:
        st.info("아직 신고된 학생이 없습니다.")