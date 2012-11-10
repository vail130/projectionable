from django.test import TestCase
from account_api.models import Account, AccountRequest
import json

class SessionManagerNoSessionTestCase(TestCase):
    def setUp(self):
        self.email = 'vail.gold@dressler-llc.com'
        self.password = 'danceparty'
        self.account = Account.create_account(self.email, self.password)

    def tearDown(self):
        self.email = None
        self.password = None
        self.account = None

    def test_400_get_no_valid_session(self):
        response = self.client.get('/api/session')
        self.assertEqual(response.status_code, 400)

    def test_400_delete_no_valid_session(self):
        response = self.client.delete('/api/session')
        self.assertEqual(response.status_code, 400)

    def test_400_post_pending_user(self):
        payload = json.dumps({"email": self.email, "password": self.password})
        response = self.client.post('/api/session', payload, content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_200_post_active_user(self):
        self.account.status = 'active'
        self.account.save()

        payload = json.dumps({"email": self.email, "password": self.password})
        response = self.client.post('/api/session', payload, content_type='application/json')
        self.assertEqual(response.status_code, 200)

class SessionManagerValidSessionTestCase(TestCase):
    def setUp(self):
        self.email = 'vail.gold@dressler-llc.com'
        self.password = 'danceparty'
        self.account = Account.create_account(self.email, self.password)
        self.account.status = 'active'
        self.account.save()
        self.client.login(username=self.account.user.username, password=self.password)

    def tearDown(self):
        self.email = None
        self.password = None
        self.account = None

    def test_200_get_valid_session(self):
        response = self.client.get('/api/session')
        self.assertEqual(response.status_code, 200)

    def test_200_delete_valid_session(self):
        response = self.client.delete('/api/session')
        self.assertEqual(response.status_code, 200)

class SessionManagerOtherTestCase(TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_405_put_method_not_allowed(self):
        response = self.client.put('/api/session', {})
        self.assertEqual(response.status_code, 405)

class AccountManagerNoSessionTestCase(TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_401_get_account_unauthorized_no_session(self):
        response = self.client.get('/api/accounts')
        self.assertEqual(response.status_code, 401)

    def test_401_delete_account_unauthorized_no_session(self):
        response = self.client.delete('/api/accounts')
        self.assertEqual(response.status_code, 401)

class AccountManagerPutTestCase(TestCase):
    def setUp(self):
        self.email = 'vail.gold@dressler-llc.com'
        self.password = 'danceparty'
        self.account = Account.create_account(self.email, self.password)
        self.account.status = 'active'
        self.account.save()
        self.client.login(username=self.account.user.username, password=self.password)

    def tearDown(self):
        self.email = None
        self.password = None
        self.account = None

    def test_400_invalid_content_type(self):
        payload = json.dumps({"action": "asdf", "email": self.email})
        response = self.client.put('/api/accounts', payload, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 400)

    def test_400_invalid_action(self):
        payload = json.dumps({"action": "asdf", "email": self.email})
        response = self.client.put('/api/accounts', payload, content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_400_invalid_email(self):
        payload = json.dumps({"action": "request_password_reset", "email": "asdf"})
        response = self.client.put('/api/accounts', payload, content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_400_incorrect_email(self):
        payload = json.dumps({"action": "request_password_reset", "email": "asdf@gmail.com"})
        response = self.client.put('/api/accounts', payload, content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_200_request_password_reset(self):
        payload = json.dumps({"action": "request_password_reset", "email": self.email})
        response = self.client.put('/api/accounts', payload, content_type='application/json')
        self.assertEqual(response.status_code, 200)

class AccountManagerPostTestCase(TestCase):
    def setUp(self):
        self.email = 'vail.gold@dressler-llc.com'
        self.password = 'danceparty'

    def tearDown(self):
        self.email = None
        self.password = None

    def test_400_missing_email(self):
        data = json.dumps({
            "password": self.password,
        })
        response = self.client.post('/api/accounts', data, content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_400_missing_password(self):
        data = json.dumps({
            "email": self.email,
        })
        response = self.client.post('/api/accounts', data, content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_400_invalid_email(self):
        data = json.dumps({
            "email": 'adfasdfasdfadfs',
            "password": self.password,
        })
        response = self.client.post('/api/accounts', data, content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_200_valid_account(self):
        data = json.dumps({
            "email": self.email,
            "password": self.password,
        })
        response = self.client.post('/api/accounts', data, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content)["email"], self.email)
        self.assertEqual(json.loads(response.content)["status"], 'pending')
        self.assertEqual(json.loads(response.content)["group"], 'trial')
        self.assertEqual(json.loads(response.content)["type"], 'primary')

    def test_400_missing_email_list(self):
        account = Account.create_account(self.email, self.password)
        account.status = 'active'
        account.group = 'agency'
        account.save()
        self.client.login(username=account.user.username, password=self.password)

        data = json.dumps({
            "type": "secondary",
        })
        response = self.client.post('/api/accounts', data, content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_400_used_email_address(self):
        account = Account.create_account(self.email, self.password)
        account.status = 'active'
        account.group = 'agency'
        account.save()
        self.client.login(username=account.user.username, password=self.password)

        data = json.dumps({
            "type": "secondary",
            "email_list": [self.email],
        })
        response = self.client.post('/api/accounts', data, content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_400_invalid_email_list(self):
        account = Account.create_account(self.email, self.password)
        account.status = 'active'
        account.group = 'agency'
        account.save()
        self.client.login(username=account.user.username, password=self.password)

        data = json.dumps({
            "type": "secondary",
            "email_list": ['adfasfdasdfasdfs'],
        })
        response = self.client.post('/api/accounts', data, content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_200_valid_secondary_accounts(self):
        account = Account.create_account(self.email, self.password)
        account.status = 'active'
        account.group = 'agency'
        account.save()
        self.client.login(username=account.user.username, password=self.password)

        data = json.dumps({
            "type": "secondary",
            "email_list": [
                'asdf@gmail.com',
                'asdfadsf@yahoo.com'
            ],
        })
        response = self.client.post('/api/accounts', data, content_type='application/json')
        self.assertEqual(response.status_code, 200)

class AccountManagerOtherTestCase(TestCase):
    def setUp(self):
        self.email = 'vail.gold@dressler-llc.com'
        self.password = 'danceparty'
        self.account = Account.create_account(self.email, self.password)
        ar = AccountRequest.objects.get(account=self.account, type='create-primary-account', status='pending')
        payload = json.dumps({"action": "verify_email", "code": ar.code})
        self.client.put('/api/accounts/' + str(self.account.id), payload, content_type='application/json')
        self.client.login(username=self.account.user.username, password=self.password)

    def tearDown(self):
        self.email = None
        self.password = None
        self.account = None

    def test_405_get_account_method_not_allowed(self):
        response = self.client.get('/api/accounts')
        self.assertEqual(response.status_code, 405)

    def test_405_delete_account_method_not_allowed(self):
        response = self.client.delete('/api/accounts')
        self.assertEqual(response.status_code, 405)

class AccountEditorNoSessionOtherTestCase(TestCase):
    def setUp(self):
        self.email = 'vail.gold@dressler-llc.com'
        self.password = 'danceparty'
        self.account = Account.create_account(self.email, self.password)
        self.account_id = self.account.user_id
        self.endpoint = '/api/accounts/' + str(self.account_id)

    def tearDown(self):
        self.email = None
        self.password = None
        self.account = None
        self.account_id = None
        self.endpoint = None

    def test_401_get_account_unauthorized_no_session(self):
        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, 401)

    def test_401_delete_account_unauthorized_no_session(self):
        response = self.client.delete(self.endpoint)
        self.assertEqual(response.status_code, 401)

    def test_401_post_account_unauthorized_no_session(self):
        response = self.client.post(self.endpoint, json.dumps({}), content_type='application/json')
        self.assertEqual(response.status_code, 401)

    def test_401_account_unauthorized_no_session(self):
        response = self.client.put(self.endpoint, json.dumps({}), content_type='application/json')
        self.assertEqual(response.status_code, 401)

class AccountEditorPutVerifyEmailTestCase(TestCase):
    def setUp(self):
        self.email = 'vail.gold@dressler-llc.com'
        self.password = 'danceparty'
        self.account = Account.create_account(self.email, self.password)
        self.endpoint = '/api/accounts/' + str(self.account.user_id)

    def tearDown(self):
        self.email = None
        self.password = None
        self.account = None
        self.endpoint = None

    def test_400_missing_code(self):
        ar = AccountRequest.objects.get(account=self.account, status='pending', type='create-primary-account')
        payload = json.dumps({
            "action": "verify_email"
        })
        response = self.client.put(self.endpoint, payload, content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_400_invalid_code(self):
        ar = AccountRequest.objects.get(account=self.account, status='pending', type='create-primary-account')
        payload = json.dumps({
            "action": "verify_email",
            "code": "asdfasdfasdfa"
        })
        response = self.client.put(self.endpoint, payload, content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_200_valid_email_verification(self):
        ar = AccountRequest.objects.get(account=self.account, status='pending', type='create-primary-account')
        payload = json.dumps({
            "action": "verify_email",
            "code": ar.code
        })
        response = self.client.put(self.endpoint, payload, content_type='application/json')
        self.assertEqual(response.status_code, 200)

class AccountEditorPutChangeEmailTestCase(TestCase):
    def setUp(self):
        self.email = 'vail.gold@dressler-llc.com'
        self.password = 'danceparty'
        self.account = Account.create_account(self.email, self.password)
        self.account.status = 'active'
        self.account.save()
        self.client.login(username=self.account.user.username, password=self.password)
        self.endpoint = '/api/accounts/' + str(self.account.user_id)

    def tearDown(self):
        self.email = None
        self.password = None
        self.account = None
        self.endpoint = None

    def test_400_email_in_use(self):
        payload = json.dumps({
            "action": "change_email",
            "password": self.password,
            "email": self.email
        })
        response = self.client.put(self.endpoint, payload, content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_400_missing_password(self):
        payload = json.dumps({
            "action": "change_email",
            "email": self.email
        })
        response = self.client.put(self.endpoint, payload, content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_400_incorrect_password(self):
        payload = json.dumps({
            "action": "change_email",
            "password": "asdfasdfasdf",
            "email": self.email
        })
        response = self.client.put(self.endpoint, payload, content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_200_valid_email_change(self):
        payload = json.dumps({
            "action": "change_email",
            "password": self.password,
            "email": "vail130@gmail.com"
        })
        response = self.client.put(self.endpoint, payload, content_type='application/json')
        self.assertEqual(response.status_code, 200)

class AccountEditorPutChangePasswordTestCase(TestCase):
    def setUp(self):
        self.email = 'vail.gold@dressler-llc.com'
        self.password = 'danceparty'
        self.account = Account.create_account(self.email, self.password)
        self.account.status = 'active'
        self.account.save()
        self.client.login(username=self.account.user.username, password=self.password)
        self.endpoint = '/api/accounts/' + str(self.account.user_id)

    def tearDown(self):
        self.email = None
        self.password = None
        self.account = None
        self.endpoint = None

    def test_400_missing_new_password(self):
        payload = json.dumps({
            "action": "change_password",
            "old_password": self.password,
            })
        response = self.client.put(self.endpoint, payload, content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_400_invalid_old_password(self):
        payload = json.dumps({
            "action": "change_password",
            "old_password": "asdf",
            "new_password": "asdf",
            })
        response = self.client.put(self.endpoint, payload, content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_200_valid_password_change(self):
        payload = json.dumps({
            "action": "change_password",
            "old_password": self.password,
            "new_password": "asdf",
            })
        response = self.client.put(self.endpoint, payload, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.client.logout()

        self.client.login(username=self.account.user.username, password=self.password)
        response1 = self.client.get('/api/session')
        self.assertEqual(response1.status_code, 400)

        self.client.login(username=self.account.user.username, password="asdf")
        response2 = self.client.get('/api/session')
        self.assertEqual(response2.status_code, 200)

class AccountEditorPutResetPasswordTestCase(TestCase):
    def setUp(self):
        self.email = 'vail.gold@dressler-llc.com'
        self.password = 'danceparty'
        self.account = Account.create_account(self.email, self.password)
        self.account.status = 'active'
        self.account.save()
        payload = json.dumps({"action": "request_password_reset", "email": self.email})
        self.client.put('/api/accounts', payload, content_type='application/json')
        self.endpoint = '/api/accounts/' + str(self.account.user_id)

    def tearDown(self):
        self.email = None
        self.password = None
        self.account = None
        self.endpoint = None

    def test_400_missing_code(self):
        payload = json.dumps({
            "action": "reset_password",
            "password": "asdf",
            })
        response = self.client.put(self.endpoint, payload, content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_400_incorrect_code(self):
        ar = AccountRequest.objects.get(account=self.account, status='pending', type='reset-password')
        payload = json.dumps({
            "action": "reset_password",
            "code": "asdfasdfasdf",
            "password": "asdf",
            })
        response = self.client.put(self.endpoint, payload, content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_400_missing_new_password(self):
        ar = AccountRequest.objects.get(account=self.account, status='pending', type='reset-password')
        payload = json.dumps({
            "action": "reset_password",
            "code": ar.code,
            })
        response = self.client.put(self.endpoint, payload, content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_200_valid_password_change(self):
        ar = AccountRequest.objects.get(account=self.account, status='pending', type='reset-password')
        payload = json.dumps({
            "action": "reset_password",
            "code": ar.code,
            "password": "asdf",
            })
        response = self.client.put(self.endpoint, payload, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.client.logout()

        self.client.login(username=self.account.user.username, password=self.password)
        response1 = self.client.get('/api/session')
        self.assertEqual(response1.status_code, 400)

        self.client.login(username=self.account.user.username, password="asdf")
        response2 = self.client.get('/api/session')
        self.assertEqual(response2.status_code, 200)

class AccountEditorPutVerifySubaccountTestCase(TestCase):
    def setUp(self):
        self.email = 'vail.gold@dressler-llc.com'
        self.password = 'danceparty'
        self.account = Account.create_account(self.email, self.password)
        self.account.status = 'active'
        self.account.group = 'agency'
        self.account.save()
        self.client.login(username=self.account.user.username, password=self.password)
        payload = json.dumps({
            "type": "secondary",
            "email_list": ['vail130@gmail.com']
        })
        response = self.client.post('/api/accounts/', payload, content_type='application/json')
        self.client.logout()

    def tearDown(self):
        self.email = None
        self.password = None
        self.account = None

    def test_400_missing_password(self):
        sa = Account.objects.get(parent=self.account, status='pending', type='secondary')
        ar = AccountRequest.objects.get(account=sa, status='pending', type='create-secondary-account')
        payload = json.dumps({
            "action": "verify_subaccount",
            "code": ar.code,
            })
        response = self.client.put('/api/accounts/' + str(sa.id), payload, content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_400_missing_code(self):
        sa = Account.objects.get(parent=self.account, status='pending', type='secondary')
        payload = json.dumps({
            "action": "verify_subaccount",
            "password": "asdf",
            })
        response = self.client.put('/api/accounts/' + str(sa.id), payload, content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_400_incorrect_code(self):
        sa = Account.objects.get(parent=self.account, status='pending', type='secondary')
        payload = json.dumps({
            "action": "verify_subaccount",
            "code": "adfadfasdfasdf",
            "password": "asdf",
            })
        response = self.client.put('/api/accounts/' + str(sa.id), payload, content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_200_valid_password_change(self):
        sa = Account.objects.get(parent=self.account, status='pending', type='secondary')
        ar = AccountRequest.objects.get(account=sa, status='pending', type='create-secondary-account')
        payload = json.dumps({
            "action": "verify_subaccount",
            "code": ar.code,
            "password": "asdf",
            })
        response = self.client.put('/api/accounts/' + str(sa.id), payload, content_type='application/json')
        self.assertEqual(response.status_code, 200)

        self.client.login(username=sa.user.username, password="sdfsdfdfds")
        response1 = self.client.get('/api/session')
        self.assertEqual(response1.status_code, 400)

        self.client.login(username=sa.user.username, password="asdf")
        response2 = self.client.get('/api/session')
        self.assertEqual(response2.status_code, 200)

class AccountEditorPutUpgradeTestCase(TestCase):
    def setUp(self):
        self.email = 'vail.gold@dressler-llc.com'
        self.password = 'danceparty'
        self.account = Account.create_account(self.email, self.password)
        self.account.status = 'active'
        self.account.save()
        self.client.login(username=self.account.user.username, password=self.password)

    def tearDown(self):
        self.email = None
        self.password = None
        self.account = None

    def test_400_missing_password(self):
        payload = json.dumps({
            "action": "upgrade",
            "group": "agency",
            })
        response = self.client.put('/api/accounts/' + str(self.account.id), payload, content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_400_incorrect_password(self):
        payload = json.dumps({
            "action": "upgrade",
            "password": "asdf",
            "group": "agency",
            })
        response = self.client.put('/api/accounts/' + str(self.account.id), payload, content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_400_missing_group(self):
        payload = json.dumps({
            "action": "upgrade",
            "password": self.password,
            })
        response = self.client.put('/api/accounts/' + str(self.account.id), payload, content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_200_valid_agency_upgrade(self):
        payload = json.dumps({
            "action": "upgrade",
            "password": self.password,
            "group": "agency",
            })
        response = self.client.put('/api/accounts/' + str(self.account.id), payload, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content)['group'], 'agency')

    def test_200_valid_advertiser_upgrade(self):
        payload = json.dumps({
            "action": "upgrade",
            "password": self.password,
            "group": "advertiser",
            })
        response = self.client.put('/api/accounts/' + str(self.account.id), payload, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content)['group'], 'advertiser')

class AccountEditorPutTestCase(TestCase):
    def setUp(self):
        self.email = 'vail.gold@dressler-llc.com'
        self.password = 'danceparty'
        self.account = Account.create_account(self.email, self.password)
        self.account.status = 'active'
        self.account.save()
        self.client.login(username=self.account.user.username, password=self.password)

    def tearDown(self):
        self.email = None
        self.password = None
        self.account = None

    def test_200_update_name(self):
        payload = json.dumps({
            "first_name": "Vail",
            "last_name": "Gold",
        })
        response = self.client.put('/api/accounts/' + str(self.account.id), payload, content_type='application/json')
        self.assertEqual(response.status_code, 200)

class AccountEditorOtherTestCase(TestCase):
    def setUp(self):
        self.email = 'vail.gold@dressler-llc.com'
        self.password = 'danceparty'
        self.account = Account.create_account(self.email, self.password)
        self.client.login(username=self.account.user.username, password=self.password)
        self.account_id = self.account.user_id
        self.endpoint = '/api/accounts/' + str(self.account_id)

    def tearDown(self):
        self.email = None
        self.password = None
        self.account = None
        self.account_id = None
        self.endpoint = None

    def test_405_post_method_not_allowed(self):
        response = self.client.post(self.endpoint, {})
        self.assertEqual(response.status_code, 405)

class AccountEditorGetTestCase(TestCase):
    def setUp(self):
        self.email = 'vail.gold@dressler-llc.com'
        self.password = 'danceparty'
        self.account = Account.create_account(self.email, self.password)
        self.client.login(username=self.account.user.username, password=self.password)
        self.account_id = self.account.user_id
        self.endpoint = '/api/accounts/' + str(self.account_id)

    def tearDown(self):
        self.email = None
        self.password = None
        self.account = None
        self.account_id = None
        self.endpoint = None

    def test_400_mismatching_session_and_endpoint(self):
        response = self.client.get('/api/accounts/20')
        self.assertEqual(response.status_code, 400)

    def test_200_valid_request(self):
        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, 200)

class AccountEditorDeleteTestCase(TestCase):
    def setUp(self):
        self.email = 'vail.gold@dressler-llc.com'
        self.password = 'danceparty'
        self.account = Account.create_account(self.email, self.password)
        self.account.status = 'active'
        self.account.save()
        self.endpoint = '/api/accounts/' + str(self.account.user_id)

    def tearDown(self):
        self.email = None
        self.password = None
        self.account = None
        self.endpoint = None

    def test_400_wrong_password(self):
        payload = json.dumps({
            "email": self.email,
            "password": self.password
        })
        response0 = self.client.post('/api/session', payload, content_type='application/json')
        self.assertEqual(response0.status_code, 200)

        response = self.client.delete(self.endpoint + "?password=" + "asdf")
        self.assertEqual(response.status_code, 400)

    def test_400_missing_password(self):
        payload = json.dumps({
            "email": self.email,
            "password": self.password
        })
        response0 = self.client.post('/api/session', payload, content_type='application/json')
        self.assertEqual(response0.status_code, 200)

        response = self.client.delete(self.endpoint)
        self.assertEqual(response.status_code, 400)

    def test_400_wrong_endpoint(self):
        payload = json.dumps({
            "email": self.email,
            "password": self.password
        })
        response0 = self.client.post('/api/session', payload, content_type='application/json')
        self.assertEqual(response0.status_code, 200)

        response = self.client.delete('/api/accounts/22')
        self.assertEqual(response.status_code, 400)

    def test_200_valid_request(self):
        payload = json.dumps({
            "email": self.email,
            "password": self.password
        })
        response0 = self.client.post('/api/session', payload, content_type='application/json')
        self.assertEqual(response0.status_code, 200)

        response = self.client.delete(self.endpoint + "?password=" + self.password)
        self.assertEqual(response.status_code, 200)

        self.client.logout()
        payload = json.dumps({
            "email": self.email,
            "password": self.password
        })
        response1 = self.client.post('/api/session', payload, content_type='application/json')
        self.assertEqual(response1.status_code, 400)

