import discord
from datetime import datetime

# ---------------------------- Button Creator ----------------------------
'''
Łatwy w użyciu kreator przycisków, który pozwala na tworzenie wielu przycisków z jedną funkcją callback.
Przykład użycia:

async def cog_load(self):
    self.persistent_view = ButtonCreator(
        button("Akcjeptuje Regulamin", discord.ButtonStyle.green, custom_id="rules_accept"),
        callback=self.callback,
        persistent=True,
        bot=self.bot
    )

async def SendVerifyButton(self, interaction: discord.Interaction):
    await interaction.response.send_message("Test", view=self.persistent_view)
''' 

class button:
    def __init__(self, label: str, style: discord.ButtonStyle = discord.ButtonStyle.primary, emoji: str = None, custom_id: str = None, row: int = None, disabled: bool = False):
        self.label = label
        self.style = style
        self.emoji = emoji
        self.custom_id = custom_id
        self.row = row
        self.disabled = disabled

class ButtonCreator(discord.ui.View):
    def __init__(self, *buttons: button, callback=None, persistent: bool = False, bot: discord.Client = None):
        super().__init__(timeout=None if persistent else 180.0)
        self.shared_callback = callback

        for b in buttons:
            btn = discord.ui.Button(
                label=b.label,
                style=b.style,
                emoji=b.emoji,
                custom_id=b.custom_id,
                row=b.row,
                disabled=b.disabled
            )

            btn.callback = self._create_callback(btn)
            self.add_item(btn)

        if persistent and bot:
            bot.add_view(self)

    def _create_callback(self, btn_obj: discord.ui.Button):
        async def inner_callback(interaction: discord.Interaction):
            if self.shared_callback:
                await self.shared_callback(interaction)

            else:
                await interaction.response.send_message("Nie przypisano żadnej akcji..", ephemeral=True)

        return inner_callback
    
# ---------------------------- Embed Creator ----------------------------
'''
Łatwy w użyciu kreator embedów, który pozwala na szybkie tworzenie estetycznych embedów bez konieczności ręcznego ustawiania każdego elementu.
Przykład użycia:

'''

def field(name: str, value: str, inline: bool = False):
    return {"name": name, "value": value, "inline": inline}

class EmbedCreator(discord.Embed):
    def __init__(self, 
                 title: str = None, 
                 description: str = None, 
                 color: discord.Color = discord.Color.blue(),
                 url: str = None,
                 timestamp: bool = False,
                 fields: list = None,
                 footer: str = None,
                 footer_icon: str = None,
                 thumbnail: str = None,
                 image: str = None,
                 author_name: str = None,
                 author_icon: str = None,
                 author_url: str = None):
        
        super().__init__(
            title=title, 
            description=description, 
            color=color, 
            url=url,
            timestamp=datetime.now() if timestamp else None
        )

        if fields:
            for f in fields:
                self.add_field(name=f['name'], value=f['value'], inline=f['inline'])

        if footer:
            self.set_footer(text=footer, icon_url=footer_icon)
        
        if thumbnail:
            self.set_thumbnail(url=thumbnail)
            
        if image:
            self.set_image(url=image)

        if author_name:
            self.set_author(name=author_name, icon_url=author_icon, url=author_url)

# ---------------------------- Modal Creator ----------------------------

'''
Łatwy w użyciu kreator modali (okienek tekstowych).
Przykład użycia:

async def callback(interaction: discord.Interaction, inputs: dict):
    powod = inputs['reason_input'].value
    await interaction.response.send_message(f"Twoje zgłoszenie: {powod}", ephemeral=True)

modal = ModalCreator(
    "Zgłaszanie błędu",
    modal_field("Opisz błąd", discord.TextStyle.long, custom_id="reason_input", placeholder="Tu wpisz treść..."),
    callback=callback
)
await interaction.response.send_modal(modal)
'''

class modal_field:
    def __init__(self, label: str, style: discord.TextStyle = discord.TextStyle.short, 
                 custom_id: str = None, placeholder: str = None, default: str = None, 
                 required: bool = True, min_length: int = None, max_length: int = None):
        self.label = label
        self.style = style
        self.custom_id = custom_id
        self.placeholder = placeholder
        self.default = default
        self.required = required
        self.min_length = min_length
        self.max_length = max_length

class ModalCreator(discord.ui.Modal):
    def __init__(self, title: str, *inputs: modal_field, callback=None, timeout: float = None):
        super().__init__(title=title, timeout=timeout)
        self.shared_callback = callback
        self.input_objects = {} # Słownik do łatwego wyciągania danych w callbacku

        for i in inputs:
            ti = discord.ui.TextInput(
                label=i.label,
                style=i.style,
                custom_id=i.custom_id,
                placeholder=i.placeholder,
                default=i.default,
                required=i.required,
                min_length=i.min_length,
                max_length=i.max_length
            )
            self.add_item(ti)
            # Zapisujemy referencję do obiektu pod jego custom_id
            if i.custom_id:
                self.input_objects[i.custom_id] = ti

    async def on_submit(self, interaction: discord.Interaction):
        if self.shared_callback:
            # Przekazujemy interakcję oraz słownik z polami tekstowymi
            await self.shared_callback(interaction, self.input_objects)
        else:
            await interaction.response.send_message("Modal wysłany, ale brak funkcji obsługującej (callback).", ephemeral=True)

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await interaction.followup.send(f'Wystąpił błąd w modalu: {error}', ephemeral=True)
