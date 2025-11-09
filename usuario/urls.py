# urls.py
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [

    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.MyTokenObtainPairView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('profile/', views.UserProfileView.as_view(), name='profile'),
    
    # Gestión de usuarios (CRUD)
    path('users/', views.UserListView.as_view(), name='user-list'),           # Listar todos
    path('profile/update/', views.UserUpdateView.as_view(), name='user-update'), # Actualizar perfil
    path('users/<int:pk>/delete/', views.UserDeleteView.as_view(), name='user-delete'), # Eliminar
    path('users/update/<int:id>', views.EditarUsuarioView.as_view(), name='user-update'), # Actualizar
    
    # --------------------------
    # PRIVILEGIO 
    # --------------------------
    path('asignar_privilegio', views.asignar_privilegio, name='asignar_privilegio'), 
    path('editar_privilegio/<int:privilegio_id>', views.editar_privilegio, name='editar_privilegio'), 
    path('eliminar_privilegio/<int:privilegio_id>', views.eliminar_privilegio, name='eliminar_privilegio'), 
    path('listar_privilegios', views.listar_privilegios, name='listar_privilegios'), 
    path('asignar_privilegios_grupo', views.asignar_privilegios_grupo, name='asignar_privilegios_grupo'),
    
    # --------------------------
    # GRUPO
    # --------------------------
    path('listar_grupos', views.listar_grupos, name='listar_grupos'), 
    path('crear_grupo', views.crear_grupo, name='crear_grupo'), 
    path('editar_grupo/<int:grupo_id>', views.editar_grupo, name='editar_grupo'), 
    path('eliminar_grupo/<int:grupo_id>', views.eliminar_grupo, name='eliminar_grupo'), 
    path('activar_grupo/<int:grupo_id>', views.activar_grupo, name='activar_grupo'), 
    path('asignar_grupo_usuario', views.asignar_grupo_usuario, name='asignar_grupo_usuario'), #PROBADO
    # --------------------------
    # COMPONENTE    
    # --------------------------
    path('crear_componente', views.crear_componente, name='crear_componente'), 
    path('editar_componente/<int:componente_id>', views.editar_componente, name='editar_componente'), 
    path('listar_componentes', views.listar_componentes, name='listar_componentes'), 
    path('eliminar_componente/<int:componente_id>', views.eliminar_componente, name='eliminar_componente'), 
    path('activar_componente/<int:componente_id>', views.activar_componente, name='activar_componente'), 
]