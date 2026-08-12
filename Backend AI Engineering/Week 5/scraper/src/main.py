import os
from pathlib import Path #dosya yollarını yonetmek ve klasor olusturmak icin
from urllib.request import Request, urlopen #pythonın yerlesik http istek atma aracları
from urllib.error import URLError, HTTPError #internet baglantısı kopması ya da sitenin hata dondurmesi gibi durumları yakalayıp hata mesajı vermek icin
from urllib.parse import urljoin
import time
from datetime import datetime, timezone
from bs4 import BeautifulSoup
import json
from pydantic import BaseModel, Field, HttpUrl, field_validator


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

BOOKS_CACHE_DIR  = CACHE_DIR / "books"
BOOKS_CACHE_DIR.mkdir(exist_ok=True)

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)
OUTPUT_BOOKS_JSON = OUTPUT_DIR / "books.json"
ERRORS_JSON = OUTPUT_DIR / "errors.json"

#Pydantic seması
class BookRecord(BaseModel):
    title: str
    product_url: HttpUrl
    price : str
    price_gbp : float
    availability: str
    rating : str
    description : str | None = None
    source_page : HttpUrl
    fetched_at : str

    @field_validator("product_url", "source_page", mode = "before")
    def validate_https(cls, v):
        if str(v).startswith("http://"):
            return str(v).replace("http://", "https://", 1)
        return str(v)

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
def run_pipeline():
    current_url = CATALOGUE_PAGE_1_URL #taramaya en baştan yani 1. katalog sayfasından baslar
    all_books_urls = [] #sayfalarda buldugumuz tum kitap linklerini biriktirmek icin bos bir liste

    page_num = 1 #dongunun hangi sayfada dosya adıyla (orn : catalogue-page-2.html) eşleşeceğini takip eder

   #sitenin toplamda 3 sayfa oldugunu bildigimiz icin ve sitenin kendi yonlendirmesi devam ettigi surece bu dongu calısacak 
    while current_url and page_num <=3: 
        cache_path = CACHE_DIR / f"catalogue-page-{page_num}.html" #her sayfanın cachedeki dosya yolu belirlenir
        html_content, from_cache = fetch_page(current_url, cache_path) #sayfanın html icerigi elde edilir ve verinin cacheden gelip gelmedigi bilgisi alınır 
        if not html_content:
            break
        
        source_page_url = current_url
        #BeautifulSoup ile html'i parse edelim ve kitap linklerini toplayalım
        b_soup = BeautifulSoup(html_content, "html.parser") #gelen ham htm metni pythonın inceleyebilecegi yapıya cevirir 
        
        #kitap linklerini bulalım
        books = b_soup.select("article.product_pod h3 a") #bu secisi ile sayfadaki tum kitap kartları icindeki baslık ve link etiketlerini secer
        for book in books:
            r_href = book.get("href") #relative url href
            #urljoin ile mutlak url'e çevirelim
            absolute_url = urljoin(current_url, r_href)
            all_books_urls.append((absolute_url, source_page_url))

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
    
    #duplicate olan linkleri temizleyelim (url'e göre benzersiz yapalım)
    #Canonical url ile temizleyeceğz
    unique_book_urls = {}
    for book_url, source_page in all_books_urls:
        cannonical_url = book_url.replace("http://", "https://")
        if cannonical_url not in unique_book_urls:
            unique_book_urls[cannonical_url] = source_page    

    valid_records = []       
    error_records = []

    #her bir kitap detay sayfasına gidelim ve verileri toplayalım
    for index, (book_url, source_page) in enumerate(unique_book_urls.items(), start=1):
        book_cache_path = BOOKS_CACHE_DIR / f"book-{index}.html"
        html_content, from_cache = fetch_page(book_url, book_cache_path)
        if not html_content:
            continue
        fetched_at_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")

        #kitap detay sayfasındaki bilgileri toplayalım
        b_soup = BeautifulSoup(html_content, "html.parser")

        #Title - kitap adı
        title_element = b_soup.select_one("div.product_main h1") #belrtilen css secicisine uyan sayfadaki ilk html etiketini bulur
        if title_element: #aranan etiket sayfada bulunursa
            title = title_element.get_text(strip=True) #bulunan html etiketinin arasındaki saf metin icerigini alır ve basındakisonundaki boslukları temizler
        else:
            title = None
        
        #price text- fiyat metni
        price_element = b_soup.select_one("div.product_main p.price_color")
        if price_element:
            price = price_element.get_text(strip=True)
        else:
            price = None
        
        #price orn "£51.77" -> prive_gbp (51.77) olacak 
        price_gbp = None
        if price:
            try:
                price_gbp = float(price.replace("£", "").strip())
            except ValueError:
                pass
        

        #availability text - stok durumu
        availability_element = b_soup.select_one("div.product_main p.instock.availability")   
        if availability_element:
            availability = availability_element.get_text(strip=True)
        else:
            availability = None
        
        #Rating text-class adından yakalanıyor
        rating_element = b_soup.select_one("div.product_main p.star-rating")
        rating_text = None
        if rating_element:
            classes = rating_element.get("class", [])
            #örn: ['star-rating', 'Three'] -> ikinci eleman rating'i verir
            if len(classes) > 1:
                rating_text = classes[1]
        
        #Description (bazı kitaplarda olmayabilir onlar null olacak)
        description_element = b_soup.select_one("#product_description ~ p")
        if description_element:
            description = description_element.get_text(strip=True)
        else:
            description = None

        raw_d = { 
            "title": title,
            "product_url": book_url,
            "price": price,
            "price_gbp" : price_gbp,
            "availability": availability,
            "rating": rating_text,
            "description": description,
            "source_page": source_page,
            "fetched_at": fetched_at_str,
        }
        
        #pydantic ile dogrulama-validation
        try:
            validated_record = BookRecord(**raw_d)
            valid_records.append(validated_record.model_dump(mode="json"))
        except Exception as e:
            error_records.append({"raw_data": raw_d, "error": str(e)})
        
        #gerçek isteklerde en az yarım saniye bekle (cacheden gelmediyse)
        if not from_cache:
            time.sleep(0.5)
        
    #dosyaları kaydedelim
    OUTPUT_BOOKS_JSON.write_text(json.dumps(valid_records, indent=4, ensure_ascii=False), encoding="utf-8")
    if error_records:
        ERRORS_JSON.write_text(json.dumps(error_records, indent=4, ensure_ascii=False), encoding="utf-8")
    print(f"CHECKPOINT — books.json has {len(valid_records)} records, errors={len(error_records)}")



if __name__ == "__main__":
    run_pipeline()