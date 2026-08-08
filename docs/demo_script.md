# Iteration 1 Demo Script

Target duration: 6–8 minutes.

## 1. Frame the product (45 seconds)

Open the home page. Say:

> Signal Review helps an external social media safety analyst prioritise
> public Twitter/X account evidence. This is an offline demonstration and a
> human-review aid. It never makes a final bot determination or takes platform
> action.

Point to “Decision support only. The final judgement remains with you.” and the
permanent **Understand this review tool** link.

## 2. Single-account path (2 minutes)

Choose **High example — @everyletterbot (project dataset)** and begin assessment.

- Point out the source-data preview and missing-value handling.
- Show feature completeness before the score.
- Show the High text label, score, model and threshold versions, time, ordered
  top factors and uncertainty caveat.
- Open **Review model information and limitations**. Show the three
  plain-language guidance sections first, then expand **Technical model and
  evaluation record** for the verified metrics and limitations.

## 3. Human accountability and reset (1 minute)

Return and show that the same 91% High result is still present. Record
**Override** with reason `context reviewed`.
Flag for follow-up with reason `second review`.

Read the two no-platform-action acknowledgements. Select **Start new
assessment** and show that the previous result, decision and follow-up state no
longer appears.

## 4. Insufficient evidence (45 seconds)

Choose `demo_incomplete_01`. Show the Insufficient data completeness state, no
risk band, direct model-information link, and optional follow-up review.

## 5. Batch partial success (1.5 minutes)

Download the template and upload:

```csv
account_id
demo_low_01
bad identifier!
demo_high_01
demo_incomplete_01
```

Show `Completed: 3`, `Failed: 1`, the row-level validation error, and the
no-platform-action statement.

## 6. Sort and filter (1 minute)

- Sort highest risk first.
- Filter High, then Eligible, then Unreviewed.
- Point out active filters and matching count.
- Clear filters and show all four original rows return without rerunning.

Close by reiterating that the model supports prioritisation, while the analyst
retains responsibility for the final reviewed decision.
