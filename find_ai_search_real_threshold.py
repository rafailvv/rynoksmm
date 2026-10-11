#!/usr/bin/env python3
"""Empirically pick a cutoff for SMM AI search with realistic category texts.

Run on the server from /home/rynoksmm:
    python3 find_ai_search_real_threshold.py

The script uses real SMM rows and target_audience categories from Postgres,
generates realistic full-text SMM ads for different categories, embeds real user
queries and ads with text-embedding-3-small, ranks through the real project
rank_ai_search_results function, and estimates a practical cosine cutoff.
"""

from __future__ import annotations

import ast
import json
import logging
import math
import os
import random
import statistics
import subprocess
import urllib.request
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
ENV_PATH = PROJECT_ROOT / "smm.env"
MODEL = "text-embedding-3-large"
LIMIT = 5
RANDOM_SEED = 20260628


@dataclass(frozen=True)
class AdCase:
    ad_id: str
    category: str
    text: str
    source: str


@dataclass(frozen=True)
class QueryCase:
    query_id: str
    category: str
    text: str


def load_env(path: Path) -> dict[str, str]:
    values = {}
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def load_rank_functions():
    source_path = PROJECT_ROOT / "Bot" / "handlers" / "message.py"
    module_ast = ast.parse(source_path.read_text(), filename=str(source_path))
    needed = {"cosine_similarity", "rank_ai_search_results"}
    selected = [node for node in module_ast.body if isinstance(node, ast.FunctionDef) and node.name in needed]
    if {node.name for node in selected} != needed:
        raise RuntimeError(f"cannot find {needed} in {source_path}")
    extracted = ast.Module(body=selected, type_ignores=[])
    ast.fix_missing_locations(extracted)
    namespace = {"math": math, "logging": logging}
    exec(compile(extracted, str(source_path), "exec"), namespace)
    return namespace["cosine_similarity"], namespace["rank_ai_search_results"]


cosine_similarity, rank_ai_search_results = load_rank_functions()


def psql_json(sql: str):
    cmd = ["docker", "exec", "rynoksmm-db_smm-1", "psql", "-U", "rynoksmm", "-d", "rynoksmm", "-t", "-A", "-c", sql]
    output = subprocess.check_output(cmd, text=True)
    return json.loads(output.strip() or "[]")


def load_real_db_ads() -> list[AdCase]:
    rows = psql_json(
        """
        select coalesce(json_agg(row_to_json(t)), '[]'::json)
        from (
            select s.id, s.description, array_agg(distinct ta.name order by ta.name) as categories
            from smm s
            left join target_audience_smm tas on tas.smm_id = s.user_id
            left join target_audience ta on ta.id = tas.target_audience_id
            where s.description is not null and trim(s.description) <> ''
            group by s.id, s.description
            order by s.id
        ) t;
        """
    )
    cases: list[AdCase] = []
    for row in rows:
        cats = [c for c in row.get("categories") or [] if c]
        text = row["description"]
        if any("недвиж" in c.lower() or "строит" in c.lower() for c in cats):
            category = "real_estate"
        elif any("салон" in c.lower() or "космет" in c.lower() or "парф" in c.lower() for c in cats):
            category = "beauty"
        else:
            category = "other"
        cases.append(AdCase(f"db-{row['id']}", category, text, "real_db"))
    return cases


CATEGORY_SPECS = {
    "beauty": {
        "names": ["Салоны красоты", "Косметика", "Парфюмерия", "Спа-центры", "Косметология", "Пластическая хирургия"],
        "objects": ["салонов красоты", "студий маникюра", "косметологических клиник", "барбершопов", "spa-центров"],
        "actions": ["делаю Reels, Stories, посты и акции", "упаковываю профиль, прайс и отзывы", "привлекаю записи на процедуры", "веду Instagram, VK и Telegram", "работаю с визуалом и локальным продвижением"],
        "query": "Ищу SMM-специалиста для салона красоты в Москве. Нужно вести Instagram, VK и Telegram, делать Reels, сторис, посты и акции, привлекать новых клиентов на записи, упаковать профиль и повысить доверие к салону. Бюджет до 20 000 рублей в месяц.",
    },
    "real_estate": {
        "names": ["Агентство недвижимости", "Строительная компания", "Связанные услуги и товары"],
        "objects": ["агентств недвижимости", "риелторов", "застройщиков", "строительных компаний", "экспертов по инвестициям в недвижимость"],
        "actions": ["показываю объекты через сторис и рилс", "упаковываю кейсы, отзывы и планировки", "привлекаю заявки покупателей и арендаторов", "делаю контент-стратегию для доверия", "веду Telegram, VK и Instagram"],
        "query": "Нужен SMM для агентства недвижимости в Москве. Нужно красиво показывать квартиры и объекты, делать посты, сторис и короткие видео, вести соцсети, повышать доверие к агентству и получать заявки от покупателей и арендаторов.",
    },
    "food": {
        "names": ["Кафе", "Ресторан", "Бар", "Продукты питания"],
        "objects": ["кафе", "ресторанов", "баров", "пекарен", "доставки еды"],
        "actions": ["снимаю блюда, интерьер и команду", "делаю афиши, акции и меню в соцсетях", "привлекаю гостей на бронирования", "веду VK, Telegram и Instagram", "работаю с отзывами и локальной аудиторией"],
        "query": "Ищу SMM-специалиста для ресторана или кафе. Нужно вести соцсети, делать фото и видео еды, сторис, акции, афиши, рассказывать про меню и привлекать гостей на бронирования.",
    },
    "fitness": {
        "names": ["Фитнес", "Инвентарь", "Спортивная одежда", "Спортивная обувь", "Детская спортивная одежда"],
        "objects": ["фитнес-клубов", "студий растяжки", "спортивных школ", "магазинов спортивной одежды", "тренеров"],
        "actions": ["показываю тренировки и результаты клиентов", "делаю Reels, сторис и прогревы", "привлекаю заявки на абонементы", "упаковываю тренеров и расписание", "веду Telegram, VK и Instagram"],
        "query": "Нужен SMM для фитнес-клуба. Нужно вести соцсети, снимать тренировки, делать Reels и сторис, рассказывать про тренеров и абонементы, привлекать людей на пробные занятия.",
    },
    "kids": {
        "names": ["Детская", "Одежда для детей", "Обувь для детей", "Игрушки", "Детские сады", "Развивающие центры"],
        "objects": ["детских центров", "детских садов", "магазинов игрушек", "брендов детской одежды", "развивающих студий"],
        "actions": ["делаю контент для родителей", "показываю занятия, педагогов и отзывы", "привлекаю заявки на пробные уроки", "веду VK, Telegram и Instagram", "упаковываю доверие и безопасность"],
        "query": "Ищу SMM для детского развивающего центра. Нужно вести соцсети для родителей, показывать занятия и педагогов, делать посты, сторис, видео, отзывы и привлекать заявки на пробные занятия.",
    },
    "legal": {
        "names": ["Юридические услуги", "Нотариусы"],
        "objects": ["юридических компаний", "нотариусов", "адвокатов", "бухгалтерских сервисов", "консалтинговых компаний"],
        "actions": ["упаковываю экспертность и доверие", "делаю понятные посты по сложным темам", "привлекаю заявки на консультации", "веду Telegram, VK и Instagram", "работаю с кейсами, отзывами и репутацией"],
        "query": "Нужен SMM для юридической компании. Нужно вести Telegram и VK, писать понятные экспертные посты, упаковать кейсы и отзывы, повысить доверие и получать заявки на консультации.",
    },
    "interior": {
        "names": ["Кухни", "Элитная мебель", "Прочие товары для интерьера", "Декор и дизайн"],
        "objects": ["брендов мебели", "студий кухонь", "магазинов декора", "дизайнеров интерьера", "производителей мебели"],
        "actions": ["показываю проекты до и после", "упаковываю каталог, материалы и кейсы", "делаю Reels, сторис и подборки", "привлекаю заявки на расчет проекта", "веду Instagram, VK и Telegram"],
        "query": "Ищу SMM для студии кухонь и мебели. Нужно вести соцсети, красиво показывать проекты, материалы, интерьеры, делать Reels и посты, привлекать заявки на расчет кухни.",
    },
    "hotel": {
        "names": ["Гостиница", "Логистика", "Все для праздника", "Цветы"],
        "objects": ["гостиниц", "отелей", "ивент-площадок", "цветочных студий", "организаторов праздников"],
        "actions": ["показываю номера, сервис и атмосферу", "делаю акции, афиши и сторис", "привлекаю бронирования и заявки", "веду VK, Telegram и Instagram", "работаю с отзывами и локальным продвижением"],
        "query": "Нужен SMM для гостиницы. Нужно вести соцсети, показывать номера, сервис и атмосферу, делать посты, сторис, акции, работать с отзывами и привлекать бронирования.",
    },
    "fashion": {
        "names": ["Женская", "Мужская", "Аксессуары", "Ткани и ателье пошива одежды"],
        "objects": ["брендов женской одежды", "магазинов мужской одежды", "ателье", "магазинов аксессуаров", "локальных fashion-брендов"],
        "actions": ["собираю визуальную концепцию и лукбуки", "делаю Reels, подборки и сторис с образами", "привлекаю заявки и продажи из соцсетей", "упаковываю коллекции, размеры и преимущества", "веду Instagram, VK, Telegram и маркетплейс-контент"],
        "query": "Ищу SMM для магазина одежды. Нужно красиво показывать образы, новые коллекции, размеры и ткани, делать Reels, сторис, посты, прогревать аудиторию и приводить продажи из соцсетей.",
    },
    "events": {
        "names": ["Все для праздника", "Цветы", "Декор и дизайн", "Кинотеатры"],
        "objects": ["организаторов праздников", "цветочных студий", "декораторов", "ивент-агентств", "площадок для мероприятий"],
        "actions": ["показываю подготовку и готовые мероприятия", "делаю сторис, афиши, Reels и кейсы", "привлекаю заявки на даты и бронирования", "упаковываю портфолио, отзывы и пакеты услуг", "работаю с сезонными инфоповодами"],
        "query": "Нужен SMM для студии праздников и декора. Нужно вести соцсети, показывать оформление мероприятий, букеты, кейсы, отзывы, делать видео и привлекать заявки на свободные даты.",
    },
    "logistics": {
        "names": ["Логистика", "Связанные услуги и товары"],
        "objects": ["логистических компаний", "служб доставки", "складских сервисов", "B2B-перевозчиков", "компаний по переездам"],
        "actions": ["объясняю сложные услуги простым языком", "упаковываю кейсы, маршруты и гарантии", "привлекаю B2B-заявки через экспертный контент", "веду Telegram, VK и сайт-контент", "работаю с доверием, отзывами и цифрами"],
        "query": "Ищу SMM для логистической компании. Нужно объяснять услуги простым языком, вести Telegram и VK, показывать кейсы перевозок, гарантии, отзывы и получать B2B-заявки.",
    },
    "retail": {
        "names": ["Продукты питания", "Косметика", "Парфюмерия", "Инвентарь", "Спортивная одежда", "Спортивная обувь", "Игрушки"],
        "objects": ["интернет-магазинов", "локальных магазинов продуктов", "магазинов косметики", "магазинов игрушек", "магазинов спортивных товаров"],
        "actions": ["показываю ассортимент и новинки", "делаю продающие подборки, сторис и акции", "привлекаю заказы и повторные покупки", "упаковываю карточки товаров и отзывы", "веду соцсети вместе с промо и сезонными кампаниями"],
        "query": "Нужен SMM для интернет-магазина. Нужно вести соцсети, показывать товары, новинки, отзывы и акции, делать подборки и короткие видео, приводить заказы и повторные покупки.",
    },
}


def load_category_names() -> list[str]:
    rows = psql_json("select coalesce(json_agg(name order by id), '[]'::json) from target_audience;")
    return rows


def generate_ads(target_total: int = 240) -> list[AdCase]:
    rng = random.Random(RANDOM_SEED)
    cities = ["Москве", "Санкт-Петербурге", "Казани", "Екатеринбурге", "Новосибирске"]
    experience = ["2 года", "3 года", "4 года", "5 лет", "7 лет"]
    channels = [
        "VK и Telegram",
        "Instagram, VK и Telegram",
        "Telegram и короткие видео",
        "VK, клипы и сторис",
        "соцсети, рассылки и комьюнити",
    ]
    cases: list[AdCase] = []
    per_category = max(1, target_total // len(CATEGORY_SPECS))
    for category, spec in CATEGORY_SPECS.items():
        for index in range(per_category):
            obj = rng.choice(spec["objects"])
            city = rng.choice(cities)
            actions = rng.sample(spec["actions"], min(5, len(spec["actions"])))
            style = index % 8
            if style == 0:
                text = (
                    f"Работаю с продвижением {obj}. Беру на себя стратегию, контент-план и регулярное ведение. "
                    f"В {city} помогаю бизнесу стать понятнее для клиентов: {actions[0]}, {actions[1]}, {actions[2]}. "
                    f"Фокус на заявках, доверии и живой подаче без шаблонного контента."
                )
            elif style == 1:
                text = (
                    f"SMM для {obj}.\n"
                    f"Город: {city}.\n"
                    f"Опыт: {rng.choice(experience)}.\n"
                    f"Что делаю: {actions[0]}; {actions[1]}; {actions[2]}.\n"
                    f"Каналы: {rng.choice(channels)}. Формат работы: план, публикации, аналитика, корректировки каждую неделю."
                )
            elif style == 2:
                text = (
                    f"Помогаю {obj} получать заявки из соцсетей. Обычно начинаю с аудита профиля и конкурентов, "
                    f"потом собираю рубрики, визуальную логику и офферы. В работе: {actions[0]}, {actions[1]}. "
                    f"Если нужно, подключаю съемки, прогревы, акции и понятную отчетность по результатам."
                )
            elif style == 3:
                text = (
                    f"Меня зовут специалист по SMM, веду проекты в нише: {obj}. "
                    f"Не просто выкладываю посты, а собираю систему: позиционирование, контент, сторис, видео, "
                    f"коммуникацию с аудиторией и точки входа в заявку. Для проектов в {city} особенно хорошо работают "
                    f"локальные темы, отзывы, кейсы и регулярные поводы вернуться в профиль."
                )
            elif style == 4:
                text = (
                    f"Кейс-формат работы для {obj}: сначала упаковываем профиль, затем запускаем 3-4 постоянные рубрики, "
                    f"добавляем короткие видео и сторис, тестируем офферы. Моя зона: {actions[0]}, {actions[1]}, "
                    f"{actions[2] if len(actions) > 2 else 'анализ контента'}. Цель - чтобы соцсети давали не лайки ради лайков, "
                    f"а обращения, записи, бронирования или заявки."
                )
            elif style == 5:
                text = (
                    f"{obj.capitalize()} часто теряют клиентов из-за пустого или хаотичного профиля. "
                    f"Я выстраиваю контент так, чтобы человек быстро понял услугу, увидел доверие и сделал следующий шаг. "
                    f"Веду {rng.choice(channels)}, готовлю тексты, идеи для съемок, сторис, Reels/клипы и ежемесячный план."
                )
            elif style == 6:
                text = (
                    f"Услуги SMM: аудит, стратегия, контент, оформление, сторис, видео, акции, аналитика. "
                    f"Подходит для {obj}, которые хотят системно вести соцсети в {city}. "
                    f"Отдельно прорабатываю боли аудитории, сезонность, отзывы, портфолио и путь клиента до заявки."
                )
            else:
                text = (
                    f"Возьму SMM-проект в нише {obj}. Можно начать с небольшого объема: 8-12 постов, сторис, "
                    f"план коротких видео и базовая упаковка профиля. Дальше смотрим, что дает заявки, усиливаем удачные рубрики, "
                    f"убираем лишнее. Работаю спокойно, с отчетностью и понятной коммуникацией."
                )
            cases.append(AdCase(f"{category}-{index + 1}", category, text, "generated"))
    rng.shuffle(cases)
    return cases


def build_queries() -> list[QueryCase]:
    return [
        QueryCase(f"{category}-{index + 1}", category, text)
        for category, spec in CATEGORY_SPECS.items()
        for index, text in enumerate(variants_for_category(category, spec), start=0)
    ]


def variants_for_category(category: str, spec: dict) -> list[str]:
    obj = spec["objects"][0]
    actions = spec["actions"]
    return [
        spec["query"],
        f"Нужно найти SMM-специалиста для {obj}. Важно, чтобы человек понимал нишу, мог вести соцсети, делать контент-план, сторис, короткие видео, посты и приводить заявки, а не просто красиво оформлять профиль.",
        f"Посоветуйте SMM под проект в категории {', '.join(spec['names'][:2])}. Нужны упаковка профиля, регулярный контент, идеи для съемок, тексты, аналитика и понятная работа с аудиторией.",
        f"Ищу специалиста, который возьмет продвижение {obj}: {actions[0]}, {actions[1]}, {actions[2]}. Хочется получить лиды из VK, Telegram и Instagram, бюджет средний, город не принципиален.",
        f"Нужен не таргетолог, а именно SMM: стратегия, рубрики, визуал, Reels/клипы, сторис, отзывы, прогрев и отчеты. Бизнес связан с направлением: {spec['names'][0].lower()}.",
    ]


def embed_texts(texts: list[str], api_key: str, batch_size: int = 64) -> list[list[float]]:
    embeddings: list[list[float]] = []
    for start in range(0, len(texts), batch_size):
        batch = texts[start : start + batch_size]
        request = urllib.request.Request(
            "https://openrouter.ai/api/v1/embeddings",
            data=json.dumps({"model": MODEL, "input": batch}).encode("utf-8"),
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json", "HTTP-Referer": "https://smm.specfind.ru", "X-Title": "specfind-ai-search-threshold-test"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=120) as response:
            payload = json.loads(response.read().decode("utf-8"))
        if "data" not in payload:
            raise RuntimeError(payload)
        embeddings.extend(item["embedding"] for item in payload["data"])
    return embeddings


def percentile(values: list[float], pct: float) -> float:
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round(len(ordered) * pct) - 1))
    return ordered[index]


def analyze_query(query: QueryCase, query_embedding, ads: list[AdCase], ad_embeddings: dict[str, list[float]]):
    rows = []
    for ad in ads:
        score = cosine_similarity(query_embedding, ad_embeddings[ad.ad_id])
        rows.append((score, ad, ad.category == query.category))
    positives = [score for score, _ad, ok in rows if ok]
    negatives = [score for score, _ad, ok in rows if not ok]
    cutoff = percentile(positives, 0.10)
    kept_positive = sum(1 for score in positives if score >= cutoff)
    removed_negative = sum(1 for score in negatives if score < cutoff)
    false_positive = sum(1 for score in negatives if score >= cutoff)
    candidates = [(ad.ad_id, (ad.text, ad.category), ad_embeddings[ad.ad_id]) for ad in ads]
    ranked = rank_ai_search_results(candidates, query_embedding, limit=len(candidates))
    top_after = []
    for ad_id, _profile in ranked:
        ad = next(item for item in ads if item.ad_id == ad_id)
        score = cosine_similarity(query_embedding, ad_embeddings[ad_id])
        if score >= cutoff:
            top_after.append((ad_id, ad.category, score, ad.category == query.category))
        if len(top_after) == LIMIT:
            break
    return {
        "query": query,
        "positive_min": min(positives),
        "positive_p10": cutoff,
        "positive_median": statistics.median(positives),
        "negative_max": max(negatives),
        "negative_median": statistics.median(negatives),
        "kept_positive": kept_positive,
        "positive_total": len(positives),
        "removed_negative": removed_negative,
        "negative_total": len(negatives),
        "false_positive": false_positive,
        "top_after": top_after,
        "real_db": [(ad.ad_id, ad.category, score) for score, ad, _ok in rows if ad.source == "real_db"],
        "rows": rows,
    }


def main() -> int:
    env = load_env(ENV_PATH)
    api_key = env.get("OPEN_ROUTER_API") or os.environ.get("OPEN_ROUTER_API")
    if not api_key:
        raise RuntimeError("OPEN_ROUTER_API is missing")

    db_categories = set(load_category_names())
    missing = sorted({name for spec in CATEGORY_SPECS.values() for name in spec["names"]} - db_categories)
    if missing:
        raise AssertionError(f"categories are not in DB: {missing}")

    ads = load_real_db_ads() + generate_ads()
    queries = build_queries()
    embeddings = embed_texts([q.text for q in queries] + [ad.text for ad in ads], api_key)
    query_embeddings = dict(zip([q.query_id for q in queries], embeddings[: len(queries)]))
    ad_embeddings = dict(zip([ad.ad_id for ad in ads], embeddings[len(queries) :]))

    reports = [analyze_query(q, query_embeddings[q.query_id], ads, ad_embeddings) for q in queries]
    cutoffs = [report["positive_p10"] for report in reports]
    recommended = min(cutoffs)
    sweep_thresholds = [0.45, 0.50] + [round(0.520 + step * 0.001, 3) for step in range(31)] + [0.58, 0.60, 0.62, 0.65]

    print(f"ads_total={len(ads)}")
    print(f"real_db_ads={sum(1 for ad in ads if ad.source == 'real_db')}")
    print(f"generated_ads={sum(1 for ad in ads if ad.source == 'generated')}")
    print(f"queries={len(queries)}")
    for report in reports:
        q = report["query"]
        print(
            "query_report="
            f"{q.category} cutoff_p10={report['positive_p10']:.3f} "
            f"pos_min={report['positive_min']:.3f} pos_median={report['positive_median']:.3f} "
            f"neg_max={report['negative_max']:.3f} neg_median={report['negative_median']:.3f} "
            f"kept_pos={report['kept_positive']}/{report['positive_total']} "
            f"removed_neg={report['removed_negative']}/{report['negative_total']} "
            f"false_pos={report['false_positive']}"
        )
        print("  top_after=" + ",".join(f"{ad_id}:{cat}:{score:.3f}:{'ok' if ok else 'bad'}" for ad_id, cat, score, ok in report["top_after"]))
        if report["real_db"]:
            print("  real_db=" + ",".join(f"{ad_id}:{cat}:{score:.3f}" for ad_id, cat, score in report["real_db"]))
    sweep_metrics = []
    for threshold in sweep_thresholds:
        positive_total = negative_total = kept_positive = removed_negative = 0
        top5_bad = top5_total = 0
        for report in reports:
            positive_total += report["positive_total"]
            negative_total += report["negative_total"]
            kept_positive += sum(1 for score, _ad, ok in report["rows"] if ok and score >= threshold)
            removed_negative += sum(1 for score, _ad, ok in report["rows"] if not ok and score < threshold)
            top_after_threshold = sorted(
                [
                    (score, ok)
                    for score, _ad, ok in report["rows"]
                    if score >= threshold
                ],
                reverse=True,
            )[:LIMIT]
            top5_bad += sum(1 for _score, ok in top_after_threshold if not ok)
            top5_total += len(top_after_threshold)
        kept_positive_rate = kept_positive / positive_total
        removed_negative_rate = removed_negative / negative_total
        sweep_metrics.append((threshold, kept_positive_rate, removed_negative_rate, top5_bad, top5_total))
        print(
            "threshold_sweep="
            f"{threshold:.3f} kept_pos={kept_positive}/{positive_total} "
            f"removed_neg={removed_negative}/{negative_total} "
            f"top5_bad={top5_bad}/{top5_total}"
        )
    practical_candidates = [
        threshold
        for threshold, kept_positive_rate, removed_negative_rate, _top5_bad, _top5_total in sweep_metrics
        if kept_positive_rate >= 0.65 and removed_negative_rate >= 0.75
    ]
    practical_cutoff = practical_candidates[-1] if practical_candidates else 0.55
    print(f"minimum_recall_cutoff={recommended:.3f}")
    print(f"recommended_practical_cutoff={practical_cutoff:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
