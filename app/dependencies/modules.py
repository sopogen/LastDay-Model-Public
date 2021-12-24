import logging
import time

import requests as r
from app.utils.config import CONFIG

kakao_api_key = CONFIG["kakao"]["key"]

logger = logging.getLogger(__name__)


"""
    해당 함수는 node위에서 직접 사용하는 것으로 결정하여 deprecate
"""
# def get_loc(keyword):
#     """장소를 입력하면 KAKAO API에서 해당 장소의 좌표를 가져와서 반환

#     Args:
#         keyword: 검색 장소 이름
#         kakao_api_key: KAKAO map API의 REST API key가 저장된 json 파일

#     Returns:
#         tuple: x, y 좌표값
#     """
#     url = "https://dapi.kakao.com/v2/local/search/keyword.json"
#     page_num = 1
#     params = {"query": keyword, "page": page_num}
#     headers = {"Authorization": "KakaoAK " + kakao_api_key}

#     places = r.get(url, params=params, headers=headers).json()["documents"]
#     logger.info(f"'{keyword}'에 대한 주소 검색결과: 총 {len(places)}개 검색 / 기준 주소: {places[0]}")
#     coordinate = (float(places[0]["x"]), float(places[0]["y"]))
#     # total = r.get(url, params=params, headers=headers).json()["meta"]["total_count"]
#     return coordinate


def get_loc_list(keyword, num=10):
    """장소를 입력하면 KAKAO API에서 해당 장소 기반 검색 결과와 좌표 리스트를 반환

    Args:
        keyword: 검색 장소 이름
        num: 가져올 검색 목록 개수

    Returns:
        dictionary:
        {'place_name' : 장소명(str),
        'address_name': 해당 장소의 주소(str),
        'location': 해당 장소의 좌표(tuple:(x, y))}
    """
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    page_num = 1
    params = {"query": keyword, "page": page_num}
    headers = {"Authorization": "KakaoAK " + kakao_api_key}

    places = r.get(url, params=params, headers=headers).json()["documents"][:num]
    result = list(
        map(
            lambda x: {
                "place_name": x["place_name"],
                "address_name": x["address_name"],
                "location": (float(x["x"]), float(x["y"])),
            },
            places,
        )
    )
    return result


def calc_dist_radius(a_x, a_y, b_x, b_y, RATIO=0.75):
    """두 좌표간 거리를 계산하여 중점과 관광지 목록을 검색할 반지름을 반환

    Arguments:
        a_x: 1번 좌표의 x좌표
        ...
        ratio: 두 좌표간 거리에 몇을 곱한 값을 검색 반지름으로 쓸 것인가. 0.5 이상

    """
    mid_x = (a_x + b_x) / 2
    mid_y = (a_y + b_y) / 2
    dist = ((a_x - b_x) ** 2 + (a_y - b_y) ** 2) ** 0.5

    radius = int(dist * RATIO * 1000 * 1000)
    # 반지름 하한 설정: 5km
    if radius <= 5000:
        radius = 5000
    return [mid_x, mid_y], radius


def get_moving_time(start_x, start_y, end_x, end_y):
    """출발지와 도착지의 좌표를 입력하면, Naver 지도 API를 사용하여 두 좌표간의 대중교통 or 도보 이동 시간을 반환

    Arguments:
        start_x = 출발지 X좌표
        start_y = 출발지 Y좌표
        end_x = 도착지 X좌표
        end_y = 도착지 Y좌표

    Returns:
        int: 대중교통 이동 소요 시간 (분)
        int: 도보 이동 소요 시간 (분) - 대중 교통 이동 경로가 없는 경우
        Null: 도보 이동 경로도 존재하지 않는 경우
    """

    url = "https://m.map.naver.com/apis/rp/pubtrans/summary"
    params = {
        "apiVersion": 3,
        "searchType": 0,
        "start": f"{start_x},{start_y},출발지",
        "destination": f"{end_x},{end_y},도착지",
    }

    response = r.get(url, params=params)
    response_json = response.json()

    if "error" not in response_json.keys():
        travel_time = response_json["result"]["path"][0]["info"]["totalTime"]
    elif response_json["error"]["code"] == -99:
        url = "https://map.naver.com/v5/api/dir/findwalk"
        params = {
            "lo": "ko",
            "r": "step",
            "st": 1,
            "o": "all",
            "l": f"{start_x},{start_y},출발지,1;{end_x},{end_y},도착지",
            "lang": "ko",
        }
        response = r.get(url, params=params)
        response_json = response.json()

        if "error" in response_json.keys():
            return
        travel_time = response_json["routes"][0]["summary"]["duration"] // 60
    else:
        return

    return int(travel_time)


if __name__ == "__main__":
    start = time.time()
    print(get_loc("광화문"))
    print("time: ", time.time() - start)
