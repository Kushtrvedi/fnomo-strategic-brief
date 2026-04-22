import os
import asyncio
from playwright.async_api import async_playwright
import sys

async def generate_pdf():
    # Define paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    html_path = os.path.join(base_dir, 'brief.html')
    output_path = os.path.join(base_dir, 'Fnomo_Strategic_Brief_V3_1.pdf')

    print(f"Loading HTML from {html_path}...")
    
    if not os.path.exists(html_path):
        print(f"Error: {html_path} not found.")
        sys.exit(1)

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Load the HTML file
            file_url = f"file:///{html_path}".replace('\\', '/')
            await page.goto(file_url, wait_until="networkidle")
            
            # Print to PDF
            await page.pdf(
                path=output_path,
                format="A4",
                print_background=True,
                margin={"top": "0px", "right": "0px", "bottom": "0px", "left": "0px"}
            )
            
            await browser.close()
            
        print(f"Successfully generated PDF at: {output_path}")
        return output_path
    except Exception as e:
        print(f"Error generating PDF: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(generate_pdf())
