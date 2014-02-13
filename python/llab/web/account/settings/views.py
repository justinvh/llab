from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

from llab.utils.request import post_or_none

from .forms import PublicKeyForm

@login_required
def settings_ssh(request):
    post_data = post_or_none(request)
    form = PublicKeyForm(post_data, prefix='public-key')
    if post_data and form.is_valid():
        form.save(user=request.user)
        return redirect('settings:ssh')
    template = 'settings/ssh.html'
    context = {'form': form, 'keys': request.user.public_keys.all()}
    return render(request, template, context)
