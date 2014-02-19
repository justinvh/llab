from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

from llab.utils.request import post_or_none

from .forms import PublicKeyForm, ProfileForm


@login_required
def settings_profile(request):
    user = request.user
    post_data = post_or_none(request)
    form = ProfileForm(post_data, instance=user.profile, prefix='profile')
    if post_data and form.is_valid():
        form.save()
        return redirect('account:settings:profile')
    template = 'settings/profile.html'
    context = {'form': form}
    return render(request, template, context)


@login_required
def settings_ssh(request):
    post_data = post_or_none(request)
    form = PublicKeyForm(post_data, prefix='public-key')
    if post_data and form.is_valid():
        form.save(user=request.user)
        return redirect('account:settings:ssh')
    template = 'settings/ssh.html'
    context = {'form': form, 'keys': request.user.public_keys.all()}
    return render(request, template, context)
