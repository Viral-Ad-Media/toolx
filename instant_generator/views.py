from io import BytesIO

from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.contrib.sites.shortcuts import get_current_site
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from docx import Document
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate

from .forms import InstantGeneratorForm, ParaphraseForm, ProfileForm, SignUpForm, UserForm
from .models import InstantGenerator, Paraphrase, Profile
from .tokens import account_activation_token

User = get_user_model()


def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()

            current_site = get_current_site(request)
            subject = 'Activate Your Tool-X Account'
            message = render_to_string(
                'registration/activation_email.html',
                {
                    'user': user,
                    'domain': current_site.domain,
                    'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                    'token': account_activation_token.make_token(user),
                },
            )
            user.email_user(subject, message)
            return redirect('activation_sent')
    else:
        form = SignUpForm()

    return render(request, 'registration/signup.html', {'form': form})


def activation_sent(request):
    return render(request, 'registration/activation_sent.html', {})


def activate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is None or not account_activation_token.check_token(user, token):
        return render(request, 'registration/activation_invalid.html')

    user.is_active = True
    user.save(update_fields=['is_active'])
    Profile.objects.filter(user=user).update(email_confirmed=True)
    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
    return redirect('index')


@login_required
def profile(request):
    return render(request, 'registration/profile.html', {'user': request.user})


@login_required
@transaction.atomic
def edit_profile(request):
    profile_obj, _ = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        form = ProfileForm(request.POST, request.FILES, instance=profile_obj)
        if user_form.is_valid() and form.is_valid():
            user_form.save()
            form.save()
            messages.success(request, 'Your profile was successfully updated.')
            return redirect('profile')
        messages.error(request, 'Please correct the error below.')
    else:
        user_form = UserForm(instance=request.user)
        form = ProfileForm(instance=profile_obj)

    return render(
        request,
        'registration/edit_profile.html',
        {
            'user_form': user_form,
            'form': form,
        },
    )


@login_required
def dashboard(request):
    context = {
        'adcopies': InstantGenerator.objects.filter(user=request.user).order_by('-created_on'),
        'my_paraphrase': Paraphrase.objects.filter(user=request.user).order_by('-created_on'),
    }
    return render(request, 'instant_generator/dashboard.html', context)


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


@login_required
@transaction.atomic
def create_paraphrase(request):
    if request.method == 'POST':
        form = ParaphraseForm(request.POST)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.user = request.user
            instance.save()
            return redirect('congratulation')
    else:
        form = ParaphraseForm()

    return render(request, 'instant_generator/create_paraphrase.html', {'form': form})


@login_required
def congratulation(request):
    return render(request, 'instant_generator/congratulation.html', {})


@login_required
def paraphrase(request):
    my_paraphrase = Paraphrase.objects.filter(user=request.user).order_by('-created_on')
    return render(request, 'instant_generator/paraphrase.html', {'my_paraphrase': my_paraphrase})


@login_required
def my_adcopies(request):
    adcopies = InstantGenerator.objects.filter(user=request.user).order_by('-created_on')
    return render(request, 'instant_generator/my_adcopies.html', {'adcopies': adcopies})


@login_required
def preview(request, pk):
    generated = get_object_or_404(InstantGenerator, pk=pk, user=request.user)
    return render(request, 'instant_generator/preview.html', {'generated': generated})


@login_required
def paraphrase_preview(request, pk):
    original = get_object_or_404(Paraphrase, pk=pk, user=request.user)
    context = {
        'original': original,
        'generated': original,
    }
    return render(request, 'instant_generator/paraphrase_preview.html', context)


@login_required
def pdf(request, pk):
    generated = get_object_or_404(InstantGenerator, pk=pk, user=request.user)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="Sales Letter.pdf"'

    pdf_buffer = BytesIO()
    my_doc = SimpleDocTemplate(pdf_buffer)
    sample_style_sheet = getSampleStyleSheet()

    sections = [
        (generated.Get_Attention, 'Title'),
        (generated.Identify_the_Problem_Your_Audience_Have, 'BodyText'),
        (generated.Provide_the_Solution, 'BodyText'),
        (generated.Present_your_Credentials, 'BodyText'),
        (generated.Show_the_Benefits, 'BodyText'),
        (generated.Give_Social_Proof, 'BodyText'),
        (generated.Make_Your_Offer, 'Heading4'),
        (generated.Give_a_Guarantee, 'Italic'),
        (generated.Inject_Scarcity, 'BodyText'),
        (generated.Call_to_action, 'Heading3'),
        (generated.Give_a_Warning, 'BodyText'),
        (generated.Close_with_a_Reminder, 'Heading4'),
    ]
    my_doc.build([Paragraph(text, sample_style_sheet[style]) for text, style in sections])

    response.write(pdf_buffer.getvalue())
    pdf_buffer.close()
    return response


@login_required
def docx(request, pk):
    generated = get_object_or_404(InstantGenerator, pk=pk, user=request.user)
    document = Document()
    document.add_heading(generated.Get_Attention, 0)
    document.add_paragraph(generated.Identify_the_Problem_Your_Audience_Have)
    document.add_paragraph(generated.Provide_the_Solution)
    document.add_paragraph(generated.Present_your_Credentials)
    document.add_paragraph(generated.Show_the_Benefits)
    document.add_paragraph(generated.Give_Social_Proof)
    document.add_paragraph(generated.Make_Your_Offer, style='IntenseQuote')
    document.add_paragraph(generated.Give_a_Guarantee)
    document.add_paragraph(generated.Inject_Scarcity)
    document.add_paragraph(generated.Call_to_action)
    document.add_paragraph(generated.Give_a_Warning)
    document.add_paragraph().add_run(generated.Close_with_a_Reminder).bold = True

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    )
    response['Content-Disposition'] = 'attachment; filename="Sales Letter.docx"'
    document.save(response)
    return response

