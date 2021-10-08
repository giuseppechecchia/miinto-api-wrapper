import requests
import json
import hashlib
import hmac

import time
from datetime import datetime
from datetime import timedelta

from random import seed
from random import randint
from random import random

from urllib.parse import urlparse


class MiintoApi:

    def __init__(self, auth):

        self.timezone_mod = auth['timezone_mod']
        self.auth_url = "https://api-auth.miinto.net/channels"

        self.order_host = "api-order.miinto.net"
        self.stock_host = "api-stock.miinto.net"

        self.miinto_type = 'MNT-HMAC-SHA256-1-0'

        self.identifier = auth['identifier']
        self.secret = auth['secret']
        self.auth_data = None

        self.empty_headers = {}
        self.dynamic_headers = {}
        self.payload = {}

        self.auth_data = self.get_auth()

        super(MiintoApi, self).__init__()

    def get_auth(self):

        # print('**** GET AUTH ****')

        payload = {
            'identifier': self.identifier,
            'secret': self.secret
        }

        response = requests.request(
            "POST",
            self.auth_url,
            headers=self.empty_headers,
            data=payload
        )

        if response.status_code == 200:
            response = json.loads(response.text)
        else:
            return False

        if response:
            status = response['meta']['status']
            version = response['meta']['version']
            miinto_id = response['data']['id']
            miinto_token = response['data']['token']
            accessorId = response['data']['data']['accessorId']

            codes = []

            for x in response['data']['privileges']['__GLOBAL__']['Store']:
                codes.append(x)

            auth_data = {
                'status': status,
                'version': version,
                'miinto_id': miinto_id,
                'miinto_token': miinto_token,
                'accessorId': accessorId,
                'codes': codes
            }

            self.auth_data = auth_data

            return auth_data

    def generate_signature(self, data):

        if data:
            method = data['method']
            anchor_host = data['anchor_host']
            endpoint = data['endpoint']
            query = data['query']
            url = data['url']
            payload = data['payload']
        else:
            raise Exception('You need to pass correct values!')

        try:
            # get from caller
            identifier = self.auth_data['miinto_id']
            token = self.auth_data['miinto_token']
            miinto_type = self.miinto_type

            anchor = urlparse(url)
            query = anchor.query.replace('?', '')

            resource = \
                method + "\n" + anchor_host + "\n" + endpoint + "\n" + query
            resourceSignature = hashlib.sha256(
                resource.encode('utf-8')).hexdigest()

            now = datetime.now() - timedelta(hours=self.timezone_mod)
            now.strftime("%s")
            now = round(time.mktime(now.timetuple()))
            timestamp = str(now)

            seed(random())
            miinto_seed = timestamp + str(randint(1, 999))
            headerString = \
                f"{identifier}\n{timestamp}\n{miinto_seed}\n{miinto_type}"
            headerSignature = hashlib.sha256(
                headerString.encode('utf-8')).hexdigest()

            if len(payload) == 0:
                payloadString = ""
            else:
                payloadString = payload

            payloadSignature = \
                hashlib.sha256(payloadString.encode('utf-8')).hexdigest()
            requestString = \
                f"{resourceSignature}\n{headerSignature}\n{payloadSignature}"

            # do the dirty job!
            signature = hmac.new(
                bytes(token, 'utf-8'),
                msg=bytes(requestString, 'utf-8'),
                digestmod=hashlib.sha256
            ).hexdigest()

            self.dynamic_headers['Miinto-Api-Auth-ID'] = identifier
            self.dynamic_headers['Miinto-Api-Auth-Signature'] = signature
            self.dynamic_headers['Miinto-Api-Auth-Timestamp'] = timestamp
            self.dynamic_headers['Miinto-Api-Auth-Seed'] = miinto_seed
            self.dynamic_headers['Miinto-Api-Auth-Type'] = miinto_type
            self.dynamic_headers['Miinto-Api-Control-Flavour'] = \
                'Miinto-Generic'
            self.dynamic_headers['Miinto-Api-Control-Version'] = '2.6'
            self.dynamic_headers['Content-Type'] = 'application/json'

            result = {
                'method': method,
                'payloadString': payloadString,
                'url': url
            }

            return result

        except Exception:
            raise

    def miinto_http_request(self, shop_id, sig_result, is_page=False):

        if sig_result:

            response = requests.request(
                sig_result['method'],
                sig_result['url'],
                headers=self.dynamic_headers,
                data=sig_result['payloadString']
            )

            if is_page:
                if response.status_code == 200:
                    # assign my values to result
                    result = json.loads(response.text)

                    # conditions
                    if result['meta']['totalItemCount'] > 0:
                        return shop_id, result
                    elif result['meta']['status'] == 'failure':
                        return shop_id, f'Shop {shop_id} not active'
                    else:
                        return shop_id, f'No content for {shop_id}'
            else:
                # standard dummy call
                if response.status_code == 200:
                    return json.loads(response.text)
                else:
                    return response.status_code
        else:
            raise

    def fetch_shop_details(self, shop_id):

        endpoint = f'/shops/{shop_id}/'
        query = ''

        data = {
            'method': 'GET',
            'anchor_host': self.order_host,
            'endpoint': endpoint,
            'query': query,
            'url': f"https://{self.order_host}{endpoint}" + query,
            'payload': {}
        }

        sig_result = self.generate_signature(data)
        result = self.miinto_http_request(shop_id, sig_result)

        return result

    def get_collection(
        self, 
        shop_id, 
        order_type='transfers',
        order_status='pending'
    ):

        # TODO: need to manage pagination where
        # totalItemCount > limit
        # do the call again with offset param

        endpoint = f'/shops/{shop_id}/{order_type}'
        query = f'?status%5B%5D={order_status}&sort=-createdAt'

        data = {
            'method': 'GET',
            'anchor_host': self.order_host,
            'endpoint': endpoint,
            'query': query,
            'url': f"https://{self.order_host}{endpoint}" + query,
            'payload': {}
        }

        sig_result = self.generate_signature(data)
        result = self.miinto_http_request(shop_id, sig_result, True)

        return result

    def update_stock(self, shop_id, stocks):

        endpoint = f'/locations/{shop_id}/items'
        query = ''
        payload = json.dumps(stocks)

        data = {
            'method': 'PATCH',
            'anchor_host': self.stock_host,
            'endpoint': endpoint,
            'query': query,
            'url': f"https://{self.stock_host}{endpoint}" + query,
            'payload': payload
        }

        sig_result = self.generate_signature(data)
        result = self.miinto_http_request(shop_id, sig_result)

        return shop_id, result
