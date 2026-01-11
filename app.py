import streamlit as st
import pandas as pd

# --------------------------------------------------
# Page config
# --------------------------------------------------
st.set_page_config(page_title="Scholarship Budget Simulator", layout="wide")
st.title("🎓 Scholarship Budget Simulator")

st.markdown("""
This tool helps you **simulate scholarship allocation strategies**:
- Full or partial scholarships
- Budget ceilings
- Coverage vs generosity trade-offs
""")

# --------------------------------------------------
# 1️⃣ Input: Scholarship costs
# --------------------------------------------------
st.subheader("📥 Define Scholarship Costs")

cost_data = st.data_editor(
    pd.DataFrame({
        "scholarship_amount": [500, 800, 1200],
        "number_of_students": [20, 15, 10]
    }),
    num_rows="dynamic",
    use_container_width=True
)

# --------------------------------------------------
# 2️⃣ Budget & ceiling
# --------------------------------------------------
st.sidebar.header("💰 Budget Settings")

total_budget = st.sidebar.number_input(
    "Total Budget",
    min_value=0,
    value=10000,
    step=100
)

ceiling = st.sidebar.number_input(
    "Maximum per Scholarship",
    min_value=0,
    value=1200,
    step=100
)

# --------------------------------------------------
# 3️⃣ Partial scholarship options
# --------------------------------------------------
st.sidebar.header("🎯 Partial Scholarship Options")

allow_partial = st.sidebar.checkbox(
    "Allow partial scholarships",
    value=False
)

min_base = st.sidebar.number_input(
    "Minimum guaranteed amount",
    min_value=0,
    value=500,
    step=100,
    disabled=not allow_partial
)

if allow_partial and min_base > ceiling:
    st.sidebar.warning(
        "Minimum guaranteed amount exceeds scholarship ceiling. "
        "Base funding will be capped at requested amounts."
    )

# --------------------------------------------------
# 4️⃣ Build student-level dataframe
# --------------------------------------------------
rows = []

for _, row in cost_data.iterrows():
    requested = min(row["scholarship_amount"], ceiling)

    for i in range(int(row["number_of_students"])):
        base_amount = min(requested, min_base) if allow_partial else requested

        rows.append({
            "student_id": f"{requested}_{i+1}",
            "requested": requested,
            "base": base_amount,
            "topup": requested - base_amount,
            "allocated": 0
        })

df = pd.DataFrame(rows)

if df.empty:
    st.warning("Please enter at least one scholarship option.")
    st.stop()

# --------------------------------------------------
# 5️⃣ Allocation logic
# --------------------------------------------------
budget_remaining = total_budget

# Stage 1: Base funding (maximize coverage)
for idx, row in df.iterrows():
    if budget_remaining >= row["base"]:
        df.at[idx, "allocated"] = row["base"]
        budget_remaining -= row["base"]
    else:
        break

# Stage 2: Top-ups (move toward full funding)
if allow_partial:
    topups = df[df["topup"] > 0].sort_values("topup")

    for idx, row in topups.iterrows():
        if budget_remaining >= row["topup"]:
            df.at[idx, "allocated"] += row["topup"]
            budget_remaining -= row["topup"]

# --------------------------------------------------
# 6️⃣ Metrics
# --------------------------------------------------
funded_students = (df["allocated"] > 0).sum()
fully_funded = (df["allocated"] == df["requested"]).sum()
partially_funded = funded_students - fully_funded
total_allocated = df["allocated"].sum()

st.subheader("📊 Results")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Budget", f"{total_budget:,}")
col2.metric("Students Funded", funded_students)
col3.metric("Fully Funded", fully_funded)
col4.metric("Partially Funded", partially_funded)

st.metric("Budget Remaining", f"{budget_remaining:,}")

# --------------------------------------------------
# 7️⃣ Display allocation table
# --------------------------------------------------
st.subheader("🎓 Allocation Details")

display_df = df[df["allocated"] > 0].copy()
display_df["status"] = display_df.apply(
    lambda r: "Full" if r["allocated"] == r["requested"] else "Partial",
    axis=1
)

st.dataframe(
    display_df[
        ["student_id", "requested", "allocated", "status"]
    ],
    use_container_width=True
)

# --------------------------------------------------
# 8️⃣ Budget vs coverage curve (base funding)
# --------------------------------------------------
st.subheader("📈 Budget vs Students Funded")

df_sorted = df.sort_values("base")
df_sorted["cumulative_base"] = df_sorted["base"].cumsum()

curve = []
max_budget = max(total_budget, int(df_sorted["cumulative_base"].max()))
step = max(100, max_budget // 50)

for b in range(0, max_budget + 1, step):
    curve.append({
        "budget": b,
        "students_funded": (df_sorted["cumulative_base"] <= b).sum()
    })

curve_df = pd.DataFrame(curve)
st.line_chart(curve_df.set_index("budget"))
