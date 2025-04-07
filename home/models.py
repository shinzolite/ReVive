from django.contrib.auth.models import User
from django.db import models
from django.conf import settings

class Seller(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='seller')
    phone_number = models.CharField(max_length=15, unique=True, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    is_neighborhood_verified = models.BooleanField(default=False)
    
    profile_image = models.ImageField(upload_to='sellers/profile_images/', null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    instagram_link = models.URLField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.user.username
    
class ItemCondition(models.TextChoices):
    NEW = 'New', 'New'
    LIKE_NEW = 'Like New', 'Like New'
    USED = 'Used', 'Used'
    REFURBISHED = 'Refurbished', 'Refurbished'

class Category(models.TextChoices):
    MOBILE = 'Mobile', 'Mobile'
    LAPTOP = 'Laptop', 'Laptop'
    VEHICLE = 'Vehicle', 'Vehicle'
    OTHER = 'Other', 'Other'

class Listing(models.Model):
    CATEGORY_CHOICES = [
        ('Mobile', 'Mobile'),
        ('Laptop', 'Laptop'),
        ('Vehicle', 'Vehicle'),
        ('Other', 'Other'),
    ]

    CONDITION_CHOICES = [
        ('new', 'New'),
        ('used', 'Used'),
        ('refurbished', 'Refurbished'),
    ]

    seller = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(
        max_length=50, choices=Category.choices, default=Category.MOBILE
    )
    condition = models.CharField(
        max_length=50, choices=ItemCondition.choices, default=ItemCondition.USED
    )

    # Primary image for the listing
    images = models.ImageField(upload_to='listings/%Y/%m/%d/', blank=True, null=True)
    # Many-to-many relationship for additional images
    additional_images = models.ManyToManyField(
        'ListingImage', related_name='additional_listings', blank=True
    )

    location = models.CharField(max_length=255)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    is_available = models.BooleanField(default=True)
    year = models.IntegerField(null=True, blank=True)
    brand = models.CharField(max_length=100, blank=True, null=True)
    model = models.CharField(max_length=100, blank=True, null=True)
    contact_number = models.CharField(max_length=15, null=True, blank=True)
    shipping_available = models.BooleanField(default=False)
    negotiable = models.BooleanField(default=False)

    other_details = models.JSONField(default=dict, blank=True, null=True)

    def __str__(self):
        return self.title

class ListingImage(models.Model):
    listing = models.ForeignKey(Listing, related_name='listing_images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='listing_images/')

    def __str__(self):
        return f"Image for {self.listing.title}"


class Buyer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='buyer')
    phone_number = models.CharField(max_length=15, unique=True, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    profile_image = models.ImageField(upload_to='buyers/profile_images/', null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.user.username
    
class Wishlist(models.Model):
    buyer = models.ForeignKey(Buyer, on_delete=models.CASCADE, related_name='wishlist_items')
    listing = models.ForeignKey('Listing', on_delete=models.CASCADE, related_name='wishlisted_by')
    added_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('buyer', 'listing')
        ordering = ['-added_on']

    def __str__(self):
        return f"{self.buyer.user.username} - {self.listing.title}"


class BuyRequest(models.Model):
    class NegotiationStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        ACCEPTED = 'accepted', 'Accepted'
        REJECTED = 'rejected', 'Rejected'
        COUNTER = 'counter', 'Counter Offer'
        COMPLETED = 'completed', 'Completed'
        
    buyer = models.ForeignKey(User, on_delete=models.CASCADE)
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE)
    proposed_price = models.DecimalField(max_digits=10, decimal_places=2)
    message = models.TextField(blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=NegotiationStatus.choices,
        default=NegotiationStatus.PENDING
    )
    counter_offer = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.buyer.username} - {self.listing.title} ({self.get_status_display()})"

class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    buy_request = models.ForeignKey(BuyRequest, on_delete=models.CASCADE, related_name='messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"Message from {self.sender} to {self.receiver} at {self.timestamp}"

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending_payment', 'Pending Payment'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ]
    
    buy_request = models.OneToOneField(BuyRequest, on_delete=models.CASCADE, related_name='order')
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='buyer_orders')
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='seller_orders')
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending_payment')
    final_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.id} - {self.listing.title}"

class Donation(models.Model):
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('donated', 'Donated'),
        ('cancelled', 'Cancelled')
    ]

    seller = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(
        max_length=50, choices=Category.choices, default=Category.OTHER
    )
    condition = models.CharField(
        max_length=50, choices=ItemCondition.choices, default=ItemCondition.USED
    )

    # Primary image for the donation
    images = models.ImageField(upload_to='donations/%Y/%m/%d/', blank=True, null=True)
    # Additional images
    additional_images = models.ManyToManyField(
        'DonationImage', related_name='additional_donations', blank=True
    )

    location = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    year = models.IntegerField(null=True, blank=True)
    brand = models.CharField(max_length=100, blank=True, null=True)
    model = models.CharField(max_length=100, blank=True, null=True)
    contact_number = models.CharField(max_length=15, null=True, blank=True)

    def __str__(self):
        return f"{self.title} - {self.get_status_display()}"

class DonationImage(models.Model):
    donation = models.ForeignKey(Donation, related_name='donation_images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='donation_images/')

    def __str__(self):
        return f"Image for {self.donation.title}"
