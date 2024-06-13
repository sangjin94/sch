import streamlit as st
from ortools.sat.python import cp_model
from datetime import datetime, timedelta

def create_schedule(employee_list, interview_slots, max_interviews_per_slot):
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
        model.Add(sum(interviews[(i, j)] for i in range(num_employees)) <= max_interviews_per_slot)

    # 목표 설정: 앞쪽 슬롯을 우선적으로 채우고, 그렇지 못한 경우 마지막 슬롯에 배정
    weighted_sum = sum((num_slots - j) * interviews[(i, j)] for i in range(num_employees) for j in range(num_slots))
    model.Maximize(weighted_sum)

    # 모델 해결
    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        schedule = {}
        for i in range(num_employees):
            for j in range(num_slots):
                if solver.Value(interviews[(i, j)]) == 1:
                    if interview_slots[j] in schedule:
                        schedule[interview_slots[j]].append(employee_list[i])
                    else:
                        schedule[interview_slots[j]] = [employee_list[i]]
        return schedule
    else:
        return None

# Streamlit 인터페이스
st.title("면담 일정 계획")

if st.sidebar.button("스케줄 생성"):
    schedule_generated = True
else:
    schedule_generated = False

employee_names = st.sidebar.text_area("직원 이름 입력 (한 줄에 한 명씩)", value="")

# 면담 가능한 시작 날짜 입력
start_date = st.sidebar.date_input("면담 가능한 시작 날짜", datetime.today())

# 면담 가능한 일 수 입력
num_days = st.sidebar.number_input("면담 가능한 일 수", min_value=1, max_value=7, value=1)

# 면담 가능한 시작 시간과 끝 시간 입력
start_time = st.sidebar.time_input("면담 가능한 시작 시간", datetime.strptime("16:00", "%H:%M").time())
end_time = st.sidebar.time_input("면담 가능한 끝 시간", datetime.strptime("23:00", "%H:%M").time())

interview_duration = st.sidebar.number_input("면담 진행 시간 (분 단위)", min_value=5, max_value=120, value=30)
break_duration = st.sidebar.number_input("쉬는 시간 (분 단위)", min_value=0, max_value=120, value=10)

max_interviews_per_slot = st.sidebar.number_input("시간대당 최대 면담 인원 수", min_value=1, value=1)

# 시간대 자동 생성
interview_slots = []
for day in range(num_days):
    current_time = datetime.combine(start_date + timedelta(days=day), start_time)
    end_time_datetime = datetime.combine(start_date + timedelta(days=day), end_time)
    if end_time <= start_time:
        end_time_datetime += timedelta(days=1)

    while current_time + timedelta(minutes=interview_duration) <= end_time_datetime:
        next_time = current_time + timedelta(minutes=interview_duration)
        slot = f"{current_time.strftime('%Y-%m-%d %H:%M')}-{next_time.strftime('%H:%M')}"
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

    if schedule_generated:
        schedule = create_schedule(employee_list, selected_slots, max_interviews_per_slot)
        if schedule:
            interviewed = set()
            for slot, employees in schedule.items():
                for employee in employees:
                    interviewed.add(employee)
            not_interviewed = set(employee_list) - interviewed

            st.write("면담 진행 인원:")
            sorted_schedule = dict(sorted(schedule.items()))
            for slot, employees in sorted_schedule.items():
                st.write(f"{slot}: {', '.join(employees)}")

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
