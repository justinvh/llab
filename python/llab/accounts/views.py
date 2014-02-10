from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate

from utils.request import post_or_none
from .forms import UserCreationForm


def accounts_register(request):
    post_data = post_or_none(request)
    form = UserCreationForm(post_data)
    if post_data and form.is_valid():
        form.save()
        username = form.cleaned_data['username']
        password = form.cleaned_data['password1']
        user = authenticate(username=username, password=password)
        login(request, user)
        return redirect('project:index')
    template = 'accounts/register.html'
    context = {'form': form}
    return render(request, template, context)
