import string
import random

import lightbulb

ALL_CHARS = string.ascii_letters + string.digits


async def autocomplete_callback(ctx: lightbulb.AutocompleteContext[str]) -> None:
    current_value: str = ctx.focused.value or ""
    values_to_recommend = [
        current_value + "".join(random.choices(ALL_CHARS, k=5)) for _ in range(10)
    ]
    await ctx.respond(values_to_recommend)

complete = lightbulb.Loader()
@complete.command
class autoComplete(
    lightbulb.SlashCommand,
    name="randomchars",
    description="autocomplete demo command"
):
    text = lightbulb.string("text", "autocompleted option", autocomplete=autocomplete_callback)

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        await ctx.respond(self.text)