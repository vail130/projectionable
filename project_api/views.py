from djangorestframework.views import View
from djangorestframework.response import Response
from djangorestframework import status
from project_api.models import Project, RequirementGroup, Requirement, Permission
from account_api.models import Account
from django.conf import settings
import datetime, json

class ProjectManager(View):
  """
  Handles HTTP requests to endpoint URL/api/projects/ with optional querystring
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

    #################
    # Validation
    #################

    try:
      request.session["_auth_user_id"]
    except KeyError:
      return Response(status=status.HTTP_401_UNAUTHORIZED)

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

    #################
    # Validation
    #################

    try:
      request.session["_auth_user_id"]
    except KeyError:
      return Response(status=status.HTTP_401_UNAUTHORIZED)

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
      errors = {"account_id": "Invalid account ID."}
      return Response(content=errors, headers=headers, status=status.HTTP_404_NOT_FOUND)

    # No content-type to check, because there's no payload

    #################
    # Operation
    #################

    try:
      permissions = Permission.objects.filter(account=account)
    except Permission.DoesNotExist:
      errors = {"permission": "Invalid permissions."}
      return Response(content=errors, headers=headers, status=status.HTTP_400_BAD_REQUEST)

    project_list = [perm.project.record_to_dictionary(account=account, children=False) for perm in permissions]

    return Response(content=project_list, headers=headers, status=status.HTTP_200_OK)

  def post(self, request):
    #################
    # Setup
    #################

    headers = {
      "Content-Type": "application/json",
      "Allow": "GET, POST",
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
      errors = {"account_id": "Invalid account ID."}
      return Response(content=errors, headers=headers, status=status.HTTP_404_NOT_FOUND)

    # Check content-type header
    if not self.content_type.startswith('application/json'):
      errors = {"header_content_type": "Content-Type must be 'application/json'. Your Content-Type is " + str(self.content_type)}
      return Response(content=errors, headers=headers, status=status.HTTP_400_BAD_REQUEST)

    #################
    # Operation
    #################

    project = Project.create_record(account, self.CONTENT)
    if not isinstance(project, Project):
      # HTTP status 422: Unprocessable Entity (WebDAV; RFC 4918)
      return Response(content=project, headers=headers, status=422)
    
    return Response(content=project.record_to_dictionary(account=account), headers=headers, status=status.HTTP_200_OK)

class ProjectEditor(View):
  """
  Handles HTTP requests to endpoint URL/api/projects/:project_id/ with optional querystring
  Allow: GET, PUT, DELETE
  """
  def post(self, request, project_id):
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

  def delete(self, request, project_id):
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
      account_id = int(request.session["_auth_user_id"])
    except KeyError:
      return Response(status=status.HTTP_401_UNAUTHORIZED)

    try:
      account = Account.objects.get(user_id=account_id)
    except Account.DoesNotExist:
      errors = {"account_id": "Invalid account ID."}
      return Response(content=errors, headers=headers, status=status.HTTP_404_NOT_FOUND)

    # test if id is a valid project identifier
    try:
      p = Project.objects.get(id=int(project_id), account=account)
    except Project.DoesNotExist:
      errors = {"id": "Invalid project ID."}
      return Response(content=errors, headers=headers, status=status.HTTP_404_NOT_FOUND)

    #################
    # Operation
    #################

    result = p.delete_record(account)
    if isinstance(result, dict):
      return Response(content=result, headers=headers, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(content={}, headers=headers, status=status.HTTP_200_OK)

  def get(self, request, project_id):
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
      errors = {"account_id": "Invalid account ID."}
      return Response(content=errors, headers=headers, status=status.HTTP_404_NOT_FOUND)

    try:
      permissions = Permission.objects.get(account=account, project_id=int(project_id))
    except Permission.DoesNotExist:
      errors = {"permission": "Invalid permissions."}
      return Response(content=errors, headers=headers, status=status.HTTP_400_BAD_REQUEST)

    #################
    # Operation
    #################

    return Response(content=permissions.project.record_to_dictionary(account=account, children=False), headers=headers, status=status.HTTP_200_OK)

  def put(self, request, project_id):
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
      account_id = int(request.session["_auth_user_id"])
    except KeyError:
      return Response(status=status.HTTP_401_UNAUTHORIZED)

    # Check content-type header
    if not self.content_type.startswith('application/json'):
      errors = {"header_content_type": "Content-Type must be 'application/json'. Your Content-Type is " + str(self.content_type)}
      return Response(content=errors, headers=headers, status=status.HTTP_400_BAD_REQUEST)

    try:
      account = Account.objects.get(user_id=account_id)
    except Account.DoesNotExist:
      errors = {"account_id": "Invalid account ID."}
      return Response(content=errors, headers=headers, status=status.HTTP_404_NOT_FOUND)

    try:
      project = Project.objects.get(id=project_id)
    except Project.DoesNotExist:
      errors = {"project_id": "Invalid project ID."}
      return Response(content=errors, headers=headers, status=status.HTTP_404_NOT_FOUND)
    
    try:
      permission = Permission.objects.get(
        account=account,
        project=project,
        permission__in=([Permission.permissions[0]] + [Permission.permissions[-1]])
      )
    except Permission.DoesNotExist:
      errors = {"permission": "Invalid permissions."}
      return Response(content=errors, headers=headers, status=status.HTTP_400_BAD_REQUEST)

    #################
    # Operation
    #################

    project = project.update_record(permission, self.CONTENT)
    if not project or not isinstance(project, Project):
      # HTTP status 422: Unprocessable Entity (WebDAV; RFC 4918)
      return Response(content=project, headers=headers, status=422)
    
    return Response(content=project.record_to_dictionary(account=account), headers=headers, status=status.HTTP_200_OK)

class GroupManager(View):
  """
  Handles HTTP requests to endpoint URL/api/groups/ with optional querystring
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

    #################
    # Validation
    #################

    try:
      request.session["_auth_user_id"]
    except KeyError:
      return Response(status=status.HTTP_401_UNAUTHORIZED)

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

    #################
    # Validation
    #################

    try:
      request.session["_auth_user_id"]
    except KeyError:
      return Response(status=status.HTTP_401_UNAUTHORIZED)

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
      errors = {"account_id": "Invalid account ID."}
      return Response(content=errors, headers=headers, status=status.HTTP_404_NOT_FOUND)

    # No content-type to check, because there's no payload

    #################
    # Operation
    #################
    
    try:
      groups = RequirementGroup.objects.filter(project__permission__account=account)
    except RequirementGroup.DoesNotExist:
      groups = []

    groups_list = [group.record_to_dictionary() for group in groups]

    return Response(content=groups_list, headers=headers, status=status.HTTP_200_OK)

  def post(self, request):
    #################
    # Setup
    #################

    headers = {
      "Content-Type": "application/json",
      "Allow": "GET, POST",
    }

    #################
    # Validation
    #################

    try:
      account_id = int(request.session["_auth_user_id"])
    except KeyError:
      return Response(status=status.HTTP_401_UNAUTHORIZED)

    # Check content-type header
    if not self.content_type.startswith('application/json'):
      errors = {"header_content_type": "Content-Type must be 'application/json'. Your Content-Type is " + str(self.content_type)}
      return Response(content=errors, headers=headers, status=status.HTTP_400_BAD_REQUEST)

    try:
      account = Account.objects.get(user_id=account_id)
    except Account.DoesNotExist:
      errors = {"account_id": "Invalid account ID."}
      return Response(content=errors, headers=headers, status=status.HTTP_404_NOT_FOUND)

    #################
    # Operation
    #################
    
    try:
      project_id = int(self.CONTENT["project_id"])
    except KeyError:
      errors = {"project_id": "Missing project ID."}
      return Response(content=errors, headers=headers, status=status.HTTP_404_NOT_FOUND)
    
    try:
      project = Project.objects.get(id=project_id)
    except Project.DoesNotExist:
      errors = {"project_id": "Invalid project ID."}
      return Response(content=errors, headers=headers, status=status.HTTP_404_NOT_FOUND)
      
    try:
      permission = Permission.objects.get(account=account, project=project)
    except Permission.DoesNotExist:
      errors = {"permission": "Invalid permissions."}
      return Response(content=errors, headers=headers, status=status.HTTP_400_BAD_REQUEST)

    group = RequirementGroup.create_record(permission, project, self.CONTENT)
    if not isinstance(group, RequirementGroup):
      # HTTP status 422: Unprocessable Entity (WebDAV; RFC 4918)
      return Response(content=group, headers=headers, status=422)
    
    return Response(content=group.record_to_dictionary(), headers=headers, status=status.HTTP_200_OK)

class GroupEditor(View):
  """
  Handles HTTP requests to endpoint URL/api/groups/:group_id/ with optional querystring
  Allow: GET, PUT, DELETE
  """
  def post(self, request, group_id):
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

  def delete(self, request, group_id):
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
      account_id = int(request.session["_auth_user_id"])
    except KeyError:
      return Response(status=status.HTTP_401_UNAUTHORIZED)

    try:
      account = Account.objects.get(user_id=account_id)
    except Account.DoesNotExist:
      errors = {"account_id": "Invalid account ID."}
      return Response(content=errors, headers=headers, status=status.HTTP_404_NOT_FOUND)

    try:
      group = RequirementGroup.objects.get(id=int(group_id))
    except RequirementGroup.DoesNotExist:
      errors = {"id": "Invalid group ID."}
      return Response(content=errors, headers=headers, status=status.HTTP_404_NOT_FOUND)

    try:
      permission = Permission.objects.get(account=account, project=group.project)
    except Permission.DoesNotExist:
      errors = {"permission": "Invalid permissions."}
      return Response(content=errors, headers=headers, status=status.HTTP_400_BAD_REQUEST)

    #################
    # Operation
    #################

    result = group.delete_record(permission)
    if isinstance(result, dict):
      return Response(content=result, headers=headers, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(content={}, headers=headers, status=status.HTTP_200_OK)

  def get(self, request, group_id):
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
      errors = {"account_id": "Invalid account ID."}
      return Response(content=errors, headers=headers, status=status.HTTP_404_NOT_FOUND)

    try:
      group = RequirementGroup.objects.get(id=int(group_id))
    except RequirementGroup.DoesNotExist:
      errors = {"group_id": "Invalid group ID."}
      return Response(content=errors, headers=headers, status=status.HTTP_404_NOT_FOUND)

    try:
      permissions = Permission.objects.get(account=account, project_id=group.project)
    except Permission.DoesNotExist:
      errors = {"permission": "Invalid permissions."}
      return Response(content=errors, headers=headers, status=status.HTTP_400_BAD_REQUEST)

    #################
    # Operation
    #################

    return Response(content=group.record_to_dictionary(), headers=headers, status=status.HTTP_200_OK)

  def put(self, request, group_id):
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
      account_id = int(request.session["_auth_user_id"])
    except KeyError:
      return Response(status=status.HTTP_401_UNAUTHORIZED)

    # Check content-type header
    if not self.content_type.startswith('application/json'):
      errors = {"header_content_type": "Content-Type must be 'application/json'. Your Content-Type is " + str(self.content_type)}
      return Response(content=errors, headers=headers, status=status.HTTP_400_BAD_REQUEST)

    try:
      account = Account.objects.get(user_id=account_id)
    except Account.DoesNotExist:
      errors = {"account_id": "Invalid account ID."}
      return Response(content=errors, headers=headers, status=status.HTTP_404_NOT_FOUND)

    try:
      group = RequirementGroup.objects.get(id=int(group_id))
    except RequirementGroup.DoesNotExist:
      errors = {"project_id": "Invalid project ID."}
      return Response(content=errors, headers=headers, status=status.HTTP_404_NOT_FOUND)
    
    try:
      permission = Permission.objects.get(account=account, project=group.project)
    except Permission.DoesNotExist:
      errors = {"permission": "Invalid permissions."}
      return Response(content=errors, headers=headers, status=status.HTTP_400_BAD_REQUEST)

    #################
    # Operation
    #################

    result = group.update_record(permission, self.CONTENT)
    if isinstance(result, dict):
      # HTTP status 422: Unprocessable Entity (WebDAV; RFC 4918)
      return Response(content=result, headers=headers, status=422)
    
    return Response(content=result.record_to_dictionary(), headers=headers, status=status.HTTP_200_OK)

class RequirementManager(View):
  """
  Handles HTTP requests to endpoint URL/api/requirements/ with optional querystring
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

    #################
    # Validation
    #################

    try:
      request.session["_auth_user_id"]
    except KeyError:
      return Response(status=status.HTTP_401_UNAUTHORIZED)

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

    #################
    # Validation
    #################

    try:
      request.session["_auth_user_id"]
    except KeyError:
      return Response(status=status.HTTP_401_UNAUTHORIZED)

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
      errors = {"account_id": "Invalid account ID."}
      return Response(content=errors, headers=headers, status=status.HTTP_404_NOT_FOUND)

    # No content-type to check, because there's no payload

    #################
    # Operation
    #################
      
    try:
      reqs = Requirement.objects.filter(group__project__permission__account=account)
    except Requirement.DoesNotExist:
      reqs = []

    req_list = [req.record_to_dictionary() for req in reqs]

    return Response(content=req_list, headers=headers, status=status.HTTP_200_OK)

  def post(self, request):
    #################
    # Setup
    #################

    headers = {
      "Content-Type": "application/json",
      "Allow": "GET, POST",
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
      errors = {"account_id": "Invalid account ID."}
      return Response(content=errors, headers=headers, status=status.HTTP_404_NOT_FOUND)

    # Check content-type header
    if not self.content_type.startswith('application/json'):
      errors = {"header_content_type": "Content-Type must be 'application/json'. Your Content-Type is " + str(self.content_type)}
      return Response(content=errors, headers=headers, status=status.HTTP_400_BAD_REQUEST)

    #################
    # Operation
    #################
    
    try:
      group_id = int(self.CONTENT["group_id"])
    except KeyError:
      errors = {"group_id": "Missing group ID."}
      return Response(content=errors, headers=headers, status=status.HTTP_404_NOT_FOUND)
    
    try:
      group = RequirementGroup.objects.get(id=group_id)
    except RequirementGroup.DoesNotExist:
      errors = {"group_id": "Invalid group ID."}
      return Response(content=errors, headers=headers, status=status.HTTP_404_NOT_FOUND)

    try:
      permission = Permission.objects.get(account=account, project=group.project)
    except Permission.DoesNotExist:
      errors = {"permission": "Invalid permissions."}
      return Response(content=errors, headers=headers, status=status.HTTP_400_BAD_REQUEST)

    req = Requirement.create_record(permission, group, self.CONTENT)
    if not isinstance(req, Requirement):
      # HTTP status 422: Unprocessable Entity (WebDAV; RFC 4918)
      return Response(content=req, headers=headers, status=422)
    
    return Response(content=req.record_to_dictionary(), headers=headers, status=status.HTTP_200_OK)

class RequirementEditor(View):
  """
  Handles HTTP requests to endpoint URL/api/requirements/:req_id/ with optional querystring
  Allow: GET, PUT, DELETE
  """
  def post(self, request, req_id):
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

  def delete(self, request, req_id):
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
      account_id = int(request.session["_auth_user_id"])
    except KeyError:
      return Response(status=status.HTTP_401_UNAUTHORIZED)

    try:
      account = Account.objects.get(user_id=account_id)
    except Account.DoesNotExist:
      errors = {"account_id": "Invalid account ID."}
      return Response(content=errors, headers=headers, status=status.HTTP_404_NOT_FOUND)

    try:
      req = Requirement.objects.get(id=int(req_id))
    except Requirement.DoesNotExist:
      errors = {"requirement_id": "Invalid requirement ID."}
      return Response(content=errors, headers=headers, status=status.HTTP_404_NOT_FOUND)

    try:
      permission = Permission.objects.get(account=account, project=req.group.project)
    except Permission.DoesNotExist:
      errors = {"permission": "Invalid permissions."}
      return Response(content=errors, headers=headers, status=status.HTTP_400_BAD_REQUEST)

    #################
    # Operation
    #################

    result = req.delete_record(permission)
    if isinstance(result, dict):
      return Response(content=result, headers=headers, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(content={}, headers=headers, status=status.HTTP_200_OK)

  def get(self, request, req_id):
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
      errors = {"account_id": "Invalid account ID."}
      return Response(content=errors, headers=headers, status=status.HTTP_404_NOT_FOUND)

    try:
      req = Requirement.objects.get(id=int(req_id))
    except Requirement.DoesNotExist:
      errors = {"group_id": "Invalid group ID."}
      return Response(content=errors, headers=headers, status=status.HTTP_404_NOT_FOUND)

    try:
      permissions = Permission.objects.get(account=account, project_id=req.group.project)
    except Permission.DoesNotExist:
      errors = {"permission": "Invalid permissions."}
      return Response(content=errors, headers=headers, status=status.HTTP_400_BAD_REQUEST)

    #################
    # Operation
    #################

    return Response(content=req.record_to_dictionary(), headers=headers, status=status.HTTP_200_OK)

  def put(self, request, req_id):
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
      account_id = int(request.session["_auth_user_id"])
    except KeyError:
      return Response(status=status.HTTP_401_UNAUTHORIZED)

    # Check content-type header
    if not self.content_type.startswith('application/json'):
      errors = {"header_content_type": "Content-Type must be 'application/json'. Your Content-Type is " + str(self.content_type)}
      return Response(content=errors, headers=headers, status=status.HTTP_400_BAD_REQUEST)
    
    try:
      account = Account.objects.get(user_id=account_id)
    except Account.DoesNotExist:
      errors = {"account_id": "Invalid account ID."}
      return Response(content=errors, headers=headers, status=status.HTTP_404_NOT_FOUND)

    try:
      req = Requirement.objects.get(id=int(req_id))
    except Requirement.DoesNotExist:
      errors = {"requirement_id": "Invalid requirement ID."}
      return Response(content=errors, headers=headers, status=status.HTTP_404_NOT_FOUND)
      
    try:
      permission = Permission.objects.get(account=account, project=req.group.project)
    except Permission.DoesNotExist:
      errors = {"permission": "Invalid permissions."}
      return Response(content=errors, headers=headers, status=status.HTTP_400_BAD_REQUEST)

    #################
    # Operation
    #################
    
    result = req.update_record(permission, self.CONTENT)
    if isinstance(result, dict):
      # HTTP status 422: Unprocessable Entity (WebDAV; RFC 4918)
      return Response(content=result, headers=headers, status=422)
    
    return Response(content=result.record_to_dictionary(), headers=headers, status=status.HTTP_200_OK)

class PermissionManager(View):
  """
  Handles HTTP requests to endpoint URL/api/comments/ with optional querystring
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

    #################
    # Validation
    #################

    try:
      request.session["_auth_user_id"]
    except KeyError:
      return Response(status=status.HTTP_401_UNAUTHORIZED)

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

    #################
    # Validation
    #################

    try:
      request.session["_auth_user_id"]
    except KeyError:
      return Response(status=status.HTTP_401_UNAUTHORIZED)

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
      errors = {"account_id": "Invalid account ID."}
      return Response(content=errors, headers=headers, status=status.HTTP_404_NOT_FOUND)

    # No content-type to check, because there's no payload

    #################
    # Operation
    #################
      
    try:
      permissions = Permission.objects.filter(project__account=account)
    except Permission.DoesNotExist:
      permissions = []

    permission_list = [permission.record_to_dictionary() for permission in permissions]

    return Response(content=permission_list, headers=headers, status=status.HTTP_200_OK)

  def post(self, request):
    #################
    # Setup
    #################

    headers = {
      "Content-Type": "application/json",
      "Allow": "GET, POST",
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
      errors = {"account_id": "Invalid account ID."}
      return Response(content=errors, headers=headers, status=status.HTTP_404_NOT_FOUND)

    # Check content-type header
    if not self.content_type.startswith('application/json'):
      errors = {"header_content_type": "Content-Type must be 'application/json'. Your Content-Type is " + str(self.content_type)}
      return Response(content=errors, headers=headers, status=status.HTTP_400_BAD_REQUEST)

    #################
    # Operation
    #################
    
    try:
      project_id = int(self.CONTENT["project_id"])
    except KeyError:
      errors = {"project_id": "Missing project ID."}
      return Response(content=errors, headers=headers, status=status.HTTP_404_NOT_FOUND)
    
    # Must be project owner to create a permission
    try:
      project = Project.objects.get(id=project_id, account=account)
    except Project.DoesNotExist:
      errors = {"project_id": "Invalid project ID."}
      return Response(content=errors, headers=headers, status=status.HTTP_404_NOT_FOUND)

    try:
      email = str(self.CONTENT['email']).lower().strip()
    except KeyError:
      errors = {"email": "Missing email address."}
      return Response(content=errors, headers=headers, status=status.HTTP_400_BAD_REQUEST)
    
    try:
      p_account = Account.objects.get(email=email)
    except Account.DoesNotExist:
      p_account = Account.create_invitation_account(email)
      if isinstance(p_account, dict):
        return Response(content=p_account, headers=headers, status=status.HTTP_400_BAD_REQUEST)
    else:
      try:
        Permission.objects.get(project=project, account=p_account)
      except Permission.DoesNotExist:
        pass
      else:
        # Send a 30X response instead for PUT to correct endpoint?
        errors = {"email": "This email address already has a permission."}
        return Response(content=errors, headers=headers, status=status.HTTP_400_BAD_REQUEST)

    try:
      permission = str(self.CONTENT['permission'])
    except KeyError:
      permission = 'client'
    else:
      if permission not in ['client', 'coworker']:
        permission = 'client'
    
    perm = Permission.create_record(account, project, p_account, self.CONTENT)
    if not isinstance(perm, Permission):
      # HTTP status 422: Unprocessable Entity (WebDAV; RFC 4918)
      return Response(content=perm, headers=headers, status=422)
    
    return Response(content=perm.record_to_dictionary(), headers=headers, status=status.HTTP_200_OK)

class PermissionEditor(View):
  """
  Handles HTTP requests to endpoint URL/api/permissions/:permission_id/ with optional querystring
  Allow: GET, DELETE
  """
  def post(self, request, permission_id):
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

    errors = {"header_request_method": "This endpoint only supports GET, PUT, and DELETE requests."}
    return Response(content=errors, headers=headers, status=status.HTTP_405_METHOD_NOT_ALLOWED)

  def delete(self, request, permission_id):
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
      account_id = int(request.session["_auth_user_id"])
    except KeyError:
      return Response(status=status.HTTP_401_UNAUTHORIZED)

    try:
      account = Account.objects.get(user_id=account_id)
    except Account.DoesNotExist:
      errors = {"account_id": "Invalid account ID."}
      return Response(content=errors, headers=headers, status=status.HTTP_404_NOT_FOUND)

    try:
      permission = Permission.objects.get(id=int(permission_id))
    except Permission.DoesNotExist:
      errors = {"permission_id": "Invalid permission ID."}
      return Response(content=errors, headers=headers, status=status.HTTP_404_NOT_FOUND)

    # Only admins can delete permissions
    if permission.project.account.id is not account_id:
      errors = {"permission": "Invalid permissions."}
      return Response(content=errors, headers=headers, status=status.HTTP_400_BAD_REQUEST)

    #################
    # Operation
    #################

    result = permission.delete_record(account)
    if isinstance(result, dict):
      return Response(content=result, headers=headers, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(content={}, headers=headers, status=status.HTTP_200_OK)

  def get(self, request, permission_id):
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
      errors = {"account_id": "Invalid account ID."}
      return Response(content=errors, headers=headers, status=status.HTTP_404_NOT_FOUND)

    try:
      permission = Permission.objects.get(id=int(permission_id))
    except Permission.DoesNotExist:
      errors = {"permission_id": "Invalid permission ID."}
      return Response(content=errors, headers=headers, status=status.HTTP_404_NOT_FOUND)

    if permission.project.account.id is not account_id:
      errors = {"permission": "Invalid permissions."}
      return Response(content=errors, headers=headers, status=status.HTTP_400_BAD_REQUEST)

    #################
    # Operation
    #################

    return Response(content=permission.record_to_dictionary(), headers=headers, status=status.HTTP_200_OK)

  def put(self, request, permission_id):
    #################
    # Setup
    #################

    headers = {
      "Content-Type": "application/json",
      "Allow": "GET, DELETE",
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
      errors = {"account_id": "Invalid account ID."}
      return Response(content=errors, headers=headers, status=status.HTTP_404_NOT_FOUND)

    try:
      permission = Permission.objects.get(id=int(permission_id))
    except Permission.DoesNotExist:
      errors = {"permission_id": "Invalid permission ID."}
      return Response(content=errors, headers=headers, status=status.HTTP_404_NOT_FOUND)

    if permission.project.account.id is not account_id:
      errors = {"permission": "Invalid permissions."}
      return Response(content=errors, headers=headers, status=status.HTTP_400_BAD_REQUEST)
    
    result = permission.update_record(account, self.CONTENT)
    if isinstance(result, dict):
      return Response(content=result, headers=headers, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(content=result, headers=headers, status=status.HTTP_200_OK)












