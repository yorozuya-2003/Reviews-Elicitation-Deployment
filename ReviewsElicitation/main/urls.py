from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

app_name = 'main'

urlpatterns = [
    path('', views.login_view, name='login'),
    path('signup/', views.signup_view,  name='signup'),
    path('home/', views.home_view, name='home'),
    path('verify/', views.verify_view, name='verify'),
    path('logout/', views.logout_view, name='logout'),
    path('update/', views.update_view, name='update'),
    path('search/', views.search_view, name='search'),
    path('user/<str:username>/', views.user_view, name='user'),
    path('edit/<int:review_id>/', views.edit_view, name='edit'),
    path('delete/<int:review_id>/', views.delete_view, name='delete'),


] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)