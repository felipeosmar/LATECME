from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.contrib.auth.views import LoginView
from .models import CustomUser, UserRole
from .forms import CustomUserCreationForm, CustomLoginForm, UserProfileForm, CustomPasswordChangeForm


class CustomLoginView(LoginView):
    """View personalizada para login"""
    template_name = 'accounts/login.html'
    form_class = CustomLoginForm
    redirect_authenticated_user = True
    
    def form_valid(self, form):
        user = form.get_user()
        
        # Verificar se o usuário pode acessar o sistema
        if not user.can_access_system():
            if user.status == 'pending':
                messages.error(self.request, 'Sua conta ainda está aguardando aprovação.')
            elif user.status == 'rejected':
                messages.error(self.request, 'Sua conta foi rejeitada. Entre em contato com o administrador.')
            elif user.status == 'suspended':
                messages.error(self.request, 'Sua conta foi suspensa. Entre em contato com o administrador.')
            elif not user.role:
                messages.error(self.request, 'Nenhuma função foi atribuída à sua conta.')
            
            return self.form_invalid(form)
        
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('core:dashboard')


class RegisterView(CreateView):
    """View para registro de novos usuários"""
    model = CustomUser
    form_class = CustomUserCreationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('accounts:register_success')
    
    def form_valid(self, form):
        # O usuário é criado com status 'pending' por padrão
        response = super().form_valid(form)
        messages.success(
            self.request, 
            'Registro realizado com sucesso! Aguarde a aprovação do administrador para acessar o sistema.'
        )
        return response


def register_success(request):
    """Página de sucesso após registro"""
    return render(request, 'accounts/register_success.html')




def custom_logout_view(request):
    """View personalizada para logout que aceita GET e POST"""
    if request.user.is_authenticated:
        username = request.user.username
        logout(request)
        messages.success(request, f'Logout realizado com sucesso. Até logo, {username}!')
    else:
        messages.info(request, 'Você já estava desconectado.')
    
    # Redirecionar para login sempre
    return redirect('accounts:login')


@login_required
def profile(request):
    """Perfil do usuário"""
    return render(request, 'accounts/profile.html', {'user': request.user})


@login_required
def edit_profile(request):
    """Editar perfil do usuário"""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil atualizado com sucesso!')
            return redirect('accounts:profile')
        else:
            messages.error(request, 'Por favor, corrija os erros abaixo.')
    else:
        form = UserProfileForm(instance=request.user)
    
    context = {
        'form': form,
        'user': request.user,
    }
    return render(request, 'accounts/edit_profile.html', context)


@login_required
def change_password(request):
    """Alterar senha do usuário"""
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Manter o usuário logado após alterar a senha
            update_session_auth_hash(request, user)
            messages.success(request, 'Sua senha foi alterada com sucesso!')
            return redirect('accounts:profile')
        else:
            messages.error(request, 'Por favor, corrija os erros abaixo.')
    else:
        form = CustomPasswordChangeForm(request.user)
    
    context = {
        'form': form,
        'user': request.user,
    }
    return render(request, 'accounts/change_password.html', context)