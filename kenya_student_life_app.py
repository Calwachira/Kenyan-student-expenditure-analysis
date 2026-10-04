"""
Kenyan University Student Life Dashboard
Work-school balance, income, spending and mental wellbeing across 40 universities.

Run:
    pip install streamlit pandas numpy plotly
    streamlit run kenya_student_life_app.py

DATA NOTE: There is no single published dataset covering all 40 universities.
The numbers below are a MODEL built from typical ranges (public vs private,
Nairobi vs town vs rural). Treat them as illustrative estimates. To use real
survey data, upload a CSV in the sidebar (columns listed in REQUIRED_COLS).
"""
import base64
import pathlib

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="USIU-Africa | Kenyan Student Life", page_icon="🎓", layout="wide")
px.defaults.template = "plotly_white"
px.defaults.color_discrete_sequence = ["#0b3d91", "#f4b400", "#0e9aa7", "#e4572e", "#7a5195",
                                       "#2a9d8f", "#8d99ae", "#ef476f", "#118ab2", "#06d6a0"]


def to_data_uri(data: bytes, mime: str) -> str:
    return f"data:{mime};base64,{base64.b64encode(data).decode()}"


def find_background(uploaded, url):
    """Priority: sidebar upload > pasted URL > usiu_background.(jpg|png|webp) next to this script."""
    if uploaded is not None:
        return to_data_uri(uploaded.getvalue(), uploaded.type or "image/jpeg")
    if url.strip():
        return url.strip().replace("'", "%27")
    here = pathlib.Path(__file__).parent
    for ext in ("jpg", "jpeg", "png", "webp"):
        p = here / f"usiu_background.{ext}"
        if p.exists():
            return to_data_uri(p.read_bytes(), f"image/{'jpeg' if ext == 'jpg' else ext}")
    return None


def apply_theme(bg, darkness):
    layer = f"url('{bg}')" if bg else "none"
    st.markdown(f"""
    <style>
    .stApp {{
        background: linear-gradient(135deg, rgba(8,32,80,{darkness}), rgba(14,154,167,{darkness * .6})),
                    {layer} center/cover fixed,
                    linear-gradient(135deg,#0b3d91,#0e9aa7);
    }}
    header[data-testid="stHeader"] {{ background: transparent; }}
    .block-container {{
        background: rgba(255,255,255,.90); backdrop-filter: blur(12px);
        border-radius: 24px; padding: 2rem 2.5rem !important; margin-top: 1rem;
        box-shadow: 0 20px 60px rgba(0,0,0,.35); animation: fade .8s ease;
    }}
    @keyframes fade {{ from {{opacity:0; transform: translateY(14px);}} to {{opacity:1; transform:none;}} }}
    section[data-testid="stSidebar"] {{ background: rgba(255,255,255,.93); backdrop-filter: blur(10px); }}
    .hero {{ background: linear-gradient(120deg,#0b3d91,#0e9aa7); padding: 26px 32px; border-radius: 18px;
             margin-bottom: 18px; border-bottom: 6px solid #f4b400; }}
    .hero h1 {{ color:#fff !important; margin:0; font-size:2.1rem; }}
    .hero p {{ color:#e0f2fe; margin:6px 0 10px; font-size:1.05rem; }}
    .hero span {{ background:#f4b400; color:#1b1b1b; padding:4px 12px; border-radius:999px; font-weight:600; font-size:.85rem; }}
    [data-testid="stMetric"] {{ background: linear-gradient(135deg,#ffffff,#eaf3ff); border-left: 5px solid #f4b400;
        border-radius: 14px; padding: 14px 16px; box-shadow: 0 4px 14px rgba(11,61,145,.12); transition: .25s; }}
    [data-testid="stMetric"]:hover {{ transform: translateY(-5px); box-shadow: 0 10px 24px rgba(11,61,145,.25); }}
    .stTabs [data-baseweb="tab-list"] {{ gap: 6px; flex-wrap: wrap; }}
    .stTabs [data-baseweb="tab"] {{ background:#eef4ff; border-radius: 12px 12px 0 0; padding: 8px 16px; font-weight:600; }}
    .stTabs [aria-selected="true"] {{ background:#0b3d91 !important; color:#fff !important; }}
    </style>""", unsafe_allow_html=True)


def chart(d, cat, title, style):
    if style == "Donut":
        return px.pie(d, names=cat, values="KES", hole=.45, title=title)
    return px.bar(d.sort_values("KES"), x="KES", y=cat, orientation="h", title=title, text_auto=",.0f")


def estimate_stress(work, study, sleep, income, spend, rural=False):
    deficit = max(spend - income, 0) / max(income, 1)
    return float(np.clip(3 + 0.07 * work + 0.05 * (study - 30) + 8 * deficit
                         + 0.4 * (7 - sleep) + (0.6 if rural else 0), 1, 10))


def estimate_balance(stress, work, study, sleep):
    return float(np.clip(100 - 4.2 * stress - 0.8 * max(work + study - 50, 0) + 2 * (sleep - 6), 0, 100))

# (name, type, location tier)
UNIVERSITIES = [
    ("University of Nairobi", "Public", "Nairobi"), ("Kenyatta University", "Public", "Nairobi"),
    ("Moi University", "Public", "Town"), ("Egerton University", "Public", "Town"),
    ("JKUAT", "Public", "Town"), ("Maseno University", "Public", "Town"),
    ("Masinde Muliro (MMUST)", "Public", "Town"), ("Dedan Kimathi (DeKUT)", "Public", "Town"),
    ("Technical University of Kenya", "Public", "Nairobi"), ("Technical University of Mombasa", "Public", "Town"),
    ("Kisii University", "Public", "Town"), ("Chuka University", "Public", "Rural"),
    ("Embu University", "Public", "Rural"), ("University of Eldoret", "Public", "Town"),
    ("Meru University", "Public", "Rural"), ("South Eastern Kenya University", "Public", "Rural"),
    ("Machakos University", "Public", "Town"), ("Kibabii University", "Public", "Rural"),
    ("Laikipia University", "Public", "Rural"), ("Karatina University", "Public", "Rural"),
    ("Multimedia University", "Public", "Nairobi"), ("Pwani University", "Public", "Rural"),
    ("Rongo University", "Public", "Rural"), ("Jaramogi Oginga Odinga (JOOUST)", "Public", "Rural"),
    ("Co-operative University of Kenya", "Public", "Nairobi"),
    ("Strathmore University", "Private", "Nairobi"), ("USIU-Africa", "Private", "Nairobi"),
    ("Daystar University", "Private", "Nairobi"), ("Catholic University of E. Africa", "Private", "Nairobi"),
    ("Mount Kenya University", "Private", "Town"), ("KCA University", "Private", "Nairobi"),
    ("Kabarak University", "Private", "Town"), ("Africa Nazarene University", "Private", "Nairobi"),
    ("Riara University", "Private", "Nairobi"), ("Zetech University", "Private", "Nairobi"),
    ("Kenya Methodist University", "Private", "Town"), ("Pan Africa Christian University", "Private", "Nairobi"),
    ("Gretsa University", "Private", "Town"), ("Great Lakes University of Kisumu", "Private", "Town"),
    ("Management University of Africa", "Private", "Nairobi"),
]

INCOME_SOURCES = ["Family/Parents", "HELB & Bursaries", "Part-time/Gig Work", "Own Business/Hustle", "Other (Scholarship/Internship)"]
SPEND_CATS = ["Rent/Hostel", "Food", "Transport", "Data & Airtime", "Books & Stationery",
              "Personal Care", "Entertainment", "Betting/Gambling", "Savings", "Other"]
REQUIRED_COLS = ["University", "Type", "Location", "Total Income", "Total Spending", "Work Hours", "Study Hours",
                 "Sleep Hours", "Stress Score", "Balance Index"] + INCOME_SOURCES + SPEND_CATS


@st.cache_data
def build_model(seed: int = 254) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    base = {"Public": 14000, "Private": 32000}
    loc_mult = {"Nairobi": 1.15, "Town": 1.0, "Rural": 0.85}
    inc_share = {"Public": [.42, .28, .15, .10, .05], "Private": [.62, .06, .15, .07, .10]}
    spend_share = np.array([.30, .26, .08, .06, .05, .07, .07, .03, .05, .03])
    rows = []
    for name, typ, loc in UNIVERSITIES:
        total_inc = base[typ] * loc_mult[loc] * rng.normal(1, 0.08)
        shares = np.clip(np.array(inc_share[typ]) * rng.normal(1, 0.15, 5), 0.01, None)
        shares /= shares.sum()
        income = dict(zip(INCOME_SOURCES, total_inc * shares))
        spend_total = total_inc * rng.uniform(0.95, 1.08)  # students often spend slightly more than they earn
        s_sh = spend_share * rng.normal(1, 0.12, 10)
        s_sh /= s_sh.sum()
        spend = dict(zip(SPEND_CATS, spend_total * s_sh))
        earn_share = shares[2] + shares[3]
        work = np.clip(5 + 70 * earn_share + rng.normal(0, 2), 2, 30)
        study = np.clip(rng.normal(36 if typ == "Public" else 34, 3), 20, 50)
        sleep = np.clip(7.2 - 0.04 * work - 0.02 * (study - 30) + rng.normal(0, 0.25), 4.5, 8.5)
        deficit = max(spend_total - total_inc, 0) / total_inc
        stress = np.clip(3 + 0.07 * work + 0.05 * (study - 30) + 8 * deficit + 0.4 * (7 - sleep)
                         + (0.6 if loc == "Rural" else 0) + rng.normal(0, 0.4), 1, 10)
        balance = np.clip(100 - 4.2 * stress - 0.8 * max(work + study - 50, 0) + 2 * (sleep - 6) + rng.normal(0, 2), 0, 100)
        rows.append({"University": name, "Type": typ, "Location": loc, "Total Income": total_inc,
                     "Total Spending": spend_total, "Work Hours": work, "Study Hours": study,
                     "Sleep Hours": sleep, "Stress Score": stress, "Balance Index": balance, **income, **spend})
    return pd.DataFrame(rows)


# ---------- Sidebar ----------
st.sidebar.title("🎓 Filters")
up = st.sidebar.file_uploader("Upload real survey CSV (optional)", type="csv")
df = build_model()
if up is not None:
    try:
        custom = pd.read_csv(up)
        missing = [c for c in REQUIRED_COLS if c not in custom.columns]
        if missing:
            st.sidebar.error(f"Missing columns: {', '.join(missing)}")
        else:
            df = custom
            st.sidebar.success("Using your uploaded data")
    except Exception as e:
        st.sidebar.error(f"Could not read file: {e}")

st.sidebar.markdown("### 🖼️ Background")
bg_up = st.sidebar.file_uploader("USIU-Africa photo", type=["jpg", "jpeg", "png", "webp"], key="bg")
bg_url = st.sidebar.text_input("…or image URL", placeholder="https://…")
darkness = st.sidebar.slider("Overlay darkness", 0.2, 0.9, 0.6, 0.05)
apply_theme(find_background(bg_up, bg_url), darkness)

st.sidebar.markdown("### 🎚️ Filters")
types = st.sidebar.multiselect("University type", df["Type"].unique(), default=list(df["Type"].unique()))
locs = st.sidebar.multiselect("Location", df["Location"].unique(), default=list(df["Location"].unique()))
stress_rng = st.sidebar.slider("Stress score range", 1.0, 10.0, (1.0, 10.0), 0.1)
bal_min = st.sidebar.slider("Minimum balance index", 0, 100, 0)
names_all = list(df["University"])
highlight = st.sidebar.selectbox("⭐ Highlight a university", ["None"] + names_all,
                                 index=names_all.index("USIU-Africa") + 1 if "USIU-Africa" in names_all else 0)
view = df[df["Type"].isin(types) & df["Location"].isin(locs)
          & df["Stress Score"].between(*stress_rng) & (df["Balance Index"] >= bal_min)]
if view.empty:
    st.warning("No universities match the filters.")
    st.stop()

# ---------- Header ----------
st.markdown("""<div class="hero"><h1>🇰🇪 Kenyan University Students</h1>
<p>Money · Work · Study · Wellbeing across 40 universities. Hover, click and slide to explore.</p>
<span>Featured: United States International University Africa (USIU-Africa), Nairobi</span></div>""",
            unsafe_allow_html=True)
st.caption("⚠️ Figures are modelled estimates (KES per month), not official survey results. Upload real data in the sidebar to replace them.")

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Avg income / month", f"KES {view['Total Income'].mean():,.0f}")
c2.metric("Avg spending / month", f"KES {view['Total Spending'].mean():,.0f}")
c3.metric("Work hrs / week", f"{view['Work Hours'].mean():.1f}")
c4.metric("Stress (1-10)", f"{view['Stress Score'].mean():.1f}")
c5.metric("Balance index", f"{view['Balance Index'].mean():.0f}/100")

if highlight != "None" and highlight in set(view["University"]):
    h = view[view["University"] == highlight].iloc[0]
    st.markdown(f"#### ⭐ {highlight} vs. selection average")
    h1, h2, h3, h4 = st.columns(4)
    h1.metric("Income", f"KES {h['Total Income']:,.0f}", f"{h['Total Income'] - view['Total Income'].mean():+,.0f}")
    h2.metric("Spending", f"KES {h['Total Spending']:,.0f}", f"{h['Total Spending'] - view['Total Spending'].mean():+,.0f}", delta_color="inverse")
    h3.metric("Work hrs/wk", f"{h['Work Hours']:.1f}", f"{h['Work Hours'] - view['Work Hours'].mean():+.1f}", delta_color="inverse")
    h4.metric("Stress", f"{h['Stress Score']:.1f}", f"{h['Stress Score'] - view['Stress Score'].mean():+.1f}", delta_color="inverse")

tab1, tab2, tab3, tab4, tabw, tabh, tab5 = st.tabs(
    ["💰 Income & Spending", "⚖️ Work-School Balance", "🧠 Mental Health",
     "🏫 Compare / Rank", "🎛️ What-if", "🆚 Head-to-head", "📄 Data"])

with tab1:
    scope = st.selectbox("Show breakdown for", ["All selected universities (average)"] + list(view["University"]))
    src = view if scope.startswith("All") else view[view["University"] == scope]
    style = st.radio("Chart style", ["Donut", "Bar"], horizontal=True)
    a, b = st.columns(2)
    inc = src[INCOME_SOURCES].mean().reset_index()
    inc.columns = ["Source", "KES"]
    a.plotly_chart(chart(inc, "Source", "Where the money comes from", style), width="stretch")
    sp = src[SPEND_CATS].mean().reset_index()
    sp.columns = ["Category", "KES"]
    b.plotly_chart(chart(sp, "Category", "Where the money goes", style), width="stretch")
    gap = view.assign(Gap=view["Total Income"] - view["Total Spending"]).sort_values("Gap")
    st.plotly_chart(px.bar(gap, x="University", y="Gap", color="Type",
                           title="Monthly surplus / deficit (income − spending, KES)"), width="stretch")

with tab2:
    t = view.copy()
    t["Free/Other Hours"] = (168 - t["Work Hours"] - t["Study Hours"] - t["Sleep Hours"] * 7).clip(lower=0)
    sel = st.selectbox("See a week in the life at:", t["University"])
    r = t[t["University"] == sel].iloc[0]
    wk = pd.DataFrame({"Activity": ["Study", "Work", "Sleep", "Other"],
                       "Hours": [r["Study Hours"], r["Work Hours"], r["Sleep Hours"] * 7, r["Free/Other Hours"]]})
    st.plotly_chart(px.pie(wk, names="Activity", values="Hours", title=f"Weekly hours: {sel}"), width="stretch")
    st.plotly_chart(px.scatter(view, x="Work Hours", y="Study Hours", size="Total Income", color="Type",
                               hover_name="University", title="Work vs study hours (bubble = income)"), width="stretch")

with tab3:
    a, b = st.columns(2)
    a.plotly_chart(px.scatter(view, x="Work Hours", y="Stress Score", color="Type", hover_name="University",
                              trendline="ols", title="More work hours → more stress?"), width="stretch")
    b.plotly_chart(px.scatter(view, x="Sleep Hours", y="Balance Index", color="Type", hover_name="University",
                              trendline="ols", title="Sleep vs overall balance"), width="stretch")
    st.info("Stress is modelled from work hours, study load, sleep, money shortfall and rural isolation. "
            "If you or someone you know is struggling, Kenya Red Cross free counselling line: 1199.")

with tab4:
    metric = st.selectbox("Rank by", ["Balance Index", "Stress Score", "Total Income", "Total Spending", "Work Hours", "Sleep Hours"])
    asc = st.checkbox("Ascending", value=metric == "Stress Score")
    rk = view.sort_values(metric, ascending=asc)
    st.plotly_chart(px.bar(rk, x="University", y=metric, color="Type", title=f"Universities ranked by {metric}"),
                    width="stretch")

with tabw:
    st.subheader("🎛️ What-if simulator")
    st.caption("Slide the values to see how a student's routine and money change stress and balance (same formula as the model).")
    c1, c2 = st.columns(2)
    with c1:
        base = st.selectbox("Start from", list(view["University"]), key="wi_base")
        r = view[view["University"] == base].iloc[0]
        work = st.slider("Work hours / week", 0, 40, int(min(r["Work Hours"], 40)), key=f"wk{base}")
        study = st.slider("Study hours / week", 10, 60, int(np.clip(r["Study Hours"], 10, 60)), key=f"st{base}")
        sleep = st.slider("Sleep hours / night", 4.0, 10.0, float(np.clip(round(r["Sleep Hours"], 1), 4, 10)), 0.1, key=f"sl{base}")
        inc_v = st.slider("Monthly income (KES)", 3000, 80000, int(np.clip(r["Total Income"], 3000, 80000)), 500, key=f"in{base}")
        spend_v = st.slider("Monthly spending (KES)", 3000, 80000, int(np.clip(r["Total Spending"], 3000, 80000)), 500, key=f"sp{base}")
    stress = estimate_stress(work, study, sleep, inc_v, spend_v, r["Location"] == "Rural")
    bal = estimate_balance(stress, work, study, sleep)
    with c2:
        g = go.Figure(go.Indicator(
            mode="gauge+number+delta", value=bal, delta={"reference": float(r["Balance Index"])},
            title={"text": "Balance index"},
            gauge={"axis": {"range": [0, 100]}, "bar": {"color": "#0b3d91"},
                   "steps": [{"range": [0, 40], "color": "#fecaca"}, {"range": [40, 70], "color": "#fde68a"},
                             {"range": [70, 100], "color": "#bbf7d0"}]}))
        g.update_layout(height=300, margin=dict(t=60, b=0))
        st.plotly_chart(g, width="stretch")
        m1, m2 = st.columns(2)
        m1.metric("Estimated stress", f"{stress:.1f} / 10")
        m2.metric("Surplus / deficit", f"KES {inc_v - spend_v:,.0f}")
        if 168 - work - study - sleep * 7 < 0:
            st.warning("These hours add up to more than a week!")

with tabh:
    names = list(view["University"])
    x, y = st.columns(2)
    u1 = x.selectbox("University A", names, index=0, key="h1")
    u2 = y.selectbox("University B", names, index=min(1, len(names) - 1), key="h2")
    mets = ["Total Income", "Total Spending", "Work Hours", "Study Hours", "Sleep Hours", "Stress Score", "Balance Index"]
    norm = (df[mets] - df[mets].min()) / (df[mets].max() - df[mets].min())
    norm["University"] = df["University"]
    pick = norm[norm["University"].isin([u1, u2])].melt(id_vars="University", var_name="Metric", value_name="Score")
    fig = px.line_polar(pick, r="Score", theta="Metric", color="University", line_close=True, markers=True,
                        title="Profile comparison (0 = lowest of all 40, 1 = highest)")
    fig.update_traces(fill="toself", opacity=.65)
    st.plotly_chart(fig, width="stretch")
    st.dataframe(view[view["University"].isin([u1, u2])].set_index("University")[mets].T.round(1), width="stretch")

with tab5:
    st.dataframe(view.round(1), width="stretch")
    st.download_button("Download CSV", view.round(1).to_csv(index=False), "kenya_student_data.csv", "text/csv")
