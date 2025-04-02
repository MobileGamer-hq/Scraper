from django.shortcuts import render
from django.http import JsonResponse
from .scraper import Crawler

def scrape_products(request):
    search_query = request.GET.get("query", "laptop")  # Default to "laptop"
    sort_order = request.GET.get("sort", "relevance")

    # Initialize and run the scraper
    urls = [Crawler.convert_search_to_url(search_query, sort=sort_order)]
    crawler = Crawler(urls)
    products = crawler.scrape_single_product(urls[0])
    crawler.close()

    # Return JSON response
    return JsonResponse(products, safe=False)

