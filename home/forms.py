from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Seller

class SellerSignupForm(UserCreationForm):
    name = forms.CharField(max_length=255)
    phone_number = forms.CharField(max_length=15, required=False)
    address = forms.CharField(widget=forms.Textarea, required=False)
    latitude = forms.DecimalField(max_digits=9, decimal_places=6, required=False)
    longitude = forms.DecimalField(max_digits=9, decimal_places=6, required=False)
    is_neighborhood_verified = forms.BooleanField(initial=False, required=False)
    profile_image = forms.ImageField(required=False)
    date_of_birth = forms.DateField(required=False)
    instagram_link = forms.URLField(max_length=255, required=False)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['name']
        
        if commit:
            user.save()
            seller = Seller.objects.create(
                user=user,
                phone_number=self.cleaned_data.get('phone_number'),
                address=self.cleaned_data.get('address'),
                latitude=self.cleaned_data.get('latitude'),
                longitude=self.cleaned_data.get('longitude'),
                is_neighborhood_verified=self.cleaned_data.get('is_neighborhood_verified'),
                profile_image=self.cleaned_data.get('profile_image'),
                date_of_birth=self.cleaned_data.get('date_of_birth'),
                instagram_link=self.cleaned_data.get('instagram_link')
            )
        return user