import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import time # 애니메이션을 위한 시간 제어

# --- 1. 시뮬레이션 파라미터 설정 ---
st.set_page_config(layout="wide") # 페이지 레이아웃 넓게 설정
st.title("🌌 미세 중력 렌즈 시뮬레이션 (애니메이션)")
st.write("다양한 파라미터를 조절하여 중력 렌즈 효과와 외계 행성으로 인한 밝기 변화 곡선을 관찰해보세요.")

# 사이드바에서 파라미터 조절
st.sidebar.header("조정 파라미터")

# 외계 행성 위치 조절 (렌즈 별에 대한 상대적인 X축 위치)
planet_position = st.sidebar.slider(
    "외계 행성 상대 위치 (렌즈 별 중심 기준)",
    min_value=-2.0, max_value=2.0, value=0.0, step=0.05,
    help="렌즈 별 중심에 대한 외계 행성의 상대적인 수평 위치. 0은 렌즈 별과 일직선."
)

# 렌즈 별 질량 조절 (태양 질량 단위)
lens_mass_solar = st.sidebar.slider(
    "렌즈 별 질량 (태양 질량)",
    min_value=0.1, max_value=2.0, value=1.0, step=0.1,
    help="빛을 휘게 하는 렌즈 별의 질량 (태양 질량 대비)."
)

# --- 새로 추가된 변수들 ---
# 1. 광원 별의 크기 (아인슈타인 반경 대비)
source_radius_ratio = st.sidebar.slider(
    "광원 별의 크기 (아인슈타인 반경 대비)",
    min_value=0.001, max_value=0.1, value=0.005, step=0.001, format="%.3f",
    help="배경 광원 별의 유한한 크기. 값이 커질수록 밝기 곡선 피크가 뭉툭해집니다."
)

# 2. 외계 행성 질량 (렌즈 별 질량 대비)
planet_mass_ratio = st.sidebar.slider(
    "외계 행성 질량 (렌즈 별 질량 대비)",
    min_value=1e-6, max_value=1e-2, value=1e-4, step=1e-6, format="%.0e",
    help="외계 행성의 질량 비율. 범프의 크기에 영향."
)

# 3. 외계 행성의 렌즈 별로부터의 거리 (아인슈타인 반경 대비)
planet_separation_from_lens = st.sidebar.slider(
    "행성-렌즈 별 분리 거리 (아인슈타인 반경 대비)",
    min_value=0.5, max_value=2.0, value=1.0, step=0.05,
    help="렌즈 별로부터 행성까지의 거리, 아인슈타인 반경의 배수."
)

# 4. 렌즈와 광원의 상대 속도 (밝기 곡선의 폭에 영향)
relative_velocity_factor = st.sidebar.slider(
    "렌즈-광원 상대 속도",
    min_value=0.1, max_value=2.0, value=1.0, step=0.1,
    help="밝기 곡선 이벤트의 지속 시간(x축 스케일)에 영향. 값이 클수록 이벤트가 짧아집니다."
)

# 5. 관측자-렌즈 거리 (kpc)
observer_lens_distance_kpc = st.sidebar.slider(
    "관측자-렌즈 거리 (kpc)",
    min_value=1.0, max_value=10.0, value=8.0, step=0.1,
    help="관측자부터 렌즈 별까지의 거리 (킬로파섹). 아인슈타인 반경 크기에 영향."
)

# --- 애니메이션 제어 슬라이더 ---
animation_progress = st.sidebar.slider(
    "시뮬레이션 시간 진행",
    min_value=0, max_value=100, value=0, step=1,
    help="배경 별의 렌즈 시스템 통과 시간 진행도를 조절합니다."
)
animate_button = st.sidebar.button("애니메이션 시작/정지")

# --- 2. 물리 상수 및 기본 설정 ---
G = 6.67430e-11  # 중력 상수 (m^3 kg^-1 s^-2)
c = 2.99792458e8 # 빛의 속도 (m/s)
M_sun = 1.989e30 # 태양 질량 (kg)
PC_TO_METER = 3.0857e16 # 1 파섹(pc) = 3.0857e16 미터

D_L = observer_lens_distance_kpc * 1000 * PC_TO_METER # kpc를 미터로 변환
D_S = D_L + (500 * PC_TO_METER) # 렌즈보다 500 파섹 뒤에 광원이 있다고 가정
D_LS = D_S - D_L

M_lens = lens_mass_solar * M_sun

einstein_radius_angle = np.sqrt(4 * G * M_lens / (c**2) * D_LS / (D_L * D_S))

R_E_display = 40 # 시각화에서 아인슈타인 반경에 해당하는 픽셀 크기


# --- 3. 중력 렌즈 광도 증폭 계산 함수 ---
# 실제 이진 렌즈 광도 곡선은 훨씬 복잡하며, 전문 라이브러리나 수치적 해결이 필요합니다.
# 이 함수는 개념적 이해를 돕기 위한 단순화된 모델입니다.
def calculate_magnification(u_source_x, u_source_y, u_planet_x, planet_separation, mass_ratio, source_size):
    """
    미세 중력 렌즈 광도 증폭률 계산 (단순화된 근사)

    Args:
        u_source_x (float): 배경 별의 렌즈 중심으로부터의 X축 무차원 거리 (아인슈타인 반경 단위).
        u_source_y (float): 배경 별의 렌즈 중심으로부터의 Y축 무차원 거리 (아인슈타인 반경 단위).
        u_planet_x (float): 외계 행성의 렌즈 별에 대한 X축 위치 (아인슈타인 반경 단위).
        planet_separation (float): 행성과 렌즈 별 사이의 거리 비율 (아인슈타인 반경 단위, Y축).
        mass_ratio (float): 행성 질량 / 렌즈 별 질량.
        source_size (float): 광원 별의 크기 (아인슈타인 반경 대비).

    Returns:
        float: 계산된 광도 증폭률.
    """
    
    # 단일 렌즈에 의한 기본 증폭 계산
    u_main = np.sqrt(u_source_x**2 + u_source_y**2) # 렌즈 중심으로부터의 거리
    
    if u_main < 1e-6: # u가 0에 매우 가까울 때 (중심)
        if source_size > 0:
            mag_main = (u_main**2 + 2) / (np.sqrt(u_main**2 + 4) * source_size)
        else:
            mag_main = 1e6 # 무한대 증폭 근사
    else:
        mag_main = (u_main**2 + 2) / (u_main * np.sqrt(u_main**2 + 4))

    # 과도한 증폭 방지
    if mag_main > 1e4:
        mag_main = 1e4
    
    magnification = mag_main

    # 행성으로 인한 추가 증폭 (매우 단순화된 모델)
    # 행성의 위치 (u_planet_x, planet_separation)를 기준으로 배경 별의 거리를 계산
    # 행성 Y 위치는 'planet_separation'으로 고정. X 위치는 'u_planet_x'로 고정.
    
    # 배경 별과 행성 사이의 상대 거리 (2D 평면)
    dist_to_planet = np.sqrt((u_source_x - u_planet_x)**2 + (u_source_y - planet_separation)**2)
    
    # 행성으로 인한 증폭의 '영향권'을 나타내는 계수
    # 행성 질량이 클수록, 그리고 행성에 가까울수록 영향이 커지도록 설정
    # 행성으로부터 멀어질수록 증폭 효과가 급격히 줄어들게 (역제곱 근사)
    
    # 이진 렌즈의 코스틱(caustic) 영역을 매우 단순하게 흉내냅니다.
    # 행성 주위의 작은 특이점을 지날 때 발생하는 범프
    if dist_to_planet < 0.1 + source_size + (mass_ratio * 10): # 영향권 범위 확대 (질량에 비례)
        # 행성 질량에 비례하고 거리에 반비례하는 추가 증폭
        # 0 나눗셈 방지 위해 0.001 추가
        additional_mag = (mass_ratio / (dist_to_planet**2 + 0.001)) * 50 # 계수 조정
        magnification += additional_mag
        
        # 행성 위치를 통과할 때 약간의 딥 효과 추가 (실제로는 더 복잡)
        # 만약 배경별이 행성 중심을 정확히 지나갈 경우를 흉내냄
        if dist_to_planet < source_size * 0.5:
             magnification *= (1 - mass_ratio * 500) # 행성으로 인한 약간의 감쇄 (극단적 딥 방지)
             if magnification < 1.0: magnification = 1.0 # 1보다 작아지지 않게 방지

    return magnification


# --- 4. 중력 렌즈 시스템 시각화 ---
st.subheader("시스템 시각화")

# 시각화 그림을 그릴 빈 컨테이너 생성
visualization_placeholder = st.empty()


def update_lensing_visualization(current_u_x, current_u_y, ax_obj):
    """
    현재 u 값에 따라 시스템 시각화를 업데이트합니다.
    """
    ax_obj.clear() # 이전 그림 지우기
    ax_obj.set_facecolor('black')
    ax_obj.set_xlim(-100, 100)
    ax_obj.set_ylim(-100, 100)
    ax_obj.set_aspect('equal')
    ax_obj.axis('off')

    # 렌즈 별 그리기 (중앙)
    ax_obj.add_artist(plt.Circle((0, 0), 10, color='yellow', zorder=5))
    ax_obj.text(0, -15, '렌즈 별', color='white', ha='center', fontsize=10)

    # 외계 행성 그리기
    planet_display_x = planet_position * R_E_display 
    planet_display_y = planet_separation_from_lens * R_E_display * 0.3 # 행성 y 위치도 아인슈타인 반경 기준으로
    ax_obj.add_artist(plt.Circle((planet_display_x, planet_display_y), 4, color='gray', zorder=6))
    ax_obj.text(planet_display_x, planet_display_y + 10, '외계 행성', color='white', ha='center', fontsize=10)

    # 배경 별 (광원) 그리기 - u 값에 따라 X, Y 위치 변화
    source_display_x = -current_u_x * R_E_display # u_x 값에 따라 배경별 X 위치 조절
    source_display_y = -current_u_y * R_E_display # u_y 값에 따라 배경별 Y 위치 조절
    source_display_radius = source_radius_ratio * R_E_display * 5 
    ax_obj.add_artist(plt.Circle((source_display_x, source_display_y), source_display_radius, color='white', zorder=4))
    ax_obj.text(source_display_x, source_display_y - 15, '배경 별', color='white', ha='center', fontsize=10)


    # 아인슈타인 링 시각화
    circle_einstein = plt.Circle((0, 0), R_E_display, color='cyan', linestyle='--', fill=False, alpha=0.5, zorder=3)
    ax_obj.add_artist(circle_einstein)
    ax_obj.text(R_E_display + 5, 0, '아인슈타인 링', color='cyan', va='center', ha='left', fontsize=10)

    # 빛의 경로 (개념적, 곡선으로 표현) - 배경 별 위치에 따라 경로도 업데이트
    # 이 부분은 현재 u_source_x, u_source_y에 맞게 동적으로 더 정교하게 그리기 어려움
    # 개념적으로만 유지하거나, 더 복잡한 광선 추적 시뮬레이션 필요
    light_path_y_offset = R_E_display * 0.7
    ax_obj.plot([-100, -20], [-light_path_y_offset, -light_path_y_offset], color='orange', linestyle='-', linewidth=1)
    ax_obj.plot([20, 100], [-light_path_y_offset, -light_path_y_offset], color='orange', linestyle='-', linewidth=1)
    ax_obj.plot([-20, 0, 20], [-light_path_y_offset, -10, -light_path_y_offset], color='orange', linestyle='-', linewidth=1, alpha=0.7)


# 초기 시각화 그림 생성 (밝기 곡선의 중앙으로 초기화)
fig_lensing, ax_lensing = plt.subplots(figsize=(8, 5))
# 초기 u_x, u_y 값을 설정 (예: 밝기 곡선 중앙값)
initial_u_x = 0.0 # 중앙값
initial_u_y = 0.5 # 배경별의 렌즈-행성 시스템에 대한 충격 인자 (Impact Parameter)를 표현
update_lensing_visualization(initial_u_x, initial_u_y, ax_lensing) 
visualization_placeholder.pyplot(fig_lensing)


# --- 5. 밝기 변화 곡선 ---
st.subheader("밝기 변화 곡선")

# 배경 별의 렌즈 시스템 횡단 경로 (X축: 렌즈-광원 상대 거리 u)
# 상대 속도에 따라 x축 범위 조절 (이벤트 지속 시간 조절)
u_min_curve = -3.0 * relative_velocity_factor
u_max_curve = 3.0 * relative_velocity_factor
u_values_x_curve = np.linspace(u_min_curve, u_max_curve, 300) 

# 광원 별의 렌즈 시스템에 대한 충격 인자 (Impact Parameter) (Y축 고정)
# 이 값이 0이면 렌즈 중앙을 정확히 통과. 값이 커질수록 렌즈에서 멀리 떨어져 통과.
# 행성 효과를 보려면 0에 가깝지만 행성의 Y위치와 어느 정도 겹쳐야 함.
u_source_y_impact_parameter = st.sidebar.slider(
    "광원 경로 Y 위치 (충격 인자)",
    min_value=0.0, max_value=1.5, value=0.5, step=0.01,
    help="배경 광원 별의 렌즈 시스템 통과 경로의 Y축 위치 (충격 인자). 값이 0에 가까울수록 렌즈 중앙을 지납니다."
)


# 각 u_x 값에 대한 밝기 증폭률 계산 (u_y는 고정)
magnifications_curve = []
for u_x_val in u_values_x_curve:
    mag = calculate_magnification(
        u_source_x=u_x_val, # 배경 별의 X축 경로
        u_source_y=u_source_y_impact_parameter, # 배경 별의 Y축 충격 인자
        u_planet_x=planet_position,
        planet_separation=planet_separation_from_lens,
        mass_ratio=planet_mass_ratio,
        source_size=source_radius_ratio
    )
    magnifications_curve.append(mag)

# 밝기 곡선 그림 초기화
fig_light_curve, ax_light_curve = plt.subplots(figsize=(8, 4))
ax_light_curve.plot(u_values_x_curve, magnifications_curve, color='blue', linewidth=2)
ax_light_curve.set_title("배경 별 밝기 변화 (광도 증폭률)")
ax_light_curve.set_xlabel(f"렌즈-광원 상대 X거리 (아인슈타인 반경의 배수, u_x)")
ax_light_curve.set_ylabel("광도 증폭률")
ax_light_curve.grid(True)
ax_light_curve.set_ylim(bottom=1.0) # 증폭률은 1 (원래 밝기)보다 작아지지 않음

# 밝기 곡선 그림을 담을 컨테이너
light_curve_placeholder = st.empty()
light_curve_placeholder.pyplot(fig_light_curve)


# --- 애니메이션 루프 ---
if animate_button:
    if 'animating' not in st.session_state:
        st.session_state.animating = False
    
    st.session_state.animating = not st.session_state.animating # 버튼 누르면 상태 토글

if st.session_state.get('animating', False):
    progress_bar = st.progress(0)
    for i in range(101):
        # 애니메이션 진행도에 따른 u_x_value 계산
        current_u_index = int(i / 100 * (len(u_values_x_curve) - 1))
        current_u_x_value_for_animation = u_values_x_curve[current_u_index]
        
        # 시각화 업데이트 (배경 별 X, Y 위치 모두 반영)
        update_lensing_visualization(current_u_x_value_for_animation, u_source_y_impact_parameter, ax_lensing)
        visualization_placeholder.pyplot(fig_lensing)

        # 밝기 곡선 업데이트 (현재 위치 마커)
        ax_light_curve.clear()
        ax_light_curve.plot(u_values_x_curve, magnifications_curve, color='blue', linewidth=2)
        ax_light_curve.set_title("배경 별 밝기 변화 (광도 증폭률)")
        ax_light_curve.set_xlabel(f"렌즈-광원 상대 X거리 (아인슈타인 반경의 배수, u_x)")
        ax_light_curve.set_ylabel("광도 증폭률")
        ax_light_curve.grid(True)
        ax_light_curve.set_ylim(bottom=1.0)
        
        current_mag_at_animation_point = calculate_magnification(
            u_source_x=current_u_x_value_for_animation,
            u_source_y=u_source_y_impact_parameter,
            u_planet_x=planet_position,
            planet_separation=planet_separation_from_lens,
            mass_ratio=planet_mass_ratio,
            source_size=source_radius_ratio
        )
        ax_light_curve.plot([current_u_x_value_for_animation], 
                            [current_mag_at_animation_point], 
                            'ro', markersize=8, label='현재 광원 위치')
        ax_light_curve.legend()
        light_curve_placeholder.pyplot(fig_light_curve)

        progress_bar.progress(i)
        time.sleep(0.05) # 애니메이션 속도 조절

    st.session_state.animating = False # 애니메이션 종료 시 상태 리셋
    st.experimental_rerun() # 애니메이션 종료 후 전체 앱 새로고침

# 슬라이더로 직접 조절 시에도 시각화 및 곡선 업데이트
else:
    current_u_index_from_slider = int(animation_progress / 100 * (len(u_values_x_curve) - 1))
    current_u_x_value_from_slider = u_values_x_curve[current_u_index_from_slider]

    # 시각화 업데이트
    update_lensing_visualization(current_u_x_value_from_slider, u_source_y_impact_parameter, ax_lensing)
    visualization_placeholder.pyplot(fig_lensing)

    # 밝기 곡선 업데이트 (현재 위치 마커)
    ax_light_curve.clear()
    ax_light_curve.plot(u_values_x_curve, magnifications_curve, color='blue', linewidth=2)
    ax_light_curve.set_title("배경 별 밝기 변화 (광도 증폭률)")
    ax_light_curve.set_xlabel(f"렌즈-광원 상대 X거리 (아인슈타인 반경의 배수, u_x)")
    ax_light_curve.set_ylabel("광도 증폭률")
    ax_light_curve.grid(True)
    ax_light_curve.set_ylim(bottom=1.0)
    
    current_mag_at_slider_point = calculate_magnification(
        u_source_x=current_u_x_value_from_slider,
        u_source_y=u_source_y_impact_parameter,
        u_planet_x=planet_position,
        planet_separation=planet_separation_from_lens,
        mass_ratio=planet_mass_ratio,
        source_size=source_radius_ratio
    )
    ax_light_curve.plot([current_u_x_value_from_slider], 
                        [current_mag_at_slider_point], 
                        'ro', markersize=8, label='현재 광원 위치')
    ax_light_curve.legend()
    light_curve_placeholder.pyplot(fig_light_curve)


# --- 6. 추가 정보 섹션 ---
st.markdown("---")
st.subheader("중력 렌즈에 대하여")
st.write("""
**중력 렌즈(Gravitational Lensing)**는 아인슈타인의 일반 상대성 이론에 의해 예측된 현상입니다.
질량을 가진 물체(예: 별, 은하, 블랙홀)가 주변의 시공간을 휘게 만들고,
이 휘어진 시공간을 통과하는 빛의 경로가 마치 렌즈를 통과하는 것처럼 휘어지는 현상입니다.
이는 멀리 떨어진 광원(배경 별)의 이미지를 확대하거나 왜곡시켜 보이는 효과를 줍니다.

**미세 중력 렌즈(Microlensing)**는 렌즈 역할을 하는 천체가 항성이나 비교적 작은 천체(예: 외계 행성)일 때 나타나는 현상입니다.
이 경우, 멀리 떨어진 배경 별의 빛이 렌즈 천체에 의해 일시적으로 밝아지는 **광도 변화**가 발생합니다.
특히 렌즈 별 주위에 외계 행성이 존재하면, 행성의 중력도 빛의 경로에 미세한 영향을 주어
배경 별의 밝기 곡선에 독특한 추가적인 변화(예: '범프' 또는 '딥')를 만들어냅니다.
이러한 미세한 밝기 변화를 분석하여 직접 보기 어려운 외계 행성의 존재를 찾아낼 수 있습니다.
""")

st.info("이 시뮬레이션은 중력 렌즈 현상, 특히 외계 행성이 미치는 영향을 개념적으로 보여주기 위해 **매우 단순화된 물리 모델**을 사용합니다. 실제 천문학적 관측 및 이론은 훨씬 더 복잡합니다.")
