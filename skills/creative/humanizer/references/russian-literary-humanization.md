# Humanizing Russian Literary Texts

## Context

The humanizer skill (29 AI-writing patterns) was designed for English prose. When applied to Russian literary texts (synopses, screenplays, fiction), additional considerations apply.

## Russian-Specific AI Tells

### 1. Overly even rhythm
Russian AI-generated text tends to have paragraphs of equal length. Break this by mixing:
- Single-sentence paragraphs («Он выигрывает.»)
- Long flowing paragraphs
- Sentence fragments («Тихо. Как замок.»)

### 2. Declarative moralizing
AI loves to explain what the film is "about":
- ❌ «Фильм о цене, которую платит человек, когда остаётся собой»
- ✅ Let the reader reach this conclusion themselves

### 3. Rule-of-three in Russian
AI overuses three-element lists:
- ❌ «Офис, совещания, костюм»
- ❌ «Два месяца, деньги, бумажки»
- Some are natural — but if there are 5+ in one text, cut most of them.

### 4. Copula avoidance with тире
Russian AI avoids «это»:
- ❌ «Это не хобби — это работа, это то, для чего он родился»
- ✅ «Это не хобби. Это то, для чего он родился» — split into sentences

### 5. "Beautiful silence" overuse
AI loves characters who "don't ask unnecessary questions", "won't say what", "nobody asks". When everyone is silently understanding, the text becomes emotionally hermetic:
- ❌ «Лапшов рядом, не спрашивает лишнего»
- ❌ «Кажется, он что-то понял. А может, и нет»
- ✅ Give at least one scene where people speak directly and painfully

### 6. Dashes vs. em-dashes
Russian uses em-dash (—) as standard punctuation, not an AI tell. The English humanizer's "em dash overuse" pattern does NOT apply to Russian. Leave Russian dashes alone.

### 7. Show, don't explain
- ❌ «Это не спорт. Это ответ на вопрос, заданный в семь лет»
- ✅ Show him driving to the hangar at midnight after a 14-hour workday. The viewer will understand.

## Real Case: «Як-130» Synopsis

Initial claude-sonnet-4.6 version was beautiful but had 7+ AI tells. After humanizer pass:
- Broke even rhythm → mixed short/long paragraphs
- Removed final moral paragraph
- Cut rule-of-three from 5 instances to 1
- Split copula-avoidance constructions
- Added mess: «кто его разберёт», «а может, и нет»
- Kept Russian dashes

After dual GPT-5.5 review, further revision added:
- Hero's internal flaw (obsession vs. family)
- Real cost (wife's scenes)
- Conflict partner (Lapshov argues)
- Symbolic justification for the title (Yak-130 = trainer aircraft = teaching yourself to fly)
- Setup/payoff for the final 3.4% measurement
