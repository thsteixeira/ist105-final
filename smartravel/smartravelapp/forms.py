from django import forms
from django.forms import ModelForm

from .models import TravelHistory
from .get_locations import get_locations_from_api

class TravelHistoryForm(ModelForm):
    
    def __init__(self, *args, **kwargs):
        # Extract location_choices from kwargs if provided
        location_choices = kwargs.pop('location_choices', None)
        super().__init__(*args, **kwargs)
        
        # Get location choices from API if not provided
        if location_choices is None:
            location_choices = get_locations_from_api()
        
        # Update the choices for both fields
        self.fields['start'] = forms.ChoiceField(
            choices=location_choices,
            widget=forms.Select(attrs={'class': 'form-control'})
        )
        self.fields['destination'] = forms.ChoiceField(
            choices=location_choices,
            widget=forms.Select(attrs={'class': 'form-control'})
        )
    
    class Meta:
        model = TravelHistory
        fields = ['start', 'destination']