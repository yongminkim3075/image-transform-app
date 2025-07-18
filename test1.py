import streamlit as st
import numpy as np
import cv2
from PIL import Image
from io import BytesIO

# ✅ 배경 스타일 (제대로 보이게 수정됨)
st.markdown("""
    <style>
    html, body, .stApp {
        background-image: url("https://images.unsplash.com/photo-1616401789715-6d3d7a5b1dff?ixlib=rb-4.0.3&auto=format&fit=crop&w=1500&q=80");
        background-size: cover;
        background-attachment: fixed;
        background-position: center;
        color: #000000;
    }

    .block-container {
        background-color: rgba(255, 255, 255, 0.85); /* 살짝 흐리게 유지 */
        padding: 2rem;
        border-radius: 15px;
        backdrop-filter: blur(4px); /* 배경 흐림 */
    }
    </style>
""", unsafe_allow_html=True)

# 페이지 설정
st.set_page_config(page_title="행렬 기반 이미지 변형", layout="centered")
st.title("🎨 행렬을 이용한 이미지 변형 실험실")

# 0. 이미지 업로드
uploaded_file = st.file_uploader(
    "📂 여기에 이미지를 끌어다 놓거나 클릭하여 업로드하세요",
    type=["png", "jpg", "jpeg"]
)

if uploaded_file is None:
    st.warning("이미지 파일을 업로드해주세요!")
else:
    image = Image.open(uploaded_file).convert("RGB")
    img_array = np.array(image)
    h, w = img_array.shape[:2]

    # ---------- 원본 이미지 ----------
    st.subheader("🖼️ 원본 이미지")
    st.image(img_array, caption="원본 이미지", use_container_width=True)

    # ---------- 변형 설정 ----------
    st.subheader("🔧 변형 설정")

    col1, col2 = st.columns(2)
    with col1:
        flip_horizontal = st.checkbox("↔️ 좌우 반전", value=False)
        flip_vertical = st.checkbox("🔃 상하 반전", value=False)
        perspective_distortion = st.checkbox("🧭 사다리꼴 왜곡 적용", value=False)
    with col2:
        angle = st.slider("🔄 회전 각도 (°)", -180, 180, step=10, value=0)
        scale = st.slider("🔍 크기 조절 비율", 0.1, 3.0, value=1.0, step=0.1)

    # ---------- 아핀 변환 ----------
    center = (w / 2, h / 2)
    M_rotate = cv2.getRotationMatrix2D(center, -angle, scale)
    transformed_img = cv2.warpAffine(img_array, M_rotate, (w, h))

    if flip_horizontal:
        transformed_img = cv2.flip(transformed_img, 1)
    if flip_vertical:
        transformed_img = cv2.flip(transformed_img, 0)

    # ---------- 사다리꼴 왜곡 ----------
    if perspective_distortion:
        src_pts = np.float32([
            [0, 0],
            [w - 1, 0],
            [0, h - 1],
            [w - 1, h - 1]
        ])
        dst_pts = np.float32([
            [w * 0.1, h * 0.1],
            [w * 0.9, h * 0.05],
            [w * 0.2, h * 0.9],
            [w * 0.8, h * 0.95]
        ])
        M_perspective = cv2.getPerspectiveTransform(src_pts, dst_pts)
        transformed_img = cv2.warpPerspective(transformed_img, M_perspective, (w, h))

    # ---------- 결과 이미지 ----------
    st.subheader("📷 변형된 이미지 결과")
    st.image(transformed_img, caption="변형된 이미지", use_container_width=True)

    # ---------- 다운로드 버튼 ----------
    result_pil = Image.fromarray(transformed_img)
    buf = BytesIO()
    result_pil.save(buf, format="PNG")
    st.download_button(
        label="💾 변형된 이미지 다운로드",
        data=buf.getvalue(),
        file_name="transformed_image.png",
        mime="image/png"
    )

    # ---------- 변환 행렬 ----------
    st.subheader("📐 적용된 변환 행렬")

    st.markdown("**🔄 회전 + 🔍 스케일 행렬 (2x3):**")
    st.code(f"{M_rotate}", language="python")

    if flip_horizontal:
        M_flip_h = np.array([
            [-1, 0, w],
            [0, 1, 0]
        ])
        st.markdown("**↔️ 좌우 반전 행렬 (2x3):**")
        st.code(f"{M_flip_h}", language="python")

    if flip_vertical:
        M_flip_v = np.array([
            [1, 0, 0],
            [0, -1, h]
        ])
        st.markdown("**🔃 상하 반전 행렬 (2x3):**")
        st.code(f"{M_flip_v}", language="python")

    if perspective_distortion:
        st.markdown("**🧭 사다리꼴 왜곡 행렬 (3x3):**")
        st.code(f"{M_perspective}", language="python")

    # ---------- 행렬 설명 ----------
    st.subheader("🧠 행렬 설명 (쉽게 보기)")

    st.markdown("### 🔄 회전 + 스케일")
    st.latex(r"""
    \text{Affine matrix} =
    \begin{bmatrix}
    s \cdot \cos\theta & -s \cdot \sin\theta & t_x \\
    s \cdot \sin\theta &  s \cdot \cos\theta & t_y
    \end{bmatrix}
    """)
    st.markdown("- 중심을 기준으로 회전하고, 크기를 조절하는 변환입니다.")

    st.markdown("### ↔️ 좌우 반전")
    st.latex(r"""
    \begin{bmatrix}
    -1 & 0 & W \\
     0 & 1 & 0
    \end{bmatrix}
    """)
    st.markdown("- x축 기준 반전. 너비(W)만큼 이동시켜 위치 보정.")

    st.markdown("### 🔃 상하 반전")
    st.latex(r"""
    \begin{bmatrix}
    1 & 0 & 0 \\
    0 & -1 & H
    \end{bmatrix}
    """)
    st.markdown("- y축 기준 반전. 높이(H)만큼 이동시켜 위치 보정.")

    st.markdown("### 🧭 사다리꼴 왜곡")
    st.latex(r"""
    \mathbf{x'} = H \cdot \mathbf{x}
    \quad \text{(H는 3x3 투시 변환 행렬)}
    """)
    st.markdown("- 투시 변환을 통해 원근감 있는 왜곡 표현이 가능합니다.")
