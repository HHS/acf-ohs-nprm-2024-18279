# Lessons Learned
[General Lessons Learned](#general-lessons-learned)\
[OHS Technical Lessons Learned](#ohs-technical-lessons-learned)\
[Best Practices on Topic Selection](#best-practices-on-topic-selection)

## General Lessons Learned
Continuous collaboration with policy experts was vital for successful delivery. The OHS Policy Team and ACF Tech Data Surge team worked together to hone topic list and prompt that was sent to ChatGPT.
- Getting the wording right to ensure broad enough, but also distinct enough topics was an iterative process that the OHS policy team informed heavily.
- The OHS Policy team had knowledge around how commenters would discuss particular topics, ACF Surge team helped to itentify topics that were too similar or specific
  
Be specific with what you want ChatGPT to give you back: ask ChatGPT to format responses in a programmatic way to make them easy to store and add to dataframes.
- Without specifically asking chatGPT to return responses in a particular format, the responses were inconsistent, and impossible to manipulate programmatically.
- Getting consistently formatted responses made it easy for us to write code to format those responses into a readable document like an excel file.
  
Keep humans in the loop throughout the process to thoroughly review interim and final results, revise prompts through trial-and-error to improve accuracy, and address gaps in the AI-generated output.
-	To validate the successes and failures of our prompts, we used a human-centered validation approach on a small set of comments. 
-	The AI analysis is not the final step: OHS’s content experts will take the results and thoroughly review them as well as address gaps
  
This project also demonstrated several keys to success for the ethical use of AI at scale in delivering results for ACF’s mission. 
-	This type of qualitative analysis is a strong use case for pre-trained large language models like ChatGPT, which are mature enough to enable quick implementation and useful results compared to building a custom algorithm from scratch
-	It was critical that we used private ChatGPT endpoints for several reasons: first, doing so ensured we had stable, high-throughput access to the model; second, it meant the data we were analyzing didn’t get thrown into the general training pool for the public ChatGPT. While this project leveraged all public data, it is especially important for future use cases that could include restricted data.
-	Finally, we were able to design cross-cloud infrastructure for this project in a way that balanced the realities of budget and procurement in the short timeline. It is worth pointing out that ChatGPT is significantly cheaper to access on Azure because Microsoft is a significant investor in OpenAI, who owns ChatGPT. In this case, we were able to finagle a way to connect OHS’s AWS environment with a temporary Azure environment that was blessed by ACF’s CISO because the data for this analysis was all public, but OHS is also considering how to improve their cloud infrastructure capacities in the future to better scale solutions that benefit from Azure like ChatGPT

## OHS Technical Lessons Learned
**Challenge ourselves to create high-level discreet topics and add sub-topic hierarchy:** A high level topic with subtopic hierarchy for bucketing segments that were interrelated may have been helpful. For example, one top-level topic of staffing compensation and benefits with multiple subtopics such as pay parity, pay scales, wages… Challenging ourselves to discreet topic areas and have a second hierarchy of interrelated sub-topics could have minimized duplicative coding of segments. Summaries could still run across high-level topics with an emphasis to run sub-topic specific summary analysis.
-	If more discreet high-level topics could have been made, then it may have been feasible for ChatGPT to only assign one primary topic per segment. And in cases when ChatGPT thought a statement covered multiple high-level discreet topics, a multi-high level topic flag may have been useful with a secondary topic noted.
  
**Trust the AI to not miss gaps:** We made choices that leaned towards overcategorizing due to concerns that a segment would not be properly categorized, but this led to more burden in pruning and/or working with over coded topics. The AI was great at categorizing segments and it may have been less burdensome to trust the AI and have content experts to focus on identifying areas that needed to be shifted to a more proper category rather than working with over coded topics.  I think there is a better balance that could have been struck here.

**Using rigid rules to code topics:** After reviewing the output, I think it’s better to not use hard and fast rules like code to topic if X bill number is displayed. It would have been faster to filter any uncategorized segments for bill numbers to identify any segments that should have been coded to that topic. I think these type of rules would be more helpful if only used towards topics that are not being properly categorized like “definition of head start”. Not so useful for topics like wages which the AI was phenomenal at coding without hard and fast rules.

## Best practices on topic selection
Topic hierarchies:
-	There is no right answer in terms of the number of topics. Instead, a couple lists should be produced to test the model at various levels of topic specificity.
-	When producing different hierarchy levels of topics, it is best to write them in a hierarchical format with the largest topic category at level 1, and sub-topic categories to their right. The larger topic categories can be repeated for each nested sub-topics. See table below:

| Level 1 | Level 2 | Level 3 |
| --- | --- | --- | 
| Standards of Conduct | Standards of Conduct | Standards of Conduct | 
| Duration | Duration for Early Head Start | Duration for Early Head Start | 
| Duration | Duration for Head Start Preschool | Duration for Head Start Preschool | 
| Lead Exposure | Lead Exposure | Lead in water | 
| Lead Exposure | Lead Exposure | Lead in paint | 

-	Sub-topics should contain the relevant key words, even if they words appear in the larger topic. For example, if the larger topic is “lead exposure”, the sub-topic should be “lead in water” rather than just “water” because the sub-topic must be able to stand alone.

Topic wording:
- Topic wording is also about balance. Currently ChatGPT charges by word, so every word counts. At the same time, each additional word can provide more content that gets at the heart of a topic’s meaning. You can strike this balance by thinking about the most central word.
  * For example, if the topic area is "Delegation of Program Operations" the topic is really talking about the "Delegate Agencies". This is a good shortening of the topic because it contains both the key action "Delegation" and the primary subject which are the "agencies" that get delegated to.
- If the topic is too vast to be captured in a single word, it is better to create a composite of a couple different phrases, which should share as little overlap as possible, and all together capture broader context of the topic.
  * For example, if the topic area is “Program Structure”, the model will struggle because these words are too vague. Instead, we can feed an abbreviated list of program structure changes: “Program Structure: class size, hours of operation, length of school year”. I excluded phrases like “school day” from this list because this phrase is already topically close enough to “hours of operation” and “school year”. When the model gets this list of phrases, it will essentially take the average semantic meaning of the list as the topic. The words “school day” won’t modify the semantic meaning enough to be worth the extra words. On the other hand, I kept in “class size” because it isn’t remotely represented by the other phrases in the sentence.
- Use as context specific words as possible, without making the topic unnecessarily narrow. Vague words that can be attributed to other topic areas will be less useful than specific words that will be more similar to the language used in the comments.
  * For example, “Protections for Data Sharing” contains less specific language. The words “Protections” and “Sharing” can be swapped for “Data Privacy” which carriers the same semantic meaning in fewer words, or the word “FERPA” which is very context specific. Ultimately, I labeled this topic “Data Privacy and FERPA”, which contains the same number of words with greater specificity.
 
| Old Topic | New Topic | Change |
| --- | --- | --- | 
| PART 1301 PROGRAM GOVERNANCE  | Governing body and parent committees | Reworded | 
| Subpart D Health Program Services | Health, nutrition and mental health | Reworded | 
| Subpart C Protections for Data Sharing | Data Privacy and FERPA | Reworded | 
| Subpart B Program Structure | Program Structure: class size, hours of operation, length of school year | Longer | 
| Subpart B Program Structure | Center or home based program structure | Longer | 
| Subpart F Additional Services for Children Eligible for IDEA  | Disabilities, IDEA, 504 Plan and Individualized Education Plan | Longer | 
| Subpart D Delegation of Program Operations 	Delegate Agencies | Delegate Agencies | Shorter | 
| Subpart A Suspension, Termination or Denial of Refunding, Reduction in funding, and their appeals | Funding suspension and refunding appeals | Shorter | 
    


