import asyncio
import os
from dotenv import load_dotenv

from database.database import init_db, get_session
from database.models import City

load_dotenv()

async def setup_cities():
    """Setup cities with Telegram topic IDs"""
    await init_db()
    
    cities_data = [
        {"name": "Краснодар", "telegram_topic_id": "3824746585_27"},
        {"name": "Красноярск", "telegram_topic_id": "3824746585_25"},
        {"name": "Пермь", "telegram_topic_id": "3824746585_23"},
        {"name": "Самара", "telegram_topic_id": "3824746585_21"},
        {"name": "Нижний Новгород", "telegram_topic_id": "3824746585_19"},
        {"name": "Воронеж", "telegram_topic_id": "3824746585_17"},
        {"name": "Казань", "telegram_topic_id": "3824746585_13"},
        {"name": "Уфа", "telegram_topic_id": "3824746585_11"},
        {"name": "Омск", "telegram_topic_id": "3824746585_9"},
        {"name": "Ростов-на-Дону", "telegram_topic_id": "3824746585_4"},
        {"name": "Новосибирск", "telegram_topic_id": "3824746585_2"},
    ]
    
    async with get_session() as session:
        for city_data in cities_data:
            existing_city = await session.execute(
                "SELECT id FROM cities WHERE name = :name",
                {"name": city_data["name"]}
            )
            existing_city = existing_city.fetchone()
            
            if not existing_city:
                city = City(
                    name=city_data["name"],
                    telegram_topic_id=city_data["telegram_topic_id"],
                    is_active=True
                )
                session.add(city)
                print(f"✅ Добавлен город: {city_data['name']}")
            else:
                print(f"⚠️ Город уже существует: {city_data['name']}")
        
        await session.commit()
        print("🎉 Города успешно настроены!")

if __name__ == "__main__":
    asyncio.run(setup_cities())
