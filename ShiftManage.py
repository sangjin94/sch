import streamlit as st
import pandas as pd
import numpy as np
import io

# 시프트 순환 규칙 정의
shift_order = ['A', 'B', 'C', 'D', 'E', 'F', 'G']

# 시프트 순환 함수
def next_shift(current_shift):
    idx = shift_order.index(current_shift)
    return shift_order[(idx + 1) % len(shift_order)]

# 다음달 시프트 계산 함수
def calculate_next_month_shifts(employees):
    employees['next_shift'] = employees.apply(lambda row: next_shift(row['current_shift']) if row['current_shift'] != '퇴사' else '퇴사', axis=1)

    # 현재 F 시프트인 사람들을 대상으로 G 시프트 인원과 맞추기
    for process in employees['process'].unique():
        f_shift_employees = employees[(employees['current_shift'] == 'F') & (employees['next_shift'] == 'G') & (employees['process'] == process)]
        g_shift_count = employees[(employees['current_shift'] == 'G') & (employees['process'] == process)].shape[0]

        if f_shift_employees.shape[0] > g_shift_count:
            excess_f_to_g = f_shift_employees.sample(f_shift_employees.shape[0] - g_shift_count).index
            employees.loc[excess_f_to_g, 'next_shift'] = 'F'

    return employees

# Streamlit 애플리케이션 설정
st.title("근무 시프트 자동 배정 시스템")

# 직원 데이터 입력 (텍스트 박스로 여러 줄 입력 받기)
st.write("직원 정보를 복사하여 아래 텍스트 박스에 붙여넣기 하세요. 형식: 사번 이름 시프트 입사일 공정 직급 (각 줄에 하나씩, 공백으로 구분)")
employee_data_input = st.text_area("직원 데이터 입력", height=200)

# 입력 데이터 처리
if employee_data_input:
    # 데이터프레임 생성
    data = [x.split() for x in employee_data_input.split('\n') if x]
    employees_df = pd.DataFrame(data, columns=['id', 'name', 'current_shift', 'entry_date', 'process', 'position'])

    # 결과 출력
    st.write("입력된 직원 데이터:")
    st.write(employees_df)

    # 다음달 시프트 계산 버튼
    if st.button("다음달 시프트 계산"):
        updated_employees_df = calculate_next_month_shifts(employees_df)

        # current_shift 열과 next_shift 열의 위치 바꾸기
        updated_employees_df = updated_employees_df[
            ['id', 'name', 'next_shift', 'entry_date', 'process', 'position', 'current_shift']]

        st.write("다음달 시프트:")
        st.write(updated_employees_df)

        # 엑셀 파일로 저장
        output = io.BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        updated_employees_df.to_excel(writer, index=False, sheet_name='Sheet1')
        writer.close()
        output.seek(0)

        st.download_button(
            label="엑셀 파일 다운로드",
            data=output,
            file_name="shift_schedule_with_process.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # 공정별로 통계 표시
        processes = employees_df['process'].unique()
        for process in processes:
            st.sidebar.write(f"### {process} 공정 통계")
            current_employees = employees_df[(employees_df['process'] == process) & (employees_df['current_shift'] != '퇴사')]
            next_employees = updated_employees_df[(updated_employees_df['process'] == process) & (updated_employees_df['next_shift'] != '퇴사')]

            current_shift_counts = current_employees['current_shift'].value_counts(normalize=True).reindex(shift_order, fill_value=0)
            current_shift_counts_abs = current_employees['current_shift'].value_counts().reindex(shift_order, fill_value=0)

            next_shift_counts = next_employees['next_shift'].value_counts(normalize=True).reindex(shift_order, fill_value=0)
            next_shift_counts_abs = next_employees['next_shift'].value_counts().reindex(shift_order, fill_value=0)

            stats = pd.DataFrame({
                '현재_비율(%)': (current_shift_counts.values * 100).round(2),
                '현재_인원': current_shift_counts_abs.values,
                '다음달_비율(%)': (next_shift_counts.values * 100).round(2),
                '다음달_인원': next_shift_counts_abs.values
            }, index=shift_order)

            # 총합 행 추가
            total_row = pd.DataFrame({
                '현재_비율(%)': [(current_shift_counts_abs.sum() / len(current_employees) * 100).round(2) if len(current_employees) > 0 else 0],
                '현재_인원': [current_shift_counts_abs.sum()],
                '다음달_비율(%)': [(next_shift_counts_abs.sum() / len(next_employees) * 100).round(2) if len(next_employees) > 0 else 0],
                '다음달_인원': [next_shift_counts_abs.sum()]
            }, index=['총합'])

            stats = pd.concat([stats, total_row])
            st.sidebar.write(stats)

        # 퇴사 인원 수 표시
        st.sidebar.write("### 퇴사 인원 통계")
        resignation_counts = employees_df[employees_df['current_shift'] == '퇴사'].groupby('process').size()
        st.sidebar.write(pd.DataFrame({
            'Process': resignation_counts.index,
            'Count': resignation_counts.values
        }).set_index('Process'))
else:
    st.write("직원 데이터를 입력하세요.")
