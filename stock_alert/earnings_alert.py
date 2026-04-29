#!/usr/bin/env python3
"""
Stock Earnings Alert System
- Monitors M7 earnings announcements
- Analyzes buy/sell opportunities for watchlist stocks (CEG, P, XE)
- Sends Telegram or email notification
"""

import os
import sys
import requests
import yfinance as yf
import anthropic
from datetime import datetime
import pytz

M7_TICKERS = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA"]
WATCH_TICKERS = ["CEG", "P", "XE"]
KST = pytz.timezone("Asia/Seoul")

EARNINGS_KEYWORDS = [
    "earn", "result", "quarter", "revenue", "profit",
    "eps", "beat", "miss", "guidance", "forecast", "q1", "q2", "q3", "q4",
]


def get_earnings_news(tickers: list[str]) -> list[dict]:
    news_items = []
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            news = stock.news or []
            for item in news[:10]:
                title = item.get("title", "")
                if any(kw in title.lower() for kw in EARNINGS_KEYWORDS):
                    news_items.append({
                        "ticker": ticker,
                        "title": title,
                        "publisher": item.get("publisher", ""),
                        "published_ts": item.get("providerPublishTime", 0),
                    })
        except Exception as e:
            print(f"  [warn] {ticker} 뉴스 수집 실패: {e}", file=sys.stderr)
    return news_items


def get_stock_snapshot(tickers: list[str]) -> dict:
    snapshots = {}
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="10d")
            info = stock.info

            if hist.empty:
                print(f"  [warn] {ticker} 가격 데이터 없음", file=sys.stderr)
                continue

            price = hist["Close"].iloc[-1]
            prev = hist["Close"].iloc[-2] if len(hist) > 1 else price
            week_ago = hist["Close"].iloc[-5] if len(hist) >= 5 else hist["Close"].iloc[0]
            high_52w = info.get("fiftyTwoWeekHigh")
            low_52w = info.get("fiftyTwoWeekLow")

            snapshots[ticker] = {
                "name": info.get("shortName", ticker),
                "price": round(price, 2),
                "change_1d_pct": round((price - prev) / prev * 100, 2),
                "change_5d_pct": round((price - week_ago) / week_ago * 100, 2),
                "volume": int(hist["Volume"].iloc[-1]),
                "avg_volume_5d": int(hist["Volume"].mean()),
                "high_52w": high_52w,
                "low_52w": low_52w,
                "pct_from_high": round((price - high_52w) / high_52w * 100, 1) if high_52w else None,
                "pct_from_low": round((price - low_52w) / low_52w * 100, 1) if low_52w else None,
                "pe": info.get("trailingPE"),
            }
        except Exception as e:
            print(f"  [warn] {ticker} 데이터 수집 실패: {e}", file=sys.stderr)
    return snapshots


def build_analysis_prompt(m7_news: list[dict], watch: dict) -> str:
    today = datetime.now(KST).strftime("%Y년 %m월 %d일")

    if m7_news:
        news_block = "\n".join(
            f"• [{n['ticker']}] {n['title']}  ({n['publisher']})"
            for n in m7_news
        )
    else:
        news_block = "아직 오늘의 실적 뉴스가 수집되지 않았습니다. (장 마감 전 실행)"

    watch_block = ""
    for ticker, d in watch.items():
        watch_block += (
            f"\n**{ticker} — {d['name']}**\n"
            f"  현재가 ${d['price']}  |  전일대비 {d['change_1d_pct']:+.2f}%  |  5일 {d['change_5d_pct']:+.2f}%\n"
            f"  52주 고점 ${d['high_52w']} ({d['pct_from_high']:+.1f}%)  저점 ${d['low_52w']} ({d['pct_from_low']:+.1f}%)\n"
            f"  거래량 {d['volume']:,}  (5일 평균 {d['avg_volume_5d']:,})  |  P/E {d['pe']}\n"
        )
    if not watch_block:
        watch_block = "관심 종목 데이터를 가져오지 못했습니다."

    return f"""당신은 주식 분석 전문가입니다. 오늘({today}) 데이터를 분석해주세요.

## M7 실적 뉴스
{news_block}

## 관심 종목 현황
{watch_block}

아래 형식으로 한국어 분석 리포트를 작성해주세요.

### 📊 M7 실적 요약
뉴스를 바탕으로 각 기업별 핵심 포인트를 정리하세요 (EPS 어닝서프라이즈, 매출, 다음 분기 가이던스 등). 뉴스가 없는 기업은 생략해도 됩니다.

### 🌐 시장 영향 분석
오늘/내일 시장 전반에 미칠 영향 예측 (위험선호 vs 위험회피 방향 포함).

### 🎯 관심 종목 매매 전략
각 종목(CEG, P, XE)별로:
- **포지션 판단**: 매수 / 관망 / 매도
- **단기차익 타겟가** (3-7% 목표, 진입 기준 명시)
- **저점매수 포인트** (지지선 기준 가격대)
- **리스크 요인** 1가지

### ⚡ 오늘의 핵심 전략 (2줄 요약)"""


def analyze_with_claude(m7_news: list[dict], watch: dict) -> str:
    client = anthropic.Anthropic()
    prompt = build_analysis_prompt(m7_news, watch)

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2500,
        system="주식 분석 전문가로서 데이터 기반의 명확하고 실행 가능한 매매 전략을 제공합니다.",
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def send_telegram(token: str, chat_id: str, text: str) -> None:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    # Telegram limit: 4096 chars per message
    for chunk in [text[i:i + 4000] for i in range(0, len(text), 4000)]:
        resp = requests.post(url, json={"chat_id": chat_id, "text": chunk, "parse_mode": "Markdown"}, timeout=10)
        resp.raise_for_status()


def send_email(subject: str, body: str, to_email: str) -> None:
    import smtplib
    from email.mime.text import MIMEText

    from_email = os.environ["EMAIL_FROM"]
    password = os.environ["EMAIL_PASSWORD"]
    smtp_server = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to_email

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(from_email, password)
        server.send_message(msg)


def main() -> None:
    now_kst = datetime.now(KST).strftime("%Y-%m-%d %H:%M KST")
    print(f"[{now_kst}] 주식 알림 실행 시작")

    print("  M7 실적 뉴스 수집 중...")
    m7_news = get_earnings_news(M7_TICKERS)
    print(f"  → {len(m7_news)}개 실적 관련 뉴스")

    print("  관심 종목 데이터 수집 중...")
    watch = get_stock_snapshot(WATCH_TICKERS)
    print(f"  → {len(watch)}개 종목 수집 완료")

    print("  Claude 분석 중...")
    analysis = analyze_with_claude(m7_news, watch)

    today = datetime.now(KST).strftime("%m/%d")
    subject = f"[주식알림] {today} M7 실적 + CEG/P/XE 전략"
    full_text = f"*{subject}*\n\n{analysis}"

    method = os.environ.get("NOTIFICATION_METHOD", "telegram")
    if method == "telegram":
        send_telegram(
            token=os.environ["TELEGRAM_BOT_TOKEN"],
            chat_id=os.environ["TELEGRAM_CHAT_ID"],
            text=full_text,
        )
        print("  Telegram 알림 전송 완료")
    elif method == "email":
        send_email(subject, analysis, os.environ["EMAIL_TO"])
        print("  이메일 알림 전송 완료")
    else:
        print(f"\n{'='*60}\n{full_text}\n{'='*60}")

    print("완료!")


if __name__ == "__main__":
    main()
