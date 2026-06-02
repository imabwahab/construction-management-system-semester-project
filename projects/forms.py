from django import forms

from .models import Project


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = (
            "title",
            "category",
            "description",
            "location",
            "budget_min",
            "budget_max",
            "deadline",
        )
        widgets = {
            "deadline": forms.DateInput(attrs={"type": "date"}),
            "description": forms.Textarea(attrs={"rows": 4}),
        }

    def clean(self):
        cleaned = super().clean()
        budget_min = cleaned.get("budget_min")
        budget_max = cleaned.get("budget_max")
        if budget_min is not None and budget_max is not None and budget_max < budget_min:
            self.add_error("budget_max", "Maximum budget cannot be less than the minimum.")
        return cleaned
