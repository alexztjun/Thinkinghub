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

log("🚀 Thinkinghub 引擎强制启动...")
API_KEY = os.getenv("GEMINI_API_KEY")
LARK_WEBHOOK = os.getenv("LARK_WEBHOOK")

if not API_KEY or not LARK_WEBHOOK:
    log("❌ 错误：环境变量缺失，请检查 GitHub Secrets")
    sys.exit(1)

genai.configure(api_key=API_KEY)

def get_ai_response(content):
    # 尝试 3 种不同的模型调用路径，彻底解决 404 问题
    models_to_try = ['gemini-1.5-flash', 'models/gemini-1.5-flash', 'gemini-pro']
    prompt = f"分析文章：{content[:6000]}。请提供一个能激荡思考、反常识的视角，100字内。"
    
    for m_name in models_to_try:
        try:
            log(f"正在尝试模型: {m_name}")
            model = genai.GenerativeModel(m_name)
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            log(f"模型 {m_name} 报错: {str(e)[:50]}")
            continue
    return None

def main():
    log("📂 读取信源清单...")
    with open("sources.yaml", "r", encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    final_reports = []
    # 随机选 4 个源 [cite: 3]
    selected_cats = random.sample(config['categories'], 4)
    
    for category in selected_cats:
        source = random.choice(category['sources'])
        log(f"🕵️ 正在读取: {source['name']}")
        
        feed = feedparser.parse(source['url'])
        if feed.entries:
            article = feed.entries[0]
            log(f"📖 发现文章: {article.title}")
            
            try:
                # 抓取全文
                res = requests.get(f"https://r.jina.ai/{article.link}", timeout=30)
                ai_text = get_ai_response(res.text)
                
                if ai_text:
                    report = f"💡 来自【{source['name']}】的思维激荡：\n{ai_text}\n🔗 原文: {article.link}"
                    final_reports.append(report)
                    log(f"✅ {source['name']} 解析成功")
            except Exception as e:
                log(f"❌ 处理失败: {e}")

    if final_reports:
        # 关键词 Thinkinghub 必须存在以通过飞书校验
        full_text = "Thinkinghub 汇报：\n\n" + "\n\n---\n\n".join(final_reports)
        r = requests.post(LARK_WEBHOOK, json={"msg_type": "text", "content": {"text": full_text}})
        log(f"🎯 飞书回执: {r.text}")
    else:
        log("📭 本次未生成任何有效报告")

if __name__ == "__main__":
    main()
