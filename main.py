import os
import requests
import feedparser
import yaml
import google.generativeai as genai
import random
import sys

def log(msg):
    print(f"--- [LOG]: {msg} ---")
    sys.stdout.flush()

log("🚀 Thinkinghub 稳固版 6 维引擎启动...")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
LARK_WEBHOOK = os.getenv("LARK_WEBHOOK")

# 1. 基础配置 (使用你之前成功的调用方式)
genai.configure(api_key=GEMINI_KEY)

def fetch_content(url):
    try:
        res = requests.get(f"https://r.jina.ai/{url}", timeout=25)
        return res.text[:6000]
    except:
        return ""

def main():
    log("正在加载 38 个顶级信源清单...")
    with open("sources.yaml", "r", encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    final_reports = []
    
    # 核心逻辑：遍历 6 个分类，每类必选 1 个源，确保高密度
    # 分类包括：Visionaries, Builders, Analysts, Deep Divers, Product Minds, Frontiers
    for category in config['categories']:
        source = random.choice(category['sources'])
        log(f"正在从分类【{category['name']}】读取: {source['name']}")
        
        feed = feedparser.parse(source['url'])
        if feed.entries:
            article = feed.entries[0]
            log(f"发现文章: {article.title}")
            
            content = fetch_content(article.link)
            if content:
                # 使用你之前成功的模型调用方式
                model = genai.GenerativeModel('gemini-1.5-flash')
                prompt = f"你是战略情报官。分析文章：{content}。请提供一个反常识、能激荡思考的视角。100字内。"
                
                try:
                    response = model.generate_content(prompt)
                    if response.text:
                        report = f"💡 来自【{category['name']} · {source['name']}】\n**标题**：{article.title}\n{response.text}\n🔗 原文: {article.link}"
                        final_reports.append(report)
                        log(f"✅ 解析成功: {source['name']}")
                except Exception as e:
                    log(f"AI 思考中断: {e}")

    # 3. 发送至飞书 (包含关键词 Thinkinghub)
    if final_reports:
        full_text = f"Thinkinghub 每日六维智慧报告 (共 {len(final_reports)} 条)：\n\n" + "\n\n---\n\n".join(final_reports)
        payload = {"msg_type": "text", "content": {"text": full_text}}
        requests.post(LARK_WEBHOOK, json=payload)
        log("🎯 报告已成功推送到飞书！")
    else:
        log("📭 本次未生成任何有效报告。")

if __name__ == "__main__":
    main()
