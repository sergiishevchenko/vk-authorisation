import vk_api

login = input("Введите логин: ")
password = input("Введите пароль: ")

vk_session = vk_api.VkApi(login, password)

vk_session.auth()

vk = vk_session.get_api()

def get_friends(user_id):
    list_of_friends = vk.friends.get(user_id=user_id, count=5, order='random', fields='first_name')['items']

    for friend in list_of_friends:
        print(friend['first_name'] + ' ' + friend['last_name'])

def main():

    friends = get_friends(0)


if __name__ == "__main__":
    main()
