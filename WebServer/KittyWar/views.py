from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate

from .forms import RegistrationForm

# Index View - redirects to registration
def index(request):
    return HttpResponseRedirect('/KittyWar/register/')

# Registration View
def registration(request):

    if request.method == 'POST':

        form = RegistrationForm(request.POST)
        if form.is_valid():

            # Check if username already exist
            username = form.cleaned_data['username']
            if User.objects.filter(username=username).exists():

                # Warn user the username is already taken
                message = 'Username already exists'
                return render(request, 'register.html', {'register_form': form, 'message': message})

            # If everything is valid create user and redirect to login
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            User.objects.create_user(username, email, password)

            return HttpResponseRedirect('/KittyWar/login/?q=success')

        else:
            message = 'Passwords fields must match'
            return render(request, 'register.html', {'register_form': form, 'message': message})
            
    form = RegistrationForm()
    return render(request, 'register.html', {'register_form': form})

# Login View
def login(request):
    
    message = request.GET.get('q', '')
    return render(request, 'login.html', {'message': message})
