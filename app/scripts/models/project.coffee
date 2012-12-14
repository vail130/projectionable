
define [
  'spine'
  'text!deployment.txt'
], (Spine, Deployment) ->
  
  class Project extends Spine.Model
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
      "date_created"
      "date_updated"
      "unix_created"
      "unix_updated"
    
    if Deployment is 'local'
      @extend Spine.Model.Local
    else
      @extend Spine.Model.Ajax
      @extend url: "/api/projects"
    
