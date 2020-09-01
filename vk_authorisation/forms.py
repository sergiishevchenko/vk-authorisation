from django.forms import ModelForm
from test_project.models import Post

class AuthForm(ModelForm):
    class Meta:
        model = Post
        fields = ['login', 'password']
