import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from PIL import Image
import numpy as np
from io import BytesIO

# ---------------- Component Library ---------------- #
COMPONENTS = {
    "LDR": {"image": None, "pins": ["VCC", "GND", "A0", "D0"]},
    "Ultrasonic": {"image": None, "pins": ["VCC", "GND", "TRIG", "ECHO"]}
}

PIN_MAP = {
    "D13": ("right", 0.47), "D12": ("right", 0.51), "D11": ("right", 0.54),
    "D10": ("right", 0.57), "D9": ("right", 0.61), "D8": ("right", 0.64),
    "D7": ("right", 0.70), "D6": ("right", 0.73), "D5": ("right", 0.76),
    "D4": ("right", 0.79), "D3": ("right", 0.83), "D2": ("right", 0.86),
    "TX": ("right", 0.90), "RX": ("right", 0.93),
    "AREF": ("right", 0.41), "GND_R": ("right", 0.44),
    "IOREF": ("left", 0.49), "RESET": ("left", 0.53), "3.3V": ("left", 0.56),
    "5V": ("left", 0.59), "GND1": ("left", 0.63), "GND2": ("left", 0.66),
    "VIN": ("left", 0.69),
    "A0": ("left", 0.76), "A1": ("left", 0.79), "A2": ("left", 0.83),
    "A3": ("left", 0.86), "A4": ("left", 0.89), "A5": ("left", 0.92)
}


def draw_conn(ax, start, end, label, color="red"):
    ax.annotate("", xy=end, xytext=start,
                arrowprops=dict(arrowstyle="->", color=color, lw=2))
    mx, my = (start[0] + end[0]) / 2, (start[1] + end[1]) / 2
    ax.text(mx, my, label, fontsize=9, ha="center", va="center",
            bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.8))
    ax.add_patch(Circle(start, 0.7, color="black", zorder=3))
    ax.add_patch(Circle(end, 0.7, color="green", zorder=3))


def place_and_draw(arduino_img, components):
    if arduino_img is None:
        raise FileNotFoundError("Arduino UNO image not found")

    # Convert PIL image to numpy array
    ar_img = np.array(arduino_img)
    ar_h, ar_w = ar_img.shape[:2]

    total_w, total_h = 100, 100
    margin, left_w, gap, right_w = 5, 40, 10, 40
    left_x0, left_x1 = margin, margin + left_w
    right_x0, right_x1 = left_x1 + gap, left_x1 + gap + right_w

    fig, ax = plt.subplots(figsize=(12, 8))

    # Arduino placement
    ar_target_h = total_h - 2 * margin
    ar_disp_w = ar_target_h * (ar_w / ar_h)
    if ar_disp_w > (left_w - 4):
        scale = (left_w - 4) / ar_disp_w
        ar_target_h *= scale
        ar_disp_w *= scale

    ar_cx = (left_x0 + left_x1) / 2
    ar_x0, ar_x1 = ar_cx - ar_disp_w / 2, ar_cx + ar_disp_w / 2
    ar_y0, ar_y1 = (total_h - ar_target_h) / 2, (total_h - ar_target_h) / 2 + ar_target_h
    ax.imshow(ar_img, extent=[ar_x0, ar_x1, ar_y0, ar_y1], origin='lower', zorder=0)

    # Arduino pins coords
    pin_coords = {}
    for pin, (side, f) in PIN_MAP.items():
        if side == "right":
            pin_coords[pin] = (ar_x1, ar_y0 + (ar_y1 - ar_y0) * f)
        else:
            pin_coords[pin] = (ar_x0, ar_y0 + (ar_y1 - ar_y0) * f)

    # Place components
    spacing, sensor_max_w = 6, right_w - 4
    y_top = total_h - margin
    for idx, (name, user_pins) in enumerate(components):
        img = COMPONENTS[name]["image"]
        if img is None:
            continue

        img_np = np.array(img)
        h, w = img_np.shape[:2]
        disp_w, disp_h = sensor_max_w, sensor_max_w * (h / w)
        y1, y0 = y_top, y_top - disp_h
        cx = (right_x0 + right_x1) / 2
        x0, x1 = cx - disp_w / 2, cx + disp_w / 2
        ax.imshow(img_np, extent=[x0, x1, y0, y1], origin='lower', zorder=1)

        n_pins = len(COMPONENTS[name]["pins"])
        pin_positions = {}
        for i, p in enumerate(COMPONENTS[name]["pins"]):
            py = y0 + (i + 1) / (n_pins + 1) * (y1 - y0)
            px = x0
            if name == "Ultrasonic" and p == "GND":
                px, py = pin_coords["GND1"]
            pin_positions[p] = (px + 2, py + 2)

        for comp_pin in COMPONENTS[name]["pins"]:
            if comp_pin == "VCC":
                draw_conn(ax, pin_positions[comp_pin], pin_coords["5V"], f"{name} VCC → 5V", "red")
            elif comp_pin == "GND":
                draw_conn(ax, pin_positions[comp_pin], pin_coords["GND1"], f"{name} GND → GND", "green")
            elif comp_pin in user_pins:
                ar_pin = user_pins[comp_pin]
                if ar_pin in pin_coords:
                    color = "blue" if comp_pin not in ["ECHO", "TRIG"] else ("orange" if comp_pin == "TRIG" else "purple")
                    draw_conn(ax, pin_positions[comp_pin], pin_coords[ar_pin], f"{name} {comp_pin} → {ar_pin}", color)

        ax.text(cx, y1 + 2, name, ha="center", fontsize=10,
                bbox=dict(facecolor="white", alpha=0.8))
        y_top = y0 - spacing

    ax.text((ar_x0 + ar_x1) / 2, ar_y1 + 3, "Arduino UNO", ha="center",
            fontsize=12, fontweight="bold", bbox=dict(facecolor="white", alpha=0.8))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")
    plt.tight_layout()

    buf = BytesIO()
    plt.savefig(buf, format="png", dpi=200, bbox_inches="tight")
    buf.seek(0)
    return buf


# ---------------- Streamlit UI ---------------- #
st.set_page_config(page_title="CircuitGPT", layout="wide")

st.markdown("""
    <style>
        body { background-color: #f9f9fb; }
        .marquee {
            width: 100%;
            overflow: hidden;
            white-space: nowrap;
            background: linear-gradient(to right, #e0f7fa, #ffffff);
            color: #00796b;
            font-weight: bold;
            font-size: 26px;
            padding: 10px;
        }
    </style>
    <div class="marquee">
        <marquee behavior="scroll" direction="left" scrollamount="6">⚡ CircuitGPT — Visualize Arduino Sensor Connections Instantly ⚡</marquee>
    </div>
""", unsafe_allow_html=True)

st.title("🔌 Circuit Connection Builder")

st.markdown("### 🖼️ Upload Required Images")
arduino_img = st.file_uploader("Upload Arduino UNO image", type=["png", "jpg", "jpeg"])
ldr_img = st.file_uploader("Upload LDR Sensor image", type=["png", "jpg", "jpeg"])
ultra_img = st.file_uploader("Upload Ultrasonic Sensor image", type=["png", "jpg", "jpeg"])

if arduino_img and ldr_img and ultra_img:
    COMPONENTS["LDR"]["image"] = Image.open(ldr_img).convert("RGB")
    COMPONENTS["Ultrasonic"]["image"] = Image.open(ultra_img).convert("RGB")
    arduino_img = Image.open(arduino_img).convert("RGB")
else:
    st.warning("⚠️ Please upload all 3 images before generating the circuit diagram.")
    arduino_img = None

num_components = st.number_input("How many components to attach?", min_value=1, max_value=5, value=1)
components = []
for i in range(num_components):
    st.markdown(f"### Component {i + 1}")
    name = st.selectbox(f"Select component {i + 1}:", list(COMPONENTS.keys()), key=f"name_{i}")
    user_pins = {}
    for pin in COMPONENTS[name]["pins"]:
        if pin in ["VCC", "GND"]:
            continue
        user_pins[pin] = st.text_input(f"Enter Arduino pin for {name} {pin}:", key=f"{name}_{pin}_{i}")
    components.append((name, user_pins))

if st.button("Generate Circuit Diagram ⚙️"):
    try:
        buf = place_and_draw(arduino_img, components)
        st.image(buf, caption="Generated Arduino Circuit", use_container_width=True)
    except Exception as e:
        st.error(f"Error: {e}")
