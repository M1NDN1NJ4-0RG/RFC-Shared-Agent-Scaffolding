# Markdown MD013 Torture Garden Fixture

## Nested lists: parent → child → grandchild, with siblings

- Parent A: This is a deliberately long sentence intended to exceed the typical 120 character limit so the reflow tool has something to chew on without chewing the bones of the list structure.
  - Child A1: Another long line that should wrap as a continuation line, NOT become a new bullet, and NOT collapse into the parent line.
    - Grandchild A1a: This line is also long and should wrap while keeping indentation consistent and while preserving grandchild association.
    - Grandchild A1b: This item exists to ensure sibling grandchildren remain siblings and do not get merged into one mega-line.
  - Child A2: Another child item that ensures the tool does not accidentally treat this as paragraph continuation of Child A1.
- Parent B: This parent exists to ensure that once you return to parent indent, the tool does not remain “stuck” in nested mode.
  - Child B1: Verify that the tool does not mistakenly indent this at the wrong level due to previous nesting.
- Parent C: Short item.

---

## Checkboxes inside nested lists (the classic mangler)

- [ ] Parent task: This task description is intentionally very long so it exceeds the line length limit and triggers wrapping behavior that must not break checkbox syntax or indentation.
  - [ ] Child task A: Another very long description designed to wrap and ensure the checkbox stays at the start of the list item, not duplicated, not moved, not split.
    - [x] Grandchild done item: This exists to ensure mixed checked/unchecked formatting remains stable even after wrapping.
  - [x] Child task B: Completed task with long tail text that should wrap as continuation, not as a new checkbox item, and not as a paragraph merged into sibling content.
- [ ] Second parent task: Ensures the tool properly resets indentation and does not continue nesting.

---

## List items with paragraph continuations

- Item 1: This is a long introduction that should wrap nicely and remain part of item 1, and the continuation should be indented correctly as a continuation line.

  This is a continuation paragraph for item 1. It should remain attached to item 1, not become a separate paragraph outside the list, and not get merged into the next list item.

  - Subitem 1a: A nested item after a paragraph continuation. Many fixers get confused here.
    This continuation line is intentionally long and should wrap while staying under the subitem, not escaping to parent indentation.

- Item 2: Another long item that ensures list parsing remains correct even after blank lines and paragraphs.
  1. Nested ordered list item: This must remain under Item 2.
  2. Second nested ordered list item: With long text that wraps.

---

## Numbered list resets and sibling list collisions

1. Item one: Long text that should wrap without turning into "1. 1. 1." or otherwise duplicating numbering.
2. Item two: Long text to wrap again and ensure numbering remains stable.

   - Sibling bullet list under item two: This tests that bullet siblings do not get merged into the numbered list items.
   - Another bullet sibling under item two: This is long enough to wrap and should remain a bullet.

3. Item three: This is short.

New list:

1. A new numbered list that restarts at 1: This is intentionally a separate list, not a continuation of the previous one, and should remain separate after reflow.
2. Second item in the restarted list: Long enough to wrap.

- A bullet list after numbered list: Ensure no confusion about resetting list contexts.
- Another bullet: Long enough to wrap.

---

## Blockquotes with lists

> - Quoted bullet item: This line is long and should wrap, but remain inside the blockquote and remain a bullet item, not escape the quote marker.
>   - Nested quoted bullet: Must remain nested inside quoted bullet.
>     - Deep quoted bullet: Must remain deep.
>
> 1. Quoted numbered item: Long and wrap.
> 2. Second quoted numbered item: Long and wrap.

- Normal list after blockquote: Ensure the tool exits quote context properly.

---

## Lists adjacent to tables (do not melt the table)

- Bullet before table: This is long and wraps but should not affect the table that follows.
- Another bullet: long.

| Column A | Column B | Column C |
| --- | --- | --- |
| A value that is long but should NEVER be reflowed by the MD013 fixer because tables must be treated as structure-sensitive | B | C |
| A2 | B2 | C2 |

- Bullet after table: Ensure the fixer doesn’t “think” the table lines are paragraphs and try to wrap them.
  - Nested bullet after table: long.

---

## Lists with HTML comments separating structure

- Parent bullet before comment: long and wrap.
  <!-- This HTML comment should remain exactly where it is and not get wrapped or moved or merged with the bullet text. -->
  - Child bullet after comment: long and wrap.
    <!-- Another comment -->
    - Grandchild bullet: long and wrap.

- Second parent bullet: Ensure sibling items remain siblings.

---

## Mixed markers and indentation oddities

* Star bullet: long and wrap.
  + Plus bullet child: long and wrap.
    - Dash grandchild: long and wrap.
      * Star deep: long and wrap.

- Dash bullet: long.
  1. Numbered child list: long and wrap.
  2. Second numbered child list: long and wrap.
  
    - Bullet inside numbered list: long and wrap.

---

## Reference links + definitions (do not break the definitions)

- This item references [the spec][mdspec] and includes long text to trigger wrapping, but the reference definition must remain intact and not be wrapped into garbage.

- Another item references [something else][otherref] and also has a long tail so wrapping triggers.

[mdspec]: https://daringfireball.net/projects/markdown/syntax "Markdown Syntax"
[otherref]: https://example.com/some/really/long/url/that/should/not/be/broken/by_the_fixer "Example Ref"

---

## Inline code: do not rewrap lines containing backticks

- This item contains inline code `some_really_long_identifier_name_that_should_not_get_split_or_wrapped_in_weird_places_even_if_the_line_is_long` and must be skipped by the reflow tool per your rule.

- This item has multiple inline code chunks: `alpha` `beta` `gamma` and also has enough text to exceed the limit and should remain untouched if your rule is "any backtick line is exempt".

- This is a long line with a single extremelylongtokenwithoutspaceswhichcannotwrapcleanly and should be left alone rather than broken mid-token.

---

## Definition-list-like patterns (common in docs)

Term A:
  - This resembles a definition list. Tools often break the indentation.
  - Long text that should wrap as continuation and stay aligned under the term.

Term B:
  1. Nested numbering under a definition style block: long and wrap.
  2. Second: long and wrap.

---

## Admonition-like blocks (not real markdown, but common)

> [!NOTE]
> This is a long note block used by GitHub-flavored markdown / docs tooling. A fixer must not rewrap or remove the blockquote prefix.

> [!WARNING]
> - This warning contains a list item inside a quote. That’s cursed, but real. Don’t break it.
> - Another item long enough to wrap.

Normal paragraph after.

---

## Code fences near lists (do not smear context)

- Item before fence: long and wrap.

~~~bash
echo "This is code and should never be wrapped."
for i in 1 2 3; do echo "$i"; done
~~~

- Item after fence: long and wrap.
  - Nested after fence: long and wrap.

```python
def example():
    return "also code"
```

- Another after python fence: long and wrap.

---

## Images in list items

- Item with image: ![alt text](images/some-image.png) and a long line that wraps but must not break the image syntax or indent weirdly.

- Another item with reference image: ![alt][imgref] and long text.

[imgref]: https://example.com/some/very/long/image/path/that/should/not_be_broken.png

---

## Autolinks and angle URLs

- This item has an autolink <https://example.com/some/really/long/url/path/that/should/not/be/wrapped> and should be skipped due to URL exemption.

- This item has https://example.com/another/really/long/url and should also be skipped.

---

## Footnotes inside lists

- Item with a footnote reference[^1] and long text to trigger wrapping but without moving or breaking the footnote marker.

- Another item referencing the same footnote[^1] to ensure repeated references remain unchanged.

[^1]: This is the footnote definition. It should not be reflowed in a way that breaks the definition syntax.

---

## Multi-line emphasis and links

- This item contains **bold text that is long and should wrap** while keeping the emphasis markers correct, and also includes a [link with text](https://example.com/somewhere) that should remain intact.

- This item contains _italic text_ and `inline code` so it should be skipped if your rule is “any backtick on the line => skip”.

---

## Frontmatter and headings

---
title: "Frontmatter file"
description: "This file includes YAML frontmatter which many tools should treat carefully."
---

# Heading must remain heading

- Bullet after frontmatter: long and wrap.

---

## Blank lines + lazy list continuation

- Parent item: long line that wraps.
  This is a lazy continuation line (no blank line). It should remain part of the parent list item and not become a new paragraph outside the list.

  - Nested child: long and wrap.

- Next parent: long and wrap.

---

## Hyper-cursed combo: everything everywhere all at once

1. Numbered parent with checkbox child and a long line to wrap, and this must not become "1. 1. 1." or lose numbering.
   - [ ] Checkbox bullet under numbered list with long text to wrap, must remain nested.
     > Blockquote inside checkbox list item with long quoted text that must keep `>` prefix.
     >
     > - Bullet inside blockquote inside checkbox: long and wrap.

   - Bullet sibling of checkbox: includes inline code `do_not_touch_this_line_even_if_long` so should be skipped.

| Table | Next |
| --- | --- |
| This long cell should not be wrapped | B |

<!-- HTML comment between lists -->
- Bullet after table + comment: long and wrap.

[ref]: https://example.com/very/long/reference/that/should_not_wrap

---
