import streamlit as st

# Page configuration
st.set_page_config(
    page_title="Local Price AI",
    page_icon="🛍️",
    layout="wide"
)

# Main title
st.title("🛍️ Local Price AI")
st.subheader("Find the best local prices with AI")

st.write(
    "Compare prices from online and local sources, "
    "analyze deals, and get an AI-powered recommendation."
)

st.divider()

# Product input
st.markdown("### 🔎 What are you looking for?")

product = st.text_input(
    "Product name",
    placeholder="Example: iPhone 15 128GB"
)

# Location input
location = st.text_input(
    "📍 Your location",
    placeholder="Example: Hyderabad"
)

# Budget
budget = st.number_input(
    "💰 Maximum budget (₹)",
    min_value=0,
    value=50000,
    step=1000
)

# Search radius
radius = st.selectbox(
    "📍 Search radius",
    ["5 km", "10 km", "25 km", "50 km"]
)

# Preferences
st.markdown("### ⚙️ Your preferences")

col1, col2 = st.columns(2)

with col1:
    condition = st.selectbox(
        "Product condition",
        ["Any", "New", "Used", "Refurbished"]
    )

with col2:
    priority = st.selectbox(
        "What matters most?",
        [
            "Lowest Price",
            "Best Overall Deal",
            "Nearest Store",
            "Best Rating"
        ]
    )

# Search button
st.divider()

if st.button("🚀 Find Best Prices", use_container_width=True):

    if not product:
        st.warning("⚠️ Please enter a product name.")

    elif not location:
        st.warning("⚠️ Please enter your location.")

    else:
        st.success("✅ Search request received!")

        st.write("### 🔍 Search Details")

        st.write(f"**Product:** {product}")
        st.write(f"**Location:** {location}")
        st.write(f"**Budget:** ₹{budget:,}")
        st.write(f"**Radius:** {radius}")
        st.write(f"**Condition:** {condition}")
        st.write(f"**Priority:** {priority}")

        st.info(
            "🤖 Your AI agent will now search multiple sources "
            "and compare the available prices."
        )