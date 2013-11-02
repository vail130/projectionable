
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
      "start"
      "deadline"
      "budget"
      "status"
      "date_created"
      "date_updated"
      "unix_created"
      "unix_updated"
    
    if Deployment is 'local'
      @extend Spine.Model.Local
    else
      @extend Spine.Model.Ajax
      @extend url: "/api/projects"
    
