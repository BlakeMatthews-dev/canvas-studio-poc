Feature: Book Personalization
  As a buyer
  I want my photo used to replace the placeholder main character
  So that I appear in the story

  Background:
    Given book key "book-001"
    And a page template for page 1
    And the template has a personalizable character layer

  Scenario: Personalize with reference photos uses img2img
    When I personalize the template with customer_id "cust-001" and 3 reference photos
    Then 1 layer was swapped
    And the personalizable layer has a new image_url
    And the old image_url is in the layer history

  Scenario: Personalize without photos uses txt2img
    When I personalize the template with customer_id "cust-002" and 0 reference photos
    Then 1 layer was swapped
    And generation did not use reference photos

  Scenario: Non-personalizable layers are untouched
    Given the template also has a background layer with image_url "data:image/png;base64,BG"
    When I personalize the template with customer_id "cust-003" and 2 reference photos
    Then the background layer image_url is still "data:image/png;base64,BG"

  Scenario: Template with no personalizable layers returns swapped=0
    Given a template with no personalizable layers
    When I personalize the template with customer_id "cust-004" and 0 reference photos
    Then 0 layers were swapped
