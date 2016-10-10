from django.shortcuts import render
from django.http import HttpResponseRedirect

from .forms import RegistrationForm

# Index View - redirects to registration
def index(request):
    return HttpResponseRedirect('/KittyWar/register/')

# Registration View
def registration(request):

    if request.method == 'POST':

        form = RegistrationForm(request.POST)
        if form.is_valid():

            return HttpResponseRedirect('/KittyWar/login/?q=success');

    form = RegistrationForm()
    return render(request, 'register.html', {'register_form': form})

# Login View
def login(request):
    
    message = request.GET.get('q', '')
    return render(request, 'login.html', {'message': message})
    
    
