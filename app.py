import streamlit as st
import pandas as pd

st.set_page_config(page_title="Scholarship Budget Simulator", layout="wide")
st.title("🎓 Scholarship Budget Simulator")
st.markdown("""
This tool helps you **plan scholarship allocations**:
- Enter scholarship amounts and number of students
- Adjust budget and ceiling
- See how many scholarships can be funded
- Explore scenarios interactively
""")

# -------------------------
# 1️⃣ Input: Scholarship costs
# -------------------------
st.subheader("📥 Define Scholarship Costs")
cost_data = st.data_editor(
    pd.DataFrame({
        "scholarship_amount": [500, 800, 1200],
        "number_of_students": [20, 15, 10]
    }),
    num_rows="dynamic",
    use_container_width=True
)

# -------------------------
# 2️⃣ Inputs: Budget & Ceiling
# -------------------------
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

# -------------------------
# 3️⃣ Input: Target scholarships (optional)
# -------------------------
target_scholarships = st.sidebar.number_input(
    "Target number of scholarships (optional)",
    min_value=0,
    value=0,
    step=1
)

# -------------------------
# 4️⃣ Build applications dataframe
# -------------------------
rows = []
for _, row in cost_data.iterrows():
    amt = min(row["scholarship_amount"], ceiling)
    for i in range(int(row["number_of_students"])):
        rows.append({"student_id": f"{amt}_{i+1}", "cost": amt})

df = pd.DataFrame(rows)

if not df.empty:
    df = df.sort_values("cost").reset_index(drop=True)
    df["cumulative_cost"] = df["cost"].cumsum()

    # -------------------------
    # 5️⃣ Calculate allocation
    # -------------------------
    allocated = df[df["cumulative_cost"] <= total_budget]
    num_scholarships = len(allocated)
    total_allocated_cost = allocated["cost"].sum()
    budget_left = total_budget - total_allocated_cost

    # Minimum budget for target
    min_budget_needed = None
    if target_scholarships > 0:
        if target_scholarships > len(df):
            min_budget_needed = "Not enough students"
        else:
            min_budget_needed = int(df.loc[target_scholarships - 1, "cumulative_cost"])

    # -------------------------
    # 6️⃣ Display results
    # -------------------------
    st.subheader("📊 Results")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Budget", f"{total_budget:,}")
    col2.metric("Scholarships Funded", num_scholarships)
    col3.metric("Budget Remaining", f"{budget_left:,}")

    if min_budget_needed:
        st.info(
            f"💡 Minimum budget needed to fund "
            f"{target_scholarships} scholarships: {min_budget_needed:,}"
        )

    st.subheader("🎓 Selected Scholarships")
    st.dataframe(allocated.drop(columns=["cumulative_cost"]))

    # -------------------------
    # 7️⃣ Budget vs Scholarships curve
    # -------------------------
    st.subheader("📈 Budget vs Scholarships")
    max_budget = max(total_budget, int(df["cumulative_cost"].max()))
    step = max(100, max_budget // 50)

    curve = []
    for b in range(0, max_budget + 1, step):
        curve.append({
            "budget": b,
            "scholarships": (df["cumulative_cost"] <= b).sum()
        })

    curve_df = pd.DataFrame(curve)
    st.line_chart(curve_df.set_index("budget"))

else:
    st.warning("Please enter at least one scholarship amount.")
