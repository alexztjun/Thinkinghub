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

log("🚀 Thinkinghub 2026 稳定引擎启动...")
API_KEY = os.getenv("GEMINI_API_KEY")
LARK_WEBHOOK = os.getenv("LARK_WEBHOOK")

if not API_KEY or not LARK_WEBHOOK:
    log("❌ 错误：密钥配置缺失")
    sys.exit(1)

# 使用 2026 标准客户端
client = genai.Client(api_key=API_KEY)

def fetch_content(url):
    try:
        res = requests.get(f"https://r.jina.ai/{url}", timeout=25)
        return res.text[:7000]
    except:
        return ""

def main():
    log("📂 读取 38 个顶级信源...")
    with open("sources.yaml", "r", encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    final_reports = []
    
    # 遍历所有 6 个分类，确保每类 1 条，保证信息密度
    for category in config['categories']:
        source = random.choice(category['sources'])
        log(f"🕵️ 正在读取: {source['name']}")
        
        feed = feedparser.parse(source['url'])
        if feed.entries:
            article = feed.entries[0]
            content = fetch_content(article.link)
            
            if content:
                try:
                    # 使用 2026 现代调用语法，彻底避开 404
                    response = client.models.generate_content(
                        model='gemini-1.5-flash',
                        contents=f"你是一位顶级战略情报官。分析文章：{content}。请给出一个极其犀利、反直觉且具备长期主义价值的视角。100字内。"
                    )
                    
                    if response.text:
                        report = f"💡 来自【{category['name']} · {source['name']}】\n**标题**：{article.title}\n{response.text}\n🔗 原文: {article.link}"
                        final_reports.append(report)
                        log(f"✅ 解析成功: {source['name']}")
                except Exception as e:
                    log(f"⚠️ AI 思考中断: {e}")

    if final_reports:
        # 包含关键词 Thinkinghub 确保飞书放行
        full_text = f"Thinkinghub 每日六维智慧报告 (共 {len(final_reports)} 条)：\n\n" + "\n\n---\n\n".join(final_reports)
        requests.post(LARK_WEBHOOK, json={"msg_type": "text", "content": {"text": full_text}})
        log("🎯 报告已送达飞书！")
    else:
        log("📭 本次未生成有效报告。")

if __name__ == "__main__":
    main()
