from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import add_expense, list_expenses

urlpatterns = [
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('add-expense/', add_expense, name='add-expense'),
    path('list-expenses/', list_expenses, name='list-expenses'),
]