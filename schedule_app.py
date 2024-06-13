import streamlit as st
from ortools.sat.python import cp_model
from datetime import datetime, timedelta


def create_schedule(employee_list, interview_slots):
    model = cp_model.CpModel()

    # 변수 생성
    interviews = {}
    num_employees = len(employee_list)
    num_slots = len(interview_slots)

    for i in range(num_employees):
        for j in range(num_slots):
            interviews[(i, j)] = model.NewBoolVar(f'interview_{i}_{j}')

    # 제약 조건 추가
    for i in range(num_employees):
        model.Add(sum(interviews[(i, j)] for j in range(num_slots)) <= 1)

    for j in range(num_slots):
        model.Add(sum(interviews[(i, j)] for i in range(num_employees)) <= 1)

    # 최대한 많은 면담을 진행하는 목표 설정
    model.Maximize(sum(interviews[(i, j)] for i in range(num_employees) for j in range(num_slots)))

    # 모델 해결
    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        schedule = {}
        for i in range(num_employees):
            for j in range(num_slots):
                if solver.Value(interviews[(i, j)]) == 1:
                    schedule[employee_list[i]] = interview_slots[j]
        return schedule
    else:
        return None


# Streamlit 인터페이스
st.title("면담 일정 계획 도구")

st.sidebar.header("입력 데이터")
employee_names = st.sidebar.text_area("직원 이름 입력 (한 줄에 한 명씩)", value="")

# 면담 가능한 시작 시간과 끝 시간 입력
start_time = st.sidebar.time_input("면담 가능한 시작 시간", datetime.strptime("13:00", "%H:%M").time())
end_time = st.sidebar.time_input("면담 가능한 끝 시간", datetime.strptime("01:00", "%H:%M").time())

interview_duration = st.sidebar.number_input("면담 진행 시간 (분 단위)", min_value=5, max_value=120, value=30)
break_duration = st.sidebar.number_input("쉬는 시간 (분 단위)", min_value=0, max_value=120, value=10)

# 시간대 자동 생성
if start_time and end_time:
    interview_slots = []
    current_time = datetime.combine(datetime.today(), start_time)
    end_time_datetime = datetime.combine(datetime.today(), end_time)
    if end_time <= start_time:
        end_time_datetime += timedelta(days=1)

    while current_time + timedelta(minutes=interview_duration) <= end_time_datetime:
        next_time = current_time + timedelta(minutes=interview_duration)
        slot = f"{current_time.strftime('%H:%M')}-{next_time.strftime('%H:%M')}"
        interview_slots.append(slot)
        current_time = next_time + timedelta(minutes=break_duration)

    st.sidebar.subheader("자동 생성된 면담 시간대")
    selected_slots = []
    for slot in interview_slots:
        if st.sidebar.checkbox(f"시간대 {slot} 제외", key=f"exclude_{slot}"):
            continue
        selected_slots.append(slot)

    if employee_names:
        employee_list = [name.strip() for name in employee_names.split("\n") if name.strip()]

        if st.sidebar.button("스케줄 생성"):
            schedule = create_schedule(employee_list, selected_slots)
            if schedule:
                st.subheader("면담 일정")
                interviewed = set(schedule.keys())
                not_interviewed = set(employee_list) - interviewed
                st.write("면담 진행 인원:")
                for employee, slot in schedule.items():
                    st.write(f"{employee}: 시간대 {slot}")
                st.write(f"\n총 면담 진행 인원 수: {len(interviewed)}")
                st.write(f"\n총 면담 미진행 인원 수: {len(not_interviewed)}")

                if not_interviewed:
                    st.write("\n면담하지 못한 인원:")
                    for employee in not_interviewed:
                        st.write(employee)
            else:
                st.write("최적의 스케줄을 찾을 수 없습니다.")
    else:
        st.sidebar.write("직원 이름을 입력해주세요.")
else:
    st.sidebar.write("면담 가능한 시간의 시작과 끝을 지정해주세요.")
