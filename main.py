import os
import requests
import feedparser
import yaml
import google.generativeai as genai
import random
import sys

# 强制打印到日志
def log(msg):
    print(f"--- [LOG]: {msg} ---")
    sys.stdout.flush()

# 1. 配置加载
log("正在启动程序...")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
LARK_WEBHOOK = os.getenv("LARK_WEBHOOK")

if not GEMINI_KEY or not LARK_WEBHOOK:
    log("错误：环境变量 GEMINI_API_KEY 或 LARK_WEBHOOK 缺失！")
    sys.exit(1)

genai.configure(api_key=GEMINI_KEY)

def fetch_content(url):
    try:
        res = requests.get(f"https://r.jina.ai/{url}", timeout=20)
        return res.text[:5000]
    except Exception as e:
        log(f"无法抓取链接 {url}: {e}")
        return ""

def main():
    log("正在加载 sources.yaml...")
    try:
        with open("sources.yaml", "r", encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        log(f"读取 sources.yaml 失败: {e}")
        return

    final_reports = []
    # 每次从 6 个分类中随机选 3 个分类来分析，确保思维激荡
    selected_cats = random.sample(config['categories'], 3)
    
    log(f"本次选中的分类：{[c['name'] for c in selected_cats]}")

    for category in selected_cats:
        source = random.choice(category['sources'])
        log(f"正在从 {source['name']} 寻找灵感...")
        
        feed = feedparser.parse(source['url'])
        if feed.entries:
            article = feed.entries[0]
            log(f"找到文章：{article.title}")
            
            content = fetch_content(article.link)
            if content:
                model = genai.GenerativeModel('gemini-1.5-flash')
                # 针对你的需求，要求 AI 提供不同风格的激荡思考
                prompt = f"你是战略情报官。分析文章内容：{content}。请给出一个与众不同的、能激荡思考的视角。100字以内。"
                
                try:
                    response = model.generate_content(prompt)
                    report = f"💡 来自【{source['name']}】的思考：\n{response.text}"
                    final_reports.append(report)
                except Exception as e:
                    log(f"AI 分析失败: {e}")

    # 3. 发送至飞书
    if final_reports:
        # 注意：这里必须包含你在飞书设置的关键词 Thinkinghub
        full_text = "Thinkinghub 每日思维激荡汇报：\n\n" + "\n\n---\n\n".join(final_reports)
        
        payload = {"msg_type": "text", "content": {"text": full_text}}
        log("正在向飞书推送...")
        r = requests.post(LARK_WEBHOOK, json=payload)
        log(f"飞书返回结果: {r.text}")
    else:
        log("本次运行没有生成任何报告。")

# 关键：这个入口必须存在且在最左侧（没有缩进）
if __name__ == "__main__":
    main()
