define [
  'jquery'
  'underscore'
  'spine'
  'text!views/projects/editor/collaborate-modal-permission.html'
  'models/permission'
], ($, _, Spine, collaborateModalPermissionTemplate, Permission) ->
  
  class CollaboratePermissionModal extends Spine.Controller
    constructor: ->
      super
    
    className: 'permission'
    
    getContext: =>
      permission: @permission
    
    render: =>
      @html _.template collaborateModalPermissionTemplate, @getContext()
      @
    
    events:
      'click .remove-link' : 'deletePermission'
    
    deletePermission: (event) =>
      event.preventDefault()
      @permission.destroy()
