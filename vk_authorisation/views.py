from vk_authorisation.module import VKAuth
from config import APP_ID
from django.shortcuts import render


def authorisation(request):
    vk = VKAuth(['friends'], APP_ID, '5.122')
    vk.auth()

    # token = vk.get_token()
    # user_id = vk.get_user_id()
    return render(request, 'authorisation.html')


def user_page(request):
    return render(request, 'user_page.html')
