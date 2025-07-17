from django.urls import path
from . import views

urlpatterns = [
    path('wallets/', views.WalletListView.as_view(), name='wallet-list'),
    path('wallets/<int:pk>/', views.WalletDetailView.as_view(), name='wallet-detail'),
    path('transactions/', views.WalletTransactionListView.as_view(), name='wallet-transaction-list'),
    path('add-to-wallet/', views.add_to_wallet, name='add-to-wallet'),
    path('debit-from-wallet/', views.debit_from_wallet, name='debit-from-wallet'),
    path('set-margin/', views.set_user_margin, name='set-user-margin'),
    path('margins/', views.UserMarginListView.as_view(), name='user-margin-list'),
]