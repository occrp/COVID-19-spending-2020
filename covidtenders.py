#!/usr/bin/env python
# coding: utf-8

import pandas as pd
import numpy as np
from datetime import date
import difflib

from pathlib import Path
                                          
def x_to_eur(x, price="price",price_currency="price_currency",price_EUR="price_EUR"):
    
    '''
    convert prices to euro
    returns a new Series with the euro prices
    '''

    price_currency = price_currency.strip()
                                           
    x_to_eur = {'EUR': 1,
               'CHF': 0.95,
               'CZK': 0.036,
               'HUF': 0.0028,
               'GBP': 1.13,
               'ALL': 0.008,
               'ISK' :  0.006,
               'MKD' : 0.016,
               'NOK' : 0.091,
               'SEK' : 0.0945,
               'RUB' : 0.012,
               "RON" : 0.206,
               "PLN" : 0.223,
               "CNY" : 0.12,
               "MDL" : 0.051,
               "BGN" : 0.511292,
               "USD" : 0.873956,
               "ALL" : 0.00806510,
               "BAM" : 0.511292,
               "UAH" : 0.031,
               "HRK" : 0.132,
               "DKK" : 0.134}
    
    # if the price in euro is not filled in in the sheet   
    if pd.isna(x[price_EUR]) or x[price_EUR] == "":
        
        n = x[price]                                   
        
        try:
            if type(n) == float or type(n) == int:
                n = n * x_to_eur[x[price_currency]] 
                return n
            elif type(n) == str:
                n = float(n.replace(",","").strip())
                n = n * x_to_eur[x[price_currency]] 
                #print(f'WAS STRING: {x[price]}')
                return n
            else:
                #print(f'REFUSED: {n}')
                return ""
        except:
            #print(f'REFUSED: {n}')
            return ""

    else:
        return x[price_EUR]
                                           
                                           
def clean_tender_data(alldata):
                                                                                     
    # 1) change the procedures to open, closed and direct award
    proc_map = {"Open procedure" : "open competition",
                "Competitive dialogue" : "open competition",
                "Restricted procedure" : "open competition",
                "Restricted procedure (OJEU)" : "open competition",
                "Open procedure (OJEU)" :"open competition",
                
                "Competitive procedure with negotiation" : "closed competition",
                "Negotiated procedure" : "closed competition", 
                
                "Contract award without prior publication" : "direct award",
                "Negotiated without a call for competition" : "direct award",
                "Contract award without notice" : "direct award",
                "Negotiated without a prior call for competition" : "direct award",
               "Negociado sin publicidad" :  "direct award",}

    alldata["procedure"] = alldata["procedure"].replace(proc_map)
    
    # 2) remove older than 2020 tenders, not-covid related tenders, tenders without a category, duplicate and cancelled tenders
    
    alldata = alldata[(pd.to_numeric(alldata["year"]) == 2020) &
                      (alldata["product"].str.lower() != "not covid19 related") &
                     (alldata["product"].notnull()) &
                      (alldata["type"].str.lower() != "call for tender") &
                      (alldata["type"].str.lower() != "duplicate") &
                     (alldata["status"].str.lower() != "cancelled")]
                                           
                                           
    # 3) calculate price in EUR
    alldata['price_EUR'] = pd.to_numeric(alldata.apply(lambda x: x_to_eur(x), axis=1), errors="coerce")                 
    alldata['price_lot_EUR'] = pd.to_numeric(alldata.apply(lambda x: x_to_eur(x, "price_lot","price_lot_currency","price_lot_EUR"), axis=1), errors="coerce")        
                                           
    # 4) strip some strings
                   
    for col in ["source", "buyer", "supplier"]:
        alldata[col] = alldata[col].str.strip()
                                           
    alldata = alldata.drop_duplicates(alldata.columns[1:])
                                           
    return(alldata)

def filter_just_tenders(df):
    
    '''
    Gets only prices of the whole tender or contract
    (some tenders have multiple lots and/or multiple winners and span over multiple rows)
        
    Most of the tenders come from TED, with a few exceptions.
    
    Returns dataframe with cleaned tenders.
    
    usage:
    TENDERS = filter_just_tenders(df)
    '''
                                           
    print('+++ Cleaning TENDER data for TENDERS AND CONTRACT info +++')   
    print(f'TENDERS ORIGINAL size: {len(df)} rows')
                                           
    df = clean_tender_data(df)
    
    print(f'... after cleaning: {len(df)} rows')
    print(f'-----------')
    
    # 1) Get all the TED sources per tender nr and lot
    TED_data = df[df["TED_id"].notnull()]
    TED_data = TED_data.drop_duplicates('TED_id',keep= 'last')
    print(f'Step 1: deduplicate TED data: {len(TED_data)} tenders')
    
    # 2) Get all contracts - these should be all unique
    ## 2.1.) Albanian tenders have a lot of missing values, no sources, no unique identifiers, and can be considered as contracts as they have no lots
    contracts = df[(df["type"] == 'contract') |
                   (df["buyer_country"] == "AL")]
                                           
    contracts = contracts.drop_duplicates(subset=["title", "price", "buyer", "date"])
    
    print(f'Step 2: add contracts: {len(contracts)} contracts')
        
    # 2) Exceptions
    ## 2.1.) Macedonian tenders have contract numbers as tendernr/lot
    mk = df[(df["buyer_country"] == "MK") & (df["type"] != "contract")]
    mk = mk.drop_duplicates(["source", "lot"],keep= 'last')
     
    print(f'Step 3: handle special cases: {len(mk)} tenders')
    

    # 3) Other sources
    # if source and price is the same and it's not a TED tender and not Macedonian or Albanian tender
    other = df[(df["TED_id"].isnull()) & (df["type"] != "contract") & ~(df["buyer_country"].str.contains("MK|AL"))]
    # sometimes the tender is divided in lots withouth this being automatically deducable from the data. We therefore drop here everything that has the same price and source URL. If the source or price is NaN it will treat them as the same string. Also the source string is the same if there is only a general URL or other source. In some of the countries therefore such as AT (data coming from a leak), MD (data coming from a one table) and UA (source url unknown). 
    other = other.drop_duplicates(['price','source'],keep= 'last')
    
    print(f'Step 4: deduplicated other: {len(other)}')
    print(f'-----------')
    
    # join all the filters
    tenders = pd.concat([TED_data, contracts, mk, other])
    
    # drop duplicates - this might remove more tenders than strictly necessary
    tenders = tenders.drop_duplicates(subset=["title","price_EUR","source"])
    
    keep_columns = ['ID', 'product', 'type', 'status', 'published', 'year',
       'date', 'procedure', 'title', 'bids', 'date_until', 'price',
       'price_currency', 'price_EUR', 'buyer','buyer_city','buyer_country','CPV_codes', 'source',
       'description', 'description_EN','date_added']
    
    print(f'Returning: {len(tenders)} rows')
    
    return tenders[keep_columns]
                                           
                                           
def filter_just_companies(df, missing_prices_filled_in_dataset, companies_deduped):
                                           
    '''
    Returns table with companies and amounts they were paid per tender / contract
    
    There are generally 4 types of documents in the data:
    - contract - just 1 seller involved
    - single win tenders - just 1 winner for the whole tender
    - single win lots - tender maybe have multiple lots but just one winner per lot
    - mutli win lots - lots that have multiple winners.
    
    We assign the prices for the particular tender in a new column 'price_contract_EUR'
    
    We then deduplicate the company names
    
    usage:
    COMPANIES = filter_just_companies(df)
    '''
    
    print('')
    print('+++ Cleaning TENDER data for COMPANY details +++')                                       
    print(f'ORIGINAL size: {len(df)} rows')
    df = clean_tender_data(df)
                                           
    print(f'... after cleaning: {len(df)} rows')
    print(f'-----------')
                                            
    # 1) build a new series with contracts prices
    price_contract_EUR = pd.Series()
                                           
    # 1.1) append all prices from contracts
    price_contract_EUR = price_contract_EUR.append(df.loc[df["type"] == "contract", "price_EUR"])
                                              
    # 1.2) lot prices from single win tenders
    for column in ["TED_id", "contract_number"]:
                                           
        # make a dataframe where the column name is filled in and it's index is not a part of the series already
        T = df[(df[column].notnull())  & ~(df.index.isin(price_contract_EUR.index.to_list()))]
        
        # count the occurences of the column in the dataset and get only the column values that have 1 occurence
        match = T[T["type"] == "awarded tender"].groupby(column).count()["product"]
        match = match[match == 1]

        # put these values in a list
        single_win_tenders = match.index.to_list()
        
        # filter out rows where the data matches the values and the price is non zero. Get only the price_EUR and append it to the Series
        filtered = T.loc[(T[column].isin(single_win_tenders)) & (T["price_EUR"].notnull()), "price_EUR"]
        price_contract_EUR = price_contract_EUR.append(filtered)
                                           
                                           
    #  1.3) lot prices from single win lots and put the lot_number_EUR in the overview
    for column in ["TED_id", "contract_number"]:
        
        T = df[(df[column].notnull()) & ~(df.index.isin(price_contract_EUR.index.to_list()))]
                                           
        # the steps are similar but now we are matching on tender ID + lot number
        T["match"] = T.apply(lambda x: f'{x[column]}-{x["lot"]}', axis=1)

        match = T[T["type"] == "awarded tender"].groupby("match").count()["product"]
        match = match[match == 1]
        single_win_tenders = match.index.to_list()
        price_contract_EUR = price_contract_EUR.append(T.loc[(T["match"].isin(single_win_tenders)) & (T["price_lot_EUR"].notnull()) , "price_lot_EUR"])
      
    
    #  1.4) create a new column 'price_contract_EUR' and filter the data:
    df["price_contract_EUR"] = price_contract_EUR
                             
    df = df[['ID','date','product','type','title','lot','buyer_country', 
"supplier",'price_contract_EUR','price_EUR','price_lot_EUR',"supplier_id","supplier_country","supplier_city","supplier_street","supplier_postcode",'procedure','bids','contract_number','TED_id','price','price_currency','price_lot',"source"]]
                                           
    missing = df[(df["price_contract_EUR"].isnull()) & ~(df.index.isin(price_contract_EUR.index.to_list()))]
    df = df[df["price_contract_EUR"].notnull()]

    # 1.5) find tenders that have unique titles and add them to the data
    df = df.set_index("ID")
    missing = missing.set_index("ID")
    missing.drop("price_contract_EUR", axis=1, inplace=True)

    only_one = missing.groupby("title").filter(lambda x: len(x) == 1)['title']
    only_one_tender = missing[missing['title'].isin(only_one)]
    only_one_tender["price_contract_EUR"] = only_one_tender["price_EUR"]
    
    df = df.append(only_one_tender)
                             
    print(f'Step 1: contracts + single win tenders from + single win lots from + unique tenders = {len(df)} winning bids')

    # 2) FILL IN MISSING VALUES - OPTIONAL STEP
    # Load the manually cleaned missing prices data. If a lot was won by multiple companies, we have divided the price evenly between them. Careful: this is certainly not the real division. Sometimes governments contract a pool of suppliers and make individual orders from each one of them. The real division can be found either in the actual contracts or in the financial administration of the buyer. This part was also not used in the publication.
    # We don't need to do this for demonstration purposes, but if you would like to clean the data yourself, uncomment the parts below 
                             
    # missing = missing[~(missing['title'].isin(only_one))]
    # missing.to_csv("companies_prices_missing.csv")
    
    #filled_in = pd.read_csv(missing_prices_filled_in_dataset)
    #print(f'Step 1.2 (Optional): estimated prices for {len(filled_in)} winning bids (price divided equally between tender winners - careful, not the real division)')
                             
   
                             
    # 3) DEDUPLICATE
    # The deduplication was done in OpenRefine (tip: up your memory limits)
    
    #to_dedupe = pd.concat([df, filled_in])
    to_dedupe = df.copy()
    to_dedupe["supplier_clean"] = to_dedupe["supplier"]
    
    # prepare the data for deduplication.
    # We don't need to do this for demonstration purposes, but if you would like to clean the data yourself, uncomment the parts below 
    # to_dedupe = to_dedupe[to_dedupe["supplier"].notnull()]
           
    # to_dedupe["supplier_clean"] = to_dedupe["supplier_clean"].str.lower().str.strip(" ,\:.")
    # to_dedupe["supplier_clean"] = to_dedupe["supplier_clean"].apply(lambda x: cyrtranslit.to_latin(x))
    # to_dedupe["supplier_clean"] = to_dedupe["supplier_clean"].apply(lambda x: re.sub(r" co\. ?ltd$| g\.?m\.?b\.?h$| d\.?o\.?o$| b\.?v$| a\.?s$| s\.?h\.?p\.?k$| s\.?r\.?[l|o]$|^uab | s\.? ?[a|l]\.?$| l\.?d\.?a\.?$| m\.?b\.?h\.?$|^ooo |\'|\"|<\>", "",x ))
    # to_dedupe["supplier_clean"] = to_dedupe["supplier_clean"].str.strip(" ,\.")
                             
    #to_dedupe = to_dedupe.sort_values("supplier_clean").reset_index(drop=True)
                             
    # #Calculate string difference for consecutive rows for visual support while going through 13.000 rows of data
                             
    #diff = 0
    #for n in range(1, len(deduped)):
    #    diff = difflib.SequenceMatcher(None, to_dedupe.loc[n, "supplier_clean"], to_dedupe.loc[n-1, "supplier_clean"]).ratio()
    #    to_dedupe.loc[n,"diff"] = diff
    
    # to_dedupe[["supplier", "supplier_clean"]].to_csv("companies_to_dedupe.csv", index=False)
                             
    deduped = pd.read_csv(companies_deduped).drop_duplicates()
    data = pd.merge(left=to_dedupe.drop("supplier_clean", axis=1), right=deduped, on="supplier")
    print(f'Step 2: manually deduplicated {len(deduped)} company names')
                             
    print(f'-----------')                         
    print(f'Returning: {len(data)} rows')
    print(f'Missing: {len(missing)} winning bids')

    return data                  
                            
                                           
def clean_unitprices(df):
    
    '''
    calculate the **unit price in EUR**
    calculate how much was spent alltogether. (might not always due to various units : packages, bottles of different size etc.)
    put all the category names are now in CAPS
    Keep the uncategorized products, because they most probably are covid-19 related.
    '''
    
    print("")
    print('+++ Cleaning UNIT PRICES data +++')                                       
    print(f'ORIGINAL size: {len(df)} rows')
                                           
    # 1) make these columns into numbers
    df["amount"] = pd.to_numeric(df["amount"], errors='coerce')
    df["unit price"] = pd.to_numeric(df["unit price"], errors='coerce')
                             
    # 2) make date
    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")

    # 3) create an 'unit prices' column with euro prices
    df["unit_price_eur"] = ""
    df["unit_price_eur"] = pd.to_numeric(df.apply(lambda x: x_to_eur(x, "unit price", "currency", "unit_price_eur"), axis=1), errors="coerce")
    
    # 4) create a new column with 'spent' based on unit prices in euro and amounts
    df["spent"] = df["unit_price_eur"] * df["amount"]
    
    # 5) make all categories uppercase
    df["Product category"] = df["Product category"].str.upper().str.strip()
    print(f'Returning: {len(df)} rows')                           

    return df
                                           