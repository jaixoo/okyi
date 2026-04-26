with col_c:
        st.subheader("Set A (Primary)")
        tw_a, ta_a, te_a = st.number_input("Min Wickets (A)", 15, key="bowl_w_a"), st.number_input("Max Avg (A)", 25.0, key="bowl_a_a"), st.number_input("Max Econ (A)", 5.0, key="bowl_e_a")
    with col_d:
        st.subheader("Set B (Secondary)")
        tw_b, ta_b, te_b = st.number_input("Min Wickets (B)", 20, key="bowl_w_b"), st.number_input("Max Avg (B)", 20.0, key="bowl_a_b"), st.number_input("Max Econ (B)", 4.5, key="bowl_e_b")
    bowl_query = f"WITH Base AS (SELECT Player, Season as Year, Wkts as Wickets, Ave as Average, Econ as Economy, (CASE WHEN Wkts > {tw_a} THEN 1 ELSE 0 END + CASE WHEN Ave < {ta_a} THEN 1 ELSE 0 END + CASE WHEN Econ < {te_a} THEN 1 ELSE 0 END) as WinsA, (CASE WHEN Wkts = {tw_a} THEN 1 ELSE 0 END + CASE WHEN Ave = {ta_a} THEN 1 ELSE 0 END + CASE WHEN Econ = {te_a} THEN 1 ELSE 0 END) as TiesA, (CASE WHEN Wkts < {tw_a} THEN 1 ELSE 0 END + CASE WHEN Ave > {ta_a} THEN 1 ELSE 0 END + CASE WHEN Econ > {te_a} THEN 1 ELSE 0 END) as LossesA, (CASE WHEN Wkts > {tw_b} THEN 1 ELSE 0 END + CASE WHEN Ave < {ta_b} THEN 1 ELSE 0 END + CASE WHEN Econ < {te_b} THEN 1 ELSE 0 END) as WinsB, (CASE WHEN Wkts = {tw_b} THEN 1 ELSE 0 END + CASE WHEN Ave < {ta_b} THEN 1 ELSE 0 END + CASE WHEN Econ < {te_b} THEN 1 ELSE 0 END) as TiesB FROM bowling) SELECT * FROM Base WHERE (WinsA + TiesA) >= 2 {'AND (WinsB + TiesB) >= 2' if 'BOTH' in filter_mode_bowl else ''} ORDER BY WinsA DESC, TiesA DESC, Wickets DESC"
    display_styled_results(pd.read_sql(bowl_query, conn), "Bowling")

# --- TAB 3: ANALYTICS ---
with tab3:
    st.header("📈 Advanced Analytics")
    ana_choice = st.radio("Choose Analysis Type:", ["Career Consistency (Win %)", "Global Season Ranking (Pairwise Percentile)"], horizontal=True)
    if ana_choice == "Career Consistency (Win %)":
        disc_cons = st.radio("Discipline:", ["Batting", "Bowling"], horizontal=True, key="dc")
        c1, c2, c3 = st.columns(3)
        if disc_cons == "Batting":
            r_c, a_c, s_c = c1.number_input("Min Runs", 250, key="c_br"), c2.number_input("Min Avg", 35.0, key="c_ba"), c3.number_input("Min SR", 85.0, key="c_bs")
            q = f"SELECT Player, COUNT(*) as Total, SUM(CASE WHEN ((Runs >= {r_c}) + (Ave >= {a_c}) + (SR >= {s_c})) >= 2 THEN 1 ELSE 0 END) as Successful FROM batting GROUP BY Player HAVING Successful > 0"
        else:
            w_c, av_c, e_c = c1.number_input("Min Wkts", 12, key="c_bw"), c2.number_input("Max Avg", 28.0, key="c_bav"), c3.number_input("Max Econ", 5.5, key="c_be")
            q = f"SELECT Player, COUNT(*) as Total, SUM(CASE WHEN ((Wkts >= {w_c}) + (Ave <= {av_c}) + (Econ <= {e_c})) >= 2 THEN 1 ELSE 0 END) as Successful FROM bowling GROUP BY Player HAVING Successful > 0"
        df_c = pd.read_sql(q, conn)
        df_c['Win %'] = (df_c['Successful'] * 100.0 / df_c['Total']).round(2)
        st.dataframe(df_c.sort_values("Win %", ascending=False), use_container_width=True, hide_index=True)
    else:
        st.subheader("🏆 Global Pairwise Rankings")
        disc_p = st.radio("Discipline:", ["Batting", "Bowling"], horizontal=True, key="dp")
        p_q = f"SELECT A.Player, A.Season, A.Runs, A.Ave, A.SR, (SELECT COUNT(*) FROM batting) as Total_Raw, (SELECT COUNT(*) FROM batting B WHERE ((CASE WHEN A.Runs > B.Runs THEN 1 ELSE 0 END) + (CASE WHEN A.Ave > B.Ave THEN 1 ELSE 0 END) + (CASE WHEN A.SR > B.SR THEN 1 ELSE 0 END)) >= 2) as Win_C, (SELECT COUNT(*) FROM batting B WHERE ((CASE WHEN B.Runs > A.Runs THEN 1 ELSE 0 END) + (CASE WHEN B.Ave > A.Ave THEN 1 ELSE 0 END) + (CASE WHEN B.SR > A.SR THEN 1 ELSE 0 END)) >= 2) as Loss_C, (SELECT COUNT(*) FROM batting B WHERE B.Runs > A.Runs AND B.Ave > A.Ave AND B.SR > A.SR) as Clean_Loss FROM batting A" if disc_p == "Batting" else f"SELECT A.Player, A.Season, A.Wkts, A.Ave, A.Econ, (SELECT COUNT(*) FROM bowling) as Total_Raw, (SELECT COUNT(*) FROM bowling B WHERE ((CASE WHEN A.Wkts > B.Wkts THEN 1 ELSE 0 END) + (CASE WHEN A.Ave < B.Ave THEN 1 ELSE 0 END) + (CASE WHEN A.Econ < B.Econ THEN 1 ELSE 0 END)) >= 2) as Win_C, (SELECT COUNT(*) FROM bowling B WHERE ((CASE WHEN B.Wkts > A.Wkts THEN 1 ELSE 0 END) + (CASE WHEN B.Ave < A.Ave THEN 1 ELSE 0 END) + (CASE WHEN B.Econ < A.Econ THEN 1 ELSE 0 END)) >= 2) as Loss_C, (SELECT COUNT(*) FROM bowling B WHERE B.Wkts > A.Wkts AND B.Ave < A.Ave AND B.Econ < A.Econ) as Clean_Loss FROM bowling A"
        df_p = pd.read_sql(p_q, conn)
        df_p['Total_Opp'] = df_p['Total_Raw'] - 1
        df_p['Tie_C'] = (df_p['Total_Raw'] - df_p['Win_C'] - df_p['Loss_C']) - 1
        def fmt(count, total):
            perc = (count * 100.0 / total) if total > 0 else 0
            return f"{int(count)} ({perc:.1f}%)"
        df_p['Wins (Percentile)'] = df_p.apply(lambda r: fmt(r['Win_C'], r['Total_Opp']), axis=1)
        df_p['Losses'] = df_p.apply(lambda r: fmt(r['Loss_C'], r['Total_Opp']), axis=1)
        df_p['Ties'] = df_p.apply(lambda r: fmt(r['Tie_C'], r['Total_Opp']), axis=1)
        df_p['sort_val'] = df_p['Win_C'] * 100.0 / df_p['Total_Opp']
        f_view = ['Player', 'Season', 'Wins (Percentile)', 'Losses', 'Ties', 'Clean_Loss'] + (['Runs', 'Ave', 'SR'] if disc_p == "Batting" else ['Wkts', 'Ave', 'Econ'])
        st.dataframe(df_p.sort_values("sort_val", ascending=False)[f_view], use_container_width=True, hide_index=True)

# --- TAB 4: PLAYER DETAILS (NEW) ---
with tab4:
    st.header("👤 Player Profile Search")
    st.write("Search for a player to see their full season-by-season global ranking details.")
    
    # Get unique player names for the dropdown
    all_players = sorted(list(set(pd.read_sql("SELECT Player FROM batting", conn)['Player']) | set(pd.read_sql("SELECT Player FROM bowling", conn)['Player'])))
    target_player = st.selectbox("Select or Type Player Name", all_players)

    if target_player:
        # 1. Batting Career
        st.subheader(f"🏏 Batting Career: {target_player}")
        b_prof_q = f"""
            SELECT A.Season, A.Runs, A.Ave, A.SR,
            (SELECT COUNT(*) FROM batting) as Total_Raw,
            (SELECT COUNT(*) FROM batting B WHERE ((CASE WHEN A.Runs > B.Runs THEN 1 ELSE 0 END) + (CASE WHEN A.Ave > B.Ave THEN 1 ELSE 0 END) + (CASE WHEN A.SR > B.SR THEN 1 ELSE 0 END)) >= 2) as Win_C,
            (SELECT COUNT(*) FROM batting B WHERE ((CASE WHEN B.Runs > A.Runs THEN 1 ELSE 0 END) + (CASE WHEN B.Ave > A.Ave THEN 1 ELSE 0 END) + (CASE WHEN B.SR > A.SR THEN 1 ELSE 0 END)) >= 2) as Loss_C,
            (SELECT COUNT(*) FROM batting B WHERE B.Runs > A.Runs AND B.Ave > A.Ave AND B.SR > A.SR) as Clean_Loss
            FROM batting A WHERE A.Player = '{target_player}'
        """
        df_b_prof = pd.read_sql(b_prof_q, conn)
        if not df_b_prof.empty:
            df_b_prof['Total_Opp'] = df_b_prof['Total_Raw'] - 1
            df_b_prof['Tie_C'] = (df_b_prof['Total_Raw'] - df_b_prof['Win_C'] - df_b_prof['Loss_C']) - 1
            df_b_prof['Wins (Percentile)'] = df_b_prof.apply(lambda r: fmt(r['Win_C'], r['Total_Opp']), axis=1)
            df_b_prof['Losses'] = df_b_prof.apply(lambda r: fmt(r['Loss_C'], r['Total_Opp']), axis=1)
            df_b_prof['Ties'] = df_b_prof.apply(lambda r: fmt(r['Tie_C'], r['Total_Opp']), axis=1)
            st.dataframe(df_b_prof[['Season', 'Runs', 'Ave', 'SR', 'Wins (Percentile)', 'Losses', 'Ties', 'Clean_Loss']], use_container_width=True, hide_index=True)
        else:
            st.info("No batting records found for this player.")

        # 2. Bowling Career
        st.subheader(f"⚽ Bowling Career: {target_player}")
        w_prof_q = f"""
            SELECT A.Season, A.Wkts, A.Ave, A.Econ,
            (SELECT COUNT(*) FROM bowling) as Total_Raw,
            (SELECT COUNT(*) FROM bowling B WHERE ((CASE WHEN A.Wkts > B.Wkts THEN 1 ELSE 0 END) + (CASE WHEN A.Ave < B.Ave THEN 1 ELSE 0 END) + (CASE WHEN A.Econ < B.Econ THEN 1 ELSE 0 END)) >= 2) as Win_C,
            (SELECT COUNT(*) FROM bowling B WHERE ((CASE WHEN B.Wkts > A.Wkts THEN 1 ELSE 0 END) + (CASE WHEN B.Ave < A.Ave THEN 1 ELSE 0 END) + (CASE WHEN B.Econ < A.Econ THEN 1 ELSE 0 END)) >= 2) as Loss_C,
            (SELECT COUNT(*) FROM bowling B WHERE B.Wkts > A.Wkts AND B.Ave < A.Ave AND B.Econ <A.Econ) as Clean_Loss
            FROM bowling A WHERE A.Player = '{target_player}'
        """
        df_w_prof = pd.read_sql(w_prof_q, conn)
        if not df_w_prof.empty:
            df_w_prof['Total_Opp'] = df_w_prof['Total_Raw'] - 1
            df_w_prof['Tie_C'] = (df_w_prof['Total_Raw'] - df_w_prof['Win_C'] - df_w_prof['Loss_C']) - 1
            df_w_prof['Wins (Percentile)'] = df_w_prof.apply(lambda r: fmt(r['Win_C'], r['Total_Opp']), axis=1)
            df_w_prof['Losses'] = df_w_prof.apply(lambda r: fmt(r['Loss_C'], r['Total_Opp']), axis=1)
            df_w_prof['Ties'] = df_w_prof.apply(lambda r: fmt(r['Tie_C'], r['Total_Opp']), axis=1)
            st.dataframe(df_w_prof[['Season', 'Wkts', 'Ave', 'Econ', 'Wins (Percentile)', 'Losses', 'Ties', 'Clean_Loss']], use_container_width=True, hide_index=True)
        else:
            st.info("No bowling records found for this player.")

conn.close()
