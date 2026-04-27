import streamlit as st
import pandas as pd
import os
from datetime import datetime

st.set_page_config(page_title="스마트 급식실 패스", layout="wide")

# 1. 새로운 데이터베이스 구조 (누가, 누구를, 언제 신고했는지 상세 기록)
CSV_FILE = 'report_log.csv'
if not os.path.exists(CSV_FILE):
    # 단순 횟수 기록에서 '상세 로그 기록'으로 진화
    df_init = pd.DataFrame(columns=['신고자', '피신고자', '신고일자'])
    df_init.to_csv(CSV_FILE, index=False, encoding='utf-8-sig')

if 'allowed_classes' not in st.session_state:
    st.session_state.allowed_classes = [1, 2, 3, 4, 5]
if 'siren' not in st.session_state:
    st.session_state.siren = False

# 🚨 새치기 적발 시 밈(Meme) 페널티 화면 발동
if st.session_state.siren:
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

    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("경고 끄기 (교실로 돌아가세요)", use_container_width=True):
            st.session_state.siren = False
            st.rerun()
    st.stop()

st.title("🏫 급식실 새치기 제로: 스마트 패스")
col_student, col_teacher = st.columns(2)

# --- 왼쪽: 학생용 UI ---
with col_student:
    st.subheader("📱 [학생용] 바코드 스캔 (입장)")
    st.info(f"🟢 현재 입장 가능 반: {min(st.session_state.allowed_classes)}반 ~ {max(st.session_state.allowed_classes)}반")

    student_id = st.text_input("본인의 학번 5자리 입력 (예: 30101)", max_chars=5)

    if st.button("바코드 찍기 (입장 확인)", use_container_width=True):
        if len(student_id) == 5 and student_id.isdigit():
            student_class = int(student_id[1:3])

            # [방어 3] 페널티 교사 크로스체크 시스템 연동
            df = pd.read_csv(CSV_FILE, encoding='utf-8-sig')
            if not df.empty:
                report_counts = df['피신고자'].value_counts()

                # 자동 차단 대신, 의심 명단임을 알리고 교사 확인 유도
                if int(student_id) in report_counts.index and report_counts[int(student_id)] >= 3:
                    st.error(f"❌ 학번 {student_id} 학생은 신고 누적 3회 이상으로 '페널티 의심 명단'에 있습니다. 선생님의 최종 확인을 받으세요!")
                else:
                    if student_class in st.session_state.allowed_classes:
                        st.success(f"✅ {student_class}반 학생 확인되었습니다. 맛있게 드세요!")
                    else:
                        st.session_state.siren = True
                        st.rerun()
            else:
                if student_class in st.session_state.allowed_classes:
                    st.success(f"✅ {student_class}반 학생 확인되었습니다. 맛있게 드세요!")
                else:
                    st.session_state.siren = True
                    st.rerun()
        else:
            st.warning("정확한 5자리 학번을 입력하세요.")

    st.divider()

    # [방어 1] 기명식 블라인드 신고
    st.subheader("🤫 [학생용] 블라인드 신고 시스템")
    st.caption("※ 본인 학번을 입력해야 신고되며, 허위 신고 적발 시 본인에게 페널티가 부여됩니다. (학생끼리는 절대 비공개)")

    col_a, col_b = st.columns(2)
    with col_a:
        reporter_id = st.text_input("본인 학번:", max_chars=5)
    with col_b:
        target_id = st.text_input("새치기 학생 학번:", max_chars=5)

    if st.button("신고하기", type="primary", use_container_width=True):
        if len(target_id) == 5 and target_id.isdigit() and len(reporter_id) == 5 and reporter_id.isdigit():
            if reporter_id == target_id:
                st.error("본인을 스스로 신고할 수 없습니다!")
            else:
                df = pd.read_csv(CSV_FILE, encoding='utf-8-sig')
                reporter_id_int = int(reporter_id)
                target_id_int = int(target_id)
                today_str = datetime.now().strftime("%Y-%m-%d")  # 오늘 날짜 추출

                # [방어 2] 1인 1회 중복 신고 제한 로직
                duplicate_check = df[(df['신고자'] == reporter_id_int) &
                                     (df['피신고자'] == target_id_int) &
                                     (df['신고일자'] == today_str)]

                if not duplicate_check.empty:
                    st.error("🚨 이미 오늘 해당 학생을 신고하셨습니다. (중복 신고 불가/버튼 테러 방지)")
                else:
                    # 새로운 상세 신고 기록 데이터베이스에 추가
                    new_row = pd.DataFrame([{'신고자': reporter_id_int, '피신고자': target_id_int, '신고일자': today_str}])
                    df = pd.concat([df, new_row], ignore_index=True)
                    df.to_csv(CSV_FILE, index=False, encoding='utf-8-sig')
                    st.success("✅ 신고가 정상 접수되었습니다. 선생님만 이 기록을 확인할 수 있습니다.")
        else:
            st.warning("본인 학번과 새치기 학생 학번을 모두 5자리 숫자로 입력하세요.")

# --- 오른쪽: 교사용 대시보드 ---
with col_teacher:
    st.subheader("👨‍🏫 [교사용] 관리자 대시보드")
    st.markdown("**1. 수동 제어 (Override)**")

    if st.button("⚡ 자리가 비었습니다! 다음 그룹(6~10반) 조기 입장 허용", use_container_width=True):
        st.session_state.allowed_classes.extend([6, 7, 8, 9, 10])
        st.success("지금부터 6~10반 입장을 조기 허용합니다!")
        st.rerun()

    st.divider()

    # [방어 3] 교사 크로스체크 (의심 명단 관리)
    st.markdown("**2. 🚨 페널티 의심 명단 (누적 3회 이상)**")
    st.caption("※ 시스템이 즉시 차단하지 않습니다. 아래 명단을 확인하고 주변 증언을 참고하여 수동으로 페널티를 확정하세요.")

    try:
        df = pd.read_csv(CSV_FILE, encoding='utf-8-sig')
        if not df.empty:
            # 누가 얼마나 신고 당했는지 계산
            report_counts = df['피신고자'].value_counts().reset_index()
            report_counts.columns = ['학번(피신고자)', '누적 신고 당한 횟수']
            suspects = report_counts[report_counts['누적 신고 당한 횟수'] >= 3]

            if not suspects.empty:
                st.dataframe(suspects, use_container_width=True, hide_index=True)
            else:
                st.info("현재 누적 3회 이상 의심 학생이 없습니다.")

            st.markdown("**3. 🕵️ 허위 신고/버튼 테러 의심자 확인**")
            st.caption("※ 악의적으로 너무 많은 신고를 남발하는 학생이 있는지 모니터링합니다.")
            abuser_counts = df['신고자'].value_counts().reset_index()
            abuser_counts.columns = ['학번(신고자)', '총 신고 한 횟수']
            st.dataframe(abuser_counts.head(5), use_container_width=True, hide_index=True)  # 최다 신고자 상위 5명
        else:
            st.info("아직 누적된 신고 데이터가 없습니다.")
    except FileNotFoundError:
        st.info("데이터베이스를 초기화 중입니다. 다시 실행해 주세요.")
