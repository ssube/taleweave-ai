# TaleWeave AI Engine

## Contents

- [TaleWeave AI Engine](#taleweave-ai-engine)
  - [Contents](#contents)
  - [What is a system?](#what-is-a-system)
  - [What kinds of entities exist in the world?](#what-kinds-of-entities-exist-in-the-world)
  - [What are actions?](#what-are-actions)
  - [What are attributes?](#what-are-attributes)
  - [What are rules?](#what-are-rules)
  - [What are triggers?](#what-are-triggers)
  - [What are events?](#what-are-events)

## What is a system?

In TaleWeave AI, a system refers to a predefined logical process that governs the interaction and behavior of entities
within the game world. These systems are essential for modifying the attributes of entities based on the actions taken
and the rules applied during gameplay. By integrating systems, TaleWeave AI facilitates dynamic and responsive
environments where each action has a potential impact, reflecting changes in the game's state and influencing subsequent
player decisions. Systems are designed to be modular and scalable, allowing developers to customize or extend the game
mechanics to suit different types of adventures and narrative styles.

## What kinds of entities exist in the world?

In the immersive world of TaleWeave AI, entities are categorized into Rooms, Actors, and Items, each playing a vital
role in crafting the narrative and gameplay experience. Rooms serve as the fundamental spatial units where the story
unfolds, each containing various Actors and potentially multiple Items. Actors, representing characters in the game,
possess inventories that hold Items, which are objects that can be interacted with or utilized by the Actors. Currently,
TaleWeave AI does not support Containers—Items that can hold other Items—but the structure is designed to support
complex interactions within and between these entity types, laying the groundwork for a deeply interactive environment.

## What are actions?

Actions in TaleWeave AI are defined as Python functions that enable both human players and AI-driven characters to
interact with the game world. These actions, which include behaviors like taking an item or moving between rooms, are
integral to advancing the gameplay and affecting the state of the world. Each actor is permitted one action per round,
which can significantly alter the attributes of entities, reposition entities between rooms or actors, or modify the
game world by adding or removing entities. This framework ensures that every turn is meaningful and that players'
decisions have direct consequences on the game's progression and outcome.

## What are attributes?

Attributes in TaleWeave AI are key-value pairs that define the properties of an entity. These attributes can be of
various types—boolean, number, or string—such as an actor’s mood being "happy," their health being quantified as 10, or
an item's quality described as "broken" or quantified with a remaining usage of 3. Attributes play a crucial role in the
game's logic system by influencing how entities react under different conditions. They are actively used to trigger
specific rules within the game, and their labels are included in prompts to guide language model players in making
decisions that are contextually appropriate and aligned with their character's current state.

## What are rules?

Rules in TaleWeave AI are defined mechanisms within the logic system that facilitate the updating of the game world
based on specific criteria. Each rule describes a transition from one state of an attribute to another—for instance, an
entity might transition from being "full" to "hungry" or from "happy" to "sad." These rules can employ set logic or use
a rule engine to execute simple predicates, allowing for sophisticated control over how and when attribute states
change. This structured approach ensures that the game world remains dynamic and responsive, with entities exhibiting
behaviors that reflect their evolving conditions.

## What are triggers?

Triggers in TaleWeave AI act as the logical counterpart to actions. While actions are initiated by players (either human
or AI) to interact with the game world, triggers are automated responses invoked by the game’s logic system based on
specific conditions or rules. When a particular condition is met, the corresponding trigger function is executed, which
can alter the attributes of an entity significantly. These triggered functions are powerful tools within the logic
system, enabling the game to automate complex behaviors and interactions, thereby enriching the player’s experience with
a more lifelike and engaging narrative environment.

## What are events?