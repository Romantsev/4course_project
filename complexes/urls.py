from django.urls import path
from . import views
from . import people_views
from . import parking_views
from . import maintenance_views
from . import access_views
from . import visitors_override

urlpatterns = [
    path('', views.complex_list, name='complex_list'),
    path('complex/<int:pk>/', views.complex_detail, name='complex_detail'),
    path('complex/<int:pk>/edit/', views.complex_edit, name='complex_edit'),
    path('complex/<int:pk>/delete/', views.complex_delete, name='complex_delete'),

    # Будинки
    path('complex/<int:complex_pk>/building/add/', views.building_add, name='building_add'),
    path('building/<int:pk>/edit/', views.building_edit, name='building_edit'),
    path('building/<int:pk>/delete/', views.building_delete, name='building_delete'),

    # Під'їзди
    path('complex/<int:complex_pk>/building/<int:building_id>/entrance/add/', views.entrance_add, name='entrance_add'),
    path('entrance/<int:pk>/edit/', views.entrance_edit, name='entrance_edit'),
    path('entrance/<int:pk>/delete/', views.entrance_delete, name='entrance_delete'),

    # Квартири
    path('complex/<int:complex_pk>/entrance/<int:entrance_id>/apartment/add/', views.entrance_add_apartment, name='apartment_add'),
    path('apartment/<int:pk>/edit/', views.apartment_edit, name='apartment_edit'),
    path('apartment/<int:pk>/delete/', views.apartment_delete, name='apartment_delete'),

    # Довідкові списки (для супер адміна)
    path('owners/', people_views.owners_list, name='owners_list'),
    path('residents/', people_views.residents_list, name='residents_list'),
    path('staff/', people_views.staff_list, name='staff_list'),
    path('parking/', parking_views.parking_list, name='parking_list'),
    path('parking_zone/<int:pk>/edit/', parking_views.parking_zone_edit, name='parking_zone_edit'),
    path('parking_zone/<int:pk>/delete/', parking_views.parking_zone_delete, name='parking_zone_delete'),
    path('parking_spot/<int:pk>/edit/', parking_views.parking_spot_edit, name='parking_spot_edit'),
    path('parking_spot/<int:pk>/delete/', parking_views.parking_spot_delete, name='parking_spot_delete'),

    # Власники
    # Owners
    path('owner/<int:pk>/edit/', views.owner_edit, name='owner_edit'),
    path('owner/<int:pk>/delete/', views.owner_delete, name='owner_delete'),

    # Жильці/персонал: редагування/видалення
    path('resident/<int:pk>/edit/', people_views.resident_edit, name='resident_edit'),
    path('resident/<int:pk>/delete/', people_views.resident_delete, name='resident_delete'),
    path('staff/<int:pk>/edit/', people_views.staff_edit, name='staff_edit'),
    path('staff/<int:pk>/delete/', people_views.staff_delete, name='staff_delete'),

     # Комірки
    path('storage/', views.storage_list, name='storage_list'), 
    path('storage/<int:pk>/edit/', views.storage_edit, name='storage_edit'),
    path('storage/<int:pk>/delete/', views.storage_delete, name='storage_delete'),   

    # Заявки на ремонт
    path('tickets/owner/', maintenance_views.tickets_owner_list, name='tickets_owner_list'),
    path('tickets/owner/create/', maintenance_views.ticket_create, name='ticket_create'),
    path('tickets/staff/', maintenance_views.tickets_staff_list, name='tickets_staff_list'),
    path('tickets/<int:pk>/take/', maintenance_views.ticket_take, name='ticket_take'),
    path('tickets/<int:pk>/done/', maintenance_views.ticket_done, name='ticket_done'),
    path('tickets/<int:pk>/delete/', maintenance_views.ticket_delete, name='ticket_delete'),

    # Відвідувачі (охорона)
    path('visitors/', visitors_override.visitors_list, name='visitors_list'),
    path('residents/quick-add/', access_views.resident_quick_add, name='resident_quick_add'),
    path('visitor/<int:pk>/delete/', access_views.visitor_delete, name='visitor_delete'),
]
