# Visual Style

Every generated image prompt gets this single token appended, so the entire
look changes by editing this one block. The images stage reads the token from
the fenced block below and appends it to every `image_prompt` — do not hardcode
style anywhere else.

## STYLE token

```
Risograph-style illustration. Limited muted palette of 2–3 flat inks
(warm ochre, deep teal, soft black) on cream paper. Visible paper grain and
halftone texture, slight ink misregistration. Flat simple shapes, minimal
detail, generous negative space. Contemplative, warm, slightly melancholic
mood. NO realistic human faces or hands — favor landscapes, silhouettes,
objects, symbolic imagery, and figures seen from behind or far away.
NO text, words, letters, numbers, or captions anywhere in the image.
```
