from django.shortcuts import render


# Create your views here.
def index(request):

    return render(request, 'index.html', {})


def features(request):

    return render(request, 'features.html', {})


def pricing(request):

    return render(request, 'pricing.html', {})


def welcome(request):

    return render(request, 'registration/welcome.html')
