import asyncio
import functools
from datetime import datetime

import requests as r
import xmltodict
from app.dependencies.modules import get_moving_time
from app.utils.config import CONFIG
from dateutil.parser import parse as dateparser
from pytz import timezone


class StationModel:
    def __init__(self):
        self.tour_config = CONFIG["tour"]
        self.kakao_config = CONFIG["kakao"]

    def get_loc_based_list(self, x, y, radius, content_type_id):
        """장소의 좌표를 입력하면 해당 좌표를 기준으로 근처의 관광지 목록을 반환

        Arguments:
            x: 장소의 X좌표
            y: 장소의 Y좌표
            radius: 해당 장소를 기준으로 몇 m 반경까지 검색을 실시할 것인지
            content_type_id: number

        Returns:
            string: 관광지 목록 json text

        To do:
            modules로 따로 뺄까? 용도가 달라질 수 있으므로 일단 놔둠
        """
        url = "http://api.visitkorea.or.kr/openapi/service/rest/KorService/locationBasedList"
        params = {
            "ServiceKey": self.tour_config["decoded_key"],
            "numOfRows": 30,
            #              "pageNo": 1,
            "MobileOS": "ETC",
            "MobileApp": "LastDay",
            "mapX": x,
            "mapY": y,
            "radius": radius,
            "arrange": "E",  # 거리순 정렬
            "ListYN": "Y",
            "contentTypeId": content_type_id,
        }
        res = r.get(url, params=params)
        parsed = xmltodict.parse(res.text)
        if "body" not in parsed["response"]:
            return []
        elif "items" not in parsed["response"]["body"]:
            return []
        elif "item" not in parsed["response"]["body"]["items"]:
            return []

        items = parsed["response"]["body"]["items"]["item"]
        return items

    def get_staying_time(self, content_id, content_type, tour_api_key):
        """관광api에서 소요시간을 조회하는 함수인데, 소요시간이 제대로 주어지지 않는 경우가 많아 deprecate"""
        url = "http://api.visitkorea.or.kr/openapi/service/rest/KorService/detailIntro"
        params = {
            "ServiceKey": self.tour_config["decoded_key"],
            "numOfRows": 20,
            "MobileOS": "ETC",
            "MobileApp": "LastDay",
            "contentId": content_id,
            "contentTypeId": content_type,
        }
        res = r.get(url, params=params)  # xml 형식
        parsed = xmltodict.parse(res.text)
        spend_time = parsed["response"]["body"]["spendtime"]
        return spend_time

    async def get_total_time(
        self, start_loc, spot_loc_info, limit_time_hour, limit_time_min
    ):
        """출발지에서 여행지에 갔다가 돌아오는 데에 걸리는 총 이동 시간을 반환

        Args:
            start_loc (int, int): 출발지 좌표
            end_loc (int, int): 도착지 좌표
            spot_loc_info (json): Tour API를 통해 받은 여행지에 대한 정보

        Returns:
            json: 총 이동시간이 포함된 Tour API output
        """
        loop = asyncio.get_event_loop()

        # 차편 시간 기준 가용 시간 계산
        now = datetime.now(timezone("Asia/Seoul"))
        limit_time = f"{now.month}-{now.day} {limit_time_hour}:{limit_time_min}+9"
        limit_time = dateparser(limit_time)
        time_diff = limit_time - now
        available_time = time_diff.seconds // 60

        tmp = dict(spot_loc_info)
        tmp["dist"] = int(tmp["dist"])
        spot_loc = (tmp["mapx"], tmp["mapy"])
        spot_time = await loop.run_in_executor(
            None,
            get_moving_time,
            start_loc[0],
            start_loc[1],
            spot_loc[0],
            spot_loc[1],
        )
        if spot_time:
            tmp["travel_time"] = spot_time * 2
            tmp["free_time"] = available_time - spot_time * 2
            return tmp
        else:
            return

    async def get_station_based_spot(
        self, start_loc, area, content_type, candidate, limit_time_hour, limit_time_min
    ):
        """역 기준으로 근처 관광지 리스트를 소요시간 순으로 반환

        Args:
            start_loc (tuple(int)): 출발지 좌표
            area (int): 검색 범위 (미터 기준)
            content_type: 관광지 타입
            - 12: 관광지
            - 14: 문화시설
            - 15: 행사, 공연, 축제
            - 25: 여행 코스
            - 28: 레포츠
            - 32: 숙박
            - 38: 쇼핑
            - 39: 음식점
            candidate: 조회할 관광지 개수

        Returns:
            왕복 소요시간이 포함된 역 주변 N개의 관광지 리스트
        """

        loc_based_list = self.get_loc_based_list(
            start_loc[0], start_loc[1], area, content_type
        )
        loc_candidate = []
        futures = [
            asyncio.ensure_future(
                self.get_total_time(
                    start_loc, spot_loc_info, limit_time_hour, limit_time_min
                )
            )
            for spot_loc_info in loc_based_list[:candidate]
        ]

        result = await asyncio.gather(*futures)

        result = list(filter(lambda x: x != None, result))
        loc_candidate = sorted(result, key=(lambda x: x["travel_time"]))
        # print(f"Data handling time: {time.time() - time_data_handling}")
        return loc_candidate


def main(
    start_keyword, end_keyword, content_type, candidate, limit_time_hour, limit_time_min
):
    inst = StationModel()
    loop = asyncio.get_event_loop()
    func = functools.partial(
        inst.get_station_based_spot,
        start_keyword,
        end_keyword,
        content_type,
        candidate,
        limit_time_hour,
        limit_time_min,
    )
    result = loop.run_until_complete(func())
    loop.close()
    return result
