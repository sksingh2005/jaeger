## ​**Skill Graphs \> SKILL .md**​

(source [https://www.dailydoseofds.com/](https://www.dailydoseofds.com/))

Right now, the default approach for Agent skills is simple. You write one skill file that captures one capability. A skill for summarizing. A skill for code review. A skill for writing tests.

|  |
| :---- |

One file details one job, and it works.

But we recently came across an idea that made me rethink this entirely.

What if skills weren't flat files but rather graphs?

Think about how a senior engineer onboards you to a large codebase. They don't hand you one giant document and say "read this." They give you a map. They point you to the right modules. They explain how pieces connect. Then they let you go deeper only where you need to.

|  |
| :---- |

That's the mental model behind a skill graph.

Instead of one big file, you build a network of small, composable skill files connected through wikilinks. Each file captures one complete thought, technique, or concept. The links between them tell the agent when and why to follow a connection.

|  |
| :---- |

Here's what changes with this approach.

The agent doesn't load everything upfront. It scans an index, reads short descriptions, follows relevant links, and only reads full content when it actually needs to. Most decisions happen before reading a single complete file.

Each node is standalone but becomes more powerful in context. A "position sizing" node in a trading skill graph works on its own. But link it to risk management, market psychology, and technical analysis, and now you have context flowing between concepts.

|  |
| :---- |

And suddenly, domains that could never fit in one file become navigable like company knowledge, legal compliance, product docs, and org structure...all traversable from a single entry point.

The building blocks are surprisingly simple.

Wikilinks embedded in prose so they carry meaning, not just references. YAML frontmatter so the agent can scan nodes without reading them. Maps of content that organize clusters into navigable sub-topics.

Markdown files linking to markdown files, and nothing more.

If you want to dig deeper or try building one yourself, check out arscontexta. It's an open-source plugin that sets up the structure and helps you build skill graphs with your agent.

​[**Here's the GitHub repo →**](https://fff97757.click.convertkit-mail2.com/38ug94226etkh20l5m7hrh4po829kt7h64xll/25h2hoh364ln08b3/aHR0cHM6Ly9naXRodWIuY29tL2FnZW50aWNub3RldGFraW5nL2Fyc2NvbnRleHRh)

