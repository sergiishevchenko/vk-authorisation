from django.forms import ModelForm
from vk_authorisation.models import Post

class AuthForm(ModelForm):
    class Meta:
        model = Post
        fields = ['login', 'password']
