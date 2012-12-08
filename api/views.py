from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api.models import Account, Contact, Project, RequirementGroup, Requirement, Permission, ProjectAsset, ProjectFile
from django.conf import settings
from django.contrib.auth import authenticate, login, logout

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

      result = Account.request_password_reset(email)

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

    return Response(data=account.read_record(), status=status.HTTP_201_CREATED)

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
    if 'action' in request.DATA:
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
        if isinstance(result, dict):
          return Response(data=result, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(status=status.HTTP_204_NO_CONTENT)
  
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
        if isinstance(result, dict):
          return Response(data=result, status=status.HTTP_400_BAD_REQUEST)
        
        user = authenticate(username=account.user.username, password=password)
        login(request, user)
        return Response(status=status.HTTP_204_NO_CONTENT)
  
      elif action == 'verify_password_reset':
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
  
        result = account.verify_password_reset(code, password)
        if isinstance(result, dict):
          return Response(data=result, status=status.HTTP_400_BAD_REQUEST)
        
        user = authenticate(username=account.user.username, password=password)
        login(request, user)
        return Response(status=status.HTTP_204_NO_CONTENT)
      
      else:
        return Response(data={"action": "Invalid action."}, status=status.HTTP_400_BAD_REQUEST)
      
    else:
      if not request.user.is_authenticated():
        return Response(status=status.HTTP_401_UNAUTHORIZED)
      
      account = request.user.account
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
    
    return Response(data=contact.read_record(), status=status.HTTP_201_CREATED)

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


class ProjectManager(APIView):
  """
  Handles HTTP requests to endpoint URL/api/projects/ with optional querystring
  """
  def get(self, request):
    if not request.user.is_authenticated():
      return Response(status=status.HTTP_401_UNAUTHORIZED)
    
    account = request.user.account

    try:
      permissions = Permission.objects.filter(account=account)
    except Permission.DoesNotExist:
      errors = {"permission": "Invalid permissions."}
      return Response(data=errors, status=status.HTTP_400_BAD_REQUEST)

    project_list = [permission.project.read_record(permission=permission) for permission in permissions]
    return Response(data=project_list, status=status.HTTP_200_OK)

  def post(self, request):
    if not request.user.is_authenticated():
      return Response(status=status.HTTP_401_UNAUTHORIZED)
    
    account = request.user.account

    project = Project.create_record(account, request.DATA)
    if not isinstance(project, Project):
      return Response(data=project, status=status.HTTP_400_BAD_REQUEST)
    
    try:
      permission = Permission.objects.get(account=account, project=project)
    except Permission.DoesNotExist:
      errors = {"permission": "Failed to create permission."}
      return Response(data=errors, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(data=project.read_record(permission=permission), status=status.HTTP_201_CREATED)

class ProjectEditor(APIView):
  """
  Handles HTTP requests to endpoint URL/api/projects/:project_id/ with optional querystring
  """
  def delete(self, request, project_id):
    if not request.user.is_authenticated():
      return Response(status=status.HTTP_401_UNAUTHORIZED)
    
    account = request.user.account
    
    # test if id is a valid project identifier
    try:
      p = Project.objects.get(id=int(project_id), account=account)
    except Project.DoesNotExist:
      errors = {"id": "Invalid project ID."}
      return Response(data=errors, status=status.HTTP_404_NOT_FOUND)
    
    try:
      permission = Permission.objects.get(account=account, project=project)
    except Permission.DoesNotExist:
      errors = {"permission": "Invalid permission."}
      return Response(data=errors, status=status.HTTP_404_NOT_FOUND)

    result = p.delete_record(permission)
    if isinstance(result, dict):
      return Response(data=result, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(status=status.HTTP_204_NO_CONTENT)

  def get(self, request, project_id):
    if not request.user.is_authenticated():
      return Response(status=status.HTTP_401_UNAUTHORIZED)
    
    account = request.user.account
    
    try:
      permission = Permission.objects.get(account=account, project_id=int(project_id))
    except Permission.DoesNotExist:
      errors = {"permission": "Invalid permissions."}
      return Response(data=errors, status=status.HTTP_400_BAD_REQUEST)
    else:
      return Response(data=permission.project.read_record(permission=permission), status=status.HTTP_200_OK)

  def put(self, request, project_id):
    if not request.user.is_authenticated():
      return Response(status=status.HTTP_401_UNAUTHORIZED)
    
    account = request.user.account

    try:
      project = Project.objects.get(id=int(project_id))
    except Project.DoesNotExist:
      errors = {"project_id": "Invalid project ID."}
      return Response(data=errors, status=status.HTTP_404_NOT_FOUND)
    
    try:
      permission = Permission.objects.get(account=account, project=project)
    except Permission.DoesNotExist:
      errors = {"permission": "Invalid permissions."}
      return Response(data=errors, status=status.HTTP_400_BAD_REQUEST)

    project = project.update_record(permission, request.DATA)
    if not project or not isinstance(project, Project):
      return Response(data=project, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(data=project.read_record(permission=permission), status=status.HTTP_200_OK)


class PermissionManager(APIView):
  """
  Handles HTTP requests to endpoint URL/api/permissions/ with optional querystring
  """
  def get(self, request):
    if not request.user.is_authenticated():
      return Response(status=status.HTTP_401_UNAUTHORIZED)
    
    account = request.user.account
    
    #try:
    #  permissions = Permission.objects.filter(account=account, project__permissions__account=account)
    #except Permission.DoesNotExist:
    # permissions = []

    try:
      permissions = Permission.objects.filter(account=account)
    except Permission.DoesNotExist:
      permissions = []
    else:
      projects = [p.project for p in list(permissions)]
      try:
        permissions = Permission.objects.filter(project__in=projects)
      except Permission.DoesNotExist:
        permissions = []
      else:
        permission_list = [permission.read_record() for permission in permissions]
      
    return Response(data=permission_list, status=status.HTTP_200_OK)

  def post(self, request):
    if not request.user.is_authenticated():
      return Response(status=status.HTTP_401_UNAUTHORIZED)
    
    account = request.user.account
    
    # Must be project owner to create a permission
    try:
      project = Project.objects.get(id=int(request.DATA["project_id"]), account=account)
    except (Project.DoesNotExist, KeyError):
      errors = {"project_id": "Invalid project ID."}
      return Response(data=errors, status=status.HTTP_404_NOT_FOUND)

    try:
      email = str(request.DATA['email']).lower().strip()
    except KeyError:
      errors = {"email": "Missing email address."}
      return Response(data=errors, status=status.HTTP_400_BAD_REQUEST)
    
    try:
      p_account = Account.objects.get(email=email)
    except Account.DoesNotExist:
      p_account = Account.create_invitation_account(email)
      if isinstance(p_account, dict):
        return Response(data=p_account, status=status.HTTP_400_BAD_REQUEST)
    else:
      try:
        Permission.objects.get(project=project, account=p_account)
      except Permission.DoesNotExist:
        pass
      else:
        # Send a 30X response instead for PUT to correct endpoint?
        errors = {"email": "This email address already has a permission."}
        return Response(data=errors, status=status.HTTP_400_BAD_REQUEST)

    try:
      permission = str(request.DATA['permission'])
    except KeyError:
      permission = 'client'
    else:
      if permission not in ['client', 'coworker']:
        permission = 'client'
    
    perm = Permission.create_record(account, project, p_account, request.DATA)
    if not isinstance(perm, Permission):
      return Response(data=perm, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(data=perm.read_record(), status=status.HTTP_201_CREATED)

class PermissionEditor(APIView):
  """
  Handles HTTP requests to endpoint URL/api/permissions/:permission_id/ with optional querystring
  """
  def delete(self, request, permission_id):
    if not request.user.is_authenticated():
      return Response(status=status.HTTP_401_UNAUTHORIZED)
    
    account = request.user.account

    try:
      permission = Permission.objects.get(id=int(permission_id))
    except Permission.DoesNotExist:
      errors = {"permission_id": "Invalid permission ID."}
      return Response(data=errors, status=status.HTTP_404_NOT_FOUND)

    # Only admins can delete permissions
    if permission.project.account.id is not account_id:
      errors = {"permission": "Invalid permissions."}
      return Response(data=errors, status=status.HTTP_400_BAD_REQUEST)

    result = permission.delete_record(account)
    if isinstance(result, dict):
      return Response(data=result, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(data={}, status=status.HTTP_204_NO_CONTENT)

  def get(self, request, permission_id):
    if not request.user.is_authenticated():
      return Response(status=status.HTTP_401_UNAUTHORIZED)
    
    account = request.user.account

    try:
      permission = Permission.objects.get(id=int(permission_id))
    except Permission.DoesNotExist:
      errors = {"permission_id": "Invalid permission ID."}
      return Response(data=errors, status=status.HTTP_404_NOT_FOUND)

    if permission.project.account.id is not account_id:
      errors = {"permission": "Invalid permissions."}
      return Response(data=errors, status=status.HTTP_400_BAD_REQUEST)

    return Response(data=permission.read_record(), status=status.HTTP_200_OK)

  def put(self, request, permission_id):
    if not request.user.is_authenticated():
      return Response(status=status.HTTP_401_UNAUTHORIZED)
    
    account = request.user.account

    try:
      permission = Permission.objects.get(id=int(permission_id))
    except Permission.DoesNotExist:
      errors = {"permission_id": "Invalid permission ID."}
      return Response(data=errors, status=status.HTTP_404_NOT_FOUND)

    if permission.project.account.id is not account_id:
      errors = {"permission": "Invalid permissions."}
      return Response(data=errors, status=status.HTTP_400_BAD_REQUEST)
    
    result = permission.update_record(account, request.DATA)
    if isinstance(result, dict):
      return Response(data=result, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(data=result, status=status.HTTP_200_OK)


class GroupManager(APIView):
  """
  Handles HTTP requests to endpoint URL/api/groups/ with optional querystring
  """
  def get(self, request):
    if not request.user.is_authenticated():
      return Response(status=status.HTTP_401_UNAUTHORIZED)
    
    account = request.user.account
    
    try:
      groups = RequirementGroup.objects.filter(project__permission__account=account)
    except RequirementGroup.DoesNotExist:
      groups = []

    groups_list = [group.read_record() for group in groups]
    return Response(data=groups_list, status=status.HTTP_200_OK)

  def post(self, request):
    if not request.user.is_authenticated():
      return Response(status=status.HTTP_401_UNAUTHORIZED)
    
    account = request.user.account
    
    try:
      project = Project.objects.get(id=int(request.DATA["project_id"]))
    except (Project.DoesNotExist, KeyError):
      errors = {"project_id": "Invalid project ID."}
      return Response(data=errors, status=status.HTTP_404_NOT_FOUND)
    
    try:
      permission = Permission.objects.get(account=account, project=project)
    except Permission.DoesNotExist:
      errors = {"permission": "Invalid permissions."}
      return Response(data=errors, status=status.HTTP_400_BAD_REQUEST)

    group = RequirementGroup.create_record(permission, project, request.DATA)
    if not isinstance(group, RequirementGroup):
      return Response(data=group, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(data=group.read_record(), status=status.HTTP_201_CREATED)

class GroupEditor(APIView):
  """
  Handles HTTP requests to endpoint URL/api/groups/:group_id/ with optional querystring
  """
  def delete(self, request, group_id):
    if not request.user.is_authenticated():
      return Response(status=status.HTTP_401_UNAUTHORIZED)
    
    account = request.user.account

    try:
      group = RequirementGroup.objects.get(id=int(group_id))
    except RequirementGroup.DoesNotExist:
      errors = {"id": "Invalid group ID."}
      return Response(data=errors, status=status.HTTP_404_NOT_FOUND)
    
    if group.project.status == Project.statuses[2]:
      errors = {"project": "Project is locked."}
      return Response(data=errors, status=status.HTTP_400_BAD_REQUEST)

    try:
      permission = Permission.objects.get(account=account, project=group.project)
    except Permission.DoesNotExist:
      errors = {"permission": "Invalid permissions."}
      return Response(data=errors, status=status.HTTP_400_BAD_REQUEST)

    result = group.delete_record(permission)
    if isinstance(result, dict):
      return Response(data=result, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(data={}, status=status.HTTP_204_NO_CONTENT)

  def get(self, request, group_id):
    if not request.user.is_authenticated():
      return Response(status=status.HTTP_401_UNAUTHORIZED)
    
    account = request.user.account

    try:
      group = RequirementGroup.objects.get(id=int(group_id))
    except RequirementGroup.DoesNotExist:
      errors = {"group_id": "Invalid group ID."}
      return Response(data=errors, status=status.HTTP_404_NOT_FOUND)

    try:
      permissions = Permission.objects.get(account=account, project_id=group.project)
    except Permission.DoesNotExist:
      errors = {"permission": "Invalid permissions."}
      return Response(data=errors, status=status.HTTP_400_BAD_REQUEST)

    return Response(data=group.read_record(), status=status.HTTP_200_OK)

  def put(self, request, group_id):
    if not request.user.is_authenticated():
      return Response(status=status.HTTP_401_UNAUTHORIZED)
    
    account = request.user.account

    try:
      group = RequirementGroup.objects.get(id=int(group_id))
    except RequirementGroup.DoesNotExist:
      errors = {"project_id": "Invalid project ID."}
      return Response(data=errors, status=status.HTTP_404_NOT_FOUND)
    
    if group.project.status == Project.statuses[2]:
      errors = {"project": "Project is locked."}
      return Response(data=errors, status=status.HTTP_400_BAD_REQUEST)
    
    try:
      permission = Permission.objects.get(account=account, project=group.project)
    except Permission.DoesNotExist:
      errors = {"permission": "Invalid permissions."}
      return Response(data=errors, status=status.HTTP_400_BAD_REQUEST)

    result = group.update_record(permission, request.DATA)
    if isinstance(result, dict):
      return Response(data=result, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(data=result.read_record(), status=status.HTTP_200_OK)


class RequirementManager(APIView):
  """
  Handles HTTP requests to endpoint URL/api/requirements/ with optional querystring
  """
  def get(self, request):
    if not request.user.is_authenticated():
      return Response(status=status.HTTP_401_UNAUTHORIZED)
    
    account = request.user.account
      
    try:
      reqs = Requirement.objects.filter(group__project__permission__account=account)
    except Requirement.DoesNotExist:
      reqs = []

    req_list = [req.read_record() for req in reqs]
    return Response(data=req_list, status=status.HTTP_200_OK)

  def post(self, request):
    if not request.user.is_authenticated():
      return Response(status=status.HTTP_401_UNAUTHORIZED)
    
    account = request.user.account

    try:
      group = RequirementGroup.objects.get(id=int(request.DATA["group_id"]))
    except (RequirementGroup.DoesNotExist, KeyError):
      errors = {"group_id": "Invalid group ID."}
      return Response(data=errors, status=status.HTTP_404_NOT_FOUND)
    
    try:
      permission = Permission.objects.get(account=account, project=group.project)
    except Permission.DoesNotExist:
      errors = {"permission": "Invalid permissions."}
      return Response(data=errors, status=status.HTTP_400_BAD_REQUEST)

    req = Requirement.create_record(permission, group, request.DATA)
    if not isinstance(req, Requirement):
      return Response(data=req, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(data=req.read_record(), status=status.HTTP_201_CREATED)

class RequirementEditor(APIView):
  """
  Handles HTTP requests to endpoint URL/api/requirements/:req_id/ with optional querystring
  """
  def delete(self, request, req_id):
    if not request.user.is_authenticated():
      return Response(status=status.HTTP_401_UNAUTHORIZED)
    
    account = request.user.account

    try:
      req = Requirement.objects.get(id=int(req_id))
    except Requirement.DoesNotExist:
      errors = {"requirement_id": "Invalid requirement ID."}
      return Response(data=errors, status=status.HTTP_404_NOT_FOUND)
    
    try:
      permission = Permission.objects.get(account=account, project=req.group.project)
    except Permission.DoesNotExist:
      errors = {"permission": "Invalid permissions."}
      return Response(data=errors, status=status.HTTP_400_BAD_REQUEST)

    result = req.delete_record(permission)
    if isinstance(result, dict):
      return Response(data=result, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(data={}, status=status.HTTP_204_NO_CONTENT)

  def get(self, request, req_id):
    if not request.user.is_authenticated():
      return Response(status=status.HTTP_401_UNAUTHORIZED)
    
    account = request.user.account

    try:
      req = Requirement.objects.get(id=int(req_id))
    except Requirement.DoesNotExist:
      errors = {"requirement_id": "Invalid requirement ID."}
      return Response(data=errors, status=status.HTTP_404_NOT_FOUND)

    try:
      permissions = Permission.objects.get(account=account, project=req.group.project)
    except Permission.DoesNotExist:
      errors = {"permission": "Invalid permissions."}
      return Response(data=errors, status=status.HTTP_400_BAD_REQUEST)

    return Response(data=req.read_record(), status=status.HTTP_200_OK)

  def put(self, request, req_id):
    if not request.user.is_authenticated():
      return Response(status=status.HTTP_401_UNAUTHORIZED)
    
    account = request.user.account

    try:
      req = Requirement.objects.get(id=int(req_id))
    except Requirement.DoesNotExist:
      errors = {"requirement_id": "Invalid requirement ID."}
      return Response(data=errors, status=status.HTTP_404_NOT_FOUND)
    
    if req.group.project.status == Project.statuses[2]:
      errors = {"project": "Project is locked."}
      return Response(data=errors, status=status.HTTP_400_BAD_REQUEST)
      
    try:
      permission = Permission.objects.get(account=account, project=req.group.project)
    except Permission.DoesNotExist:
      errors = {"permission": "Invalid permissions."}
      return Response(data=errors, status=status.HTTP_400_BAD_REQUEST)
    
    result = req.update_record(permission, request.DATA)
    if isinstance(result, dict):
      return Response(data=result, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(data=result.read_record(), status=status.HTTP_200_OK)


class AssetManager(APIView):
  """
  Handles HTTP requests to endpoint URL/api/assets/ with optional querystring
  """
  def get(self, request):
    if not request.user.is_authenticated():
      return Response(status=status.HTTP_401_UNAUTHORIZED)
    
    account = request.user.account
    projects = [permission.project for permission in account.permission_set.all()]
    try:
      assets = ProjectAsset.objects.filter(project__in=projects)
    except ProjectAsset.DoesNotExist:
      assets = []

    assets_list = [asset.read_record() for asset in assets]
    return Response(data=assets_list, status=status.HTTP_200_OK)

  def post(self, request):
    if not request.user.is_authenticated():
      return Response(status=status.HTTP_401_UNAUTHORIZED)
    
    account = request.user.account
    
    try:
      project = Project.objects.get(id=int(request.DATA["project_id"]))
    except (Project.DoesNotExist, KeyError):
      errors = {"project_id": "Invalid project ID."}
      return Response(data=errors, status=status.HTTP_404_NOT_FOUND)
    
    try:
      permission = Permission.objects.get(account=account, project=project)
    except Permission.DoesNotExist:
      errors = {"permission": "Invalid permissions."}
      return Response(data=errors, status=status.HTTP_400_BAD_REQUEST)

    asset = ProjectAsset.create_record(permission, project, request.DATA)
    if not isinstance(asset, ProjectAsset):
      return Response(data=asset, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(data=asset.read_record(), status=status.HTTP_201_CREATED)

class AssetEditor(APIView):
  """
  Handles HTTP requests to endpoint URL/api/assets/:asset_id/ with optional querystring
  """
  def delete(self, request, asset_id):
    if not request.user.is_authenticated():
      return Response(status=status.HTTP_401_UNAUTHORIZED)
    
    account = request.user.account

    try:
      asset = ProjectAsset.objects.get(id=int(asset_id))
    except ProjectAsset.DoesNotExist:
      errors = {"id": "Invalid asset ID."}
      return Response(data=errors, status=status.HTTP_404_NOT_FOUND)
    
    if asset.project.status == Project.statuses[2]:
      errors = {"project": "Project is locked."}
      return Response(data=errors, status=status.HTTP_400_BAD_REQUEST)

    try:
      permission = Permission.objects.get(account=account, project=asset.project)
    except Permission.DoesNotExist:
      errors = {"permission": "Invalid permissions."}
      return Response(data=errors, status=status.HTTP_400_BAD_REQUEST)

    result = asset.delete_record(permission)
    if isinstance(result, dict):
      return Response(data=result, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(status=status.HTTP_204_NO_CONTENT)

  def get(self, request, asset_id):
    if not request.user.is_authenticated():
      return Response(status=status.HTTP_401_UNAUTHORIZED)
    
    account = request.user.account

    try:
      asset = ProjectAsset.objects.get(id=int(asset_id))
    except ProjectAsset.DoesNotExist:
      errors = {"id": "Invalid asset ID."}
      return Response(data=errors, status=status.HTTP_404_NOT_FOUND)

    try:
      permissions = Permission.objects.get(account=account, project_id=asset.project)
    except Permission.DoesNotExist:
      errors = {"permission": "Invalid permissions."}
      return Response(data=errors, status=status.HTTP_400_BAD_REQUEST)

    return Response(data=asset.read_record(), status=status.HTTP_200_OK)

  def put(self, request, asset_id):
    if not request.user.is_authenticated():
      return Response(status=status.HTTP_401_UNAUTHORIZED)
    
    account = request.user.account

    try:
      asset = ProjectAsset.objects.get(id=int(asset_id))
    except ProjectAsset.DoesNotExist:
      errors = {"project_id": "Invalid project ID."}
      return Response(data=errors, status=status.HTTP_404_NOT_FOUND)
    
    if asset.project.status == Project.statuses[2]:
      errors = {"project": "Project is locked."}
      return Response(data=errors, status=status.HTTP_400_BAD_REQUEST)
    
    try:
      permission = Permission.objects.get(account=account, project=asset.project)
    except Permission.DoesNotExist:
      errors = {"permission": "Invalid permissions."}
      return Response(data=errors, status=status.HTTP_400_BAD_REQUEST)

    result = asset.update_record(permission, request.DATA)
    if isinstance(result, dict):
      return Response(data=result, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(data=result.read_record(), status=status.HTTP_200_OK)


class FileManager(APIView):
  """
  Handles HTTP requests to endpoint URL/api/files/ with optional querystring
  """
  def get(self, request):
    if not request.user.is_authenticated():
      return Response(status=status.HTTP_401_UNAUTHORIZED)
    
    account = request.user.account
    projects = [permission.project for permission in account.permission_set.all()]
    try:
      project_files = ProjectFile.objects.filter(project__in=projects)
    except ProjectFile.DoesNotExist:
      project_files = []

    project_files_list = [project_file.read_record() for project_file in project_files]
    return Response(data=project_files_list, status=status.HTTP_200_OK)

  def post(self, request):
    if not request.user.is_authenticated():
      return Response(status=status.HTTP_401_UNAUTHORIZED)
    
    account = request.user.account
    
    try:
      project = Project.objects.get(id=int(request.DATA["project_id"]))
    except (Project.DoesNotExist, KeyError):
      errors = {"project_id": "Invalid project ID."}
      return Response(data=errors, status=status.HTTP_404_NOT_FOUND)
    
    try:
      permission = Permission.objects.get(account=account, project=project)
    except Permission.DoesNotExist:
      errors = {"permission": "Invalid permissions."}
      return Response(data=errors, status=status.HTTP_400_BAD_REQUEST)

    project_file = ProjectFile.create_record(permission, project, request.DATA)
    if not isinstance(project_file, ProjectFile):
      return Response(data=project_file, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(data=project_file.read_record(), status=status.HTTP_201_CREATED)

class FileEditor(APIView):
  """
  Handles HTTP requests to endpoint URL/api/files/:project_file_id/ with optional querystring
  """
  def delete(self, request, project_file_id):
    if not request.user.is_authenticated():
      return Response(status=status.HTTP_401_UNAUTHORIZED)
    
    account = request.user.account

    try:
      project_file = ProjectFile.objects.get(id=int(project_file_id))
    except ProjectFile.DoesNotExist:
      errors = {"id": "Invalid file ID."}
      return Response(data=errors, status=status.HTTP_404_NOT_FOUND)
    
    if project_file.project.status == Project.statuses[2]:
      errors = {"project": "Project is locked."}
      return Response(data=errors, status=status.HTTP_400_BAD_REQUEST)

    try:
      permission = Permission.objects.get(account=account, project=project_file.project)
    except Permission.DoesNotExist:
      errors = {"permission": "Invalid permissions."}
      return Response(data=errors, status=status.HTTP_400_BAD_REQUEST)

    result = project_file.delete_record(permission)
    if isinstance(result, dict):
      return Response(data=result, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(status=status.HTTP_204_NO_CONTENT)

  def get(self, request, project_file_id):
    if not request.user.is_authenticated():
      return Response(status=status.HTTP_401_UNAUTHORIZED)
    
    account = request.user.account

    try:
      project_file = ProjectFile.objects.get(id=int(project_file_id))
    except ProjectFile.DoesNotExist:
      errors = {"id": "Invalid file ID."}
      return Response(data=errors, status=status.HTTP_404_NOT_FOUND)

    try:
      permissions = Permission.objects.get(account=account, project_id=project_file.project)
    except Permission.DoesNotExist:
      errors = {"permission": "Invalid permissions."}
      return Response(data=errors, status=status.HTTP_400_BAD_REQUEST)

    return Response(data=project_file.read_record(), status=status.HTTP_200_OK)

  def put(self, request, project_file_id):
    if not request.user.is_authenticated():
      return Response(status=status.HTTP_401_UNAUTHORIZED)
    
    account = request.user.account

    try:
      project_file = ProjectFile.objects.get(id=int(project_file_id))
    except ProjectFile.DoesNotExist:
      errors = {"project_id": "Invalid project ID."}
      return Response(data=errors, status=status.HTTP_404_NOT_FOUND)
    
    if project_file.project.status == Project.statuses[2]:
      errors = {"project": "Project is locked."}
      return Response(data=errors, status=status.HTTP_400_BAD_REQUEST)
    
    try:
      permission = Permission.objects.get(account=account, project=project_file.project)
    except Permission.DoesNotExist:
      errors = {"permission": "Invalid permissions."}
      return Response(data=errors, status=status.HTTP_400_BAD_REQUEST)

    result = project_file.update_record(permission, request.DATA)
    if isinstance(result, dict):
      return Response(data=result, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(data=result.read_record(), status=status.HTTP_200_OK)












