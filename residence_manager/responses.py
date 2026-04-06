from django.shortcuts import render


def forbidden_response(request):
    return render(request, 'forbidden.html', status=403)


def forbidden_view(request, exception=None):
    return forbidden_response(request)
