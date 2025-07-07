import logging

from fastapi import FastAPI
from contextlib import asynccontextmanager
import pandas as pd
import requests

logger = logging.getLogger("uvicorn.error")

features_store_url = "http://127.0.0.1:8010"
events_store_url = "http://127.0.0.1:8020"

class Recommendations:

    def __init__(self):

        self._recs = {"personal": None, "default": None}
        self._stats = {
            "request_personal_count": 0,
            "request_default_count": 0,
        }

    def load(self, type, path, **kwargs):
        """
        Загружает рекомендации из файла
        """

        logger.info(f"Loading recommendations, type: {type}")
        self._recs[type] = pd.read_parquet(path, **kwargs)
        if type == "personal":
            self._recs[type] = self._recs[type].set_index("user_id")
        logger.info(f"Loaded")

    def get(self, user_id: int, k: int=100):
        """
        Возвращает список рекомендаций для пользователя
        """
        try:
            recs = self._recs["personal"].loc[user_id]
            recs = recs["item_id"].to_list()[:k]
            self._stats["request_personal_count"] += 1
        except KeyError:
            recs = self._recs["default"]
            recs = recs["item_id"].to_list()[:k]
            self._stats["request_default_count"] += 1
        except:
            logger.error("No recommendations found")
            recs = []

        return recs

    def stats(self):

        logger.info("Stats for recommendations")
        for name, value in self._stats.items():
            logger.info(f"{name:<30} {value} ")


class SimilarItems:

    def __init__(self):

        self._similar_items = None

    def load(self, path, **kwargs):
        """
        Загружаем данные из файла
        """

        logger.info(f"Loading data, type: {type}")
        self._similar_items = pd.read_parquet(path)
        #self._similar_items = # ваш код здесь #
        logger.info(f"Loaded")

    def get(self, item_id: int, k: int = 10):
        """
        Возвращает список похожих объектов
        """
        try:
            #i2i = self._similar_items.loc[item_id].head(k)
            i2i = self._similar_items[self._similar_items["item_id_1"] == item_id].head(k)
            i2i = i2i[["item_id_2", "score"]].to_dict(orient="list")
        except KeyError:
            logger.error("No recommendations found")
            i2i = {"item_id_2": [], "score": {}}

        return i2i

sim_items_store = SimilarItems()
rec_store = Recommendations()     

@asynccontextmanager
async def lifespan(app: FastAPI):
    # код ниже (до yield) выполнится только один раз при запуске сервиса
    logger.info("Starting")
    rec_store.load(
    "personal",
    'final_recommendations_feat.parquet',
    columns=["user_id", "item_id", "rank"],
    )
    rec_store.load(
        "default",
        'top_recs.parquet',
        columns=["item_id", "rank"],
    )
    yield
    # этот код выполнится только один раз при остановке сервиса
    logger.info("Stopping")
    rec_store.stats()

# создаём приложение FastAPI
app = FastAPI(title="recommendations", lifespan=lifespan)

# @app.post("/recommendations")
# async def recommendations(user_id: int, k: int = 100):
#     """
#     Возвращает список рекомендаций длиной k для пользователя user_id
#     """

#     recs = []

#     return {"recs": recs}

@app.post("/recommendations")
async def recommendations(user_id: int, k: int = 100):
    """
    Возвращает список рекомендаций длиной k для пользователя user_id
    """

    recs = rec_store.get(user_id, k)

    return {"recs": recs}


# @app.post("/recommendations_online")
# async def recommendations_online(user_id: int, k: int = 100):
#     """
#     Возвращает список онлайн-рекомендаций длиной k для пользователя user_id
#     """

#     headers = {"Content-type": "application/json", "Accept": "text/plain"}

#     # получаем последнее событие пользователя
#     params = {"user_id": user_id, "k": 1}
#     resp = requests.post(events_store_url + "/get", headers=headers, params=params)
#     events = resp.json()
#     events = events["events"]

#     # получаем список похожих объектов
#     if len(events) > 0:
#         item_id = events[0]
#         params = {"item_id": item_id, "k": k}
#         item_similar_items = sim_items_store.get(params)
#         recs = item_similar_items[:k]
#     else:
#         recs = []

#     return {"recs": recs}

@app.post("/recommendations_online")
async def recommendations_online(user_id: int, k: int = 100):
    try:
        # Получаем последнее событие пользователя
        resp = requests.get(
            f"{events_store_url}/get",
            params={"user_id": user_id, "k": 1},
            timeout=5
        )
        resp.raise_for_status()
        events_data = resp.json()
        
        if not events_data or "events" not in events_data:
            return {"recs": []}

        events = events_data["events"]
        if not events:
            return {"recs": []}

        # Получаем похожие товары
        similar_items = sim_items_store.get(events[0], k)
        return {"recs": similar_items.get("item_id_2", [])[:k]}

    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {str(e)}")
        return {"recs": []}
    except Exception as e:
        logger.error(f"Internal error: {str(e)}")
        return {"recs": []}
