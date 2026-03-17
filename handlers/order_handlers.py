from aiogram import types, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext

from database.database import get_session
from database.models import User, UserRole, Order, OrderStatus, City, Payment, PaymentStatus
from utils.keyboards import get_order_actions
from datetime import datetime

async def callback_take_order(callback: CallbackQuery, state: FSMContext):
    order_id = int(callback.data.split("_")[2])
    
    async with get_session() as session:
        order = await session.get(Order, order_id)
        cleaner = await session.get(User, callback.from_user.id)
        
        if not order or order.status != OrderStatus.NEW:
            await callback.message.answer("❌ Заказ уже взят или недоступен")
            await callback.answer()
            return
        
        if not cleaner or cleaner.role != UserRole.CLEANER:
            await callback.message.answer("❌ Только клинеры могут брать заказы")
            await callback.answer()
            return
        
        # Assign order to cleaner
        order.cleaner_id = callback.from_user.id
        order.status = OrderStatus.ASSIGNED
        await session.commit()
        
        # Get manager info
        manager = await session.get(User, order.manager_id)
        
        await callback.message.answer(
            f"✅ Вы взяли заказ #{order_id}!\n\n"
            f"📋 Детали заказа:\n"
            f"👤 Клиент: {order.client_name}\n"
            f"📞 Телефон: {order.client_phone}\n"
            f"📍 Адрес: {order.address}\n"
            f"🧹 Тип: {order.cleaning_type}\n"
            f"🕐 Время: {order.date_time.strftime('%d.%m.%Y %H:%M')}\n"
            f"💰 Цена: {order.price} руб.\n\n"
            f"📞 Свяжитесь с менеджером: @{manager.username if manager.username else manager.full_name}"
        )
        
        # Notify manager
        try:
            await callback.bot.send_message(
                order.manager_id,
                f"👤 Клинер взял заказ #{order_id}\n\n"
                f"🧹 Исполнитель: {cleaner.full_name}\n"
                f"📞 Телефон: {cleaner.phone or 'Не указан'}\n\n"
                f"Заказ теперь в работе."
            )
        except:
            pass  # Manager might have blocked the bot
    
    await callback.answer()

async def callback_reject_order(callback: CallbackQuery, state: FSMContext):
    order_id = int(callback.data.split("_")[2])
    
    async with get_session() as session:
        order = await session.get(Order, order_id)
        cleaner = await session.get(User, callback.from_user.id)
        
        if not order or order.cleaner_id != callback.from_user.id:
            await callback.message.answer("❌ Заказ не найден или у вас нет к нему доступа")
            await callback.answer()
            return
        
        if order.status != OrderStatus.ASSIGNED:
            await callback.message.answer("❌ Заказ нельзя отклонить на этом этапе")
            await callback.answer()
            return
        
        # Reset order to new status
        order.cleaner_id = None
        order.status = OrderStatus.NEW
        await session.commit()
        
        await callback.message.answer(
            f"❌ Вы отклонили заказ #{order_id}\n\n"
            f"Заказ снова доступен для других клинеров."
        )
        
        # Notify manager
        try:
            await callback.bot.send_message(
                order.manager_id,
                f"❌ Клинер отклонил заказ #{order_id}\n\n"
                f"🧹 Исполнитель: {cleaner.full_name}\n\n"
                f"Заказ снова доступен для назначения."
            )
        except:
            pass
    
    await callback.answer()

async def callback_contact_manager(callback: CallbackQuery, state: FSMContext):
    order_id = int(callback.data.split("_")[2])
    
    async with get_session() as session:
        order = await session.get(Order, order_id)
        cleaner = await session.get(User, callback.from_user.id)
        
        if not order or order.cleaner_id != callback.from_user.id:
            await callback.message.answer("❌ Заказ не найден или у вас нет к нему доступа")
            await callback.answer()
            return
        
        manager = await session.get(User, order.manager_id)
        
        if not manager:
            await callback.message.answer("❌ Менеджер не найден")
            await callback.answer()
            return
        
        contact_info = f"@{manager.username}" if manager.username else manager.full_name
        
        await callback.message.answer(
            f"📞 **Контактная информация менеджера**\n\n"
            f"👤 Имя: {manager.full_name}\n"
            f"🆔 Telegram: {contact_info}\n"
            f"📞 Телефон: {manager.phone or 'Не указан'}\n\n"
            f"Свяжитесь с менеджером для уточнения деталей заказа #{order_id}"
        )
    
    await callback.answer()

async def callback_edit_order(callback: CallbackQuery, state: FSMContext):
    order_id = int(callback.data.split("_")[2])
    
    async with get_session() as session:
        order = await session.get(Order, order_id)
        user = await session.get(User, callback.from_user.id)
        
        if not order:
            await callback.message.answer("❌ Заказ не найден")
            await callback.answer()
            return
        
        # Check permissions
        can_edit = (
            (user.role == UserRole.ADMIN) or
            (user.role == UserRole.MANAGER and order.manager_id == callback.from_user.id)
        )
        
        if not can_edit:
            await callback.message.answer("❌ У вас нет прав для редактирования этого заказа")
            await callback.answer()
            return
        
        await callback.message.answer(
            f"✏️ **Редактирование заказа #{order_id}**\n\n"
            f"Функция редактирования в разработке...\n"
            f"Для срочных изменений свяжитесь с администратором."
        )
    
    await callback.answer()

async def callback_cancel_order(callback: CallbackQuery, state: FSMContext):
    order_id = int(callback.data.split("_")[2])
    
    async with get_session() as session:
        order = await session.get(Order, order_id)
        user = await session.get(User, callback.from_user.id)
        
        if not order:
            await callback.message.answer("❌ Заказ не найден")
            await callback.answer()
            return
        
        # Check permissions
        can_cancel = (
            (user.role == UserRole.ADMIN) or
            (user.role == UserRole.MANAGER and order.manager_id == callback.from_user.id)
        )
        
        if not can_cancel:
            await callback.message.answer("❌ У вас нет прав для отмены этого заказа")
            await callback.answer()
            return
        
        # Cancel order
        order.status = OrderStatus.CANCELLED
        await session.commit()
        
        await callback.message.answer(
            f"❌ Заказ #{order_id} отменен\n\n"
            f"Клиент: {order.client_name}\n"
            f"Адрес: {order.address}\n\n"
            f"Заказ перемещен в архив."
        )
        
        # Notify cleaner if assigned
        if order.cleaner_id:
            try:
                await callback.bot.send_message(
                    order.cleaner_id,
                    f"❌ Заказ #{order_id} был отменен менеджером\n\n"
                    f"Пожалуйста, проверьте список доступных заказов."
                )
            except:
                pass
    
    await callback.answer()

async def callback_order_details(callback: CallbackQuery, state: FSMContext):
    order_id = int(callback.data.split("_")[2])
    
    async with get_session() as session:
        order = await session.get(Order, order_id)
        user = await session.get(User, callback.from_user.id)
        
        if not order:
            await callback.message.answer("❌ Заказ не найден")
            await callback.answer()
            return
        
        # Check permissions
        can_view = (
            (user.role == UserRole.ADMIN) or
            (user.role == UserRole.MANAGER and order.manager_id == callback.from_user.id) or
            (user.role == UserRole.CLEANER and order.cleaner_id == callback.from_user.id)
        )
        
        if not can_view:
            await callback.message.answer("❌ У вас нет прав для просмотра этого заказа")
            await callback.answer()
            return
        
        # Get additional info
        city = await session.get(City, order.city_id)
        manager = await session.get(User, order.manager_id)
        cleaner = await session.get(User, order.cleaner_id) if order.cleaner_id else None
        
        details_text = f"📋 **Детали заказа #{order_id}**\n\n"
        details_text += f"👤 Клиент: {order.client_name}\n"
        details_text += f"📞 Телефон: {order.client_phone}\n"
        details_text += f"📍 Адрес: {order.address}\n"
        details_text += f"🏙️ Город: {city.name if city else 'Не указан'}\n"
        details_text += f"🧹 Тип уборки: {order.cleaning_type}\n"
        details_text += f"🕐 Дата/время: {order.date_time.strftime('%d.%m.%Y %H:%M')}\n"
        details_text += f"⏱ Длительность: {order.duration_hours} ч.\n"
        details_text += f"💰 Цена: {order.price} руб.\n"
        details_text += f"🔧 Оборудование: {'Есть' if order.equipment_available else 'Нет'}\n"
        details_text += f"🧴 Средства: {'Есть' if order.chemicals_available else 'Нет'}\n"
        
        if order.notes:
            details_text += f"📝 Примечания: {order.notes}\n"
        
        details_text += f"\n👤 Менеджер: {manager.full_name}\n"
        
        if cleaner:
            details_text += f"🧹 Клинер: {cleaner.full_name}\n"
        
        details_text += f"📊 Статус: {order.status.value}\n"
        details_text += f"📅 Создан: {order.created_at.strftime('%d.%m.%Y %H:%M')}\n"
        
        await callback.message.answer(details_text)
    
    await callback.answer()

async def callback_refresh_orders(callback: CallbackQuery, state: FSMContext):
    # This would refresh the available orders list
    await callback.message.answer("🔄 Обновление списка заказов...")
    
    # Re-run the available orders command
    from handlers.cleaner_handlers import cmd_cleaner_available_orders
    await cmd_cleaner_available_orders(callback.message, state)
    
    await callback.answer()
