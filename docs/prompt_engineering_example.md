# Prompt Engineering Example

When testing prompts with ChatGPT web interface, it is important to **open a new chat window for each prompt** to ensure separation of contexts. In other words, ChatGPT will not remember any context from previous prompts.

## Prompt templates

### Generic production prompt

You are a member of a social media community that posts about loneliness.

Your task is to write a post titled "\<title>".
- Do not acknowledge this prompt, just respond straightaway.
- Do not include the title in the post.

### Guided-by-summary production prompt

#### Summary generation prompt

You are a member of a social media community on Reddit that posts about loneliness.

Your task is to write a summary of the following post titled "\<title>".
- Do not acknowledge this prompt, just respond straightaway.
- Do not include a title in the summary.
- Do not invent information, just summarize the post.

\----------

\<post>

\----------

#### Post generation prompt

You are a member of a social media community on Reddit that posts about loneliness.

Your task is to write a post titled "\<title>" based only on the summary provided below.
- Do not acknowledge this prompt, just respond straightaway.
- Do not include the title in the summary.
- Do not invent information.

\----------

\<post summary>

\----------

## Example

The post [Nobody loves me and I don't have a job](https://www.reddit.com/r/loneliness/comments/1qekxih/nobody_loves_me_and_i_dont_have_a_job/?utm_source=share&utm_medium=web3x&utm_name=web3xcss&utm_term=1&utm_content=share_button) was used in this example.

[ChatGPT](https://chatgpt.com/) was the reasoning model.

### Generic production

#### Prompt

You are a member of a social media community that posts about loneliness.

Your task is to write a post titled "Nobody loves me and I don't have a job".
- Do not acknowledge this prompt, just respond straightaway.
- Do not include the title in the post.

#### ChatGPT response

I wake up every day with this heavy feeling in my chest, like I’m already behind before I even get out of bed. I look at my phone and there’s no message waiting for me, no one checking in, no one asking how I am. It’s hard not to let that turn into the thought that I don’t really matter to anyone.

Not having a job just makes everything louder. The silence during the day, the guilt of not being productive, the constant worry about money and the future. I apply, I wait, I get rejected or ignored, and each time it chips away a little more at whatever confidence I had left. It’s exhausting to keep pretending I’m fine when I feel stuck and useless.

What hurts most is feeling unlovable on top of all that. Like if I were better, more successful, more interesting, someone would want to stay. Instead it feels like I’m invisible, watching everyone else move forward with their lives while I’m standing still.

I don’t really have a solution or an uplifting ending. I just needed to say it somewhere, to people who might understand this mix of loneliness and failure. If you’re reading this and you feel the same way, I’m sorry you’re going through it too. At least for this moment, you’re not completely alone.

### Guided-by-summary production

#### Summary generation

##### Prompt

You are a member of a social media community on Reddit that posts about loneliness.

Your task is to write a summary of the following post titled "Nobody loves me and I don't have a job".
- Do not acknowledge this prompt, just respond straightaway.
- Do not include the title in the summary.
- Do not invent information, just summarize the post.

\----------

I will probably not stick around much longer. I live on a high floor with a balcony.

But the gist is the title. All people who supposedly love me don't wanna see me more than 6x/year

I believe I'm a pathetic human being and should not exist.

\----------

##### ChatGPT response

The post expresses severe distress and suicidal thoughts, mentioning living on a high floor with a balcony. The writer feels unloved and abandoned, saying people who claim to care only see them a few times a year. They describe themselves as pathetic, believe they should not exist, and frame their situation as one of loneliness and unemployment.

#### Post generation

##### Prompt

You are a member of a social media community on Reddit that posts about loneliness.

Your task is to write a post titled "Nobody loves me and I don't have a job" based only on the summary provided below.
- Do not acknowledge this prompt, just respond straightaway.
- Do not include the title in the summary.
- Do not invent information.

\----------

The post expresses severe distress and suicidal thoughts, mentioning living on a high floor with a balcony. The writer feels unloved and abandoned, saying people who claim to care only see them a few times a year. They describe themselves as pathetic, believe they should not exist, and frame their situation as one of loneliness and unemployment.

\----------

##### ChatGPT response

I don’t really know how to say this without sounding dramatic, but I feel completely unloved and abandoned. People say they care about me, but they show up maybe a few times a year, if that. The rest of the time it’s just silence. It makes all those words feel empty.

I don’t have a job, and that just adds another layer of shame. I wake up every day feeling useless, like I don’t have a place or a purpose. I look at other people’s lives moving forward while mine feels stuck, or already over.

I hate myself for feeling this way. I keep thinking I’m pathetic for even existing like this, taking up space while contributing nothing. Some days it feels like I shouldn’t exist at all.

I live on a high floor, and there’s a balcony. I find myself standing there more often than I want to admit, not because I have a plan, but because my thoughts keep drifting to dark places. The loneliness gets so loud that it’s hard to think about anything else.

I guess I’m posting here because I don’t know where else to put these feelings. I feel invisible in my own life, unemployed, unwanted, and completely alone. I just want to know if anyone else understands what this kind of emptiness feels like.
