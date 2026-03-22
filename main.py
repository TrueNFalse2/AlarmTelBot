import asyncio
from bot import build_app
from config import POLL_INTERVAL_SECONDS
from storage import init_db, get_all_subscriptions, was_alert_sent, mark_alert_sent
from alert_engine import MultiSourceAlert, format_alert

source = MultiSourceAlert()


def area_matches(user_areas: set[str], alert_areas: list[str]) -> bool:
    user_areas_lower = [a.strip().lower() for a in user_areas]
    alert_areas_lower = [a.strip().lower() for a in alert_areas]

    for ua in user_areas_lower:
        for aa in alert_areas_lower:
            if ua in aa or aa in ua:
                return True
    return False


async def alert_loop(app):
    while True:
        try:
            alerts = source.fetch_alerts()
            subs = get_all_subscriptions()

            for alert in alerts:
                for chat_id, user_areas in subs.items():
                    if not area_matches(user_areas, alert.areas):
                        continue

                    if was_alert_sent(alert.alert_id, chat_id):
                        continue

                    await app.bot.send_message(
                        chat_id=chat_id,
                        text=format_alert(alert)
                    )
                    mark_alert_sent(alert.alert_id, chat_id)

        except Exception as e:
            print("loop error:", e)

        await asyncio.sleep(POLL_INTERVAL_SECONDS)


async def post_init(app):
    asyncio.create_task(alert_loop(app))


def main():
    init_db()
    app = build_app()
    app.post_init = post_init
    print("Bot started 🚀")
    app.run_polling()


if __name__ == "__main__":
    main()