from django.urls import path
from . import views
from . import account_actions as actions

app_name = 'accounts'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('complex-admin/create/', views.create_complex_admin, name='create_complex_admin'),
    path('complex-admin/<int:pk>/edit/', actions.edit_complex_admin, name='edit_complex_admin'),
    path('complex-admin/<int:pk>/delete/', actions.delete_complex_admin, name='delete_complex_admin'),
    path('owner/create/', views.create_owner_account, name='create_owner_account'),
    path('owner/<int:pk>/edit/', actions.edit_owner_account, name='edit_owner_account'),
    path('owner/<int:pk>/delete/', actions.delete_owner_account, name='delete_owner_account'),
    path('staff/create/', views.create_staff_account, name='create_staff_account'),
    path('staff/<int:pk>/edit/', actions.edit_staff_account, name='edit_staff_account'),
    path('staff/<int:pk>/delete/', actions.delete_staff_account, name='delete_staff_account'),
]
