import matplotlib.pyplot as plt
import io

async def send_daily_graph(app, chat_id):
    """מייצר ושולח גרף התפלגות איומים יומית"""
    labels = ['Rockets', 'Drones', 'False Alarms']
    # נתונים לדוגמה מה-storage שלך
    sizes = [70, 25, 5] 
    colors = ['#ff4b2b', '#ffb400', '#2ecc71']

    plt.figure(figsize=(6, 6))
    plt.pie(sizes, labels=labels, autopct='%1.1f%%', colors=colors, startangle=140)
    plt.title("סיכום איומים יומי - גזרת הצפון")

    # הפיכה לתמונה
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)

    await app.bot.send_photo(
        chat_id=chat_id,
        photo=buf,
        caption="📊 **הסיכום הסטטיסטי היומי שלך.**\nלילה שקט ובטוח."
    )
    plt.close()