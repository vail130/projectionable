from django.db import models
from account_api.models import Account, AccountEmail
from utilities import *
from django.conf import settings
from django.db.models import Sum
import copy, json, datetime, math, time

class Project(models.Model):
  account = models.ForeignKey(Account)
  title = models.CharField(max_length=100)
  rate = models.PositiveIntegerField()
  status = models.CharField(max_length=20)
  client_enabled = models.BooleanField()
  date_updated = models.DateTimeField(auto_now=True)
  date_created = models.DateTimeField(auto_now_add=True)
  
  statuses = ['pending', 'started', 'locked']
  
  validation = {
    'title': ('string', (0, 100)),
    'rate': ('integer', (0, None)),
    'status': lambda x: x in Project.statuses,
    'client_enabled': 'boolean'
  }
  
  @classmethod
  def create_record(cls, account, raw_schema):
    schema = shim_schema(cls, raw_schema)
    project = cls(
      account=account,
      title=schema['title'],
      rate=schema['rate'],
      client_enabled=False,
      status=cls.statuses[0],
    )
    project.save()
    perm = Permission.create_record(account, project, account, {"permission": "owner"})
    
    return project
  
  @classmethod
  def get_dummy_schema(cls):
    return {
      'title': '',
      "status": '',
      'rate': 0,
      'client_enabled': False,
    }
  
  def record_to_dictionary(self, account=None, children=True):
    try:
      result = Requirement.objects.filter(group__project=self).exclude(status='rejected').aggregate(Sum('hours'))
    except Requirement.DoesNotExist:
      hours = 0
    else:
      hours = result["hours__sum"]
      if hours is None:
        hours = 0
    
    try:
      result = Requirement.objects.filter(group__project=self).exclude(status='rejected').aggregate(Sum('hours_worked'))
    except Requirement.DoesNotExist:
      hours_worked = 0
    else:
      hours_worked = result["hours_worked__sum"]
      if hours_worked is None:
        hours_worked = 0
    
    record_dict = {
      "id": self.id,
      "account": self.account,
      "title": self.title,
      "rate": self.rate,
      "status": self.status,
      "client_enabled": self.client_enabled,
      "hours": hours,
      "hours_worked": hours_worked,
      "date_updated": self.date_updated,
      "date_created": self.date_created,
    }
    
    if children is True:
      try:
        groups = list(RequirementGroup.objects.filter(project=self).order_by('index'))
      except RequirementGroup.DoesNotExist:
        record_dict["groups"] = []
      else:
        record_dict["groups"] = [group.record_to_dictionary() for group in groups]
      
      try:
        reqs = list(Requirement.objects.filter(group__project=self).order_by('index'))
      except Requirement.DoesNotExist:
        record_dict["requirements"] = []
      else:
        record_dict["requirements"] = [req.record_to_dictionary() for req in reqs]
    
    if account is not None:
      try:
        perm = Permission.objects.get(project=self, account=account)
      except Permission.DoesNotExist:
        pass
      else:
        record_dict["permission"] = perm.permission
    
    return record_dict
  
  def update_record(self, permission, raw_schema):
    schema = filter_valid(self.__class__, raw_schema)
    
    changed = False
    project_started = False
    client_enabled = False
    
    if self.status == Project.statuses[0]:
      if permission.permission == 'owner':
        if 'title' in schema:
          self.title = schema['title']
          changed = True
        
        ###
        if 'client_enabled' in schema and self.client_enabled is False and schema['client_enabled'] is True:
          self.client_enabled = True
          changed = True
          client_enabled = True
        ###
        
        if 'rate' in schema:
          self.rate = schema['rate']
          changed = True
        
      elif permission.permission == 'client':
        if 'status' in schema and schema['status'] == Project.statuses[1] and self.is_startable():
          self.status = schema['status']
          changed = True
          project_started = True
          
    elif permission.permission == 'owner' and self.status in Project.statuses[1:3]:
      if 'status' in schema and schema['status'] in Project.statuses[1:3] and self.status != schema['status']:
        self.status = schema['status']
        changed = True
        
    if changed:
      self.save()
      
    if project_started:
      self.approve_pending_children()
      AccountEmail.create_and_send(self.account, 'project-started', project=self)
    
    if client_enabled:
      AccountEmail.create_and_send(self.account, 'client-enabled', project=self)
    
    return self
    
  def is_startable(self):
    # There cannot be any groups or requirements that are requested
    try:
      group_count = RequirementGroup.objects.filter(project=self, status='requested').count()
    except RequirementGroup.DoesNotExist:
      pass
    else:
      if group_count > 0:
        return False
    
    try:
      req_count = Requirement.objects.filter(group__project=self, status='requested').count()
    except Requirement.DoesNotExist:
      pass
    else:
      if req_count > 0:
        return False
    
    return True
  
  def approve_pending_children(self):
    # Starting a project automatically approves all pending groups/requirements
    try:
      RequirementGroup.objects.filter(project=self, status='pending').update(status='approved')
    except RequirementGroup.DoesNotExist:
      pass
    
    try:
      Requirement.objects.filter(group__project=self, status='pending').update(status='approved')
    except Requirement.DoesNotExist:
      pass
    
    return True
  
  def delete_record(self, account):
    try:
      Permission.objects.filter(project=self).delete()
    except Permission.DoesNotExist:
      pass
    
    self.delete()
    return True

class RequirementGroup(models.Model):
  project = models.ForeignKey(Project)
  title = models.CharField(max_length=100)
  index = models.PositiveIntegerField()
  status = models.CharField(max_length=20)
  date_updated = models.DateTimeField(auto_now=True)
  date_created = models.DateTimeField(auto_now_add=True)
  
  statuses = ['pending', 'requested', 'approved', 'rejected']
  
  validation = {
    'title': ('string', (0, 100)),
    'index': ('integer', (0, None)),
    'status': lambda x: x in RequirementGroup.statuses,
  }
  
  @staticmethod
  def get_dummy_schema():
    return {
      "title": '',
      "index": 0,
      "status": '',
      "hours": None,
      "hours_worked": 0,
    }
  
  @classmethod
  def create_record(cls, permission, project, raw_schema):
    schema = shim_schema(cls, raw_schema)
    
    if permission.permission == 'client':
      status = cls.statuses[1]
    elif permission.permission in ['coworker', 'owner']:
      status = cls.statuses[0]
    
    record = cls(
      project=project,
      title=schema['title'],
      index=schema['index'],
      status=status,
    )
    record.save()
    return record
  
  def record_to_dictionary(self, children=True):
    try:
      result = Requirement.objects.filter(group=self).exclude(status='rejected').aggregate(Sum('hours'))
    except Requirement.DoesNotExist:
      hours = 0
    else:
      hours = result["hours__sum"]
      if hours is None:
        hours = 0
    
    try:
      result = Requirement.objects.filter(group=self).exclude(status='rejected').aggregate(Sum('hours_worked'))
    except Requirement.DoesNotExist:
      hours_worked = 0
    else:
      hours_worked = result["hours_worked__sum"]
      if hours_worked is None:
        hours_worked = 0
    
    record_dict = {
      "id": self.id,
      "account": self.project.account,
      "project_id": self.project.id,
      "index": self.index,
      "title": self.title,
      "status": self.status,
      "hours": hours,
      "hours_worked": hours_worked,
      "date_updated": self.date_updated,
      "date_created": self.date_created,
    }
    
    if children is True:
      try:
        reqs = Requirement.objects.filter(group=self).order_by('index')
      except Requirement.DoesNotExist:
        reqs = []
      
      record_dict["requirements"] = [req.record_to_dictionary() for req in reqs]
    
    return record_dict
  
  def update_record(self, permission, raw_schema):
    schema = filter_valid(self.__class__, raw_schema)
    changed = False
    status_changed = False
    
    # If title is in schema AND different
    if 'title' in schema and self.title != schema['title']:
      # If coworker/owner is updating pending OR client is updated requested
      if (self.status == 'pending' and permission.permission in ['coworker', 'owner']) or (self.status == 'requested' and permission.permission == 'client'):
        self.title = schema['title']
        changed = True
    
    # If index is in schema AND different
    if 'index' in schema and self.index != schema['index']:
      self.index = schema['index']
      changed = True
    
    # If status is in schema AND different
    if 'status' in schema and self.status != schema['status']:
      proceed = False
      revert = False
      
      if permission.permission == 'owner' and self.status in ['approved', 'rejected'] and schema['status'] == 'pending':
        proceed = True
        revert = True
      elif permission.permission in ['coworker', 'owner'] and self.status == 'requested' and schema['status'] in ['approved', 'rejected']:
        proceed = True
      elif permission.permission == 'client':
        if self.status == 'pending' and schema['status'] in ['approved', 'rejected']:
          proceed = True
        
        elif self.status == 'approved' and schema['status'] in ['requested', 'rejected']:
          proceed = True
          revert = True
        
        # This condition differs from the corresponding code in Requirement
        elif self.status == 'rejected' and schema['status'] in ['requested', 'approved']:
          proceed = True
          revert = True
      
      if proceed is True:
        self.status = schema['status']
        changed = True
        status_changed = True
        
        project = self.project
        if revert is True and project.status == 'started':
          project.status = 'pending'
          project.save()
    
    if changed:
      self.save()
      
    if status_changed is True and self.status == 'rejected':
      self.reject_children()
    
    return self
  
  def reject_children(self):
    try:
      Requirement.objects.filter(group=self).update(status='rejected')
    except Requirement.DoesNotExist:
      pass
    return True
  
  def delete_record(self, permission):
    if permission.permission == 'client' and self.status == 'requested':
      self.delete()
      return True
      
    elif permission.permission == 'coworker' and self.status == 'pending':
      self.delete()
      return True
    
    elif permission.permission == 'owner':
      self.delete()
      project = self.project
      if project.status == 'approved':
        project.status = 'pending'
        project.save()
      return True
      
    return False
  
class Requirement(models.Model):
  group = models.ForeignKey(RequirementGroup)
  title = models.CharField(max_length=100)
  index = models.PositiveIntegerField()
  status = models.CharField(max_length=20)
  hours = models.FloatField(null=True, blank=True)
  hours_worked = models.FloatField()
  date_updated = models.DateTimeField(auto_now=True)
  date_created = models.DateTimeField(auto_now_add=True)
  
  statuses = ['pending', 'requested', 'approved', 'rejected']
  
  validation = {
    'title': ('string', (0, 100)),
    'index': ('integer', (0, None)),
    'status': lambda x: x in Requirement.statuses,
    'hours': ('float', (0, None)),
    'hours_worked': ('float', (0, None)),
  }
  
  @staticmethod
  def get_dummy_schema():
    return {
      "title": '',
      "index": 0,
      "status": '',
      "hours": None,
      "hours_worked": 0,
    }
  
  @classmethod
  def create_record(cls, permission, group, raw_schema):
    schema = shim_schema(cls, raw_schema)
    
    if permission.permission == 'client':
      status = cls.statuses[1]
      hours = None
    elif permission.permission in ['coworker', 'owner']:
      status = cls.statuses[0]
      hours = schema['hours']
    
    record = cls(
      group=group,
      title=schema['title'],
      index=schema['index'],
      status=status,
      hours=hours,
      hours_worked=0,
    )
    record.save()
    return record
    
  def record_to_dictionary(self, children=True):
    return {
      "id": self.id,
      "account": self.group.project.account,
      "project_id": self.group.project.id,
      "group_id": self.group.id,
      "index": self.index,
      "title": self.title,
      "status": self.status,
      "hours": self.hours,
      "hours_worked": self.hours_worked,
      "date_updated": self.date_updated,
      "date_created": self.date_created,
    }
  
  def update_record(self, permission, raw_schema):
    schema = filter_valid(self.__class__, raw_schema)
    
    if 'hours' in raw_schema and 'hours' not in schema:
      schema['hours'] = None
    
    changed = False
    hours_updated = False
    
    # If index is in schema AND different
    if 'index' in schema and self.index != schema['index']:
      self.index = schema['index']
      changed = True
    
    # If title is in schema AND different
    if 'title' in schema and self.title != schema['title']:
      # If coworker/owner is updating pending OR client is updated requested
      if (self.status == 'pending' and permission.permission in ['coworker', 'owner']) or (self.status == 'requested' and permission.permission == 'client'):
        self.title = schema['title']
        changed = True
    
    # If hours is in schema AND different AND pending/requested AND coworker/owner
    if 'hours' in schema and self.hours != schema['hours'] and self.status in ['pending', 'requested'] and permission.permission in ['coworker', 'owner']:
      self.hours = schema['hours']
      hours_updated = True
      changed = True
    
    # If status is in schema AND different
    if 'status' in schema and self.status != schema['status']:
      proceed = False
      revert = False
      
      if permission.permission == 'owner' and self.status in ['approved', 'rejected'] and schema['status'] == 'pending':
        proceed = True
        revert = True
      elif permission.permission in ['coworker', 'owner'] and self.status == 'requested' and schema['status'] in ['approved', 'rejected']:
        proceed = True
      elif permission.permission == 'client':
        if self.status == 'pending' and schema['status'] in ['approved', 'rejected']:
          proceed = True
        elif self.status == 'approved' and schema['status'] in ['requested', 'rejected']:
          proceed = True
          revert = True
        elif self.status == 'rejected' and ((schema['status'] == 'approved' and self.hours >= 0) or schema['status'] == 'requested'):
          proceed = True
          revert = True
      
      if proceed is True:
        self.status = schema['status']
        changed = True
        
        group = self.group
        if self.status == 'approved' and group.status != 'approved':
          group.status = 'approved'
          group.save()
    
        project = self.group.project
        if revert is True and project.status == 'started':
          project.status = 'pending'
          project.save()
    
    if changed:
      self.save()
    
    return self
  
  def delete_record(self, permission):
    if permission.permission == 'client' and self.status == 'requested':
      self.delete()
      return True
      
    elif permission.permission == 'coworker' and self.status == 'pending':
      self.delete()
      return True
    
    elif permission.permission == 'owner':
      self.delete()
      project = self.group.project
      if project.status == 'started':
        project.status = 'pending'
        project.save()
      return True
      
    return False
  
class Permission(models.Model):
  account = models.ForeignKey(Account)
  project = models.ForeignKey(Project)
  permission = models.CharField(max_length=20)
  date_updated = models.DateTimeField(auto_now=True)
  date_created = models.DateTimeField(auto_now_add=True)
  
  permissions = ['client', 'coworker', 'owner']
  
  validation = {
    'permission': lambda x: x in Permission.permissions,
  }
  
  @classmethod
  def get_dummy_schema(cls):
    return {
      'permission': cls.permissions[0],
    }
  
  @classmethod
  def create_record(cls, account, project, p_account, raw_schema):
    schema = shim_schema(cls, raw_schema)
    record = cls(
      account=p_account,
      project=project,
      permission=schema['permission']
    )
    record.save()
    return record
  
  def update_record(self, account, raw_schema):
    schema = shim_schema(self.__class__, raw_schema)
    
    # Only project owner can change permissions
    if self.project.account.id is not account.id or schema['permission'] not in Permission.permissions[:1]:
      return self
    
    self.permission = schema['permission']
    self.save()
    return self
  
  def record_to_dictionary(self):
    return {
      "id" : self.id,
      "account": self.account.record_to_dictionary(),
      "project_id": self.project.id,
      "permission": self.permission,
      "date_updated": self.date_updated,
      "date_created": self.date_created,
    }

  def delete_record(self, account):
    # Owner cannot remove self from account permissions, unless project is deleted
    if self.project.account.id is self.account.id:
      return self
    
    self.delete()
    return True






