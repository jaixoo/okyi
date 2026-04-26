import streamlit as st
import sqlite3
import pandas as pd

# Connect to the database
conn = sqlite3.connect('cricket_stats.db')

st.set_page_config(page_title="World Cup Stats Tracker", layout="wide")

st.title("🏏 World Cup Player Stats & Analytics")

# --- SHARED HELPER FUNCTIONS ---
def get_profile_label(w, t, l):
    if w == 3: return "🏆 Beat all 3 categories"
    if w == 2 and t == 1: return "⭐ Beat 2 categories, Tied 1 category"
    if w == 2 and l == 1: return "✅ Beat 2 categories, Lost 1 category"
    if w == 1 and t == 2: return "⚠️ Beat 1 category, Tied 2 categories"
    if w == 1 and t == 1 and l == 1: return "⚖️ Beat 1 category, Tied 1, Lost 1 (Tie Case)"
    if w == 0 and t == 3: return "🎯 Tied all 3 categories"
    if w == 0 and t == 2 and l == 1: return "🤏 Tied 2 categories, Lost 1 category"
    return "Other"

def display_styled_results(df, title_prefix):
    if df.empty:
        st.warning(f"No players found matching these criteria for {title_prefix}.")
        return
    df['Result_Profile'] = df.apply(lambda row: get_profile_label(row['WinsA'], row['TiesA'], row['LossesA']), axis=1)
    st.subheader(f"📊 Summary of Milestones ({title_prefix})")
    summary = df['Result_Profile'].value_counts()
    for profile, count in summary.items():
        st.write(f"- {count} records: {profile}")
    st.divider()
    st.subheader("📋 Respective Lists by Category")
    for profile in sorted(df['Result_Profile'].unique(), reverse=True):
        sub_df = df[df['Result_Profile'] == profile].drop(columns=['WinsA', 'TiesA', 'LossesA', 'Result_Profile', 'WinsB', 'TiesB'])
        st.markdown(f"#### {profile} ({len(sub_df)} records)")
        st.dataframe(sub_df, use_container_width=True, hide_index=True)
    st.divider()
    with st.expander("View Full Combined List"):
        st.dataframe(df.drop(columns=['WinsA', 'TiesA', 'LossesA', 'WinsB', 'TiesB']), use_container_width=True)

# --- MAIN TABS ---
tab1, tab2, tab3, tab4 = st.tabs(["Batting Milestones", "Bowling Milestones", "📈 Player Analytics", "👤 Player Details"])

# --- TAB 1: BATTING ---
with tab1:
    st.header("Batting Filter")
    filter_mode_bat = st.radio("Display Mode:", ["Meet Set A Only", "Meet BOTH Set A and Set B"], horizontal=True, key="fmbat")
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Set A (Primary)")
        tr1a, ta1a, ts1a = st.number_input("Min Runs (A)", value=300, key="bat_runs_a"), st.number_input("Min Avg (A)", value=40.0, key="bat_avg_a"), st.number_input("Min SR (A)", value=90.0, key="bat_sr_a")
    with col_b:
        st.subheader("Set B (Secondary)")
        tr1b, ta1b, ts1b = st.number_input("Min Runs (B)", value=500, key="bat_runs_b"), st.number_input("Min Avg (B)", value=50.0, key="bat_avg_b"), st.number_input("Min SR (B)", value=100.0, key="bat_sr_b")
    bat_query = f"WITH Base AS (SELECT Player, Season as Year, Runs, Ave as Average, SR as Strike_Rate, (CASE WHEN Runs > {tr1a} THEN 1 ELSE 0 END + CASE WHEN Ave > {ta1a} THEN 1 ELSE 0 END + CASE WHEN SR > {ts1a} THEN 1 ELSE 0 END) as WinsA, (CASE WHEN Runs = {tr1a} THEN 1 ELSE 0 END + CASE WHEN Ave = {ta1a} THEN 1 ELSE 0 END + CASE WHEN SR = {ts1a} THEN 1 ELSE 0 END) as TiesA, (CASE WHEN Runs < {tr1a} THEN 1 ELSE 0 END + CASE WHEN Ave < {ta1a} THEN 1 ELSE 0 END + CASE WHEN SR < {ts1a} THEN 1 ELSE 0 END) as LossesA, (CASE WHEN Runs > {tr1b} THEN 1 ELSE 0 END + CASE WHEN Ave > {ta1b} THEN 1 ELSE 0 END + CASE WHEN SR > {ts1b} THEN 1 ELSE 0 END) as WinsB, (CASE WHEN Runs = {tr1b} THEN 1 ELSE 0 END + CASE WHEN Ave = {ta1b} THEN 1 ELSE 0 END + CASE WHEN SR = {ts1b} THEN 1 ELSE 0 END) as TiesB FROM batting) SELECT * FROM Base WHERE (WinsA + TiesA) >= 2 {'AND (WinsB + TiesB) >= 2' if 'BOTH' in filter_mode_bat else ''} ORDER BY WinsA DESC, TiesA DESC, Runs DESC"
    display_styled_results(pd.read_sql(bat_query, conn), "Batting")

# --- TAB 2: BOWLING ---
with tab2:
    st.header("Bowling Filter")
    filter_mode_bowl = st.radio("Display Mode:", ["Meet Set A Only", "Meet BOTH Set A and Set B"], horizontal=True, key="fmbowl")
    col_c, col_d = st.columns(2)
