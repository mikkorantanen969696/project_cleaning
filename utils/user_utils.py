import os
from database.database import async_session
from database.models import User, UserRole
from sqlalchemy import select

async def get_or_create_user(telegram_id: int, username: str, full_name: str):
    """Безопасное получение или создание пользователя"""
    async with async_session() as session:
        # Сначала пытаемся получить существующего пользователя
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        
        if user:
            # Обновляем информацию если изменилась
            if user.username != username or user.full_name != full_name:
                user.username = username
                user.full_name = full_name
                await session.commit()
            return user
        else:
            # Создаем нового пользователя
            admin_id = int(os.getenv("ADMIN_TELEGRAM_ID", "0"))
            
            if telegram_id == admin_id:
                # Создаем администратора
                user = User(
                    telegram_id=telegram_id,
                    username=username,
                    full_name=full_name,
                    role=UserRole.ADMIN,
                    is_active=True
                )
            else:
                # Создаем неактивного пользователя до авторизации
                user = User(
                    telegram_id=telegram_id,
                    username=username,
                    full_name=full_name,
                    role=UserRole.MANAGER,  # Временно, до авторизации
                    is_active=False  # Неактивен до авторизации
                )
            
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return user
