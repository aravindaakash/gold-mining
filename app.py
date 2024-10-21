import time
import requests
from bs4 import BeautifulSoup
from prettytable import PrettyTable
from colorama import Fore, Style, init
import asyncio
from playwright.sync_api import sync_playwright
from flask import Flask, render_template, jsonify

VENDORS = {
    'chennai': "https://www.livechennai.com/gold_silverrate.asp",
    '22k': {
        'GRT': {
            'url': "https://www.grtjewels.com/22kt-1-gram-lakshmi-gold-coin-26e643863.html",
            'output_type': 'html',
        },
        'SARAVANA_STORE': {
            'url': "https://www.saravanastores.in/home/5-1-grm-gold-laxmi-916-coin.html",
            'output_type': 'html',
        },
        'MALABAR_GOLD': {
            'url': "https://www.malabargoldanddiamonds.com/gold-coins/type/916/1g/916-purity-1-grams-rose-gold-coin-mgrs916p1g.html",
            'output_type': 'html',
        },
        'JOYALUKKAS': {
          'url': "https://www.joyalukkas.in/graphql?query=query+MiniCartQuery%28%24cartId%3AString%21%29%7Bcart%28cart_id%3A%24cartId%29%7Bid+...MiniCartFragment+__typename%7D%7Dfragment+MiniCartFragment+on+Cart%7Bid+total_quantity+prices%7Bsubtotal_excluding_tax%7Bcurrency+value+__typename%7Dsubtotal_including_tax%7Bcurrency+value+__typename%7D__typename%7D...ProductListFragment+__typename%7Dfragment+AmGiftCardCartItemFragment+on+CartItemInterface%7B...on+AmGiftCardCartItem%7Bam_giftcard_image+am_giftcard_options%7Bcode+label+value+__typename%7D__typename%7D__typename%7Dfragment+ProductListFragment+on+Cart%7Bid+items%7Buid+product%7Buid+name+sku+url_key+thumbnail%7Burl+__typename%7Dstock_status+...on+ConfigurableProduct%7Bvariants%7Battributes%7Buid+__typename%7Dproduct%7Buid+thumbnail%7Burl+__typename%7D__typename%7D__typename%7D__typename%7D__typename%7Dprices%7Bprice%7Bcurrency+value+__typename%7Dtotal_item_discount%7Bvalue+__typename%7D__typename%7Dquantity+...AmGiftCardCartItemFragment+...on+ConfigurableCartItem%7Bconfigurable_options%7Bconfigurable_product_option_uid+option_label+configurable_product_option_value_uid+value_label+__typename%7D__typename%7D__typename%7D__typename%7D&operationName=MiniCartQuery&variables=%7B%22cartId%22%3A%22l5aZJlk8EtvC5GM9yJGxK04u2KmIFq1O%22%7D",
          'output_type': 'json',
        },
        'Flipkart': {
          'url': "https://www.flipkart.com/search?q=gold+coin+22k+1g&sid=mcr%2C73x%2Cydh&as=on&as-show=on&otracker=AS_QueryStore_OrganicAutoSuggest_2_14_na_na_na&otracker1=AS_QueryStore_OrganicAutoSuggest_2_14_na_na_na&as-pos=2&as-type=RECENT&suggestionId=gold+coin+22k+1g%7CCoins+%26+Bars&requestId=5e737665-0b82-49d8-b88f-be7e7de52c69&as-backfill=on&sort=price_asc",
          'output_type': 'html',
        },
        'TANISHQ': {
          'url': "https://www.tanishq.co.in/product/1-gram-22-karat-gold-coin-with-lakshmi-motif-600105zfarap00.html?lang=en_IN",
          'output_type': 'html',
        }
    }
}


def fetch_tanishq_gold_content(html_content):
  global BASE_PRICE
  soup = BeautifulSoup(html_content, 'html.parser')
  # Initialize a dictionary to hold the final structured data
  data = {}
  data['store'] = "Tanishq"
  data['carat'] = '22'
  data['Purity'] = '91.6%'
  data['Weight'] = '1'
  data['discount'] = 0

  # Find all col-values elements to extract pricing details
  price_sections = soup.find_all('div', class_='col-values')
  
  for section in price_sections:
      columns = section.find_all('div')

      # Ensure there are enough columns to extract relevant details
      if len(columns) >= 5:
          item_name = columns[1].get_text(strip=True)
          value = columns[-1].get_text(strip=True)
          # import ipdb; ipdb.set_trace()
          # print(item_name, value)
          if "Yellow Gold22KT" in item_name:
              data['Rate'] = value.replace('₹', '').replace(',', '').strip()
          elif "Making Charges" in item_name:
              data['Making Charges'] = value.replace('₹', '').replace(',', '').strip()
          elif "Sub Total" in item_name:
              sub_total = value.replace('₹', '').replace(',', '').strip()
          elif "GST" in item_name:
              data['gst'] = value.replace('₹', '').replace(',', '').strip()
          
  data['Grand Total'] = float(sub_total) + float(data['gst'])
  data['Extra amount'] = round((data['Grand Total'] - BASE_PRICE),2)
  data['Link'] = VENDORS['22k']['TANISHQ']['url']
  return data
   
def fetch_flipkart_gold_content(html):
  global BASE_PRICE
  soup = BeautifulSoup(html, 'html.parser')

  # Find the first item container with a data-id attribute
  first_item = soup.find('div', {'data-id': True})

  if not first_item:
    return None

  # Extract the item name
  item_name_tag = first_item.find('a', {'class': lambda x: x and 'WKTcLC' in x.split()})
  item_name = item_name_tag.text.strip() if item_name_tag else 'N/A'

  # Extract the item price
  item_price_tag = first_item.find('div', {'class': lambda x: x and 'Nx9bqj' in x.split()})
  item_price = item_price_tag.text.strip() if item_price_tag else 'N/A'

  # Extract the item URL
  item_url_tag = first_item.find('a', {'class': lambda x: x and 'rPDeLR' in x.split()})
  item_url = f"https://www.flipkart.com{item_url_tag['href']}" if item_url_tag else 'N/A'

  data = {}
  data['store'] = "Flipkart"
  data['carat'] = '22'
  data['Purity'] = '91.6%'
  data['Rate'] = float(item_price.replace('₹', '').replace(',', '').strip())
  data['Weight'] = '1'
  data['discount'] = 0
  data['Making Charges'] = 'NA'
  data['gst'] = 'NA'
  data['Grand Total'] = float(item_price.replace('₹', '').replace(',', '').strip())
  data['Extra amount'] = round((data['Grand Total'] - BASE_PRICE),2)
  data['Link'] = item_url
  return data

def is_cloudflare_block(content):
    # Check if the content contains the Cloudflare block keywords
    return "Attention Required! | Cloudflare" in content or "You have been blocked" in content


def get_html_content(url, playwrite=False, retries=10, delay=3):
    attempt = 0
    while attempt < retries:
        if playwrite:
            with sync_playwright() as p:
                # Launch the browser
                browser = p.chromium.launch(headless=False)  # Use headless=False for debugging
                page = browser.new_page()
                
                # Navigate to the website
                page.goto(url)
                
                # Get the page content after the page has fully loaded
                content = page.content()
                # Close the browser
                browser.close()
                
                if not is_cloudflare_block(content):
                    return content
                else:
                    print(f"Cloudflare block detected, retrying... (Attempt {attempt + 1}/{retries})")
        else:
            response = requests.get(url)
            content = response.content.decode('utf-8')

            if not is_cloudflare_block(content):
                return content
            else:
                print(f"Cloudflare block detected, retrying... (Attempt {attempt + 1}/{retries})")

        # Wait before retrying
        attempt += 1
        time.sleep(delay)

    raise Exception("Max retries exceeded. Unable to fetch the content due to Cloudflare block.")


def get_json_content(url):
    payload = {}
    headers = {
      'accept': '*/*',
      'accept-language': 'en-GB,en;q=0.9',
      'content-type': 'application/json',
    }
    response = requests.request("GET", url, headers=headers, data=payload)
    return response.json()

def fetch_gold_price_from_vendor(content, store_name):
    match store_name:
      case 'GRT':
        return fetch_grt_price_content(content)
      case 'SARAVANA_STORE':
        return fetch_saravana_store_content(content)
      case 'MALABAR_GOLD':
        return fetch_malabar_gold_content(content)
      case 'JOYALUKKAS':
        return fetch_joyalukkas_gold_content(content)
      case 'Flipkart':
        return fetch_flipkart_gold_content(content)
      case 'TANISHQ':
        return fetch_tanishq_gold_content(content)
      case _:
        return fetch_gold_price_content(content)

def fetch_gold_price_content(html):
    # Parse the HTML content with BeautifulSoup
    data = {}
    soup = BeautifulSoup(html, 'html.parser')

    # Locate all tables on the page
    tables = soup.find_all('table')

    # Iterate over each table to find the correct one (with gold prices)
    for table in tables:
        # Check if this table has the header we are looking for (Pure Gold or Standard Gold)
        header = table.find('thead')
        if header and 'Pure Gold' in header.text:
            # Once we find the correct table, extract data from the first row (today's prices)
            table_body = table.find('tbody')
            today_row = table_body.find('tr')

            # Extract the gold prices from the relevant columns
            date = today_row.find_all('td')[0].text.strip()  # First column is the date
            gold_24k_price = today_row.find_all('td')[1].text.strip()  # Second column: 24k price for 1 gram
            gold_22k_price = today_row.find_all('td')[3].text.strip()  # Fourth column: 22k price for 1 gram

            # Clean up the price text and convert to float
            gold_24k_price = float(gold_24k_price.replace('₹', '').replace(',', '').strip())
            gold_22k_price = float(gold_22k_price.replace('₹', '').replace(',', '').strip())

            data['date'] = date 
            data['gold_22k_price'] = gold_22k_price
            data['gold_24k_price'] = gold_24k_price
            return data

    # Return None if the table wasn't found
    return data

def fetch_grt_price_content(html_content):
    global BASE_PRICE
    soup = BeautifulSoup(html_content, 'html.parser')

    # Find the table in the Price Breakup section
    table = soup.find('table')

    # Initialize a list to hold the extracted data
    price_breakup = []

    # Extract header names
    headers = [th.get_text(strip=True) for th in table.find_all('th')]
    price_breakup.append(headers)

    # Extract rows from the table
    for row in table.find_all('tr')[1:]:  # Skip the header row
        columns = row.find_all('td')
        if columns:  # Make sure it's not an empty row
            row_data = [col.get_text(strip=True) for col in columns]
            price_breakup.append(row_data)

    # Initialize a dictionary to hold the final structured data
    price_breakup_dict = {}
    price_breakup_dict['store'] = 'GRT'
    # Populate the dictionary with relevant data
    for i, row in enumerate(price_breakup):
        if i == 0:
            continue  # Skip the header row

        # Check if the row has enough columns
        if len(row) < 6:
            # print(f"Skipping row due to insufficient columns: {row}")
            continue  # Skip this row if it doesn't have enough columns

        # Check for the gold component
        if 'Gold' in row[0]:  
            # price_breakup_dict['Component'] = 'Gold'
            price_breakup_dict['carat'] = '22'
            price_breakup_dict['Purity'] = '91.6%'
            price_breakup_dict['Rate'] = row[1]
            price_breakup_dict['Weight'] = row[2]
            # price_breakup_dict['Value'] = row[3].replace('₹', '').replace(',', '').strip()  # Remove currency symbols
            price_breakup_dict['Discount'] = int(row[4].replace('₹', '').strip() or 0)  # Convert discount to integer, default to 0 if empty
        elif 'Making Charges' in row[0]:  # For making charges
            price_breakup_dict['Making Charges'] = row[3].replace('₹', '').replace(',', '').strip()
        elif 'GST (3%)' in row[0]:  # For GST
            price_breakup_dict['gst'] = row[3].replace('₹', '').replace(',', '').strip()
        elif 'Grand Total' in row[0]:  # For Grand Total
            price_breakup_dict['Grand Total'] = float(row[3].replace('₹', '').replace(',', '').strip())

    # Return the final dictionary
    price_breakup_dict['Extra amount'] = round((price_breakup_dict['Grand Total'] - BASE_PRICE),2)
    price_breakup_dict['Link'] = VENDORS['22k']['GRT']['url']
    return price_breakup_dict

def fetch_saravana_store_content(html_content):
    global BASE_PRICE
    soup = BeautifulSoup(html_content, 'html.parser')

    # Find the table in the Price Breakup section
    table = soup.find('table', {'id': 'super-product-table'})

    # Initialize a dictionary to hold the final structured data
    price_breakup_dict = {}

    # Check if the table is found
    if table:
        # Extract the headers
        headers = [th.get_text(strip=True) for th in table.find_all('th')]
        
        # Extract the row data
        for row in table.find_all('tr')[1:]:  # Skip the header row
            columns = row.find_all('td')
            if columns:  # Make sure it's not an empty row
                row_data = [col.get_text(strip=True).replace('₹', '').replace(',', '').strip() for col in columns]

                # Populate the dictionary based on the headers
                if len(row_data) == len(headers):
                    price_breakup_dict[headers[0]] = row_data[0]  # Gold
                    price_breakup_dict[headers[1]] = row_data[1]  # Making Charge + VA
                    price_breakup_dict[headers[2]] = row_data[2]  # GST 3%

    price_breakup_dict
    data = {}
    data['store'] = 'Saravana Store'
    data['carat'] = '22'
    data['Purity'] = '91.6%'
    data['Rate'] = price_breakup_dict['Gold']
    data['Weight'] = '1'
    data['discount'] = 0
    data['Making Charges'] = price_breakup_dict['Making Charge + VA']
    data['gst'] = price_breakup_dict['GST 3%']
    data['Grand Total'] = (float(price_breakup_dict['Gold'])+float(price_breakup_dict['Making Charge + VA'])+float(price_breakup_dict['GST 3%']))
    data['Extra amount'] = round((data['Grand Total'] - BASE_PRICE),2)
    data['Link'] = VENDORS['22k']['SARAVANA_STORE']['url']
    return data

def fetch_joyalukkas_gold_content(json_content):
    global BASE_PRICE
    data = {}
    data['store'] = 'Joyalukkas'
    data['carat'] = '22'
    data['Purity'] = '91.6%'
    data['Rate'] = json_content['data']['cart']['items'][0]['prices']['price']['value']
    data['Weight'] = '1'
    data['discount'] = json_content['data']['cart']['items'][0]['prices']['total_item_discount']['value']
    data['Making Charges'] = 'NA'
    data['gst'] = 'NA'
    data['Grand Total'] = float(json_content['data']['cart']['items'][0]['prices']['price']['value'])
    data['Extra amount'] = round((data['Grand Total'] - BASE_PRICE),2)
    data['Link'] = VENDORS['22k']['JOYALUKKAS']['url']
    return data

def fetch_malabar_gold_content(html_content):
    global BASE_PRICE
    soup = BeautifulSoup(html_content, 'html.parser')
    price_tag = soup.find('span', class_='price')

    # Extract the text and clean it
    if price_tag:
        price = price_tag.get_text(strip=True)
        # return price  # Output: ₹ 7,779
    data = {}
    data['store'] = 'Malabar Gold'
    data['carat'] = '22'
    data['Purity'] = '91.6%'
    data['Rate'] = price.replace('₹', '').replace(',', '').strip()
    data['Weight'] = '1'
    data['discount'] = 0
    data['Making Charges'] = 'NA'
    data['gst'] = 'NA'
    data['Grand Total'] = float(price.replace('₹', '').replace(',', '').strip())
    data['Extra amount'] = round((data['Grand Total'] - BASE_PRICE),2)
    data['Link'] = VENDORS['22k']['MALABAR_GOLD']['url']
    return data

def fetch_chennai_gold_price():
    html_content =  get_html_content(VENDORS['chennai'])
    return fetch_gold_price_from_vendor(html_content, 'CHENNAI')

def print_data(data, prices):
  # ANSI escape codes for styling
  GREEN = '\033[92m'
  RED = '\033[91m'
  YELLOW = '\033[93m'
  BLUE = '\033[94m'
  BOLD = '\033[1m'
  UNDERLINE = '\033[4m'
  RESET = '\033[0m'

  print(f"\n\n{BOLD}Gold Price Comparison{RESET}\n")
  print(f"{BOLD}Date: {data['date']}{RESET}")
  print(f"{BOLD}Gold 22K Price: {YELLOW}₹{data['gold_22k_price']}{RESET}")
  print(f"{BOLD}Gold 24K Price: {YELLOW}₹{data['gold_24k_price']}{RESET}\n")

  # Sort prices by Grand Total in descending order
  sorted_prices = sorted(prices, key=lambda x: x['Grand Total'])

  # Create a PrettyTable object
  table = PrettyTable()

  # Define table columns
  table.field_names = ["Store", "Carat", "Rate", "Purity", "Weight", "Discount", "Making Charges", "GST", "Grand Total", "Extra amount", "Link" ]

  # Add rows to the table
  for i, price in enumerate(sorted_prices):
    row = [
      price['store'],
      price['carat'],
      price['Rate'],
      price['Purity'],
      price['Weight'],
      price.get('Discount', price.get('discount', 'NA')),  # Check for both Discount and discount keys
      price['Making Charges'],
      price['gst'],
      price['Grand Total'],
      price['Extra amount'],
      f"\033]8;;{price['Link']}\033\\{UNDERLINE}Link\033]8;;\033\\"
    ]
    if i == 0:
      table.add_row([f"{GREEN}{BOLD}{item}{RESET}" for item in row])
    else:
      table.add_row([f"{BLUE}{item}{RESET}" for item in row])

  # Print the table
  print(table)

# Function to compare and display the best prices
def gold_coin_prices():
    prices = []
    global BASE_PRICE
    data = fetch_chennai_gold_price()
    BASE_PRICE = data['gold_22k_price']
    for stores in VENDORS['22k']:
        print(f"Fetching {stores} price")
        playwright = False
        if stores == 'Flipkart' or stores == 'TANISHQ':
           playwright = True
        if VENDORS['22k'][stores]['output_type'] == 'html':
            prices.append(fetch_gold_price_from_vendor(get_html_content(VENDORS['22k'][stores]['url'],playwright), stores))
        elif VENDORS['22k'][stores]['output_type'] == 'json':
            prices.append(fetch_gold_price_from_vendor(get_json_content(VENDORS['22k'][stores]['url']), stores))
    # import ipdb; ipdb.set_trace()
    print_data(data, prices)
    
# gold_coin_prices()

app = Flask(__name__)

@app.route('/gold-prices', methods=['GET'])
def gold_coin_prices():
  prices = []
  global BASE_PRICE
  data = fetch_chennai_gold_price()
  BASE_PRICE = data['gold_22k_price']
  for stores in VENDORS['22k']:
    print(f"Fetching {stores} price")
    playwright = False
    if stores == 'Flipkart' or stores == 'TANISHQ':
      playwright = True
    if VENDORS['22k'][stores]['output_type'] == 'html':
      prices.append(fetch_gold_price_from_vendor(get_html_content(VENDORS['22k'][stores]['url'],playwright), stores))
    elif VENDORS['22k'][stores]['output_type'] == 'json':
      prices.append(fetch_gold_price_from_vendor(get_json_content(VENDORS['22k'][stores]['url']), stores))
  return render_template('gold_prices.html', data=data, prices=prices)

if __name__ == '__main__':
     import os
     port = int(os.environ.get('PORT', 5000))
     app.run(debug=True, host='0.0.0.0', port=port)
