from django.http import JsonResponse
from django.views import View
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime
from .models import EntitiesMaster
import json,logging,re
from langchain_anthropic import ChatAnthropic
from langchain.chains import LLMChain
from langchain_core.prompts import PromptTemplate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# DATA FETCHING USING SELENIUM
# class SaveEntityView(View):
#     def get(self, request):
#         url = request.GET.get('url')
#         driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
#         driver.get(url)
#         location_element = WebDriverWait(driver, 20).until(
#             EC.presence_of_element_located((By.CSS_SELECTOR, 'p.location.subhead6'))
#         )
#         auditorium = location_element.text.strip()
#         h1_element = driver.find_element(By.CSS_SELECTOR, 'h1')
#         program_name = h1_element.text.strip()
#         date_time_element = driver.find_element(By.CSS_SELECTOR, 'p.body-text3')
#         date_time = date_time_element.text.strip()

#         date_time_parts = re.split(r'\s+at\s+', date_time)
#         if len(date_time_parts) == 2:
#             date_str = date_time_parts[0]
#             time_str = date_time_parts[1]
#             date = datetime.strptime(date_str, '%a, %b %d, %Y').date()
#             time = datetime.strptime(time_str, '%I:%M%p').time()
#         else:
#             date = None
#             time = None
#         artist_elements = driver.find_elements(By.CLASS_NAME, 'event-detail-artist')
#         artists = []
#         for artist in artist_elements:
#             name_element = artist.find_element(By.CSS_SELECTOR, 'p.subhead4 a')
#             role_element = artist.find_element(By.CSS_SELECTOR, 'p.subhead6')
#             name = name_element.text.strip()
#             role = role_element.text.strip()
#             artists.append({'name': name, 'role': role})

#         EntitiesMaster.objects.create(
#             auditorium=auditorium,
#             date_time=date_time,
#             program_name=program_name,
#             artists=artists
#         )

#         return JsonResponse({
#             'message': 'Entities saved successfully',
#             'auditorium': auditorium,
#             'date_time': date_time,
#             'program_name': program_name,
#             'artists': artists,
#             'date': date.isoformat() if date else None,
#             'time': time.isoformat() if time else None,
#         }, status=200)    

class SaveEntityView(View):
    def get(self, request):
        try:
            url = request.GET.get('url')
            if not url:
                return JsonResponse({'error': 'URL parameter is required'}, status=400)

            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
            driver.get(url)
            location_element = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'p.location.subhead6'))
            )
            auditorium = location_element.text.strip()
            h1_element = driver.find_element(By.CSS_SELECTOR, 'h1')
            program_name = h1_element.text.strip()
            date_time_element = driver.find_element(By.CSS_SELECTOR, 'p.body-text3')
            date_time = date_time_element.text.strip()

            date_time_parts = re.split(r'\s+at\s+', date_time)
            if len(date_time_parts) == 2:
                date_str = date_time_parts[0]
                time_str = date_time_parts[1]
                date = datetime.strptime(date_str, '%a, %b %d, %Y').date()
                time = datetime.strptime(time_str, '%I:%M%p').time()
            else:
                date = None
                time = None
            artist_elements = driver.find_elements(By.CLASS_NAME, 'event-detail-artist')
            artists = []
            for artist in artist_elements:
                name_element = artist.find_element(By.CSS_SELECTOR, 'p.subhead4 a')
                role_element = artist.find_element(By.CSS_SELECTOR, 'p.subhead6')
                name = name_element.text.strip()
                role = role_element.text.strip()
                artists.append({'name': name, 'role': role})
            driver.quit()
            logger.info(f"Extracted data: Auditorium: {auditorium}, Program Name: {program_name}, Date and Time: {date_time}, Artists: {artists}")

            # Use LangChain and LLM for additional processing
            anthropic_llm = ChatAnthropic(api_key="ANTHROPIC_API_KEY----", model_name="Claude 3 Haiku")
            prompt = PromptTemplate(
                input_variables=["auditorium", "date_time", "program_name", "artists"],
                template="""
                Given the following information about an event:
                Auditorium: {auditorium}
                Date and Time: {date_time}
                Program Name: {program_name}
                Artists: {artists}
                 You are a data transformer. You will take the following event data and clean, validate, and enhance it.
                The input data includes: {data}
                1. Clean any typos or inconsistencies in artist names and auditorium.
                2. Ensure the date and time are in the correct format.
                3. Generate a summary of the event.
                4. Suggest any missing or incorrect information.
                Respond with a JSON object including cleaned data and the summary.
                """,
                
            )
            llm_chain = LLMChain(llm=anthropic_llm, prompt=prompt)
            enhanced_data = llm_chain.run({
                "auditorium": auditorium,
                "date_time": date_time,
                "program_name": program_name,
                "artists": artists
            })
            logger.info(f"Enhanced data: {enhanced_data}")
            enhanced_data = json.loads(enhanced_data)

            EntitiesMaster.objects.create(
                auditorium=enhanced_data['auditorium'],
                date_time=enhanced_data['date_time'],
                program_name=enhanced_data['program_name'],
                artists=enhanced_data['artists']
            )
            return JsonResponse({
                'message': 'Entities saved successfully',
                'data': enhanced_data
            }, status=200)

        except Exception as e:
            logger.error(f"Error occurred: {e}", exc_info=True)
            return JsonResponse({'error': str(e)}, status=500)
