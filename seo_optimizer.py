from openai import OpenAI
import os
from dotenv import load_dotenv
import re
import time

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_seo_proposals(processed_data, seo_goal):
    seo_proposals = {}
    for page, data in processed_data.items():
        try:
            prompt = create_prompt(data, seo_goal)
            response = call_openai_api_with_retry(prompt)
            parsed_response = parse_response(response, data)
            
            # 回答が不完全な場合、再試行
            if is_incomplete_response(parsed_response):
                print(f"Incomplete response for {page}. Retrying...")
                response = call_openai_api_with_retry(prompt)
                parsed_response = parse_response(response, data)
            
            seo_proposals[page] = parsed_response
        except Exception as e:
            print(f"Error processing page {page}: {str(e)}")
            seo_proposals[page] = {
                'current_title': data.get('title', ''),
                'current_description': data.get('description', ''),
                'clinic_address': data.get('address', ''),
                'proposed_titles': [],
                'proposed_descriptions': []
            }
    return seo_proposals

def call_openai_api_with_retry(prompt, max_retries=1):
    for attempt in range(max_retries + 1):
        try:
            return call_openai_api(prompt)
        except Exception as e:
            if attempt < max_retries:
                print(f"API call failed. Retrying... (Attempt {attempt + 1}/{max_retries + 1})")
                time.sleep(2)  # 2秒待機してから再試行
            else:
                raise e

def is_incomplete_response(parsed_response):
    # 提案されたタイトルまたはディスクリプションが3つ未満の場合、不完全とみなす
    return (len(parsed_response['proposed_titles']) < 3 or 
            len(parsed_response['proposed_descriptions']) < 3)

def create_prompt(data, seo_goal):
    # 住所から市区町村までを抽出
    short_address = extract_city(data['address'])
    
    return f"""
    クリニックのウェブページのSEO最適化を行ってください。以下の情報を考慮してください：

    現在のタイトル: {data['title']}
    現在のディスクリプション: {data['description']}
    クリニック所在地: {short_address}
    SEO目標: {seo_goal}

    ページコンテンツ:
    {data['content'][:2500]}...  # コンテンツの一部のみを使用

    """

def extract_city(address):
    # 住所から市区町村までを抽出する簡易的な関数
    # 注: この正規表現は日本の住所形式を想定しています。必要に応じて調整してください。
    match = re.search(r'(.+?[都道府県])?(.+?[市区町村])', address)
    if match:
        return match.group(0)
    return address  # マッチしない場合は元の住所を返す

def call_openai_api(prompt):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini-2024-07-18",  # または "gpt-4-turbo" など、利用可能なモデルを指定
            messages=[
                {"role": "system", "content": 
    """
    あなたはSEO専門家です。クリニックのウェブサイト最適化を支援します。
    
    タスク:
    1. 最適化されたタイトルを3つ提案してください。
    2. 最適化されたディスクリプションを3つ提案してください。
      - ページコンテンツの内容がある場合は、既存サイトのディスクリプションとページコンテンツを合わせてSEO最適化して出力してください。
      - ページコンテンツの内容がない場合は、既存サイトのディスクリプションをSEO最適化して出力してください。
    3. 各提案には、クリニックの所在地（市区町村まで）を適切に含めてください。ただし、必要な場合のみ含めてください。
    4. ディスクリプションの文章量は多めに書き、説明文を充実させてください。
    """
                },
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": 
    """
    禁止事項：
    1. 万が一、個人情報が入力された場合はタイトルとディスクリプションには絶対含めないでください。
    
    
    タイトルの出力例：
    1. 必ず既存サイトのtitleに書かれているページ名を冒頭に入れること。ページ名は変更しない！
    - 内科｜XXXXXX（SEO最適化されたページのタイトル）
    - お知らせ｜XXXXXX（SEO最適化されたページのタイトル）
    - 医師・クリニック紹介｜XXXXXX（SEO最適化されたページのタイトル）
    - はじめての方へ｜XXXXXX（SEO最適化されたページのタイトル）
    2. indexページの場合は冒頭にサイト名を入れること。
    - まめる医院｜XXXXXX（SEO最適化されたページのタイトル）
    - みえる眼科クリニック｜XXXXXX（SEO最適化されたページのタイトル）
    
    
    ディスクリプションの出力例：
    1. 必ず冒頭に既存サイトのdiscriptionに書かれているページ名を入れること。ページ名は変更しない！
    - 内科。XXXXXX（ページの説明）
    - お知らせ。XXXXXX（ページの説明）
    - 医師・クリニック紹介。XXXXXX（ページの説明）
    - はじめての方へ。XXXXXX（ページの説明）
    2. indexページの場合は冒頭にサイト名を入れること。
    - まめる医院。XXXXXX（ページの説明）
    - みえる眼科クリニック。XXXXXX（ページの説明）
    

    回答は以下の形式で提供してください：
    タイトル案1: [提案]
    タイトル案2: [提案]
    タイトル案3: [提案]
    ディスクリプション案1: [提案]
    ディスクリプション案2: [提案]
    ディスクリプション案3: [提案]
    """
            }
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        raise Exception(f"OpenAI APIの呼び出しに失敗しました: {e}")

def parse_response(response, data):
    # APIレスポンスをパースして構造化されたデータに変換
    lines = response.split('\n')
    proposals = {
        'current_title': data['title'],
        'current_description': data['description'],
        'clinic_address': extract_city(data['address']),  # 市区町村までの住所を使用
        'proposed_titles': [],
        'proposed_descriptions': []
    }

    for line in lines:
        if line.startswith("タイトル案"):
            proposals['proposed_titles'].append(line.split(": ", 1)[1])
        elif line.startswith("ディスクリプション案"):
            proposals['proposed_descriptions'].append(line.split(": ", 1)[1])

    return proposals