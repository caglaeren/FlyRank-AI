import os
from pathlib import Path #dosya yollarını yonetmek ve klasor olusturmak icin
from urllib.request import Request, urlopen #pythonın yerlesik http istek atma aracları
from urllib.error import URLError, HTTPError #internet baglantısı kopması ya da sitenin hata dondurmesi gibi durumları yakalayıp hata mesajı vermek icin
from urllib.parse import urljoin
import time
from bs4 import BeautifulSoup


#Request -> user-agent headırını eklemek icin
#urlopen -> istegi gonderiyorum

BASE_URL = "https://books.toscrape.com/"
CATALOGUE_PAGE_1_URL = BASE_URL + "catalogue/page-1.html" #ilk katalog sayfasi ana sayfasıdır


#Kendini tanıtan doğru bir user-agent
USER_AGENT = "FlyRankInternship-A9/1.0 (+https://github.com/caglaeren/FlyRank-AI/tree/main/Backend%20AI%20Engineering/Week%205/scraper)"
TIME_OUT = 10


CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True)

CATALOGUE_PAGE_1_CACHE = CACHE_DIR / "catalogue-page-1.html"

def fetch_page(url, cache_path):
    #belirli bir url'i cacheden veya internetten ceker
    if cache_path.exists():
        html_content = cache_path.read_text(encoding="utf-8")
        print(f"CACHE HIT ({cache_path.name}) - Response size: {len(html_content)} bytes")
        return html_content, True # True cacheden gelir
    
    #Cache (onbellekte) yoksa internetten cekip gercekten indir
    request = Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urlopen(request, timeout = TIME_OUT) as response:
            status = response.status
            if status != 200:
                raise RuntimeError(f"Unexpected status code: {status}")
            html_content = response.read().decode("utf-8", errors="replace")
    except HTTPError as e:
        raise RuntimeError(f"HTTP Error {e.code}") from e
    except URLError as e:
        raise RuntimeError(f"URL Error {e.reason}") from e
    except TimeoutError:
        print("Request timed out.")
        return None, False
    #Cache olustur ve kaydet
    cache_path.write_text(html_content, encoding="utf-8")
    print(f"FETCH ({cache_path.name}) - Response size: {len(html_content)} bytes")
    return html_content, False # False -> internetten indirildi

#tarama, 3 sayfalık katalog yapısını bastan sona yonetir.
def scan_catalogue():
    current_url = CATALOGUE_PAGE_1_URL #taramaya en baştan yani 1. katalog sayfasından baslar
    catalogue_pages = 0 #gezilen sayfa sayısını sayan sayac
    all_books_urls = [] #sayfalarda buldugumuz tum kitap linklerini biriktirmek icin bos bir liste

    page_num = 1 #dongunun hangi sayfada dosya adıyla (orn : catalogue-page-2.html) eşleşeceğini takip eder

   #sitenin toplamda 3 sayfa oldugunu bildigimiz icin ve sitenin kendi yonlendirmesi devam ettigi surece bu dongu calısacak 
    while current_url and page_num <=3: 
        cache_path = CACHE_DIR / f"catalogue-page-{page_num}.html" #her sayfanın cachedeki dosya yolu belirlenir
        html_content, from_cache = fetch_page(current_url, cache_path) #sayfanın html icerigi elde edilir ve verinin cacheden gelip gelmedigi bilgisi alınır 
        if not html_content:
            break
        
        catalogue_pages += 1

        #BeautifulSoup ile html'i parse edelim ve kitap linklerini toplayalım
        b_soup = BeautifulSoup(html_content, "html.parser") #gelen ham htm metni pythonın inceleyebilecegi yapıya cevirir 
        #kitap linklerini bulalım
        books = b_soup.select("article.product_pod h3 a") #bu secisi ile sayfadaki tum kitap kartları icindeki baslık ve link etiketlerini secer
        for book in books:
            r_href = book.get("href") #relative url href
            #urljoin ile mutlak url'e çevirelim
            absolute_url = urljoin(current_url, r_href)
            all_books_urls.append(absolute_url)

        #sonraki sayfaya gidelim , next butonunu bulalım
        next_page_link = b_soup.select_one("li.next > a") #sayfada next butonu olup olmadıgını kontrol eder
        if next_page_link: #eger next butonu varsa
            next_href = next_page_link.get("href")
            current_url = urljoin(current_url, next_href) #sonraki sayfanın tam adresi olusturulur
            page_num += 1

            #gerçek isteklerde en az yarım saniye bekle (cacheden gelmediyse)
            if not from_cache:
                time.sleep(0.5)
        else:
            current_url = None
    
    #duplicate olan linkleri temizleyelim
    unique_urls = list(set(all_books_urls))
    print(f"\nCHECKPOINT — catalogue_pages={catalogue_pages}, discovered={len(all_books_urls)}, unique_urls={len(unique_urls)}")

        




if __name__ == "__main__":
    scan_catalogue()