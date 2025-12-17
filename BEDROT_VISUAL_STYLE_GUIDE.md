# BEDROT Visual Style Guide
## Cyberpunk UI Design System

*Last Updated: August 13, 2025*

---

## What We Learned

### Key Discoveries from UI Implementation

1. **Less is More with Contrast**
   - Initial attempt used harsh black (`#0a0a0a`) backgrounds with bright neon green (`#00ff88`) text
   - Users found this too harsh and difficult to look at for extended periods
   - **Solution**: Softer dark grey (`#121212`) background with light grey (`#e0e0e0`) text for main content
   - Neon colors reserved for accents and interactive elements only

2. **Readability Over Aesthetic**
   - Originally used monospace fonts (Consolas) everywhere for "hacker aesthetic"
   - **Better approach**: Clean sans-serif (Segoe UI) for UI, monospace only for logs/code
   - Font size matters: 11px minimum for buttons, 10px for labels, 12px for important text

3. **Button Design Evolution**
   - Started with high-contrast solid neon buttons
   - Users experienced text cutoff with overly stylized buttons
   - **Final solution**: 
     - Semi-transparent backgrounds (80% opacity)
     - Proper min-width constraints (120-180px based on text length)
     - Uppercase text for consistency
     - Padding adjusted to `6px 10px` to prevent cutoff

4. **Table Readability**
   - Pure black/white alternating rows were jarring
   - **Improved approach**: Subtle alternating rows (`#1a1a1a` and `#202020`)
   - Text color `#cccccc` (light grey) instead of neon green for body content
   - Selection highlight using transparent cyan instead of solid magenta

---

## BEDROT Design Principles

### Core Philosophy
**"Cyberpunk without the eye strain"** - Create a futuristic, underground aesthetic that's actually usable for daily work.

### Visual Hierarchy
1. **Background layers** - Use subtle gradients of dark grey, not pure black
2. **Content first** - Text should be readable without strain
3. **Accent strategically** - Neon colors for CTAs and hover states only
4. **Consistent interaction** - All interactive elements should glow/transform on hover

---

## Color Palette

### Primary Colors
```css
/* Backgrounds */
--bg-primary: #121212;        /* Main background */
--bg-secondary: #1a1a1a;      /* Panels, cards */
--bg-tertiary: #202020;       /* Alternate rows */
--bg-hover: #252525;          /* Hover states */
--bg-active: #2a2a2a;         /* Active/selected background */

/* Text */
--text-primary: #e0e0e0;      /* Main content */
--text-secondary: #cccccc;    /* Body text, tables */
--text-muted: #888888;        /* Disabled, hints */

/* Borders */
--border-primary: #404040;    /* Main borders */
--border-subtle: #2a2a2a;     /* Table gridlines */
--border-highlight: #333333;  /* Separators */
```

### Accent Colors (Use Sparingly!)
```css
/* Neon Accents */
--accent-green: #00ff88;      /* Primary actions, success */
--accent-cyan: #00ffff;       /* Highlights, active states */
--accent-magenta: #ff00ff;    /* Special actions */
--accent-pink: #ff00aa;       /* Secondary special actions */
--accent-orange: #ff8800;     /* Warnings, important */
--accent-red: #ff0066;        /* Danger, stop actions */

/* Hover Variants (10% brighter) */
--accent-green-hover: #00ffaa;
--accent-cyan-hover: #66ffff;
--accent-magenta-hover: #ff66ff;
--accent-pink-hover: #ff44cc;
--accent-orange-hover: #ffaa00;
--accent-red-hover: #ff3388;

/* Pressed Variants (20% darker) */
--accent-green-pressed: #00cc66;
--accent-cyan-pressed: #00cccc;
--accent-magenta-pressed: #cc00cc;
--accent-pink-pressed: #cc0088;
--accent-orange-pressed: #cc6600;
--accent-red-pressed: #cc0044;
```

---

## Typography

### Font Stack
```css
/* UI Elements */
font-family: 'Segoe UI', 'Arial', sans-serif;

/* Code/Logs */
font-family: 'Consolas', 'Courier New', monospace;
```

### Font Sizes
- **Headers**: 14-16px, bold, uppercase
- **Buttons**: 11px, bold, uppercase
- **Labels**: 10px, normal
- **Body text**: 12px, normal
- **Status text**: 9px, normal
- **Code/Logs**: 10px, normal

---

## Component Patterns

### Buttons

#### Primary Action (Green)
```python
# PyQt5/6
QPushButton {
    background-color: rgba(0, 255, 136, 0.8);
    color: #000000;
    font-weight: bold;
    padding: 6px 10px;
    border: none;
    border-radius: 4px;
    font-size: 11px;
    text-transform: uppercase;
    min-width: 120px;
}
QPushButton:hover {
    background-color: rgba(0, 255, 136, 0.9);
    box-shadow: 0 0 8px rgba(0, 255, 136, 0.3);
}

# Tkinter
style.configure('Run.TButton',
    background='#00ff88',
    foreground='#000000',
    borderwidth=0,
    font=('Segoe UI', 10, 'bold'))
```

#### Danger Action (Red)
```python
# PyQt5/6
QPushButton {
    background-color: transparent;
    color: #ff0066;
    border: 1px solid #ff0066;
    padding: 6px 10px;
    border-radius: 4px;
    font-weight: bold;
    font-size: 11px;
    text-transform: uppercase;
    min-width: 80px;
}
```

### Tables

```python
QTableWidget {
    background-color: #151515;
    color: #cccccc;
    gridline-color: #2a2a2a;
    selection-background-color: rgba(0, 255, 255, 0.3);
    selection-color: #ffffff;
    border: 1px solid #404040;
    border-radius: 4px;
    font-size: 12px;
    alternate-background-color: #1a1a1a;
}

QTableWidget::item {
    padding: 5px;
    border: none;
    background-color: #1a1a1a;
    color: #cccccc;
}

QTableWidget::item:alternate {
    background-color: #202020;
}
```

### Scrollbars

```python
QScrollBar:vertical {
    background-color: #0a0a0a;
    width: 14px;
    border: 1px solid #1a1a1a;
    border-radius: 7px;
    margin: 2px;
}

QScrollBar::handle:vertical {
    background-color: #00ff88;
    border-radius: 6px;
    min-height: 30px;
    margin: 1px;
}

QScrollBar::handle:vertical:hover {
    background-color: #00ffff;
    box-shadow: 0 0 5px rgba(0, 255, 255, 0.5);
}
```

### Input Fields

```python
QLineEdit, QTextEdit {
    background-color: #1a1a1a;
    color: #e0e0e0;
    border: 1px solid #333333;
    border-radius: 4px;
    padding: 5px;
    font-family: 'Segoe UI', sans-serif;
}

QLineEdit:focus, QTextEdit:focus {
    border: 1px solid #00ffff;
    background-color: #222222;
}
```

---

## Key Differences from Initial Approach

### What Changed
1. **Background**: From pure black to dark grey (#121212)
2. **Text**: From neon green everywhere to light grey with neon accents
3. **Contrast**: From maximum to comfortable
4. **Fonts**: From all-monospace to mixed typography
5. **Buttons**: From full opacity to 80% transparency
6. **Borders**: From bright neon to subtle grey with neon accents

### Why It Works Better
- **Eye comfort**: Can work for hours without strain
- **Professional**: Looks polished, not like a terminal from 1985
- **Usable**: Text is actually readable
- **Consistent**: Cohesive across different UI frameworks
- **Scalable**: Pattern works for both simple and complex interfaces

---

## Implementation Guidelines

### Do's ✅
- Use dark grey backgrounds, not pure black
- Reserve neon colors for interactive elements
- Add subtle hover effects with glow
- Use proper padding to prevent text cutoff
- Test readability at different screen brightnesses
- Enable alternating row colors for tables
- Always show scrollbars for long content

### Don'ts ❌
- Don't use neon colors for body text
- Don't create harsh black/white contrasts
- Don't make everything uppercase
- Don't use tiny fonts (< 9px)
- Don't forget hover states
- Don't use 3D/beveled borders
- Don't mix too many neon colors at once

---

## Framework-Specific Notes

### PyQt5/6
- Use `setStyleSheet()` for comprehensive theming
- Enable `setAlternatingRowColors(True)` for tables
- Set `ScrollBarAlwaysOn` for consistent UI

### Tkinter
- Use `ttk.Style()` with 'clam' theme as base
- Configure both normal and hover states
- Use `tk.Frame` for custom borders (ttk.LabelFrame limitations)

### Cross-Framework Consistency
- Same color values across all frameworks
- Consistent spacing (padding/margins)
- Identical interaction patterns
- Unified uppercase for buttons/headers

---

## Future Improvements for Memory

### For Claude/AI Assistants
When implementing BEDROT style:

1. **Start with readability** - Don't go full cyberpunk immediately
2. **Ask about contrast preferences** - Some users are more sensitive
3. **Button text space** - Always add min-width to prevent cutoff
4. **Test with content** - Empty UIs look different than filled ones
5. **Iterative refinement** - Start subtle, add flair gradually

### Specific Instructions Update
```
When creating BEDROT-style interfaces:
- Use #121212 as main background, not pure black
- Use #e0e0e0 for primary text, not neon green
- Neon colors (#00ff88, #00ffff, #ff00ff) for accents only
- Buttons: 80% opacity backgrounds with proper min-width
- Tables: Subtle alternating rows (#1a1a1a/#202020)
- Always include hover states with subtle glow effects
- Scrollbars: 14px wide with neon handles
- Font: Segoe UI for UI, Consolas for logs only
```

---

## Code Templates

### Quick PyQt5 Theme Application
```python
def apply_bedrot_theme(self):
    with open('bedrot_theme.qss', 'r') as f:
        self.setStyleSheet(f.read())
    self.table.setAlternatingRowColors(True)
    self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
```

### Quick Tkinter Theme Setup
```python
BG_COLOR = '#121212'
FG_COLOR = '#e0e0e0'
ACCENT_GREEN = '#00ff88'
ACCENT_CYAN = '#00ffff'

style = ttk.Style()
style.theme_use('clam')
# Apply configurations...
```

---

## Results

The final BEDROT visual style successfully achieves:
- ✅ Cyberpunk aesthetic without eye strain
- ✅ Professional appearance suitable for daily use
- ✅ Consistent experience across different frameworks
- ✅ Clear visual hierarchy and usability
- ✅ Distinctive brand identity

**User Feedback**: "I really like the vertical scrollbar... wow this UI looks absolutely beautiful!"

---

*This style guide is a living document based on actual implementation experience. The key learning: cyberpunk can be beautiful AND usable.*