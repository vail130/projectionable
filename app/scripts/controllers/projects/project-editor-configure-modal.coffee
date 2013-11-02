define [
  'jquery'
  'underscore'
  'spine'
  'text!views/projects/editor/configure-modal.html'
], ($, _, Spine, configureModalTemplate) ->

  class ConfigureModal extends Spine.Controller
    constructor: ->
      super
      @$ConfigureModal.on 'hidden', @render
      
    elements:
      '#configure-modal' : '$ConfigureModal'
      '.project-title-input' : '$projectTitleInput'
      '.project-rate-input' : '$projectRateInput'
      '.project-budget-input' : '$projectBudgetInput'
      '.project-start-input' : '$projectStartInput'
      '.project-deadline-input' : '$projectDeadlineInput'
      '.configure-save-button' : '$configureSaveButton'
    
    initDatepickers: =>
      if @parent.project.deadline not in [undefined, '']
        @$projectDeadlineInput.val(
          moment(@parent.project.deadline.split('.')[0], 'YYYY-MM-DD HH:mm:ss').format('MM/DD/YYYY')
        )
      
      @$projectDeadlineInput.datepicker
        showButtonPanel: true
      
      if @parent.project.start not in [undefined, '']
        @$projectStartInput.val(
          moment(@parent.project.start.split('.')[0], 'YYYY-MM-DD HH:mm:ss').format('MM/DD/YYYY')
        )
      
      @$projectStartInput.datepicker
        showButtonPanel: true
      
      @
    
    getContext: =>
      project: @parent.project
    
    render: =>
      @html _.template configureModalTemplate, @getContext()
      @initDatepickers()
    
    events:
      'click .configure-save-button' : 'saveConfiguration'
    
    saveConfiguration: (event) =>
      event.preventDefault()
      return if @$configureSaveButton.hasClass 'disabled'
      @$configureSaveButton.addClass 'disabled'
      
      rate = parseInt @$projectRateInput.val()
      budget = parseInt @$projectBudgetInput.val()
      
      console.log budget, rate
      
      @parent.project.updateAttributes
        title: @$projectTitleInput.val()
        rate: (if isNaN rate then null else rate)
        budget: (if isNaN budget then null else budget)
        deadline: @$projectDeadlineInput.val()
        start: @$projectStartInput.val()
