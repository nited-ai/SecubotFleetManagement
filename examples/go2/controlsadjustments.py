import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# --- Logic ---
def scale_input(input_pct, max_val, alpha, deadzone=0.10):
    output = np.zeros_like(input_pct)
    # Mask for inputs outside the deadzone
    mask = input_pct >= deadzone
    # Map the range [deadzone, 1.0] to [0.0, 1.0]
    normalized_input = (input_pct[mask] - deadzone) / (1.0 - deadzone)
    output[mask] = (normalized_input ** alpha) * max_val
    return output

# --- UI Setup ---
st.set_page_config(page_title="Unitree Go2 Velocity Tuner", layout="wide")
st.title("🦿 Unitree Go2 Speed Curve Tuner")
st.markdown("Adjust the 'Exponantiality' (Alpha) to see how the robot will respond to your stick inputs.")

# Sidebar Controls
st.sidebar.header("Global Settings")
deadzone = st.sidebar.slider("Deadzone (%)", 0, 30, 10) / 100.0

st.sidebar.header("Linear (Forward/Back)")
max_lin = st.sidebar.number_input("Max Linear (m/s)", value=5.0)
alpha_lin = st.sidebar.slider("Linear Alpha", 0.5, 4.0, 1.5, 0.1)

st.sidebar.header("Strafe (Left/Right)")
max_str = st.sidebar.number_input("Max Strafe (m/s)", value=0.6)
alpha_str = st.sidebar.slider("Strafe Alpha", 0.5, 4.0, 1.2, 0.1)

st.sidebar.header("Rotation (Yaw)")
max_yaw = st.sidebar.number_input("Max Rotation (rad/s)", value=3.0)
alpha_yaw = st.sidebar.slider("Rotation Alpha", 0.5, 4.0, 2.5, 0.1)

# --- Plotting ---
input_range = np.linspace(0, 1.0, 100)
fig, ax = plt.subplots(1, 3, figsize=(18, 6))

configs = [
    ("Linear", max_lin, alpha_lin, "m/s", 0),
    ("Strafe", max_str, alpha_str, "m/s", 1),
    ("Rotation", max_yaw, alpha_yaw, "rad/s", 2)
]

for name, v_max, alpha, unit, idx in configs:
    speeds = scale_input(input_range, v_max, alpha, deadzone)
    ax[idx].plot(input_range * 100, speeds, lw=3, color='#00FFAA')
    ax[idx].fill_between(input_range * 100, speeds, alpha=0.2, color='#00FFAA')
    ax[idx].axvline(deadzone * 100, color='red', linestyle='--', label='Deadzone')
    ax[idx].set_title(f"{name} (α={alpha})")
    ax[idx].set_xlabel("Joystick Input (%)")
    ax[idx].set_ylabel(f"Output Velocity ({unit})")
    ax[idx].grid(True, alpha=0.3)

st.pyplot(fig)

# --- Data Table for Quick Reference ---
st.subheader("Reference Table (Output Speeds)")
test_points = np.array([0.1, 0.25, 0.5, 0.75, 1.0])
cols = st.columns(3)

with cols[0]:
    st.write("**Linear**")
    vals = scale_input(test_points, max_lin, alpha_lin, deadzone)
    for p, v in zip(test_points, vals):
        st.text(f"{int(p*100)}% input -> {v:.2f} m/s")

with cols[1]:
    st.write("**Strafe**")
    vals = scale_input(test_points, max_str, alpha_str, deadzone)
    for p, v in zip(test_points, vals):
        st.text(f"{int(p*100)}% input -> {v:.2f} m/s")

with cols[2]:
    st.write("**Rotation**")
    vals = scale_input(test_points, max_yaw, alpha_yaw, deadzone)
    for p, v in zip(test_points, vals):
        st.text(f"{int(p*100)}% input -> {v:.2f} rad/s")