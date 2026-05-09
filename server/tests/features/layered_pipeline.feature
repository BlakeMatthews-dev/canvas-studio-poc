Feature: Layered Page Generation
  As a book creator
  I want to build pages as a stack of independently-generated layers
  So that I can regenerate individual elements without rebuilding the whole page

  Background:
    Given book key "book-001"
    And a page template for page 1

  Scenario: Add a background layer to a template
    When I add a background layer with prompt "cozy library"
    Then a layer exists with layer_kind "background"
    And the layer has no image_url

  Scenario: Generate a background layer uses txt2img
    Given a background layer with prompt "cozy library"
    When I trigger generation for the background layer
    Then the layer has an image_url
    And the history is empty

  Scenario: Regenerating a layer pushes old image to history
    Given a background layer with prompt "forest"
    And the layer already has image_url "data:image/png;base64,OLD"
    When I trigger generation for the background layer
    Then the layer history contains "data:image/png;base64,OLD"
    And the layer has a new image_url

  Scenario: Generate a character layer with IP-Adapter refs uses img2img
    Given a character layer referencing asset "hero" with sheet_image
    When I trigger generation for the character layer
    Then the generation backend is "diffusers-img2img"

  Scenario: Generate a character layer without refs uses txt2img
    Given a character layer with prompt "brave hero" and no ip_refs
    When I trigger generation for the character layer
    Then the generation backend is "diffusers-txt2img"

  Scenario: Generate a text layer uses Pillow
    Given a text layer with text "Once upon a time" and font_size 48
    When I trigger generation for the text layer
    Then the generation backend is "pillow"
    And the image is a transparent PNG

  Scenario: LoRAs are forwarded to the generation call
    Given a character layer with lora "hero_lora.safetensors" at weight 0.8
    When I trigger generation for the character layer
    Then the LoRA "hero_lora.safetensors" was forwarded with weight 0.8

  Scenario: ControlNet is forwarded to the generation call
    Given a character layer with openpose controlnet input
    When I trigger generation for the character layer
    Then the controlnet type "openpose" was forwarded

  Scenario: Preview composites all layers
    Given layers at z=0, z=1, z=2 all with image_urls
    When I get the preview
    Then the preview is a PNG data URL

  Scenario: Finalize composites and stores
    Given layers at z=0, z=1, z=2 all with image_urls
    When I finalize page 1
    Then the finalized record has a composite_url

  Scenario: Finalizing with no layer images returns error
    Given a background layer with prompt "empty"
    When I attempt to finalize page 1
    Then finalization fails with 422
