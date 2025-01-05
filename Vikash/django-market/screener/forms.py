from django import forms
from .models import AddScreener

class ScreenerUploadForm(forms.ModelForm):
    '''
    options = [('stocks-trending-above-10-ema-for-a-month', 
                          'stocks-trending-above-10-ema-for-a-month'),
                         ('all-emas-in-all-candles-trending',
                           'all-emas-in-all-candles-trending'),
                         ('weekly-10-21-50-200-first-time',
                          'weekly-10-21-50-200-first-time'),
                         ('stocks-crossed-200-ema-and-gone-bullish',
                          'stocks-crossed-200-ema-and-gone-bullish'),
                         ('bullish-stocks-respecting-10ema',
                          'bullish-stocks-respecting-10ema')]
    file = forms.FileField()
    choice_field = forms.ChoiceField(choices=options,
                                   label="Choose an option")
    '''
    class Meta:
        model = AddScreener
        exclude = ['name','url']

    file = forms.FileField()
    screener = forms.ModelChoiceField(
            queryset=AddScreener.objects.all(),
            empty_label='Select a Screener',
            label="Screener"
    )
    

class AddScreenerForm(forms.Form):
    name = forms.CharField(max_length=100)
    url = forms.CharField(max_length=200)



