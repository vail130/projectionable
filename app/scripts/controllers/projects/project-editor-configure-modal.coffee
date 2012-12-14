define [
  'jquery'
  'underscore'
  'spine'
  'text!views/projects/editor/configure-modal.html'
], ($, _, Spine, configureModalTemplate) ->

  class ConfigureModal extends Spine.Controller
    constructor: ->
      super
    
    elements:
      '.project-title-input' : '$projectTitleInput'
      '.project-rate-input' : '$projectRateInput'
      '.project-budget-input' : '$projectBudgetInput'
      '.project-deadline-input' : '$projectDeadlineInput'
    
    initDeadlineDatepicker: =>
      if @parent.project.deadline not in [undefined, '']
        @$projectDeadlineInput.val(
          moment(@parent.project.deadline.split('.')[0], 'YYYY-MM-DD HH:mm:ss').format('MM/DD/YYYY')
        )
      
      @$projectDeadlineInput.datepicker
        showButtonPanel: true
      
      @
    
    getContext: =>
      project: @parent.project
    
    render: =>
      @html _.template configureModalTemplate, @getContext()
      @initDeadlineDatepicker()
    
    events:
      'click configure-save-button' : 'saveConfiguration'
    
    saveConfiguration: (event) =>
      event.preventDefault()
      
      rate = parseFloat @$projectRateInput.val()
      budget = parseFloat @$projectBudgetInput.val()
      try
        deadline = moment(@$projectDeadlineInput.val()).unix()
      catch error
        deadline = null
      
      @parent.project.updateAttributes
        title: @$projectTitleInput.val()
        rate: (if isNaN rate then null else rate)
        budget: (if isNaN budget then null else budget)
        deadline: deadline
