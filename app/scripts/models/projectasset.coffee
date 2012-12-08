
define [
  'spine'
  'text!deployment.txt'
], (Spine, Deployment) ->
  
  class ProjectAsset extends Spine.Model
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
      "unix_created"
      "unix_updated"
    
    if Deployment is 'local'
      @extend Spine.Model.Local
    else
      @extend Spine.Model.Ajax
      @extend url: "#{Host}/api/assets"
    