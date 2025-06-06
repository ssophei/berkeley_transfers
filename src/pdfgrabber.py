import time
import urllib.request
import urllib.parse
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import base64

class PDFGrabber():
    def __init__(self, school_id=79, major='Computer Science, B.A.', major_nickname='CS', delay=0.5):
        self.school_id = school_id
        self.major = major
        self.major_nickname = major_nickname
        self.delay = delay
    
    def get_agreements(self):
        with urllib.request.urlopen(f'https://assist.org/api/institutions/{self.school_id}/agreements') as url:
            data = json.loads(url.read().decode())
        agreement_list = []
        for agreement in list(data):
            if agreement['isCommunityCollege']:
                school_id = agreement['institutionParentId']
                year = agreement['sendingYearIds'][-1]
                curr = {'id': school_id, 'year': year}
                agreement_list.append(curr)
        print('list of agreements found!')
        return agreement_list
    
    def get_keys(self):
        agreement_list = self.get_agreements()
        keys = []
        for agreement in agreement_list:
            time.sleep(self.delay)
            school_id, year = agreement['id'], agreement['year']
            with urllib.request.urlopen(f'https://assist.org/api/agreements?receivingInstitutionId={self.school_id}'
                                        f'&sendingInstitutionId={school_id}'
                                        f'&academicYearId={year}'
                                        f'&categoryCode=major') as url:
                data = json.loads(url.read().decode())
            data = data['reports']
            for report in list(data):
                if report['label'] == self.major:
                    curr = {'key': report['key'], 'school_id': school_id, 'year': year}
                    keys.append(curr)
                    print(curr)
        with open(f'keys/{self.school_id}_{self.major_nickname}_keys.json', 'w') as outfile:
            json.dump(keys, outfile)
        return keys
    
    def get_pdfs(self):
        with open(f'keys/{self.school_id}_{self.major_nickname}_keys.json', 'r') as infile:
            keys = json.load(infile)
        id_to_key = {} # helps remove duplicates
        options = Options()
        options.add_argument('--headless')
        driver = webdriver.Chrome(options=options)
        for key in keys:
            if key['key'] not in id_to_key.values():
                key_val = key['key']
                school_id = key['school_id']
                year = key['year']
                id_to_key[school_id] = key_val
                encoded_key = urllib.parse.quote(key_val, safe='')
                agreement_url = (f'https://assist.org/transfer/results?year={year}'
                f'[&institution={self.school_id}&agreement={school_id}'
                f'&agreementType=from&viewAgreementsOptions=true&view=agreement&viewBy=major&viewSendingAgreements=false'
                f'&viewByKey={encoded_key}')
                driver.get(agreement_url)
                time.sleep(5)
                pdf = driver.print_page()
                pdf_bytes = base64.b64decode(pdf)
                with open(f'pdfs/{self.major_nickname}/'
                          f'to{self.school_id}_{self.major_nickname}_from{school_id}_in{year}.pdf', 'wb') as file:
                    file.write(pdf_bytes)
                print(f'{self.major_nickname} agreement from {1950 + year} saved!'
                      f'(receiving: {self.school_id}, sending: {school_id})')
        driver.quit
        return id_to_key
