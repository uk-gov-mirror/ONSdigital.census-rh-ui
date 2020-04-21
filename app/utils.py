import string
import re
import json

from aiohttp.client_exceptions import (ClientConnectionError,
                                       ClientConnectorError,
                                       ClientResponseError)
from structlog import get_logger
logger = get_logger('respondent-home')

OBSCURE_WHITESPACE = (
    '\u180E'  # Mongolian vowel separator
    '\u200B'  # zero width space
    '\u200C'  # zero width non-joiner
    '\u200D'  # zero width joiner
    '\u2060'  # word joiner
    '\uFEFF'  # zero width non-breaking space
)

uk_prefix = '44'


class View:
    valid_display_regions = r'{display_region:\ben|cy|ni\b}'

    @staticmethod
    def setup_request(request):
        request['client_ip'] = request.headers.get('X-Forwarded-For', None)

    @staticmethod
    def log_entry(request, endpoint):
        method = request.method
        logger.info(f"received {method} on endpoint '{endpoint}'",
                    method=request.method,
                    path=request.path)

    @staticmethod
    def _handle_response(response):
        try:
            response.raise_for_status()
        except ClientResponseError as ex:
            if not ex.status == 404:
                logger.error('error in response',
                             url=response.url,
                             status_code=response.status)
            raise ex
        else:
            logger.debug('successfully connected to service',
                         url=str(response.url))

    @staticmethod
    async def _make_request(request,
                            method,
                            url,
                            func,
                            auth=None,
                            json=None,
                            return_json=False):
        """
        :param request: The AIOHTTP user request, used for logging and app access
        :param method: The HTTP verb
        :param url: The target URL
        :param auth: Authorization
        :param json: JSON payload to pass as request data
        :param func: Function to call on the response
        :param return_json: If True, the response JSON will be returned
        """
        logger.debug('making request with handler',
                     method=method,
                     url=url,
                     handler=func.__name__)
        try:
            async with request.app.http_session_pool.request(
                    method, url, auth=auth, json=json, ssl=False) as resp:
                func(resp)
                if return_json:
                    return await resp.json()
                else:
                    return None
        except (ClientConnectionError, ClientConnectorError) as ex:
            logger.error('client failed to connect',
                         url=url,
                         client_ip=request['client_ip'])
            raise ex


class InvalidDataError(Exception):

    def __init__(self, message=None):
        super().__init__(message or 'The supplied value is invalid')


class InvalidDataErrorWelsh(Exception):

    def __init__(self, message=None):
        super().__init__(message or 'WELSH The supplied value is invalid')


class ProcessPostcode:

    postcode_validation_pattern = re.compile(
        r'^((AB|AL|B|BA|BB|BD|BH|BL|BN|BR|BS|BT|BX|CA|CB|CF|CH|CM|CO|CR|CT|CV|CW|DA|DD|DE|DG|DH|DL|DN|DT|DY|E|EC|EH|EN|EX|FK|FY|G|GL|GY|GU|HA|HD|HG|HP|HR|HS|HU|HX|IG|IM|IP|IV|JE|KA|KT|KW|KY|L|LA|LD|LE|LL|LN|LS|LU|M|ME|MK|ML|N|NE|NG|NN|NP|NR|NW|OL|OX|PA|PE|PH|PL|PO|PR|RG|RH|RM|S|SA|SE|SG|SK|SL|SM|SN|SO|SP|SR|SS|ST|SW|SY|TA|TD|TF|TN|TQ|TR|TS|TW|UB|W|WA|WC|WD|WF|WN|WR|WS|WV|YO|ZE)(\d[\dA-Z]?[ ]?\d[ABD-HJLN-UW-Z]{2}))|BFPO[ ]?\d{1,4}$'  # NOQA
    )

    @staticmethod
    def validate_postcode(postcode, locale):

        for character in string.whitespace + OBSCURE_WHITESPACE:
            postcode = postcode.replace(character, '')

        postcode = postcode.upper()

        if not postcode.isalnum():
            if locale == 'cy':
                raise InvalidDataErrorWelsh('The postcode must not contain symbols')
            else:
                raise InvalidDataError('The postcode must not contain symbols')

        if len(postcode) < 5:
            if locale == 'cy':
                raise InvalidDataErrorWelsh('The postcode does not contain enough characters')
            else:
                raise InvalidDataError('The postcode does not contain enough characters')

        if len(postcode) > 7:
            if locale == 'cy':
                raise InvalidDataErrorWelsh('The postcode contains too many characters')
            else:
                raise InvalidDataError('The postcode contains too many characters')

        if not ProcessPostcode.postcode_validation_pattern.fullmatch(postcode):
            if locale == 'cy':
                raise InvalidDataErrorWelsh('The postcode is not a valid UK postcode')
            else:
                raise InvalidDataError('The postcode is not a valid UK postcode')

        postcode_formatted = postcode[:-3] + ' ' + postcode[-3:]

        return postcode_formatted


class ProcessMobileNumber:

    @staticmethod
    def normalise_phone_number(number, locale):

        for character in string.whitespace + OBSCURE_WHITESPACE + '()-+':
            number = number.replace(character, '')

        try:
            list(map(int, number))
        except ValueError:
            if locale == 'cy':
                raise InvalidDataErrorWelsh('The mobile phone number must not contain letters or symbols')
            else:
                raise InvalidDataError('The mobile phone number must not contain letters or symbols')

        return number.lstrip('0')

    @staticmethod
    def validate_uk_mobile_phone_number(number, locale):

        number = ProcessMobileNumber.normalise_phone_number(number, locale).lstrip(uk_prefix).lstrip('0')

        if not number.startswith('7'):
            if locale == 'cy':
                raise InvalidDataErrorWelsh('The mobile phone number is not a UK mobile number')
            else:
                raise InvalidDataError('The mobile phone number is not a UK mobile number')

        if len(number) > 10:
            if locale == 'cy':
                raise InvalidDataErrorWelsh('The mobile phone number contains too many digits')
            else:
                raise InvalidDataError('The mobile phone number contains too many digits')

        if len(number) < 10:
            if locale == 'cy':
                raise InvalidDataErrorWelsh('The mobile phone number does not contain enough digits')
            else:
                raise InvalidDataError('The mobile phone number does not contain enough digits')

        return '{}{}'.format(uk_prefix, number)


class FlashMessage:

    @staticmethod
    def generate_flash_message(text, level, message_type, field):
        json_return = {'text': text, 'level': level, 'type': message_type, 'field': field}
        return json_return


class AddressIndex(View):

    @staticmethod
    async def get_postcode_return(request, postcode, display_region):
        postcode_return = await AddressIndex.get_ai_postcode(request, postcode)

        address_options = []

        if display_region == 'cy':
            cannot_find_text = 'I cannot find my address'
        else:
            cannot_find_text = 'I cannot find my address'

        for singleAddress in postcode_return['response']['addresses']:
            address_options.append({
                'value':
                json.dumps({
                    'uprn': singleAddress['uprn'],
                    'address': singleAddress['formattedAddress']
                }),
                'label': {
                    'text': singleAddress['formattedAddress']
                },
                'id':
                singleAddress['uprn']
            })

        address_options.append({
            'value':
            json.dumps({
                'uprn': 'xxxx',
                'address': cannot_find_text
            }),
            'label': {
                'text': cannot_find_text
            },
            'id': 'xxxx'
        })

        address_content = {
            'postcode': postcode,
            'addresses': address_options,
            'total_matches': postcode_return['response']['total']
        }

        return address_content

    @staticmethod
    async def get_ai_postcode(request, postcode):
        ai_svc_url = request.app['ADDRESS_INDEX_SVC_URL']
        url = f'{ai_svc_url}/addresses/postcode/{postcode}'
        return await View._make_request(request,
                                        'GET',
                                        url,
                                        View._handle_response,
                                        auth=request.app['ADDRESS_INDEX_SVC_AUTH'],
                                        return_json=True)

    @staticmethod
    async def get_ai_uprn(request, uprn):
        ai_svc_url = request.app['ADDRESS_INDEX_SVC_URL']
        url = f'{ai_svc_url}/addresses/rh/uprn/{uprn}?addresstype=paf'
        return await View._make_request(request,
                                        'GET',
                                        url,
                                        View._handle_response,
                                        auth=request.app['ADDRESS_INDEX_SVC_AUTH'],
                                        return_json=True)


class RHService(View):

    @staticmethod
    async def get_cases_by_uprn(request, uprn):
        rhsvc_url = request.app['RHSVC_URL']
        return await View._make_request(request,
                                        'GET',
                                        f'{rhsvc_url}/cases/uprn/{uprn}',
                                        View._handle_response,
                                        return_json=True)

    @staticmethod
    async def post_unlinked_uac(request, uac, address):
        uac_hash = uac
        logger.info('request linked case',
                    uac_hash=uac_hash,
                    client_ip=request['client_ip'])
        rhsvc_url = request.app['RHSVC_URL']
        address_json = {
            "addressLine1": address['addressLine1'],
            "addressLine2": address['addressLine2'],
            "addressLine3": address['addressLine3'],
            "townName": address['townName'],
            "region": address['countryCode'],
            "postcode": address['postcode'],
            "uprn": address['uprn'],
            "estabType": address['censusEstabType'],
            "addressType": address['censusAddressType']
        }
        url = f'{rhsvc_url}/uacs/{uac_hash}/link'
        return await View._make_request(request,
                                        'POST',
                                        url,
                                        View._handle_response,
                                        auth=request.app['RHSVC_AUTH'],
                                        json=address_json,
                                        return_json=True)
