from . import views
from django.urls import path

urlpatterns = [
    path('', views.index, name='index'),
    path('buyer_login/', views.buyer_login, name='buyer_login'),
    path('buyer_signup/', views.buyer_signup, name='buyer_signup'),
    path('buyer/dashboard/', views.buyer_dashboard, name='buyer_dashboard'),
    path('seller_signup/', views.seller_signup, name='seller_signup'),
    path('seller_login/', views.seller_login, name='seller_login'),
    path('seller/dashboard/', views.seller_dashboard, name='seller_dashboard'),
    path('seller_logout/', views.seller_logout, name='seller_logout'),
    path('buyer_logout/', views.buyer_logout, name='buyer_logout'),
    path('seller/add_listing/', views.add_listing, name='add_listing'),
    path('all_listings/', views.all_listings, name='all_listings'),
    path('listing/<int:listing_id>/', views.listing_detail, name='listing_detail'),
    path("listing/<int:listing_id>/edit/", views.edit_listing, name="edit_listing"),
    path("listing/<int:listing_id>/delete/", views.delete_listing, name="delete_listing"),
    path('wishlist/add/<int:listing_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/<int:listing_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
    path('buy-request/<int:listing_id>/', views.make_buy_request, name='make_buy_request'),
    path('reject-buy-request/<int:request_id>/', views.reject_buy_request, name='reject_buy_request'),
    path('cancel-buy-request/<int:request_id>/', views.cancel_buy_request, name='cancel_buy_request'),
    path('accept-buy-request/<int:request_id>/', views.accept_buy_request, name='accept_buy_request'),
    path('chat/<int:buy_request_id>/', views.chat_room, name='chat_room'),
    path('confirm-order/<int:buy_request_id>/', views.confirm_order, name='confirm_order'),
]