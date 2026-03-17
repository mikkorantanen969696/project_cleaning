from aiogram import types, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database.database import get_session
from database.models import User, UserRole, Order, OrderStatus, City, Payment, PaymentStatus, OrderPhoto
from utils.keyboards import get_cleaner_menu, get_order_actions
from utils.qr_generator import generate_contact_qr
import os
from datetime import datetime

class CleanerStates(StatesGroup):
    photo_upload = State()
    payment_details = State()
    bank_details = State()

async def is_cleaner(telegram_id: int) -> bool:
    async with get_session() as session:
        user = await session.get(User, telegram_id)
        return user and user.role == UserRole.CLEANER and user.is_active

async def cmd_cleaner_available_orders(message: Message, state: FSMContext):
    if not await is_cleaner(message.from_user.id):
        await message.answer("❌ У вас нет доступа к функциям клинера")
        return
    
    async with get_session() as session:
        # Get cleaner's city
        cleaner = await session.get(User, message.from_user.id)
        
        if not cleaner.city_id:
            await message.answer("❌ У вас не указан город. Обратитесь к администратору.")
            return
        
        # Get available orders in cleaner's city
        orders = await session.execute(
            """SELECT o.id, o.client_name, o.address, o.cleaning_type, 
                      o.date_time, o.duration_hours, o.price
               FROM orders o 
               WHERE o.city_id = :city_id 
               AND o.status = 'new'
               ORDER BY o.date_time ASC""",
            {"city_id": cleaner.city_id}
        )
        orders = orders.fetchall()
        
        if not orders:
            await message.answer("📋 На данный момент нет доступных заказов")
            return
        
        message_text = "📋 **Доступные заказы**\n\n"
        
        for order in orders:
            message_text += (
                f"🆕 Заказ #{order.id}\n"
                f"👤 Клиент: {order.client_name}\n"
                f"📍 Адрес: {order.address}\n"
                f"🧹 Тип: {order.cleaning_type}\n"
                f"🕐 Время: {order.date_time.strftime('%d.%m.%Y %H:%M')}\n"
                f"⏱ Длительность: {order.duration_hours} ч.\n"
                f"💰 Цена: {order.price} руб.\n\n"
            )
        
        await message.answer(
            message_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📋 Обновить список", callback_data="refresh_orders")]
            ])
        )

async def cmd_cleaner_my_orders(message: Message, state: FSMContext):
    if not await is_cleaner(message.from_user.id):
        await message.answer("❌ У вас нет доступа к функциям клинера")
        return
    
    async with get_session() as session:
        orders = await session.execute(
            """SELECT o.id, o.client_name, o.address, o.status, o.date_time, o.price
               FROM orders o 
               WHERE o.cleaner_id = :cleaner_id 
               ORDER BY o.created_at DESC""",
            {"cleaner_id": message.from_user.id}
        )
        orders = orders.fetchall()
        
        if not orders:
            await message.answer("📋 У вас пока нет заказов")
            return
        
        message_text = "📋 **Мои заказы**\n\n"
        
        for order in orders:
            status_emoji = {
                OrderStatus.ASSIGNED: "👤",
                OrderStatus.IN_PROGRESS: "🔄",
                OrderStatus.COMPLETED: "✅",
                OrderStatus.CANCELLED: "❌"
            }.get(order.status, "❓")
            
            message_text += (
                f"{status_emoji} Заказ #{order.id}\n"
                f"👤 Клиент: {order.client_name}\n"
                f"📍 Адрес: {order.address}\n"
                f"💰 Цена: {order.price} руб.\n"
                f"📅 {order.date_time.strftime('%d.%m.%Y %H:%M')}\n\n"
            )
        
        await message.answer(message_text, reply_markup=get_cleaner_menu())

async def cmd_cleaner_upload_photos(message: Message, state: FSMContext):
    if not await is_cleaner(message.from_user.id):
        await message.answer("❌ У вас нет доступа к функциям клинера")
        return
    
    async with get_session() as session:
        # Get cleaner's active orders
        orders = await session.execute(
            """SELECT o.id, o.client_name, o.address
               FROM orders o 
               WHERE o.cleaner_id = :cleaner_id 
               AND o.status IN ('assigned', 'in_progress')
               ORDER BY o.created_at DESC""",
            {"cleaner_id": message.from_user.id}
        )
        orders = orders.fetchall()
        
        if not orders:
            await message.answer("📋 У вас нет активных заказов для загрузки фото")
            return
        
        keyboard = []
        for order_id, client_name, address in orders:
            keyboard.append([
                InlineKeyboardButton(
                    text=f"📸 Заказ #{order_id} - {client_name}",
                    callback_data=f"photo_order_{order_id}"
                )
            ])
        
        await message.answer(
            "📸 **Выберите заказ для загрузки фото**\n\n"
            "Загрузите фото 'до' и 'после' выполнения работ:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )

async def callback_photo_order(callback: CallbackQuery, state: FSMContext):
    if not await is_cleaner(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен")
        return
    
    order_id = int(callback.data.split("_")[2])
    
    async with get_session() as session:
        order = await session.get(Order, order_id)
        
        if not order or order.cleaner_id != callback.from_user.id:
            await callback.message.answer("❌ Заказ не найден или у вас нет к нему доступа")
            await callback.answer()
            return
        
        # Check existing photos
        existing_photos = await session.execute(
            "SELECT photo_type FROM order_photos WHERE order_id = :order_id",
            {"order_id": order_id}
        )
        existing_photos = [row[0] for row in existing_photos.fetchall()]
        
        message_text = f"📸 **Фото для заказа #{order_id}**\n\n"
        
        if "before" in existing_photos:
            message_text += "✅ Фото 'ДО' загружено\n"
        else:
            message_text += "❌ Фото 'ДО' не загружено\n"
        
        if "after" in existing_photos:
            message_text += "✅ Фото 'ПОСЛЕ' загружено\n"
        else:
            message_text += "❌ Фото 'ПОСЛЕ' не загружено\n"
        
        keyboard = []
        
        if "before" not in existing_photos:
            keyboard.append([
                InlineKeyboardButton(text="📷 Загрузить фото 'ДО'", callback_data=f"upload_before_{order_id}")
            ])
        
        if "after" not in existing_photos:
            keyboard.append([
                InlineKeyboardButton(text="📷 Загрузить фото 'ПОСЛЕ'", callback_data=f"upload_after_{order_id}")
            ])
        
        keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_orders")])
        
        await callback.message.answer(
            message_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
    
    await callback.answer()

async def callback_upload_photo(callback: CallbackQuery, state: FSMContext):
    if not await is_cleaner(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен")
        return
    
    photo_type = callback.data.split("_")[1]  # before or after
    order_id = int(callback.data.split("_")[2])
    
    await state.update_data(photo_type=photo_type, order_id=order_id)
    
    await callback.message.answer(
        f"📷 Загрузите фото '{photo_type.upper()}' для заказа #{order_id}:"
    )
    await state.set_state(CleanerStates.photo_upload)
    await callback.answer()

async def process_photo_upload(message: Message, state: FSMContext):
    if not message.photo:
        await message.answer("❌ Пожалуйста, отправьте фото")
        return
    
    data = await state.get_data()
    photo_type = data["photo_type"]
    order_id = data["order_id"]
    
    async with get_session() as session:
        order = await session.get(Order, order_id)
        
        if not order or order.cleaner_id != message.from_user.id:
            await message.answer("❌ Заказ не найден или у вас нет к нему доступа")
            await state.clear()
            return
        
        # Save photo
        photo_file_id = message.photo[-1].file_id
        
        # Check if photo already exists
        existing_photo = await session.execute(
            "SELECT id FROM order_photos WHERE order_id = :order_id AND photo_type = :photo_type",
            {"order_id": order_id, "photo_type": photo_type}
        )
        existing_photo = existing_photo.fetchone()
        
        if existing_photo:
            # Update existing photo
            await session.execute(
                "UPDATE order_photos SET file_id = :file_id WHERE id = :id",
                {"file_id": photo_file_id, "id": existing_photo[0]}
            )
        else:
            # Create new photo record
            photo = OrderPhoto(
                order_id=order_id,
                file_id=photo_file_id,
                photo_type=photo_type
            )
            session.add(photo)
        
        await session.commit()
        
        await message.answer(
            f"✅ Фото '{photo_type.upper()}' успешно загружено для заказа #{order_id}"
        )
        
        # Check if both photos are uploaded
        photos = await session.execute(
            "SELECT photo_type FROM order_photos WHERE order_id = :order_id",
            {"order_id": order_id}
        )
        photos = [row[0] for row in photos.fetchall()]
        
        if "before" in photos and "after" in photos:
            await message.answer(
                "🎉 Все фото загружены! Заказ готов к проверке.\n"
                "Менеджер проверит фото и подтвердит выполнение заказа."
            )
    
    await state.clear()

async def cmd_cleaner_payment_details(message: Message, state: FSMContext):
    if not await is_cleaner(message.from_user.id):
        await message.answer("❌ У вас нет доступа к функциям клинера")
        return
    
    async with get_session() as session:
        cleaner = await session.get(User, message.from_user.id)
        
        await message.answer(
            f"💳 **Ваши реквизиты**\n\n"
            f"📞 Телефон: {cleaner.phone or 'Не указан'}\n"
            f"🏦 Банковские данные: {cleaner.bank_details or 'Не указаны'}\n\n"
            f"Для обновления реквизитов используйте команду /update_requisites"
        )

async def cmd_update_requisites(message: Message, state: FSMContext):
    if not await is_cleaner(message.from_user.id):
        await message.answer("❌ У вас нет доступа к функциям клинера")
        return
    
    await message.answer(
        "💳 **Обновление реквизитов**\n\n"
        "Введите ваш номер телефона:"
    )
    await state.set_state(CleanerStates.payment_details)

async def process_payment_details(message: Message, state: FSMContext):
    phone = message.text.strip()
    
    async with get_session() as session:
        cleaner = await session.get(User, message.from_user.id)
        cleaner.phone = phone
        await session.commit()
        
        await message.answer(
            "✅ Телефон обновлен!\n\n"
            "Теперь введите ваши банковские данные (номер карты, реквизиты):"
        )
        await state.set_state(CleanerStates.bank_details)

async def process_bank_details(message: Message, state: FSMContext):
    bank_details = message.text.strip()
    
    async with get_session() as session:
        cleaner = await session.get(User, message.from_user.id)
        cleaner.bank_details = bank_details
        await session.commit()
        
        await message.answer(
            "✅ Банковские данные обновлены!\n\n"
            "Теперь вы можете получать оплату за выполненные заказы.",
            reply_markup=get_cleaner_menu()
        )
    
    await state.clear()

async def cmd_cleaner_help(message: Message, state: FSMContext):
    if not await is_cleaner(message.from_user.id):
        await message.answer("❌ У вас нет доступа к функциям клинера")
        return
    
    help_text = """
    📖 **Помощь для клинера**
    
    📋 **Доступные заказы:**
    - Нажмите "📋 Доступные заказы"
    - Выберите заказ для выполнения
    - Нажмите "Взять заказ"
    
    📸 **Загрузка фото:**
    - Нажмите "📸 Загрузить фото"
    - Выберите заказ
    - Загрузите фото "ДО" и "ПОСЛЕ"
    
    💳 **Получение оплаты:**
    - Обновите реквизиты в профиле
    - Дождитесь выполнения заказа
    - Получите оплату от менеджера
    
    📊 **Статистика:**
    - Просмотрите свои заказы
    - Отслеживайте выполнение
    
    ❓ **Если у вас возникли вопросы:**
    - Свяжитесь с менеджером
    - Используйте команду /help
    """
    
    await message.answer(help_text, reply_markup=get_cleaner_menu())
