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

log("正在启动 Thinkinghub 引擎...")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
LARK_WEBHOOK = os.getenv("LARK_WEBHOOK")

if not GEMINI_KEY or not LARK_WEBHOOK:
    log("错误：环境变量配置不完整")
    sys.exit(1)

genai.configure(api_key=GEMINI_KEY)

def get_ai_response(content):
    # 自修复逻辑：尝试不同的模型名称
    model_names = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro']
    prompt = f"分析文章：{content[:6000]}。请提供一个能激荡思考、反常识的视角，100字内。"
    
    for name in model_names:
        try:
            log(f"尝试调用模型: {name}")
            model = genai.GenerativeModel(name)
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            log(f"模型 {name} 调用失败: {e}")
            continue
    return None

def main():
    with open("sources.yaml", "r", encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    final_reports = []
    # 从 38 个源中随机选 3 个，保持思维多样性 [cite: 3]
    selected_cats = random.sample(config['categories'], 3)
    
    for category in selected_cats:
        source = random.choice(category['sources'])
        log(f"正在从 {source['name']} 寻找灵感...")
        
        feed = feedparser.parse(source['url'])
        if feed.entries:
            article = feed.entries[0]
            log(f"发现文章: {article.title}")
            
            try:
                # 使用 Jina Reader 抓取
                res = requests.get(f"https://r.jina.ai/{article.link}", timeout=25)
                ai_text = get_ai_response(res.text)
                
                if ai_text:
                    report = f"💡 来自【{source['name']}】的思维激荡：\n{ai_text}\n🔗 原文: {article.link}"
                    final_reports.append(report)
                    log("AI 分析完成")
            except Exception as e:
                log(f"处理失败: {e}")

    if final_reports:
        # 关键词 Thinkinghub 必须存在
        full_text = "Thinkinghub 每日汇报：\n\n" + "\n\n---\n\n".join(final_reports)
        requests.post(LARK_WEBHOOK, json={"msg_type": "text", "content": {"text": full_text}})
        log("报告已发送至飞书")
    else:
        log("本次未生成有效内容")

if __name__ == "__main__":
    main()
