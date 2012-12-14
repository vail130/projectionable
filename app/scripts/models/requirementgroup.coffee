
define [
  'spine'
  'text!deployment.txt'
], (Spine, Deployment) ->
  
  class RequirementGroup extends Spine.Model
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
      "unix_created"
      "unix_updated"
    
    if Deployment is 'local'
      @extend Spine.Model.Local
    else
      @extend Spine.Model.Ajax
      @extend url: "/api/groups"
    