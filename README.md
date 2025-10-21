# Web Scraper – Greffe des Associations (Service-Public Annuaire)

This project is a Selenium-based web scraper that collects public data from the French government directory — specifically from listings of Greffe des associations (registrars of associations).

It automates browser actions to navigate through search results, open detailed pages, and extract structured information such as contact details, addresses, and regions.

## Objective

The goal of this scraper is to build a complete dataset of association registries across France, for research, visualization, or administrative analysis.  
It replaces tedious manual collection by automatically browsing and parsing the directory.

## Features

- Performs automated searches for “Greffe des associations” on Service-Public Annuaire
- Handles pagination to scrape all pages of results
- Opens each result’s detail page to extract key data fields
- Exports the scraped data to CSV
- Includes error handling, waits, and retry mechanisms for stability
- Uses `time.sleep()` or `WebDriverWait` to avoid overloading the site
- Cleans and formats the output for analysis or reuse

## Data Extracted

For each “Greffe des associations” entry, the scraper retrieves:

- Name of the office
- Department / Region / City
- Address
- Phone number
- Email (if available)
- Website link (if available)
- Opening hours / additional notes (if present)
### Website link
  https://lannuaire.service-public.gouv.fr/recherche?whoWhat=Greffe+des+associations
