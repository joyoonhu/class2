
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os

# 폰트 경로
font_path = "NanumGothic.ttf"

try:
    # 폰트를 직접 등록하고 이름 강제 지정
    fm.fontManager.addfont(font_path)
    plt.rc('font', family='NanumGothic')
    plt.rcParams['axes.unicode_minus'] = False

except Exception as e:
    st.error(f"❌ 폰트 적용 실패: {e}")
# 제목
st.title("외계 행성 중력 렌즈 시뮬레이터")

# --- 1. 시뮬레이션 파라미터 설정 ---
st.set_page_config(layout="wide") # 페이지 레이아웃 넓게 설정
st.title("🌌 미세 중력 렌즈 시뮬레이션")
st.write("외계 행성 위치와 렌즈 별 질량을 조절하여 중력 렌즈 효과와 밝기 변화 곡선을 관찰해보세요.")

# 사이드바에서 파라미터 조절
st.sidebar.header("조정 파라미터")

# 외계 행성 위치 조절 (렌즈 별에 대한 상대적인 X축 위치)
# 이 값은 렌즈 별을 기준으로 행성의 횡단면 위치를 결정합니다.
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

# --- 2. 물리 상수 및 기본 설정 ---
# 실제 물리 상수 (SI 단위)
G = 6.67430e-11  # 중력 상수 (m^3 kg^-1 s^-2)
c = 2.99792458e8 # 빛의 속도 (m/s)
M_sun = 1.989e30 # 태양 질량 (kg)

# 천문학적 거리 단위 변환
# 1 파섹(pc) = 3.0857e16 미터
# 1 광년(ly) = 9.461e15 미터
PC_TO_METER = 3.0857e16

# 시뮬레이션에 사용할 거리 파라미터 (예시 값)
# D_L: 관측자-렌즈 거리, D_S: 관측자-광원 거리
# 미세 중력 렌즈에서 일반적으로 사용되는 거리 스케일
D_L = 8000 * PC_TO_METER # 8 kpc (8000 파섹)
D_S = 8500 * PC_TO_METER # 8.5 kpc (8500 파섹)

# 렌즈-광원 거리 (D_LS = D_S - D_L)
D_LS = D_S - D_L

# 렌즈 별 질량 (kg 단위로 변환)
M_lens = lens_mass_solar * M_sun

# 아인슈타인 반경 (각도 단위 - 라디안)
# 이는 렌즈 시스템의 특징적인 스케일입니다.
# θ_E = sqrt(4GM/c^2 * (D_LS / (D_L * D_S)))
einstein_radius_angle = np.sqrt(4 * G * M_lens / (c**2) * D_LS / (D_L * D_S))

# 시각화 목적을 위한 아인슈타인 반경의 '표시' 스케일 (픽셀 또는 임의 단위)
# 이 값은 그림을 그릴 때 스케일링 팩터로 사용됩니다.
R_E_display = 40 # 시각화에서 아인슈타인 반경에 해당하는 픽셀 크기


# --- 3. 중력 렌즈 광도 증폭 계산 함수 ---
def calculate_magnification(u, alpha_planet=0.0, planet_separation=0.1, planet_mass_ratio=1e-3):
    """
    미세 중력 렌즈 광도 증폭률 계산 (두 물체 렌즈 시스템의 단순화된 근사)

    Args:
        u (float or np.array): 배경 별이 렌즈 별 중심으로부터 떨어져 있는 무차원 거리 (충격 매개변수 / 아인슈타인 반경).
                               이 u 값은 시간 경과에 따라 변합니다.
        alpha_planet (float): 외계 행성의 렌즈 별에 대한 상대적인 X축 위치 (아인슈타인 반경의 배수).
        planet_separation (float): 행성과 렌즈 별 사이의 거리 비율 (아인슈타인 반경 기준).
                                   일반적으로 0.1~2.0 사이의 값.
        planet_mass_ratio (float): 행성 질량 / 렌즈 별 질량. (예: 지구/태양 = 3e-6)

    Returns:
        float or np.array: 계산된 광도 증폭률.

    참고: 이 함수는 이진 렌즈(binary lens)의 복잡한 수식을
          매우 단순화하여 행성 영향을 대략적으로 보여줍니다.
          정확한 시뮬레이션을 위해서는 전문적인 렌즈 방정식 해결이 필요합니다.
    """
    
    # 렌즈 별에 의한 기본 증폭 (단일 렌즈 공식)
    u_squared = u**2
    magnification = (u_squared + 2) / (u * np.sqrt(u_squared + 4)) if u > 1e-6 else 1e6 # 0 나눗셈 방지

    # 행성으로 인한 추가 증폭 (간단한 근사)
    # 배경 별이 렌즈 별과 행성 사이의 특별한 영역을 통과할 때 '범프'를 만듭니다.
    # 여기서는 `planet_position` (alpha_planet)이 u 값과 가까울 때 추가적인 영향을 줍니다.
    
    # 행성의 중력 영향 범위 (예: 행성 분리 거리의 일정 비율)
    planet_influence_range = planet_separation * 0.5 
    
    # 배경 별의 경로가 행성 위치 근처를 지날 때 추가 증폭 적용
    if abs(u - alpha_planet) < planet_influence_range:
        # 행성 질량비에 비례하고, 거리에 반비례하는 간단한 형태의 추가 증폭
        additional_magnification = (planet_mass_ratio / (0.01 + abs(u - alpha_planet)**2)) * 1000 
        magnification += additional_magnification

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
# `planet_position`은 아인슈타인 반경의 배수로 해석하여 시각화에 적용
# `planet_position`은 렌즈 별 중심으로부터의 상대적인 횡단면 거리 (u_param과 유사)
planet_display_x = planet_position * R_E_display 
ax_lensing.add_artist(plt.Circle((planet_display_x, 15), 4, color='gray', zorder=6)) # 외계 행성
ax_lensing.text(planet_display_x, 25, '외계 행성', color='white', ha='center', fontsize=10)

# 배경 별 (광원) 그리기 (시뮬레이션에서 고정된 위치 - 관측자 시점에서 렌즈 뒤)
ax_lensing.add_artist(plt.Circle((R_E_display * 0.8, -R_E_display * 0.6), 6, color='white', zorder=4)) # 배경 별 (광원)
ax_lensing.text(R_E_display * 0.8, -R_E_display * 0.75, '배경 별', color='white', ha='center', fontsize=10)

# 아인슈타인 링 시각화 (개념적 표현)
# 렌즈 별을 중심으로 아인슈타인 반경을 시각적으로 나타냅니다.
circle_einstein = plt.Circle((0, 0), R_E_display, color='cyan', linestyle='--', fill=False, alpha=0.5, zorder=3)
ax_lensing.add_artist(circle_einstein)
ax_lensing.text(R_E_display + 5, 0, '아인슈타인 링', color='cyan', va='center', ha='left', fontsize=10)

# 빛의 경로 (개념적, 곡선으로 표현)
# 실제 렌즈 효과는 훨씬 복잡하지만, 여기서는 빛이 휘는 것을 개념적으로 나타냅니다.
light_path_y_offset = R_E_display * 0.7
ax_lensing.plot([-100, -20], [-light_path_y_offset, -light_path_y_offset], color='orange', linestyle='-', linewidth=1)
ax_lensing.plot([20, 100], [-light_path_y_offset, -light_path_y_offset], color='orange', linestyle='-', linewidth=1)
# 렌즈에 의해 굴절되는 부분
ax_lensing.plot([-20, 0, 20], [-light_path_y_offset, -10, -light_path_y_offset], color='orange', linestyle='-', linewidth=1, alpha=0.7)

# 스트림릿에 Matplotlib 그림 표시
st.pyplot(fig_lensing)


# --- 5. 밝기 변화 곡선 ---
st.subheader("밝기 변화 곡선")

# 배경 별의 렌즈 시스템 통과 시간에 따른 상대 거리 (u 값)
# x축은 배경 별이 렌즈 시스템을 횡단할 때 렌즈 중심으로부터의 무차원 거리 u를 나타냅니다.
u_values = np.linspace(-3.0, 3.0, 300) # -3 R_E 에서 3 R_E 까지의 상대 거리

# 각 u 값에 대한 밝기 증폭률 계산
magnifications = []
# 시뮬레이션 상의 행성 분리 거리 (렌즈 별에서 행성까지의 상대 거리)
sim_planet_separation = 0.5 # 아인슈타인 반경의 0.5배 위치에 행성이 있다고 가정 (조절 가능)
sim_planet_mass_ratio = 1e-4 # 행성 질량 / 렌즈 별 질량 비율 (예: 목성 정도의 행성)

for u_val in u_values:
    # calculate_magnification 함수에 현재 u_val과 planet_position을 전달
    mag = calculate_magnification(
        abs(u_val), # u_param은 항상 0에서 양의 값 (중심으로부터의 거리)
        alpha_planet=abs(planet_position), # 슬라이더의 행성 위치 (양수 값만 고려)
        planet_separation=sim_planet_separation,
        planet_mass_ratio=sim_planet_mass_ratio
    )
    magnifications.append(mag)

# Matplotlib으로 밝기 곡선 그리기
fig_light_curve, ax_light_curve = plt.subplots(figsize=(8, 4))
ax_light_curve.plot(u_values, magnifications, color='blue', linewidth=2)
ax_light_curve.set_title("배경 별 밝기 변화 (광도 증폭률)")
ax_light_curve.set_xlabel("렌즈-광원 상대 거리 (아인슈타인 반경의 배수, u)")
ax_light_curve.set_ylabel("광도 증폭률")
ax_light_curve.grid(True)
ax_light_curve.set_ylim(bottom=1.0) # 증폭률은 1 (원래 밝기)보다 작아지지 않음

# 현재 행성 위치에 해당하는 밝기 곡선 상의 위치 표시
# `planet_position` 슬라이더의 값과 `u_values`의 연결을 시각적으로 보여줍니다.
current_u_for_marker = planet_position # 슬라이더 값 그대로 사용
current_mag_at_marker = calculate_magnification(
    abs(current_u_for_marker),
    alpha_planet=abs(planet_position),
    planet_separation=sim_planet_separation,
    planet_mass_ratio=sim_planet_mass_ratio
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
