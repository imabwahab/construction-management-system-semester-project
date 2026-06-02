from django import forms

from .models import Bid


class BidForm(forms.ModelForm):
    class Meta:
        model = Bid
        fields = ("bid_amount", "proposed_timeline_days")
        widgets = {
            "bid_amount": forms.NumberInput(attrs={"min": "0", "step": "0.01"}),
            "proposed_timeline_days": forms.NumberInput(attrs={"min": "1"}),
        }
