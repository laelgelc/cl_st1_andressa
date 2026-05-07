Below I treat f1 (neg) as one pole of a single discourse dimension, focusing only on this pole.

---

## 1. Which group is driving this pole?

Mean scores on f1:

- generic_gpt: 29.89  
- summary_guided_gpt: 17.10  
- human: 12.82  

These are *positive* means, so the **negative pole** is, by definition, the *relative* low end of this factor. Humans have the lowest mean, so:

- **Human posts are driving the negative pole** of f1.
- The two GPT conditions cluster higher on f1, so they are relatively *less* associated with this negative pole.

So whatever discourse this pole encodes is **most characteristic of human-authored loneliness posts**, and comparatively underrepresented in GPT outputs.

---

## 2. Loadings: what does `script` tell us?

Only one lexical variable loads on this pole:

- `script` (loading = −0.31)

So, as scores move toward the **negative** side of f1, the word *script* becomes **more frequent** (or more characteristic). Conversely, texts with high *positive* f1 scores tend to avoid or underuse *script*.

In this dataset, *script* is likely to occur in metadiscursive or meta-textual contexts, e.g.:

- talking about “scripts” of social interaction (“social script”, “conversation script”)
- referring to writing or generating text (“this isn’t a script”, “not following a script”)
- possibly gaming / coding / role-play scripts, but in a loneliness subreddit, the first two are more plausible.

Because the example excerpts are very short and none of them actually contain *script*, we have to treat *script* as a **corpus-wide signal**: it tells us that, across the full dataset, the negative pole is associated with posts where people explicitly talk about *scripts*—often in the sense of **social scripts, authenticity, or not wanting to be scripted**.

So, from the loadings alone, this pole looks like:

> A discourse where loneliness is framed in terms of **(not) following scripts**—social scripts, expected behaviours, or artificial/constructed language.

---

## 3. What do the high-scoring negative-pole excerpts look like?

All 10 high-scoring texts at this pole are **human** posts, and they are all very short. They show a cluster of discourse functions:

1. **Direct invitations to interact / meta-communication**
   - “Come chat. It's free and hopefully therapeutic”
   - “Are there any loners out there looking for a friend?”
   - “theres no reason in particular why I’m telling you this, I just am”
   - “Idk, so we could be lonely and unsocial a little closer”

   These are *overtly interpersonal* moves: invitations, justifications for posting, and explicit orientation to the communicative situation (“telling you this”, “we could be lonely… closer”).

2. **Blunt, compressed emotional stance**
   - “Life is exhausting.”
   - “It’s all hitting me now. There’s so little hope out there. I’m just so tired.”
   - “thats how desperate i am and i hate my healthy life anyways”

   These are short, unelaborated, affect-heavy statements. They read as **raw, unpolished self-disclosure** rather than narrative or reflective essays.

3. **Self-positioning in social relations**
   - “I’m more of a least favorite backup than a friend to them.”
   - “We all have our explanations as to why we are loners, I would like to hear some reasons you guys have.”
   - “Yes I am alone too.”
   - “Idk, so we could be lonely and unsocial a little closer”

   These posts explicitly negotiate **social identity** (“loners”, “friend”, “backup”) and **ingroup alignment** (“we all”, “you guys”, “we could be lonely… closer”).

4. **Questioning and seeking explanation**
   - “Why do I feel lonely and sad when I recall my childhood memories? Why was my father always hating me out of 3 siblings? And why at the age of 40, do I feel very sad about this?”
   - “We all have our explanations as to why we are loners, I would like to hear some reasons you guys have.”

   These are not polished life stories; they are **open questions** and invitations for others to share explanations.

Across these examples, several discourse properties stand out:

- **High interpersonal engagement**: direct address (“you guys”), inclusive “we”, explicit invitations (“come chat”, “are there any loners out there…”).
- **Meta-communicative framing**: “theres no reason in particular why I’m telling you this, I just am” explicitly comments on the act of posting.
- **Non-elaborated, fragmentary style**: many are one or two sentences, often with minimal context.
- **Authenticity / unscriptedness**: they *feel* like spontaneous, unplanned utterances rather than carefully composed narratives.

Even though *script* itself doesn’t appear in these 10 snippets, the *style* of these posts is strikingly **unscripted**: short, abrupt, sometimes grammatically rough, and heavily interactional.

---

## 4. Integrating loadings and examples

We need to give equal weight to:

- the **loading** on `script` (corpus-wide pattern), and  
- the **examples** (local, high-scoring texts).

Putting them together:

1. **From the loading (`script`)**  
   The negative pole is associated with language that explicitly references *scripts*—likely in the sense of:
   - social scripts (“I don’t know the script for making friends”),
   - or rejecting scripted / artificial behaviour (“I don’t want some scripted response”).

   In a corpus that also contains GPT-generated posts, *script* can also be a way humans talk about **LLM-like, formulaic language** (“this sounds like a script”, “not some AI script”).

2. **From the examples**  
   The high-scoring negative-pole texts are:
   - human,
   - short, interactional, and affective,
   - often explicitly meta-communicative (“I’m telling you this”, “come chat”),
   - and they *read* as **unscripted, off-the-cuff self-disclosure**.

So, the discourse encoded at this pole can be characterised as:

- **Human, unscripted, interactional self-disclosure** about loneliness,
- often explicitly oriented to the act of communication and to other users,
- and, at corpus level, associated with talking about *scripts*—either lacking social scripts or rejecting scripted/artificial interaction.

This contrasts (implicitly) with the more elaborated, possibly more “composed” or “generic” style that GPT outputs tend to have, but we do not need to define the opposite pole here.

---

## 5. Possible labels for this pole (with justification)

Here are several candidate labels, each grounded in both the loadings and the examples:

1. **“Unscripted interpersonal self-disclosure”**

   - *Unscripted*: captures both the **corpus-level association with `script`** (negative loading → more `script` at this pole, often in the sense of *not* wanting scripts) and the **spontaneous, fragmentary style** of the examples.
   - *Interpersonal*: reflects the strong **address to others**, invitations to chat, and inclusive “we”.
   - *Self-disclosure*: all examples are brief but explicit revelations of emotional state or social position.

2. **“Anti-script, conversational loneliness talk”**

   - *Anti-script*: foregrounds the idea that these posts are **positioned against scripted or formulaic interaction**, consistent with the `script` loading and the human vs GPT distribution.
   - *Conversational*: the examples look like **snippets of conversation** rather than essays—short, direct, often question–answer or invitation-like.
   - *Loneliness talk*: keeps the thematic domain explicit.

3. **“Raw, unscripted bids for connection”**

   - *Raw*: the emotional bluntness (“Life is exhausting”, “I’m just so tired”, “I hate my healthy life anyways”).
   - *Unscripted*: again ties to `script` and the spontaneous feel.
   - *Bids for connection*: many examples are **explicit attempts to reach out** (“Come chat”, “looking for a friend?”, “we could be lonely… a little closer”).

4. **“Meta-communicative, unscripted posting”**

   - *Meta-communicative*: captures lines like “theres no reason in particular why I’m telling you this, I just am”, which explicitly comment on the act of posting.
   - *Unscripted*: again, the key lexical cue and stylistic impression.
   - *Posting*: emphasises that this is about how people *use the subreddit* to reach out, not just about their internal state.

---

## 6. Recommended primary label

If I had to choose a single label for this negative pole of f1, integrating both the `script` loading and the example texts, I would propose:

> **Unscripted interpersonal self-disclosure**

Justification:

- **“Unscripted”**:  
  - Directly motivated by the negative loading of `script` (this pole is where `script` is characteristic, often in contexts of *not* wanting or not having a script).  
  - Matches the stylistic feel of the examples: short, rough, non-formulaic, emotionally blunt.

- **“Interpersonal”**:  
  - The examples are saturated with **address to others** (“you guys”, “come chat”, “are there any loners out there…”), invitations, and group alignment (“we all”, “we could be lonely… closer”).

- **“Self-disclosure”**:  
  - Every excerpt is a **personal revelation** about loneliness, exhaustion, being a “backup friend”, childhood pain, or desperation, often with minimal narrative scaffolding.

This label captures the discourse type that is:

- **driven by human posts** (lowest mean on f1),
- **lexically signalled** by references to `script` (often in a rejecting or contrastive way),
- and **textually realised** as brief, raw, interaction-oriented posts that feel like people speaking without a prepared script.