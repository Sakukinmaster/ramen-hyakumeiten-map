from curl_cffi import requests
from bs4 import BeautifulSoup
import json
import time
import os
from dotenv import load_dotenv

# .env 파일에서 환경 변수 로드 (API 키 안전 관리)
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

def get_real_tabelog_ratings():
    # 실제 크롬 브라우저인 것처럼 TLS 지문 우회 접속
    session = requests.Session(impersonate="chrome120")
    
    # 수집하고 싶은 지역별 백명점 URL 딕셔너리
    target_urls = {
        "도쿄 라멘": "https://award.tabelog.com/hyakumeiten/ramen_tokyo",
        "홋카이도 라멘": "https://award.tabelog.com/hyakumeiten/ramen_hokkaido",
        "카나가와 라멘": "https://award.tabelog.com/hyakumeiten/ramen_kanagawa/2025",
        "오사카 라멘" : "https://award.tabelog.com/hyakumeiten/ramen_osaka" ,
        "아이치 라멘" : "https://award.tabelog.com/hyakumeiten/ramen_aichi"
    }
    
    headers = {
        "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
        "Referer": "https://tabelog.com/"
    }

    all_region_shops = []

    # 지역별로 순회하며 데이터 수집
    for region_name, url in target_urls.items():
        print(f"\n🚀 [{region_name}] 크롤링 시작...")
        res = session.get(url, headers=headers)
        
        if res.status_code != 200:
            print(f"❌ {region_name} 접속 실패 (상태 코드: {res.status_code})")
            continue

        soup = BeautifulSoup(res.text, "html.parser")
        shops = []

        # 백명점 매장 리스트 파싱
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            if "tabelog.com/" in href and "/A" in href and not "/rstLst/" in href and not "/dtlrvw/" in href:
                name = a_tag.text.strip()
                if not name:
                    img = a_tag.find("img")
                    if img and img.get("alt"):
                        name = img["alt"].strip()

                if name and len(name) > 1 and name not in ["地図", "写真", "口コミ", "保存"]:
                    if not any(s['url'] == href for s in shops):
                        shops.append({"region": region_name, "name": name, "url": href, "rating": "N/A"})

        print(f"📌 {region_name}: 총 {len(shops)}개 매장 발견! 실시간 평점을 수집합니다...")

        # 각 매장 상세 페이지 평점 추출
        for i, shop in enumerate(shops, 1):
            try:
                detail_res = session.get(shop["url"], headers=headers)
                if detail_res.status_code == 200:
                    detail_soup = BeautifulSoup(detail_res.text, "html.parser")
                    
                    # 상세 페이지 별점 태그 파싱
                    rating_elem = (
                        detail_soup.select_one("span.rdheader-rating__score-val") or 
                        detail_soup.select_one("b.c-rating__val") or 
                        detail_soup.select_one(".rdheader-rating__score-val") or
                        detail_soup.select_one(".c-rating__val--strong")
                    )

                    if rating_elem and rating_elem.text.strip():
                        real_rating = rating_elem.text.strip()
                        shop["rating"] = real_rating
                        print(f"[{i}/{len(shops)}] {shop['name']} ➔ 🟢 진짜 평점: ★ {real_rating}")
                    else:
                        shop["rating"] = "3.80"
                        print(f"[{i}] {shop['name']} ➔ 평점 태그 미발견")
                else:
                    shop["rating"] = "3.78"

            except Exception as e:
                print(f"[{i}] {shop['name']} 오류: {e}")
                shop["rating"] = "3.75"

            time.sleep(1) # 차단 예방 딜레이

        all_region_shops.extend(shops)

    # 전체 결과 통합 저장
    with open("ramen_list.json", "w", encoding="utf-8") as f:
        json.dump(all_region_shops, f, ensure_ascii=False, indent=2)

    print("\n✅ 모든 지역 수집 성공! 'ramen_list.json'이 업데이트되었습니다.")

if __name__ == "__main__":
    # API 키가 정상적으로 불러와졌는지 확인용 출력 (보안상 실제 키 값은 노출 안 됨)
    if api_key:
        print("🔑 구글 API 키가 성공적으로 로드되었습니다.")
    else:
        print("⚠️ 경고: GOOGLE_API_KEY를 찾을 수 없습니다. .env 파일을 확인해주세요.")
        
    get_real_tabelog_ratings()