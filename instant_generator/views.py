from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth import login, authenticate
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib import messages
from django.template.loader import render_to_string
from .models import User, InstantGenerator
from .forms import UserForm, ProfileForm, InstantGeneratorForm
from .tokens import account_activation_token
from django.db import transaction

from io import BytesIO
from reportlab.pdfgen import canvas
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.pagesizes import A4


# Create your views here.
def signup(request):
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.is_active = True
            user.save()
            current_site = get_current_site(request)
            subject = 'Activate Your Tool-X Account'
            message = render_to_string('registration/activation_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': account_activation_token.make_token(user),
            })
            user.email_user(subject, message)
            return redirect('activation_sent')

    else:
        form = UserForm()

    return render(request, 'registration/signup.html', {'form': form})


def activation_sent(request):

    return render(request, 'registration/activation_sent.html', {})


def activate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.email_confirmed = True
        user.save()
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        return redirect('index')
    else:
        return render(request, 'registration/activation_invalid.html')


def profile(request):

    return render(request, 'registration/profile.html', {'user': request.user})


@transaction.atomic
def edit_profile(request):
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        form = ProfileForm(request.POST, instance=request.user)
        if user_form.is_valid() and form.is_valid():
            user_form.save()
            form.save()
            messages.success(request, 'Your profile was successfully updated!')
            return redirect('profile')

        else:
            messages.error(request, 'Please correct the error below.')

    else:
        user_form = UserForm(instance=request.user)
        form = ProfileForm(instance=request.user)

    return render(request, 'registration/edit_profile.html', {
        'user_form': user_form,
        'form': form
    })


def dashboard(request):

    return render(request, 'instant_generator/dashboard.html', {})


@login_required
@transaction.atomic
def create(request):
    if request.method == 'POST':
        form = InstantGeneratorForm(request.POST)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.user = request.user
            instance.save()
            return redirect('congratulation')

    else:
        form = InstantGeneratorForm()

    return render(request, 'instant_generator/create.html', {'form': form})


def congratulation(request):

    return render(request, 'instant_generator/congratulation.html', {})


def my_adcopies(request):
    adcopies = InstantGenerator.objects.all().order_by('-created_on')
    context = {
        "adcopies": adcopies,
    }

    return render(request, 'instant_generator/my_adcopies.html', context)


def preview(request, pk):
    generated = InstantGenerator.objects.get(pk=pk)

    return render(request, 'instant_generator/preview.html', {'generated': generated})


# def download(request):
#
#     return render(request, 'instant_generator/download.html', {})


def download(request):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="mypdf.pdf"'

    buffer = BytesIO()
    p = canvas.Canvas(buffer)

    # Start writing the PDF here
    p.drawString(100, 100, 'Hello world.')
    # End writing

    p.showPage()
    p.save()

    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)

    return response
