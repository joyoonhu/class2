
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
st.set_page_config(layout="wide")
st.title("🌌 미세 중력 렌즈 시뮬레이션")
st.write("외계 행성 위치와 렌즈 별 질량을 조절하여 중력 렌즈 효과와 밝기 변화 곡선을 관찰해보세요.")

# 사이드바에서 파라미터 조절
st.sidebar.header("조정 파라미터")

# 외계 행성 위치 조절 (상대적인 위치)
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

# --- 이 부분에 D_L, D_S, D_LS 정의 추가 또는 수정 ---
# 시뮬레이션 스케일 (예시 값, 실제 우주 거리에 비례하도록 조정 필요)
# 광년 -> 미터 변환 (1 광년 = 9.461e15 미터)
LIGHT_YEAR = 9.461e15 # 미터

# 관측자-렌즈 거리 (D_L)
D_L = 500 * LIGHT_YEAR # 500 광년 (미터)

# 관측자-광원 거리 (D_S)
D_S = 1000 * LIGHT_YEAR # 1000 광년 (미터)

# 렌즈-광원 거리 (D_LS)
D_LS = D_S - D_L

# 렌즈 별 질량 (kg)
M_lens = lens_mass_solar * M_sun

# 아인슈타인 반경 (각도 또는 거리 단위)
# Theta_E = sqrt(4GM/c^2 * (D_LS / (D_L * D_S)))
einstein_radius_angle = np.sqrt(4 * G * M_lens / (c**2) * D_LS / (D_L * D_S))
# 여기서는 시뮬레이션 상의 임의의 스케일로 변환
R_E = 50 # 픽셀 또는 임의 단위로 아인슈타인 반경 설정 (시각화 목적)


# --- 3. 중력 렌즈 계산 함수 ---
# ... (calculate_magnification 함수는 동일)
def calculate_magnification(u, alpha_planet=0.0):
    u_eff = np.sqrt(u**2 + alpha_planet**2)
    # 0으로 나누는 오류 방지
    if u_eff < 1e-6: # u_eff가 0에 매우 가까울 때 무한대 증폭 방지
        return 1e6 # 임의의 큰 값으로 설정
    return (u_eff**2 + 2) / (u_eff * np.sqrt(u_eff**2 + 4))


# --- 4. 시스템 시각화 ---
st.subheader("시스템 시각화")

fig_lensing, ax_lensing = plt.subplots(figsize=(8, 5))
ax_lensing.set_facecolor('black')
ax_lensing.set_xlim(-100, 100)
ax_lensing.set_ylim(-100, 100)
ax_lensing.set_aspect('equal')
ax_lensing.axis('off')

# 렌즈 별 그리기
ax_lensing.add_artist(plt.Circle((0, 0), 10, color='yellow', zorder=5))
ax_lensing.text(0, -15, '렌즈 별', color='white', ha='center')

# 외계 행성 그리기
planet_display_x = planet_position * R_E * 0.5
ax_lensing.add_artist(plt.Circle((planet_display_x, 15), 4, color='gray', zorder=6))
ax_lensing.text(planet_display_x, 25, '외계 행성', color='white', ha='center')

# 배경 별 (광원) 그리기
ax_lensing.add_artist(plt.Circle((R_E * 0.8, -R_E * 0.6), 6, color='white', zorder=4))
ax_lensing.text(R_E * 0.8, -R_E * 0.75, '배경 별', color='white', ha='center')

# 아인슈타인 링 시각화 (개념적)
circle_einstein = plt.Circle((0, 0), R_E, color='cyan', linestyle='--', fill=False, alpha=0.5, zorder=3)
ax_lensing.add_artist(circle_einstein)
ax_lensing.text(R_E + 5, 0, '아인슈타인 링', color='cyan', va='center', ha='left')

# 빛의 경로 (개념적, 곡선으로 표현)
# ...
light_path_y_offset = R_E * 0.7
ax_lensing.plot([-100, -20], [-light_path_y_offset, -light_path_y_offset], color='orange', linestyle='-', linewidth=1)
ax_lensing.plot([20, 100], [-light_path_y_offset, -light_path_y_offset], color='orange', linestyle='-', linewidth=1)
ax_lensing.plot([-20, 0, 20], [-light_path_y_offset, -10, -light_path_y_offset], color='orange', linestyle='-', linewidth=1, alpha=0.7) # 굴절

st.pyplot(fig_lensing)


# --- 5. 밝기 변화 곡선 ---
st.subheader("밝기 변화 곡선")

u_values = np.linspace(-3.0, 3.0, 300)

magnifications = []
for u_val in u_values:
    # 행성 영향에 따른 밝기 변화 계산
    if abs(u_val - planet_position) < 0.2:
        mag = calculate_magnification(u_val, alpha_planet=0.1)
    else:
        mag = calculate_magnification(u_val, alpha_planet=0.0)
    magnifications.append(mag)

fig_light_curve, ax_light_curve = plt.subplots(figsize=(8, 4))
ax_light_curve.plot(u_values, magnifications, color='blue', linewidth=2)
ax_light_curve.set_title("배경 별 밝기 변화 (광도 증폭률)")
ax_light_curve.set_xlabel("렌즈-광원 상대 거리 (아인슈타인 반경의 배수, u)")
ax_light_curve.set_ylabel("광도 증폭률")
ax_light_curve.grid(True)
ax_light_curve.set_ylim(bottom=1.0)

# 현재 행성 위치에 해당하는 밝기 곡선 상의 위치 표시
current_u = 0
current_mag = calculate_magnification(current_u, alpha_planet=0.0)
ax_light_curve.plot([current_u], [current_mag], 'ro')

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
