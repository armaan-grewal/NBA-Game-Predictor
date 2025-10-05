
# %%
import os 
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
import time
import asyncio

# %%
SEASONS = list(range(2018, 2026)) 


# %%
DATA_DIR = "data"
STANDINGS_DIR = os.path.join(DATA_DIR, "standings")
SCORES_DIR = os.path.join(DATA_DIR, "scores")


# %%
async def get_html(url, selector, sleep=3, retries=3):
    html = None

    for i in range(1, retries+1):
        await asyncio.sleep((sleep * i)) #sleep longer with more retries

        try:
            async with async_playwright() as brows:
                browser = await brows.chromium.launch()   #await makes it syncronus and tells it to wait cuz of async
                page = await browser.new_page()
                await page.goto(url)
                print(await page.title())

                html = await page.inner_html(selector)
                break

        except PlaywrightTimeout:
            print(f"Timeout error on {url}")
            continue

    return html
        


# %%
async def scrape_season(season):
    url = f"https://www.basketball-reference.com/leagues/NBA_{season}_games.html"
    # use # to find the unique element with id of 'content', within that find for class filter
    html = await get_html(url, "#content .filter")


    soup = BeautifulSoup(html, "html.parser")
    links = soup.find_all("a")
    href = [link["href"]for link in links]
    standings_pages = [f"https://basketball-reference.com{link}" for link in href]


    for url in standings_pages:
        save_path = os.path.join(STANDINGS_DIR, url.split("/")[-1]) #last part for naming purposes
        #if it exists continue
        if os.path.exists(save_path):
            continue


        html = await get_html(url, "#all_schedule")
        
        if html is not None:
            with open(save_path, "w+") as f:
                f.write(html)

        else:
            print(f"Failed to scrape {url}")
            continue
                              

    



# %%
async def scrape_game(standings_file):
    with open(standings_file, 'r') as f:
        html = f.read()
    
    soup = BeautifulSoup(html)
    links = soup.find_all("a")
    
    #use .get now because first line has a attribute without href, link["href"] will throw error
    href = [link.get("href") for link in links]    #get all <a> attributes then all href show in line below
    
    box_score = [link for link in href if link and "boxscore" in link and ".html" in link]
    
    box_score = [f"https://basketball-reference.com{link}" for link in box_score]
    box_score
    for url in box_score:
        save_path = os.path.join(SCORES_DIR, url.split("/")[-1])
        if os.path.exists(save_path):
            continue
    
        html = await get_html(url, "#content")
    
        #if retries fail
        if html is None:
            continue
    
        with open(save_path, "+w") as f:
            f.write(html)




async def main():

    # %%
    #scrape all seasons
    for season in SEASONS:
        await scrape_season(season)

    # %%
    standings_files_all = os.listdir(STANDINGS_DIR)

    # %%
    standings_files_all = [s for s in standings_files_all if ".html" in s]
    for file in standings_files_all:
        filepath = os.path.join(STANDINGS_DIR, file)
        await scrape_game(filepath)


if __name__ == "__main__":
    asyncio.run(main())