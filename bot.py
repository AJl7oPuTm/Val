import asyncio
import logging
import random
import re
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton, 
    InlineKeyboardMarkup, InlineKeyboardButton,
    WebAppInfo
)

# ==================== КОНФИГУРАЦИЯ ====================
BOT_TOKEN = "8669209199:AAFnRG3FG4q0KpR7T-bk_THhpAhEltz_H7U"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# ==================== ХРАНИЛИЩЕ ====================
exchanges = {}
user_balances = {}
user_history = {}
user_lang = {}  # {user_id: "ru" | "en" | "uk" | "ar"}

# ==================== ПЕРЕВОДЫ ====================
LANG = {
    "ru": {
        "welcome": "✨ *Добро пожаловать в Trade Bot!* ✨\n\n🤝 Безопасный обмен подарками\n\n📌 Для начала работы используйте кнопки ниже.\n❓ Если не знаете что делать — нажмите «Инструкция».",
        "use_buttons": "💬 Используйте кнопки ниже для работы с ботом:",
        "instruction_title": "📖 *Инструкция по использованию Trade Bot*\n\nВыберите вашу роль:",
        "instruction_seller": "📤 *Инструкция для ПРОДАВЦА:*\n\n1️⃣ Нажмите кнопку «🆕 Создать сделку»\n2️⃣ Отправьте *ссылку на подарок*, который вы продаете\n3️⃣ Укажите *цену в долларах* 💰\n4️⃣ После создания вы получите *номер* и *пароль* от сделки\n5️⃣ Отправьте их покупателю\n\n6️⃣ После того как покупатель оплатит:\n   📦 *Перекиньте подарок на @ValletTrade*\n   ✅ После проверки вы получите деньги на баланс\n\n⚠️ *Важно:* Не отправляйте подарок напрямую покупателю!\nТолько через гаранта @ValletTrade",
        "instruction_buyer": "🛒 *Инструкция для ПОКУПАТЕЛЯ:*\n\n1️⃣ Нажмите кнопку «🔗 Подключиться»\n2️⃣ Введите *номер сделки* и *пароль* от неё\n3️⃣ Оплатите товар 💳\n   _(деньги НЕ идут напрямую продавцу)_\n\n4️⃣ После оплаты ожидайте:\n   • Продавец отправит подарок гаранту @ValletTrade\n   • Гарант проверит его\n   • После проверки вы получите подарок ✅\n\n🔒 *Безопасность:* Все сделки проходят через гаранта!\nВаши деньги в безопасности до получения товара.",
        "back_to_roles": "🔙 Назад к ролям",
        "close": "❌ Закрыть",
        "select_role": "Выберите вашу роль:",
        "create_exchange": "🆕 Создать сделку",
        "connect": "🔗 Подключиться",
        "balance": "💰 Баланс",
        "history": "📊 История",
        "instruction_btn": "❓ Инструкция",
        "cancel": "❌ Отмена",
        "no_active": "❌ Нет активных операций.",
        "cancelled": "✅ Операция отменена.",
        "exchange_created": "🎉 *Сделка создана!*",
        "exchange_number": "📌 *Номер:* `{}`",
        "exchange_password": "🔑 *Пароль:* `{}`",
        "send_gift_link": "📎 Отправьте *ссылку на подарок*:",
        "invalid_link": "❌ Отправьте ссылку (http:// или https://)",
        "enter_price": "💰 Укажите *сумму* (в долларах):",
        "price_invalid": "❌ Введите число",
        "price_zero": "❌ Сумма должна быть > 0",
        "exchange_created_success": "✅ *Сделка создана!* 🎉\n\n📋 Номер: `{}`\n🔑 Пароль: `{}`\n💰 Сумма: {}\n\n⏳ Ожидайте покупателя...\n📖 Не знаете что дальше? Нажмите «❓ Инструкция»",
        "enter_exchange_id": "🔍 Введите *номер сделки*:\n\n_(который вы получили от продавца)_",
        "exchange_not_found": "❌ *Сделка #{} не найдена!*\nПроверьте номер и попробуйте снова.",
        "exchange_completed": "❌ *Сделка #{} уже завершена!*",
        "exchange_active": "❌ *Сделка #{} уже активна!*",
        "enter_password": "🔑 Введите *пароль* для сделки #{}:",
        "wrong_password": "❌ *Неверный пароль!*\nПопробуйте снова.",
        "connect_success": "✅ *Подключение успешно!* 🔗\n\n📋 *Сделка #{}*\n🔗 *Ссылка:* {}\n💰 *Сумма:* {}\n\n⏳ *Ожидайте завершения сделки...*\n📖 Не знаете что дальше? Нажмите «❓ Инструкция»",
        "someone_connected": "🔔 *Кто-то подключился к сделке #{}!*\n\n💰 *Сумма:* {}\n📦 Подготовьте подарок!\n\n📖 Инструкция: нажмите «❓ Инструкция»",
        "deal_completed_buyer": "✅ *Сделка #{} завершена!* 🎉\n\n📦 *Отправьте подарок гаранту:* @ValletTrade\n🔗 Ссылка на подарок: {}\n💰 Сумма: {}\n\n⏳ После проверки гарантом, продавцу будет зачислена сумма.\n\n📖 Инструкция: нажмите «❓ Инструкция»",
        "deal_completed_seller": "✅ *Сделка #{} завершена!* 🎉\n\n💰 *Покупатель заплатил {}*\n📦 Отправьте подарок гаранту: @ValletTrade\n🔗 Ссылка на подарок: {}\n\n⏳ После проверки гарантом, вам зачислят на баланс.\n\n📖 Инструкция: нажмите «❓ Инструкция»",
        "balance_text": "💰 *Ваш баланс:* ${:.2f}\n\n📊 Всего транзакций: {}",
        "history_empty": "📭 История пуста.",
        "history_text": "📊 *История транзакций:*\n\n",
        "unknown": "❓ Используйте кнопки ниже 👇\nЕсли не знаете что делать — нажмите «❓ Инструкция»",
        "follow_instructions": "⏳ Следуйте инструкциям бота."
    },
    "en": {
        "welcome": "✨ *Welcome to Trade Bot!* ✨\n\n🤝 Secure gift exchange\n\n📌 Use the buttons below to get started.\n❓ If you're not sure what to do, press 'Instructions'.",
        "use_buttons": "💬 Use the buttons below to interact with the bot:",
        "instruction_title": "📖 *Trade Bot Instructions*\n\nSelect your role:",
        "instruction_seller": "📤 *Instructions for SELLER:*\n\n1️⃣ Press '🆕 Create deal'\n2️⃣ Send the *gift link* you are selling\n3️⃣ Set the *price in dollars* 💰\n4️⃣ After creation you will get the *ID* and *password* for the deal\n5️⃣ Send them to the buyer\n\n6️⃣ After the buyer pays:\n   📦 *Forward the gift to @ValletTrade*\n   ✅ After verification, you will receive the money to your balance\n\n⚠️ *Important:* Don't send the gift directly to the buyer!\nOnly through the guarantor @ValletTrade",
        "instruction_buyer": "🛒 *Instructions for BUYER:*\n\n1️⃣ Press '🔗 Connect'\n2️⃣ Enter the *deal ID* and *password*\n3️⃣ Pay for the item 💳\n   _(money does NOT go directly to the seller)_\n\n4️⃣ After payment, wait:\n   • Seller sends the gift to guarantor @ValletTrade\n   • Guarantor verifies it\n   • After verification, you receive the gift ✅\n\n🔒 *Security:* All deals go through a guarantor!\nYour money is safe until you receive the item.",
        "back_to_roles": "🔙 Back to roles",
        "close": "❌ Close",
        "select_role": "Select your role:",
        "create_exchange": "🆕 Create deal",
        "connect": "🔗 Connect",
        "balance": "💰 Balance",
        "history": "📊 History",
        "instruction_btn": "❓ Instructions",
        "cancel": "❌ Cancel",
        "no_active": "❌ No active operations.",
        "cancelled": "✅ Operation cancelled.",
        "exchange_created": "🎉 *Deal created!*",
        "exchange_number": "📌 *ID:* `{}`",
        "exchange_password": "🔑 *Password:* `{}`",
        "send_gift_link": "📎 Send the *gift link*:",
        "invalid_link": "❌ Send a link (http:// or https://)",
        "enter_price": "💰 Set the *price* (in dollars):",
        "price_invalid": "❌ Enter a number",
        "price_zero": "❌ Price must be > 0",
        "exchange_created_success": "✅ *Deal created!* 🎉\n\n📋 ID: `{}`\n🔑 Password: `{}`\n💰 Price: {}\n\n⏳ Waiting for buyer...\n📖 Not sure what to do? Press '❓ Instructions'",
        "enter_exchange_id": "🔍 Enter the *deal ID*:\n\n_(received from the seller)_",
        "exchange_not_found": "❌ *Deal #{} not found!*\nCheck the ID and try again.",
        "exchange_completed": "❌ *Deal #{} is already completed!*",
        "exchange_active": "❌ *Deal #{} is already active!*",
        "enter_password": "🔑 Enter the *password* for deal #{}:",
        "wrong_password": "❌ *Wrong password!*\nTry again.",
        "connect_success": "✅ *Connection successful!* 🔗\n\n📋 *Deal #{}*\n🔗 *Link:* {}\n💰 *Price:* {}\n\n⏳ *Waiting for deal completion...*\n📖 Not sure what to do? Press '❓ Instructions'",
        "someone_connected": "🔔 *Someone connected to deal #{}!*\n\n💰 *Price:* {}\n📦 Prepare the gift!\n\n📖 Instructions: press '❓ Instructions'",
        "deal_completed_buyer": "✅ *Deal #{} completed!* 🎉\n\n📦 *Send the gift to guarantor:* @ValletTrade\n🔗 Gift link: {}\n💰 Price: {}\n\n⏳ After verification by the guarantor, the seller will receive the money.\n\n📖 Instructions: press '❓ Instructions'",
        "deal_completed_seller": "✅ *Deal #{} completed!* 🎉\n\n💰 *Buyer paid {}*\n📦 Send the gift to guarantor: @ValletTrade\n🔗 Gift link: {}\n\n⏳ After verification by the guarantor, you will receive the money to your balance.\n\n📖 Instructions: press '❓ Instructions'",
        "balance_text": "💰 *Your balance:* ${:.2f}\n\n📊 Total transactions: {}",
        "history_empty": "📭 History is empty.",
        "history_text": "📊 *Transaction history:*\n\n",
        "unknown": "❓ Use the buttons below 👇\nIf you're not sure what to do, press '❓ Instructions'",
        "follow_instructions": "⏳ Follow the bot's instructions."
    },
    "uk": {
        "welcome": "✨ *Ласкаво просимо до Trade Bot!* ✨\n\n🤝 Безпечний обмін подарунками\n\n📌 Для початку роботи використовуйте кнопки нижче.\n❓ Якщо не знаєте що робити — натисніть «Інструкція».",
        "use_buttons": "💬 Використовуйте кнопки нижче для роботи з ботом:",
        "instruction_title": "📖 *Інструкція з використання Trade Bot*\n\nОберіть вашу роль:",
        "instruction_seller": "📤 *Інструкція для ПРОДАВЦЯ:*\n\n1️⃣ Натисніть кнопку «🆕 Створити угоду»\n2️⃣ Відправте *посилання на подарунок*, який ви продаєте\n3️⃣ Вкажіть *ціну в доларах* 💰\n4️⃣ Після створення ви отримаєте *номер* та *пароль* угоди\n5️⃣ Відправте їх покупцеві\n\n6️⃣ Після того як покупець оплатить:\n   📦 *Перекиньте подарунок на @ValletTrade*\n   ✅ Після перевірки ви отримаєте гроші на баланс\n\n⚠️ *Важливо:* Не відправляйте подарунок напряму покупцеві!\nТільки через гаранта @ValletTrade",
        "instruction_buyer": "🛒 *Інструкція для ПОКУПЦЯ:*\n\n1️⃣ Натисніть кнопку «🔗 Підключитися»\n2️⃣ Введіть *номер угоди* та *пароль* від неї\n3️⃣ Оплатіть товар 💳\n   _(гроші НЕ йдуть напряму продавцю)_\n\n4️⃣ Після оплати очікуйте:\n   • Продавець відправить подарунок гаранту @ValletTrade\n   • Гарант перевірить його\n   • Після перевірки ви отримаєте подарунок ✅\n\n🔒 *Безпека:* Всі угоди проходять через гаранта!\nВаші гроші в безпеці до отримання товару.",
        "back_to_roles": "🔙 Назад до ролей",
        "close": "❌ Закрити",
        "select_role": "Оберіть вашу роль:",
        "create_exchange": "🆕 Створити угоду",
        "connect": "🔗 Підключитися",
        "balance": "💰 Баланс",
        "history": "📊 Історія",
        "instruction_btn": "❓ Інструкція",
        "cancel": "❌ Відміна",
        "no_active": "❌ Немає активних операцій.",
        "cancelled": "✅ Операцію скасовано.",
        "exchange_created": "🎉 *Угоду створено!*",
        "exchange_number": "📌 *Номер:* `{}`",
        "exchange_password": "🔑 *Пароль:* `{}`",
        "send_gift_link": "📎 Відправте *посилання на подарунок*:",
        "invalid_link": "❌ Відправте посилання (http:// або https://)",
        "enter_price": "💰 Вкажіть *суму* (в доларах):",
        "price_invalid": "❌ Введіть число",
        "price_zero": "❌ Сума повинна бути > 0",
        "exchange_created_success": "✅ *Угоду створено!* 🎉\n\n📋 Номер: `{}`\n🔑 Пароль: `{}`\n💰 Сума: {}\n\n⏳ Очікуйте покупця...\n📖 Не знаєте що далі? Натисніть «❓ Інструкція»",
        "enter_exchange_id": "🔍 Введіть *номер угоди*:\n\n_(який ви отримали від продавця)_",
        "exchange_not_found": "❌ *Угоду #{} не знайдено!*\nПеревірте номер та спробуйте знову.",
        "exchange_completed": "❌ *Угода #{} вже завершена!*",
        "exchange_active": "❌ *Угода #{} вже активна!*",
        "enter_password": "🔑 Введіть *пароль* для угоди #{}:",
        "wrong_password": "❌ *Невірний пароль!*\nСпробуйте знову.",
        "connect_success": "✅ *Підключення успішне!* 🔗\n\n📋 *Угода #{}*\n🔗 *Посилання:* {}\n💰 *Сума:* {}\n\n⏳ *Очікуйте завершення угоди...*\n📖 Не знаєте що далі? Натисніть «❓ Інструкція»",
        "someone_connected": "🔔 *Хтось підключився до угоди #{}!*\n\n💰 *Сума:* {}\n📦 Підготуйте подарунок!\n\n📖 Інструкція: натисніть «❓ Інструкція»",
        "deal_completed_buyer": "✅ *Угода #{} завершена!* 🎉\n\n📦 *Відправте подарунок гаранту:* @ValletTrade\n🔗 Посилання на подарунок: {}\n💰 Сума: {}\n\n⏳ Після перевірки гарантом, продавцю буде зарахована сума.\n\n📖 Інструкція: натисніть «❓ Інструкція»",
        "deal_completed_seller": "✅ *Угода #{} завершена!* 🎉\n\n💰 *Покупець заплатив {}*\n📦 Відправте подарунок гаранту: @ValletTrade\n🔗 Посилання на подарунок: {}\n\n⏳ Після перевірки гарантом, вам зарахують на баланс.\n\n📖 Інструкція: натисніть «❓ Інструкція»",
        "balance_text": "💰 *Ваш баланс:* ${:.2f}\n\n📊 Всього транзакцій: {}",
        "history_empty": "📭 Історія порожня.",
        "history_text": "📊 *Історія транзакцій:*\n\n",
        "unknown": "❓ Використовуйте кнопки нижче 👇\nЯкщо не знаєте що робити — натисніть «❓ Інструкція»",
        "follow_instructions": "⏳ Слідуйте інструкціям бота."
    },
    "ar": {
        "welcome": "✨ *مرحبًا بك في Trade Bot!* ✨\n\n🤝 تبادل آمن للهدايا\n\n📌 استخدم الأزرار أدناه للبدء.\n❓ إذا كنت لا تعرف ما تفعل، اضغط «تعليمات».",
        "use_buttons": "💬 استخدم الأزرار أدناه للتفاعل مع البوت:",
        "instruction_title": "📖 *تعليمات استخدام Trade Bot*\n\nاختر دورك:",
        "instruction_seller": "📤 *تعليمات للبائع:*\n\n1️⃣ اضغط «🆕 إنشاء صفقة»\n2️⃣ أرسل *رابط الهدية* التي تبيعها\n3️⃣ حدد *السعر بالدولار* 💰\n4️⃣ بعد الإنشاء ستحصل على *رقم* و *كلمة مرور* الصفقة\n5️⃣ أرسلها للمشتري\n\n6️⃣ بعد أن يدفع المشتري:\n   📦 *أعد توجيه الهدية إلى @ValletTrade*\n   ✅ بعد التحقق، ستتلقى المال في رصيدك\n\n⚠️ *مهم:* لا ترسل الهدية مباشرة للمشتري!\nفقط من خلال الضامن @ValletTrade",
        "instruction_buyer": "🛒 *تعليمات للمشتري:*\n\n1️⃣ اضغط «🔗 الاتصال»\n2️⃣ أدخل *رقم الصفقة* و *كلمة المرور*\n3️⃣ ادفع ثمن السلعة 💳\n   _(المال لا يذهب مباشرة للبائع)_\n\n4️⃣ بعد الدفع، انتظر:\n   • البائع يرسل الهدية للضامن @ValletTrade\n   • الضامن يتحقق منها\n   • بعد التحقق، تتلقى الهدية ✅\n\n🔒 *الأمان:* جميع الصفقات تمر عبر الضامن!\nأموالك آمنة حتى استلام السلعة.",
        "back_to_roles": "🔙 العودة للأدوار",
        "close": "❌ إغلاق",
        "select_role": "اختر دورك:",
        "create_exchange": "🆕 إنشاء صفقة",
        "connect": "🔗 الاتصال",
        "balance": "💰 الرصيد",
        "history": "📊 السجل",
        "instruction_btn": "❓ تعليمات",
        "cancel": "❌ إلغاء",
        "no_active": "❌ لا توجد عمليات نشطة.",
        "cancelled": "✅ تم إلغاء العملية.",
        "exchange_created": "🎉 *تم إنشاء الصفقة!*",
        "exchange_number": "📌 *الرقم:* `{}`",
        "exchange_password": "🔑 *كلمة المرور:* `{}`",
        "send_gift_link": "📎 أرسل *رابط الهدية*:",
        "invalid_link": "❌ أرسل رابطًا (http:// أو https://)",
        "enter_price": "💰 حدد *السعر* (بالدولار):",
        "price_invalid": "❌ أدخل رقمًا",
        "price_zero": "❌ يجب أن يكون السعر > 0",
        "exchange_created_success": "✅ *تم إنشاء الصفقة!* 🎉\n\n📋 الرقم: `{}`\n🔑 كلمة المرور: `{}`\n💰 السعر: {}\n\n⏳ في انتظار المشتري...\n📖 لا تعرف ما تفعل؟ اضغط «❓ تعليمات»",
        "enter_exchange_id": "🔍 أدخل *رقم الصفقة*:\n\n_(الذي تلقته من البائع)_",
        "exchange_not_found": "❌ *الصفقة #{} غير موجودة!*\nتحقق من الرقم وحاول مرة أخرى.",
        "exchange_completed": "❌ *الصفقة #{} مكتملة بالفعل!*",
        "exchange_active": "❌ *الصفقة #{} نشطة بالفعل!*",
        "enter_password": "🔑 أدخل *كلمة المرور* للصفقة #{}:",
        "wrong_password": "❌ *كلمة مرور خاطئة!*\nحاول مرة أخرى.",
        "connect_success": "✅ *الاتصال ناجح!* 🔗\n\n📋 *الصفقة #{}*\n🔗 *الرابط:* {}\n💰 *السعر:* {}\n\n⏳ *في انتظار اكتمال الصفقة...*\n📖 لا تعرف ما تفعل؟ اضغط «❓ تعليمات»",
        "someone_connected": "🔔 *شخص ما اتصل بالصفقة #{}!*\n\n💰 *السعر:* {}\n📦 جهز الهدية!\n\n📖 التعليمات: اضغط «❓ تعليمات»",
        "deal_completed_buyer": "✅ *الصفقة #{} مكتملة!* 🎉\n\n📦 *أرسل الهدية للضامن:* @ValletTrade\n🔗 رابط الهدية: {}\n💰 السعر: {}\n\n⏳ بعد التحقق من قبل الضامن، سيتم إيداع المبلغ للبائع.\n\n📖 التعليمات: اضغط «❓ تعليمات»",
        "deal_completed_seller": "✅ *الصفقة #{} مكتملة!* 🎉\n\n💰 *المشتري دفع {}*\n📦 أرسل الهدية للضامن: @ValletTrade\n🔗 رابط الهدية: {}\n\n⏳ بعد التحقق من قبل الضامن، سيتم إيداع المبلغ في رصيدك.\n\n📖 التعليمات: اضغط «❓ تعليمات»",
        "balance_text": "💰 *رصيدك:* ${:.2f}\n\n📊 إجمالي المعاملات: {}",
        "history_empty": "📭 السجل فارغ.",
        "history_text": "📊 *سجل المعاملات:*\n\n",
        "unknown": "❓ استخدم الأزرار أدناه 👇\nإذا كنت لا تعرف ما تفعل، اضغط «❓ تعليمات»",
        "follow_instructions": "⏳ اتبع تعليمات البوت."
    }
}

# ==================== ФУНКЦИИ ====================
def get_lang(user_id: int) -> str:
    return user_lang.get(user_id, "ru")

def get_text(user_id: int, key: str, *args) -> str:
    lang = get_lang(user_id)
    text = LANG.get(lang, LANG["ru"]).get(key, LANG["ru"].get(key, key))
    if args:
        return text.format(*args)
    return text

def generate_code():
    return f"{random.randint(0, 9999):04d}"

def format_price(price):
    if price.is_integer():
        return f"${int(price)}"
    return f"${price:.2f}"

def get_balance(user_id: int) -> float:
    return user_balances.get(user_id, 0.0)

def add_to_balance(user_id: int, amount: float, exchange_id: str):
    if user_id not in user_balances:
        user_balances[user_id] = 0.0
    user_balances[user_id] += amount
    
    if user_id not in user_history:
        user_history[user_id] = []
    user_history[user_id].append({
        "type": "income",
        "amount": amount,
        "exchange_id": exchange_id,
        "date": str(asyncio.get_event_loop().time())
    })
    return user_balances[user_id]

def subtract_from_balance(user_id: int, amount: float, exchange_id: str):
    if user_id not in user_balances:
        user_balances[user_id] = 0.0
    user_balances[user_id] -= amount
    
    if user_id not in user_history:
        user_history[user_id] = []
    user_history[user_id].append({
        "type": "outcome",
        "amount": amount,
        "exchange_id": exchange_id,
        "date": str(asyncio.get_event_loop().time())
    })
    return user_balances[user_id]

# ==================== КЛАВИАТУРЫ ====================
def get_lang_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru"),
                InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en")
            ],
            [
                InlineKeyboardButton(text="🇺🇦 Українська", callback_data="lang_uk"),
                InlineKeyboardButton(text="🇸🇦 العربية", callback_data="lang_ar")
            ]
        ]
    )
    return keyboard

def get_main_keyboard(user_id: int):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=get_text(user_id, "create_exchange"))],
            [KeyboardButton(text=get_text(user_id, "connect"))],
            [KeyboardButton(text=get_text(user_id, "balance")), KeyboardButton(text=get_text(user_id, "history"))],
            [KeyboardButton(text=get_text(user_id, "instruction_btn")), KeyboardButton(text=get_text(user_id, "cancel"))]
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие..." if get_lang(user_id) == "ru" else "Choose action..."
    )
    return keyboard

def get_cancel_keyboard(user_id: int):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=get_text(user_id, "cancel"))]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_instruction_keyboard(user_id: int):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="📤 " + ("Продавец" if get_lang(user_id) == "ru" else "Seller" if get_lang(user_id) == "en" else "Продавець" if get_lang(user_id) == "uk" else "بائع"),
                callback_data="instruction_seller"
            )],
            [InlineKeyboardButton(
                text="🛒 " + ("Покупатель" if get_lang(user_id) == "ru" else "Buyer" if get_lang(user_id) == "en" else "Покупець" if get_lang(user_id) == "uk" else "مشتري"),
                callback_data="instruction_buyer"
            )],
            [InlineKeyboardButton(
                text=get_text(user_id, "close"),
                callback_data="instruction_close"
            )]
        ]
    )
    return keyboard

# ==================== СОСТОЯНИЯ ====================
class TradeStates(StatesGroup):
    waiting_for_exchange = State()
    waiting_for_password = State()
    waiting_for_create_link = State()
    waiting_for_create_price = State()

# ==================== КОМАНДЫ ====================
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    
    await message.answer(
        "🌍 *Выберите язык / Choose language / Оберіть мову / اختر اللغة:*",
        parse_mode="Markdown",
        reply_markup=get_lang_keyboard()
    )

@dp.callback_query(lambda c: c.data.startswith("lang_"))
async def process_lang(callback_query: types.CallbackQuery, state: FSMContext):
    lang_code = callback_query.data.split("_")[1]
    user_id = callback_query.from_user.id
    
    user_lang[user_id] = lang_code
    
    await bot.answer_callback_query(callback_query.id)
    
    web_app_button = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="🚀 Открыть приложение" if lang_code == "ru" else "🚀 Open app" if lang_code == "en" else "🚀 Відкрити застосунок" if lang_code == "uk" else "🚀 فتح التطبيق",
                web_app=WebAppInfo(url="https://ajl7oputm.github.io/AppTrade/")
            )],
            [InlineKeyboardButton(
                text="💬 " + ("Использовать чат" if lang_code == "ru" else "Use chat" if lang_code == "en" else "Використовувати чат" if lang_code == "uk" else "استخدام الدردشة"),
                callback_data="use_chat"
            )]
        ]
    )
    
    await bot.send_message(
        user_id,
        get_text(user_id, "welcome"),
        parse_mode="Markdown",
        reply_markup=web_app_button
    )

@dp.callback_query(lambda c: c.data == "use_chat")
async def process_callback(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(
        user_id,
        get_text(user_id, "use_buttons"),
        reply_markup=get_main_keyboard(user_id)
    )

@dp.message(Command("app"))
async def cmd_app(message: types.Message):
    user_id = message.from_user.id
    web_app_button = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="🚀 " + ("Открыть приложение" if get_lang(user_id) == "ru" else "Open app" if get_lang(user_id) == "en" else "Відкрити застосунок" if get_lang(user_id) == "uk" else "فتح التطبيق"),
                web_app=WebAppInfo(url="https://ajl7oputm.github.io/AppTrade/")
            )]
        ]
    )
    
    await message.answer(
        "📱 *Trade Bot App*\n\n" + ("Нажмите кнопку, чтобы открыть приложение!" if get_lang(user_id) == "ru" else "Press the button to open the app!" if get_lang(user_id) == "en" else "Натисніть кнопку, щоб відкрити застосунок!" if get_lang(user_id) == "uk" else "اضغط الزر لفتح التطبيق!"),
        parse_mode="Markdown",
        reply_markup=web_app_button
    )

@dp.message(Command("balance"))
async def cmd_balance(message: types.Message):
    user_id = message.from_user.id
    balance = get_balance(user_id)
    await message.answer(
        get_text(user_id, "balance_text", balance, len(user_history.get(user_id, []))),
        parse_mode="Markdown",
        reply_markup=get_main_keyboard(user_id)
    )

@dp.message(Command("history"))
async def cmd_history(message: types.Message):
    user_id = message.from_user.id
    history = user_history.get(user_id, [])
    if not history:
        await message.answer(get_text(user_id, "history_empty"), reply_markup=get_main_keyboard(user_id))
        return
    
    text = get_text(user_id, "history_text")
    for h in history[-10:]:
        sign = "+" if h["type"] == "income" else "-"
        text += f"└ #{h['exchange_id']}: {sign}${h['amount']:.2f}\n"
    
    await message.answer(text, parse_mode="Markdown", reply_markup=get_main_keyboard(user_id))

@dp.message(Command("cancel"))
async def cmd_cancel(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    current_state = await state.get_state()
    if current_state is None:
        await message.answer(get_text(user_id, "no_active"), reply_markup=get_main_keyboard(user_id))
        return
    await state.clear()
    await message.answer(get_text(user_id, "cancelled"), reply_markup=get_main_keyboard(user_id))

@dp.message(Command("instruction"))
async def cmd_instruction(message: types.Message):
    user_id = message.from_user.id
    await show_instruction(message, user_id)

# ==================== ИНСТРУКЦИЯ ====================
async def show_instruction(message: types.Message, user_id: int):
    await message.answer(
        get_text(user_id, "instruction_title"),
        parse_mode="Markdown",
        reply_markup=get_instruction_keyboard(user_id)
    )

@dp.callback_query(lambda c: c.data.startswith("instruction_"))
async def instruction_callback(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    action = callback_query.data.split("_")[1]
    
    if action == "close":
        await bot.answer_callback_query(callback_query.id)
        await bot.delete_message(user_id, callback_query.message.message_id)
        return
    
    if action == "seller":
        text = get_text(user_id, "instruction_seller")
    elif action == "buyer":
        text = get_text(user_id, "instruction_buyer")
    else:
        await bot.answer_callback_query(callback_query.id)
        return
    
    await bot.answer_callback_query(callback_query.id)
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=get_text(user_id, "back_to_roles"),
                callback_data="instruction_back"
            )],
            [InlineKeyboardButton(
                text=get_text(user_id, "close"),
                callback_data="instruction_close"
            )]
        ]
    )
    
    await bot.edit_message_text(
        text,
        chat_id=user_id,
        message_id=callback_query.message.message_id,
        parse_mode="Markdown",
        reply_markup=keyboard
    )

@dp.callback_query(lambda c: c.data == "instruction_back")
async def instruction_back(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    await bot.answer_callback_query(callback_query.id)
    await bot.edit_message_text(
        get_text(user_id, "instruction_title"),
        chat_id=user_id,
        message_id=callback_query.message.message_id,
        parse_mode="Markdown",
        reply_markup=get_instruction_keyboard(user_id)
    )

# ==================== КНОПКА ИНСТРУКЦИЯ ====================
@dp.message(lambda message: message.text == "❓ Инструкция" or message.text == "❓ Instructions" or message.text == "❓ Інструкція" or message.text == "❓ تعليمات")
async def button_instruction(message: types.Message):
    user_id = message.from_user.id
    await show_instruction(message, user_id)

# ==================== СОЗДАНИЕ СДЕЛКИ ====================
@dp.message(lambda message: message.text in ["🆕 Создать сделку", "🆕 Create deal", "🆕 Створити угоду", "🆕 إنشاء صفقة"])
async def button_create_exchange(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    exchange_id = generate_code()
    while exchange_id in exchanges:
        exchange_id = generate_code()
    
    password = generate_code()
    
    exchanges[exchange_id] = {
        "password": password,
        "creator": user_id,
        "gift_link": None,
        "price": None,
        "buyer": None,
        "status": "waiting_for_link",
        "created_at": asyncio.get_event_loop().time()
    }
    
    await state.update_data(exchange_id=exchange_id)
    await state.set_state(TradeStates.waiting_for_create_link)
    
    await message.answer(
        f"{get_text(user_id, 'exchange_created')}\n\n"
        f"{get_text(user_id, 'exchange_number', exchange_id)}\n"
        f"{get_text(user_id, 'exchange_password', password)}\n\n"
        f"{get_text(user_id, 'send_gift_link')}",
        parse_mode="Markdown",
        reply_markup=get_cancel_keyboard(user_id)
    )

@dp.message(TradeStates.waiting_for_create_link)
async def process_create_link(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    gift_link = message.text.strip()
    
    if not re.match(r'^https?://', gift_link):
        await message.answer(get_text(user_id, "invalid_link"), parse_mode="Markdown")
        return
    
    data = await state.get_data()
    exchange_id = data.get('exchange_id')
    
    if exchange_id in exchanges:
        exchanges[exchange_id]["gift_link"] = gift_link
        exchanges[exchange_id]["status"] = "waiting_for_price"
    
    await state.set_state(TradeStates.waiting_for_create_price)
    await message.answer(get_text(user_id, "enter_price"), parse_mode="Markdown")

@dp.message(TradeStates.waiting_for_create_price)
async def process_create_price(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    try:
        price = float(message.text.replace(',', '.'))
        if price <= 0:
            await message.answer(get_text(user_id, "price_zero"))
            return
    except ValueError:
        await message.answer(get_text(user_id, "price_invalid"))
        return
    
    data = await state.get_data()
    exchange_id = data.get('exchange_id')
    
    if exchange_id in exchanges:
        exchanges[exchange_id]["price"] = price
        exchanges[exchange_id]["status"] = "waiting_for_buyer"
    
    price_str = format_price(price)
    
    await message.answer(
        get_text(user_id, "exchange_created_success", exchange_id, exchanges[exchange_id]['password'], price_str),
        parse_mode="Markdown",
        reply_markup=get_main_keyboard(user_id)
    )
    await state.clear()

# ==================== ПОДКЛЮЧЕНИЕ ====================
@dp.message(lambda message: message.text in ["🔗 Подключиться", "🔗 Connect", "🔗 Підключитися", "🔗 الاتصال"])
async def button_connect_exchange(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    await state.set_state(TradeStates.waiting_for_exchange)
    await message.answer(
        get_text(user_id, "enter_exchange_id"),
        parse_mode="Markdown",
        reply_markup=get_cancel_keyboard(user_id)
    )

@dp.message(TradeStates.waiting_for_exchange)
async def process_exchange_number(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    exchange_id = message.text.strip()
    
    if exchange_id not in exchanges:
        await message.answer(
            get_text(user_id, "exchange_not_found", exchange_id),
            parse_mode="Markdown"
        )
        return
    
    if exchanges[exchange_id]["status"] == "completed":
        await message.answer(
            get_text(user_id, "exchange_completed", exchange_id),
            parse_mode="Markdown"
        )
        await state.clear()
        return
    
    if exchanges[exchange_id]["status"] == "active":
        await message.answer(
            get_text(user_id, "exchange_active", exchange_id),
            parse_mode="Markdown"
        )
        await state.clear()
        return
    
    await state.update_data(exchange_id=exchange_id)
    await state.set_state(TradeStates.waiting_for_password)
    
    await message.answer(
        get_text(user_id, "enter_password", exchange_id),
        parse_mode="Markdown"
    )

@dp.message(TradeStates.waiting_for_password)
async def process_password(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    password = message.text.strip()
    data = await state.get_data()
    exchange_id = data.get('exchange_id')
    
    if exchange_id not in exchanges:
        await message.answer(get_text(user_id, "exchange_not_found", exchange_id), reply_markup=get_main_keyboard(user_id))
        await state.clear()
        return
    
    if exchanges[exchange_id]["password"] != password:
        await message.answer(
            get_text(user_id, "wrong_password"),
            parse_mode="Markdown"
        )
        return
    
    # ✅ Подключение
    buyer_id = user_id
    exchanges[exchange_id]["buyer"] = buyer_id
    exchanges[exchange_id]["status"] = "active"
    
    price = exchanges[exchange_id]["price"]
    gift_link = exchanges[exchange_id]["gift_link"]
    price_str = format_price(price)
    
    # Уведомление покупателя
    await message.answer(
        get_text(user_id, "connect_success", exchange_id, gift_link, price_str),
        parse_mode="Markdown",
        reply_markup=get_main_keyboard(user_id)
    )
    
    # Уведомление продавца
    creator_id = exchanges[exchange_id]["creator"]
    try:
        await bot.send_message(
            creator_id,
            get_text(creator_id, "someone_connected", exchange_id, price_str),
            parse_mode="Markdown"
        )
    except:
        pass
    
    await state.clear()
    
    # ⏳ Задержка 60 секунд
    await asyncio.sleep(60)
    
    # Проверяем, активна ли сделка
    if exchange_id not in exchanges or exchanges[exchange_id]["status"] != "active":
        return
    
    # Завершаем сделку
    exchanges[exchange_id]["status"] = "completed"
    
    creator_id = exchanges[exchange_id]["creator"]
    buyer_id = exchanges[exchange_id]["buyer"]
    amount = exchanges[exchange_id]["price"]
    gift_link = exchanges[exchange_id]["gift_link"]
    price_str = format_price(amount)
    
    # Сообщение покупателю
    try:
        await bot.send_message(
            buyer_id,
            get_text(buyer_id, "deal_completed_buyer", exchange_id, gift_link, price_str),
            parse_mode="Markdown",
            reply_markup=get_main_keyboard(buyer_id)
        )
    except:
        pass
    
    # Сообщение продавцу
    try:
        await bot.send_message(
            creator_id,
            get_text(creator_id, "deal_completed_seller", exchange_id, price_str, gift_link),
            parse_mode="Markdown",
            reply_markup=get_main_keyboard(creator_id)
        )
    except:
        pass

# ==================== КНОПКА БАЛАНС ====================
@dp.message(lambda message: message.text in ["💰 Баланс", "💰 Balance", "💰 Баланс", "💰 الرصيد"])
async def button_balance(message: types.Message):
    await cmd_balance(message)

# ==================== КНОПКА ИСТОРИЯ ====================
@dp.message(lambda message: message.text in ["📊 История", "📊 History", "📊 Історія", "📊 السجل"])
async def button_history(message: types.Message):
    await cmd_history(message)

# ==================== КНОПКА ОТМЕНА ====================
@dp.message(lambda message: message.text in ["❌ Отмена", "❌ Cancel", "❌ Відміна", "❌ إلغاء"])
async def button_cancel(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    current_state = await state.get_state()
    if current_state is None:
        await message.answer(get_text(user_id, "no_active"), reply_markup=get_main_keyboard(user_id))
        return
    await state.clear()
    await message.answer(get_text(user_id, "cancelled"), reply_markup=get_main_keyboard(user_id))

# ==================== ОСТАЛЬНЫЕ СООБЩЕНИЯ ====================
@dp.message()
async def handle_all_messages(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    current_state = await state.get_state()
    
    if current_state is None:
        await message.answer(
            get_text(user_id, "unknown"),
            reply_markup=get_main_keyboard(user_id)
        )
    else:
        await message.answer(
            get_text(user_id, "follow_instructions"),
            reply_markup=get_main_keyboard(user_id)
        )

# ==================== ЗАПУСК ====================
async def main():
    print("=" * 50)
    print("🌍 TRADE BOT (Многоязычный)")
    print("🇷🇺 Русский | 🇬🇧 English | 🇺🇦 Українська | 🇸🇦 العربية")
    print("🔗 Web App: https://ajl7oputm.github.io/AppTrade/")
    print("=" * 50)
    
    try:
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        print("\n🛑 Бот остановлен")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
