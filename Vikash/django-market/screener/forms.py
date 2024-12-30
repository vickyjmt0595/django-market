from django import forms

class ScreenerForm(forms.Form):
    file = forms.FileField()