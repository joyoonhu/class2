import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import time 

# --- 1. 시뮬레이션 파라미터 설정 ---
st.set_page_config(layout="wide") 
st.title("🌌 미세 중력 렌즈 시뮬레이션 (최종 애니메이션 개선)")
st.write("다양한 파라미터를 조절하여 중력 렌즈 효과와 외계 행성으로 인한 밝기 변화 곡선을 관찰해보세요.")

# 사이드바에서 파라미터 조절
st.sidebar.header("조정 파라미터")

# 행성의 초기 각도 조절 (궤도 상의 시작점)
planet_initial_angle_deg = st.sidebar.slider(
    "행성 초기 각도 (도)",
    min_value=0, max_value=360, value=0, step=10,
    help="렌즈 별 주위를 공전하는 외계 행성의 시작 각도."
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
    "행성-렌즈 별 궤도 반경 (아인슈타인 반경 대비)",
    min_value=0.5, max_value=2.0, value=1.0, step=0.05,
    help="렌즈 별로부터 행성까지의 궤도 반경, 아인슈타인 반경의 배수."
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

# 6. 광원 별의 렌즈 시스템에 대한 충격 인자 (Impact Parameter) (Y축 고정)
u_source_y_impact_parameter = st.sidebar.slider(
    "광원 경로 Y 위치 (충격 인자)",
    min_value=0.0, max_value=1.5, value=0.5, step=0.01,
    help="배경 광원 별의 렌즈 시스템 통과 경로의 Y축 위치 (충격 인자). 값이 0에 가까울수록 렌즈 중앙을 지납니다."
)

# 7. 행성 공전 주기 (애니메이션 시간 단위)
planet_orbital_period_factor = st.sidebar.slider(
    "행성 공전 주기 (시뮬레이션 시간 배수)",
    min_value=0.1, max_value=5.0, value=1.0, step=0.1,
    help="행성이 렌즈 별 주위를 한 바퀴 도는 데 걸리는 시간. 값이 작을수록 빠르게 움직입니다."
)


# --- 애니메이션 제어 슬라이더 ---
animation_progress = st.sidebar.slider(
    "시뮬레이션 시간 진행",
    min_value=0, max_value=100, value=0, step=1,
    help="배경 별의 렌즈 시스템 통과 시간 진행도를 조절합니다. (행성 움직임 포함)"
)
animate_button = st.sidebar.button("애니메이션 시작/정지")

# --- Streamlit Session State 초기화 (중요!) ---
# 앱이 시작될 때마다 애니메이션 상태를 초기화하여 이전 세션 문제 방지
if 'animating' not in st.session_state:
    st.session_state.animating = False


# --- 2. 물리 상수 및 기본 설정 ---
G = 6.67430e-11  # 중력 상수 (m^3 kg^-1 s^-2)
c = 2.99792458e8 # 빛의 속도 (m/s)
M_sun = 1.989e30 # 태양 질량 (kg)
PC_TO_METER = 3.0857e16 # 1 파섹(pc) = 3.0857e16 미터

D_L = observer_lens_distance_kpc * 1000 * PC_TO_METER 
D_S = D_L + (500 * PC_TO_METER) 
D_LS = D_S - D_L

M_lens = lens_mass_solar * M_sun

einstein_radius_angle = np.sqrt(4 * G * M_lens / (c**2) * D_LS / (D_L * D_S))

R_E_display = 40 


# --- 3. 중력 렌즈 광도 증폭 계산 함수 ---
def calculate_magnification(u_source_x, u_source_y, u_planet_x, u_planet_y, mass_ratio, source_size):
    """
    미세 중력 렌즈 광도 증폭률 계산 (단순화된 근사)
    """
    
    u_main = np.sqrt(u_source_x**2 + u_source_y**2) 
    
    if u_main < 1e-6: 
        if source_size > 0:
            mag_main = (u_main**2 + 2) / (np.sqrt(u_main**2 + 4) * source_size)
        else:
            mag_main = 1e6 
    else:
        mag_main = (u_main**2 + 2) / (u_main * np.sqrt(u_main**2 + 4))

    if mag_main > 1e4:
        mag_main = 1e4
    
    magnification = mag_main

    dist_to_planet = np.sqrt((u_source_x - u_planet_x)**2 + (u_source_y - u_planet_y)**2)
    
    if dist_to_planet < 0.1 + source_size + (mass_ratio * 10): 
        additional_mag = (mass_ratio / (dist_to_planet**2 + 0.001)) * 50 
        magnification += additional_mag
        
        if dist_to_planet < source_size * 0.5:
             magnification *= (1 - mass_ratio * 500) 
             if magnification < 1.0: magnification = 1.0 

    return magnification


# --- 4. 중력 렌즈 시스템 시각화 ---
st.subheader("시스템 시각화")

# 시각화 그림을 그릴 빈 컨테이너 생성
visualization_placeholder = st.empty()


def update_lensing_visualization(current_u_x, current_u_y, current_planet_x, current_planet_y, ax_obj):
    """
    현재 u 값과 행성 위치에 따라 시스템 시각화를 업데이트합니다.
    """
    ax_obj.clear() 
    ax_obj.set_facecolor('black')
    ax_obj.set_xlim(-100, 100)
    ax_obj.set_ylim(-100, 100)
    ax_obj.set_aspect('equal')
    ax_obj.axis('off')

    # 렌즈 별 그리기 (중앙)
    ax_obj.add_artist(plt.Circle((0, 0), 10, color='yellow', zorder=5))
    ax_obj.text(0, -15, '렌즈 별', color='white', ha='center', fontsize=10)

    # 외계 행성 그리기 (동적으로 위치 변화)
    planet_display_x = current_planet_x * R_E_display 
    planet_display_y = current_planet_y * R_E_display 
    ax_obj.add_artist(plt.Circle((planet_display_x, planet_display_y), 4, color='gray', zorder=6))
    ax_obj.text(planet_display_x, planet_display_y + 10, '외계 행성', color='white', ha='center', fontsize=10)

    # 배경 별 (광원) 그리기 - u 값에 따라 X, Y 위치 변화
    source_display_x = -current_u_x * R_E_display 
    source_display_y = -current_u_y * R_E_display 
    source_display_radius = source_radius_ratio * R_E_display * 5 
    ax_obj.add_artist(plt.Circle((source_display_x, source_display_y), source_display_radius, color='orange', zorder=4)) 
    ax_obj.text(source_display_x, source_display_y - 15, '배경 별', color='white', ha='center', fontsize=10)


    # 아인슈타인 링 시각화
    circle_einstein = plt.Circle((0, 0), R_E_display, color='cyan', linestyle='--', fill=False, alpha=0.5, zorder=3)
    ax_obj.add_artist(circle_einstein)
    ax_obj.text(R_E_display + 5, 0, '아인슈타인 링', color='cyan', va='center', ha='left', fontsize=10)

    # 빛의 경로 (개념적)
    light_path_y_offset = R_E_display * 0.7
    ax_obj.plot([-100, -20], [-light_path_y_offset, -light_path_y_offset], color='orange', linestyle='-', linewidth=1)
    ax_obj.plot([20, 100], [-light_path_y_offset, -light_path_y_offset], color='orange', linestyle='-', linewidth=1)
    ax_obj.plot([-20, 0, 20], [-light_path_y_offset, -10, -light_path_y_offset], color='orange', linestyle='-', linewidth=1, alpha=0.7)


# 초기 시각화 그림 생성
fig_lensing, ax_lensing = plt.subplots(figsize=(8, 5))

# 초기 행성 위치 계산 (슬라이더에 따라)
initial_planet_angle_rad = np.deg2rad(planet_initial_angle_deg)
initial_planet_x = planet_separation_from_lens * np.cos(initial_planet_angle_rad)
initial_planet_y = planet_separation_from_lens * np.sin(initial_planet_angle_rad)

update_lensing_visualization(
    -3.0 * relative_velocity_factor, 
    u_source_y_impact_parameter,    
    initial_planet_x,               
    initial_planet_y,               
    ax_lensing
) 
visualization_placeholder.pyplot(fig_lensing)


# --- 5. 밝기 변화 곡선 ---
st.subheader("밝기 변화 곡선")

u_min_curve = -3.0 * relative_velocity_factor
u_max_curve = 3.0 * relative_velocity_factor
u_values_x_curve = np.linspace(u_min_curve, u_max_curve, 300) 

fig_light_curve, ax_light_curve = plt.subplots(figsize=(8, 4))
light_curve_placeholder = st.empty()


# --- 애니메이션 루프 ---
if animate_button:
    st.session_state.animating = not st.session_state.animating 

if st.session_state.get('animating', False):
    st.write("애니메이션 실행 중... 🌟") 
    progress_bar = st.progress(0)
    for i in range(101):
        current_u_index = int(i / 100 * (len(u_values_x_curve) - 1))
        current_u_x_value_for_animation = u_values_x_curve[current_u_index]
        
        current_planet_angle_rad = np.deg2rad(planet_initial_angle_deg + (i / 100) * 360 / planet_orbital_period_factor)
        current_planet_x = planet_separation_from_lens * np.cos(current_planet_angle_rad)
        current_planet_y = planet_separation_from_lens * np.sin(current_planet_angle_rad)

        update_lensing_visualization(
            current_u_x_value_for_animation, 
            u_source_y_impact_parameter,
            current_planet_x, 
            current_planet_y, 
            ax_lensing
        )
        visualization_placeholder.pyplot(fig_lensing)

        ax_light_curve.clear()
        
        magnifications_curve_animated = []
        for idx, u_x_val in enumerate(u_values_x_curve):
            temp_planet_angle_rad = np.deg2rad(planet_initial_angle_deg + (i / 100) * 360 / planet_orbital_period_factor)
            temp_planet_x = planet_separation_from_lens * np.cos(temp_planet_angle_rad)
            temp_planet_y = planet_separation_from_lens * np.sin(temp_planet_angle_rad)

            mag = calculate_magnification(
                u_source_x=u_x_val,
                u_source_y=u_source_y_impact_parameter,
                u_planet_x=temp_planet_x,
                u_planet_y=temp_planet_y,
                mass_ratio=planet_mass_ratio,
                source_size=source_radius_ratio
            )
            magnifications_curve_animated.append(mag)

        ax_light_curve.plot(u_values_x_curve, magnifications_curve_animated, color='blue', linewidth=2)
        
        ax_light_curve.set_title("배경 별 밝기 변화 (광도 증폭률)")
        ax_light_curve.set_xlabel(f"렌즈-광원 상대 X거리 (아인슈타인 반경의 배수, u_x)")
        ax_light_curve.set_ylabel("광도 증폭률")
        ax_light_curve.grid(True)
        ax_light_curve.set_ylim(bottom=1.0)
        
        current_mag_at_animation_point = calculate_magnification(
            u_source_x=current_u_x_value_for_animation,
            u_source_y=u_source_y_impact_parameter,
            u_planet_x=current_planet_x, 
            u_planet_y=current_planet_y, 
            mass_ratio=planet_mass_ratio,
            source_size=source_radius_ratio
        )
        ax_light_curve.plot([current_u_x_value_for_animation], 
                            [current_mag_at_animation_point], 
                            'ro', markersize=8, label='현재 광원 위치')
        ax_light_curve.legend()
        light_curve_placeholder.pyplot(fig_light_curve)

        progress_bar.progress(i)
        time.sleep(0.05) 

    st.session_state.animating = False 
    st.experimental_rerun() 

# 슬라이더로 직접 조절 시에도 시각화 및 곡선 업데이트
else:
    current_u_index_from_slider = int(animation_progress / 100 * (len(u_values_x_curve) - 1))
    current_u_x_value_from_slider = u_values_x_curve[current_u_index_from_slider]

    current_planet_angle_rad = np.deg2rad(planet_initial_angle_deg + (animation_progress / 100) * 360 / planet_orbital_period_factor)
    current_planet_x = planet_separation_from_lens * np.cos(current_planet_angle_rad)
    current_planet_y = planet_separation_from_lens * np.sin(current_planet_angle_rad)

    update_lensing_visualization(
        current_u_x_value_from_slider, 
        u_source_y_impact_parameter,
        current_planet_x, 
        current_planet_y, 
        ax_lensing
    )
    visualization_placeholder.pyplot(fig_lensing)

    magnifications_curve_static = []
    for u_x_val in u_values_x_curve:
        mag = calculate_magnification(
            u_source_x=u_x_val,
            u_source_y=u_source_y_impact_parameter,
            u_planet_x=current_planet_x, 
            u_planet_y=current_planet_y, 
            mass_ratio=planet_mass_ratio,
            source_size=source_radius_ratio
        )
        magnifications_curve_static.append(mag)

    ax_light_curve.clear()
    ax_light_curve.plot(u_values_x_curve, magnifications_curve_static, color='blue', linewidth=2) 
    
    ax_light_curve.set_title("배경 별 밝기 변화 (광도 증폭률)")
    ax_light_curve.set_xlabel(f"렌즈-광원 상대 X거리 (아인슈타인 반경의 배수, u_x)")
    ax_light_curve.set_ylabel("광도 증폭률")
    ax_light_curve.grid(True)
    ax_light_curve.set_ylim(bottom=1.0)
    
    current_mag_at_slider_point = calculate_magnification(
        u_source_x=current_u_x_value_from_slider,
        u_source_y=u_source_y_impact_parameter,
        u_planet_x=current_planet_x, 
        u_planet_y=current_planet_y, 
        mass_ratio=planet_mass_ratio,
        source_size=source_radius_ratio
    )
    ax_light_curve.plot([current_u_x_value_from_slider], 
                        [current_mag_at_slider_point], 
                        'ro', markersize=8, label='현재 광원 위치')
    ax_light_curve.legend()
    light_curve_placeholder.pyplot(fig_light_curve)

# --- 유효 증폭률 분포: 배경 별 크기의 영향 ---
st.subheader("🌠 유효 증폭률 분포: 배경 별 크기의 영향")
st.write("배경 별의 크기(`source_radius_ratio`)가 단일 렌즈에 의한 밝기 곡선의 최대 증폭률에 어떤 영향을 미치는지 보여줍니다. 배경 별이 커질수록 피크가 뭉툭해지는 것을 볼 수 있습니다.")

fig_effective_mag, ax_effective_mag = plt.subplots(figsize=(8, 4))

# 테스트할 source_radius_ratio 값들
test_source_sizes = [0.001, 0.01, 0.05, 0.1]
colors = ['purple', 'green', 'blue', 'red']
labels = [f'Size: {s:.3f}' for s in test_source_sizes]

# 단일 렌즈의 밝기 곡선을 위한 u 값 범위
u_values_for_effect_mag = np.linspace(-1.0, 1.0, 200)

for i, s_size in enumerate(test_source_sizes):
    magnifications = []
    for u_val in u_values_for_effect_mag:
        # 단일 렌즈의 증폭률만 계산 (행성 효과 배제, u_planet_x=0, u_planet_y=0, mass_ratio=0)
        # calculate_magnification 함수를 재사용하여 단일 렌즈 케이스를 시뮬레이션
        mag = calculate_magnification(
            u_source_x=u_val,
            u_source_y=0.0, # 렌즈 중심 통과 가정
            u_planet_x=0.0,
            u_planet_y=0.0,
            mass_ratio=0.0, # 행성 질량 0으로 설정하여 행성 효과 제거
            source_size=s_size
        )
        magnifications.append(mag)
    ax_effective_mag.plot(u_values_for_effect_mag, magnifications, color=colors[i], label=labels[i])

ax_effective_mag.set_title("배경 별 크기에 따른 단일 렌즈 증폭률")
ax_effective_mag.set_xlabel("렌즈 중심으로부터의 거리 (u)")
ax_effective_mag.set_ylabel("광도 증폭률")
ax_effective_mag.grid(True)
ax_effective_mag.set_ylim(bottom=1.0)
ax_effective_mag.legend()

st.pyplot(fig_effective_mag)

# --- 7. 추가 정보 섹션 ---
st.markdown("---")
st.subheader("🔭 중력 렌즈에 대하여")
st.write("""
**중력 렌즈(Gravitational Lensing)**는 아인슈타인의 일반 상대성 이론에 의해 예측된 현상입니다. 질량을 가진 물체(예: 별, 은하, 블랙홀)가 주변의 시공간을 휘게 만들고, 이 휘어진 시공간을 통과하는 빛의 경로가 마치 렌즈를 통과하는 것처럼 휘어지는 현상입니다. 이는 멀리 떨어진 광원(배경 별)의 이미지를 확대하거나 왜곡시켜 보이는 효과를 줍니다.

**미세 중력 렌즈(Microlensing)**는 렌즈 역할을 하는 천체가 항성이나 비교적 작은 천체(예: 외계 행성)일 때 나타나는 현상입니다. 이 경우, 멀리 떨어진 배경 별의 빛이 렌즈 천체에 의해 일시적으로 밝아지는 **광도 변화**가 발생합니다. 특히 렌즈 별 주위에 외계 행성이 존재하면, 행성의 중력도 빛의 경로에 미세한 영향을 주어 배경 별의 밝기 곡선에 독특한 추가적인 변화(예: '범프' 또는 '딥')를 만들어냅니다. 이러한 미세한 밝기 변화를 분석하여 직접 보기 어려운 외계 행성의 존재를 찾아낼 수 있습니다.


이 시뮬레이션은 중력 렌즈 현상, 특히 외계 행성이 미치는 영향을 개념적으로 보여주기 위해 **매우 단순화된 물리 모델**을 사용합니다. 실제 천문학적 관측 및 이론은 훨씬 더 복잡합니다.
""")

st.subheader("💡 아인슈타인 반경이란?")
st.write("""
**아인슈타인 반경(Einstein Radius)**은 중력 렌즈 현상에서 중요한 물리량이에요. 관측자, 렌즈 별, 그리고 배경 별이 **정확히 일직선상**에 놓였을 때, 렌즈 별의 중력 때문에 배경 별의 빛이 휘어져 우리 눈에는 마치 배경 별이 **완벽한 원형 고리**처럼 보이는 현상이 생겨요. 이 원형 고리를 **아인슈타인 링(Einstein Ring)**이라고 부르는데, 이 고리의 **반경**이 바로 **아인슈타인 반경**입니다.


아인슈타인 반경은 렌즈 별의 **질량**과 **거리**에 따라 달라지며, 중력 렌즈 효과의 '영향권'을 나타내는 척도가 됩니다. 외계 행성을 미세 중력 렌즈로 탐사할 때, 배경 별의 경로가 이 아인슈타인 반경 근처를 지나가야 행성의 서명(밝기 변화)을 포착할 가능성이 높아집니다.
""")
