import discord
import logging
from enum import Enum
from typing import List, Optional, Callable, Dict, Any

logger = logging.getLogger("bot.ui")

# ==============================================================================
# ---------------------------- Button Creator ----------------------------------
# ==============================================================================

class button:
    def __init__(self, label: str, style: discord.ButtonStyle = discord.ButtonStyle.primary, 
                 emoji: Optional[str] = None, custom_id: Optional[str] = None, 
                 row: Optional[int] = None, disabled: bool = False):
        self.label = label
        self.style = style
        self.emoji = emoji
        self.custom_id = custom_id
        self.row = row
        self.disabled = disabled

class ButtonCreator(discord.ui.View):
    def __init__(self, *buttons: button, callback: Optional[Callable] = None, 
                 persistent: bool = False, bot: Optional[discord.Client] = None):
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
                # USPRAWNIENIE: Przekazujemy również obiekt klikniętego przycisku
                await self.shared_callback(interaction, btn_obj)
            else:
                await interaction.response.send_message("Nie przypisano żadnej akcji...", ephemeral=True)
        return inner_callback
    
def get_button_style(style_name: str) -> discord.ButtonStyle:
    """Zamienia string z configu na obiekt discord.ButtonStyle."""
    style_map = {
        "PRIMARY": discord.ButtonStyle.primary,      # Blurple (fioletowo-niebieski)
        "SECONDARY": discord.ButtonStyle.secondary,  # Szary
        "SUCCESS": discord.ButtonStyle.success,      # Zielony
        "DANGER": discord.ButtonStyle.danger,        # Czerwony
        "LINK": discord.ButtonStyle.link             # Styl dla linków URL
    }
    
    # .upper() zabezpiecza przed pisownią "primary" czy "Primary" w YAML
    return style_map.get(style_name.upper(), discord.ButtonStyle.primary)
   
# ==============================================================================
# ---------------------------- Embed Creator -----------------------------------
# ==============================================================================

def field(name: str, value: str, inline: bool = False) -> Dict[str, Any]:
    return {"name": name, "value": value, "inline": inline}

class EmbedCreator(discord.Embed):
    def __init__(self,
                 title: Optional[str] = None,
                 description: Optional[str] = None,
                 color: discord.Color = discord.Color.blue(),
                 url: Optional[str] = None,
                 timestamp: bool = False,
                 fields: Optional[List[Dict[str, Any]]] = None,
                 footer: Optional[str] = None,
                 footer_icon: Optional[str] = None,
                 thumbnail: Optional[str] = None,
                 image: Optional[str] = None,
                 author_name: Optional[str] = None,
                 author_icon: Optional[str] = None,
                 author_url: Optional[str] = None):
       
        # USPRAWNIENIE: discord.utils.utcnow() zamiast datetime.now() zapobiega problemom ze strefami czasowymi bota
        super().__init__(
            title=title,
            description=description,
            color=color,
            url=url,
            timestamp=discord.utils.utcnow() if timestamp else None
        )

        if fields:
            for f in fields:
                self.add_field(name=f['name'], value=f['value'], inline=f.get('inline', False))

        if footer:
            self.set_footer(text=footer, icon_url=footer_icon)
       
        if thumbnail:
            self.set_thumbnail(url=thumbnail)
           
        if image:
            self.set_image(url=image)

        if author_name:
            self.set_author(name=author_name, icon_url=author_icon, url=author_url)

# ==============================================================================
# ---------------------------- Modal Creator V3 --------------------------------
# ==============================================================================

class ModalInputType(str, Enum):
    TEXT = "text"
    SELECT = "select"
    CHECKBOX = "checkbox"
    CHECKBOX_GROUP = "checkbox_group"
    RADIO = "radio"
    USER = "user"
    ROLE = "role"
    CHANNEL = "channel"
    MENTIONABLE = "mentionable"

class ModalInput:
    """Jedna klasa z typowaniem Enum, by obsłużyć wszystkie komponenty modala."""
    def __init__(self, 
                 type: ModalInputType,
                 label: str, 
                 custom_id: str,
                 placeholder: Optional[str] = None,
                 min_values: int = 1,
                 max_values: int = 1,
                 options: Optional[List[Any]] = None,
                 **kwargs: Any):
        self.type = type
        self.label = label
        self.custom_id = custom_id
        self.placeholder = placeholder
        self.min_values = min_values
        self.max_values = max_values
        self.options = options or []
        self.extra = kwargs  # Przechowuje unikalne flagi typu style, default, channel_types

class ModalCreator(discord.ui.Modal):
    def __init__(self, title: str, *args: Any, callback: Optional[Callable] = None, 
                 timeout: Optional[float] = None, inputs: Optional[List[Any]] = None,
                 action_id: Optional[str] = None):
        super().__init__(title=title, timeout=timeout, custom_id=action_id)
        self.shared_callback = callback
        self.output_values: Dict[str, Any] = {}
        all_inputs = list(inputs) if inputs is not None else list(args)

        # Mapa fabryczna korzysta teraz bezpośrednio z wartości Enuma
        component_mapping = {
            ModalInputType.TEXT: lambda i: discord.ui.TextInput(
                label=i.label, custom_id=i.custom_id, placeholder=i.placeholder,
                style=i.extra.get("style", discord.TextStyle.short),
                default=i.extra.get("default"),
                required=i.extra.get("required", True),
                min_length=i.extra.get("min_length"),
                max_length=i.extra.get("max_length")
            ),
            ModalInputType.SELECT: lambda i: discord.ui.Select(custom_id=i.custom_id, placeholder=i.placeholder, min_values=i.min_values, max_values=i.max_values, options=i.options),
            ModalInputType.CHECKBOX: lambda i: discord.ui.Checkbox(custom_id=i.custom_id, default=i.extra.get("default_checked", False)),
            ModalInputType.CHECKBOX_GROUP: lambda i: discord.ui.CheckboxGroup(custom_id=i.custom_id, min_values=i.min_values, max_values=i.max_values, options=i.options),
            ModalInputType.RADIO: lambda i: discord.ui.RadioGroup(custom_id=i.custom_id, options=i.options),
            ModalInputType.USER: lambda i: discord.ui.UserSelect(custom_id=i.custom_id, placeholder=i.placeholder, min_values=i.min_values, max_values=i.max_values),
            ModalInputType.ROLE: lambda i: discord.ui.RoleSelect(custom_id=i.custom_id, placeholder=i.placeholder, min_values=i.min_values, max_values=i.max_values),
            ModalInputType.CHANNEL: lambda i: discord.ui.ChannelSelect(custom_id=i.custom_id, placeholder=i.placeholder, min_values=i.min_values, max_values=i.max_values, channel_types=i.extra.get("channel_types")),
            ModalInputType.MENTIONABLE: lambda i: discord.ui.MentionableSelect(custom_id=i.custom_id, placeholder=i.placeholder, min_values=i.min_values, max_values=i.max_values)
        }

        for i in all_inputs:
            if not isinstance(i, ModalInput) or i.type not in component_mapping:
                continue
            
            comp = component_mapping[i.type](i)
            
            # Klasyczny TextInput dodajemy bezpośrednio. Reszta wymaga kontenera ui.Label
            if i.type == ModalInputType.TEXT:
                self.add_item(comp)
            else:
                self.add_item(discord.ui.Label(text=i.label, component=comp))
                
            self.output_values[i.custom_id] = comp

    async def on_submit(self, interaction: discord.Interaction):
        if self.shared_callback:
            resolved_inputs = {}
            for cid, obj in self.output_values.items():
                if isinstance(obj, discord.ui.TextInput):
                    resolved_inputs[cid] = obj.value
                elif isinstance(obj, discord.ui.Checkbox):
                    resolved_inputs[cid] = obj.value
                elif isinstance(obj, discord.ui.RadioGroup):
                    resolved_inputs[cid] = obj.value  # Pojedynczy str
                elif isinstance(obj, discord.ui.Select):
                    values = obj.values
                    if getattr(obj, "max_values", 1) == 1:
                        resolved_inputs[cid] = values[0] if values else None
                    else:
                        resolved_inputs[cid] = values
                elif isinstance(obj, (discord.ui.CheckboxGroup, discord.ui.MentionableSelect)):
                    resolved_inputs[cid] = obj.values  # List obiektów lub str

            await self.shared_callback(interaction, resolved_inputs)

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        logger.error(
            "Modal callback failed custom_id=%s interaction_id=%s user_id=%s",
            self.custom_id,
            interaction.id,
            getattr(interaction.user, "id", None),
            exc_info=(type(error), error, error.__traceback__),
        )
        try:
            message = "Wystąpił błąd podczas obsługi formularza. Szczegóły zapisano w logu."
            if interaction.response.is_done():
                await interaction.followup.send(message, ephemeral=True)
            else:
                await interaction.response.send_message(message, ephemeral=True)
        except discord.HTTPException:
            logger.exception("Could not send modal error response interaction_id=%s", interaction.id)
