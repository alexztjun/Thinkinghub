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

log("🚀 Thinkinghub 10条高密度交叉引擎启动...")
API_KEY = os.getenv("GEMINI_API_KEY")
LARK_WEBHOOK = os.getenv("LARK_WEBHOOK")

genai.configure(api_key=API_KEY)

def fetch_content(url):
    try:
        res = requests.get(f"https://r.jina.ai/{url}", timeout=30)
        return res.text[:7000] 
    except:
        return ""

def main():
    with open("sources.yaml", "r", encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    all_articles = []
    # 1. 扫描所有分类，准备基础素材
    for category in config['categories']:
        source = random.choice(category['sources'])
        log(f"正在扫描: {source['name']}")
        feed = feedparser.parse(source['url'])
        if feed.entries:
            article = feed.entries[0]
            content = fetch_content(article.link)
            if content:
                all_articles.append({
                    "cat": category['name'],
                    "src": source['name'],
                    "title": article.title,
                    "content": content,
                    "link": article.link
                })

    if not all_articles:
        log("📭 今日无更新。")
        return

    final_reports = []
    model = genai.GenerativeModel('gemini-1.5-flash')

    # 2. 生成前 6 条：单点深度情报
    log("正在生成单点深度情报...")
    for art in all_articles[:6]:
        prompt = f"分析文章：{art['content']}。请提供一个反常识、具备无限游戏逻辑的视角，80字内。"
        try:
            res = model.generate_content(prompt)
            final_reports.append(f"💡 【{art['cat']} · {art['src']}】\n{res.text}\n🔗 原文: {art['link']}")
        except: continue

    # 3. 生成后 4 条：跨界交叉洞察 (Cross-disciplinary)
    log("正在进行跨界交叉合成...")
    if len(all_articles) >= 2:
        for i in range(4): # 尝试生成4条交叉
            # 随机选两篇完全不同分类的文章进行化学反应
            pair = random.sample(all_articles, 2)
            prompt = f"""
            任务：跨界逻辑合成。
            素材A ({pair[0]['cat']}): {pair[0]['content'][:3000]}
            素材B ({pair[1]['cat']}): {pair[1]['content'][:3000]}
            请寻找这两者之间的深层关联。如何用 A 的逻辑去优化 B 的挑战？提供一个价值投资者视角的穿透性建议。120字内。
            """
            try:
                res = model.generate_content(prompt)
                final_reports.append(f"🔗 【跨界碰撞：{pair[0]['src']} × {pair[1]['src']}】\n{res.text}")
            except: continue

    # 4. 推送到飞书
    if final_reports:
        full_text = f"Thinkinghub 每日 10 条高密度简报 (含交叉洞察)：\n\n" + "\n\n---\n\n".join(final_reports[:10])
        requests.post(LARK_WEBHOOK, json={"msg_type": "text", "content": {"text": full_text}})
        log("🎯 报告已送达！")

if __name__ == "__main__":
    main()
