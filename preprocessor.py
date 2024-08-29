import re

def preprocess_data(scraped_data):
    processed_data = {}
    for page, data in scraped_data.items():
        processed_data[page] = {
            'title': data['title'],
            'description': data['description'],
            'content': anonymize_content(data['content']),
            'address': data['address']
        }
    return processed_data

def anonymize_content(content):
    # 医師名と経歴の匿名化（改良版）
    content = re.sub(r'(理事長|院長|医師|先生|Dr\.?)\s*[\u3000-\u303f\u3040-\u309f\u30a0-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\uff66-\uff9f\s]{1,20}', '[医師名]', content, flags=re.IGNORECASE)
    content = re.sub(r'経歴[:：].*?(?=\n|$)', '経歴: [匿名化された経歴]', content, flags=re.DOTALL)
    return content