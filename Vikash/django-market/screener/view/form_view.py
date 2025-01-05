from django.shortcuts import render

from ..forms import AddScreenerForm
from ..models import AddScreener


def add_screener(request):
    screeners = AddScreener.objects.all()
    if request.method == 'POST':
        form = AddScreenerForm(request.POST, request.FILES)
        if form.is_valid():
            # Access the values from the form
            name = form.cleaned_data['name']
            url = form.cleaned_data['url']
            created = AddScreener.objects.create(name=name,
                                   url=url)
            return render(request, 'screener/add_screener_success.html',
                          {'created': created})

    else:
        form = AddScreenerForm()
        return render(request, 'screener/add_screener.html',
                      {'form': form,
                       'screeners': screeners})
        