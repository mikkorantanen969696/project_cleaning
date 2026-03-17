from aiogram import types, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database.database import get_session
from database.models import User, UserRole, Order, OrderStatus, City, Payment, PaymentStatus
from utils.keyboards import get_manager_menu, get_order_actions
from utils.pdf_generator import generate_invoice_pdf
from utils.qr_generator import generate_payment_qr
from utils.statistics import StatisticsManager
import os
from datetime import datetime

class ManagerStates(StatesGroup):
    invoice_order = State()
    payment_cleaner = State()
    cleaner_details = State()

async def is_manager(telegram_id: int) -> bool:
    async with get_session() as session:
        user = await session.get(User, telegram_id)
        return user and user.role == UserRole.MANAGER and user.is_active

async def cmd_manager_orders(message: Message, state: FSMContext):
    if not await is_manager(message.from_user.id):
        await message.answer("❌ У вас нет доступа к функциям менеджера")
        return
    
    async with get_session() as session:
        orders = await session.execute(
            "SELECT * FROM orders WHERE manager_id = :manager_id ORDER BY created_at DESC LIMIT 10",
            {"manager_id": message.from_user.id}
        )
        orders = orders.fetchall()
        
        if not orders:
            await message.answer("📋 У вас пока нет заказов")
            return
        
        message_text = "📋 **Ваши заказы**\n\n"
        
        for order in orders:
            status_emoji = {
                OrderStatus.NEW: "🆕",
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
                f"📅 {order.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
            )
        
        await message.answer(message_text, reply_markup=get_manager_menu())

async def cmd_manager_stats(message: Message, state: FSMContext):
    if not await is_manager(message.from_user.id):
        await message.answer("❌ У вас нет доступа к функциям менеджера")
        return
    
    stats_manager = StatisticsManager()
    stats = await stats_manager.get_manager_stats(manager_id=message.from_user.id)
    
    if not stats:
        await message.answer("📊 У вас пока нет статистики")
        return
    
    manager_stat = stats[0]
    
    await message.answer(
        f"📊 **Ваша статистика**\n\n"
        f"📋 Всего заказов: {manager_stat['total_orders']}\n"
        f"✅ Выполнено: {manager_stat['completed_orders']}\n"
        f"📈 Процент выполнения: {manager_stat['completion_rate']:.1f}%\n"
        f"💰 Общая выручка: {manager_stat['total_revenue']:.2f} руб.\n"
        f"💳 Средний чек: {manager_stat['total_revenue'] / manager_stat['completed_orders']:.2f} руб." if manager_stat['completed_orders'] > 0 else ""
    )

async def cmd_manager_invoice(message: Message, state: FSMContext):
    if not await is_manager(message.from_user.id):
        await message.answer("❌ У вас нет доступа к функциям менеджера")
        return
    
    async with get_session() as session:
        orders = await session.execute(
            "SELECT id, client_name, price FROM orders WHERE manager_id = :manager_id AND status != 'cancelled' ORDER BY created_at DESC",
            {"manager_id": message.from_user.id}
        )
        orders = orders.fetchall()
        
        if not orders:
            await message.answer("📋 Нет доступных заказов для выставления счета")
            return
        
        keyboard = []
        for order_id, client_name, price in orders:
            keyboard.append([
                InlineKeyboardButton(
                    text=f"📄 Заказ #{order_id} - {client_name} ({price} руб.)",
                    callback_data=f"invoice_{order_id}"
                )
            ])
        
        await message.answer(
            "💰 **Выберите заказ для выставления счета**\n\n",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )

async def callback_invoice_order(callback: CallbackQuery, state: FSMContext):
    if not await is_manager(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен")
        return
    
    order_id = int(callback.data.split("_")[1])
    
    async with get_session() as session:
        order = await session.get(Order, order_id)
        
        if not order or order.manager_id != callback.from_user.id:
            await callback.message.answer("❌ Заказ не найден или у вас нет к нему доступа")
            await callback.answer()
            return
        
        # Generate PDF invoice
        order_data = {
            'id': order.id,
            'client_name': order.client_name,
            'client_phone': order.client_phone,
            'address': order.address,
            'cleaning_type': order.cleaning_type,
            'date_time': order.date_time,
            'duration_hours': float(order.duration_hours),
            'price': float(order.price),
            'equipment_available': order.equipment_available,
            'chemicals_available': order.chemicals_available,
            'notes': order.notes or ""
        }
        
        try:
            pdf_path = generate_invoice_pdf(order_data)
            qr_path = generate_payment_qr(
                float(order.price),
                order.client_name,
                order.id
            )
            
            # Send PDF and QR code
            await callback.message.answer_document(
                FSInputFile(pdf_path),
                caption=f"📄 **Счет для заказа #{order.id}**\n\n"
                       f"👤 Клиент: {order.client_name}\n"
                       f"💰 Сумма: {order.price} руб.\n\n"
                       f"Отправьте этот счет клиенту для оплаты."
            )
            
            await callback.message.answer_photo(
                FSInputFile(qr_path),
                caption="📱 **QR-код для оплаты**\n\n"
                       "Клиент может отсканировать этот код для быстрой оплаты"
            )
            
        except Exception as e:
            await callback.message.answer(f"❌ Ошибка при создании счета: {str(e)}")
    
    await callback.answer()

async def cmd_manager_payment(message: Message, state: FSMContext):
    if not await is_manager(message.from_user.id):
        await message.answer("❌ У вас нет доступа к функциям менеджера")
        return
    
    async with get_session() as session:
        orders = await session.execute(
            """SELECT o.id, o.client_name, u.full_name as cleaner_name, o.price 
               FROM orders o 
               JOIN users u ON o.cleaner_id = u.id 
               WHERE o.manager_id = :manager_id 
               AND o.status = 'completed'
               AND o.id NOT IN (
                   SELECT order_id FROM payments WHERE payment_type = 'cleaner_payment' AND status = 'paid'
               )
               ORDER BY o.updated_at DESC""",
            {"manager_id": message.from_user.id}
        )
        orders = orders.fetchall()
        
        if not orders:
            await message.answer("💳 Нет заказов для оплаты клинеров")
            return
        
        keyboard = []
        for order_id, client_name, cleaner_name, price in orders:
            keyboard.append([
                InlineKeyboardButton(
                    text=f"💳 Заказ #{order_id} - {cleaner_name} ({price} руб.)",
                    callback_data=f"pay_cleaner_{order_id}"
                )
            ])
        
        await message.answer(
            "💳 **Выберите заказ для оплаты клинера**\n\n",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )

async def callback_pay_cleaner(callback: CallbackQuery, state: FSMContext):
    if not await is_manager(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен")
        return
    
    order_id = int(callback.data.split("_")[2])
    
    async with get_session() as session:
        order = await session.get(Order, order_id)
        
        if not order or order.manager_id != callback.from_user.id:
            await callback.message.answer("❌ Заказ не найден или у вас нет к нему доступа")
            await callback.answer()
            return
        
        if order.status != OrderStatus.COMPLETED:
            await callback.message.answer("❌ Заказ еще не выполнен")
            await callback.answer()
            return
        
        # Check if already paid
        existing_payment = await session.execute(
            "SELECT id FROM payments WHERE order_id = :order_id AND payment_type = 'cleaner_payment' AND status = 'paid'",
            {"order_id": order_id}
        )
        existing_payment = existing_payment.fetchone()
        
        if existing_payment:
            await callback.message.answer("💳 Оплата за этот заказ уже произведена")
            await callback.answer()
            return
        
        # Create payment record
        payment = Payment(
            order_id=order_id,
            user_id=order.cleaner_id,
            amount=order.price * 0.7,  # 70% to cleaner
            payment_type="cleaner_payment",
            status=PaymentStatus.PENDING
        )
        
        session.add(payment)
        await session.commit()
        
        # Get cleaner details
        cleaner = await session.get(User, order.cleaner_id)
        
        await callback.message.answer(
            f"💳 **Оплата клинеру**\n\n"
            f"📋 Заказ #{order_id}\n"
            f"👤 Клинер: {cleaner.full_name}\n"
            f"💰 Сумма к оплате: {payment.amount:.2f} руб.\n\n"
            f"💳 Реквизиты клинера:\n"
            f"📞 Телефон: {cleaner.phone or 'Не указан'}\n"
            f"🏦 Банковские данные: {cleaner.bank_details or 'Не указаны'}\n\n"
            f"После оплаты подтвердите платеж командой /confirm_payment {payment.id}"
        )
    
    await callback.answer()

async def cmd_manager_requisites(message: Message, state: FSMContext):
    if not await is_manager(message.from_user.id):
        await message.answer("❌ У вас нет доступа к функциям менеджера")
        return
    
    await message.answer(
        "📄 **Реквизиты компании**\n\n"
        "🏢 Название: [Название вашей компании]\n"
        "📝 ИНН: [Ваш ИНН]\n"
        "🏦 Банк: [Название банка]\n"
        "📱 Расчетный счет: [Номер счета]\n"
        "📧 Email: [Email для связи]\n"
        "📞 Телефон: [Телефон для связи]\n\n"
        "Используйте эти реквизиты для выставления счетов клиентам."
    )

async def cmd_manager_help(message: Message, state: FSMContext):
    if not await is_manager(message.from_user.id):
        await message.answer("❌ У вас нет доступа к функциям менеджера")
        return
    
    help_text = """
    📖 **Помощь для менеджера**
    
    📝 **Создание заказа:**
    - Нажмите "📝 Создать заказ"
    - Следуйте инструкциям бота
    - Заполните все поля заказа
    
    💰 **Выставление счета:**
    - Нажмите "💰 Выставить счет"
    - Выберите заказ из списка
    - Отправьте PDF счет клиенту
    
    💳 **Оплата клинеру:**
    - Нажмите "💳 Оплатить клинеру"
    - Выберите выполненный заказ
    - Оплатите по реквизитам клинера
    
    📊 **Статистика:**
    - Нажмите "📊 Статистика"
    - Просмотрите свои показатели
    
    ❓ **Если у вас возникли вопросы:**
    - Свяжитесь с администратором
    - Используйте команду /help
    """
    
    await message.answer(help_text, reply_markup=get_manager_menu())
