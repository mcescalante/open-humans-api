from unittest import TestCase

import pytest
import vcr

from ohapi.api import (
    SettingsError, oauth2_auth_url, oauth2_token_exchange,
    get_page, message, delete_file)

parameter_defaults = {
    'CLIENT_ID_VALID': 'validclientid',
    'CLIENT_SECRET_VALID': 'validclientsecret',
    'CODE_VALID': 'validcode',
    'REFRESH_TOKEN_VALID': 'validrefreshtoken',
    'CLIENT_ID_INVALID': 'invalidclientid',
    'CLIENT_SECRET_INVALID': 'invalidclientsecret',
    'CODE_INVALID': 'invalidcode',
    'REFRESH_TOKEN_INVALID': 'invalidrefreshtoken',
    'REDIRECT_URI': 'http://127.0.0.1:5000/authorize_openhumans/',
    'ACCESS_TOKEN': 'accesstoken',
    'ACCESS_TOKEN_EXPIRED': 'accesstokenexpired',
    'ACCESS_TOKEN_INVALID': 'accesstokeninvalid',
    'MASTER_ACCESS_TOKEN': 'masteraccesstoken',
    'INVALID_PMI1': 'invalidprojectmemberid1',
    'INVALID_PMI2': 'invalidprojectmemberid2',
    'VALID_PMI1': 'validprojectmemberid1',
    'VALID_PMI2': 'validprojectmemberid2',
    'SUBJECT': 'testsubject',
    'MESSAGE': 'testmessage',

}

"""
_config_params_api.py is not usually present.  You can create this to use valid
codes and tokens if you wish to record new cassettes. If present, this file is
used to overwrite `parameter_defaults` with the (hopefully valid, but secret)
items in the file. DO NOT COMMIT IT TO GIT!

To get started, do:
cp _config_params_api.py.example _config_params_api.py

Edit _config_params_api.py to define valid secret codes, tokens, etc.

Run a specific function to (re)create an associated cassette, e.g.:
pytest ohapi/tests/test_api.py::APITest::test_oauth2_token_exchange__valid_code

(This only makes a new cassette if one doesn't already exist!)
"""
try:
    from _config_params_api import params
    for param in params:
        parameter_defaults[param] = params[param]
except ImportError:
    pass

for param in parameter_defaults:
    locals()[param] = parameter_defaults[param]


FILTERSET = [('access_token', 'ACCESSTOKEN'), ('client_id', 'CLIENTID'),
             ('client_secret', 'CLIENTSECRET'), ('code', 'CODE'),
             ('refresh_token', 'REFRESHTOKEN'),
             ('invalid_access_token', 'INVALIDACCESSTOKEN')]

my_vcr = vcr.VCR(path_transformer=vcr.VCR.ensure_suffix('.yaml'),
                 cassette_library_dir='ohapi/cassettes',
                 filter_headers=[('Authorization', 'XXXXXXXX')],
                 filter_query_parameters=FILTERSET,
                 filter_post_data_parameters=FILTERSET)


class APITestOAuthTokenExchange(TestCase):

    def setUp(self):
        pass

    def test_oauth2_auth_url__no_client_id(self):
        with pytest.raises(SettingsError):
            oauth2_auth_url()

    def test_oauth2_auth_url__with_client_id(self):
        auth_url = oauth2_auth_url(client_id='abcd1234')
        assert auth_url == (
            'https://www.openhumans.org/direct-sharing/projects/'
            'oauth2/authorize/?client_id=abcd1234&response_type=code')

    def test_oauth2_auth_url__with_client_id_and_redirect_uri(self):
        auth_url = oauth2_auth_url(client_id='abcd1234',
                                   redirect_uri='http://127.0.0.1:5000/auth/')
        assert auth_url == (
            'https://www.openhumans.org/direct-sharing/projects/'
            'oauth2/authorize/?client_id=abcd1234&response_type=code'
            '&redirect_uri=http%3A%2F%2F127.0.0.1%3A5000%2Fauth%2F')

    @my_vcr.use_cassette()
    def test_oauth2_token_exchange__valid_code(self):
        data = oauth2_token_exchange(
            code=CODE_VALID, client_id=CLIENT_ID_VALID,
            client_secret=CLIENT_SECRET_VALID, redirect_uri=REDIRECT_URI)
        assert data == {
            'access_token': 'returnedaccesstoken',
            'expires_in': 36000,
            'refresh_token': 'returnedrefreshtoken',
            'scope': 'american-gut read wildlife open-humans write '
                     'pgp go-viral',
            'token_type': 'Bearer'}

    @my_vcr.use_cassette()
    def test_oauth2_token_exchange__invalid_code(self):
        data = oauth2_token_exchange(
            code=CODE_VALID, client_id=CLIENT_ID_VALID,
            client_secret=CLIENT_SECRET_VALID, redirect_uri=REDIRECT_URI)
        assert data == {'error': 'invalid_grant'}

    @my_vcr.use_cassette()
    def test_oauth2_token_exchange__invalid_client(self):
        data = oauth2_token_exchange(
            code=CODE_INVALID, client_id=CLIENT_ID_INVALID,
            client_secret=CLIENT_SECRET_VALID, redirect_uri=REDIRECT_URI)
        assert data == {'error': 'invalid_client'}

    @my_vcr.use_cassette()
    def test_oauth2_token_exchange__invalid_secret(self):
        data = oauth2_token_exchange(
            code=CODE_VALID, client_id=CLIENT_ID_VALID,
            client_secret=CLIENT_SECRET_INVALID, redirect_uri=REDIRECT_URI)
        assert data == {'error': 'invalid_client'}

    @my_vcr.use_cassette()
    def test_oauth2_token_exchange__valid_refresh(self):
        data = oauth2_token_exchange(
            refresh_token=REFRESH_TOKEN_VALID, client_id=CLIENT_ID_VALID,
            client_secret=CLIENT_SECRET_VALID, redirect_uri=REDIRECT_URI)
        assert data == {
            'access_token': 'newaccesstoken',
            'expires_in': 36000,
            'refresh_token': 'newrefreshtoken',
            'scope': 'american-gut read wildlife open-humans write '
                     'pgp go-viral',
            'token_type': 'Bearer'}

    @my_vcr.use_cassette()
    def test_oauth2_token_exchange__invalid_refresh(self):
        data = oauth2_token_exchange(
            refresh_token=REFRESH_TOKEN_INVALID, client_id=CLIENT_ID_VALID,
            client_secret=CLIENT_SECRET_VALID, redirect_uri=REDIRECT_URI)
        assert data == {'error': 'invalid_grant'}


class APITestGetPage(TestCase):

    def setUp(self):
        pass

    @my_vcr.use_cassette()
    def test_get_page_with_results(self):
        url = ('https://www.openhumans.org/api/direct-sharing/project/'
               'exchange-member/?'
               'access_token={}'.format(ACCESS_TOKEN))
        response = get_page(url)
        self.assertEqual(response['project_member_id'], 'PMI')
        self.assertEqual(response['message_permission'], True)
        self.assertEqual(response['data'], [])
        self.assertEqual(response['username'], 'test_user')
        self.assertEqual(response['sources_shared'], [])
        self.assertEqual(response['created'], 'created_date_time')

    @my_vcr.use_cassette()
    def test_get_page_invalid_access_token(self):
        url = ('https://www.openhumans.org/api/direct-sharing/project/'
               'exchange-member/?access_token={}'.format("invalid_token"))
        self.assertRaises(Exception, get_page, url)


class APITestMessage(TestCase):

    def setUp(self):
        pass

    @my_vcr.use_cassette()
    def test_message_valid_access_token(self):
        response = message(subject=SUBJECT, message=MESSAGE,
                           access_token=ACCESS_TOKEN)
        self.assertEqual(response.status_code, 200)

    @my_vcr.use_cassette()
    def test_message_expired_access_token(self):
        response = message(subject=SUBJECT, message=MESSAGE,
                           access_token=ACCESS_TOKEN_EXPIRED)
        assert response.json() == {"detail": "Expired token."}

    @my_vcr.use_cassette()
    def test_message_invalid_access_token(self):
        response = message(subject=SUBJECT, message=MESSAGE,
                           access_token=ACCESS_TOKEN_INVALID)
        assert response.json() == {"detail": "Invalid token."}

    @my_vcr.use_cassette()
    def test_message_all_members_true_project_member_id_none(self):
        response = message(all_members=True, subject=SUBJECT, message=MESSAGE,
                           access_token=ACCESS_TOKEN)
        self.assertEqual(response.status_code, 200)

    @my_vcr.use_cassette()
    def test_message_all_members_true_project_member_id_not_none(self):
        self.assertRaises(Exception, message, all_members=True,
                          project_member_ids=['abcdef', 'sdf'],
                          subject=SUBJECT, message=MESSAGE,
                          access_token=ACCESS_TOKEN)

    @my_vcr.use_cassette()
    def test_message_all_members_false_projectmemberid_has_invalid_char(self):
        response = message(project_member_ids=['abcdef1', 'test'],
                           subject=SUBJECT, message=MESSAGE,
                           access_token=MASTER_ACCESS_TOKEN)
        assert response.json() == {"errors":
                                   {"project_member_ids":
                                    ["Project member IDs are always 8" +
                                     " digits long."]}}

    @my_vcr.use_cassette()
    def test_message_all_members_false_projectmemberid_has_invalid_digit(self):
        response = message(project_member_ids=[INVALID_PMI1, INVALID_PMI2],
                           subject=SUBJECT, message=MESSAGE,
                           access_token=MASTER_ACCESS_TOKEN)
        assert response.json() == {"errors":
                                   {"project_member_ids":
                                    ["Invalid project member ID(s):" +
                                     " invalidPMI2"]}}

    @my_vcr.use_cassette()
    def test_message_all_members_false_project_member_id_not_none_valid(self):
        response = message(project_member_ids=[VALID_PMI1, VALID_PMI2],
                           subject=SUBJECT, message=MESSAGE,
                           access_token=ACCESS_TOKEN)
        self.assertEqual(response.status_code, 200)


class APITestDeleteFile(TestCase):

    def setUp(self):
        pass

    @my_vcr.use_cassette()
    def test_delete_file__invalid_access_token(self):
        response = delete_file(
            access_token=ACCESS_TOKEN_INVALID, project_member_id='59319749',
            all_files=True)
        assert response.json() == {"detail": "Invalid token."}

    @my_vcr.use_cassette()
    def test_delete_file_project_member_id_given(self):
        response = delete_file(access_token=ACCESS_TOKEN,
                               project_member_id='59319749', all_files=True)
        self.assertEqual(response.status_code, 200)

    @my_vcr.use_cassette()
    def test_delete_file_project_member_id_invalid(self):
        response = delete_file(access_token=ACCESS_TOKEN, all_files=True,
                               project_member_id='1234')
        self.assertEqual(response.status_code, 400)

    @my_vcr.use_cassette()
    def test_delete_file__expired_access_token(self):
        response = delete_file(access_token=ACCESS_TOKEN_EXPIRED,
                               all_files=True,
                               project_member_id='59319749')
        assert response.json() == {"detail": "Expired token."}

    @my_vcr.use_cassette()
    def test_delete_file__valid_access_token(self):
        response = delete_file(
            access_token=ACCESS_TOKEN, project_member_id='59319749',
            all_files=True)
        self.assertEqual(response.status_code, 200)
