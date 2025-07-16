
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

# 외계 행성 위치 조절 (상대적인 위치)
# 이 값은 렌즈 별에 대한 행성의 상대적 위치를 결정합니다.
planet_position = st.sidebar.slider(
    "외계 행성 상대 위치 (렌즈 별 기준)",
    min_value=-2.0, max_value=2.0, value=0.0, step=0.05,
    help="렌즈 별에 대한 외계 행성의 상대적인 수평 위치"
)

# 렌즈 별 질량 조절 (태양 질량 단위)
lens_mass_solar = st.sidebar.slider(
    "렌즈 별 질량 (태양 질량)",
    min_value=0.1, max_value=2.0, value=1.0, step=0.1,
    help="빛을 휘게 하는 렌즈 별의 질량"
)

# --- 2. 물리 상수 및 기본 설정 ---
# 실제 물리 상수 (SI 단위)
G = 6.67430e-11  # 중력 상수 (m^3 kg^-1 s^-2)
c = 2.99792458e8 # 빛의 속도 (m/s)
M_sun = 1.989e30 # 태양 질량 (kg)

# 시뮬레이션 스케일 및 거리 설정
# 광년 -> 미터 변환 (1 광년 = 9.461e15 미터)
LIGHT_YEAR = 9.461e15 # 미터

# 관측자-렌즈 거리 (D_L)
D_L = 500 * LIGHT_YEAR # 500 광년

# 관측자-광원 거리 (D_S)
D_S = 1000 * LIGHT_YEAR # 1000 광년

# 렌즈-광원 거리 (D_LS)
D_LS = D_S - D_L

# 렌즈 별 질량 (kg)
M_lens = lens_mass_solar * M_sun

# 아인슈타인 반경 (단위: 라디안)
# 이는 아인슈타인 링이 형성되는 각도 반경을 나타냅니다.
einstein_radius_angle = np.sqrt(4 * G * M_lens / (c**2) * D_LS / (D_L * D_S))

# 시각화 목적을 위한 임의의 픽셀 스케일의 아인슈타인 반경
# 실제 물리적 값(einstein_radius_angle)을 화면에 그릴 때 비율로 사용됩니다.
R_E_display = 50 # 픽셀 또는 임의 단위 (시각화 조절용)


# --- 3. 중력 렌즈 계산 함수 ---
def calculate_magnification(u_param, alpha_planet=0.0, planet_dist_ratio=0.1, planet_mass_ratio=1e-3):
    """
    미세 중력 렌즈 광도 증폭률 계산 (단순화된 모델)
    u_param: 렌즈-광원 간의 상대적 무차원 거리 (충격 매개변수 / 아인슈타인 반경)
    alpha_planet: 행성의 상대적인 충격 매개변수 (행성 위치와 질량에 따라 달라짐)
    planet_dist_ratio: 행성과 렌즈 별 사이의 거리 비율 (아인슈타인 반경 기준)
    planet_mass_ratio: 행성과 렌즈 별의 질량 비율
    """
    
    # 이 부분은 실제 미세 중력 렌즈 이론에 기반한 정확한 수식이 들어가야 합니다.
    # 특히 행성의 영향을 정확히 모델링하려면 이진 렌즈(binary lens) 수식이 필요합니다.
    # 현재는 매우 간단한 형태로 행성 영향을 추가했습니다.

    # 렌즈 별에 의한 기본 증폭
    magnification_main = (u_param**2 + 2) / (u_param * np.sqrt(u_param**2 + 4)) if u_param > 1e-6 else 1e6

    # 행성에 의한 추가 증폭 (매우 단순화된 모델)
    # 행성이 배경 별-렌즈 별 경로에 가까워질 때 추가 증폭을 발생시킴
    # 여기서는 `alpha_planet`과 `planet_dist_ratio`를 사용하여 간단히 모델링
    if abs(u_param - planet_position) < (planet_dist_ratio * R_E_display / R_E_display): # 행성 위치 근처
        # 행성의 질량비에 비례하여 추가 증폭 발생
        magnification_planet_effect = planet_mass_ratio * 50 # 임의의 증폭 계수
        magnification_main += magnification_planet_effect

    return magnification_main


# --- 4. 시스템 시각화 ---
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
planet_display_x = planet_position * (R_E_display * 0.5) # 시각화 스케일 조절
ax_lensing.add_artist(plt.Circle((planet_display_x, 15), 4, color='gray', zorder=6)) # 외계 행성
ax_lensing.text(planet_display_x, 25, '외계 행성', color='white', ha='center', fontsize=10)

# 배경 별 (광원) 그리기 (시뮬레이션에서 고정된 위치)
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

# 배경 별의 렌즈 시스템 통과 시간 (또는 상대적 위치)에 따른 u 값
# x축은 렌즈-광원 간의 상대적 무차원 거리 (아인슈타인 반경의 배수, u)를 나타냅니다.
u_values = np.linspace(-3.0, 3.0, 300) # -3 R_E 에서 3 R_E 까지

# 각 u 값에 대한 밝기 증폭률 계산
magnifications = []
for u_val in u_values:
    # `planet_position` 슬라이더 값을 `calculate_magnification` 함수에 전달하여 행성의 영향을 시뮬레이션
    # 이 부분에서 행성의 정확한 영향을 모델링하는 것이 핵심입니다.
    magnifications.append(calculate_magnification(
        abs(u_val), # u_param은 항상 양수 (중심으로부터의 거리)
        alpha_planet=planet_position # 행성 위치를 alpha_planet으로 전달 (간단화된 모델)
    ))

# Matplotlib으로 밝기 곡선 그리기
fig_light_curve, ax_light_curve = plt.subplots(figsize=(8, 4))
ax_light_curve.plot(u_values, magnifications, color='blue', linewidth=2)
ax_light_curve.set_title("배경 별 밝기 변화 (광도 증폭률)")
ax_light_curve.set_xlabel("렌즈-광원 상대 거리 (아인슈타인 반경의 배수, u)")
ax_light_curve.set_ylabel("광도 증폭률")
ax_light_curve.grid(True)
ax_light_curve.set_ylim(bottom=1.0) # 증폭률은 1 (원래 밝기)보다 작아지지 않음

# 현재 행성 위치에 해당하는 밝기 곡선 상의 위치 표시
# `planet_position`은 x축 `u_values`에 대한 상대적인 위치를 나타냅니다.
# 현재 행성 위치에서의 증폭률을 다시 계산하여 표시
current_mag_at_planet_pos = calculate_magnification(
    abs(planet_position), # 현재 행성 위치에 해당하는 u 값
    alpha_planet=planet_position
)
ax_light_curve.plot([planet_position], [current_mag_at_planet_pos], 'ro', markersize=8) # 붉은 점으로 현재 위치 표시

st.pyplot(fig_light_curve)


# --- 추가 정보 섹션 ---
st.markdown("---")
st.subheader("중력 렌즈에 대하여")
st.write("""
**중력 렌즈(Gravitational Lensing)**는 아인슈타인의 일반 상대성 이론에 의해 예측된 현상으로,
질량을 가진 물체가 시공간을 휘게 하여 그 뒤를 지나는 빛의 경로를 휘게 만드는 현상입니다.
마치 거대한 렌즈처럼 작용하여 멀리 있는 광원의 이미지를 왜곡하거나 증폭시킵니다.

**미세 중력 렌즈(Microlensing)**는 항성이나 작은 천체(행성 등)가 렌즈 역할을 할 때 나타나는 현상으로,
주로 배경 별의 **밝기 변화**로 관측됩니다. 특히 외계 행성을 발견하는 데 중요한 방법으로 사용됩니다.
행성이 렌즈 별 주변을 돌면서 배경 별의 빛을 추가적으로 미세하게 왜곡시켜,
밝기 변화 곡선에 독특한 '범프(bump)'를 만들어냅니다.
""")
