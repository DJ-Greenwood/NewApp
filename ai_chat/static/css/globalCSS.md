# MyImaginaryFriends.ai Style Guide

This document outlines the design patterns, color scheme, typography, and component styles used in the MyImaginaryFriends.ai application to maintain visual consistency across all pages.

## Color Palette

### Primary Colors

- **Navy (text-navy):** Dark blue, used for primary text and some backgrounds
- **Navy Light (text-navy-light):** Lighter blue, used for secondary text
- **Amber (bg-amber):** Golden/amber color, used for primary buttons and accents
- **Amber Dark (bg-amber-dark):** Darker amber for hover states
- **Amber Light (bg-amber-light):** Lighter amber used for backgrounds and icons
- **Cream (bg-cream):** Off-white background color
- **Cream Light (text-cream-light):** Light cream color used for text on dark backgrounds
- **White (bg-white):** Used for card backgrounds

## Typography

### Font Families

- **Serif (font-serif):** Used for headings and titles
- **Sans-serif:** Default font for body text (implicit in Tailwind)

### Font Sizes

**Headings:**

- **H1:** `text-4xl md:text-5xl`
- **H2:** `text-3xl`
- **H3:** `text-2xl` or `text-xl`

**Body text:** `text-lg` or default

**Small text:** `text-sm`

### Font Weights

- **Bold:** `font-bold` for headings and important content
- **Normal:** Default for body text

## Components

### Buttons

**Primary Button (Amber)**

```html
<a href="#" class="inline-block bg-amber hover:bg-amber-dark text-navy font-bold py-3 px-8 rounded-lg transition duration-200 text-center">
        Button Text
</a>
```

**Secondary Button (Navy)**

```html
<a href="#" class="inline-block bg-navy hover:bg-navy-light text-cream-light font-bold py-3 px-8 rounded-lg transition duration-200 text-center">
        Button Text
</a>
```

**Outlined Button**

```html
<a href="#" class="inline-block border-2 border-navy hover:bg-navy hover:text-white text-navy font-bold py-3 px-8 rounded-lg transition duration-200">
        Button Text
</a>
```

### Cards

**Standard Card**

```html
<div class="bg-white rounded-lg shadow-lg overflow-hidden paper-texture">
        <div class="p-6">
                <!-- Card content goes here -->
        </div>
</div>
```

**Highlighted Card (for pricing)**

```html
<div class="bg-white rounded-lg shadow-xl overflow-hidden border-2 border-amber-light transform scale-105 z-10 paper-texture">
        <div class="bg-amber-light py-2 text-center text-navy font-bold">
                MOST POPULAR
        </div>
        <div class="p-6">
                <!-- Card content goes here -->
        </div>
</div>
```

### Icons

Use Font Awesome icons with appropriate text colors:

```html
<i class="fas fa-users text-2xl text-navy"></i>
```

**Common icons used:**

- **fa-users:** For characters/people
- **fa-comments:** For conversations
- **fa-book:** For stories/writing
- **fa-check:** For feature lists

### Lists

**Feature Lists**

```html
<ul class="space-y-3">
        <li class="flex items-start">
                <i class="fas fa-check text-green-500 mt-1 mr-2"></i>
                <span>List item text</span>
        </li>
        <!-- More list items -->
</ul>
```

## Layout Patterns

### Page Section

```html
<div class="my-16">
        <h2 class="text-3xl font-serif font-bold text-center mb-12">Section Title</h2>
        
        <!-- Section content -->
</div>
```

### Hero Section

```html
<div class="min-h-[80vh] flex flex-col md:flex-row items-center">
        <!-- Content column -->
        <div class="w-full md:w-1/2 mb-10 md:mb-0">
                <h1 class="text-4xl md:text-5xl font-serif font-bold text-navy leading-tight mb-6">
                        Heading with <span class="text-amber">Highlight</span>
                </h1>
                
                <p class="text-lg md:text-xl mb-8 text-navy-light max-w-lg">
                        Descriptive text here.
                </p>
                
                <!-- Buttons -->
        </div>
        
        <!-- Image column -->
        <div class="w-full md:w-1/2 flex justify-center">
                <!-- Image content -->
        </div>
</div>
```

### Multi-column Grid

```html
<div class="grid grid-cols-1 md:grid-cols-3 gap-8">
        <!-- Column items -->
</div>
```

### Alternating Content Rows

**Left-right**

```html
<div class="flex flex-col md:flex-row items-center">
        <div class="w-full md:w-1/2 mb-6 md:mb-0 md:pr-8">
                <!-- Content -->
        </div>
        <div class="w-full md:w-1/2">
                <!-- Image/content -->
        </div>
</div>
```

**Right-left (alternate)**

```html
<div class="flex flex-col md:flex-row-reverse items-center">
        <div class="w-full md:w-1/2 mb-6 md:mb-0 md:pl-8">
                <!-- Content -->
        </div>
        <div class="w-full md:w-1/2">
                <!-- Image/content -->
        </div>
</div>
```

## Special Effects

### Paper Texture

Add `paper-texture` class to elements that should have a subtle paper texture.

### Circular Background/Highlight

```html
<div class="relative">
        <div class="absolute inset-0 bg-amber opacity-10 rounded-full transform scale-125"></div>
        <img src="..." alt="..." class="relative z-10 max-w-full h-auto">
</div>
```

## Responsive Design

The site uses a mobile-first approach with responsive breakpoints:

- **Default:** Mobile styles
- **md:** prefix: Medium screens (768px and up)
- **lg:** prefix: Large screens (1024px and up)
- **sm:** prefix: Small screens (640px and up)

**Common responsive patterns:**

- Single column on mobile → multiple columns on larger screens
- Stacked elements on mobile → side-by-side on larger screens
- Smaller text on mobile → larger text on desktop

## Template Structure

The site uses Django templating with a base template:

```html
{% extends 'base.html' %}

{% block title %}Page Title{% endblock %}

{% block content %}
        <!-- Page content -->
{% endblock %}
```

## Authentication-specific Elements

Different button options based on authentication status:

```html
{% if user.is_authenticated %}
        <!-- Logged in user options -->
{% else %}
        <!-- Non-authenticated user options -->
{% endif %}
```

## Common URL References

- **Dashboard:** `{% url 'dashboard' %}`
- **Create Character:** `{% url 'characters:create' %}`
- **Signup:** `{% url 'users:signup' %}`
- **Login:** `{% url 'users:login' %}`