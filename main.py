import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# --- 1. 시뮬레이션 파라미터 설정 ---
st.set_page_config(layout="wide") # 페이지 레이아웃 넓게 설정
st.title("🌌 미세 중력 렌즈 시뮬레이션")
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
# 이 값은 행성이 렌즈 별로부터 얼마나 떨어져 있는지 나타냅니다.
planet_separation_from_lens = st.sidebar.slider(
    "행성-렌즈 별 분리 거리 (아인슈타인 반경 대비)",
    min_value=0.5, max_value=2.0, value=1.0, step=0.05,
    help="렌즈 별로부터 행성까지의 거리, 아인슈타인 반경의 배수."
)

# 4. 렌즈와 광원의 상대 속도 (밝기 곡선의 폭에 영향)
# 이 값은 밝기 곡선 이벤트의 지속 시간을 조절하는 데 사용됩니다.
relative_velocity_factor = st.sidebar.slider(
    "렌즈-광원 상대 속도",
    min_value=0.1, max_value=2.0, value=1.0, step=0.1,
    help="밝기 곡선 이벤트의 지속 시간(x축 스케일)에 영향. 값이 클수록 이벤트가 짧아집니다."
)

# 5. 관측자-렌즈 거리 (kpc)
# 이 값은 아인슈타인 반경의 크기에 영향을 줍니다.
observer_lens_distance_kpc = st.sidebar.slider(
    "관측자-렌즈 거리 (kpc)",
    min_value=1.0, max_value=10.0, value=8.0, step=0.1,
    help="관측자부터 렌즈 별까지의 거리 (킬로파섹). 아인슈타인 반경 크기에 영향."
)

# --- 2. 물리 상수 및 기본 설정 ---
# 실제 물리 상수 (SI 단위)
G = 6.67430e-11  # 중력 상수 (m^3 kg^-1 s^-2)
c = 2.99792458e8 # 빛의 속도 (m/s)
M_sun = 1.989e30 # 태양 질량 (kg)

# 천문학적 거리 단위 변환
PC_TO_METER = 3.0857e16 # 1 파섹(pc) = 3.0857e16 미터

# 시뮬레이션에 사용할 거리 파라미터 (사용자 입력 반영)
D_L = observer_lens_distance_kpc * 1000 * PC_TO_METER # kpc를 미터로 변환

# 관측자-광원 거리 (고정 값으로 설정하거나 추가 슬라이더로 조절 가능)
# 여기서는 렌즈가 광원보다 가까이 있다고 가정
D_S = D_L + (500 * PC_TO_METER) # 렌즈보다 500 파섹 뒤에 광원이 있다고 가정

# 렌즈-광원 거리 (D_LS = D_S - D_L)
D_LS = D_S - D_L

# 렌즈 별 질량 (kg 단위로 변환)
M_lens = lens_mass_solar * M_sun

# 아인슈타인 반경 (각도 단위 - 라디안)
einstein_radius_angle = np.sqrt(4 * G * M_lens / (c**2) * D_LS / (D_L * D_S))

# 시각화 목적을 위한 아인슈타인 반경의 '표시' 스케일 (픽셀 또는 임의 단위)
R_E_display = 40 # 시각화에서 아인슈타인 반경에 해당하는 픽셀 크기


# --- 3. 중력 렌즈 광도 증폭 계산 함수 ---
# 이 함수는 단일 렌즈와 행성의 매우 단순화된 상호작용을 모델링합니다.
# 실제 이진 렌즈 광도 곡선은 훨씬 복잡하며, 전문 라이브러리나 수치적 해결이 필요합니다.
def calculate_magnification(u_source, u_planet_x, planet_separation, mass_ratio, source_size):
    """
    미세 중력 렌즈 광도 증폭률 계산 (단순화된 근사)

    Args:
        u_source (float or np.array): 배경 별이 렌즈 중심으로부터 떨어져 있는 무차원 거리 (x축).
                                      아인슈타인 반경 단위.
        u_planet_x (float): 외계 행성의 렌즈 별에 대한 X축 위치 (아인슈타인 반경 단위).
        planet_separation (float): 행성과 렌즈 별 사이의 거리 비율 (아인슈타인 반경 단위).
        mass_ratio (float): 행성 질량 / 렌즈 별 질량.
        source_size (float): 광원 별의 크기 (아인슈타인 반경 대비).

    Returns:
        float or np.array: 계산된 광도 증폭률.
    """
    
    # magnification 변수를 초기화합니다.
    # 이 변수는 함수 내의 모든 실행 경로에서 값을 가질 수 있도록 보장됩니다.
    magnification = 1.0 # 기본 증폭률을 1.0으로 설정 (아무런 렌즈 효과가 없을 때의 밝기)

    # 단일 렌즈에 의한 증폭 (유한한 광원 크기 근사 포함)
    u_squared = u_source**2
    
    # u_source가 0에 매우 가까울 때 무한대 증폭을 피하기 위한 처리
    if u_source < 1e-6: # u_source가 0에 매우 가깝다면 (점 광원 근사)
        if source_size > 0: # 광원 크기가 정의되어 있다면
            # 유한한 광원 크기를 고려한 중앙 증폭 상한
            magnification = (u_squared + 2) / (np.sqrt(u_squared + 4) * source_size)
        else: # source_size가 0이거나 매우 작다면 (거의 점 광원)
            magnification = 1e6 # 임의의 큰 값으로 설정 (무한대 발산 근사)
    else:
        magnification = (u_squared + 2) / (u_source * np.sqrt(u_squared + 4))

    # 과도한 증폭 방지 (시뮬레이션 안정성 목적)
    if magnification > 1e4: # 너무 큰 값 방지
        magnification = 1e4


    # 행성으로 인한 추가 증폭 (매우 단순화된 모델)
    # 이 모델은 실제 물리 현상을 정확히 반영하지 않으며, 개념적 이해를 돕기 위함입니다.
    # 실제 이진 렌즈 곡선을 위해서는 전문적인 렌즈 방정식 해결이 필요합니다.
    
    # 행성 중력의 영향이 미치는 범위 (아인슈타인 반경 대비)
    influence_radius = 0.05 + mass_ratio * 50 # 질량이 클수록 영향 범위 증가

    # 배경 별이 행성의 '영향권'에 들어왔을 때 추가 증폭 적용
    effective_dist_to_planet_feature = abs(u_source - u_planet_x)
    
    # 이 조건은 배경별이 행성 위치(u_planet_x)에 가까이 있을 때만 행성 효과를 적용합니다.
    if effective_dist_to_planet_feature < influence_radius: 
        # 행성 질량비와 거리에 반비례하는 추가 증폭
        denom_planet = (0.001 + effective_dist_to_planet_feature**2) # 0 나눗셈 방지
        additional_mag_from_planet = (mass_ratio / denom_planet) * 500 # 증폭 계수 조정
        magnification += additional_mag_from_planet

    return magnification


# --- 4. 중력 렌즈 시스템 시각화 ---
st.subheader("시스템 시각화")

# Matplotlib figure와 axes 생성
fig_lensing, ax_lensing = plt.subplots(figsize=(8, 5))
ax_lensing.set_facecolor('black') # 우주 배경
ax_lensing.set_xlim(-100, 100)
ax_lensing.set_ylim(-100, 100)
ax_lensing.set_aspect('equal') # X, Y 축 비율 동일하게 설정
ax_lensing.axis('off') # 축 숨기기

# 렌즈 별 그리기 (중앙에 위치)
ax_lensing.add_artist(plt.Circle((0, 0), 10, color='yellow', zorder=5)) # 렌즈 별
ax_lensing.text(0, -15, '렌즈 별', color='white', ha='center', fontsize=10)

# 외계 행성 그리기 (렌즈 별 주위에 위치, planet_position 슬라이더 값 반영)
planet_display_x = planet_position * R_E_display 
planet_display_y = planet_separation_from_lens * 15 # 행성이 렌즈 별로부터의 거리 시각화에 반영
ax_lensing.add_artist(plt.Circle((planet_display_x, planet_display_y), 4, color='gray', zorder=6)) # 외계 행성
ax_lensing.text(planet_display_x, planet_display_y + 10, '외계 행성', color='white', ha='center', fontsize=10)

# 배경 별 (광원) 그리기 (시뮬레이션에서 고정된 위치 - 관측자 시점에서 렌즈 뒤)
source_display_radius = source_radius_ratio * R_E_display * 5 # 시각화 스케일 조정
ax_lensing.add_artist(plt.Circle((R_E_display * 0.8, -R_E_display * 0.6), source_display_radius, color='white', zorder=4)) # 배경 별 (광원)
ax_lensing.text(R_E_display * 0.8, -R_E_display * 0.75, '배경 별', color='white', ha='center', fontsize=10)

# 아인슈타인 링 시각화 (개념적 표현)
circle_einstein = plt.Circle((0, 0), R_E_display, color='cyan', linestyle='--', fill=False, alpha=0.5, zorder=3)
ax_lensing.add_artist(circle_einstein)
ax_lensing.text(R_E_display + 5, 0, '아인슈타인 링', color='cyan', va='center', ha='left', fontsize=10)

# 빛의 경로 (개념적, 곡선으로 표현)
light_path_y_offset = R_E_display * 0.7
ax_lensing.plot([-100, -20], [-light_path_y_offset, -light_path_y_offset], color='orange', linestyle='-', linewidth=1)
ax_lensing.plot([20, 100], [-light_path_y_offset, -light_path_y_offset], color='orange', linestyle='-', linewidth=1)
ax_lensing.plot([-20, 0, 20], [-light_path_y_offset, -10, -light_path_y_offset], color='orange', linestyle='-', linewidth=1, alpha=0.7)

# 스트림릿에 Matplotlib 그림 표시
st.pyplot(fig_lensing)


# --- 5. 밝기 변화 곡선 ---
st.subheader("밝기 변화 곡선")

# 배경 별의 렌즈 시스템 횡단 경로 (X축: 렌즈-광원 상대 거리 u)
# 상대 속도에 따라 x축 범위 조절 (이벤트 지속 시간 조절)
u_min = -3.0 * relative_velocity_factor
u_max = 3.0 * relative_velocity_factor
u_values = np.linspace(u_min, u_max, 300) 

# 각 u 값에 대한 밝기 증폭률 계산
magnifications = []
for u_val in u_values:
    # calculate_magnification 함수에 모든 슬라이더 값을 전달
    mag = calculate_magnification(
        u_source=abs(u_val), # 배경 별의 렌즈 중심으로부터의 거리 (양수)
        u_planet_x=abs(planet_position), # 행성 X축 위치 (양수)
        planet_separation=planet_separation_from_lens,
        mass_ratio=planet_mass_ratio,
        source_size=source_radius_ratio
    )
    magnifications.append(mag)

# Matplotlib으로 밝기 곡선 그리기
fig_light_curve, ax_light_curve = plt.subplots(figsize=(8, 4))
ax_light_curve.plot(u_values, magnifications, color='blue', linewidth=2)
ax_light_curve.set_title("배경 별 밝기 변화 (광도 증폭률)")
ax_light_curve.set_xlabel(f"렌즈-광원 상대 거리 (아인슈타인 반경의 배수, u)")
ax_light_curve.set_ylabel("광도 증폭률")
ax_light_curve.grid(True)
ax_light_curve.set_ylim(bottom=1.0) # 증폭률은 1 (원래 밝기)보다 작아지지 않음

# 현재 행성 위치에 해당하는 밝기 곡선 상의 위치 표시
current_u_for_marker = planet_position
current_mag_at_marker = calculate_magnification(
    abs(current_u_for_marker),
    u_planet_x=abs(planet_position),
    planet_separation=planet_separation_from_lens,
    mass_ratio=planet_mass_ratio,
    source_size=source_radius_ratio
)
ax_light_curve.plot([current_u_for_marker], [current_mag_at_marker], 'ro', markersize=8, label='행성 위치') # 붉은 점으로 현재 행성 위치 표시
ax_light_curve.legend()

st.pyplot(fig_light_curve)


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
