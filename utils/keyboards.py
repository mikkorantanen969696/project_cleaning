from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

def get_main_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📋 Мои заказы")],
            [KeyboardButton(text="📊 Статистика")],
            [KeyboardButton(text="⚙️ Настройки")],
            [KeyboardButton(text="❓ Помощь")]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_admin_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📋 Все заказы")],
            [KeyboardButton(text="👥 Управление пользователями")],
            [KeyboardButton(text="📊 Статистика")],
            [KeyboardButton(text="🏙️ Управление городами")],
            [KeyboardButton(text="💳 Финансы")],
            [KeyboardButton(text="⚙️ Настройки")],
            [KeyboardButton(text="❓ Помощь")]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_manager_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📝 Создать заказ")],
            [KeyboardButton(text="📋 Мои заказы")],
            [KeyboardButton(text="📊 Статистика")],
            [KeyboardButton(text="💰 Выставить счет")],
            [KeyboardButton(text="💳 Оплатить клинеру")],
            [KeyboardButton(text="📄 Реквизиты")],
            [KeyboardButton(text="❓ Помощь")]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_cleaner_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📋 Доступные заказы")],
            [KeyboardButton(text="🏠 Мои заказы")],
            [KeyboardButton(text="📸 Загрузить фото")],
            [KeyboardButton(text="💳 Мои реквизиты")],
            [KeyboardButton(text="💰 Получить оплату")],
            [KeyboardButton(text="❓ Помощь")]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_admin_actions():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="➕ Добавить менеджера", callback_data="admin_add_manager"),
                InlineKeyboardButton(text="➖ Удалить менеджера", callback_data="admin_remove_manager")
            ],
            [
                InlineKeyboardButton(text="👥 Все пользователи", callback_data="admin_users"),
                InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")
            ],
            [
                InlineKeyboardButton(text="🏙️ Управление городами", callback_data="admin_cities"),
                InlineKeyboardButton(text="💳 Финансы", callback_data="admin_finance")
            ],
            [
                InlineKeyboardButton(text="📋 Экспорт данных", callback_data="admin_export")
            ],
            [
                InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")
            ]
        ]
    )
    return keyboard

def get_order_actions(order_id: int, role: str):
    if role == "cleaner":
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Взять заказ", callback_data=f"order_take_{order_id}"),
                    InlineKeyboardButton(text="❌ Отклонить", callback_data=f"order_reject_{order_id}")
                ],
                [
                    InlineKeyboardButton(text="📞 Связаться с менеджером", callback_data=f"order_contact_{order_id}")
                ]
            ]
        )
    elif role == "manager":
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"order_edit_{order_id}"),
                    InlineKeyboardButton(text="❌ Отменить", callback_data=f"order_cancel_{order_id}")
                ],
                [
                    InlineKeyboardButton(text="💰 Выставить счет", callback_data=f"order_invoice_{order_id}"),
                    InlineKeyboardButton(text="📊 Статистика по заказу", callback_data=f"order_stats_{order_id}")
                ]
            ]
        )
    else:  # admin
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="👤 Детали заказа", callback_data=f"order_details_{order_id}"),
                    InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"order_edit_{order_id}")
                ],
                [
                    InlineKeyboardButton(text="❌ Отменить", callback_data=f"order_cancel_{order_id}"),
                    InlineKeyboardButton(text="📊 Статистика", callback_data=f"order_stats_{order_id}")
                ]
            ]
        )
    
    return keyboard

def get_statistics_options():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📊 Общая статистика", callback_data="stats_general"),
                InlineKeyboardButton(text="👥 По менеджерам", callback_data="stats_managers")
            ],
            [
                InlineKeyboardButton(text="🧹 По клинерам", callback_data="stats_cleaners"),
                InlineKeyboardButton(text="🏙️ По городам", callback_data="stats_cities")
            ],
            [
                InlineKeyboardButton(text="📅 За период", callback_data="stats_period"),
                InlineKeyboardButton(text="📈 Графики", callback_data="stats_charts")
            ],
            [
                InlineKeyboardButton(text="📄 Экспорт в Excel", callback_data="stats_export_excel"),
                InlineKeyboardButton(text="📄 Экспорт в PDF", callback_data="stats_export_pdf")
            ],
            [
                InlineKeyboardButton(text="🔙 Назад", callback_data="stats_back")
            ]
        ]
    )
    return keyboard

def get_city_selection():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="➕ Добавить город", callback_data="city_add"),
                InlineKeyboardButton(text="➖ Удалить город", callback_data="city_remove")
            ],
            [
                InlineKeyboardButton(text="✏️ Редактировать город", callback_data="city_edit"),
                InlineKeyboardButton(text="📋 Список городов", callback_data="city_list")
            ]
        ]
    )
    return keyboard
