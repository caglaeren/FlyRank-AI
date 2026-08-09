import os
from pathlib import Path #dosya yollarını yonetmek ve klasor olusturmak icin
from urllib.request import Request, urlopen #pythonın yerlesik http istek atma aracları
from urllib.error import URLError, HTTPError #internet baglantısı kopması ya da sitenin hata dondurmesi gibi durumları yakalayıp hata mesajı vermek icin
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

def fetch_first_catalogue_page():
    #cache (onbellek) kontrolu
    if CATALOGUE_PAGE_1_CACHE.exists():
        html_content = CATALOGUE_PAGE_1_CACHE.read_text(encoding="utf-8")
        print(f"CACHE HIT - Response size: {len(html_content)} bytes")
        return html_content
    
    #Cache (onbellekte) yoksa internetten cekip gercekten indir
    request = Request(CATALOGUE_PAGE_1_URL, headers={"User-Agent": USER_AGENT})
    try:
        with urlopen(request, timeout = TIME_OUT) as response:
            status = response.status
            if status != 200:
                raise RuntimeError(f"Unexpected status code: {status}")
            html_content = response.read().decode("utf-8", errors="replace")
    except HTTPError as e:
        raise RuntimeError(f"HTTP Error {e.code}") from e
        return None
    except URLError as e:
        raise RuntimeError(f"URL Error {e.reason}") from e
        return None
    except TimeoutError:
        print("Request timed out.")
        return None
    #Cache olustur ve kaydet
    CATALOGUE_PAGE_1_CACHE.write_text(html_content, encoding="utf-8")
    print(f"FETCH - Response size: {len(html_content)} bytes")
    return html_content


if __name__ == "__main__":
    fetch_first_catalogue_page()