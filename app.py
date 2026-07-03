import io
import urllib.parse
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st


from scraper import scrape_live_public_opinions, analyze_sentiment_scores
from database import save_records_to_postgres

st.set_page_config(page_title="Universal OpinionMetric AI Pro", page_icon="🛡️", layout="wide")

bg_color = "#FFFFFF"
card_bg = "#F8FAFC"
accent_cyan = "#0284C7" 
text_main = "#1E293B"

st.markdown(f"""
<style>
    .stApp {{ background-color: {bg_color}; color: {text_main}; }}
    .main-title {{ text-align: center; color: {accent_cyan}; font-size: 42px; font-weight: 800; margin-bottom: 5px; }}
    .sub-title {{ text-align: center; color: #64748B; font-size: 16px; margin-bottom: 30px; }}
    .intel-card {{ background-color: {card_bg}; padding: 20px; border-radius: 12px; border: 1px solid #E2E8F0; margin-bottom: 25px; }}
    .metric-value {{ font-size: 28px; font-weight: bold; color: {accent_cyan}; }}
    .verdict-good {{ color: #16A34A; font-weight: bold; font-size: 18px; }}
    .verdict-improve {{ color: #DC2626; font-weight: bold; font-size: 18px; }}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">🛡️ Universal OpinionMetric AI Pro</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Enterprise Web Scraping & Relational Database Ingestion Architecture</div>', unsafe_allow_html=True)

product_query = st.text_input("🔍 Enter Target Asset or Competitor Name:", placeholder="Type here...")

if product_query:
    with st.spinner("🌐 Fetching live market records..."):
        raw_df = scrape_live_public_opinions(product_query)
        
    if raw_df.empty:
        st.error("❌ Extraction stream timed out or returned empty payloads.")
    else:
        df_analyzed = analyze_sentiment_scores(raw_df)
        
     
        try:
            new_rows = save_records_to_postgres(df_analyzed, product_query)
            if new_rows and new_rows > 0:
                st.sidebar.success(f"💾 Permanently logged {new_rows} entries to PostgreSQL!")
            else:
                st.sidebar.info("ℹ️ Records are up to date. No duplicate entries added.")
        except Exception as db_err:
            st.sidebar.warning(f"Database sync suspended: {db_err}")

        total_reviews = len(df_analyzed)
        counts = df_analyzed['Sentiment_Category'].value_counts()
        pos_p = (counts.get('Positive', 0) / total_reviews) * 100 if total_reviews > 0 else 0
        neg_p = (counts.get('Negative', 0) / total_reviews) * 100 if total_reviews > 0 else 0
        nss_score = pos_p - neg_p
        
        st.markdown(f"## 📦 Intelligence Profile: *{product_query}*")
        
        col1, col2, col3 = st.columns(3)
        col1.markdown(f"<div class='intel-card'>🟢 Recognition Rate<br/><span class='metric-value'>{pos_p:.1f}%</span></div>", unsafe_allow_html=True)
        col2.markdown(f"<div class='intel-card'>📉 Net Sentiment Score<br/><span class='metric-value'>{nss_score:.1f}%</span></div>", unsafe_allow_html=True)
        col3.markdown(f"<div class='intel-card'>📁 Samples Active<br/><span class='metric-value'>{total_reviews} rows</span></div>", unsafe_allow_html=True)

        st.markdown("## 📊 Visual Segmentation Analysis")

    
        fig_bar, ax_bar = plt.subplots(figsize=(12, 4))
        fig_bar.patch.set_facecolor(bg_color)
        ax_bar.set_facecolor(bg_color)
        ax_bar.tick_params(colors='#1E293B', labelsize=9)
        ax_bar.grid(True, color="#E2E8F0", linestyle="--", alpha=0.7)

        sns.countplot(
            data=df_analyzed, x='Channel', hue='Sentiment_Category', ax=ax_bar,
            palette={'Positive': '#16A34A', 'Neutral': '#64748B', 'Negative': '#DC2626'},
            hue_order=['Negative', 'Neutral', 'Positive']
        )
        ax_bar.set_title("Sentiment Inflow Volume Across Channels", fontsize=12, fontweight='bold', color=accent_cyan)
        ax_bar.set_ylabel("Count", fontsize=10, color='#1E293B')
        ax_bar.set_xlabel("Channel Platform", fontsize=10, color='#1E293B')
        ax_bar.legend(facecolor=card_bg, edgecolor="#E2E8F0", labelcolor="#1E293B", fontsize=9)
        st.pyplot(fig_bar)

      
        fig_line, ax_line = plt.subplots(figsize=(12, 4))
        fig_line.patch.set_facecolor(bg_color)
        ax_line.set_facecolor(bg_color)
        ax_line.tick_params(colors='#1E293B', labelsize=9)
        ax_line.grid(True, color="#E2E8F0", linestyle="--", alpha=0.7)

        df_trend_sentiment = df_analyzed.groupby(['Date', 'Sentiment_Category'], observed=False).size().unstack(fill_value=0)
        for col_name in ['Negative', 'Neutral', 'Positive']:
            if col_name not in df_trend_sentiment.columns:
                df_trend_sentiment[col_name] = 0
        df_trend_sentiment = df_trend_sentiment[['Negative', 'Neutral', 'Positive']].sort_index()

        df_trend_sentiment.plot(kind='line', ax=ax_line, marker='o', color=['#DC2626', '#64748B', '#16A34A'], linewidth=2, markersize=5)
        ax_line.set_title("Opinion Velocity Profile (Daily Trend)", fontsize=12, fontweight='bold', color=accent_cyan)
        ax_line.set_xlabel("Timeline Dates", fontsize=10, color='#1E293B')
        ax_line.set_ylabel("Review Volume", fontsize=10, color='#1E293B')
        ax_line.legend(facecolor=card_bg, edgecolor="#E2E8F0", labelcolor="#1E293B", fontsize=9)

        plt.xticks(rotation=45)
        plt.tight_layout()
        st.pyplot(fig_line)

        st.markdown("### 📄 Real-Time Dataset Logs")
        st.dataframe(df_analyzed[['Response_ID', 'Timestamp', 'Channel', 'Region', 'Customer_Feedback', 'Polarity']], use_container_width=True)
        
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_analyzed.to_excel(writer, index=False, sheet_name='Live Analysis')
            
        st.download_button(
            label="📥 Download Dataset to Excel (.xlsx)",
            data=buffer.getvalue(),
            file_name=f"live_metrics_{product_query.replace(' ', '_')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
else:
    st.info("💡 **Welcome to the Live Data Portal:** Enter a product query or brand name above to view dynamic visualizations.")
