from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages


@login_required
def dashboard(request):
    """Dashboard principal - verificação adicional de acesso"""
    if not request.user.can_access_system():
        messages.error(request, 'Você não tem permissão para acessar o sistema.')
        return redirect('accounts:login')
    
    context = {
        'user': request.user,
        'permissions': request.user.get_permissions() if hasattr(request.user, 'get_permissions') else [],
    }
    return render(request, 'dashboard/index.html', context)