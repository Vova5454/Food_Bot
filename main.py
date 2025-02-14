import telebot as tb
from telebot import types
import json

ITEMS_PER_PAGE = 4
token = "7949756952:AAGheS7kkN67sGaXqWVN0omyEzW0uBev6Uo"
bot = tb.TeleBot(token)

with open("client_info.json", "r", encoding="utf-8") as f:
    user_info = json.load(f)

menu_items = [
        {"name": "Грибной суп", "price": "450 руб.", "photo": "mushroom_soup.png"},
        {"name": "Салат Цезарь", "price": "550 руб.", "photo": "caesar.png"},
        {"name": "Утка с апельсинами", "price": "700 руб.", "photo": "duck_orange.png"},
        {"name": "Бефстроганов", "price": "650 руб.", "photo": "stroganoff.png"},
        {"name": "Ризотто", "price": "500 руб.", "photo": "risotto.png"},
        {"name": "Тирамису", "price": "400 руб.", "photo": "tiramisu.png"},
        {"name": "Блины", "price": "300 руб.", "photo": "pancakes.png"},
        {"name": "Паста Карбонара", "price": "550 руб.", "photo": "carbonara.png"},
        {"name": "Гаспачо", "price": "350 руб.", "photo": "gazpacho.png"},
        {"name": "Фалафель", "price": "400 руб.", "photo": "falafel.png"},
        {"name": "Вода", "price": "100 руб", "photo": "water.png" },
        {"name": "Яблочный сок", "price": "150 руб", "photo": "apple_juice.png"},
        {"name": "Кока кола", "price": "200 руб", "photo": "cola.png"},
        {"name": "Молоко", "price": "150 руб", "photo": "milk.png"},
        {"name": "Махито", "price": "500 руб", "photo": "majito.png"},
        {"name": "Спрайт", "price": "200 руб", "photo": "sprite.png"},
        {"name": "Горячий шоколад", "price": "300 руб", "photo": "hot_chocolate.png"},
        {"name": "Чай", "price": "150 руб", "photo": "tea.png"},
        {"name": "Молочный коктель", "price": "250 руб", "photo": "milkshake.png"},
        {"name": "Фруктовый смузи", "price": "500 руб", "photo": "smoothie.png"}]

@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, "Привет. Я бот для заказа еды😀", reply_markup=summon_button())
    with open("client_info.json", "r", encoding="utf-8") as f:
        user_info = json.load(f)
    for client in user_info.get("clients", []):
        if client["id"] == str(message.chat.id):
            bot.send_message(message.chat.id, "Вы уже зарегистрированы!", reply_markup=summon_button())
            break
    else:
        user_info["clients"].append({"id": str(message.chat.id), "cart": []})
        bot.send_message(message.chat.id, "Вы теперь зарегистрированы!", reply_markup=summon_button())
    with open("client_info.json", "w", encoding="utf-8") as f:
        json.dump(user_info, f, ensure_ascii=False, indent=4)

@bot.message_handler(commands=["add_info"])
def add_info(message):
    bot.send_message(message.chat.id, "Введите ваше имя: ", reply_markup=summon_button())
    bot.register_next_step_handler_by_chat_id(message.chat.id, save_name)

@bot.message_handler(func=lambda message: True)
def echo(message):
    if message.text == "Меню🍜":
        bot.send_message(message.chat.id, "Просмотр меню🥪", reply_markup=menu_keyboard())
    if message.text == "Корзина🗑️":
        cart = get_cart(message.chat.id)
        keyboard = types.InlineKeyboardMarkup()
        if cart == []:
            bot.send_message(message.chat.id, "Ваша корзина пуста!", reply_markup=summon_button())
        else:
            for dish in cart:
                keyboard.add(types.InlineKeyboardButton(text=f"{dish[0]} x{dish[1]}", callback_data=f"remove_{dish[0]}"))
            bot.send_message(message.chat.id, "Просмотр корзины🗑️", reply_markup=keyboard)
    if message.text == "Заказать🍕":
        with open("client_info.json", "r", encoding="utf-8") as f:
            user_info = json.load(f)
        client_data = user_info.get("clients", [])
        for client in client_data:
            if client["id"] == str(message.chat.id):
                cart = client["cart"]
        if cart == []:
            bot.send_message(message.chat.id, "Ваша корзина пуста!", reply_markup=summon_button())
        else:
            order = "Ваш заказ:\n"
            for item in cart:
                order = f"{order}{item[0]} x{item[1]}\n"
            bot.send_message(message.chat.id, order, reply_markup=summon_button())
            bot.send_message(message.chat.id, "Подтвердите правильность заказа:", reply_markup=confirm_buttons())
    if message.text == "Отмена❌":
        bot.send_message(message.chat.id, "Заказ не принят в работу. Вы можете изменить заказ.", reply_markup=summon_button())
    if message.text == "Подтвердить✅":
        bot.send_message(message.chat.id, "Выберите адрес любым способом:\nГеометка\nТекст", reply_markup=summon_button())
        bot.register_next_step_handler_by_chat_id(message.chat.id, create_order)

@bot.callback_query_handler(func=lambda call: True)
def query(call):
    global user_info
    if call.data.startswith("page_"):
        _, page = call.data.split("_")
        markup = menu_keyboard(int(page))
        bot.edit_message_text(chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              text="Просмотр меню🥪",
                              reply_markup=markup)
    if call.data.startswith("food_"):
        info = call.data.split("_")
        add_to_cart(call.message.chat.id, info[1])
        bot.send_message(call.message.chat.id, f"{info[1]} добавлено в заказ!", reply_markup=summon_button())
    if call.data.startswith("remove_"):
        food = call.data.split("_")[1]
        delete_from_cart(call.message, food)
        bot.send_message(call.message.chat.id, f"{food} удалено из карзины!", reply_markup=summon_button())
        cart = get_cart(call.message.chat.id)
        if cart == []:
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Ваша корзина пуста!")
        else:
            keyboard = types.InlineKeyboardMarkup()
            for dish in cart:
                keyboard.add(types.InlineKeyboardButton(text=f"{dish[0]} x{dish[1]}", callback_data=f"remove_{dish[0]}"))
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Просмотр корзины🗑️", reply_markup=keyboard)

def summon_button():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("Меню🍜")
    btn2 = types.KeyboardButton("Корзина🗑️")
    btn3 = types.KeyboardButton("Заказать🍕")
    keyboard.add(btn1, btn2, btn3)
    return keyboard

def confirm_buttons():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    confirm = types.KeyboardButton("Подтвердить✅")
    decline = types.KeyboardButton("Отмена❌")
    keyboard.add(confirm, decline)
    return keyboard

def menu_keyboard(page=0):
    keyboard = types.InlineKeyboardMarkup()
    start_index = page * ITEMS_PER_PAGE
    end_index = start_index + ITEMS_PER_PAGE
    for item in menu_items[start_index:end_index]:
        button = types.InlineKeyboardButton(text=f"{item["name"]}", callback_data=f"food_{item['name']}")
        keyboard.add(button)
    if end_index < len(menu_items):
        keyboard.add(types.InlineKeyboardButton(text="-->", callback_data=f"page_{page+1}"))
    if page > 0:
        keyboard.add(types.InlineKeyboardButton(text="<--", callback_data=f"page_{page-1}"))
    return keyboard

def save_name(message):
    name = message.text
    bot.send_message(message.chat.id, "Имя сохранено, напишите номер вашего телефона: ", reply_markup=summon_button())
    bot.register_next_step_handler_by_chat_id(message.chat.id, save_phone, name)

def save_phone(message, name):
    global user_info
    try:
        phone = int(message.text)
        client_data = user_info.get("clients", [])
        for client in client_data:
            if client["id"] == str(message.chat.id):
                client["name"] = name
                client["phone"] = str(phone)
                save_data(user_info)
                bot.send_message(message.chat.id, f"Имя: {name}, Телефон: {phone}", reply_markup=summon_button())
    except ValueError:
        bot.send_message(message.chat.id, "Номер телефона должен содержать только цифры! Попробуйте заново: /add_info", reply_markup=summon_button())

def save_data(user_info):
    with open("client_info.json", "w", encoding="utf-8") as f:
        json.dump(user_info, f, ensure_ascii=False, indent=4)

def get_cart(client_id):
    with open("client_info.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    clients = data.get("clients", [])
    for client in clients:
        if client.get("id") == str(client_id):
            return client.get("cart", []) 
    return []

def add_to_cart(client_id, item):
    with open("client_info.json", "r", encoding="utf-8") as file:
        user_info = json.load(file)
    client_data = user_info.get("clients", [])
    for client in client_data:
        if client.get("id") == str(client_id):
            found = False
            for dish in client["cart"]:
                if dish[0] == item:
                    dish[1] += 1
                    found = True
            if not found:
                client["cart"].append([item, 1])
    user_info["clients"] = client_data
    with open("client_info.json", "w", encoding="utf-8") as file:
        json.dump(user_info, file, ensure_ascii=False, indent=4)

def delete_from_cart(message, item):
    with open("client_info.json", "r", encoding="utf-8") as f:
        user_info = json.load(f)
    client_data = user_info.get("clients", [])
    for client in client_data:
        if client.get("id") == str(message.chat.id):
            for dish in client["cart"]:
                if dish[0] == item:
                    if dish[1] == 1:
                        client["cart"].remove(dish)
                    else:
                        dish[1] -= 1
    user_info["clients"] = client_data
    with open("client_info.json", "w", encoding="utf-8") as file:
        json.dump(user_info, file, ensure_ascii=False, indent=4)

def create_order(message):
    if message.content_type == "text":
        addres = message.text
    elif message.content_type == "location":
        coord1 = message.location.latitude
        coord2 = message.location.longitude
        addres = f"{coord1}, {coord2}"
    bot.send_message(message.chat.id, f"Ваш адрес: {addres}", reply_markup=summon_button())
    bot.send_message(message.chat.id, f"Стоимость заказа: {calculate_cart_total(message.chat.id)}", reply_markup=summon_button())
    bot.send_message(message.chat.id, "Доступна только оплата наличными курьеру.", reply_markup=summon_button())
    bot.send_message(message.chat.id, "Заказ принят в работу🚀", reply_markup=summon_button())

def calculate_cart_total(client_id):
    total = 0
    cart = get_cart(client_id)
    for item in cart:
        for dish in menu_items:
            if item[0] == dish["name"]:
                total += int(dish["price"].split(" ")[0]) * item[1]
    return total

           
bot.polling(none_stop=True)