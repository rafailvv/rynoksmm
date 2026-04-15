from dataclasses import dataclass


@dataclass(frozen=True)
class PaymentPlan:
    plan_id: str
    price: int
    days: int
    req: str


PAYMENT_PLANS = {
    "subscription_30": PaymentPlan(
        plan_id="subscription_30",
        price=1000,
        days=30,
        req="subscription",
    ),
    "subscription_90": PaymentPlan(
        plan_id="subscription_90",
        price=2700,
        days=90,
        req="subscription",
    ),
    "subscription_180": PaymentPlan(
        plan_id="subscription_180",
        price=4500,
        days=180,
        req="subscription",
    ),
    "subscription_360": PaymentPlan(
        plan_id="subscription_360",
        price=7200,
        days=360,
        req="subscription",
    ),
    "requests_50": PaymentPlan(
        plan_id="requests_50",
        price=990,
        days=50,
        req="requests",
    ),
    "requests_100": PaymentPlan(
        plan_id="requests_100",
        price=1490,
        days=100,
        req="requests",
    ),
    "requests_500": PaymentPlan(
        plan_id="requests_500",
        price=5990,
        days=500,
        req="requests",
    ),
}


def get_payment_plan(plan_id: str) -> PaymentPlan | None:
    return PAYMENT_PLANS.get(plan_id)
