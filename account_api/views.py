from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate, login, logout
from account_api.models import Account, Contact

class SessionManager(APIView):
  """
  Handles HTTP requests to endpoint URL/api/sessions/ with optional querystring
  Allow: GET, POST
  """
  def get(self, request):
    if request.user.is_authenticated():
      return Response(data=[{"id": request.user.id}], status=status.HTTP_200_OK)
    else:
      return Response(status=status.HTTP_204_NO_CONTENT)
  
  def post(self, request):
    if request.user.is_authenticated():
      return Response(data={"id": request.user.id}, status=status.HTTP_200_OK)

    if 'email' not in request.DATA:
      error = {"email": "Missing email address field."}
      return Response(data=error, status=status.HTTP_400_BAD_REQUEST)

    if 'password' not in request.DATA:
      error = {"password": "Missing password field."}
      return Response(data=error, status=status.HTTP_400_BAD_REQUEST)
    
    email = str(request.DATA['email'])
    password = str(request.DATA['password'])
    
    try:
      account = Account.objects.get(email=email)
    except Account.DoesNotExist:
      error = {"email": "Email address is not in use."}
      return Response(data=error, status=status.HTTP_404_NOT_FOUND)

    if account.status != 'active':
      error = {"email": "Email address belongs to an invalid account."}
      return Response(data=error, status=status.HTTP_400_BAD_REQUEST)

    user = authenticate(username=account.user.username, password=password)
    if user is None:
      error = {"password": "Invalid password for email address."}
      return Response(data=error, status=status.HTTP_400_BAD_REQUEST)

    login(request, user)
    return Response(data={"id": user.id}, status=status.HTTP_201_CREATED)

class SessionEditor(APIView):
  """
  Handles HTTP requests to endpoint URL/api/sessions/:session_id with optional querystring
  Allow: GET, DELETE
  """
  def delete(self, request, session_id):
    if request.user.is_authenticated():
      logout(request)
    return Response(status=status.HTTP_204_NO_CONTENT)
  
  def get(self, request, session_id):
    if request.user.is_authenticated():
      return Response(data={"id": request.user.id}, status=status.HTTP_200_OK)
    else:
      return Response(status=status.HTTP_204_NO_CONTENT)

class AccountManager(APIView):
  """
  Handles HTTP requests to endpoint URL/api/accounts/ with optional querystring
  Allow: PUT, POST
  """
  def put(self, request):
    try:
      action = request.DATA['action']
    except KeyError:
      error = {"action": "Missing action."}
      return Response(data=error, status=status.HTTP_400_BAD_REQUEST)

    # Request to reset user's password
    if action == 'request_password_reset':
      try:
        email = request.DATA['email']
      except KeyError:
        error = {"email": "Missing email address."}
        return Response(data=error, status=status.HTTP_400_BAD_REQUEST)

      result = Account.request_reset_password(email)

    else:
      result = {"action": "Invalid action."}

    if isinstance(result, dict):
      return Response(data=result, status=status.HTTP_400_BAD_REQUEST)

    return Response(status=status.HTTP_204_NO_CONTENT)

  def get(self, request):
    if not request.user.is_authenticated():
      return Response(status=status.HTTP_401_UNAUTHORIZED)

    account = request.user.account
    if account.type is 'standard':
      return Response(data=account.read_record(), status=status.HTTP_200_OK)
      
    else:
      try:
        accounts = Account.objects.all()
      except Account.DoesNotExist:
        accounts = []
      
      account_list = [dict(acc.read_record(), **{"projects": list(acc.project_set.all())}) for acc in accounts]
      return Response(data=account_list, status=status.HTTP_200_OK)

  def post(self, request):
    if request.user.is_authenticated():
      error = {"session": "Unable to create new account with a valid session."}
      return Response(data=error, status=status.HTTP_400_BAD_REQUEST)

    try:
      email = request.DATA['email']
    except KeyError:
      error = {"email": "Missing email address field."}
      return Response(data=error, status=status.HTTP_400_BAD_REQUEST)

    try:
      password = request.DATA['password']
    except KeyError:
      error = {"password": "Missing password field."}
      return Response(data=error, status=status.HTTP_400_BAD_REQUEST)

    try:
      code = request.DATA['code']
    except KeyError:
      code = None

    account = Account.create_account(email, password, code=code)
    if not isinstance(account, Account):
      return Response(data=account, status=status.HTTP_400_BAD_REQUEST)

    return Response(data=account.read_record(), status=status.HTTP_200_OK)

class AccountEditor(APIView):
  """
  Handles HTTP requests to endpoint URL/api/accounts/:account_id/ with optional querystring
  Allow: GET, PUT, DELETE
  """
  def delete(self, request, account_id):
    if not request.user.is_authenticated():
      return Response(status=status.HTTP_401_UNAUTHORIZED)
    account = request.user.account
    account.status = 'terminated'
    account.save()
    return Response(status=status.HTTP_204_NO_CONTENT)
  
  def get(self, request, account_id):
    if not request.user.is_authenticated():
      return Response(status=status.HTTP_401_UNAUTHORIZED)
    
    user_account = request.user.account
    if user_account.type == 'standard':
      if user_account.user_id == int(account_id):
        return Response(data=user_account.read_record(), status=status.HTTP_200_OK)
      else:
        return Response(status=status.HTTP_404_NOT_FOUND)
    else:
      try:
        account = Account.objects.get(id=account_id)
      except Account.DoesNotExist:
        errors = {"account_id": "Invalid account ID."}
        return Response(data=errors, status=status.HTTP_400_BAD_REQUEST)
      else:
        return Response(data=account.read_record(), status=status.HTTP_200_OK)
  
  def put(self, request, account_id):
    try:
      action = request.DATA['action']
    except KeyError:
      action = None

    if action not in ['verify_email', 'verify_invitation', 'reset_password']:
      if not request.user.is_authenticated():
        return Response(status=status.HTTP_401_UNAUTHORIZED)
      else:
        account = request.user.account
    
    elif not request.user.is_authenticated():
      try:
        account = Account.objects.get(user_id=int(account_id))
      except Account.DoesNotExist:
        errors = {"account_id": "Invalid account ID."}
        return Response(data=errors, status=status.HTTP_400_BAD_REQUEST)

    # Request to prove that the user owns the email address
    if action == 'verify_email':
      try:
        code = request.DATA['code']
      except KeyError:
        error = {"code": "Missing verification code."}
        return Response(data=error, status=status.HTTP_400_BAD_REQUEST)

      result = account.verify_email(code)

    # Request to prove that the user owns the email address
    elif action == 'verify_invitation':
      try:
        code = request.DATA['code']
      except KeyError:
        error = {"code": "Missing verification code."}
        return Response(data=error, status=status.HTTP_400_BAD_REQUEST)

      try:
        password = request.DATA['password']
      except KeyError:
        error = {"password": "Missing password."}
        return Response(data=error, status=status.HTTP_400_BAD_REQUEST)

      result = account.verify_invitation(code, password)
      if not isinstance(result, dict):
        user = authenticate(username=account.user.username, password=password)
        login(request, user)

    # Request to change user's email address
    elif action == 'change_email':
      if account.status != 'active':
        error = {"account": "This account is inactive."}
        return Response(data=error, status=status.HTTP_400_BAD_REQUEST)

      try:
        password = request.DATA['password']
      except KeyError:
        error = {"password": "Missing password."}
        return Response(data=error, status=status.HTTP_400_BAD_REQUEST)

      try:
        email = request.DATA['email']
      except KeyError:
        error = {"email": "Missing email address."}
        return Response(data=error, status=status.HTTP_400_BAD_REQUEST)

      result = account.request_email_change(password, email)

    # Request to change a user's password
    elif action == 'change_password':
      if account.status != 'active':
        error = {"account": "This account is inactive."}
        return Response(data=error, status=status.HTTP_400_BAD_REQUEST)

      try:
        old_password = request.DATA['old_password']
      except KeyError:
        error = {"old_password": "Missing old password."}
        return Response(data=error, status=status.HTTP_400_BAD_REQUEST)

      try:
        new_password = request.DATA['new_password']
      except KeyError:
        error = {"new_password": "Missing new password."}
        return Response(data=error, status=status.HTTP_400_BAD_REQUEST)

      result = account.change_password(old_password, new_password)

    elif action == 'reset_password':
      if account.status != 'active':
        error = {"account": "This account is inactive."}
        return Response(data=error, status=status.HTTP_400_BAD_REQUEST)

      try:
        code = request.DATA['code']
      except KeyError:
        error = {"code": "Missing code."}
        return Response(data=error, status=status.HTTP_400_BAD_REQUEST)

      try:
        password = request.DATA['password']
      except KeyError:
        error = {"password": "Missing new password."}
        return Response(data=error, status=status.HTTP_400_BAD_REQUEST)

      result = account.reset_password(code, password)
      if not isinstance(result, dict):
        user = authenticate(username=account.user.username, password=password)
        login(request, user)

    else:
      if account.status != 'active':
        error = {"account": "This account is inactive."}
        return Response(data=error, status=status.HTTP_400_BAD_REQUEST)

      result = account.update_account(request.DATA)

    if isinstance(result, dict):
      return Response(data=result, status=status.HTTP_400_BAD_REQUEST)

    return Response(data=account.read_record(), status=status.HTTP_200_OK)

class ContactManager(APIView):
  """
  Handles HTTP requests to endpoint URL/api/contacts/ with optional querystring
  Allow: PUT, GET, POST
  """
  def get(self, request):
    if not request.user.is_authenticated() or request.user.account.type != 'administrator':
      return Response(status=status.HTTP_401_UNAUTHORIZED)
    
    try:
      contacts = Contact.objects.all()
    except Contact.DoesNotExist:
      contacts = []
    
    contact_list = [contact.read_record() for contact in contacts]
    return Response(data=contact_list, status=status.HTTP_200_OK)
  
  def post(self, request):
    if request.user.is_authenticated():
      account = request.user.account
    else:
      account = None
    
    contact = Contact.create_record(account, request.DATA)
    if not isinstance(contact, Contact):
        return Response(data=contact, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(data=contact.read_record(), status=status.HTTP_200_OK)

class ContactEditor(APIView):
  """
  Handles HTTP requests to endpoint URL/api/contacts/:contact_id/ with optional querystring
  Allow: GET, PUT
  """
  def get(self, request, contact_id):
    if not request.user.is_authenticated() or request.user.account.type != 'administrator':
      return Response(status=status.HTTP_401_UNAUTHORIZED)

    try:
      contact = Contact.objects.get(id=int(contact_id))
    except Contact.DoesNotExist:
      errors = {"contact_id": "Invalid contact ID."}
      return Response(data=errors, status=status.HTTP_404_NOT_FOUND)

    return Response(data=contact.read_record(), status=status.HTTP_200_OK)

  def put(self, request, contact_id):
    if not request.user.is_authenticated() or request.user.account.type != 'administrator':
      return Response(status=status.HTTP_401_UNAUTHORIZED)
    
    try:
      contact = Contact.objects.get(id=int(contact_id))
    except Contact.DoesNotExist:
      errors = {"contact_id": "Invalid contact ID."}
      return Response(data=errors, status=status.HTTP_404_NOT_FOUND)
    
    result = contact.update_record(request.DATA)
    if isinstance(result, dict):
      return Response(data=result, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(data=contact.read_record(), status=status.HTTP_200_OK)

