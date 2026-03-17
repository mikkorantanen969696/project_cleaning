from aiogram import types, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from database.database import async_session
from database.models import User, UserRole
from utils.keyboards import get_admin_menu, get_manager_menu, get_cleaner_menu

# Обработчики текстовых сообщений для кнопок меню

async def handle_admin_orders(message: Message, state: FSMContext):
    """Обработка кнопки 'Все заказы' для администратора"""
    async with async_session() as session:
        user = await session.get(User, message.from_user.id)
        
        if not user or user.role != UserRole.ADMIN:
            await message.answer("❌ У вас нет доступа к этой функции")
            return
        
        # Показываем список всех заказов
        await message.answer("📋 **Все заказы системы**\n\nФункция в разработке...")

async def handle_admin_users(message: Message, state: FSMContext):
    """Обработка кнопки 'Управление пользователями' для администратора"""
    async with async_session() as session:
        user = await session.get(User, message.from_user.id)
        
        if not user or user.role != UserRole.ADMIN:
            await message.answer("❌ У вас нет доступа к этой функции")
            return
        
        from handlers.admin_handlers import callback_admin_add_manager, callback_admin_remove_manager
        from utils.keyboards import get_admin_actions
        
        await message.answer("👥 **Управление пользователями**", reply_markup=get_admin_actions())

async def handle_admin_stats(message: Message, state: FSMContext):
    """Обработка кнопки 'Статистика' для администратора"""
    async with async_session() as session:
        user = await session.get(User, message.from_user.id)
        
        if not user or user.role != UserRole.ADMIN:
            await message.answer("❌ У вас нет доступа к этой функции")
            return
        
        from handlers.admin_handlers import callback_admin_stats
        from utils.keyboards import get_statistics_options
        
        await message.answer("📊 **Статистика**", reply_markup=get_statistics_options())

async def handle_admin_cities(message: Message, state: FSMContext):
    """Обработка кнопки 'Управление городами' для администратора"""
    async with async_session() as session:
        user = await session.get(User, message.from_user.id)
        
        if not user or user.role != UserRole.ADMIN:
            await message.answer("❌ У вас нет доступа к этой функции")
            return
        
        await message.answer("🏙️ **Управление городами**\n\nФункция в разработке...")

async def handle_admin_finance(message: Message, state: FSMContext):
    """Обработка кнопки 'Финансы' для администратора"""
    async with async_session() as session:
        user = await session.get(User, message.from_user.id)
        
        if not user or user.role != UserRole.ADMIN:
            await message.answer("❌ У вас нет доступа к этой функции")
            return
        
        await message.answer("💳 **Финансы**\n\nФункция в разработке...")

async def handle_admin_settings(message: Message, state: FSMContext):
    """Обработка кнопки 'Настройки' для администратора"""
    async with async_session() as session:
        user = await session.get(User, message.from_user.id)
        
        if not user or user.role != UserRole.ADMIN:
            await message.answer("❌ У вас нет доступа к этой функции")
            return
        
        await message.answer("⚙️ **Настройки**\n\nФункция в разработке...")

async def handle_admin_help(message: Message, state: FSMContext):
    """Обработка кнопки 'Помощь' для администратора"""
    async with async_session() as session:
        user = await session.get(User, message.from_user.id)
        
        if not user or user.role != UserRole.ADMIN:
            await message.answer("❌ У вас нет доступа к этой функции")
            return
        
        await message.answer(
            "❓ **Помощь администратора**\n\n"
            "Доступные команды:\n"
            "/start - Главное меню\n"
            "/admin - Панель администратора\n\n"
            "Основные функции:\n"
            "• Управление пользователями\n"
            "• Просмотр статистики\n"
            "• Управление городами\n"
            "• Финансовый контроль\n\n"
            "Для подробной информации смотрите документацию.",
            reply_markup=get_admin_menu()
        )

# Менеджерские обработчики
async def handle_manager_create_order(message: Message, state: FSMContext):
    """Обработка кнопки 'Создать заказ' для менеджера"""
    async with async_session() as session:
        user = await session.get(User, message.from_user.id)
        
        if not user or user.role != UserRole.MANAGER:
            await message.answer("❌ У вас нет доступа к этой функции")
            return
        
        await message.answer(
            "📝 Создание нового заказа\n\n"
            "Введите имя клиента:",
            reply_markup=types.ReplyKeyboardRemove()
        )
        from bot.main import OrderCreation
        await state.set_state(OrderCreation.client_name)

async def handle_manager_orders(message: Message, state: FSMContext):
    """Обработка кнопки 'Мои заказы' для менеджера"""
    async with async_session() as session:
        user = await session.get(User, message.from_user.id)
        
        if not user or user.role != UserRole.MANAGER:
            await message.answer("❌ У вас нет доступа к этой функции")
            return
        
        from handlers.manager_handlers import cmd_manager_orders
        await cmd_manager_orders(message, state)

async def handle_manager_stats(message: Message, state: FSMContext):
    """Обработка кнопки 'Статистика' для менеджера"""
    async with async_session() as session:
        user = await session.get(User, message.from_user.id)
        
        if not user or user.role != UserRole.MANAGER:
            await message.answer("❌ У вас нет доступа к этой функции")
            return
        
        from handlers.manager_handlers import cmd_manager_stats
        await cmd_manager_stats(message, state)

async def handle_manager_invoice(message: Message, state: FSMContext):
    """Обработка кнопки 'Выставить счет' для менеджера"""
    async with async_session() as session:
        user = await session.get(User, message.from_user.id)
        
        if not user or user.role != UserRole.MANAGER:
            await message.answer("❌ У вас нет доступа к этой функции")
            return
        
        from handlers.manager_handlers import cmd_manager_invoice
        await cmd_manager_invoice(message, state)

async def handle_manager_payment(message: Message, state: FSMContext):
    """Обработка кнопки 'Оплатить клинеру' для менеджера"""
    async with async_session() as session:
        user = await session.get(User, message.from_user.id)
        
        if not user or user.role != UserRole.MANAGER:
            await message.answer("❌ У вас нет доступа к этой функции")
            return
        
        from handlers.manager_handlers import cmd_manager_payment
        await cmd_manager_payment(message, state)

async def handle_manager_requisites(message: Message, state: FSMContext):
    """Обработка кнопки 'Реквизиты' для менеджера"""
    async with async_session() as session:
        user = await session.get(User, message.from_user.id)
        
        if not user or user.role != UserRole.MANAGER:
            await message.answer("❌ У вас нет доступа к этой функции")
            return
        
        from handlers.manager_handlers import cmd_manager_requisites
        await cmd_manager_requisites(message, state)

# Клинерские обработчики
async def handle_cleaner_available(message: Message, state: FSMContext):
    """Обработка кнопки 'Доступные заказы' для клинера"""
    async with async_session() as session:
        user = await session.get(User, message.from_user.id)
        
        if not user or user.role != UserRole.CLEANER:
            await message.answer("❌ У вас нет доступа к этой функции")
            return
        
        from handlers.cleaner_handlers import cmd_cleaner_available_orders
        await cmd_cleaner_available_orders(message, state)

async def handle_cleaner_orders(message: Message, state: FSMContext):
    """Обработка кнопки 'Мои заказы' для клинера"""
    async with async_session() as session:
        user = await session.get(User, message.from_user.id)
        
        if not user or user.role != UserRole.CLEANER:
            await message.answer("❌ У вас нет доступа к этой функции")
            return
        
        from handlers.cleaner_handlers import cmd_cleaner_my_orders
        await cmd_cleaner_my_orders(message, state)

async def handle_cleaner_photos(message: Message, state: FSMContext):
    """Обработка кнопки 'Загрузить фото' для клинера"""
    async with async_session() as session:
        user = await session.get(User, message.from_user.id)
        
        if not user or user.role != UserRole.CLEANER:
            await message.answer("❌ У вас нет доступа к этой функции")
            return
        
        from handlers.cleaner_handlers import cmd_cleaner_upload_photos
        await cmd_cleaner_upload_photos(message, state)

async def handle_cleaner_payment(message: Message, state: FSMContext):
    """Обработка кнопки 'Мои реквизиты' для клинера"""
    async with async_session() as session:
        user = await session.get(User, message.from_user.id)
        
        if not user or user.role != UserRole.CLEANER:
            await message.answer("❌ У вас нет доступа к этой функции")
            return
        
        from handlers.cleaner_handlers import cmd_cleaner_payment_details
        await cmd_cleaner_payment_details(message, state)

async def handle_cleaner_get_payment(message: Message, state: FSMContext):
    """Обработка кнопки 'Получить оплату' для клинера"""
    async with async_session() as session:
        user = await session.get(User, message.from_user.id)
        
        if not user or user.role != UserRole.CLEANER:
            await message.answer("❌ У вас нет доступа к этой функции")
            return
        
        await message.answer(
            "💰 **Получение оплаты**\n\n"
            "Оплата за выполненные заказы поступает на ваши реквизиты.\n\n"
            "Текущий статус:\n"
            "• Ожидает выполнения: 0 заказов\n"
            "• Ожидает оплаты: 0 заказов\n"
            "• Оплачено: 0 заказов\n\n"
            "Для обновления реквизитов используйте кнопку '💳 Мои реквизиты'."
        )
