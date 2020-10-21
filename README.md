# Europen COVID-19 spending 2020

OCCRP and media partners collected data on COVID-19 related spending from across Europe from February to October this year.
The story analyzing the data can be found [here]().

We have also decided to share the raw data with the public.

In this notebook, we will clean the data for analysis and explain some of the features and caveats of the data along the way. We have collected data into **two data sets**: tenders and contracts, and unit prices.


## Source data sets

### 1. TENDERS

This dataset contains information on contracts and tenders related to COVID-19. This information can be found [here](https://docs.google.com/spreadsheets/d/1VXURZlKH-_GeNvPrytgJOeTUH3hXf0r_veIXWJp1K20/edit?usp=sharing).
A quick note here on the difference between contracts and tenders. Where as contracts typically cover a simple, one-off purchase from a single company, tenders are often divided into multiple parts, or “lots”, with more than one company acting as supplier.
This means there is sometimes duplication in this data. The data is structured around companies (i.e. one row = one winning company). If a tender has multiple winning companies, that means it spans over multiple rows.

We have also made an effort to categorize each tender or contract (visible in the `product` column), in order to filter out those not related to COVID-19, and to make it easier to compare different deals with each other. This process was done with a mix of manual edits and automation, meaning that there may be mistakes.


### 2. UNIT PRICES

This dataset contains information on the prices paid per unit for certain COVID-19 purchases. The information can also be found in the [Unit Prices Sheet](https://docs.google.com/spreadsheets/d/10VL5FpviSXctagcoQM_pr0xP4Lsmzzc3-i7mEyCE2kw/edit?usp=sharing). 
This data comes from multiple sources. In Ukraine, for example, data came from the [Prozorro](https://prozorro.gov.ua/en/tender/search/) procurement platform. In Portugal, data was obtained from the government and filtered and categorized by our media partner [Publico](https://www.publico.pt). Czech data was filtered by [hlidacstatu.cz](https://www.hlidacstatu.cz/).
Most of the time there is a reference to a source and an ID corresponding to the relevant tender or contract.
