from django.db import models
from account_api.models import Account, AccountEmail
from utilities import *
from django.conf import settings
from django.db.models import Sum
import copy, json, datetime, math, time

class Project(models.Model):
  account = models.ForeignKey(Account)
  title = models.CharField(max_length=100)
  deadline = models.DateTimeField(blank=True)
  rate = models.PositiveIntegerField(blank=True)
  budget = models.PositiveIntegerField(blank=True)
  status = models.CharField(max_length=20)
  date_updated = models.DateTimeField(auto_now=True)
  date_created = models.DateTimeField(auto_now_add=True)
  
  statuses = ['open', 'locked']
  
  validation = {
    'title': ('string', (0, 100)),
    'rate': ('integer', (0, None)),
    'budget': ('integer', (0, None)),
    'deadline': 'string',
    'status': lambda x: x in Project.statuses,
  }
  
  @classmethod
  def get_dummy_schema(cls):
    return {
      'title': '',
      "status": '',
      'rate': 0,
      'budget': 0,
      'deadline': '',
    }
  
  @classmethod
  def create_record(cls, account, raw_schema):
    schema = shim_schema(cls, raw_schema)
    
    project_dict = {
      "account": account,
      "title": schema['title'],
      "status": cls.statuses[0]
    }
    
    for field in ['rate', 'deadline', 'budget']:
      if field in schema:
        project_dict[field] = schema[field]
        
    project = cls(**project_dict)
    project.save()
    perm = Permission.create_record(account, project, account, {"permission": "owner"})
    
    return project
  
  def read_record(self, permission):
    req_hours_data = {}
    for field_type in ['front-end', 'back-end']:
      for field in ['hours', 'hours_worked']:
        req_hours_data['_'.join(field_type.split('-')) + '_' + field] = 0
        try:
          result = Requirement.objects.filter(group__project=self, group__type=field_type).aggregate(Sum(field))
        except Requirement.DoesNotExist:
          pass
        else:
          if result[field + "__sum"] is not None:
            req_hours_data['_'.join(field_type.split('-')) + '_' + field] = float(result[field + "__sum"])
    
    asset_hours_data = {}
    for field in ['hours', 'hours_worked']:
      asset_hours_data[field] = 0
      try:
        result = ProjectAsset.objects.filter(project=self).aggregate(Sum(field))
      except ProjectAsset.DoesNotExist:
        pass
      else:
        if result[field + "__sum"] is not None:
          asset_hours_data[field] = float(result[field + "__sum"])
    
    collaborator_data = {}
    for user_type in ['coworker', 'client']:
      collaborator_data[user_type] = []
      try:
        perm = Permission.objects.filter(project=self, permission=user_type)
      except Permission.DoesNotExist:
        pass
      else:
        for p in list(perm):
          collaborator_data[user_type].append({
            "account_id": p.account.id,
            "email": p.account.email
          })
    
    try:
      work_logs = WorkLog.objects.filter(project=self).order_by('-date_created')
    except WorkLog.DoesNotExist:
      work_logs = []
    
    return {
      "id": self.id,
      "account_id": self.account.id,
      "title": self.title,
      "rate": self.rate,
      "budget": self.budget,
      "deadline": self.deadline,
      "status": self.status,
      "front_end_hours": req_hours_data['front_end_hours'],
      "front_end_hours_worked": req_hours_data['front_end_hours_worked'],
      "back_end_hours": req_hours_data['back_end_hours'],
      "back_end_hours_worked": req_hours_data['back_end_hours_worked'],
      "asset_hours": asset_hours_data['hours'],
      "asset_hours_worked": asset_hours_data['hours_worked'],
      "owner": {
        "account_id": permission.account.id,
        "email": permission.account.email,
      },
      "coworkers": collaborator_data['coworker'],
      "clients": collaborator_data['client'],
      "logs": [wl.read_record() for wl in work_logs],
      "date_updated": self.date_updated,
      "date_created": self.date_created,
    }
  
  def update_record(self, permission, raw_schema):
    if permission.permission != 'owner':
      return {"permission": "Invalid permissions."}
    
    schema = filter_valid(self.__class__, raw_schema)
    changed = False
    
    for prop in ['title', 'rate', 'budget', 'deadline']:
      if prop in schema and getattr(self, prop) != schema[prop]:
        setattr(self, prop, schema[prop])
        changed = True
    
    if 'status' in schema and self.status != schema['status'] and schema['status'] in self.__class__.statuses:
      self.status = schema['status']
      changed = True
        
    if changed:
      self.save()
      
    return self
    
  def delete_record(self, permission):
    if permission.permission != 'owner':
      return {"permission": "Invalid permissions."}
    
    try:
      Permission.objects.filter(project=self).delete()
    except Permission.DoesNotExist:
      pass
    
    self.delete()
    return True

class RequirementGroup(models.Model):
  project = models.ForeignKey(Project)
  title = models.CharField(max_length=255)
  uri = models.CharField(max_length=255)
  index = models.PositiveIntegerField()
  type = models.CharField(max_length=20)
  method = models.CharField(max_length=20)
  date_updated = models.DateTimeField(auto_now=True)
  date_created = models.DateTimeField(auto_now_add=True)
  
  types = ['front_end', 'back_end']
  methods = ['get', 'post', 'put', 'delete', 'head', 'options']
  
  validation = {
    'uri': ('string', (0, 200)),
    'title': ('string', (0, 200)),
    'type': lambda x: x in RequirementGroup.types,
    'index': ('integer', (0, None)),
    'method': lambda x: str(x).lower() in RequirementGroup.methods,
  }
  
  @staticmethod
  def get_dummy_schema():
    return {
      "title": '',
      "uri": '',
      "index": 0,
      "type": '',
      "method": '',
    }
  
  @classmethod
  def create_record(cls, permission, project, raw_schema):
    if permission.permission not in ['owner', 'coworker']:
      return {"permission": "Invalid permissions."}
    
    if permission.permission != 'owner' and project.status == 'locked':
      return {"project": "Project is locked."}
    
    schema = shim_schema(cls, raw_schema)
    
    record_dict = {
      "project": project,
      "title": schema['title'],
      "uri": schema['uri'],
      "type": schema['type'],
      "index": schema['index'],
      "method": schema['method'],
    }
    
    record = cls(**record_dict)
    record.save()
    return record
  
  def read_record(self):
    hours_data = {}
    for field in ['hours', 'hours_worked']:
      hours_data[field] = 0
      try:
        result = Requirement.objects.filter(group=self).aggregate(Sum(field))
      except Requirement.DoesNotExist:
        pass
      else:
        if result[field + "__sum"] is not None:
          hours_data[field] = result[field + "__sum"]
    
    return {
      "id": self.id,
      "account_id": self.project.account.id,
      "project_id": self.project.id,
      "index": self.index,
      "title": self.title,
      "method": self.method,
      "uri": self.uri,
      "type": self.type,
      "hours": hours_data['hours'],
      "hours_worked": hours_data['hours_worked'],
      "date_updated": self.date_updated,
      "date_created": self.date_created,
    }
  
  def update_record(self, permission, raw_schema):
    if permission.permission not in ['owner', 'coworker']:
      return {"permission": "Invalid permission."}
    
    if permission.permission != 'owner' and self.project.status == 'locked':
      return {"permission": "Invalid permission."}
    
    schema = filter_valid(self.__class__, raw_schema)
    changed = False
    
    for prop in ['title', 'index', 'method', 'uri']:
      if prop in schema and getattr(self, prop) != schema[prop]:
        setattr(self, prop, schema[prop])
        changed = True
    
    if changed:
      self.save()
      
    return self
  
  def delete_record(self, permission):
    if permission.permission not in ['owner', 'coworker']:
      return {"permission": "Invalid permission."}
    
    if permission.permission != 'owner' and self.project.status == 'locked':
      return {"permission": "Invalid permission."}
    
    self.delete()
    return self

class Requirement(models.Model):
  group = models.ForeignKey(RequirementGroup)
  title = models.CharField(max_length=255)
  description = models.TextField()
  index = models.PositiveIntegerField()
  status = models.CharField(max_length=20)
  hours = models.FloatField(null=True, blank=True)
  hours_worked = models.FloatField()
  requester = models.ForeignKey(Account, blank=True)
  date_updated = models.DateTimeField(auto_now=True)
  date_created = models.DateTimeField(auto_now_add=True)
  
  statuses = ['pending', 'working', 'completed', 'approved', 'rejected']
  
  validation = {
    'title': ('string', (0, 255)),
    'description': 'string',
    'index': ('integer', (0, None)),
    'status': lambda x: x in Requirement.statuses,
    'hours': ('float', (0, None)),
    'hours_worked': ('float', (0, None)),
  }
  
  @staticmethod
  def get_dummy_schema():
    return {
      "title": '',
      "description": '',
      "index": 0,
      "status": '',
      "hours": None,
      "hours_worked": 0,
    }
  
  @classmethod
  def create_record(cls, permission, group, raw_schema):
    if permission.permission not in ['owner', 'coworker']:
      return {"permission": "Invalid permission."}
    
    if permission.permission != 'owner' and group.project.status == 'locked':
      return {"project": "Project is locked."}
    
    schema = shim_schema(cls, raw_schema)
    
    requester = None
    if 'requester_id' in raw_schema:
      try:
        perm = Permission.objects.get(account_id=int(raw_schema['requester_id']), project=group.project)
      except Permission.DoesNotExist:
        pass
      else:
        requester = perm.account
    
    record = cls(
      group=group,
      title=schema['title'],
      description=schema['description'],
      index=schema['index'],
      status=cls.statuses[0],
      hours=schema['hours'],
      hours_worked=0,
      requester=requester,
    )
    
    record.save()
    return record
    
  def read_record(self):
    if self.requester is None:
      requester_id = None
    else:
      requester_id = self.requester.id
    
    return {
      "id": self.id,
      "account_id": self.group.project.account.id,
      "project_id": self.group.project.id,
      "group_id": self.group.id,
      "index": self.index,
      "title": self.title,
      "description": self.description,
      "status": self.status,
      "requester_id": requester_id,
      "hours": self.hours,
      "hours_worked": self.hours_worked,
      "date_updated": self.date_updated,
      "date_created": self.date_created,
    }
  
  def update_record(self, permission, raw_schema):
    if permission.permission not in ['owner', 'coworker']:
      return {"permission": "Invalid permission."}
    
    if self.group.project.status == 'locked' and permission.permission != 'owner':
      return {"permission": "Invalid permission."}
    
    schema = filter_valid(self.__class__, raw_schema)
    changed = False
    
    if 'requester_id' in schema and self.requester.id != schema['requester_id']:
      try:
        perm = Permission.objects.get(account_id=int(schema['requester_id']), project=self.group.project)
      except Permission.DoesNotExist:
        pass
      else:
        self.requester = perm.account
        changed = True
    
    # If status is in schema AND different
    if 'status' in schema and self.status != schema['status']:
      status_changed = True
      
      if self.status == 'pending' and schema['status'] == 'working':
        WorkLog.create_record({
          "account": permission.account,
          "requirement": self,
          "action": "start",
        })
        
      elif self.status == 'working' and schema['status'] == 'pending':
        WorkLog.create_record({
          "account": permission.account,
          "requirement": self,
          "action": "stop",
        })
        
        self.hours_worked = self.calculate_hours_worked()
      
      elif self.status == 'working' and schema['status'] == 'completed':
        WorkLog.create_record({
          "account": permission.account,
          "requirement": self,
          "action": "stop",
        })
        
        WorkLog.create_record({
          "account": permission.account,
          "requirement": self,
          "action": "complete",
        })
        
        self.hours_worked = self.calculate_hours_worked()
        
        if self.requester is not None:
          if self.type == 'front-end':
            subject = "Front-End Story Completed"
          else:
            subject = "Back-End Story Completed"
          
          full_name = ''
          if permission.account.first_name != '':
            full_name += permission.account.first_name
            if permission.account.last_name != '':
              full_name += ' ' + permission.account.last_name
          else:
            full_name = permission.account.email
          
          AccountEmail.create_and_send({
            "recipient": self.requester.email,
            "subject": subject,
            "template": "requirement-completed",
            "context": {
              "full_name": full_name,
              "requirement_type": self.type,
              "requirement_title": self.title,
              "hours": self.hours,
              "hours_worked": self.hours_worked,
              "hours_percent": str(round(self.hours_worked / float(self.hours) * 100, 1)) + '%'
            }
          })
        
      elif self.status == 'pending' and schema['status'] == 'completed':
        WorkLog.create_record({
          "account": permission.account,
          "requirement": self,
          "action": "complete",
        })
        
        if self.requester is not None:
          if self.type == 'front-end':
            subject = "Front-End Story Completed"
          else:
            subject = "Back-End Story Completed"
          
          full_name = ''
          if permission.account.first_name != '':
            full_name += permission.account.first_name
            if permission.account.last_name != '':
              full_name += ' ' + permission.account.last_name
          else:
            full_name = permission.account.email
          
          AccountEmail.create_and_send({
            "recipient": self.requester.email,
            "subject": subject,
            "template": "requirement-completed",
            "context": {
              "full_name": full_name,
              "requirement_type": self.type,
              "requirement_title": self.title,
              "hours": self.hours,
              "hours_worked": self.hours_worked,
              "hours_percent": str(round(self.hours_worked / float(self.hours) * 100, 1)) + '%'
            }
          })
        
      elif self.status == 'completed' and schema['status'] == 'approved':
        WorkLog.create_record({
          "account": permission.account,
          "requirement": self,
          "action": "approve",
        })
        
        try:
          log = WorkLog.objects.filter(requirement=self, action='completed').order_by('-date_updated').reverse()[0]
        except WorkLog.DoesNotExist:
          pass
        else:
          if self.type == 'front-end':
            subject = "Front-End Story Approved"
          else:
            subject = "Back-End Story Approved"
          
          full_name = ''
          if permission.account.first_name != '':
            full_name += permission.account.first_name
            if permission.account.last_name != '':
              full_name += ' ' + permission.account.last_name
          else:
            full_name = permission.account.email
          
          AccountEmail.create_and_send({
            "recipient": log.account.email,
            "subject": subject,
            "template": "requirement-approved",
            "context": {
              "full_name": full_name,
              "requirement_type": self.type,
              "requirement_title": self.title,
              "hours": self.hours,
              "hours_worked": self.hours_worked,
              "hours_percent": str(round(self.hours_worked / float(self.hours) * 100, 1)) + '%'
            }
          })
        
      elif self.status == 'completed' and schema['status'] == 'rejected':
        if 'note' in raw_schema:
          log_note = raw_schema['note']
        else:
          log_note = None
        
        WorkLog.create_record({
          "account": permission.account,
          "requirement": self,
          "action": "reject",
          "note": log_note
        })
        
        try:
          log = WorkLog.objects.filter(requirement=self, action='completed').order_by('-date_updated').reverse()[0]
        except WorkLog.DoesNotExist:
          pass
        else:
          if self.type == 'front-end':
            subject = "Front-End Story Rejected"
          else:
            subject = "Back-End Story Rejected"
          
          full_name = ''
          if permission.account.first_name != '':
            full_name += permission.account.first_name
            if permission.account.last_name != '':
              full_name += ' ' + permission.account.last_name
          else:
            full_name = permission.account.email
          
          AccountEmail.create_and_send({
            "recipient": log.account.email,
            "subject": subject,
            "template": "requirement-rejected",
            "context": {
              "full_name": full_name,
              "requirement_type": self.type,
              "requirement_title": self.title,
              "note": log_note,
              "hours": self.hours,
              "hours_worked": self.hours_worked,
              "hours_percent": str(round(self.hours_worked / float(self.hours) * 100, 1)) + '%'
            }
          })
        
      elif self.status in ['approved', 'rejected', 'completed'] and schema['status'] == 'pending':
        if 'note' in raw_schema:
          log_note = raw_schema['note']
        else:
          log_note = None
        
        WorkLog.create_record({
          "account": permission.account,
          "requirement": self,
          "action": "revert",
          "note": log_note
        })
        
        if self.requester is not None and self.requester.id != permission.account.id:
          if self.type == 'front-end':
            subject = "Front-End Story Reverted"
          else:
            subject = "Back-End Story Reverted"
          
          full_name = ''
          if permission.account.first_name != '':
            full_name += permission.account.first_name
            if permission.account.last_name != '':
              full_name += ' ' + permission.account.last_name
          else:
            full_name = permission.account.email
          
          AccountEmail.create_and_send({
            "recipient": self.requester.email,
            "subject": subject,
            "template": "requirement-reverted",
            "context": {
              "full_name": full_name,
              "requirement_type": self.type,
              "requirement_title": self.title,
              "note": log_note,
              "hours": self.hours,
              "hours_worked": self.hours_worked,
              "hours_percent": str(round(self.hours_worked / float(self.hours) * 100, 1)) + '%'
            }
          })
        
      else:
        status_changed = False
      
      if status_changed is True:
        self.status = schema['status']
        changed = True
  
    for prop in ['title', 'description', 'index', 'hours']:
      if prop in schema and getattr(self, prop) != schema[prop]:
        setattr(self, prop, schema[prop])
        changed = True
    
    if changed:
      self.save()
    
    return self
  
  def calculate_hours_worked(self):
    hours_worked = 0
    try:
      logs = list(WorkLog.objects.filter(requirement=self, action__in=['start', 'stop']).order_by('-date_created'))
    except WorkLog.DoesNotExist:
      return hours_worked
    else:
      num_logs = len(logs)
      for i in range(num_logs):
        if logs[i].action == 'start' and i < num_logs - 1 and logs[i+1].action == 'stop':
          hours_worked += (logs[i+1].date_created - logs[i].date_created).seconds / 3600.0
      return hours_worked
  
  def delete_record(self, permission):
    if permission.permission not in ['owner', 'coworker']:
      return {"permission": "Invalid permission."}
    
    if permission.permission != 'owner' and self.group.project.status == 'locked':
      return {"permission": "Invalid permission."}
    
    if self.hours_worked > 0:
      self.status = 'deleted'
      self.save()
    else:
      self.delete()
    
    return True

class ProjectAsset(models.Model):
  project = models.ForeignKey(RequirementGroup)
  title = models.CharField(max_length=255)
  description = models.TextField()
  index = models.PositiveIntegerField()
  status = models.CharField(max_length=20)
  asset = models.FileField(upload_to='/', blank=True)
  hours = models.FloatField(null=True, blank=True)
  hours_worked = models.FloatField()
  requester = models.ForeignKey(Account, blank=True)
  date_updated = models.DateTimeField(auto_now=True)
  date_created = models.DateTimeField(auto_now_add=True)
  
  statuses = ['pending', 'working', 'completed', 'approved', 'rejected']
  
  validation = {
    'title': ('string', (0, 255)),
    'description': 'string',
    'index': ('integer', (0, None)),
    'status': lambda x: x in ProjectAsset.statuses,
    'hours': ('float', (0, None)),
    'hours_worked': ('float', (0, None)),
  }
  
  @staticmethod
  def get_dummy_schema():
    return {
      "title": '',
      "description": '',
      "index": 0,
      "status": '',
      "hours": None,
      "hours_worked": 0,
    }
  
  @classmethod
  def create_record(cls, permission, project, raw_schema):
    if permission.permission not in ['owner', 'coworker']:
      return {"permission": "Invalid permission."}
    
    if permission.permission != 'owner' and project.status == 'locked':
      return {"project": "Project is locked."}
    
    schema = shim_schema(cls, raw_schema)
    
    requester = None
    if 'requester_id' in raw_schema:
      try:
        perm = Permission.objects.get(account_id=int(raw_schema['requester_id']), project=project)
      except Permission.DoesNotExist:
        pass
      else:
        requester = perm.account
    
    record = cls(
      project=project,
      title=schema['title'],
      description=schema['description'],
      index=schema['index'],
      status=cls.statuses[0],
      hours=schema['hours'],
      hours_worked=0,
      requester=requester,
    )
    
    record.save()
    return record
    
  def read_record(self):
    if self.requester is None:
      requester_id = None
    else:
      requester_id = self.requester.id
    
    return {
      "id": self.id,
      "account_id": self.project.account.id,
      "project_id": self.project.id,
      "index": self.index,
      "title": self.title,
      "description": self.description,
      "asset": self.asset.url,
      "status": self.status,
      "requester_id": requester_id,
      "hours": self.hours,
      "hours_worked": self.hours_worked,
      "date_updated": self.date_updated,
      "date_created": self.date_created,
    }
  
  def update_record(self, permission, raw_schema):
    if permission.permission not in ['owner', 'coworker']:
      return {"permission": "Invalid permission."}
    
    if self.project.status == 'locked' and permission.permission != 'owner':
      return {"permission": "Invalid permission."}
    
    schema = filter_valid(self.__class__, raw_schema)
    changed = False
    
    if 'requester_id' in schema and self.requester.id != schema['requester_id']:
      try:
        perm = Permission.objects.get(account_id=int(schema['requester_id']), project=self.project)
      except Permission.DoesNotExist:
        pass
      else:
        self.requester = perm.account
        changed = True
    
    # If status is in schema AND different
    if 'status' in schema and self.status != schema['status']:
      status_changed = True
      
      if self.status == 'pending' and schema['status'] == 'working':
        WorkLog.create_record({
          "account": permission.account,
          "asset": self,
          "action": "start",
        })
        
      elif self.status == 'working' and schema['status'] == 'pending':
        WorkLog.create_record({
          "account": permission.account,
          "asset": self,
          "action": "stop",
        })
        
        self.hours_worked = self.calculate_hours_worked()
        
      elif self.status == 'working' and self.asset is not None and schema['status'] == 'completed':
        WorkLog.create_record({
          "account": permission.account,
          "asset": self,
          "action": "stop",
        })
        
        WorkLog.create_record({
          "account": permission.account,
          "asset": self,
          "action": "complete",
        })
        
        self.hours_worked = self.calculate_hours_worked()
        
        if self.requester is not None:
          full_name = ''
          if permission.account.first_name != '':
            full_name += permission.account.first_name
            if permission.account.last_name != '':
              full_name += ' ' + permission.account.last_name
          else:
            full_name = permission.account.email
          
          AccountEmail.create_and_send({
            "recipient": self.requester.email,
            "subject": "Project Asset Completed",
            "template": "requirement-completed",
            "context": {
              "full_name": full_name,
              "requirement_type": "project asset",
              "requirement_title": self.title,
              "hours": self.hours,
              "hours_worked": self.hours_worked,
              "hours_percent": str(round(self.hours_worked / float(self.hours) * 100, 1)) + '%'
            }
          })
        
      elif self.status == 'pending' and self.asset is not None and schema['status'] == 'completed':
        WorkLog.create_record({
          "account": permission.account,
          "asset": self,
          "action": "complete",
        })
        
        if self.requester is not None:
          full_name = ''
          if permission.account.first_name != '':
            full_name += permission.account.first_name
            if permission.account.last_name != '':
              full_name += ' ' + permission.account.last_name
          else:
            full_name = permission.account.email
          
          AccountEmail.create_and_send({
            "recipient": self.requester.email,
            "subject": "Project Asset Completed",
            "template": "requirement-completed",
            "context": {
              "full_name": full_name,
              "requirement_type": "project asset",
              "requirement_title": self.title,
              "hours": self.hours,
              "hours_worked": self.hours_worked,
              "hours_percent": str(round(self.hours_worked / float(self.hours) * 100, 1)) + '%'
            }
          })
        
      elif self.status == 'completed' and schema['status'] == 'approved':
        WorkLog.create_record({
          "account": permission.account,
          "asset": self,
          "action": "approve",
        })
        
        try:
          log = WorkLog.objects.filter(asset=self, action='completed').order_by('-date_updated').reverse()[0]
        except WorkLog.DoesNotExist:
          pass
        else:
          full_name = ''
          if permission.account.first_name != '':
            full_name += permission.account.first_name
            if permission.account.last_name != '':
              full_name += ' ' + permission.account.last_name
          else:
            full_name = permission.account.email
          
          AccountEmail.create_and_send({
            "recipient": log.account.email,
            "subject": "Project Asset Approved",
            "template": "requirement-approved",
            "context": {
              "full_name": full_name,
              "requirement_type": "project asset",
              "requirement_title": self.title,
              "hours": self.hours,
              "hours_worked": self.hours_worked,
              "hours_percent": str(round(self.hours_worked / float(self.hours) * 100, 1)) + '%'
            }
          })
        
      elif self.status == 'completed' and schema['status'] == 'rejected':
        if 'note' in raw_schema:
          log_note = raw_schema['note']
        else:
          log_note = None
        
        WorkLog.create_record({
          "account": permission.account,
          "asset": self,
          "action": "reject",
          "note": log_note
        })
        
        try:
          log = WorkLog.objects.filter(asset=self, action='completed').order_by('-date_updated').reverse()[0]
        except WorkLog.DoesNotExist:
          pass
        else:
          full_name = ''
          if permission.account.first_name != '':
            full_name += permission.account.first_name
            if permission.account.last_name != '':
              full_name += ' ' + permission.account.last_name
          else:
            full_name = permission.account.email
          
          AccountEmail.create_and_send({
            "recipient": log.account.email,
            "subject": "Project Asset Rejected",
            "template": "requirement-rejected",
            "context": {
              "full_name": full_name,
              "requirement_type": "project asset",
              "requirement_title": self.title,
              "note": log_note,
              "hours": self.hours,
              "hours_worked": self.hours_worked,
              "hours_percent": str(round(self.hours_worked / float(self.hours) * 100, 1)) + '%'
            }
          })
        
      elif self.status in ['approved', 'rejected', 'completed'] and schema['status'] == 'pending':
        if 'note' in raw_schema:
          log_note = raw_schema['note']
        else:
          log_note = None
        
        WorkLog.create_record({
          "account": permission.account,
          "asset": self,
          "action": "revert",
          "note": log_note
        })
        
        if self.requester is not None and self.requester.id != permission.account.id:
          full_name = ''
          if permission.account.first_name != '':
            full_name += permission.account.first_name
            if permission.account.last_name != '':
              full_name += ' ' + permission.account.last_name
          else:
            full_name = permission.account.email
          
          AccountEmail.create_and_send({
            "recipient": self.requester.email,
            "subject": "Project Asset Reverted",
            "template": "requirement-reverted",
            "context": {
              "full_name": full_name,
              "requirement_type": "project asset",
              "requirement_title": self.title,
              "note": log_note,
              "hours": self.hours,
              "hours_worked": self.hours_worked,
              "hours_percent": str(round(self.hours_worked / float(self.hours) * 100, 1)) + '%'
            }
          })
        
      else:
        status_changed = False
      
      if status_changed is True:
        self.status = schema['status']
        changed = True
  
    for prop in ['title', 'index', 'hours', 'description']:
      if prop in schema and getattr(self, prop) != schema[prop]:
        setattr(self, prop, schema[prop])
        changed = True
    
    if changed:
      self.save()
    
    return self
  
  def calculate_hours_worked(self):
    hours_worked = 0
    try:
      logs = list(WorkLog.objects.filter(asset=self, action__in=['start', 'stop']).order_by('-date_created'))
    except WorkLog.DoesNotExist:
      return hours_worked
    else:
      num_logs = len(logs)
      for i in range(num_logs):
        if logs[i].action == 'start' and i < num_logs - 1 and logs[i+1].action == 'stop':
          hours_worked += (logs[i+1].date_created - logs[i].date_created).seconds / 3600.0
      return hours_worked
  
  def delete_record(self, permission):
    if permission.permission not in ['owner', 'coworker']:
      return {"permission": "Invalid permission."}
    
    if permission.permission != 'owner' and self.project.status == 'locked':
      return {"permission": "Invalid permission."}
    
    if self.hours_worked > 0:
      self.status = 'deleted'
      self.save()
    else:
      self.delete()
    
    return True
  
  def update_asset(self, asset):
    if permission.permission not in ['owner', 'coworker']:
      return {"permission": "Invalid permission."}
    
    if self.project.status == 'locked' and permission.permission != 'owner':
      return {"permission": "Invalid permission."}
    
    if self.status in ['pending', 'working']:
      self.asset = asset
      self.save()
    
    return self

class ProjectFile(models.Model):
  project = models.ForeignKey(RequirementGroup)
  title = models.CharField(max_length=255)
  description = models.TextField()
  index = models.PositiveIntegerField()
  asset = models.FileField(upload_to='/', blank=True)
  date_updated = models.DateTimeField(auto_now=True)
  date_created = models.DateTimeField(auto_now_add=True)
  
  validation = {
    'title': ('string', (0, 255)),
    'description': 'string',
    'index': ('integer', (0, None)),
  }
  
  @staticmethod
  def get_dummy_schema():
    return {
      "title": '',
      "description": '',
      "index": 0,
    }
  
  @classmethod
  def create_record(cls, permission, project, raw_schema):
    if permission.permission not in ['owner', 'coworker']:
      return {"permission": "Invalid permission."}
    
    if permission.permission != 'owner' and project.status == 'locked':
      return {"project": "Project is locked."}
    
    schema = shim_schema(cls, raw_schema)
    
    record = cls(
      project=project,
      title=schema['title'],
      description=schema['description'],
      index=schema['index'],
    )
    
    record.save()
    return record
    
  def read_record(self):
    return {
      "id": self.id,
      "account_id": self.project.account.id,
      "project_id": self.project.id,
      "index": self.index,
      "title": self.title,
      "description": self.description,
      "asset": self.asset.url,
      "date_updated": self.date_updated,
      "date_created": self.date_created,
    }
  
  def update_record(self, permission, raw_schema):
    if permission.permission not in ['owner', 'coworker']:
      return {"permission": "Invalid permission."}
    
    if self.project.status == 'locked' and permission.permission != 'owner':
      return {"permission": "Invalid permission."}
    
    schema = filter_valid(self.__class__, raw_schema)
    changed = False
    
    for prop in ['title', 'index', 'description']:
      if prop in schema and getattr(self, prop) != schema[prop]:
        setattr(self, prop, schema[prop])
        changed = True
    
    if changed:
      self.save()
    
    return self
  
  def delete_record(self, permission):
    if permission.permission not in ['owner', 'coworker']:
      return {"permission": "Invalid permission."}
    
    if permission.permission != 'owner' and self.project.status == 'locked':
      return {"permission": "Invalid permission."}
    
    self.delete()
    return True
  
  def update_asset(self, asset):
    if permission.permission not in ['owner', 'coworker']:
      return {"permission": "Invalid permission."}
    
    if self.project.status == 'locked' and permission.permission != 'owner':
      return {"permission": "Invalid permission."}
    
    self.asset = asset
    self.save
    return self

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
  
  def read_record(self):
    return {
      "id" : self.id,
      "account_id": self.account.user_id,
      "email": self.account.email,
      "project_id": self.project.id,
      "permission": self.permission,
      "date_updated": self.date_updated,
      "date_created": self.date_created,
    }

  def delete_record(self, account):
    # Owner cannot remove self from account permissions, unless project is deleted
    if self.project.account.id is self.account.id:
      return {"permission": "Invalid permissions."}
    
    self.delete()
    return True

class WorkLog(models.Model):
  account = models.ForeignKey(Account)
  asset = models.ForeignKey(ProjectAsset, blank=True)
  requirement = models.ForeignKey(Requirement, blank=True)
  action = models.CharField(max_length=20)
  note = models.TextField(blank=True)
  date_created = models.DateTimeField(auto_now_add=True)
  
  actions = ['start', 'stop', 'complete', 'approve', 'reject', 'revert']
  
  @classmethod
  def create_record(cls, schema):
    log_dict = {
      "account": schema['account'],
      "action": schema['action']
    }
    
    for prop in ['requirement', 'asset', 'note']:
      if prop in schema:
        log_dict[prop] = schema[prop]
    
    record = cls(**log_dict)
    record.save()
    return record
  
  def read_record(self):
    record_dict = {
      "account_id": self.account.id,
      "action": self.action,
      "note": self.note,
      "date_created": self.date_created,
    }
    
    if self.asset is not None:
      record_dict['asset_id'] = self.asset.id
    
    if self.requirement is not None:
      record_dict['requirement_id'] = self.requirement.id
    
    return record_dict

