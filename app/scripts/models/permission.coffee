
define [
  'spine'
  'text!deployment.txt'
], (Spine, Deployment) ->
  
  class Permission extends Spine.Model
    @configure "Permission",
      "id"
      "account_id"
      "email"
      "project_id"
      "permission"
      "date_created"
      "date_updated"
      "unix_created"
      "unix_updated"
    
    if Deployment is 'local'
      @extend Spine.Model.Local
    else
      @extend Spine.Model.Ajax
      @extend url: "#{Host}/api/permissions"
