import os
import requests
import feedparser
import yaml
import google.generativeai as genai
import random

# 配置
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
LARK_WEBHOOK = os.getenv("LARK_WEBHOOK")
genai.configure(api_key=GEMINI_KEY)

def fetch_content(url):
    try:
        # 使用 Jina Reader 抓取全文 [cite: 32]
        res = requests.get(f"https://r.jina.ai/{url}", timeout=15)
        return res.text[:6000] 
    except:
        return ""

def main():
    with open("sources.yaml", "r") as f:
        config = yaml.safe_load(f)
    
    final_reports = []
    
    # 从 6 个分类中，每个随机抽取 1 个源，确保风格多样化 [cite: 32]
    for category in config['categories']:
        source = random.choice(category['sources'])
        feed = feedparser.parse(source['url'])
        
        if feed.entries:
            # 选该源最新的一篇 [cite: 32]
            article = feed.entries[0]
            print(f"正在读取 {source['name']}: {article.title}")
            
            content = fetch_content(article.link)
            if not content: continue

            # AI 分析指令：强调思维激荡与独特性
            model = genai.GenerativeModel('gemini-1.5-flash')
            prompt = f"""
            你是一位博学且具有批判性思维的战略情报官。
            请分析这篇文章：{content}
            
            任务要求：
            1. 核心逻辑：用一句话概括作者最独特的观点。
            2. 思想激荡：指出该观点与普通人常识、或传统商业逻辑的“冲突点”在哪里？它能给人带来什么新启发？
            3. 关键事实：列出 2-3 个支撑该观点的硬核事实。
            4. 保持精炼，避免套话。
            """
            
            try:
                response = model.generate_content(prompt)
                report = f"### 💡 [{category['name']}] 来自 {source['name']}\n**标题**：{article.title}\n{response.text}\n\n"
                final_reports.append(report)
            except:
                continue

    # 组合报告并推送到飞书
    if final_reports:
        full_text = "\n---\n".join(final_reports)
        # 飞书格式
        payload = {
            "msg_type": "post",
            "content": {
                "post": {
                    "zh_cn": {
                        "title": "Thinkinghub 每日思维激荡",
                        "content": [[{"tag": "text", "text": full_text}]]
                    }
                }
            }
        }
        requests.post(LARK_WEBHOOK, json=payload)

if __name__ == "__main__":
    main()
