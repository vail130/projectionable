
define [
  'spine'
  'text!deployment.txt'
], (Spine, Deployment) ->
  
  class ProjectFile extends Spine.Model
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
      "unix_created"
      "unix_updated"
    
    if Deployment is 'local'
      @extend Spine.Model.Local
    else
      @extend Spine.Model.Ajax
      @extend url: "#{Host}/api/files"
    
