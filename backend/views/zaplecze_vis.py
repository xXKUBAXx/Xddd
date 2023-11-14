from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

import requests
import json
import os
import datetime
import time

@method_decorator(csrf_exempt, name='dispatch')
class ZapleczeVisibility(View):
    
    def post(self, request):

        data = json.loads(request.body)
        services_token = data.get('semstorm_key') 

        # prod
        list_of_domains = get_list_of_zaplecza("../zaplecza.tsv")
        list_of_domains = [i.lower() for i in list_of_domains]
        temporary_list_of_domains = []

        # test server
        # list_of_domains = get_list_of_zaplecza("../../zaplecza_temp.tsv")

        controller = 0
        full_lenght = len(list_of_domains)
        while True:
            
            temporary_list_of_domains = list_of_domains[:5]

            if len(list_of_domains) > 0:
                controller += len(temporary_list_of_domains)
                
                list_of_domains = list(set(list_of_domains)-set(temporary_list_of_domains))
                # list_of_domains.sort()
                vis_data = get_basic_stats(temporary_list_of_domains, services_token)
                for item in temporary_list_of_domains:

                    # prod
                    save_to_tsv(item, vis_data, "../visibility_data.tsv")

                    # test server
                    # save_to_tsv(item, vis_data, "../../visibility_data.tsv")
                
                print(f'Done {controller} out of {full_lenght}')
                temporary_list_of_domains = []
                # time.sleep(1)
                    
            else:
                return JsonResponse({"message": f"Baza widoczności została zaktualizowana - Sprawdzono {controller} Zaplecz"})
                break
        



    def get(self, request, *args, **kwargs):
        return JsonResponse({"error": "Nieprawidłowa metoda żądania."}, status=400)
    
def get_list_of_zaplecza(filename):
    backlink_addresses = []

    with open(filename, 'r', encoding="utf-8") as file:
        next(file)
        for line in file:
            parts = line.strip().split('\t')
            if len(parts) > 1:
                backlink_addresses.append(parts[1])

    return backlink_addresses 
    
     
   
def get_basic_stats(domain, services_token):
        url = 'https://api.semstorm.com/api-v3/explorer/explorer-keywords/basic-stats.json'
        params = {
            'services_token': services_token
        }
        headers = {
            'Content-Type': 'application/json'
        }
        payload = {
            'domains': domain
        }

        response = requests.post(url, params=params, headers=headers, data=json.dumps(payload))

        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: {response.status_code}, Message: {response.text}")
            return None
        
def save_to_tsv(domain, stats, filename):
        today = datetime.datetime.now().strftime("%d-%m-%Y")

        new_data_line = {
            "top3": f"{stats['results'][domain]['keywords_top_3']}",
            "top10": f"{stats['results'][domain]['keywords_top']}",
            "top50": f"{stats['results'][domain]['keywords']}"
        }

        today = datetime.datetime.now().strftime("%Y-%m-%d")

        if filename:
            with open(filename, "r") as file:
                lines = file.readlines()

            updated = False
            for i, line in enumerate(lines):
                if line.startswith(domain):
                    parts = line.strip().split("\t")
                    if today not in parts[1]:
        
                        new_line = [domain, today] + [new_data_line[key] for key in ['top3', 'top10', 'top50']]
                        lines.append("\t".join(new_line) + "\n")
                        updated = True
                        break

            if not updated:
                new_line = [domain, today] + [new_data_line[key] for key in ['top3', 'top10', 'top50']]
                lines.append("\t".join(new_line) + "\n")

        else:

            header = "domain\tdate\ttop3\ttop10\ttop50\n"
            new_line = [domain, today] + [new_data_line[key] for key in ['top3', 'top10', 'top50']]
            lines = [header, "\t".join(new_line) + "\n"]

        with open(filename, "w") as file:
            file.writelines(lines)
