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
    "status"
    "hours"
    "hours_worked"
    "client_enabled"
    "permission"
    "date_created"
    "date_updated"
    
  @extend Spine.Model.Ajax
  @extend url: "/api/projects"
  
class Projectionable.Permission extends Spine.Model
  @configure "Permission",
    "id"
    "email"
    "account_id"
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
    "status"
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
    "index"
    "status"
    "hours"
    "hours_worked"
    "date_created"
    "date_updated"
    
  @extend Spine.Model.Ajax
  @extend url: "/api/requirements"
  
  
