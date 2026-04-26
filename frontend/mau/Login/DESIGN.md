---
name: Security Profile 360
colors:
  surface: '#13140f'
  surface-dim: '#13140f'
  surface-bright: '#393934'
  surface-container-lowest: '#0e0e0a'
  surface-container-low: '#1c1c17'
  surface-container: '#20201b'
  surface-container-high: '#2a2a25'
  surface-container-highest: '#353530'
  on-surface: '#e5e2db'
  on-surface-variant: '#c8c7b8'
  inverse-surface: '#e5e2db'
  inverse-on-surface: '#31312c'
  outline: '#919283'
  outline-variant: '#47483c'
  surface-tint: '#c3cc8c'
  primary: '#c3cc8c'
  on-primary: '#2d3404'
  primary-container: '#4b5320'
  on-primary-container: '#bdc787'
  inverse-primary: '#5a632e'
  secondary: '#fff9ef'
  on-secondary: '#3a3000'
  secondary-container: '#ffdb3c'
  on-secondary-container: '#725f00'
  tertiary: '#c6c6c7'
  on-tertiary: '#2f3131'
  tertiary-container: '#4d4f4f'
  on-tertiary-container: '#c0c1c1'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#dfe8a6'
  primary-fixed-dim: '#c3cc8c'
  on-primary-fixed: '#191e00'
  on-primary-fixed-variant: '#434b18'
  secondary-fixed: '#ffe16d'
  secondary-fixed-dim: '#e9c400'
  on-secondary-fixed: '#221b00'
  on-secondary-fixed-variant: '#544600'
  tertiary-fixed: '#e2e2e2'
  tertiary-fixed-dim: '#c6c6c7'
  on-tertiary-fixed: '#1a1c1c'
  on-tertiary-fixed-variant: '#454747'
  background: '#13140f'
  on-background: '#e5e2db'
  surface-variant: '#353530'
typography:
  h1:
    fontFamily: Inter
    fontSize: 40px
    fontWeight: '700'
    lineHeight: '1.2'
    letterSpacing: -0.02em
  h2:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '600'
    lineHeight: '1.3'
    letterSpacing: -0.01em
  h3:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: '1.4'
    letterSpacing: '0'
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: '1.6'
    letterSpacing: '0'
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.6'
    letterSpacing: '0'
  label-caps:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '700'
    lineHeight: '1.2'
    letterSpacing: 0.1em
  code:
    fontFamily: monospace
    fontSize: 14px
    fontWeight: '500'
    lineHeight: '1.4'
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  unit: 8px
  container-padding: 32px
  gutter: 24px
  card-gap: 20px
  section-margin: 48px
---

## Brand & Style
The design system is engineered to project a sense of absolute authority, high-tech vigilance, and modern transparency. It serves a specialized audience of law enforcement and security professionals who require rapid data synthesis in high-stakes environments.

The visual style is **Modern Glassmorphism**. This aesthetic choice moves away from traditional, heavy-handed government interfaces toward a "command center" feel. By utilizing semi-transparent layers and deep blurs, the system creates a spatial hierarchy that feels organized yet interconnected. The atmosphere is nocturnal, serious, and precise, evoking the feeling of a sophisticated digital lens focused on public safety.

## Colors
The palette is rooted in a traditional olive green, modernized through saturation and application.

- **Primary Olive (#4B5320):** Used for critical structural elements like headers and primary action buttons. In glass containers, this color is used at lower opacities to tint the background blur.
- **Accent Gold (#FFD700):** Reserved for high-priority alerts, active states, and critical highlights. It acts as a visual "ping" against the dark background.
- **Pure White (#FFFFFF):** Utilized for primary typography and iconography to ensure maximum legibility and a crisp, clinical feel.
- **Background Deep Charcoal/Olive (#1A1C14):** A near-black base with a slight olive undertone that provides the necessary contrast for the glass effects to appear luminous.

## Typography
The system utilizes **Inter** for all interface text. This choice ensures institutional clarity and technical precision.

Headlines are tight and bold to command attention. Body text maintains a generous line height to ensure readability of reports and profiles. A specific "Label-Caps" style is used for metadata and secondary headers to create a distinct visual hierarchy within glass cards. For technical data or ID numbers, a monospaced font is used to prevent character confusion.

## Layout & Spacing
The layout follows a **fluid grid** model to maximize the real estate of large monitoring screens.

- **Grid:** A 12-column system with 24px gutters allows for flexible arrangement of data widgets and profile details.
- **Rhythm:** An 8px linear scale governs all padding and margins. 
- **Density:** High-density data views are encouraged, but glass elements must maintain at least 20px of separation (card-gap) to prevent the blurred backgrounds from overlapping in a muddy fashion.

## Elevation & Depth
Depth is created through light and refraction rather than traditional shadows.

1.  **Backdrop Blur:** All primary containers must use `backdrop-filter: blur(16px)`.
2.  **Translucency:** Card backgrounds should use an RGBA value of the Primary Olive or Charcoal at 15-25% opacity.
3.  **Borders:** A consistent 1px solid border at 20% white opacity (`rgba(255, 255, 255, 0.2)`) defines the edges of all glass components, simulating the "rim light" of a physical glass pane.
4.  **Shadows:** Shadows are "Global Ambient," meaning they are very large, very soft, and low opacity (#000000 at 30%), used only to separate the main glass panels from the base background.

## Shapes
The shape language is modern and approachable, utilizing **heavily rounded corners** to offset the serious nature of the content.

- **Standard Elements:** 16px radius for buttons, input fields, and small widgets.
- **Glass Cards:** 24px radius for primary dashboard cards and profile containers.
- **Indicators:** Status pills and circular avatars use a fully "rounded-full" or pill-shape to contrast against the architectural geometry of the grid.

## Components
- **Glass Cards:** The foundational unit. Features the 24px radius, 1px white border, and 16px blur. Content within cards should have consistent 24px internal padding.
- **Buttons:** 
  - *Primary:* Solid Olive Green with white text; no transparency.
  - *Secondary:* Glass style with a Gold border and Gold text.
  - *Tertiary:* Ghost style with Gold text and an underline on hover.
- **Status Indicators:** Vibrant, glowing dots or pills (using `box-shadow: 0 0 8px [color]`) to indicate "Active," "Warning," or "Secure" states.
- **Input Fields:** Semi-transparent dark backgrounds with 16px corners. The border glows Gold on focus.
- **Data Visualization:** Charts should use semi-transparent fills for areas and high-contrast Gold or White for lines and data points to ensure visibility against the blurred background.
- **Profile Header:** A specialized component that uses a larger blur radius (32px) and a subtle gradient overlay to anchor the primary subject's information at the top of the screen.