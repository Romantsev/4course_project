from django.http import HttpResponseForbidden

from .views import storage_list as _storage_list_impl
from .views import storage_edit as _storage_edit_impl
from .views import storage_delete as _storage_delete_impl
from .maintenance_views import _has_technician_access


def storage_list(request):
    if _has_technician_access(request.user):
        return HttpResponseForbidden("Недостатньо прав доступу.")
    return _storage_list_impl(request)


def storage_edit(request, pk):
    if _has_technician_access(request.user):
        return HttpResponseForbidden("Недостатньо прав доступу.")
    return _storage_edit_impl(request, pk)


def storage_delete(request, pk):
    if _has_technician_access(request.user):
        return HttpResponseForbidden("Недостатньо прав доступу.")
    return _storage_delete_impl(request, pk)

