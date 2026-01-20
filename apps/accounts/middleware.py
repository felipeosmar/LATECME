from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from django.utils.deprecation import MiddlewareMixin


class UserApprovalMiddleware(MiddlewareMixin):
    """
    Middleware para verificar se o usuário tem aprovação para acessar o sistema
    """
    
    # URLs que não precisam de verificação de aprovação
    EXEMPT_URLS = [
        '/',
        '/accounts/login/',
        '/accounts/logout/',
        '/accounts/register/',
        '/accounts/register/success/',
        '/admin/',
        '/static/',
        '/media/',
    ]
    
    def process_request(self, request):
        # Não verificar se o usuário não está autenticado
        if not request.user.is_authenticated:
            return None
        
        # Não verificar para URLs isentas
        if any(request.path.startswith(url) for url in self.EXEMPT_URLS):
            return None
        
        # Não verificar para superusuários
        if request.user.is_superuser:
            return None
        
        # Verificar se o usuário pode acessar o sistema
        if hasattr(request.user, 'can_access_system') and not request.user.can_access_system():
            # Evitar loop de redirecionamento: não redirecionar se já está na página de login
            if request.path == '/accounts/login/':
                return None

            if request.user.status == 'pending':
                messages.warning(request, 'Sua conta ainda está aguardando aprovação.')
            elif request.user.status == 'rejected':
                messages.error(request, 'Sua conta foi rejeitada. Entre em contato com o administrador.')
            elif request.user.status == 'suspended':
                messages.error(request, 'Sua conta foi suspensa. Entre em contato com o administrador.')
            elif not request.user.role:
                messages.warning(request, 'Nenhuma função foi atribuída à sua conta.')

            return redirect('accounts:login')

        return None