import requests
from bs4 import BeautifulSoup


def parseSitemap(url):
    r = requests.get(url)
    xml = r.text
    url_list = []

    soup = BeautifulSoup(xml, features="xml")
    sitemap_tags = soup.find_all("url")

    for sitemap in sitemap_tags:
        url = sitemap.findNext("loc").text
        if url[-5:] == ".html":
            url_list.append(url)
    return url_list
