import csv
import yfinance as yf
import pandas as pd
import requests_cache
import numpy as np

from datetime import datetime
from django.shortcuts import render
from django.http import HttpResponse
from dateutil.relativedelta import relativedelta
from icecream import ic
from django.db.utils import IntegrityError

from .forms import AddScreenerForm , ScreenerUploadForm
from .models import ScreenerFileUpload, Stock

# Enable disk caching
# yf.set_caching(enabled=True)
session = requests_cache.CachedSession('yfinance.cache',
                                       expire_after=43200)  # Cache expiration: 1 day
session.headers['User-agent'] = 'vicky-program/3.0'


def home(request):
    return render(request, 'screener/home.html')


def screener_upload(request):
    recent_uploads = ScreenerFileUpload.objects.all()[:10]
    if request.method == 'POST':
        form = ScreenerUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['file']
            # Access the value of 'filename'
            file = form.cleaned_data['file']
            screener = form.cleaned_data['screener']
            if uploaded_file.name.endswith('.csv'):
                upload_instance = ScreenerFileUpload.objects.create(
                    file=file, screener=screener)
            else:
                return render(request, 'screener/screener_upload.html',
                              {'form': form,
                               'error': 'Unsupported file type'})
            return render(request, 'screener/upload_success.html',
                          {'uploads': upload_instance})
    else:
        form = ScreenerUploadForm()
    return render(request, 'screener/screener_upload.html',
                  {'form': form,
                   'uploads': recent_uploads
                   })


def get_appearance_count(stocks_data, date_details, current_date):
    stocks_count_details = {}

    for stock in stocks_data:
        count = 0
        if current_date in stocks_data[stock]:
            date_index = stocks_data[stock].index(current_date)
            if date_index == 0:
                count = 1
            # If stock appearing after a week, consider it as new
            else:
                last_found_date = stocks_data[stock][date_index-1]
                # Convert from string to datetime format
                date_format = "%d-%m-%Y"
                last_found_date_obj =datetime.strptime(last_found_date, date_format)
                current_date_obj = datetime.strptime(current_date, date_format)
                difference = relativedelta(current_date_obj,
                                           last_found_date_obj)
                if difference.days > 20:
                    print("There is a difference of a month.")
                    count = 1
        stocks_count_details[stock] = count
    # stocks_count_details[stock] = count
    # print('stocks_count_details :', stocks_count_details)
    return stocks_count_details



def get_new_stocks_change_percent(count_data, current_date, tickers):
    new_stocks = dict()
    date_format = '-'.join(val for val in current_date.split('-')[::-1])
    for stock in count_data:
        if (count_data[stock] == 1):
            try:
                new_stocks[stock] = get_price_change_percentage(f'{stock}.NS',
                                                            current_date,
                                                            tickers)
            except KeyError as err:
                ic(f'Got {err} for {stock}')
                new_stocks[stock] = -1000

    return new_stocks

def construct_urls(stock):
    return (f"https://chartink.com/stocks/{stock.lower()}.html")

def get_new_stocks_and_urls(count_data):
    new_stocks = dict()
    for stock in count_data:
        if (count_data[stock] == 1):
            new_stocks[stock] = construct_urls(stock)
            
    return new_stocks


def get_stocks_price_data(stocks_data, start_date, end_date):
    # Join stock symbols with ".NS" and fetch all data in one request
    tickers = ' '.join(f'{stock}.NS' for stock in stocks_data)
    # Fetch historical data for all stocks at once
    historical_data = yf.download(tickers, session=session, group_by="ticker",
                                  start=start_date, end=end_date)
    # Process the data into a dictionary
    stocks_price_data = {}
    for stock in stocks_data:
        stock_ticker = f'{stock}.NS'
        if stock_ticker in historical_data:
            stocks_price_data[stock_ticker] = historical_data[stock_ticker]

    return stocks_price_data

def screener_analysis(request, id):
    file_instance = ScreenerFileUpload.objects.get(id=id)
    screener = file_instance.screener
    file_path = file_instance.file.path
    stocks_data, date_details = get_all_stock_details(file_path)
    history_days = len(date_details)
    list_of_date = list(date_details.keys())
    for index in range(1, history_days):
        current_date = list_of_date[index]
        current_date_ymd = '-'.join(val for val in current_date.split('-')[::-1])
        count_details = get_appearance_count(stocks_data,
                                             date_details,
                                             current_date)
        new_stocks = get_new_stocks_and_urls(count_details)

        for stock,url in new_stocks.items():
            Stock.objects.get_or_create(
            date=current_date_ymd,
            name=stock,
            screener=screener,
            url=url
        )

    stocks_data = Stock.objects.filter(screener=screener)
    return render(request, 'screener/stock_screener_analysis.html',
                  {'file': file_instance.file.name,
                   'stocks_data': stocks_data,
                   'screener': screener
                   })


# To work on it later
def screener_analysis_price_change(request, id):
    file_instance = ScreenerFileUpload.objects.get(id=id)
    file_path = file_instance.file.path
    # file_name = file_instance.filename
    # print('file_path -----:', file_path)
    # print('file name ----:', file_instance.filename)
    stocks_data, date_details = get_all_stock_details(file_path)
    screener_data = Stock.objects.all()
    if len(screener_data) >= len(stocks_data):
        return render(request, 'screener/screener_analysis.html',
                  {'file': file_instance.filename,
                   'screener_data': screener_data
                   })

    sorted_date_details = sorted(date_details.items(),
                                 key=lambda x: datetime.strptime(x[0],
                                                                 '%d-%m-%Y'))
    screener_data = {}
    history_days = len(date_details)
    list_of_date = list(date_details.keys())
    start_date = '-'.join(val for val in list_of_date[0].split('-')[::-1])
    end_date = '-'.join(val for val in list_of_date[-1].split('-')[::-1])
    tickers = get_stocks_price_data(stocks_data.keys(), start_date,
                                        end_date)
    for index in range(1, history_days):
        current_date = list_of_date[index]
        current_date_ymd = '-'.join(val for val in current_date.split('-')[::-1])
        count_details = get_appearance_count(stocks_data,
                                             date_details,
                                             current_date)
        new_stocks = get_new_stocks_change_percent(count_details, current_date,
                                    tickers)
        # screener_data[current_date_ymd] = new_stocks
        for stock, change in new_stocks.items():
            if not Stock.objects.filter(name=stock,
                                        date=current_date_ymd).exists():
                Stock.objects.create(date=current_date_ymd,
                                 name=stock, change=change)
    screener_data = Stock.objects.all()
        
    return render(request, 'screener/screener_analysis.html',
                  {'file': file_instance.filename,
                   'screener_data': screener_data
                   })


def get_all_stock_details(input_file):
    with open(input_file) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        stock_details = {}
        stock_date_details = {}
        for row in csv_reader:
            if line_count:
                # Get details based on stocks
                stock_date, stock_name = row[0], row[1]
                if stock_details.get(stock_name):
                    stock_details[stock_name].append(stock_date)
                else:
                    stock_details[stock_name] = [stock_date]
                # Get details based on date
                if stock_date_details.get(stock_date):
                    stock_date_details[stock_date].append(stock_name)
                else:
                    stock_date_details[stock_date] = [stock_name]
                line_count += 1
            else:
                line_count += 1
        return stock_details, stock_date_details


def get_price_change_percentage(ticker_symbol, start_date, tickers):
   # Fetch historical data
    historical_data = tickers[ticker_symbol]
    # start_date = '-'.join(val for val in start_date.split('-')[::-1])
    specific_date_close = historical_data.loc[start_date]["Close"]
    # Ensure data exists
    if not specific_date_close:
        return f"No data available for {ticker_symbol} since {start_date}"
    # Get the starting and current prices as scalars
    start_price = round(specific_date_close, 2)  # This gives the first value
    current_price = historical_data["Close"].iloc[-1] # Get the latest date

    # Calculate the percentage change
    change_percentage = ((current_price - start_price) / start_price) * 100
    change_percentage = float(round(change_percentage, 2))
    if np.isnan(change_percentage):
        print('Change_percent is nan')
        change_percent = -500

    return change_percentage