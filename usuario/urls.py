# urls.py
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    RegisterView, MyTokenObtainPairView, LogoutView, 
    UserProfileView, UserListView, UserDetailView, UserUpdateView, UserDeleteView
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', MyTokenObtainPairView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/', UserProfileView.as_view(), name='profile'),
    # Gestión de usuarios (CRUD)
    path('users/', UserListView.as_view(), name='user-list'),           # Listar todos
    path('users/<int:pk>/update/', UserUpdateView.as_view(), name='user-update'), # Actualizar
    path('users/<int:pk>/delete/', UserDeleteView.as_view(), name='user-delete'), # Eliminar
]