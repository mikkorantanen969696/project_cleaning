import asyncio
import logging
import os
import sys
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# Добавляем корневую директорию проекта в Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.database import init_db, async_session
from database.models import User, UserRole, Order, OrderStatus, City
from utils.keyboards import get_main_menu, get_admin_menu, get_manager_menu, get_cleaner_menu
from utils.pdf_generator import generate_invoice_pdf
from utils.qr_generator import generate_payment_qr
from utils.user_utils import get_or_create_user
from bot.callbacks import register_callbacks
from handlers.cleaner_handlers import CleanerStates
from handlers.admin_handlers import AdminStates
import handlers.message_handlers

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OrderCreation(StatesGroup):
    client_name = State()
    client_phone = State()
    address = State()
    city = State()
    cleaning_type = State()
    date_time = State()
    duration = State()
    price = State()
    equipment = State()
    chemicals = State()
    notes = State()

class ManagerAuth(StatesGroup):
    password = State()

class AdminActions(StatesGroup):
    action = State()
    target_user = State()

bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher(storage=MemoryStorage())

async def check_user_role(telegram_id: int) -> UserRole:
    async with async_session() as session:
        user = await session.get(User, telegram_id)
        return user.role if user else None

async def is_authenticated(telegram_id: int) -> bool:
    async with async_session() as session:
        user = await session.get(User, telegram_id)
        return user is not None and user.is_active

@dp.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    
    # Безопасное получение или создание пользователя
    user = await get_or_create_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.full_name
    )
    
    if not user.is_active:
        # Если пользователь неактивен (новый менеджер)
        admin_id = int(os.getenv("ADMIN_TELEGRAM_ID", "0"))
        if message.from_user.id == admin_id:
            # Активируем администратора
            user.is_active = True
            async with async_session() as session:
                await session.commit()
            await message.answer(
                "👋 Добро пожаловать, Администратор!\n"
                "Вы успешно зарегистрированы как администратор системы.",
                reply_markup=get_admin_menu()
            )
        else:
            await message.answer(
                "🔐 Добро пожаловать в систему управления клинингом!\n\n"
                "Для доступа к системе необходимо авторизоваться.\n"
                "Пожалуйста, введите пароль, выданный администратором:",
                reply_markup=types.ReplyKeyboardRemove()
            )
            await state.set_state(ManagerAuth.password)
    else:
        # Активный пользователь - показываем соответствующее меню
        if user.role == UserRole.ADMIN:
            await message.answer("👋 Добро пожаловать, Администратор!", reply_markup=get_admin_menu())
        elif user.role == UserRole.MANAGER:
            await message.answer("👋 Добро пожаловать, Менеджер!", reply_markup=get_manager_menu())
        elif user.role == UserRole.CLEANER:
            await message.answer("👋 Добро пожаловать, Клинер!", reply_markup=get_cleaner_menu())

@dp.message(Command("admin"))
async def cmd_admin_panel(message: Message, state: FSMContext):
    from handlers.admin_handlers import cmd_admin_panel
    await cmd_admin_panel(message, state)

@dp.message(Command("manager_orders"))
async def cmd_manager_orders(message: Message, state: FSMContext):
    from handlers.manager_handlers import cmd_manager_orders
    await cmd_manager_orders(message, state)

@dp.message(Command("manager_stats"))
async def cmd_manager_stats(message: Message, state: FSMContext):
    from handlers.manager_handlers import cmd_manager_stats
    await cmd_manager_stats(message, state)

@dp.message(Command("manager_invoice"))
async def cmd_manager_invoice(message: Message, state: FSMContext):
    from handlers.manager_handlers import cmd_manager_invoice
    await cmd_manager_invoice(message, state)

@dp.message(Command("manager_payment"))
async def cmd_manager_payment(message: Message, state: FSMContext):
    from handlers.manager_handlers import cmd_manager_payment
    await cmd_manager_payment(message, state)

@dp.message(Command("manager_requisites"))
async def cmd_manager_requisites(message: Message, state: FSMContext):
    from handlers.manager_handlers import cmd_manager_requisites
    await cmd_manager_requisites(message, state)

@dp.message(Command("manager_help"))
async def cmd_manager_help(message: Message, state: FSMContext):
    from handlers.manager_handlers import cmd_manager_help
    await cmd_manager_help(message, state)

@dp.message(Command("cleaner_available"))
async def cmd_cleaner_available_orders(message: Message, state: FSMContext):
    from handlers.cleaner_handlers import cmd_cleaner_available_orders
    await cmd_cleaner_available_orders(message, state)

@dp.message(Command("cleaner_orders"))
async def cmd_cleaner_my_orders(message: Message, state: FSMContext):
    from handlers.cleaner_handlers import cmd_cleaner_my_orders
    await cmd_cleaner_my_orders(message, state)

@dp.message(Command("cleaner_photos"))
async def cmd_cleaner_upload_photos(message: Message, state: FSMContext):
    from handlers.cleaner_handlers import cmd_cleaner_upload_photos
    await cmd_cleaner_upload_photos(message, state)

@dp.message(Command("cleaner_payment"))
async def cmd_cleaner_payment_details(message: Message, state: FSMContext):
    from handlers.cleaner_handlers import cmd_cleaner_payment_details
    await cmd_cleaner_payment_details(message, state)

@dp.message(Command("update_requisites"))
async def cmd_update_requisites(message: Message, state: FSMContext):
    from handlers.cleaner_handlers import cmd_update_requisites
    await cmd_update_requisites(message, state)

@dp.message(Command("cleaner_help"))
async def cmd_cleaner_help(message: Message, state: FSMContext):
    from handlers.cleaner_handlers import cmd_cleaner_help
    await cmd_cleaner_help(message, state)

@dp.message(Command("skip"))
async def skip_notes(message: Message, state: FSMContext):
    await state.update_data(notes="")
    await create_order(message, state)

@dp.message(OrderCreation.notes)
async def process_notes(message: Message, state: FSMContext):
    await state.update_data(notes=message.text)
    await create_order(message, state)

@dp.message(ManagerAuth.password)
async def auth_manager(message: Message, state: FSMContext):
    password = message.text
    
    async with async_session() as session:
        user = await session.get(User, message.from_user.id)
        
        if user and user.password == password and user.role == UserRole.MANAGER:
            # Активируем менеджера
            user.is_active = True
            await session.commit()
            await message.answer(
                "✅ Авторизация успешна!\n"
                "Добро пожаловать в систему, Менеджер!",
                reply_markup=get_manager_menu()
            )
            await state.clear()
        else:
            await message.answer(
                "❌ Неверный пароль. Попробуйте еще раз или обратитесь к администратору."
            )

@dp.message(CleanerStates.payment_details)
async def process_payment_details(message: Message, state: FSMContext):
    from handlers.cleaner_handlers import process_payment_details
    await process_payment_details(message, state)

@dp.message(CleanerStates.bank_details)
async def process_bank_details(message: Message, state: FSMContext):
    from handlers.cleaner_handlers import process_bank_details
    await process_bank_details(message, state)

@dp.message(CleanerStates.photo_upload)
async def process_photo_upload(message: Message, state: FSMContext):
    from handlers.cleaner_handlers import process_photo_upload
    await process_photo_upload(message, state)

@dp.message(AdminStates.add_manager_username)
async def process_add_manager_username(message: Message, state: FSMContext):
    from handlers.admin_handlers import process_add_manager_username
    await process_add_manager_username(message, state)

@dp.message(AdminStates.add_manager_password)
async def process_add_manager_telegram_id(message: Message, state: FSMContext):
    from handlers.admin_handlers import process_add_manager_telegram_id
    await process_add_manager_telegram_id(message, state)

@dp.message(Command("skip"))
async def cmd_skip_add_manager(message: Message, state: FSMContext):
    from handlers.admin_handlers import cmd_skip_add_manager
    await cmd_skip_add_manager(message, state)

@dp.message(OrderCreation.client_name)
async def process_client_name(message: Message, state: FSMContext):
    await state.update_data(client_name=message.text)
    await message.answer("Введите телефон клиента:")
    await state.set_state(OrderCreation.client_phone)

@dp.message(OrderCreation.client_phone)
async def process_client_phone(message: Message, state: FSMContext):
    await state.update_data(client_phone=message.text)
    await message.answer("Введите адрес уборки:")
    await state.set_state(OrderCreation.address)

@dp.message(OrderCreation.address)
async def process_address(message: Message, state: FSMContext):
    await state.update_data(address=message.text)
    
    async with get_session() as session:
        cities = await session.execute("SELECT id, name FROM cities WHERE is_active = true")
        cities = cities.fetchall()
        
        keyboard = []
        for city_id, city_name in cities:
            keyboard.append([InlineKeyboardButton(text=city_name, callback_data=f"city_{city_id}")])
        
        await message.answer(
            "Выберите город:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )

@dp.message(OrderCreation.date_time)
async def process_date_time(message: Message, state: FSMContext):
    try:
        date_time = datetime.strptime(message.text, "%d.%m.%Y %H:%M")
        await state.update_data(date_time=date_time)
        
        await message.answer("Введите продолжительность в часах:")
        await state.set_state(OrderCreation.duration)
    except ValueError:
        await message.answer("❌ Неверный формат. Используйте: ДД.ММ.ГГГГ ЧЧ:ММ")

@dp.message(OrderCreation.duration)
async def process_duration(message: Message, state: FSMContext):
    try:
        duration = float(message.text)
        await state.update_data(duration=duration)
        
        await message.answer("Введите стоимость заказа:")
        await state.set_state(OrderCreation.price)
    except ValueError:
        await message.answer("❌ Введите корректное число")

@dp.message(OrderCreation.price)
async def process_price(message: Message, state: FSMContext):
    try:
        price = float(message.text)
        await state.update_data(price=price)
        
        await message.answer(
            "Оборудование на месте?",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✅ Да", callback_data="equipment_yes")],
                [InlineKeyboardButton(text="❌ Нет", callback_data="equipment_no")]
            ])
        )
    except ValueError:
        await message.answer("❌ Введите корректную сумму")

@dp.message(OrderCreation.notes)
async def process_order_notes(message: Message, state: FSMContext):
    await state.update_data(notes=message.text)
    await create_order(message, state)

async def create_order(message: Message, state: FSMContext):
    data = await state.get_data()
    
    async with async_session() as session:
        order = Order(
            client_name=data["client_name"],
            client_phone=data["client_phone"],
            address=data["address"],
            city_id=data["city_id"],
            cleaning_type=data["cleaning_type"],
            date_time=data["date_time"],
            duration_hours=data["duration"],
            price=data["price"],
            equipment_available=data["equipment_available"],
            chemicals_available=data["chemicals_available"],
            notes=data["notes"],
            manager_id=message.from_user.id
        )
        
        session.add(order)
        await session.commit()
        
        await message.answer(
            f"✅ Заказ успешно создан!\n\n"
            f"📋 Детали заказа:\n"
            f"👤 Клиент: {order.client_name}\n"
            f"📞 Телефон: {order.client_phone}\n"
            f"📍 Адрес: {order.address}\n"
            f"🕐 Время: {order.date_time.strftime('%d.%m.%Y %H:%M')}\n"
            f"💰 Стоимость: {order.price} руб.\n\n"
            f"Заказ отправлен в соответствующую тему города для клинеров.",
            reply_markup=get_manager_menu()
        )
    
    await state.clear()

async def main():
    await init_db()
    
    # Register all callbacks
    register_callbacks(dp)
    
    # Register message handlers
    from handlers.message_handlers import (
        handle_admin_orders, handle_admin_users, handle_admin_stats,
        handle_admin_cities, handle_admin_finance, handle_admin_settings, handle_admin_help,
        handle_manager_create_order, handle_manager_orders, handle_manager_stats,
        handle_manager_invoice, handle_manager_payment, handle_manager_requisites,
        handle_cleaner_available, handle_cleaner_orders, handle_cleaner_photos,
        handle_cleaner_payment, handle_cleaner_get_payment
    )
    
    # Admin message handlers
    dp.message.register(handle_admin_orders, F.text == "📋 Все заказы")
    dp.message.register(handle_admin_users, F.text == "👥 Управление пользователями")
    dp.message.register(handle_admin_stats, F.text == "📊 Статистика")
    dp.message.register(handle_admin_cities, F.text == "🏙️ Управление городами")
    dp.message.register(handle_admin_finance, F.text == "💳 Финансы")
    dp.message.register(handle_admin_settings, F.text == "⚙️ Настройки")
    dp.message.register(handle_admin_help, F.text == "❓ Помощь")
    
    # Manager message handlers
    dp.message.register(handle_manager_create_order, F.text == "📝 Создать заказ")
    dp.message.register(handle_manager_orders, F.text == "📋 Мои заказы")
    dp.message.register(handle_manager_stats, F.text == "📊 Статистика")
    dp.message.register(handle_manager_invoice, F.text == "💰 Выставить счет")
    dp.message.register(handle_manager_payment, F.text == "💳 Оплатить клинеру")
    dp.message.register(handle_manager_requisites, F.text == "📄 Реквизиты")
    
    # Cleaner message handlers
    dp.message.register(handle_cleaner_available, F.text == "📋 Доступные заказы")
    dp.message.register(handle_cleaner_orders, F.text == "🏠 Мои заказы")
    dp.message.register(handle_cleaner_photos, F.text == "📸 Загрузить фото")
    dp.message.register(handle_cleaner_payment, F.text == "💳 Мои реквизиты")
    dp.message.register(handle_cleaner_get_payment, F.text == "💰 Получить оплату")
    
    logger.info("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
