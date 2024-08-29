import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, unquote
from collections import OrderedDict

def scrape_clinic_site(url, progress_callback):
    base_domain = urlparse(url).netloc
    visited = OrderedDict()  # 訪問済みURLを順序付きで保存
    to_visit = [url]
    scraped_data = {}
    total_pages = 30  # 最大ページ数

    while to_visit and len(scraped_data) < total_pages:
        current_url = to_visit.pop(0)
        normalized_url = normalize_url(current_url)
        
        if normalized_url in visited or not is_same_domain(current_url, base_domain) or is_blog_page(current_url) or is_excluded_file(current_url) or is_news_subpage(current_url):
            continue

        visited[normalized_url] = True

        try:
            response = requests.get(current_url)
            response.raise_for_status()
            
            # エンコーディングを自動検出
            if response.encoding.lower() == 'iso-8859-1':
                response.encoding = response.apparent_encoding
            
            soup = BeautifulSoup(response.text, 'html.parser')

            display_url = get_display_url(current_url)
            # トップページのURLを統一
            if display_url.endswith('/index.html'):
                display_url = display_url[:-10]  # '/index.html'を削除
            
            scraped_data[display_url] = {
                'title': soup.title.string.strip() if soup.title else '',
                'description': extract_description(soup),
                'content': soup.get_text(),
                'address': extract_address(soup)
            }

            # 新しいリンクを追加
            for link in soup.find_all('a', href=True):
                new_url = urljoin(current_url, link['href'])
                normalized_new_url = normalize_url(new_url)
                if normalized_new_url not in visited and is_same_domain(new_url, base_domain) and not is_blog_page(new_url) and not is_excluded_file(new_url) and not is_news_subpage(new_url):
                    to_visit.append(new_url)

            # 進捗状況をコールバック
            progress = min(len(scraped_data) / total_pages, 1.0)
            progress_callback(progress, f"スクレイピング中: {display_url}")

        except requests.RequestException as e:
            progress_callback(progress, f"エラー: {current_url} のスクレイピングに失敗しました - {str(e)}")

    return scraped_data

def extract_description(soup):
    # 大文字小文字を区別せずにdescriptionを検索
    meta_desc = soup.find('meta', attrs={'name': lambda x: x and x.lower() == 'description'})
    if meta_desc and 'content' in meta_desc.attrs:
        return meta_desc['content'].strip()
    return ''

def normalize_url(url):
    # URLを正規化（日本語URLのデコード、フラグメント除去、末尾のスラッシュ統一）
    parsed = urlparse(unquote(url))
    path = parsed.path.rstrip('/')
    if path.endswith('/index.html'):
        path = path[:-10]  # '/index.html'を削除
    path += '/'  # 末尾のスラッシュを統一
    return f"{parsed.scheme}://{parsed.netloc}{path}"

def get_display_url(url):
    # 表示用のURLを生成（日本語URLの場合はデコード、それ以外は元のURL）
    parsed = urlparse(url)
    path = unquote(parsed.path)
    if path != parsed.path:  # パスに日本語が含まれている場合
        return f"{parsed.scheme}://{parsed.netloc}{path}"
    return url

def is_same_domain(url, base_domain):
    return urlparse(url).netloc == base_domain

def is_blog_page(url):
    return 'blog' in url.lower()

def is_excluded_file(url):
    # 除外するファイル拡張子のリスト
    excluded_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.zip', '.rar']
    return any(url.lower().endswith(ext) for ext in excluded_extensions)

def extract_address(soup):
    # クリニックの住所を抽出する処理（実装が必要）
    # 例: 特定のクラスやID、構造に基づいて住所を抽出
    address_element = soup.find('address')  # または適切なセレクタを使用
    return address_element.text.strip() if address_element else "住所抽出済み"

def is_news_subpage(url):
    # ニュースの子ページを判定
    parsed = urlparse(url)
    path = parsed.path.strip('/')
    parts = path.split('/')
    return len(parts) > 1 and parts[0].lower() in ['news', 'topics', 'information'] and len(parts) > 1