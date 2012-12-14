
define [
  'spine'
  'text!deployment.txt'
], (Spine, Deployment) ->
  
  class Requirement extends Spine.Model
    @configure "Requirement",
      "id"
      "account_id"
      "project_id"
      "group_id"
      "title"
      "index"
      "status"
      "requester_id"
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
      @extend url: "/api/requirements"
    