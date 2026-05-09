Feature: Asset Registry
  As a book creator
  I want to register visual assets with reference material
  So that I can generate consistent characters, settings, and props across all pages

  Background:
    Given book key "book-001"

  Scenario: Create a new character asset
    When I create asset "hero" of kind "character" with name "The Hero"
    Then the asset exists with ip_adapter_weight 0.8
    And the asset has no sheet_image

  Scenario: Upserting an asset with the same key updates it
    Given asset "hero" exists for book "book-001"
    When I upsert asset "hero" with name "Updated Hero"
    Then the asset name is "Updated Hero"

  Scenario: Generate a reference sheet using reference photos
    Given asset "hero" of kind "character" with 3 reference photos
    When I generate a sheet for asset "hero"
    Then the generation used img2img
    And the asset has a sheet_image

  Scenario: Generate a reference sheet from description only
    Given asset "library" of kind "setting" with prompt "Victorian library"
    And asset "library" has no reference photos
    When I generate a sheet for asset "library"
    Then the generation used txt2img
    And the asset has a sheet_image

  Scenario: Setting assets are not background-removed
    Given asset "library" of kind "setting" with prompt "warm library"
    And asset "library" has no reference photos
    When I generate a sheet for asset "library"
    Then background removal was not applied

  Scenario: Character assets have background removed
    Given asset "hero" of kind "character" with 1 reference photos
    When I generate a sheet for asset "hero"
    Then background removal was applied

  Scenario: Update asset with LoRA name
    Given asset "hero" exists for book "book-001"
    When I update asset "hero" lora_name to "hero_style.safetensors"
    Then the asset lora_name is "hero_style.safetensors"

  Scenario: Delete an asset
    Given asset "hero" exists for book "book-001"
    When I delete asset "hero"
    Then asset "hero" does not exist

  Scenario: List assets for a book returns all assets
    Given assets "hero", "sidekick", "library" exist for book "book-001"
    When I list assets for book "book-001"
    Then I receive 3 assets
