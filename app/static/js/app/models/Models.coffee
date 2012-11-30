class Projectionable.Session extends Spine.Model
  @configure "Session",
    "id"
    
  @extend Spine.Model.Ajax
  @extend url: "/api/sessions"

class Projectionable.Account extends Spine.Model
  @configure "Account",
    "id"
    "first_name"
    "last_name"
    "email"
    "type"
    "status"
    "date_created"
    "date_updated"
    
  @extend Spine.Model.Ajax
  @extend url: "/api/accounts"

class Projectionable.Project extends Spine.Model
  @configure "Project",
    "id"
    "account_id"
    "title"
    "rate"
    "deadline"
    "budget"
    "status"
    "front_end_hours"
    "front_end_hours_worked"
    "back_end_hours"
    "back_end_hours_worked"
    "asset_hours"
    "asset_hours_worked"
    "owner"
    "clients"
    "coworkers"
    "logs"
    "date_created"
    "date_updated"
    
  @extend Spine.Model.Ajax
  @extend url: "/api/projects"
  
class Projectionable.Permission extends Spine.Model
  @configure "Permission",
    "id"
    "account_id"
    "email"
    "project_id"
    "permission"
    "date_created"
    "date_updated"
    
  @extend Spine.Model.Ajax
  @extend url: "/api/permissions"
  
class Projectionable.RequirementGroup extends Spine.Model
  @configure "RequirementGroup",
    "id"
    "account_id"
    "project_id"
    "title"
    "index"
    "method"
    "uri"
    "type"
    "hours"
    "hours_worked"
    "date_created"
    "date_updated"
    
  @extend Spine.Model.Ajax
  @extend url: "/api/groups"
  
class Projectionable.Requirement extends Spine.Model
  @configure "Requirement",
    "id"
    "account_id"
    "project_id"
    "group_id"
    "title"
    "description"
    "index"
    "status"
    "requester_id"
    "hours"
    "hours_worked"
    "date_created"
    "date_updated"
    
  @extend Spine.Model.Ajax
  @extend url: "/api/requirements"
  
class Projectionable.ProjectAsset extends Spine.Model
  @configure "ProjectAsset",
    "id"
    "account_id"
    "project_id"
    "title"
    "description"
    "asset"
    "index"
    "status"
    "requester_id"
    "hours"
    "hours_worked"
    "date_created"
    "date_updated"
    
  @extend Spine.Model.Ajax
  @extend url: "/api/assets"
  
class Projectionable.ProjectFile extends Spine.Model
  @configure "ProjectFile",
    "id"
    "account_id"
    "project_id"
    "title"
    "description"
    "asset"
    "index"
    "date_created"
    "date_updated"
    
  @extend Spine.Model.Ajax
  @extend url: "/api/files"
  
  
