import asyncio
import sys
import os
from dotenv import load_dotenv

# Добавляем корневую директорию проекта в Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.database import init_db, async_session
from database.models import User, UserRole
from sqlalchemy import select, text

load_dotenv()

async def check_user():
    """Проверка пользователя в базе данных"""
    await init_db()
    
    admin_id = int(os.getenv("ADMIN_TELEGRAM_ID", "864433722"))
    print(f"Проверяем пользователя с ID: {admin_id}")
    
    async with async_session() as session:
        # Проверяем прямым SQL запросом
        result = await session.execute(
            text("SELECT * FROM users WHERE telegram_id = :telegram_id"),
            {"telegram_id": admin_id}
        )
        user = result.fetchone()
        
        print(f"Результат прямого запроса: {user}")
        
        # Проверяем через SQLAlchemy
        result = await session.execute(
            select(User).where(User.telegram_id == admin_id)
        )
        user_sqla = result.scalar_one_or_none()
        
        print(f"Результат SQLAlchemy: {user_sqla}")
        
        if user_sqla:
            print(f"Пользователь найден:")
            print(f"  ID: {user_sqla.telegram_id}")
            print(f"  Username: {user_sqla.username}")
            print(f"  Full Name: {user_sqla.full_name}")
            print(f"  Role: {user_sqla.role}")
            print(f"  Is Active: {user_sqla.is_active}")
        else:
            print("Пользователь НЕ найден в базе данных!")
            
            # Создаем пользователя если не найден
            print("Создаем администратора...")
            new_user = User(
                telegram_id=admin_id,
                username="maks_krivosheev",
                full_name="mk",
                role=UserRole.ADMIN,
                is_active=True
            )
            session.add(new_user)
            await session.commit()
            await session.refresh(new_user)
            
            print(f"Создан пользователь:")
            print(f"  ID: {new_user.telegram_id}")
            print(f"  Role: {new_user.role}")
            print(f"  Is Active: {new_user.is_active}")

if __name__ == "__main__":
    asyncio.run(check_user())
