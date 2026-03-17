import asyncio
import sys
import os
from dotenv import load_dotenv

# Добавляем корневую директорию проекта в Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.database import init_db, async_session
from database.models import User, UserRole, City
from sqlalchemy import text

load_dotenv()

async def init_database():
    """Initialize database with basic data"""
    await init_db()
    
    async with async_session() as session:
        # Add default cities
        cities = [
            {"name": "Москва", "telegram_topic_id": "moscow_orders"},
            {"name": "Санкт-Петербург", "telegram_topic_id": "spb_orders"},
            {"name": "Новосибирск", "telegram_topic_id": "nsk_orders"},
            {"name": "Екатеринбург", "telegram_topic_id": "ekb_orders"},
            {"name": "Казань", "telegram_topic_id": "kzn_orders"},
        ]
        
        for city_data in cities:
            existing_city = await session.execute(
                text("SELECT id FROM cities WHERE name = :name"),
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
        
        # Create admin user
        admin_id = int(os.getenv("ADMIN_TELEGRAM_ID", "0"))
        if admin_id > 0:
            existing_admin = await session.get(User, admin_id)
            
            if not existing_admin:
                admin = User(
                    telegram_id=admin_id,
                    username=os.getenv("ADMIN_USERNAME", "admin"),
                    full_name="Administrator",
                    role=UserRole.ADMIN,
                    is_active=True
                )
                session.add(admin)
        
        await session.commit()
        print("✅ База данных успешно инициализирована!")

if __name__ == "__main__":
    asyncio.run(init_database())
