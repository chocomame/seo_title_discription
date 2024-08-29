import streamlit as st
from scraper import scrape_clinic_site
from preprocessor import preprocess_data
from seo_optimizer import generate_seo_proposals

def main():
    st.title("クリニックSEO最適化支援ツール")
    st.markdown("✨更新情報  \n▼ver1.0.0  \nツール作成しました。")
    st.markdown("<font color='red' style='font-size: 13px;line-height:1.5;'>URLにblogが入っている場合は検索対象になりません（膨大な量になる可能性があるため）。<br>そのため、もしも診療案内としてblogを使用されている医院がありましたら、<br>お手数ですが、手動にてご確認をお願いいたします。</font>", unsafe_allow_html=True)
    st.markdown("※必ず、人の確認をいれてください。")
    

    # ユーザー入力
    clinic_url = st.text_input("クリニックサイトのURLを入力してください")
    seo_goal = st.text_area("SEO最適化の目標を入力してください")

    if st.button("分析開始"):
        if clinic_url and seo_goal:
            try:
                # 進捗バーの初期化
                progress_bar = st.progress(0)
                status_text = st.empty()

                # スクレイピング
                scraped_data = scrape_clinic_site(clinic_url, lambda p, m: update_progress(progress_bar, status_text, p, m))
                
                # データ前処理
                update_progress(progress_bar, status_text, 0.7, "データ前処理中...")
                processed_data = preprocess_data(scraped_data)
                
                # SEO最適化提案生成
                update_progress(progress_bar, status_text, 0.8, "SEO最適化提案生成中(GPT-4o-mini)...")
                seo_proposals = generate_seo_proposals(processed_data, seo_goal)
                
                # 結果表示
                update_progress(progress_bar, status_text, 1.0, "完了")
                display_results(seo_proposals)
            except Exception as e:
                st.error(f"エラーが発生しました: {str(e)}")
        else:
            st.error("URLとSEO目標を入力してください。")

def update_progress(progress_bar, status_text, progress, message):
    progress_bar.progress(progress)
    status_text.text(message)

def display_results(seo_proposals):
    st.subheader("SEO最適化提案")
    for page, proposals in seo_proposals.items():
        with st.expander(f"ページ: {page}"):
            st.markdown("### 現在の情報:", unsafe_allow_html=True)
            st.write(f"タイトル: {proposals['current_title']}")
            st.write(f"ディスクリプション: {proposals['current_description']}")
            st.write(f"クリニック所在地: {proposals['clinic_address']}")
            
            st.markdown("### 最適化提案:", unsafe_allow_html=True)
            for i, title in enumerate(proposals['proposed_titles'], 1):
                st.write(f"タイトル案 {i}: {title}")
            for i, desc in enumerate(proposals['proposed_descriptions'], 1):
                st.write(f"ディスクリプション案 {i}: {desc}")

if __name__ == "__main__":
    main()