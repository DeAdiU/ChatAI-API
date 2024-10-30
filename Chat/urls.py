
from django.conf.urls import include
from .views import (SignupView, LoginView, ChatView, TokenBalanceView)
from django.urls import path, re_path
from drf_yasg.views import get_schema_view
from drf_yasg import openapi



schema_view = get_schema_view(
   openapi.Info(
      title="Chat API",  # API title
      default_version='v1',  # API version
      description="API documentation for the AI Chat API",  # API description
      contact=openapi.Contact(email="adityauttarwar29@gmail.com"),  # Support email for the API
      
   ),
   public=True,  # Public visibility
)


urlpatterns = [
    path('register/', SignupView.as_view(), name='register'),  # User registration
    path('login/', LoginView.as_view(), name='login'),  # User login
    path('chat/', ChatView.as_view(), name='chat'),  # Chat endpoint
    path('token-balance/', TokenBalanceView.as_view(), name='token-balance'),  # Token balance endpoint
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),  # Swagger UI for API documentation
]