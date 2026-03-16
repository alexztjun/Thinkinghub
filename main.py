import os
import requests
import feedparser
import yaml
import google.generativeai as genai
import random
import sys
import time

def log(msg):
    print(f"--- [LOG]: {msg} ---")
    sys.stdout.flush()

log("正在启动程序...")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
LARK_WEBHOOK = os.getenv("LARK_WEBHOOK")

if not GEMINI_KEY or not LARK_WEBHOOK:
    log("错误：环境变量缺失！")
    sys.exit(1)

# 配置 Gemini
genai.configure(api_key=GEMINI_KEY)

def fetch_content(url):
    try:
        # 增加超时时间到 30 秒，防止抓取国外网站卡死
        res = requests.get(f"https://r.jina.ai/{url}", timeout=30)
        return res.text[:6000]
    except Exception as e:
        log(f"无法抓取链接: {e}")
        return ""

def main():
    log("加载信源清单...")
    with open("sources.yaml", "r", encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    final_reports = []
    # 随机选 3 个分类，激荡思维
    selected_cats = random.sample(config['categories'], 3)
    
    for category in selected_cats:
        source = random.choice(category['sources'])
        log(f"正在读取 {source['name']} 的最新动态...")
        
        feed = feedparser.parse(source['url'])
        if feed.entries:
            article = feed.entries[0]
            log(f"发现文章: {article.title}")
            
            content = fetch_content(article.link)
            if content:
                # 💡 修复点：使用更标准的模型名称字符串
                model = genai.GenerativeModel(model_name='gemini-1.5-flash')
                
                prompt = f"""
                你是一位博学且具有批判性思维的战略情报官。
                请分析这篇文章：{content}
                任务：提供一个反常识或能激荡思考的视角，100字以内。
                """
                
                try:
                    # 增加一点重试机制
                    response = model.generate_content(prompt)
                    report = f"💡 来自【{source['name']}】的思维碰撞：\n{response.text}\n🔗 原文: {article.link}"
                    final_reports.append(report)
                    log(f"AI 成功生成报告：{source['name']}")
                except Exception as e:
                    log(f"AI 思考失败: {e}")

    # 推送逻辑
    if final_reports:
        # 关键词必须包含 Thinkinghub
        full_text = "Thinkinghub 每日思维激荡汇报：\n\n" + "\n\n---\n\n".join(final_reports)
        payload = {"msg_type": "text", "content": {"text": full_text}}
        
        log("推送至飞书群...")
        r = requests.post(LARK_WEBHOOK, json=payload)
        log(f"飞书回执: {r.text}")
    else:
        log("警告：本次运行未生成有效报告。")

if __name__ == "__main__":
    main()
