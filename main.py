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

log("🚀 Thinkinghub 引擎深度自检启动...")
API_KEY = os.getenv("GEMINI_API_KEY")
LARK_WEBHOOK = os.getenv("LARK_WEBHOOK")

if not API_KEY or not LARK_WEBHOOK:
    log("❌ 错误：GitHub Secrets 配置缺失")
    sys.exit(1)

genai.configure(api_key=API_KEY)

def get_best_model():
    """自动寻找可用的模型全称"""
    try:
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        log(f"当前 Key 可用的模型列表: {models}")
        # 优先使用 flash-latest，如果没有则选第一个
        for target in ['models/gemini-1.5-flash-latest', 'models/gemini-1.5-flash', 'models/gemini-pro']:
            if target in models:
                return target
        return models[0] if models else None
    except Exception as e:
        log(f"获取模型列表失败: {e}")
        return 'models/gemini-1.5-flash-latest' # 2026 标准兜底名

def main():
    target_model = get_best_model()
    log(f"🎯 最终选定大脑: {target_model}")
    
    with open("sources.yaml", "r", encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    final_reports = []
    # 随机选 4 个分类激荡思维
    selected_cats = random.sample(config['categories'], 4)
    
    for category in selected_cats:
        source = random.choice(category['sources'])
        log(f"🕵️ 正在读取: {source['name']}")
        
        feed = feedparser.parse(source['url'])
        if feed.entries:
            article = feed.entries[0]
            log(f"📖 发现文章: {article.title}")
            
            try:
                # 使用 Jina Reader 抓取全文
                res = requests.get(f"https://r.jina.ai/{article.link}", timeout=30)
                model = genai.GenerativeModel(target_model)
                
                prompt = f"分析文章：{res.text[:8000]}。请提供一个能激荡思考、反常识的视角，100字内。"
                response = model.generate_content(prompt)
                
                if response.text:
                    report = f"💡 来自【{source['name']}】的思维碰撞：\n{response.text}\n🔗 原文: {article.link}"
                    final_reports.append(report)
                    log(f"✅ {source['name']} 解析成功")
            except Exception as e:
                log(f"⚠️ 思考中断: {e}")

    if final_reports:
        # 包含关键词 Thinkinghub 绕过飞书拦截
        full_text = "Thinkinghub 战略情报汇报：\n\n" + "\n\n---\n\n".join(final_reports)
        r = requests.post(LARK_WEBHOOK, json={"msg_type": "text", "content": {"text": full_text}})
        log(f"🎯 飞书推送结果: {r.text}")
    else:
        log("📭 本次未生成有效报告")

if __name__ == "__main__":
    main()
