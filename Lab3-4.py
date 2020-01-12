import pika
import time
import threading
import json
import random
import string
from tkinter import *

# Функция, которая принимает сообщения из очереди
def Receiver():
    # Функция, которая активируется когда в очереди появляется новое сообщение
    def callback(ch, method, properties, body):
        body = json.loads(body) # Распаковываем сообщение в словарь 
        currentNick = nickNameEntry.get() # Получаем ник, записанный в поле ввода ника на форме
        if body["nickname"] != currentNick: # Если ник в сообщение не равен текущему нику
            if body["notify"] == True: # Если тип сообщения это нотификация
                messagesList.insert(END, body["nickname"] + " зашел в чат.") # Сообщаем всем пользователям что новый юзер зашел в чат
                return
            
            msg = body["msg"] # Записываем в переменую текст сообщения
            nick = body["nickname"] # Записываем в переменную ник отправителя

            if msg.startswith("@who_are_here?"): # Если сообщение это команда @who_are_here?
                SendMessage("[+] i am here!", False, nick) # Тогда мы посылаем сообщение что мы тут определенному пользователю
                return

            if msg.startswith("@"): # Если сообщение начинается со знака @
                if msg.startswith("@" + currentNick): # Если сообщение начинается с ника текущего пользователя (т.е. личное сообщение)
                    messagesList.insert(END, f"[PM][{nick}] > {msg.split(' ', maxsplit = 1)[1]}") # тогда выводим что это личное сообщение и от кого
            else:
                if body["msgFor"] == '' or body["msgFor"] == currentNick: # Если сообщение никому не адресовано или адресовано текущему пользователю
                    message = nick + " < " + msg # Формируем сообщение которые выведется в ListBox
                    messagesList.insert(END, message) # Добавляем в конец полученное сообщение

    connection = pika.BlockingConnection(pika.ConnectionParameters(host = 'localhost')) # Подключение к localhost

    channel = connection.channel() # Подключаемся к каналу
    
    channel.exchange_declare(exchange='chat_messages', exchange_type='fanout') # fanout - тип для рассылки сообщения всем

    result = channel.queue_declare(queue='', exclusive=True) # exclusive - флаг, указывающий что если пользователь отключится, очередь должна будет удалиться
    queueName = result.method.queue # Получаем имя очереди

    channel.queue_bind(exchange='chat_messages', queue=queueName) # Устанавливаем взаимосвязь между обменником и очередью 

    channel.basic_consume(queue=queueName, on_message_callback=callback, auto_ack=True) # Указываем функцию, которая будем активироваться при появлении новых сообщений 

    channel.start_consuming() # Начинаем слушать канал

# Функция для генерации рандомной строки из латинских букв указанной длины
def RandomString(stringLength=10):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(stringLength))

# Функция для отправки сообщения
def SendMessage(message, toMe = True, msgFor = ''):
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost')) # Подключение к localhost
    channel = connection.channel() # Подключение к каналу
    channel.exchange_declare(exchange='chat_messages', exchange_type='fanout') 

    nickName = nickNameEntry.get() # Записываем в переменную ник, указанный в поле ввода ника на форме

    if toMe == True: # Если стоит флаг toMe, указывающий что нужно показать отправленное нами сообщение в нашем окне чата
        messagesList.insert(END, nickName + " > " + message) # Вставляем сообщение в ListBox сообщений

    # Создаем словарь и записываем в него нужны данные
    body = {"nickname" : nickName, "datetime" : time.time(), "msg" : message, "notify" : False, "msgFor" : msgFor}
    # Отправляем сообщение
    channel.basic_publish(exchange = 'chat_messages', routing_key = 'chat_messages', body = json.dumps(body), 
                          properties=pika.BasicProperties(delivery_mode=2,))    
    connection.close() # Закрываем соединение

# Функция для отправки сообщения что мы новый пользователь в чате
def SendHello():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()
    channel.exchange_declare(exchange='chat_messages', exchange_type='fanout')

    nickName = nickNameEntry.get()
    body = {"nickname" : nickName, "notify" : True}
    channel.basic_publish(exchange = 'chat_messages', routing_key = 'chat_messages', body = json.dumps(body), 
                          properties=pika.BasicProperties(delivery_mode=2,))    
    connection.close()

# Создание и настройка формы tkinter
mainWindow = Tk()
mainWindow.title("Чат")
mainWindow.geometry("300x250")

messagesFrame = Frame(mainWindow)
nickFrame = Frame(mainWindow)
buttonFrame = Frame(mainWindow)
scrollbar = Scrollbar(messagesFrame) 
messagesList = Listbox(messagesFrame, height = 10, width = 50, yscrollcommand = scrollbar.set)

nickFrame.pack(side = TOP, fill = Y)
scrollbar.pack(side = RIGHT, fill = Y)
messagesList.pack(side = LEFT, fill = BOTH)
messagesFrame.pack()

nickLabel = Label(nickFrame, text = "Ник:")
nickLabel.pack(side = LEFT, anchor = S, padx = 5)
defaultNick = StringVar(nickFrame, value='User_' + RandomString(5))
nickNameEntry = Entry(nickFrame, textvariable = defaultNick)
nickNameEntry.pack(side = LEFT, anchor = SE, pady = 5)

lb = Label(buttonFrame, text = "Текст:")
lb.pack(side = LEFT, anchor = S, padx = 5)
messageEntry = Entry(buttonFrame, textvariable = '')
messageEntry.pack(side = LEFT, anchor = SE, pady =  5)

send_button = Button(buttonFrame, text = "Отправить", command = lambda: SendMessage(messageEntry.get()))
send_button.pack(side = LEFT, anchor = S, pady = 5, padx = 5)

buttonFrame.pack()
# конец создания и настройки формы tkinter

receive_thread = threading.Thread(target = Receiver) # Создаем поток, в котором будет функция слушающая новые сообщения
receive_thread.start() # Запускаем поток

SendHello() # Уведомляем пользователей что мы зашли в чат

mainWindow.mainloop() # Запускаем созданную и настроенную форму tkinter