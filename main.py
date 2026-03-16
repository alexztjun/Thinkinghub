import os
import requests
import feedparser
import yaml
from google import genai
import random
import sys

def log(msg):
    print(f"--- [LOG]: {msg} ---")
    sys.stdout.flush()

log("🚀 Thinkinghub 2026 现代引擎启动...")
API_KEY = os.getenv("GEMINI_API_KEY")
LARK_WEBHOOK = os.getenv("LARK_WEBHOOK")

if not API_KEY or not LARK_WEBHOOK:
    log("❌ 错误：环境变量缺失")
    sys.exit(1)

# 使用最新的 google-genai 客户端
client = genai.Client(api_key=API_KEY)

def fetch_content(url):
    try:
        res = requests.get(f"https://r.jina.ai/{url}", timeout=30)
        return res.text[:8000] 
    except Exception as e:
        log(f"抓取失败: {e}")
        return ""

def main():
    log("📂 读取 38 个顶级信源清单...")
    with open("sources.yaml", "r", encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    final_reports = []
    # 随机选 4 个源进行思维激荡
    selected_cats = random.sample(config['categories'], 4)
    
    for category in selected_cats:
        source = random.choice(category['sources'])
        log(f"🕵️ 正在从 {source['name']} 搜寻深度观点...")
        
        feed = feedparser.parse(source['url'])
        if feed.entries:
            article = feed.entries[0]
            log(f"📖 发现文章: {article.title}")
            
            content = fetch_content(article.link)
            if content:
                try:
                    # 2026 现代调用语法
                    response = client.models.generate_content(
                        model='gemini-1.5-flash',
                        contents=f"你是一位顶级战略情报官。分析文章：{content}。请给出一个极其犀利、反直觉且能激荡思维的观点。100字内。"
                    )
                    
                    if response.text:
                        report = f"💡 来自【{source['name']}】的思维激荡：\n{response.text}\n🔗 原文: {article.link}"
                        final_reports.append(report)
                        log(f"✅ AI 成功解析: {source['name']}")
                except Exception as e:
                    log(f"⚠️ AI 思考中断: {e}")

    if final_reports:
        full_text = "Thinkinghub 每日思维激荡汇报：\n\n" + "\n\n---\n\n".join(final_reports)
        requests.post(LARK_WEBHOOK, json={"msg_type": "text", "content": {"text": full_text}})
        log("🎯 报告已送达飞书！")
    else:
        log("📭 本次未生成有效报告。")

if __name__ == "__main__":
    main()
