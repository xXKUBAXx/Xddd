import asyncio
import aiohttp
from django.views import View
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from ..models import primislaoDomains, vdTarget, primislaoLinks
from asgiref.sync import sync_to_async
import json
from datetime import date
import re

@method_decorator(csrf_exempt, name='dispatch')
class PanelPrimislao(View):
    async def post(self, request):
        try:
            data = json.loads(request.body)
            # print(f"Received data: {data}")
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)
        
        user_id, user_mail = await sync_to_async(check_user)(request)
             

        response_data = {}
        
        link_counter = 0

        for i in data:
            for _ in data[i]:
                link_counter +=1

        global task_id
        task_id = await sync_to_async(primislaoLinks.objects.order_by, thread_sensitive=False)('task_id')
        task_id = await sync_to_async(task_id.last, thread_sensitive=False)()
        try:
            task_id = task_id.task_id + 1
        except AttributeError:
            task_id = 1

        print(f'{user_mail} ordered {link_counter-len(data)} primislao links from {len(data)} domains')

        async def process_domain(domain_name, domain_data_list):
            # print(f"Processing domain: {domain_name}")
            domain_name = await clean_domain_name(domain_name)
            domain = await sync_to_async(primislaoDomains.objects.filter(domain_name=domain_name).first, thread_sensitive=False)()
            # print(f"Domain object for {domain_name}: {domain}")
            if domain:
                server_name = domain.server_name
                response_data[domain_name] = {
                    'server_name': server_name,
                    'plugin_domain': None,
                    'data': []
                }

                vd_target = await sync_to_async(vdTarget.objects.filter(server_name=server_name).first, thread_sensitive=False)()
                # print(f"vdTarget object for {server_name}: {vd_target}")
                if vd_target:
                    response_data[domain_name]['plugin_domain'] = vd_target.plugin_domain

                    async with aiohttp.ClientSession() as session:
                        for domain_data in domain_data_list:
                            if not all(domain_data.values()):
                                continue
                            # print(f"Sending request for domain: {domain_name}")
                            try:
                                async with session.post(
                                    url=f"https://{vd_target.plugin_domain}/Lokalizacje.php",
                                    params={
                                        'do': 'dodaj',
                                        'katalog': domain_name
                                    },
                                    headers={
                                        'User-Agent': 'dodawanie linkow'
                                    },
                                    data={
                                        'D[link]': domain_data['url'],
                                        'D[anchor]': domain_data['anchor'],
                                        'D[limit]': domain_data['limit'],
                                        'D[nofollow]': domain_data['nofollow']
                                    }
                                ) as response:
                                    await asyncio.sleep(2)

                                    link_id = await check_if_links_exist(domain_name, vd_target.plugin_domain, domain_data['url'])
                                    domain_data['link_id'] = link_id

                                    await sync_to_async(save_to_database, thread_sensitive=False)(user_mail, domain_name, domain_data)

                            except aiohttp.ClientError as e:
                                print(f"Error occurred while sending request for domain: {domain_name}")
                                print(f"Error details: {str(e)}")

                            response_data[domain_name]['data'].append(domain_data)
            else:
                print(f"Domain not found: {domain_name}")
                response_data[domain_name] = {
                    'server_name': None,
                    'plugin_domain': None,
                    'data': domain_data_list
                }

        tasks = []
        for domain_name, domain_data_list in data.items():
            tasks.append(asyncio.create_task(process_domain(domain_name, domain_data_list)))

        await asyncio.gather(*tasks)

        # print(f"Response data: {response_data}")
        return JsonResponse({'message': 'Data processed successfully', 'data': response_data})

    async def get(self, request):
        return JsonResponse({'error': 'GET method not allowed'}, status=405)
    
def check_user(request):
    user = request.user
    if user.is_authenticated:
        return user.id, user.email
    else:
        return None
    
    
def save_to_database(user_mail, domain_name, domain_data):
    primislaoLinks.objects.create(
        task_id = task_id,
        user=user_mail,
        link_domain=domain_name,
        target_domain=domain_data['url'],
        anchor=domain_data['anchor'],
        nofollow=domain_data['nofollow'],
        limit=domain_data['limit'],
        link_id=domain_data['link_id'],
        link_data = date.today()
    )
    
async def check_if_links_exist(domain_name, plugin_domain, target_url):
    async with aiohttp.ClientSession() as session:
        async with session.get(
            url=f"https://{plugin_domain}/Lokalizacje.php",
            params={
                'do': 'linki',
                'katalog': domain_name
            }
        ) as response:
            content = await response.text()
            links_data = parse_links_data(content)

            for link_data in reversed(links_data):
                if link_data[1] == target_url or link_data[2] == target_url:
                    return link_data[0]
            return None

def parse_links_data(content):
    links_data = []
    try:
        data = json.loads(content.strip())
        for item in data:
            if isinstance(item, list) and len(item) >= 5:
                links_data.append(item)
    except json.JSONDecodeError:
        pass
    return links_data

async def clean_domain_name(domain):
    if domain.startswith("https://"):
        domain = domain[8:]
    elif domain.startswith("http://"):
        domain = domain[7:]
    if domain.startswith("www."):
        domain = domain[4:]
    if domain.endswith("/"):
        domain = domain[:-1]
    return domain