from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required

from llab.utils.request import post_or_none

from .forms import UserForm

def account_join(request):
    post_data = post_or_none(request)
    form = UserForm(post_data, prefix='user')
    if post_data and form.is_valid():
        form.save()
        username = form.cleaned_data['username']
        password = form.cleaned_data['password1']
        user = authenticate(username=username, password=password)
        login(request, user)
        return redirect('project:index')
    template = 'account/join.html'
    context = {'form': form}
    return render(request, template, context)


@login_required
def account_settings_ssh(request):
    post_data = post_or_none(request)
    form = PublicKeyForm(post_data, prefix='public-key')
    if post_data and form.is_valid():
        form.save(user=request.user)
        return redirect('account:account_keys')
    template = 'account/settings/ssh.html'
    context = {'form': form, 'keys': request.user.public_keys.all()}
    return render(request, template, context)
