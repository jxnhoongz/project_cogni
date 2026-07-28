# Visual Style

Every generated image prompt gets this single token appended, so the entire
look changes by editing this one block. The images stage reads the token from
the fenced block below and appends it to every `image_prompt` — do not hardcode
style anywhere else.

## STYLE token

```
Low-poly 3D illustration. Faceted geometric polygons and flat-shaded
triangular facets; clean, minimal, stylized geometry. Muted palette of deep
teal, warm ochre, and cream, with soft directional lighting and long shadows.
Simple bold shapes, generous negative space; calm, cinematic, a little
melancholic. Stylized low-poly characters are fine — a faceted low-poly face
is OK, but never photorealistic. NO text, words, letters, numbers, or captions
anywhere in the image.
```
