from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib import auth
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required


from .forms import RegistrationForm, LoginForm

### Index View - redirects to registration
def index_view(request):
    return HttpResponseRedirect('/Kittywar/register/')

### Registration View
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

            return HttpResponseRedirect('/Kittywar/login/?q=Registration Successful')

        else:
            message = 'Passwords fields must match'
            context = {'register_form': form, 'message': message}
            return render(request, 'register.html', context)
    
    else:

        # If not POST then render blank form        
        form = RegistrationForm()
        return render(request, 'register.html', {'register_form': form})

### Login View
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
                return HttpResponseRedirect('/Kittywar/home/')
            else:
                message = 'Invalid username or password'
                context = {'login_form': form, 'message': message}
                return render(request, 'login.html', context)
    
    else:

        # If not POST then render blank form
        message = request.GET.get('q', '')
        form = LoginForm()
        context = {'login_form': form, 'message': message}
        return render(request, 'login.html', context)

### Home View
@login_required(login_url = '/Kittywar/login/')
def home_view(request):
    return render(request, 'home.html')

### Logout View
def logout_view(request):

    auth.logout(request)
    return HttpResponseRedirect('/Kittywar/login/')
