from django.urls import path
from . import views

urlpatterns = [
    path('signup/', views.signup, name='signup'),
    path('profile/', views.profile, name='profile'),
    path('profile/edit', views.edit_profile, name='edit-profile'),
    path('activation_sent/', views.activation_sent, name='activation_sent'),
    path('activate/<uidb64>/<token>/', views.activate, name='activate'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('create/', views.create, name='create'),
    path('congratulation/', views.congratulation, name='congratulation'),
    path('my_adcopies', views.my_adcopies, name='my_adcopies'),
    path('preview/<int:pk>', views.preview, name='preview'),
]
