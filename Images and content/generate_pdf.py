import asyncio
from playwright.async_api import async_playwright
import os

async def generate_pdf():
    desktop_path = os.path.join(os.environ['USERPROFILE'], 'Desktop')
    output_pdf = os.path.join(desktop_path, 'FNOMO_Strategic_Partnership_Brief.pdf')
    html_file = r'd:\Antigravity\eigent\Downloads\fnomo\FNOMO — Institutional Firewall for Retail Capital\preview_cinematic.html'
    html_file_forward = html_file.replace("\\", "/")
    file_url = f'file:///{html_file_forward}'

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        # Emulate screen to keep the cinematic dark theme
        await page.emulate_media(media="screen")
        
        print(f"Navigating to {file_url}...")
        await page.goto(file_url, wait_until="load", timeout=60000)
        
        # Wait for the main container to ensure content is there
        await page.wait_for_selector("#brief-content")
        
        # Give extra time for fonts to render
        await asyncio.sleep(5)
        
        print(f"Generating PDF to {output_pdf}...")
        await page.pdf(
            path=output_pdf,
            format="Letter",
            print_background=True,
            margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
            display_header_footer=False
        )
        
        await browser.close()
        print("Success! PDF created on Desktop.")

if __name__ == "__main__":
    asyncio.run(generate_pdf())
