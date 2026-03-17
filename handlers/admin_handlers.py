from aiogram import types, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database.database import get_session
from database.models import User, UserRole, Order, OrderStatus, City
from utils.keyboards import get_admin_actions, get_statistics_options
from utils.statistics import StatisticsManager
import random
import string

class AdminStates(StatesGroup):
    add_manager_username = State()
    add_manager_password = State()
    remove_manager_id = State()
    add_city_name = State()
    add_city_topic = State()

async def is_admin(telegram_id: int) -> bool:
    async with get_session() as session:
        user = await session.get(User, telegram_id)
        return user and user.role == UserRole.ADMIN and user.is_active

def generate_password(length=8):
    """Generate random password for manager"""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

# Admin command handlers
async def cmd_admin_panel(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа к админ-панели")
        return
    
    await message.answer("🔧 Панель администратора", reply_markup=get_admin_actions())

async def callback_admin_add_manager(callback: CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен")
        return
    
    await callback.message.answer(
        "➕ Добавление менеджера\n\n"
        "Введите username менеджера (без @):"
    )
    await state.set_state(AdminStates.add_manager_username)
    await callback.answer()

async def process_add_manager_username(message: Message, state: FSMContext):
    username = message.text.strip().lstrip('@')
    
    async with get_session() as session:
        # Check if user exists
        existing_user = await session.execute(
            "SELECT id FROM users WHERE username = :username",
            {"username": username}
        )
        existing_user = existing_user.fetchone()
        
        if existing_user:
            await message.answer("❌ Пользователь с таким username уже существует в системе")
            return
        
        # Generate password
        password = generate_password()
        
        # Create manager (temporarily without telegram_id)
        await message.answer(
            f"🔑 Пароль для менеджера: `{password}`\n\n"
            "Отправьте этот пароль менеджеру. "
            "Когда менеджер впервые запустит бота, он сможет авторизоваться с этим паролем.\n\n"
            "Введите ID Telegram менеджера (или отправьте /skip для добавления позже):"
        )
        await state.update_data(username=username, password=password)
        await state.set_state(AdminStates.add_manager_password)

async def process_add_manager_telegram_id(message: Message, state: FSMContext):
    data = await state.get_data()
    
    try:
        telegram_id = int(message.text)
    except ValueError:
        await message.answer("❌ Неверный ID. Введите число или /skip")
        return
    
    async with get_session() as session:
        # Check if user with this telegram_id exists
        existing_user = await session.get(User, telegram_id)
        
        if existing_user:
            await message.answer("❌ Пользователь с таким Telegram ID уже существует")
            return
        
        # Create manager
        manager = User(
            telegram_id=telegram_id,
            username=data["username"],
            role=UserRole.MANAGER,
            password=data["password"],
            is_active=True
        )
        
        session.add(manager)
        await session.commit()
        
        await message.answer(
            f"✅ Менеджер @{data['username']} успешно добавлен!\n\n"
            f"🔑 Пароль: `{data['password']}`\n"
            f"🆔 Telegram ID: {telegram_id}\n\n"
            "Менеджер может теперь авторизоваться в боте.",
            reply_markup=get_admin_actions()
        )
    
    await state.clear()

async def cmd_skip_add_manager(message: Message, state: FSMContext):
    data = await state.get_data()
    
    await message.answer(
        f"✅ Менеджер @{data['username']} добавлен в базу данных.\n\n"
        f"🔑 Пароль: `{data['password']}`\n\n"
        "Менеджер сможет авторизоваться когда запустит бота и введет этот пароль.",
        reply_markup=get_admin_actions()
    )
    
    await state.clear()

async def callback_admin_remove_manager(callback: CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен")
        return
    
    async with get_session() as session:
        managers = await session.execute(
            "SELECT id, username, full_name FROM users WHERE role = 'manager' AND is_active = true"
        )
        managers = managers.fetchall()
        
        if not managers:
            await callback.message.answer("❌ Нет активных менеджеров для удаления")
            await callback.answer()
            return
        
        keyboard = []
        for manager_id, username, full_name in managers:
            display_name = f"@{username}" if username else full_name or f"ID: {manager_id}"
            keyboard.append([
                InlineKeyboardButton(
                    text=f"❌ {display_name}",
                    callback_data=f"remove_manager_{manager_id}"
                )
            ])
        
        keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")])
        
        await callback.message.answer(
            "➖ Удаление менеджера\n\n"
            "Выберите менеджера для удаления:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
        await callback.answer()

async def callback_remove_manager(callback: CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен")
        return
    
    manager_id = int(callback.data.split("_")[2])
    
    async with get_session() as session:
        manager = await session.get(User, manager_id)
        
        if not manager or manager.role != UserRole.MANAGER:
            await callback.message.answer("❌ Менеджер не найден")
            await callback.answer()
            return
        
        # Deactivate manager instead of deleting
        manager.is_active = False
        await session.commit()
        
        await callback.message.answer(
            f"✅ Менеджер @{manager.username or 'N/A'} деактивирован",
            reply_markup=get_admin_actions()
        )
    
    await callback.answer()

async def callback_admin_stats(callback: CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен")
        return
    
    await callback.message.answer(
        "📊 Статистика\n\n"
        "Выберите тип статистики:",
        reply_markup=get_statistics_options()
    )
    await callback.answer()

async def callback_stats_general(callback: CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен")
        return
    
    stats_manager = StatisticsManager()
    stats = await stats_manager.get_general_stats()
    
    await callback.message.answer(
        f"📊 **Общая статистика**\n\n"
        f"📋 Всего заказов: {stats['total_orders']}\n"
        f"✅ Выполнено: {stats['completed_orders']}\n"
        f"❌ Отменено: {stats['cancelled_orders']}\n"
        f"📈 Процент выполнения: {stats['completion_rate']:.1f}%\n"
        f"💰 Общая выручка: {stats['total_revenue']:.2f} руб.\n"
        f"💳 Средний чек: {stats['avg_order_value']:.2f} руб."
    )
    await callback.answer()

async def callback_stats_managers(callback: CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен")
        return
    
    stats_manager = StatisticsManager()
    stats = await stats_manager.get_manager_stats()
    
    if not stats:
        await callback.message.answer("📊 Нет данных по менеджерам")
        await callback.answer()
        return
    
    message_text = "📊 **Статистика по менеджерам**\n\n"
    
    for manager_stat in stats[:10]:  # Limit to first 10
        message_text += (
            f"👤 {manager_stat['manager_name']}\n"
            f"📋 Заказов: {manager_stat['total_orders']}\n"
            f"✅ Выполнено: {manager_stat['completed_orders']}\n"
            f"📈 Процент: {manager_stat['completion_rate']:.1f}%\n"
            f"💰 Выручка: {manager_stat['total_revenue']:.2f} руб.\n\n"
        )
    
    await callback.message.answer(message_text)
    await callback.answer()

async def callback_admin_cities(callback: CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен")
        return
    
    async with get_session() as session:
        cities = await session.execute("SELECT id, name, telegram_topic_id FROM cities")
        cities = cities.fetchall()
        
        if not cities:
            await callback.message.answer("🏙️ Городов пока нет. Добавьте первый город:")
            await callback.answer()
            return
        
        message_text = "🏙️ **Список городов**\n\n"
        
        for city_id, name, topic_id in cities:
            status = "🟢 Активен" if topic_id else "🔴 Не настроен"
            message_text += f"📍 {name} - {status}\n"
        
        await callback.message.answer(message_text)
    
    await callback.answer()

async def callback_admin_export(callback: CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен")
        return
    
    await callback.message.answer(
        "📄 **Экспорт данных**\n\n"
        "Выберите формат экспорта:\n\n"
        "📊 Excel - Полная статистика\n"
        "📄 PDF - Отчеты\n"
        "💾 CSV - Сырые данные\n\n"
        "Функция в разработке..."
    )
    await callback.answer()

async def callback_admin_back(callback: CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен")
        return
    
    await callback.message.answer("🔧 Панель администратора", reply_markup=get_admin_actions())
    await callback.answer()
