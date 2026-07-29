import asyncio
import logging
import random
import re
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# ==================== КОНФИГУРАЦИЯ ====================
BOT_TOKEN = "8669209199:AAFnRG3FG4q0KpR7T-bk_THhpAhEltz_H7U"

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Инициализация бота
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# ==================== ХРАНИЛИЩЕ СДЕЛОК ====================
exchanges = {}

# ==================== ФУНКЦИИ ====================
def generate_code():
    """Генерирует 4-значный код с ведущими нулями"""
    return f"{random.randint(0, 9999):04d}"

# ==================== КНОПКИ ====================
def get_main_keyboard():
    """Главная клавиатура с кнопками"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔄 Создать сделку")],
            [KeyboardButton(text="📝 Подключиться к сделке")],
            [KeyboardButton(text="❌ Отмена")]
        ],
        resize_keyboard=True
    )
    return keyboard

# ==================== СОСТОЯНИЯ ====================
class TradeStates(StatesGroup):
    waiting_for_exchange = State()
    waiting_for_password = State()
    waiting_for_gift_link = State()
    waiting_for_price = State()
    waiting_for_confirmation = State()
    waiting_for_create_link = State()
    waiting_for_create_price = State()

# ==================== КОМАНДЫ ====================
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    """Обработчик команды /start"""
    await state.clear()
    await message.answer(
        "🤖 *Добро пожаловать в Trade Bot!*\n"
        "Используйте кнопки для навигации:\n\n"
        "🔄 *Создать сделку* - создать новый обмен\n"
        "📝 *Подключиться к сделке* - войти в существующую\n\n"
        "🤖 *Welcome to Trade Bot!*\n"
        "Use the buttons to navigate:",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )

@dp.message(Command("cancel"))
async def cmd_cancel(message: types.Message, state: FSMContext):
    """Обработчик команды /cancel"""
    current_state = await state.get_state()
    if current_state is None:
        await message.answer(
            "❌ Нет активных операций для отмены.\n"
            "❌ No active operations to cancel.",
            reply_markup=get_main_keyboard()
        )
        return
    
    await state.clear()
    await message.answer(
        "❌ Операция отменена.\n"
        "❌ Operation cancelled.",
        reply_markup=get_main_keyboard()
    )

# ==================== КНОПКА СОЗДАТЬ СДЕЛКУ ====================
@dp.message(lambda message: message.text == "🔄 Создать сделку")
async def button_create_exchange(message: types.Message, state: FSMContext):
    """Создание новой сделки"""
    exchange_id = generate_code()
    while exchange_id in exchanges:
        exchange_id = generate_code()
    
    password = generate_code()
    
    exchanges[exchange_id] = {
        "password": password,
        "creator": message.from_user.id,
        "gift_link": None,
        "price": None,
        "buyer": None,
        "status": "waiting_for_link"
    }
    
    await state.update_data(exchange_id=exchange_id)
    await state.set_state(TradeStates.waiting_for_create_link)
    
    await message.answer(
        f"✅ *Сделка успешно создана!*\n\n"
        f"📋 *Номер сделки:* `{exchange_id}`\n"
        f"🔑 *Пароль:* `{password}`\n\n"
        f"🔗 Отправьте *ссылку на подарок*:\n\n"
        f"✅ *Exchange created successfully!*\n\n"
        f"📋 *Exchange ID:* `{exchange_id}`\n"
        f"🔑 *Password:* `{password}`\n\n"
        f"🔗 Send the *gift link*:",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )

@dp.message(TradeStates.waiting_for_create_link)
async def process_create_link(message: types.Message, state: FSMContext):
    """Обработка ссылки на подарок при создании"""
    gift_link = message.text.strip()
    
    if not re.match(r'^https?://', gift_link):
        await message.answer(
            "❌ Пожалуйста, отправьте *ссылку* (начинается с http:// или https://):\n"
            "❌ Please send a *link* (starts with http:// or https://):",
            parse_mode="Markdown"
        )
        return
    
    data = await state.get_data()
    exchange_id = data.get('exchange_id')
    
    if exchange_id in exchanges:
        exchanges[exchange_id]["gift_link"] = gift_link
        exchanges[exchange_id]["status"] = "waiting_for_price"
    
    await state.update_data(gift_link=gift_link)
    await state.set_state(TradeStates.waiting_for_create_price)
    
    await message.answer(
        f"✅ *Ссылка сохранена!*\n\n"
        f"💰 Теперь укажите сумму за подарок (в долларах):\n\n"
        f"✅ *Link saved!*\n\n"
        f"💰 Now set the price for the gift (in dollars):",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )

@dp.message(TradeStates.waiting_for_create_price)
async def process_create_price(message: types.Message, state: FSMContext):
    """Установка цены при создании сделки"""
    try:
        price = float(message.text.replace(',', '.'))
        if price <= 0:
            await message.answer(
                "❌ Сумма должна быть *больше 0*:\n"
                "❌ Amount must be *greater than 0*:",
                parse_mode="Markdown"
            )
            return
    except ValueError:
        await message.answer(
            "❌ Пожалуйста, введите *число* (например: 100 или 150.50):\n"
            "❌ Please enter a *number* (e.g., 100 or 150.50):",
            parse_mode="Markdown"
        )
        return
    
    data = await state.get_data()
    exchange_id = data.get('exchange_id')
    gift_link = data.get('gift_link')
    
    if exchange_id in exchanges:
        exchanges[exchange_id]["price"] = price
        exchanges[exchange_id]["status"] = "waiting_for_buyer"
    
    if price.is_integer():
        price_str = f"${int(price)}"
    else:
        price_str = f"${price:.2f}"
    
    await message.answer(
        f"✅ *Сделка создана!*\n\n"
        f"📋 *Номер сделки:* `{exchange_id}`\n"
        f"🔗 *Ссылка:* {gift_link}\n"
        f"💰 *Сумма:* {price_str}\n"
        f"🔑 *Пароль:* `{exchanges[exchange_id]['password']}`\n\n"
        f"⏳ Ожидайте подключения покупателя...\n\n"
        f"✅ *Exchange created!*\n\n"
        f"📋 *Exchange ID:* `{exchange_id}`\n"
        f"🔗 *Link:* {gift_link}\n"
        f"💰 *Amount:* {price_str}\n"
        f"🔑 *Password:* `{exchanges[exchange_id]['password']}`\n\n"
        f"⏳ Waiting for buyer to connect...",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )
    
    await state.clear()

# ==================== КНОПКА ПОДКЛЮЧИТЬСЯ К СДЕЛКЕ ====================
@dp.message(lambda message: message.text == "📝 Подключиться к сделке")
async def button_connect_exchange(message: types.Message, state: FSMContext):
    """Подключение к существующей сделке"""
    await state.set_state(TradeStates.waiting_for_exchange)
    await message.answer(
        "📝 Введите *номер сделки*:\n\n"
        "📝 Enter the *exchange ID*:",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )

@dp.message(TradeStates.waiting_for_exchange)
async def process_exchange_number(message: types.Message, state: FSMContext):
    """Обработка номера сделки"""
    exchange_id = message.text.strip()
    
    if exchange_id not in exchanges:
        await message.answer(
            f"❌ *Сделка #{exchange_id} не найдена!*\n"
            f"Пожалуйста, проверьте номер и попробуйте снова.\n\n"
            f"❌ *Exchange #{exchange_id} not found!*\n"
            f"Please check the number and try again.",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
        return
    
    if exchanges[exchange_id]["status"] == "completed":
        await message.answer(
            f"❌ *Сделка #{exchange_id} уже завершена!*\n\n"
            f"❌ *Exchange #{exchange_id} is already completed!*",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
        return
    
    await state.update_data(exchange_id=exchange_id)
    await state.set_state(TradeStates.waiting_for_password)
    
    await message.answer(
        f"🔑 Введите *пароль* для сделки #{exchange_id}:\n\n"
        f"🔑 Enter the *password* for exchange #{exchange_id}:",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )

@dp.message(TradeStates.waiting_for_password)
async def process_password(message: types.Message, state: FSMContext):
    """Обработка пароля"""
    password = message.text.strip()
    data = await state.get_data()
    exchange_id = data.get('exchange_id')
    
    print(f"🔍 Проверка пароля: ID={exchange_id}, Введен={password}")  # Отладка
    
    if exchange_id not in exchanges:
        await message.answer(
            "❌ Сделка не найдена. Начните заново.",
            reply_markup=get_main_keyboard()
        )
        await state.clear()
        return
    
    correct_password = exchanges[exchange_id]["password"]
    print(f"🔍 Правильный пароль: {correct_password}")  # Отладка
    
    if correct_password != password:
        await message.answer(
            f"❌ *Неверный пароль!*\n"
            f"Вы ввели: `{password}`\n"
            f"Пожалуйста, попробуйте снова.\n\n"
            f"❌ *Wrong password!*\n"
            f"You entered: `{password}`\n"
            f"Please try again.",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
        return
    
    # ✅ ПАРОЛЬ ВЕРНЫЙ
    print(f"✅ Пароль верный для сделки {exchange_id}")
    
    exchanges[exchange_id]["buyer"] = message.from_user.id
    exchanges[exchange_id]["status"] = "active"
    
    price = exchanges[exchange_id]["price"]
    gift_link = exchanges[exchange_id]["gift_link"]
    
    if price.is_integer():
        price_str = f"${int(price)}"
    else:
        price_str = f"${price:.2f}"
    
    # ✅ ОТВЕЧАЕМ ПОКУПАТЕЛЮ СРАЗУ
    await message.answer(
        f"✅ *Пароль верный!*\n"
        f"✅ *Вы успешно подключились к сделке #{exchange_id}!*\n\n"
        f"🔗 *Ссылка на подарок:* {gift_link}\n"
        f"💰 *Сумма:* {price_str}\n\n"
        f"⏳ Ожидайте 1 минуту для подтверждения...\n\n"
        f"✅ *Password correct!*\n"
        f"✅ *You successfully connected to exchange #{exchange_id}!*\n\n"
        f"🔗 *Gift link:* {gift_link}\n"
        f"💰 *Amount:* {price_str}\n\n"
        f"⏳ Please wait 1 minute for confirmation...",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )
    
    # Уведомляем создателя
    creator_id = exchanges[exchange_id]["creator"]
    try:
        await bot.send_message(
            creator_id,
            f"✅ *Кто-то подключился к вашей сделке #{exchange_id}!*\n"
            f"🔗 *Ссылка:* {gift_link}\n"
            f"💰 *Сумма:* {price_str}\n\n"
            f"⏳ Ожидайте 1 минуту...\n"
            f"Покупатель подтвердит покупку через минуту.\n\n"
            f"✅ *Someone connected to your exchange #{exchange_id}!*\n"
            f"🔗 *Link:* {gift_link}\n"
            f"💰 *Amount:* {price_str}\n\n"
            f"⏳ Please wait 1 minute...",
            parse_mode="Markdown"
        )
    except Exception as e:
        print(f"❌ Ошибка уведомления создателя: {e}")
    
    # Очищаем состояние
    await state.clear()
    
    # ⏳ ЗАДЕРЖКА 60 СЕКУНД
    await asyncio.sleep(60)
    
    # Проверяем, активна ли сделка
    if exchange_id not in exchanges or exchanges[exchange_id]["status"] != "active":
        print(f"⚠️ Сделка {exchange_id} уже не активна")
        return
    
    # Завершаем сделку
    exchanges[exchange_id]["status"] = "completed"
    
    # Финальное сообщение для покупателя
    try:
        await message.answer(
            f"✅ *Покупатель подтвердил покупку!*\n"
            f"📦 Отправьте подарок продавцу: @ValletTrade\n\n"
            f"📋 *Детали сделки:*\n"
            f"└ Номер: #{exchange_id}\n"
            f"└ Ссылка: {gift_link}\n"
            f"└ Сумма: {price_str}\n\n"
            f"✅ *Buyer confirmed the purchase!*\n"
            f"📦 Send the gift to the seller: @ValletTrade\n\n"
            f"📋 *Exchange details:*\n"
            f"└ ID: #{exchange_id}\n"
            f"└ Link: {gift_link}\n"
            f"└ Amount: {price_str}",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
    except Exception as e:
        print(f"❌ Ошибка финального сообщения покупателю: {e}")
    
    # Уведомляем создателя
    try:
        await bot.send_message(
            creator_id,
            f"✅ *Покупатель подтвердил покупку!*\n"
            f"📦 Отправьте подарок: @ValletTrade\n\n"
            f"📋 *Детали сделки:*\n"
            f"└ Номер: #{exchange_id}\n"
            f"└ Ссылка: {gift_link}\n"
            f"└ Сумма: {price_str}\n\n"
            f"✅ *Buyer confirmed the purchase!*\n"
            f"📦 Send the gift: @ValletTrade\n\n"
            f"📋 *Exchange details:*\n"
            f"└ ID: #{exchange_id}\n"
            f"└ Link: {gift_link}\n"
            f"└ Amount: {price_str}",
            parse_mode="Markdown"
        )
    except Exception as e:
        print(f"❌ Ошибка уведомления создателя: {e}")

# ==================== КНОПКА ОТМЕНА ====================
@dp.message(lambda message: message.text == "❌ Отмена")
async def button_cancel(message: types.Message, state: FSMContext):
    """Кнопка Отмена"""
    current_state = await state.get_state()
    if current_state is None:
        await message.answer(
            "❌ Нет активных операций для отмены.",
            reply_markup=get_main_keyboard()
        )
        return
    
    await state.clear()
    await message.answer(
        "❌ Операция отменена.\n"
        "❌ Operation cancelled.",
        reply_markup=get_main_keyboard()
    )

# ==================== ОБРАБОТКА ЛЮБЫХ СООБЩЕНИЙ ====================
@dp.message()
async def handle_all_messages(message: types.Message, state: FSMContext):
    """Обработка любых сообщений, если нет активного состояния"""
    current_state = await state.get_state()
    
    if current_state is None:
        await message.answer(
            "❓ Я не понимаю эту команду.\n"
            "Используйте кнопки для навигации:\n\n"
            "❓ I don't understand this command.\n"
            "Use the buttons to navigate:",
            reply_markup=get_main_keyboard()
        )
        return
    
    await message.answer(
        "⏳ Пожалуйста, следуйте инструкциям бота.\n"
        "Используйте кнопки для ответа.\n\n"
        "⏳ Please follow the bot's instructions.\n"
        "Use the buttons to reply.",
        reply_markup=get_main_keyboard()
    )

# ==================== ЗАПУСК БОТА ====================
async def main():
    """Главная функция запуска бота"""
    print("=" * 50)
    print("🤖 TRADE BOT ЗАПУЩЕН!")
    print("📋 Номер сделки: 4 цифры")
    print("🔑 Пароль: 4 цифры")
    print("🔗 Запрос ссылки на подарок")
    print("⏳ Задержка перед подтверждением: 60 секунд")
    print("=" * 50)
    
    try:
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        print("\n🛑 Бот остановлен пользователем")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
