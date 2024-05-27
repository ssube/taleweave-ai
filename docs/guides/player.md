# Player's Guide to TaleWeave AI

## Contents

- [Player's Guide to TaleWeave AI](#players-guide-to-taleweave-ai)
  - [Contents](#contents)
  - [Prompt Syntax](#prompt-syntax)
    - [Prompt Function Syntax](#prompt-function-syntax)

## Prompt Syntax

### Prompt Function Syntax

In order to call functions or use actions from your prompt replies, you (or more likely your GUI) can send valid JSON,
or you can use this prompt function syntax.

To use the prompt function syntax, start your prompt with `~` and use the syntax `~action:parameter=value,next=value`
where `action` is the name of the action (the function being called) and the remainder are parameters to be passed into
the function.

There are some limits on this syntax:

- the function name cannot contain `:`
- the parameter names cannot contain `=`
- the values cannot contain `,`
