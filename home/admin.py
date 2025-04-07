from django.contrib import admin
from .models import *

admin.site.register(Seller)
admin.site.register(Listing)
admin.site.register(ListingImage)
admin.site.register(BuyRequest)
admin.site.register(Order)
admin.site.register(Message)
admin.site.register(Donation)