from django.shortcuts import render, HttpResponse, redirect, get_object_or_404
from . models import *
from . forms import *
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from decimal import Decimal
import os
from .utils import generate_chat_hash
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect, csrf_exempt

# Create your views here.
def index(request):
    return render(request, 'index.html')

def buyer_login(request):
    if request.user.is_authenticated and hasattr(request.user, 'buyer'):
        return redirect('buyer_dashboard')

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("buyer_dashboard")  
        else:
            messages.error(request, "Invalid username or password.")

    return render(request, "buyer_login.html")


def buyer_signup(request):
    if request.user.is_authenticated:
        return redirect('buyer_dashboard')  # Redirect to the dashboard if already logged in

    if request.method == "POST":
        # Get data from the form submission
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        phone_number = request.POST.get("phone_number")
        address = request.POST.get("address")
        date_of_birth = request.POST.get("date_of_birth")  # Format should match (YYYY-MM-DD)
        profile_image = request.FILES.get("profile_image")  # Optional

        user = User.objects.create_user(username=username, email=email, password=password)
        buyer = Buyer.objects.create(
            user=user,
            phone_number=phone_number,
            address=address,
            date_of_birth=date_of_birth,
            profile_image=profile_image,
        )

        return redirect("buyer_login")  

    return render(request, 'buyer_signup.html')

@login_required
def buyer_dashboard(request):
    if request.user.is_authenticated and request.user.buyer:
        print(f"Authenticated User: {request.user.username}")

    
    wishlist_items = Wishlist.objects.filter(buyer=request.user.buyer)
    buy_requests = BuyRequest.objects.filter(buyer=request.user)
    orders = Order.objects.filter(buyer=request.user).order_by('-created_at')
    
    context = {
        'wishlist_items': wishlist_items,
        'buy_requests': buy_requests,
        'orders': orders
    }
    return render(request, 'buyer_dashboard.html', context)

@login_required
def add_to_wishlist(request, listing_id):
    try:
        buyer = request.user.buyer
    except AttributeError:
        messages.error(request, "You must be a buyer to add items to your wishlist.")
        return redirect('buyer_signup')  
    listing = get_object_or_404(Listing, id=listing_id)

    wishlist_item, created = Wishlist.objects.get_or_create(buyer=buyer, listing=listing)
    if created:
        messages.success(request, "Listing added to your wishlist!")
    else:
        messages.info(request, "This listing is already in your wishlist.")

    return redirect('listing_detail', listing_id=listing.id)


@login_required
def remove_from_wishlist(request, listing_id):
    try:
        buyer = request.user.buyer
    except AttributeError:
        messages.error(request, "You must be a buyer to remove items from your wishlist.")
        return redirect("buyer_login") 

    wishlist_item = get_object_or_404(Wishlist, buyer=buyer, listing__id=listing_id)

    wishlist_item.delete()

    messages.success(request, "Item removed from your wishlist.")

    return redirect("buyer_dashboard") 


@login_required
def make_buy_request(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id)

    # Ensure the logged-in user is the buyer
    if request.user == listing.seller:
        messages.error(request, "You cannot make an offer on your own listing.")
        return redirect('listing_detail', listing_id=listing.id)

    if request.method == "POST":
        proposed_price = request.POST.get("proposed_price")
        message = request.POST.get("message", "")

        if not proposed_price:
            messages.error(request, "Please enter a valid price.")
            return redirect('listing_detail', listing_id=listing.id)

        # Create a new BuyRequest
        BuyRequest.objects.create(
            buyer=request.user,
            listing=listing,
            proposed_price=proposed_price,
            message=message
        )

        messages.success(request, "Your buy request has been sent to the seller!")
        return redirect('listing_detail', listing_id=listing.id)

    return redirect('listing_detail', listing_id=listing.id)

def seller_signup(request):
    if request.method == 'POST':
        form = SellerSignupForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Account created successfully! Please login.')
            return redirect('seller_login')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = SellerSignupForm()
    
    return render(request, 'seller_signup.html', {'form': form})

def seller_login(request):
    if request.user.is_authenticated:
        try:
            seller = request.user.seller  
            return redirect('seller_dashboard') 
        except Seller.DoesNotExist:
            pass 

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Authenticate user
        user = authenticate(request, username=username, password=password)
        if user is not None:
            # Log the user in
            login(request, user)

            # Check if the user is a seller and redirect accordingly
            try:
                seller = user.seller 
                return redirect('seller_dashboard')
            except Seller.DoesNotExist:
                # If the user is not a seller, redirect to another page
                return redirect('seller_login')  
        else:
            messages.error(request, 'Invalid username or password')

    return render(request, 'seller_login.html')

@login_required
def seller_dashboard(request):
    if not hasattr(request.user, 'seller'):
        return redirect('seller_login')
    
    seller = request.user.seller
    listings = Listing.objects.filter(seller=request.user)
    offers = BuyRequest.objects.filter(listing__seller=request.user)
    orders = Order.objects.filter(seller=request.user).order_by('-created_at')
    donations = Donation.objects.filter(seller=request.user).order_by('-created_at')  # Fetch donations

    context = {
        'seller': seller,
        'listings': listings,
        'offers': offers,
        'orders': orders,
        'donations': donations,  # Pass donations to the context
    }
    return render(request, 'seller_dashboard.html', context)


def seller_logout(request):
    logout(request)
    return redirect('seller_login')

def buyer_logout(request):
    logout(request)
    return redirect('buyer_login')

@login_required
def add_listing(request):
    if request.method == "POST":
        # Get data from the form
        title = request.POST.get("title")
        description = request.POST.get("description")
        price = request.POST.get("price")
        category = request.POST.get("category")
        condition = request.POST.get("condition")
        location = request.POST.get("location")
        latitude = request.POST.get("latitude")
        longitude = request.POST.get("longitude")
        contact_number = request.POST.get("contact_number")
        shipping_available = request.POST.get("shipping_available") == "on"
        negotiable = request.POST.get("negotiable") == "on"
        brand = request.POST.get("brand")
        model = request.POST.get("model")
        year = request.POST.get("year")

        # Convert price and year to proper types
        price = Decimal(price) if price else None
        year = int(year) if year else None

        # Handle other details as JSON
        other_details = {
            "extra_info": request.POST.get("other_details", ""),
        }

        # Create and save the listing
        listing = Listing.objects.create(
            seller=request.user,
            title=title,
            description=description,
            price=price,
            category=category,
            condition=condition,
            location=location,
            latitude=latitude if latitude else None,
            longitude=longitude if longitude else None,
            contact_number=contact_number,
            shipping_available=shipping_available,
            negotiable=negotiable,
            brand=brand,
            model=model,
            year=year,
            other_details=other_details,
            is_available=True,  # Default to available when creating
        )

        # Handle primary and additional images
        images = request.FILES.getlist("images")
        if images:
            listing.images = images[0]  # Set the first image as the primary image
            listing.save()
            for image in images[1:]:  # Remaining images as additional
                ListingImage.objects.create(listing=listing, image=image)

        return redirect("seller_dashboard")  # Redirect to the seller's dashboard after saving

    return render(
        request,
        "add_listing.html",
        {
            "category_choices": Listing.CATEGORY_CHOICES,
            "condition_choices": Listing.CONDITION_CHOICES,
        },
    )

def all_listings(request):
    query = request.GET.get('query', '')
    category = request.GET.get('category', '')

    listings = Listing.objects.filter(is_available=True)

    if query:
        listings = listings.filter(title__icontains=query)  # Filter by search query

    if category:
        listings = listings.filter(category=category)  # Filter by category

    for listing in listings:
        if not listing.images:
            additional_image = ListingImage.objects.filter(listing=listing).first()
            listing.primary_image = additional_image.image.url if additional_image else None
        else:
            listing.primary_image = listing.images.url

    return render(request, 'partials/listings_partial.html', {'listings': listings})

def listing_detail(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id)
    images = ListingImage.objects.filter(listing=listing)

    is_seller = False

    if hasattr(request.user, 'seller'):
        is_seller = True

    if not images.exists():
        images = [{"image": listing.images}] 

    context = {
        "listing": listing,
        "images": images,
        "is_seller": is_seller,
    }
    return render(request, "listing_detail.html", context)

@login_required
def edit_listing(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id, seller=request.user)

    context = {
        "listing": listing,
        "category_choices": Listing.CATEGORY_CHOICES,
        "condition_choices": Listing.CONDITION_CHOICES,
    }

    if request.method == "POST":
        listing.title = request.POST.get("title")
        listing.category = request.POST.get("category")
        listing.condition = request.POST.get("condition")
        listing.price = request.POST.get("price")
        listing.brand = request.POST.get("brand")
        listing.model = request.POST.get("model")
        listing.year = request.POST.get("year")
        listing.other_details = request.POST.get("other_details")
        listing.contact_number = request.POST.get("contact_number")
        listing.description = request.POST.get("description")
        listing.shipping_available = "shipping_available" in request.POST
        listing.negotiable = "negotiable" in request.POST

        # Ensure is_available is set correctly
        listing.is_available = True  # Ensure it remains available unless explicitly set otherwise

        if "images" in request.FILES:
            listing.image = request.FILES["images"]  # Update main image

        listing.save()
        return redirect("listing_detail", listing_id=listing.id)

    return render(request, "edit_listing.html", context)

def delete_listing(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id, seller=request.user)

    if listing.images: 
        image_path = os.path.join(settings.MEDIA_ROOT, str(listing.images))
        if os.path.exists(image_path):
            os.remove(image_path)

    related_images = ListingImage.objects.filter(listing=listing)
    for img in related_images:
        img_path = os.path.join(settings.MEDIA_ROOT, str(img.image))
        if os.path.exists(img_path):
            os.remove(img_path)
        img.delete()  

    listing.delete()

    return redirect("seller_dashboard") 

@login_required
def reject_buy_request(request, request_id):
    # Get the buy request or return 404
    buy_request = get_object_or_404(BuyRequest, id=request_id)
    
    # Ensure the logged-in user is the seller of the listing
    if request.user != buy_request.listing.seller:
        messages.error(request, "You don't have permission to reject this request.")
        return redirect('seller_dashboard')
    
    # Update the status to rejected
    buy_request.status = BuyRequest.NegotiationStatus.REJECTED
    buy_request.save()
    
    messages.success(request, f"You have rejected the offer of ₹{buy_request.proposed_price} for {buy_request.listing.title}")
    return redirect('seller_dashboard')

@login_required
def cancel_buy_request(request, request_id):
    # Get the buy request or return 404
    buy_request = get_object_or_404(BuyRequest, id=request_id)
    
    # Ensure the logged-in user is the buyer who made the request
    if request.user != buy_request.buyer:
        messages.error(request, "You don't have permission to cancel this request.")
        return redirect('buyer_dashboard')
    
    # Ensure the request is still pending
    if buy_request.status != BuyRequest.NegotiationStatus.PENDING:
        messages.error(request, "Only pending requests can be cancelled.")
        return redirect('buyer_dashboard')
    
    # Delete the buy request
    buy_request.delete()
    
    messages.success(request, f"Your buy request for {buy_request.listing.title} has been cancelled.")
    return redirect('buyer_dashboard')

@login_required
def accept_buy_request(request, request_id):
    buy_request = get_object_or_404(BuyRequest, id=request_id)
    
    # Ensure the logged-in user is the seller
    if request.user != buy_request.listing.seller:
        messages.error(request, "You don't have permission to accept this request.")
        return redirect('seller_dashboard')
    
    # Ensure the request is still pending
    if buy_request.status != BuyRequest.NegotiationStatus.PENDING:
        messages.error(request, "This request cannot be accepted.")
        return redirect('seller_dashboard')
    
    # Update buy request status
    buy_request.status = BuyRequest.NegotiationStatus.PENDING
    buy_request.save()
    
    # Create order
    order = Order.objects.create(
        buy_request=buy_request,
        buyer=buy_request.buyer,
        seller=request.user,
        listing=buy_request.listing,
        final_price=buy_request.proposed_price
    )
    
    # Create initial message
    Message.objects.create(
        sender=request.user,
        receiver=buy_request.buyer,
        buy_request=buy_request,
        content=f"Offer of ₹{buy_request.proposed_price} has been accepted. You can now discuss the details."
    )
    
    messages.success(request, f"You have accepted the offer. You can now communicate with the buyer.")
    return redirect('chat_room', buy_request_id=buy_request.id)

@login_required
def chat_room(request, buy_request_id):
    buy_request = get_object_or_404(BuyRequest.objects.select_related('listing', 'listing__seller', 'buyer'), id=buy_request_id)
    
    # Ensure user is either buyer or seller
    if request.user not in [buy_request.buyer, buy_request.listing.seller]:
        messages.error(request, "You don't have permission to access this chat.")
        return redirect('home')
    

    other_user = buy_request.buyer if request.user == buy_request.listing.seller else buy_request.listing.seller
    is_seller = False

    if hasattr(request.user, 'seller'):
        is_seller = True
    # Get chat messages
    chat_messages = Message.objects.filter(buy_request=buy_request).order_by('timestamp')
        
    order = Order.objects.filter(buy_request=buy_request).first()

    order_status = order.status if order else BuyRequest.NegotiationStatus.PENDING

    context = {
        'buy_request': buy_request,
        'other_user': other_user,
        'messages': chat_messages,
        'order_status': order_status,
        'is_seller': is_seller
    }
    print(order_status)
    return render(request, 'chat_room.html', context)

@login_required
def confirm_order(request, buy_request_id):
    if request.method != 'POST':
        return redirect('chat_room', buy_request_id=buy_request_id)
        
    buy_request = get_object_or_404(BuyRequest, id=buy_request_id)
    
    # Verify seller permissions
    if request.user != buy_request.listing.seller:
        messages.error(request, "You don't have permission to confirm this order.")
        return redirect('chat_room', buy_request_id=buy_request_id)
    
    try:
        # Update buy request status
        buy_request.status = BuyRequest.NegotiationStatus.COMPLETED
        buy_request.save()

        # Create or update order
        order, created = Order.objects.get_or_create(
            buy_request=buy_request,
            defaults={
                'buyer': buy_request.buyer,
                'seller': request.user,
                'listing': buy_request.listing,
                'final_price': buy_request.proposed_price,
                'status': 'completed'  # Set order status to completed
            }
        )
        
        if not created:
            order.status = 'completed'
            order.save()
        
        # Mark the listing as unavailable
        listing = buy_request.listing
        listing.is_available = False
        listing.save()
        
        # Reject all other pending buy requests for this listing
        BuyRequest.objects.filter(
            listing=listing,
            status=BuyRequest.NegotiationStatus.PENDING
        ).exclude(id=buy_request.id).update(
            status=BuyRequest.NegotiationStatus.REJECTED
        )
        
        # Create a confirmation message in the chat
        Message.objects.create(
            sender=request.user,
            receiver=buy_request.buyer,
            buy_request=buy_request,
            content="Order has been confirmed and marked as completed. Thank you for using our platform!"
        )
        
        messages.success(request, "Order has been confirmed and marked as completed.")
        
    except Exception as e:
        messages.error(request, f"An error occurred while confirming the order: {str(e)}")
    
    return redirect('chat_room', buy_request_id=buy_request_id)

def search_listings(request):
    query = request.GET.get('query', '')
    listings = Listing.objects.filter(is_available=True)

    if query:
        listings = listings.filter(title__icontains=query)

    for listing in listings:
        if not listing.images:
            additional_image = ListingImage.objects.filter(listing=listing).first()
            listing.primary_image = additional_image.image.url if additional_image else None
        else:
            listing.primary_image = listing.images.url

    # Return only the listings grid for HTMX requests
    if request.headers.get('HX-Request'):
        return render(request, 'partials/listings_grid.html', {'listings': listings})
    return render(request, 'partials/listings_partial.html', {'listings': listings})

def filter_listings(request):
    max_price = request.GET.get('max_price')
    listings = Listing.objects.filter(is_available=True)

    if max_price:
        listings = listings.filter(price__lte=max_price)

    for listing in listings:
        if not listing.images:
            additional_image = ListingImage.objects.filter(listing=listing).first()
            listing.primary_image = additional_image.image.url if additional_image else None
        else:
            listing.primary_image = listing.images.url

    if request.headers.get('HX-Request'):
        return render(request, 'partials/listings_grid.html', {'listings': listings})
    return render(request, 'partials/listings_partial.html', {'listings': listings})

def sort_listings(request):
    order = request.GET.get('order', '')
    listings = Listing.objects.filter(is_available=True)
    if order == 'price_low_high':
        listings = listings.order_by('price')
    elif order == 'price_high_low':
        listings = listings.order_by('-price')
    elif order == 'newest':
        listings = listings.order_by('-created_at') 
    elif order == 'oldest':
        listings = listings.order_by('created_at')  

    for listing in listings:
        if not listing.images:
            additional_image = ListingImage.objects.filter(listing=listing).first()
            listing.primary_image = additional_image.image.url if additional_image else None
        else:
            listing.primary_image = listing.images.url

    if request.headers.get('HX-Request'):
        return render(request, 'partials/listings_grid.html', {'listings': listings})
    return render(request, 'partials/listings_partial.html', {'listings': listings})

def category_search(request):
    categories = Category.choices  # Get the available categories

    # Get the latest 3 listings
    latest_listings = Listing.objects.filter(is_available=True).order_by('-created_at')[:3]

    context = {
        'categories': categories,
        'latest_listings': latest_listings,
    }
    return render(request, 'category_search.html', context)

def listings_view(request):
    """View for initial page load with base template and styling"""
    listings = Listing.objects.filter(is_available=True)
    
    for listing in listings:
        if not listing.images:
            additional_image = ListingImage.objects.filter(listing=listing).first()
            listing.primary_image = additional_image.image.url if additional_image else None
        else:
            listing.primary_image = listing.images.url
    
    return render(request, 'listings.html', {'listings': listings})

@login_required
def create_donation(request):
    if request.method == 'POST':
        try:
            # Create donation
            donation = Donation.objects.create(
                seller=request.user,
                title=request.POST['title'],
                description=request.POST['description'],
                category=request.POST['category'],
                condition=request.POST['condition'],
                location=request.POST['location'],
                contact_number=request.POST['contact_number'],
            )

            # Handle primary image
            if request.FILES.get('images'):
                donation.images = request.FILES['images']
                donation.save()

            # Handle additional images
            for image in request.FILES.getlist('images')[1:]:  # Skip the first image as it's the primary
                DonationImage.objects.create(
                    donation=donation,
                    image=image
                )

            messages.success(request, 'Your donation has been listed successfully!')
            return redirect('seller_dashboard')

        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')
            return redirect('create_donation')

    context = {
        'category_choices': Category.choices,
        'condition_choices': ItemCondition.choices,
    }
    return render(request, 'donation_form.html', context)

def admin_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_superuser:
            login(request, user)
            return redirect('admin_dashboard')
        else:
            messages.error(request, 'Invalid credentials or not an admin user.')
    return render(request, 'home/admin_login.html')

@login_required
def admin_dashboard(request):
    # Fetch sales and donation data
    total_sales = Order.objects.count()
    total_donations = Donation.objects.count()
    donations = Donation.objects.all()  # Fetch all donations
    
    context = {
        'total_sales': total_sales,
        'total_donations': total_donations,
        'donations': donations,  # Pass donations to the context
    }
    return render(request, 'home/admin_dashboard.html', context)

@login_required
def update_donation_status(request, donation_id):
    donation = get_object_or_404(Donation, id=donation_id)
    if request.method == 'POST':
        status = request.POST.get('status')
        if status in ['donated', 'cancelled']:
            donation.status = status
            donation.save()
            messages.success(request, 'Donation status updated successfully.')
        else:
            messages.error(request, 'Invalid status.')
    return redirect('admin_dashboard')

