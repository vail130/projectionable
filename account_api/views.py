from djangorestframework.views import View
from djangorestframework.response import Response
from djangorestframework import status
from django.contrib.auth import authenticate, login
from account_api.models import Account, Contact

class SessionManager(View):
    """
    Handles HTTP requests to endpoint URL/api/sessions/ with optional querystring
    Allow: GET, POST
    """
    def put(self, request):
        #################
        # Setup
        #################

        headers = {
            "Content-Type": "application/json",
            "Allow": "GET, POST",
        }

        errors = {"header_request_method": "This endpoint only supports GET and POST requests."}
        return Response(content=errors, headers=headers, status=status.HTTP_405_METHOD_NOT_ALLOWED)
    
    def delete(self, request):
        #################
        # Setup
        #################

        headers = {
            "Content-Type": "application/json",
            "Allow": "GET, POST",
        }

        errors = {"header_request_method": "This endpoint only supports GET and POST requests."}
        return Response(content=errors, headers=headers, status=status.HTTP_405_METHOD_NOT_ALLOWED)
    
    def get(self, request):
        #################
        # Setup
        #################

        headers = {
            "Content-Type": "application/json",
            "Allow": "GET, POST",
        }

        try:
            session_id = int(request.session["_auth_user_id"])
        except KeyError:
            return Response(content=[{"id": None}], headers=headers, status=status.HTTP_200_OK)
        else:
            return Response(content=[{"id": session_id}], headers=headers, status=status.HTTP_200_OK)
    
    def post(self, request):
        #################
        # Setup
        #################

        headers = {
            "Content-Type": "application/json",
            "Allow": "GET, POST",
        }

        # Check content-type header
        if not self.content_type.startswith('application/json'):
            errors = {"header_content_type": "Content-Type must be 'application/json'. Your Content-Type is " + str(self.content_type)}
            return Response(content=errors, headers=headers, status=status.HTTP_400_BAD_REQUEST)

        try:
            session_id = int(request.session["_auth_user_id"])
        except KeyError:
            pass
        else:
            return Response(content={"id": session_id}, headers=headers, status=status.HTTP_200_OK)

        try:
            email = self.CONTENT['email']
        except KeyError:
            error = {"email": "Missing email address field."}
            return Response(content=error, headers=headers, status=status.HTTP_400_BAD_REQUEST)

        try:
            password = self.CONTENT['password']
        except KeyError:
            error = {"password": "Missing password field."}
            return Response(content=error, headers=headers, status=status.HTTP_400_BAD_REQUEST)

        try:
            account = Account.objects.get(email=email)
        except Account.DoesNotExist:
            error = {"email": "Email address is not in use."}
            return Response(content=error, headers=headers, status=status.HTTP_400_BAD_REQUEST)

        if account.status != 'active':
            error = {"email": "Email address belongs to an invalid account."}
            return Response(content=error, headers=headers, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(username=account.user.username, password=password)
        if user is None:
            error = {"password": "Invalid password for email address."}
            return Response(content=error, headers=headers, status=status.HTTP_400_BAD_REQUEST)

        login(request, user)

        return Response(content={"id": account.id}, headers=headers, status=status.HTTP_200_OK)

class SessionEditor(View):
    """
    Handles HTTP requests to endpoint URL/api/sessions/:session_id with optional querystring
    Allow: GET, DELETE
    """
    def put(self, request, session_id):
        #################
        # Setup
        #################

        headers = {
            "Content-Type": "application/json",
            "Allow": "GET, DELETE",
        }

        errors = {"header_request_method": "This endpoint only supports GET and DELETE requests."}
        return Response(content=errors, headers=headers, status=status.HTTP_405_METHOD_NOT_ALLOWED)
    
    def post(self, request, session_id):
        #################
        # Setup
        #################

        headers = {
            "Content-Type": "application/json",
            "Allow": "GET, DELETE",
        }

        errors = {"header_request_method": "This endpoint only supports GET and DELETE requests."}
        return Response(content=errors, headers=headers, status=status.HTTP_405_METHOD_NOT_ALLOWED)
    
    def delete(self, request, session_id):
        #################
        # Setup
        #################

        headers = {
            "Content-Type": "application/json",
            "Allow": "GET, DELETE",
        }

        try:
            request.session["_auth_user_id"]
        except KeyError:
            pass
        else:
            del request.session["_auth_user_id"]
        
        return Response(content={"id": None}, headers=headers, status=status.HTTP_200_OK)
    
    def get(self, request, session_id):
        #################
        # Setup
        #################

        headers = {
            "Content-Type": "application/json",
            "Allow": "GET, DELETE",
        }

        try:
            request.session["_auth_user_id"]
        except KeyError:
            return Response(content={"id": None}, headers=headers, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(content={"id": int(session_id)}, headers=headers, status=status.HTTP_200_OK)

class AccountManager(View):
    """
    Handles HTTP requests to endpoint URL/api/accounts/ with optional querystring
    Allow: PUT, POST
    """
    def put(self, request):
        #################
        # Setup
        #################

        headers = {
            "Content-Type": "application/json",
            "Allow": "GET, POST",
        }

        # Check content-type header
        if not self.content_type.startswith('application/json'):
            errors = {"header_content_type": "Content-Type must be 'application/json'. Your Content-Type is " + str(self.content_type)}
            return Response(content=errors, headers=headers, status=status.HTTP_400_BAD_REQUEST)

        try:
            action = self.CONTENT['action']
        except KeyError:
            error = {"action": "Missing action."}
            return Response(content=error, headers=headers, status=status.HTTP_400_BAD_REQUEST)

        #################
        # Validation
        #################

        # Request to reset user's password
        if action == 'request_password_reset':
            try:
                email = self.CONTENT['email']
            except KeyError:
                error = {"email": "Missing email address."}
                return Response(content=error, headers=headers, status=status.HTTP_400_BAD_REQUEST)

            result = Account.request_reset_password(email)

        else:
            result = {"action": "Invalid action."}

        if isinstance(result, dict):
            return Response(content=result, headers=headers, status=status.HTTP_400_BAD_REQUEST)

        return Response(content={}, headers=headers, status=status.HTTP_200_OK)

    def delete(self, request):
        #################
        # Setup
        #################

        headers = {
            "Content-Type": "application/json",
            "Allow": "GET, POST",
        }

        try:
            request.session["_auth_user_id"]
        except KeyError:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        #################
        # Validation
        #################

        errors = {"header_request_method": "This endpoint only supports POST requests."}
        return Response(content=errors, headers=headers, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def get(self, request):
        #################
        # Setup
        #################

        headers = {
            "Content-Type": "application/json",
            "Allow": "GET, POST",
            }

        try:
            account_id = int(request.session["_auth_user_id"])
        except KeyError:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        try:
            account = Account.objects.get(user_id=account_id)
        except Account.DoesNotExist:
            errors = {"account_id": "Invalid account ID."}
            return Response(content=errors, headers=headers, status=status.HTTP_404_NOT_FOUND)

        #################
        # Operation
        #################

        if account.type is 'standard':
            return Response(content=account.record_to_dictionary(), headers=headers, status=status.HTTP_200_OK)
          
        else:
            try:
                accounts = Account.objects.all()
            except Account.DoesNotExist:
                accounts = []
            
            account_list = [acc.record_to_dictionary() for acc in accounts]
            return Response(content=account_list, headers=headers, status=status.HTTP_200_OK)

    def post(self, request):
        #################
        # Setup
        #################

        headers = {
            "Content-Type": "application/json",
            "Allow": "GET, POST",
        }

        # Check content-type header
        if not self.content_type.startswith('application/json'):
            errors = {"header_content_type": "Content-Type must be 'application/json'. Your Content-Type is " + str(self.content_type)}
            return Response(content=errors, headers=headers, status=status.HTTP_400_BAD_REQUEST)

        try:
            request.session["_auth_user_id"]
        except KeyError:
            pass
        else:
            error = {"session": "Unable to create new account with a valid session."}
            return Response(content=error, headers=headers, status=status.HTTP_400_BAD_REQUEST)

        try:
            email = self.CONTENT['email']
        except KeyError:
            error = {"email": "Missing email address field."}
            return Response(content=error, headers=headers, status=status.HTTP_400_BAD_REQUEST)

        try:
            password = self.CONTENT['password']
        except KeyError:
            error = {"password": "Missing password field."}
            return Response(content=error, headers=headers, status=status.HTTP_400_BAD_REQUEST)

        account = Account.create_account(email, password)
        if not isinstance(account, Account):
            return Response(content=account, headers=headers, status=status.HTTP_400_BAD_REQUEST)

        return Response(content=account.record_to_dictionary(), headers=headers, status=status.HTTP_200_OK)

class AccountEditor(View):
    """
    Handles HTTP requests to endpoint URL/api/accounts/:account_id/ with optional querystring
    Allow: GET, PUT, DELETE
    """
    def post(self, request, account_id):
        #################
        # Setup
        #################

        headers = {
            "Content-Type": "application/json",
            "Allow": "GET, PUT, DELETE",
        }

        #################
        # Validation
        #################

        try:
            request.session["_auth_user_id"]
        except KeyError:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        errors = {"header_request_method": "This endpoint only supports GET, PUT and DELETE requests."}
        return Response(content=errors, headers=headers, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def delete(self, request, account_id):
        #################
        # Setup
        #################

        headers = {
            "Content-Type": "application/json",
            "Allow": "GET, PUT, DELETE",
        }

        query_dict = dict([(k,v) for k,v in request.GET.iteritems()])

        #################
        # Validation
        #################

        try:
            request.session["_auth_user_id"]
        except KeyError:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        if int(account_id) is not int(request.session["_auth_user_id"]):
            errors = {"account_id": "Your session does not match your API endpoint account ID."}
            return Response(content=errors, headers=headers, status=status.HTTP_400_BAD_REQUEST)

        try:
            account = Account.objects.get(user_id=account_id)
        except Account.DoesNotExist:
            errors = {"account_id": "Invalid account ID."}
            return Response(content=errors, headers=headers, status=status.HTTP_400_BAD_REQUEST)

        #################
        # Operation
        #################

        if 'password' not in query_dict:
            errors = {"password": "Password is required to delete account."}
            return Response(content=errors, headers=headers, status=status.HTTP_400_BAD_REQUEST)

        if query_dict['password'] == '':
            errors = {"password": "Password cannot be an empty string."}
            return Response(content=errors, headers=headers, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(username=account.user.username, password=query_dict['password'])
        if user is None:
            errors = {"password": "Invalid password."}
            return Response(content=errors, headers=headers, status=status.HTTP_400_BAD_REQUEST)

        account.status = 'terminated'
        account.save()

        return Response(content={}, headers=headers, status=status.HTTP_200_OK)

    def get(self, request, account_id):
        #################
        # Setup
        #################

        headers = {
            "Content-Type": "application/json",
            "Allow": "GET, PUT, DELETE",
        }

        query_dict = dict([(k,v) for k,v in request.GET.iteritems()])

        #################
        # Validation
        #################

        try:
            request.session["_auth_user_id"]
        except KeyError:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        if int(account_id) is not int(request.session["_auth_user_id"]):
            errors = {"account_id": "Your session does not match your API endpoint account ID."}
            return Response(content=errors, headers=headers, status=status.HTTP_400_BAD_REQUEST)

        try:
            account = Account.objects.get(user_id=account_id)
        except Account.DoesNotExist:
            errors = {"account_id": "Invalid account ID."}
            return Response(content=errors, headers=headers, status=status.HTTP_400_BAD_REQUEST)

        #################
        # Operation
        #################

        return Response(content=account.record_to_dictionary(), headers=headers, status=status.HTTP_200_OK)

    def put(self, request, account_id):
        #################
        # Setup
        #################

        headers = {
            "Content-Type": "application/json",
            "Allow": "GET, PUT, DELETE",
        }

        #################
        # Validation
        #################

        try:
            action = self.CONTENT['action']
        except KeyError:
            action = None

        if action not in ['verify_email', 'verify_invitation', 'reset_password']:
            try:
                request.session["_auth_user_id"]
            except KeyError:
                return Response(status=status.HTTP_401_UNAUTHORIZED)

        # Check content-type header
        if not self.content_type.startswith('application/json'):
            errors = {"header_content_type": "Content-Type must be 'application/json'. Your Content-Type is " + str(self.content_type)}
            return Response(content=errors, headers=headers, status=status.HTTP_400_BAD_REQUEST)

        if action not in ['verify_email', 'verify_invitation', 'reset_password']:
            if int(account_id) is not int(request.session["_auth_user_id"]):
                errors = {"account_id": "Your session does not match your API endpoint account ID."}
                return Response(content=errors, headers=headers, status=status.HTTP_400_BAD_REQUEST)

        # Check content-type header
        if not self.content_type.startswith('application/json'):
            errors = {"header_content_type": "Content-Type must be 'application/json'. Your Content-Type is " + str(self.content_type)}
            return Response(content=errors, headers=headers, status=status.HTTP_400_BAD_REQUEST)

        try:
            account = Account.objects.get(id=account_id)
        except Account.DoesNotExist:
            errors = {"account_id": "Invalid account ID."}
            return Response(content=errors, headers=headers, status=status.HTTP_400_BAD_REQUEST)

        #################
        # Operation
        #################

        # Request to prove that the user owns the email address
        if action == 'verify_email':
            try:
                code = self.CONTENT['code']
            except KeyError:
                error = {"code": "Missing verification code."}
                return Response(content=error, headers=headers, status=status.HTTP_400_BAD_REQUEST)

            result = account.verify_email(code)

        # Request to prove that the user owns the email address
        elif action == 'verify_invitation':
            try:
                code = self.CONTENT['code']
            except KeyError:
                error = {"code": "Missing verification code."}
                return Response(content=error, headers=headers, status=status.HTTP_400_BAD_REQUEST)

            try:
                password = self.CONTENT['password']
            except KeyError:
                error = {"password": "Missing password."}
                return Response(content=error, headers=headers, status=status.HTTP_400_BAD_REQUEST)

            result = account.verify_invitation(code, password)
            if not isinstance(result, dict):
              user = authenticate(username=account.user.username, password=password)
              login(request, user)

        # Request to change user's email address
        elif action == 'change_email':
            if account.status != 'active':
                error = {"account": "This account is inactive."}
                return Response(content=error, headers=headers, status=status.HTTP_400_BAD_REQUEST)

            try:
                password = self.CONTENT['password']
            except KeyError:
                error = {"password": "Missing password."}
                return Response(content=error, headers=headers, status=status.HTTP_400_BAD_REQUEST)

            try:
                email = self.CONTENT['email']
            except KeyError:
                error = {"email": "Missing email address."}
                return Response(content=error, headers=headers, status=status.HTTP_400_BAD_REQUEST)

            result = account.request_email_change(password, email)

        # Request to change a user's password
        elif action == 'change_password':
            if account.status != 'active':
                error = {"account": "This account is inactive."}
                return Response(content=error, headers=headers, status=status.HTTP_400_BAD_REQUEST)

            try:
                old_password = self.CONTENT['old_password']
            except KeyError:
                error = {"old_password": "Missing old password."}
                return Response(content=error, headers=headers, status=status.HTTP_400_BAD_REQUEST)

            try:
                new_password = self.CONTENT['new_password']
            except KeyError:
                error = {"new_password": "Missing new password."}
                return Response(content=error, headers=headers, status=status.HTTP_400_BAD_REQUEST)

            result = account.change_password(old_password, new_password)

        elif action == 'reset_password':
            if account.status != 'active':
                error = {"account": "This account is inactive."}
                return Response(content=error, headers=headers, status=status.HTTP_400_BAD_REQUEST)

            try:
                code = self.CONTENT['code']
            except KeyError:
                error = {"code": "Missing code."}
                return Response(content=error, headers=headers, status=status.HTTP_400_BAD_REQUEST)

            try:
                password = self.CONTENT['password']
            except KeyError:
                error = {"password": "Missing new password."}
                return Response(content=error, headers=headers, status=status.HTTP_400_BAD_REQUEST)

            result = account.reset_password(code, password)
            if not isinstance(result, dict):
              user = authenticate(username=account.user.username, password=password)
              login(request, user)

        else:
            if account.status != 'active':
                error = {"account": "This account is inactive."}
                return Response(content=error, headers=headers, status=status.HTTP_400_BAD_REQUEST)

            result = account.update_account(self.CONTENT)

        if isinstance(result, dict):
            return Response(content=result, headers=headers, status=status.HTTP_400_BAD_REQUEST)

        return Response(content=account.record_to_dictionary(), headers=headers, status=status.HTTP_200_OK)

class ContactManager(View):
    """
    Handles HTTP requests to endpoint URL/api/contacts/ with optional querystring
    Allow: PUT, POST
    """
    def put(self, request):
        #################
        # Setup
        #################

        headers = {
            "Content-Type": "application/json",
            "Allow": "POST",
        }

        try:
            request.session["_auth_user_id"]
        except KeyError:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        #################
        # Validation
        #################

        errors = {"header_request_method": "This endpoint only supports POST requests."}
        return Response(content=errors, headers=headers, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def delete(self, request):
        #################
        # Setup
        #################

        headers = {
            "Content-Type": "application/json",
            "Allow": "POST",
        }

        try:
            request.session["_auth_user_id"]
        except KeyError:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        #################
        # Validation
        #################

        errors = {"header_request_method": "This endpoint only supports POST requests."}
        return Response(content=errors, headers=headers, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def get(self, request):
        #################
        # Setup
        #################

        headers = {
            "Content-Type": "application/json",
            "Allow": "POST",
        }

        try:
            account_id = int(request.session["_auth_user_id"])
        except KeyError:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        try:
            account = Account.objects.get(user_id=account_id)
        except Account.DoesNotExist:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
          
        if account.type is not 'administrator':
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        #################
        # Operation
        #################
        
        try:
            contacts = Contact.objects.all()
        except Contact.DoesNotExist:
            contacts = []

        contact_list = [contact.record_to_dictionary() for contact in contacts]
        return Response(content=contact_list, headers=headers, status=status.HTTP_200_OK)

    def post(self, request):
        #################
        # Setup
        #################

        headers = {
            "Content-Type": "application/json",
            "Allow": "POST",
        }

        # Check content-type header
        if not self.content_type.startswith('application/json'):
            errors = {"header_content_type": "Content-Type must be 'application/json'. Your Content-Type is " + str(self.content_type)}
            return Response(content=errors, headers=headers, status=status.HTTP_400_BAD_REQUEST)

        try:
            account_id = int(request.session["_auth_user_id"])
        except KeyError:
            pass
        else:
            try:
                account = Account.objects.get(user_id=account_id)
            except Account.DoesNotExist:
                account = None

        contact = Contact.create_record(account, self.CONTENT)
        if not isinstance(contact, Contact):
            return Response(content=contact, headers=headers, status=status.HTTP_400_BAD_REQUEST)

        return Response(content=contact.record_to_dictionary(), headers=headers, status=status.HTTP_200_OK)

class ContactEditor(View):
    """
    Handles HTTP requests to endpoint URL/api/contacts/:contact_id/ with optional querystring
    Allow: GET, PUT, DELETE
    """
    def post(self, request, contact_id):
        #################
        # Setup
        #################

        headers = {
            "Content-Type": "application/json",
            "Allow": "",
        }

        #################
        # Validation
        #################

        try:
            account_id = int(request.session["_auth_user_id"])
        except KeyError:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        try:
            account = Account.objects.get(user_id=account_id)
        except Account.DoesNotExist:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
          
        if account.type is not 'administrator':
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        errors = {"header_request_method": "This endpoint only supports GET, PUT and DELETE requests."}
        return Response(content=errors, headers=headers, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def delete(self, request, contact_id):
        #################
        # Setup
        #################

        headers = {
            "Content-Type": "application/json",
            "Allow": "",
        }

        query_dict = dict([(k,v) for k,v in request.GET.iteritems()])

        #################
        # Validation
        #################

        try:
            account_id = int(request.session["_auth_user_id"])
        except KeyError:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        try:
            account = Account.objects.get(user_id=account_id)
        except Account.DoesNotExist:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
          
        if account.type is not 'administrator':
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        #################
        # Operation
        #################

        errors = {"header_request_method": "This endpoint only supports GET and PUT requests."}
        return Response(content=errors, headers=headers, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def get(self, request, contact_id):
        #################
        # Setup
        #################

        headers = {
            "Content-Type": "application/json",
            "Allow": "GET, PUT, DELETE",
        }

        query_dict = dict([(k,v) for k,v in request.GET.iteritems()])

        #################
        # Validation
        #################

        try:
            account_id = int(request.session["_auth_user_id"])
        except KeyError:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        try:
            account = Account.objects.get(user_id=account_id)
        except Account.DoesNotExist:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
          
        if account.type is not 'administrator':
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        #################
        # Operation
        #################
        
        try:
            contact = Contact.objects.get(id=int(contact_id))
        except Contact.DoesNotExist:
            errors = {"contact_id": "Invalid contact ID."}
            return Response(content=errors, headers=headers, status=status.HTTP_404_NOT_FOUND)

        return Response(content=contact.record_to_dictionary(), headers=headers, status=status.HTTP_200_OK)

    def put(self, request, contact_id):
        #################
        # Setup
        #################

        headers = {
            "Content-Type": "application/json",
            "Allow": "",
        }

        #################
        # Validation
        #################

        try:
            account_id = int(request.session["_auth_user_id"])
        except KeyError:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        try:
            account = Account.objects.get(user_id=account_id)
        except Account.DoesNotExist:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
          
        if account.type is not 'administrator':
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        # Check content-type header
        if not self.content_type.startswith('application/json'):
            errors = {"header_content_type": "Content-Type must be 'application/json'. Your Content-Type is " + str(self.content_type)}
            return Response(content=errors, headers=headers, status=status.HTTP_400_BAD_REQUEST)

        #################
        # Operation
        #################

        try:
            contact = Contact.objects.get(id=int(contact_id))
        except Contact.DoesNotExist:
            errors = {"contact_id": "Invalid contact ID."}
            return Response(content=errors, headers=headers, status=status.HTTP_404_NOT_FOUND)

        result = contact.update_record(self.CONTENT)
        if isinstance(result, dict):
            return Response(content=result, headers=headers, status=status.HTTP_400_BAD_REQUEST)

        return Response(content=contact.record_to_dictionary(), headers=headers, status=status.HTTP_200_OK)

