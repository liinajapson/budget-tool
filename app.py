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
        # Cannot fully fund base, stop allocation
        break

# Stage 2: Top-ups (strict: full top-ups only)
if allow_partial:
    topups = df[df["topup"] > 0].sort_values("topup")

    for idx, row in topups.iterrows():
        if budget_remaining >= row["topup"]:
            df.at[idx, "allocated"] += row["topup"]
            budget_remaining -= row["topup"]
        else:
            break  # Stop if budget cannot cover full top-up

# --------------------------------------------------
# 6️⃣ Metrics (corrected)
# --------------------------------------------------
funded_mask = df["allocated"] > 0

funded_students = funded_mask.sum()
fully_funded = (funded_mask & (df["allocated"] == df["requested"])).sum()
partially_funded = (funded_mask & (df["allocated"] < df["requested"])).sum()

# Consistency safeguard
assert funded_students == fully_funded + partially_funded

# --------------------------------------------------
# 7️⃣ Display results
# --------------------------------------------------
st.subheader("📊 Results")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Budget", f"{total_budget:,}")
col2.metric("Students Funded", funded_students)
col3.metric("Fully Funded", fully_funded)
col4.metric("Partially Funded", partially_funded)

st.metric("Budget Remaining", f"{budget_remaining:,}")

# --------------------------------------------------
# 8️⃣ Allocation table
# --------------------------------------------------
st.subheader("🎓 Allocation Details")

display_df = df[funded_mask].copy()
display_df["status"] = display_df.apply(
    lambda r: "Full" if r["allocated"] == r["requested"] else "Partial",
    axis=1
)

st.dataframe(
    display_df[["student_id", "requested", "allocated", "status"]],
    use_container_width=True
)

# --------------------------------------------------
# 9️⃣ Cumulative Coverage Curve (CUSUM)
# --------------------------------------------------
st.subheader("📈 Cumulative Coverage Curve")

# Sort by base funding
curve_df = df.sort_values("base").copy()
curve_df["cum_spend"] = curve_df["base"].cumsum()
curve_df["cum_students"] = range(1, len(curve_df) + 1)

# Limit to realistic budget for display
curve_df = curve_df[curve_df["cum_spend"] <= max(total_budget, curve_df["cum_spend"].max())]

# Plot cumulative curve
st.line_chart(
    curve_df.set_index("cum_spend")["cum_students"]
)
