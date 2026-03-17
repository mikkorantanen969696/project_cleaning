import asyncio
import os
import sys
from aiogram import types, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

# Добавляем корневую директорию проекта в Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.database import get_session
from database.models import User, UserRole, Order, OrderStatus, City
from handlers import admin_handlers, manager_handlers, cleaner_handlers, order_handlers
from utils.keyboards import get_manager_menu
from datetime import datetime

# Menu callbacks
async def callback_handle_menu(callback: CallbackQuery, state: FSMContext):
    action = callback.data.split("_")[1]
    
    if action == "orders":
        await callback.message.answer("📋 Функция заказов в разработке...")
    elif action == "create_order":
        await callback.message.answer(
            "📝 Создание нового заказа\n\n"
            "Введите имя клиента:",
            reply_markup=types.ReplyKeyboardRemove()
        )
        from bot.main import OrderCreation
        await state.set_state(OrderCreation.client_name)
    elif action == "stats":
        await callback.message.answer("📊 Функция статистики в разработке...")
    elif action == "users":
        await callback.message.answer("👥 Функция управления пользователями в разработке...")
    
    await callback.answer()

async def callback_admin_add_manager(callback: CallbackQuery, state: FSMContext):
    await admin_handlers.callback_admin_add_manager(callback, state)

async def callback_admin_remove_manager(callback: CallbackQuery, state: FSMContext):
    await admin_handlers.callback_admin_remove_manager(callback, state)

async def callback_remove_manager(callback: CallbackQuery, state: FSMContext):
    await admin_handlers.callback_remove_manager(callback, state)

async def callback_admin_stats(callback: CallbackQuery, state: FSMContext):
    await admin_handlers.callback_admin_stats(callback, state)

async def callback_stats_general(callback: CallbackQuery, state: FSMContext):
    await admin_handlers.callback_stats_general(callback, state)

async def callback_stats_managers(callback: CallbackQuery, state: FSMContext):
    await admin_handlers.callback_stats_managers(callback, state)

async def callback_admin_cities(callback: CallbackQuery, state: FSMContext):
    await admin_handlers.callback_admin_cities(callback, state)

async def callback_admin_export(callback: CallbackQuery, state: FSMContext):
    await admin_handlers.callback_admin_export(callback, state)

async def callback_admin_back(callback: CallbackQuery, state: FSMContext):
    await admin_handlers.callback_admin_back(callback, state)

# Manager callbacks
async def callback_invoice_order(callback: CallbackQuery, state: FSMContext):
    await manager_handlers.callback_invoice_order(callback, state)

async def callback_pay_cleaner(callback: CallbackQuery, state: FSMContext):
    await manager_handlers.callback_pay_cleaner(callback, state)

# Cleaner callbacks
async def callback_photo_order(callback: CallbackQuery, state: FSMContext):
    await cleaner_handlers.callback_photo_order(callback, state)

async def callback_upload_photo(callback: CallbackQuery, state: FSMContext):
    await cleaner_handlers.callback_upload_photo(callback, state)

# Order callbacks
async def callback_take_order(callback: CallbackQuery, state: FSMContext):
    await order_handlers.callback_take_order(callback, state)

async def callback_reject_order(callback: CallbackQuery, state: FSMContext):
    await order_handlers.callback_reject_order(callback, state)

async def callback_contact_manager(callback: CallbackQuery, state: FSMContext):
    await order_handlers.callback_contact_manager(callback, state)

async def callback_edit_order(callback: CallbackQuery, state: FSMContext):
    await order_handlers.callback_edit_order(callback, state)

async def callback_cancel_order(callback: CallbackQuery, state: FSMContext):
    await order_handlers.callback_cancel_order(callback, state)

async def callback_order_details(callback: CallbackQuery, state: FSMContext):
    await order_handlers.callback_order_details(callback, state)

async def callback_refresh_orders(callback: CallbackQuery, state: FSMContext):
    await order_handlers.callback_refresh_orders(callback, state)

# Order creation callbacks
async def callback_process_city(callback: CallbackQuery, state: FSMContext):
    city_id = int(callback.data.split("_")[1])
    await state.update_data(city_id=city_id)
    
    await callback.message.answer(
        "Выберите тип уборки:",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="🧹 Регулярная уборка", callback_data="type_regular")],
            [types.InlineKeyboardButton(text="🧼 Глубокая уборка", callback_data="type_deep")],
            [types.InlineKeyboardButton(text="🏗️ Послестроительная уборка", callback_data="type_post_repair")],
            [types.InlineKeyboardButton(text="🪟 Уборка окон", callback_data="type_windows")]
        ])
    )
    await callback.answer()

async def callback_process_cleaning_type(callback: CallbackQuery, state: FSMContext):
    cleaning_type = callback.data.split("_")[1]
    await state.update_data(cleaning_type=cleaning_type)
    
    await callback.message.answer(
        "Введите дату и время уборки (формат: ДД.ММ.ГГГГ ЧЧ:ММ):"
    )
    from bot.main import OrderCreation
    await state.set_state(OrderCreation.date_time)
    await callback.answer()

async def callback_process_equipment(callback: CallbackQuery, state: FSMContext):
    equipment = callback.data.split("_")[1] == "yes"
    await state.update_data(equipment_available=equipment)
    
    await callback.message.answer(
        "Моющие средства на месте?",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="✅ Да", callback_data="chemicals_yes")],
            [types.InlineKeyboardButton(text="❌ Нет", callback_data="chemicals_no")]
        ])
    )
    await callback.answer()

async def callback_process_chemicals(callback: CallbackQuery, state: FSMContext):
    chemicals = callback.data.split("_")[1] == "yes"
    await state.update_data(chemicals_available=chemicals)
    
    await callback.message.answer(
        "Введите дополнительные примечания (или отправьте /skip):"
    )
    from bot.main import OrderCreation
    await state.set_state(OrderCreation.notes)
    await callback.answer()

# Register all callbacks
def register_callbacks(dp):
    dp.callback_query.register(callback_handle_menu, F.data.startswith("menu_"))
    
    # Admin callbacks
    dp.callback_query.register(callback_admin_add_manager, F.data == "admin_add_manager")
    dp.callback_query.register(callback_admin_remove_manager, F.data == "admin_remove_manager")
    dp.callback_query.register(callback_remove_manager, F.data.startswith("remove_manager_"))
    dp.callback_query.register(callback_admin_stats, F.data == "admin_stats")
    dp.callback_query.register(callback_stats_general, F.data == "stats_general")
    dp.callback_query.register(callback_stats_managers, F.data == "stats_managers")
    dp.callback_query.register(callback_admin_cities, F.data == "admin_cities")
    dp.callback_query.register(callback_admin_export, F.data == "admin_export")
    dp.callback_query.register(callback_admin_back, F.data == "admin_back")
    
    # Manager callbacks
    dp.callback_query.register(callback_invoice_order, F.data.startswith("invoice_"))
    dp.callback_query.register(callback_pay_cleaner, F.data.startswith("pay_cleaner_"))
    
    # Cleaner callbacks
    dp.callback_query.register(callback_photo_order, F.data.startswith("photo_order_"))
    dp.callback_query.register(callback_upload_photo, F.data.startswith("upload_"))
    
    # Order callbacks
    dp.callback_query.register(callback_take_order, F.data.startswith("order_take_"))
    dp.callback_query.register(callback_reject_order, F.data.startswith("order_reject_"))
    dp.callback_query.register(callback_contact_manager, F.data.startswith("order_contact_"))
    dp.callback_query.register(callback_edit_order, F.data.startswith("order_edit_"))
    dp.callback_query.register(callback_cancel_order, F.data.startswith("order_cancel_"))
    dp.callback_query.register(callback_order_details, F.data.startswith("order_details_"))
    dp.callback_query.register(callback_refresh_orders, F.data == "refresh_orders")
    
    # Order creation callbacks
    dp.callback_query.register(callback_process_city, F.data.startswith("city_"))
    dp.callback_query.register(callback_process_cleaning_type, F.data.startswith("type_"))
    dp.callback_query.register(callback_process_equipment, F.data.startswith("equipment_"))
    dp.callback_query.register(callback_process_chemicals, F.data.startswith("chemicals_"))
