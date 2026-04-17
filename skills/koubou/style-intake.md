# Style Intake

Read the app before you ask for art direction. The goal is to ground the screenshot campaign in the product's actual visual language, not in a generic App Store aesthetic.

## Order Of Operations

1. Inspect the app's local artifacts
2. Extract concrete visual and tonal signals
3. Decide what is trustworthy vs missing vs contradictory
4. Ask only the questions needed to resolve uncertainty
5. Lock the style decision before writing copy or HTML

## What To Read

Prioritize these sources in roughly this order:

1. `Assets.xcassets`, app icons, logos, illustration assets
2. Existing app screenshots, simulator exports, marketing captures
3. Product docs: `README*`, `CLAUDE.md`, docs folders, launch plans
4. Existing App Store work: `AppStore/`, `fastlane/screenshots/`, old templates
5. UI code and design tokens:
   - SwiftUI colors, gradients, fonts, materials
   - CSS variables, theme files, design constants
   - reusable card, button, and surface styles
6. Landing pages or web marketing files if present

If several sources disagree, trust the sources closest to the shipped UI first, then current marketing, then old screenshot sets.

## What To Infer

Extract and name the app's signals in plain language:

- Palette: dominant colors, accents, neutrals, warmth/coolness
- Contrast: light, dark, mixed, muted, high-contrast
- Density: airy, balanced, dense
- Surfaces: flat, layered, card-heavy, glossy, matte
- Geometry: sharp, soft, rounded, oversized, minimal
- Visual energy: calm, technical, warm, playful, editorial, energetic
- Copy voice: precise, warm, friendly, premium, technical, punchy
- Brand distinctives: icon shape, illustration language, recurring accent, signature gradient, recurring motif

## What To Ask

Ask questions only when the local evidence cannot answer them safely.

Ask if:

- brand signals are weak or inconsistent
- the app UI is visually plain but the marketing needs a stronger identity
- the product serves multiple audiences and the campaign direction is ambiguous
- the app style works in-product but would be weak as App Store marketing
- the user likely has explicit taste constraints not visible in the repo

Do not ask for colors, fonts, or mood if they are already obvious from the app and marketing files. Instead, summarize what you found and confirm it.

## Conflict Resolution

Sometimes the app's UI style should not be copied literally into the screenshots.

Use this order:

1. Preserve brand truth
2. Adapt for App Store readability and conversion
3. Respect explicit user direction

Examples:

- If the app UI is neutral and utilitarian, the screenshot set can still be more dramatic, but it should retain the app's palette logic and tone.
- If the UI is busy or dense, simplify the campaign rather than reproducing every visual detail.
- If the user asks for a mood that conflicts with the shipped product, keep the product recognizable and say what you are amplifying or softening.

## Heuristics: App Style -> Screenshot Style

1. Minimal, high-contrast UI with restrained color usually wants a premium or editorial campaign, not playful gradients and stickers.
2. Colorful UI with friendly copy and illustration can support more layered, energetic, and expressive screenshot compositions.
3. Dense utility UI should usually become clearer and more selective in the campaign; keep the precision, remove the clutter.
4. If the product relies on trust, privacy, finance, or workflow credibility, lean toward cleaner structure and stronger hierarchy over decorative depth.
5. If the app's strongest brand signal is a specific accent color or shape, reuse that motif across slides so the set feels product-specific.
6. If the UI uses soft radii, cards, and warm accents, the campaign can feel warmer and more tactile without copying every component.
7. If the UI uses dark surfaces and vivid highlights, that does not automatically justify the generic dark-gradient fallback; keep the palette, but vary composition and texture.
8. If the app has weak visual branding but strong product value, anchor the campaign in copy voice and UI crops instead of inventing unrelated visual gimmicks.

## Minimum Output Of Intake

Before designing, you should be able to state:

- `brand signals detected`
- `what should carry over into the campaign`
- `what should be amplified for App Store marketing`
- `what should be avoided`
- `what remains uncertain and must be confirmed with the user`
