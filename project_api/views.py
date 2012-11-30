from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from project_api.models import Project, RequirementGroup, Requirement, Permission, ProjectAsset, ProjectFile
from account_api.models import Account
from django.conf import settings


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
    
    return Response(data=project.read_record(permission=permission), status=status.HTTP_200_OK)


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
      
    try:
      permissions = Permission.objects.filter(project__account=account)
    except Permission.DoesNotExist:
      permissions = []

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
    
    return Response(data=perm.read_record(), status=status.HTTP_200_OK)


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
    
    return Response(data=group.read_record(), status=status.HTTP_200_OK)


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
    
    return Response(data=req.read_record(), status=status.HTTP_200_OK)


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
    
    return Response(data=asset.read_record(), status=status.HTTP_200_OK)

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
    
    return Response(data=project_file.read_record(), status=status.HTTP_200_OK)

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












