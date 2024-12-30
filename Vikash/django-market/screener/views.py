import csv
import yfinance as yf                                                                                                                  
import pandas as pd

from datetime import datetime
from django.shortcuts import render
from django.http import HttpResponse


from .forms import ScreenerForm
from .models import ScreenerUpload

# Enable disk caching
# yf.set_caching(enabled=True)

def home(request):
    return render(request, 'screener/home.html')

def screener_upload(request):
    recent_uploads = ScreenerUpload.objects.all()[:10]
    if request.method == 'POST':
        form = ScreenerForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['file']
            if uploaded_file.name.endswith('.csv'):
                upload_instance = ScreenerUpload.objects.create(file=uploaded_file)
            else:
                return render(request, 'screener/screener_upload.html',
                        {'form': form,
                        'error': 'Unsupported file type'})
            return HttpResponse('File Uploaded Successfully',
                                content_type='text/plain')
    else:
        form = ScreenerForm()
    return render(request, 'screener/screener_upload.html',
                  {'form': form,
                   'uploads': recent_uploads})

def get_appearance_count(stocks_data,sorted_date_details, index):
    stocks_count_details = {} 
    for stock in stocks_data:
        stocks_count = len(stocks_data[stock])
                                                 
        for date_detail in sorted_date_details[-index:]:
            if stock in date_detail[1]:
                # print(f'stock found {index-1} days ago : {stock}')
                stocks_count -= 1
        stocks_count_details[stock] = stocks_count
    # print('stocks_count_details :', stocks_count_details)
    return stocks_count_details

def get_new_stocks_and_change(count_data, date_data, index):
    new_stocks = dict()
    date = date_data[-index][0]
    date_format = '-'.join(val for val in date.split('-')[::-1])
    for stock in count_data:
        if (count_data[stock] == 1 and stock in date_data[-index][1]):
            new_stocks[stock] = get_price_change_percentage(f'{stock}.NS',
                                                            date_format)         
    return new_stocks, date

def screener_analysis(request, id):
    file_instance = ScreenerUpload.objects.get(id=id)
    file_path = file_instance.file.path
    # file_name = file_instance.filename
    # print('file_path -----:', file_path)
    # print('file name ----:', file_instance.filename)
    stocks_data, date_details = get_all_stock_details(file_path)
    sorted_date_details = sorted(date_details.items(),
                                     key=lambda x:datetime.strptime(x[0],
                                     '%d-%m-%Y') )
    screener_data = {}
    history_days = 11
    for index in range(1, history_days):
            count_details = get_appearance_count(stocks_data,
                                                 sorted_date_details,
                                                 index)
            new_stocks, date = get_new_stocks_and_change(count_details,
                                              sorted_date_details, index)
            screener_data[date] = new_stocks
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

def get_price_change_percentage(ticker_symbol, start_date):                                                                         
    """                                                                                                                                
    Calculate the percentage change in price for a stock since a given date to today.                                                  
                                                                                                                                       
    Args:                                                                                                                              
        ticker_symbol (str): The stock ticker symbol (e.g., 'AAPL').                                                                   
        start_date (str): The starting date in the format 'YYYY-MM-DD'.                                                                
                                                                                                                                       
    Returns:                                                                                                                           
        float: The percentage change in price.                                                                                         
    """                                                                                                                                
    # Fetch historical data                                                                                                            
    stock_data = yf.download(ticker_symbol, start=start_date)                                                                          
                                                                                                                                       
    # Ensure data exists
    if stock_data.empty:
        return f"No data available for {ticker_symbol} since {start_date}"

    # Extract the 'Close' column for the specific ticker and ensure it's a Series
    stock_data_close = stock_data['Close']

    # Get the starting and current prices as scalars
    start_price = stock_data_close.iloc[0]  # This gives the first value
    current_price = stock_data_close.iloc[-1]  # This gives the last value

    # Convert to scalar if it's still a Series
    if isinstance(start_price, pd.Series):
        start_price = start_price.item()
    if isinstance(current_price, pd.Series):
        current_price = current_price.item()

    # Calculate the percentage change
    change_percentage = ((current_price - start_price) / start_price) * 100

    return round(change_percentage, 2)