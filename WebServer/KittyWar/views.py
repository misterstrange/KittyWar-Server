from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, HttpResponseBadRequest
from django.shortcuts import render
from django.contrib import auth
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
import json
from django.views.decorators.csrf import csrf_exempt

from .forms import RegistrationForm, LoginForm


# Index View - redirects to registration
def index_view(request):
    return HttpResponseRedirect('/kittywar/register/')


# Registration View
def register_view(request):

    if request.method == 'POST':

        form = RegistrationForm(request.POST)
        if form.is_valid():

            # Check if username already exist
            username = form.cleaned_data['username']
            if User.objects.filter(username=username).exists():

                # Warn user the username is already taken
                message = 'Username already exists'
                context = {'register_form': form, 'message': message}
                return render(request, 'register.html', context)

            # If everything is valid create user and redirect to login
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            User.objects.create_user(username, email, password)

            return HttpResponseRedirect('/kittywar/login/?s=Registration Successful')

        else:
            message = 'Passwords fields must match'
            context = {'register_form': form, 'message': message}
            return render(request, 'register.html', context)

    else:

        # If not POST then render blank form
        form = RegistrationForm()
        return render(request, 'register.html', {'register_form': form})

@csrf_exempt
def register_mobile_view(request):

    if request.method == 'POST':

        json_data = json.loads(request.body.decode('utf-8'))
        print(json_data)

        username = json_data['username']
        if User.objects.filter(username=username).exists():
            return JsonResponse(dict(status='409'))

        email = json_data['email']
        password = json_data['password']
        User.objects.create_user(username, email, password)

        return JsonResponse(dict(status='201'))

    else:
        return HttpResponseBadRequest("Bad Request - 409")


# Login View
def login_view(request):

    if request.method == 'POST':

        form = LoginForm(request.POST)
        if form.is_valid():

            # Authenticate user
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = auth.authenticate(username=username, password=password)

            if user is not None:

                auth.login(request, user)
                return HttpResponseRedirect('/kittywar/home/')
            else:
                message = 'Invalid username or password'
                context = {'login_form': form, 'message': message}
                return render(request, 'login.html', context)

    else:

        # If not POST then render blank form
        message = request.GET.get('s', '')
        form = LoginForm()
        context = {'login_form': form, 'message': message}
        return render(request, 'login.html', context)


# Home View
@login_required(login_url = '/kittywar/login/')
def home_view(request):
    return render(request, 'home.html')


# Logout View
def logout_view(request):

    auth.logout(request)
    return HttpResponseRedirect('/kittywar/login/')
