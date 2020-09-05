import vk_api

login = input("Введите логин:")
password = input("Введите пароль:")

vk_session = vk_api.VkApi('login', 'password')

vk_session.auth()

vk = vk_session.get_api()

print(vk)
