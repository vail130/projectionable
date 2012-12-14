
define [
  'spine'
  'text!deployment.txt'
], (Spine, Deployment) ->
  
  class Worklog extends Spine.Model
    @configure "Worklog",
      "id"
      "account_id"
      "action"
      "note"
      "asset_id"
      "requirement_id"
      "date_created"
      "date_updated"
      "unix_created"
      "unix_updated"
    
    if Deployment is 'local'
      @extend Spine.Model.Local
    else
      @extend Spine.Model.Ajax
      @extend url: "/api/worklogs"
