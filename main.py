import config
from random import randrange
from time import time
import requests

import vk_api
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.longpoll import VkLongPoll, VkEventType

from vk_agent import VkAgent
from data_base_v2 import set_favorite, show_favorite, create_table


token = config.vk_group_token
user_token = config.vk_user_token

vk = vk_api.VkApi(token=token)
longpoll = VkLongPoll(vk)
vk_upload = vk_api.VkUpload(vk)

vk_user = VkAgent(config.vk_user_token)


def write_msg(user_id, message, keyboard=None):
    param = {'user_id': user_id,
             'message': message,
             'random_id': randrange(10 ** 7)}
    if keyboard is not None:
        param['keyboard'] = keyboard.get_keyboard()
    vk.method('messages.send', param)


def write_msg_with_photo(user_id, list_of_ids, owner_id):
    for i in list_of_ids:
        vk.method('messages.send', {'user_id': user_id, 'attachment': f"photo{owner_id}_{i}",
                                    'random_id': randrange(10 ** 7)})


search_params_all_user = {}
current_found_id = None


def main():
    create_table()
    try:
        for event in longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW:
                if event.to_me:
                    request = event.text.lower()

                    if request == 'начать' or request == 'привет':
                        if event.user_id in search_params_all_user:
                            continue
                        else:
                            search_params_all_user[event.user_id] = vk_user.get_default_param(event.user_id)

                        if search_params_all_user[event.user_id][0] == 0:
                            keyboard = VkKeyboard(inline=True)
                            keyboard.add_button('Параметры', color=VkKeyboardColor.PRIMARY)
                            keyboard.add_button('Искать', color=VkKeyboardColor.PRIMARY)
                            write_msg(event.user_id, 'Кажется у вас не указан пол, '
                                                     'для корректного поиска рекоммендуется изменить параметры.', keyboard)
                        if search_params_all_user[event.user_id][2] == 0:
                            keyboard = VkKeyboard(inline=True)
                            keyboard.add_button('Параметры', color=VkKeyboardColor.PRIMARY)
                            write_msg(event.user_id, 'Мы не смогли определить ваш возраст,'
                                                     ' для корректного поиска неоходимо изменить параметры.', keyboard)
                        else:
                            if vk_user.get_name(event.user_id):
                                write_msg(event.user_id, f'Привет, {vk_user.get_name(event.user_id)}')
                                write_msg(event.user_id, 'Поиск будет осуществлен на основании данных вашей анкеты.'
                                                         ' Изменить параметры поиска можно отпавив команду "Параметры"')
                                keyboard = VkKeyboard(inline=True)
                                keyboard.add_button('Искать', color=VkKeyboardColor.PRIMARY)
                                write_msg(event.user_id, 'Начнем искать пару?', keyboard)
                            else:
                                write_msg(event.user_id, 'Ой, кажется возникла проблема на стороне VK.'
                                                         ' Специалисты уже работают над ее устранением.')

                    elif request == 'искать' or request == 'дальше':
                        photo_param = vk_user.get_photo(search_params_all_user[event.user_id], event.user_id)
                        current_found_id = photo_param[0]
                        write_msg_with_photo(event.user_id, photo_param[1], photo_param[2])
                        keyboard = VkKeyboard(inline=True)
                        keyboard.add_button('В избранное', color=VkKeyboardColor.PRIMARY)
                        keyboard.add_button('Дальше', color=VkKeyboardColor.PRIMARY)
                        write_msg(event.user_id, f'{vk_user.get_name(photo_param[0])}  - vk.com/id{photo_param[0]}', keyboard)

                    elif request == 'в избранное':
                        set_favorite(current_found_id, event.user_id)
                        keyboard = VkKeyboard(inline=True)
                        keyboard.add_button('Дальше', color=VkKeyboardColor.PRIMARY)
                        write_msg(event.user_id, 'Пользователь добавлен в список "Избранные"', keyboard)

                    elif request == 'параметры':
                        keyboard = VkKeyboard(inline=True)
                        keyboard.add_button('1', color=VkKeyboardColor.PRIMARY)
                        keyboard.add_button('2', color=VkKeyboardColor.PRIMARY)
                        keyboard.add_button('3', color=VkKeyboardColor.PRIMARY)
                        keyboard.add_button('4', color=VkKeyboardColor.PRIMARY)
                        write_msg(event.user_id, 'Какой параметр меняем?\n1 - Пол\n2 - Статус\n3 - Возраст\n4 - Город', keyboard)
                        vk_user.clear_search_params(event.user_id)

                        for event in longpoll.listen():
                            if event.type == VkEventType.MESSAGE_NEW:
                                if event.to_me:
                                    request = event.text.lower()

                                    if request == '1':
                                        keyboard = VkKeyboard(inline=True)
                                        keyboard.add_button('Женщину', color=VkKeyboardColor.NEGATIVE)
                                        keyboard.add_button('Мужчину', color=VkKeyboardColor.PRIMARY)
                                        write_msg(event.user_id, 'Кого ищем?', keyboard)
                                        for event in longpoll.listen():
                                            if event.type == VkEventType.MESSAGE_NEW:
                                                if event.to_me:
                                                    request = event.text.lower()
                                                    if request == 'женщину':
                                                        search_params_all_user[event.user_id][0] = 1
                                                    else:
                                                        search_params_all_user[event.user_id][0] = 2
                                                    keyboard = VkKeyboard(inline=True)
                                                    keyboard.add_button('Искать', color=VkKeyboardColor.PRIMARY)
                                                    keyboard.add_button('Параметры', color=VkKeyboardColor.PRIMARY)
                                                    write_msg(event.user_id, 'Готово!\nИщем или еще меняем параметры?', keyboard)
                                                    break
                                        break

                                    if request == '2':
                                        keyboard = VkKeyboard(inline=True)
                                        keyboard.add_button('1', color=VkKeyboardColor.SECONDARY)
                                        keyboard.add_button('2', color=VkKeyboardColor.SECONDARY)
                                        keyboard.add_button('3', color=VkKeyboardColor.SECONDARY)
                                        keyboard.add_button('4', color=VkKeyboardColor.SECONDARY)
                                        write_msg(event.user_id, 'В каком статусе?')
                                        write_msg(event.user_id, 'Не женат (замужем) - 1\nВ активном поиске - 2\n'
                                                                 'Женат (Замужем) - 3\nВсе сложно - 4', keyboard)
                                        for event in longpoll.listen():
                                            if event.type == VkEventType.MESSAGE_NEW:
                                                if event.to_me:
                                                    request = event.text.lower()
                                                    if request == '1':
                                                        search_params_all_user[event.user_id][1] = 1
                                                    elif request == '2':
                                                        search_params_all_user[event.user_id][1] = 6
                                                    elif request == '3':
                                                        search_params_all_user[event.user_id][1] = 4
                                                    elif request == '4':
                                                        search_params_all_user[event.user_id][1] = 5
                                                    keyboard = VkKeyboard(inline=True)
                                                    keyboard.add_button('Искать', color=VkKeyboardColor.PRIMARY)
                                                    keyboard.add_button('Параметры', color=VkKeyboardColor.PRIMARY)
                                                    write_msg(event.user_id, 'Готово!\nИщем или еще меняем параметры?', keyboard)
                                                    break
                                        break

                                    if request == '3':
                                        write_msg(event.user_id, 'С какого возраста ищем?')
                                        for event in longpoll.listen():
                                            if event.type == VkEventType.MESSAGE_NEW:
                                                if event.to_me:
                                                    request = event.text.lower()
                                                    search_params_all_user[event.user_id][2] = request
                                                    keyboard = VkKeyboard(inline=True)
                                                    keyboard.add_button('Искать', color=VkKeyboardColor.PRIMARY)
                                                    keyboard.add_button('Параметры', color=VkKeyboardColor.PRIMARY)
                                                    write_msg(event.user_id, 'Готово!\nИщем или еще меняем параметры?', keyboard)
                                                    break
                                        break

                                    if request == '4':
                                        write_msg(event.user_id, 'Где ищем (населенный пункт)?')
                                        for event in longpoll.listen():
                                            if event.type == VkEventType.MESSAGE_NEW:
                                                if event.to_me:
                                                    request = event.text
                                                    search_params_all_user[event.user_id][3] = request
                                                    keyboard = VkKeyboard(inline=True)
                                                    keyboard.add_button('Искать', color=VkKeyboardColor.PRIMARY)
                                                    keyboard.add_button('Параметры', color=VkKeyboardColor.PRIMARY)
                                                    write_msg(event.user_id, 'Готово!\nИщем или еще меняем параметры?', keyboard)
                                                    break
                                        break

                    elif request == 'избранное':
                        user_list = show_favorite(event.user_id)
                        if len(user_list) < 1:
                            keyboard = VkKeyboard(inline=True)
                            keyboard.add_button('Искать', color=VkKeyboardColor.PRIMARY)
                            write_msg(event.user_id, 'Список "Избранное" пуст!\nДавай поскорее найдем кого-нибудь', keyboard)
                        else:
                            for user in user_list:
                                write_msg(event.user_id, f'{vk_user.get_name(user)}  - vk.com/id{user}')
                    elif request == 'пока':
                        write_msg(event.user_id, 'Пока((')
                    elif request == 'помощь' or request == 'help' or request == 'хелп':
                        write_msg(event.user_id, 'Комманды для бота:\n"Параметры" - установить параметры поиска.\n"Искать" -'
                                                 ' искать пару.\n"Избранное" - показать список избранных пользователей')
                    else:
                        write_msg(event.user_id, 'Не понял вашего ответа...')
    except requests.exceptions.RequestException:
        time.sleep(10)

if __name__ == '__main__':
    main()
