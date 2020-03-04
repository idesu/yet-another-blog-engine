from django.shortcuts import render
from django.shortcuts import redirect

# Create your views here.
# позволяет узнать ссылку на URL по его имени, параметр name функции path
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.core.mail import send_mail

from .forms import CreationForm


class SignUp(CreateView):
    form_class = CreationForm
    success_url = "/auth/login/"
    template_name = "signup.html"


    def form_valid(self, form):
        email = form.cleaned_data['email']
        send_mail('Подтверждение регистрации YABE', 'Вы зарегистрированы!',
                  'YABE.ru <admin@YABE.ru>', [email], fail_silently=False)
        return super().form_valid(form)
