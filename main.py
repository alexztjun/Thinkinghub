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

log("🚀 Thinkinghub 10条高密度交叉引擎 (稳健版) 启动...")
API_KEY = os.getenv("GEMINI_API_KEY")
LARK_WEBHOOK = os.getenv("LARK_WEBHOOK")

genai.configure(api_key=API_KEY)

def fetch_content(url):
    try:
        res = requests.get(f"https://r.jina.ai/{url}", timeout=25)
        return res.text[:6000] # 适度缩短长度提高稳定性
    except:
        return ""

def main():
    with open("sources.yaml", "r", encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    all_articles = []
    # 1. 扫描所有分类
    for category in config['categories']:
        # 随机选一个源，防止总是抓同一个
        sources = category['sources']
        random.shuffle(sources)
        for source in sources:
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
                    break # 每个分类抓到一个有内容的就跳出

    if not all_articles:
        log("📭 今日所有信源均无更新内容。")
        return

    final_reports = []
    model = genai.GenerativeModel('gemini-1.5-flash')

    # 2. 生成单点深度情报 (最多6条)
    log(f"正在生成单点深度情报 (共 {len(all_articles)} 篇)...")
    for art in all_articles[:6]:
        prompt = f"分析文章：{art['content']}。请提供一个反常识、具备无限游戏逻辑的视角，80字内。"
        try:
            res = model.generate_content(prompt)
            final_reports.append(f"💡 【{art['cat']} · {art['src']}】\n**{art['title']}**\n{res.text}\n🔗 原文: {art['link']}")
            time.sleep(1) # 稍作停顿，防止API过热
        except Exception as e:
            log(f"单点分析失败: {e}")

    # 3. 生成跨界交叉洞察 (素材充足时生成)
    if len(all_articles) >= 2:
        log("正在进行跨界交叉合成...")
        # 尝试生成的交叉条数取决于素材，最多4条
        num_cross = min(4, len(all_articles))
        for i in range(num_cross):
            pair = random.sample(all_articles, 2)
            prompt = f"跨界合成：\n素材A: {pair[0]['content'][:2500]}\n素材B: {pair[1]['content'][:2500]}\n请寻找两者深层关联，给出一个跨界穿透性建议。100字内。"
            try:
                res = model.generate_content(prompt)
                final_reports.append(f"🔗 【交叉碰撞：{pair[0]['src']} × {pair[1]['src']}】\n{res.text}")
                time.sleep(1)
            except Exception as e:
                log(f"交叉合成失败: {e}")

    # 4. 推送到飞书
    if final_reports:
        # 加入 Thinkinghub 关键词绕过拦截
        full_text = f"Thinkinghub 每日 10 条高密度简报 (含交叉洞察)：\n\n" + "\n\n---\n\n".join(final_reports)
        r = requests.post(LARK_WEBHOOK, json={"msg_type": "text", "content": {"text": full_text}})
        log(f"🎯 报告送达结果: {r.text}")
    else:
        log("📭 遗憾，未能生成有效报告。")

if __name__ == "__main__":
    main()
