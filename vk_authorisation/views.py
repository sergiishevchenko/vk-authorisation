from django.shortcuts import render
import requests
import getpass
from html.parser import HTMLParser
from config import access_token, APP_ID


def authorisation(request):

    class FormParser(HTMLParser):
        def __init__(self):
            HTMLParser.__init__(self)
            self.url = None
            self.denial_url = None
            self.params = {}
            self.method = 'GET'
            self.in_form = False
            self.in_denial = False
            self.form_parsed = False

        def handle_starttag(self, tag, attrs):
            tag = tag.lower()
            if tag == 'form':
                if self.in_form:
                    raise RuntimeError('Nested form tags are not supported yet')
                else:
                    self.in_form = True
            if not self.in_form:
                return

            attrs = dict((name.lower(), value) for name, value in attrs)

            if tag == 'form':
                self.url = attrs['action']
                if 'method' in attrs:
                    self.method = attrs['method']
            elif tag == 'input' and 'type' in attrs and 'name' in attrs:
                if attrs['type'] in ['hidden', 'text', 'password']:
                    self.params[attrs['name']] = attrs['value'] if 'value' in attrs else ''
            elif tag == 'input' and 'type' in attrs:
                if attrs['type'] == 'submit':
                    self.params['submit_allow_access'] = True
            elif tag == 'div' and 'class' in attrs:
                if attrs['class'] == 'near_btn':
                    self.in_denial = True
            elif tag == 'a' and 'href' in attrs and self.in_denial:
                self.denial_url = attrs['href']

        def handle_endtag(self, tag):
            tag = tag.lower()
            if tag == 'form':
                if not self.in_form:
                    raise RuntimeError('Unexpected end of <form>')
                self.form_parsed = True
                self.in_form = False
            elif tag == 'div' and self.in_denial:
                self.in_denial = False

    class VKAuth(object):

        def __init__(self, permissions, app_id, api_v, email=None, pswd=None, two_factor_auth=False, security_code=None, auto_access=True):

            self.session = requests.Session()
            self.form_parser = FormParser()
            self._user_id = None
            self._access_token = None
            self.response = None
            self.permissions = permissions
            self.api_v = api_v
            self.app_id = app_id
            self.two_factor_auth = two_factor_auth
            self.security_code = security_code
            self.email = email
            self.pswd = pswd
            self.auto_access = auto_access

            if security_code is not None and two_factor_auth is False:
                raise RuntimeError('Security code provided for non-two-factor authorization')

        def auth(self):
            api_auth_url = 'https://oauth.vk.com/authorize'
            app_id = self.app_id
            permissions = self.permissions
            redirect_uri = 'https://oauth.vk.com/blank.html'
            display = 'wap'
            api_version = self.api_v
            auth_url_template = '{0}?client_id={1}&scope={2}&redirect_uri={3}&display={4}&v={5}&response_type=token'
            auth_url = auth_url_template.format(api_auth_url, app_id, ','.join(permissions), redirect_uri, display, api_version)

            self.response = self.session.get(auth_url)
            template_name = "authorisation.html"

            if not self._parse_form():
                raise RuntimeError('No <form> element found. Please, check url address')
            else:
                while not self._log_in():
                    pass

                if self.two_factor_auth:
                    self._two_fact_auth()

                self._allow_access()

                self._get_params()

                self._close()

        def get_token(self):
            print(self._access_token)
            return self._access_token

        def get_user_id(self):
            print(self._user_id)
            return self._user_id

        def _parse_form(self):

            self.form_parser = FormParser()
            parser = self.form_parser

            try:
                parser.feed(str(self.response.content))
            except Exception:
                print('Unexpected error occured while looking for <form> element')
                return False

            return True

        def _submit_form(self, *params):

            parser = self.form_parser

            if parser.method == 'post':
                payload = parser.params
                payload.update(*params)
                try:
                    self.response = self.session.post(parser.url, data=payload)
                except requests.exceptions.RequestException as err:
                    print("Error: ", err)
                except requests.exceptions.HTTPError as err:
                    print("Error: ", err)
                except requests.exceptions.ConnectionError as err:
                    print("Error: ConnectionError\n", err)
                except requests.exceptions.Timeout as err:
                    print("Error: Timeout\n", err)
                except Exception:
                    print("Unexpecred error occured")

            else:
                self.response = None

        def _log_in(self):
            if self.email is None:
                self.email = ''
                while self.email.strip() == '':
                    self.email = input('Enter an email to log in: ')

            if self.pswd is None:
                self.pswd = ''
                while self.pswd.strip() == '':
                    self.pswd = getpass.getpass('Enter the password: ')
            self._submit_form({'email': self.email, 'pass': self.pswd})

            if not self._parse_form():
                raise RuntimeError('No <form> element found. Please, check url address')

            if 'pass' in self.form_parser.params:
                print('Wrong email or password')
                self.email = None
                self.pswd = None
                return False
            elif 'code' in self.form_parser.params and not self.two_factor_auth:
                self.two_factor_auth = True
            else:
                return True

        def _two_fact_auth(self):

            prefix = 'https://m.vk.com'

            if prefix not in self.form_parser.url:
                self.form_parser.url = prefix + self.form_parser.url

            if self.security_code is None:
                self.security_code = input('Enter security code for two-factor authentication: ')

            self._submit_form({'code': self.security_code})

            if not self._parse_form():
                raise RuntimeError('No <form> element found. Please, check url address')

        def _allow_access(self):

            parser = self.form_parser

            if 'submit_allow_access' in parser.params and 'grant_access' in parser.url:
                if not self.auto_access:
                    answer = ''
                    msg = 'Application needs access to the following details in your profile:\n' + str(self.permissions) + '\n' + 'Allow it to use them? (yes or no)'

                    attempts = 5
                    while answer not in ['yes', 'no'] and attempts > 0:
                        answer = input(msg).lower().strip()
                        attempts -= 1

                    if answer == 'no' or attempts == 0:
                        self.form_parser.url = self.form_parser.denial_url
                        print('Access denied')

                self._submit_form({})

        def _get_params(self):

            try:
                params = self.response.url.split('#')[1].split('&')
                self._access_token = params[0].split('=')[1]
                self._user_id = params[2].split('=')[1]
            except IndexError as err:
                print('Coudln\'t fetch token and user id\n')
                print(err)

        def _close(self):
            self.session.close()
            self.response = None
            self.form_parser = None
            self.security_code = None
            self.email = None
            self.pswd = None

    vk = VKAuth(['friends'], APP_ID, '5.122')
    vk.auth()
    # token = vk.get_token()
    # user_id = vk.get_user_id()
    return render(request, 'authorisation.html')

def user_page(request):
    return render(request, 'user_page.html')
